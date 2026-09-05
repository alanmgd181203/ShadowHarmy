"""Vigilante flota piedra OKX — dedupe, relanzar caidos, sellar sanidad.

Tras corte de luz o internet: un tick repone manos faltantes con --continuar.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RANGO_DIR = ROOT / "data" / "beru" / "rango"
INFORME_PATH = RANGO_DIR / "vigilante_flota_informe.json"
LOCK_PATH = RANGO_DIR / "vigilante_flota.lock"
LOG_DIR = RANGO_DIR / "vigilante_flota"
ASIG_PATH = RANGO_DIR / "piedra_asignacion.json"
PIDS_PATH = LOG_DIR / "manos_pids.json"


def _ahora_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _leer_pids_registro() -> dict[str, int]:
    if not PIDS_PATH.is_file():
        return {}
    try:
        raw = json.loads(PIDS_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    out: dict[str, int] = {}
    for k, v in (raw or {}).items():
        act = str(k or "").upper()
        try:
            pid = int(v)
        except (TypeError, ValueError):
            continue
        if act and pid > 0:
            out[act] = pid
    return out


def _guardar_pids_registro(mapa: dict[str, int]) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    limpio = {str(k).upper(): int(v) for k, v in mapa.items() if int(v) > 0}
    PIDS_PATH.write_text(
        json.dumps(limpio, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _pid_vivo(pid: int) -> bool:
    if pid <= 0:
        return False
    # OpenProcess es instantaneo; evita tasklist (lento + encoding).
    try:
        import ctypes

        PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
        handle = ctypes.windll.kernel32.OpenProcess(
            PROCESS_QUERY_LIMITED_INFORMATION, False, int(pid),
        )
        if handle:
            ctypes.windll.kernel32.CloseHandle(handle)
            return True
        return False
    except Exception:
        return False


def flota_esperada(asig_path: Path | None = None) -> list[str]:
    path = Path(asig_path) if asig_path else ASIG_PATH
    data = json.loads(path.read_text(encoding="utf-8"))
    out: list[str] = []
    for base in sorted((data.get("activos") or {}).keys()):
        act = str(base).strip().upper()
        if act:
            out.append(act)
    return out


def _powershell_json(script: str, *, timeout: float = 120.0) -> Any:
    cmd = ["powershell", "-NoProfile", "-Command", script]
    raw = subprocess.check_output(
        cmd, text=True, errors="replace", timeout=timeout,
    ).strip()
    if not raw:
        return []
    return json.loads(raw)


def escanear_manos_piedra() -> dict[str, list[int]]:
    """activo -> lista PIDs (registro local + verificación rapida)."""
    out: dict[str, list[int]] = {}
    reg = _leer_pids_registro()
    vivos_reg: dict[str, int] = {}
    for act, pid in reg.items():
        if _pid_vivo(pid):
            out.setdefault(act, []).append(pid)
            vivos_reg[act] = pid
    if vivos_reg != reg:
        _guardar_pids_registro(vivos_reg)

    # Si el registro ya cubre la flota esperada, no hace falta CIM lento.
    esperados = set(flota_esperada())
    if esperados and esperados.issubset(set(out.keys())):
        return out

    # Fallback corto: solo completar huecos (timeout duro).
    faltan = sorted(esperados - set(out.keys()))
    if not faltan and out:
        return out
    ps = r"""
    $rows = @()
    Get-CimInstance Win32_Process -Filter "Name='python.exe'" -ErrorAction SilentlyContinue |
      Where-Object { $_.CommandLine -match 'arise_beru_rango_manos' } |
      ForEach-Object {
        $c = $_.CommandLine
        if ($c -notmatch '--perfil\s+piedra' -and $c -notmatch 'BERU_RANGO_PERFIL=piedra') { return }
        if ($c -match '--activo\s+(\S+)') {
          $rows += [PSCustomObject]@{ activo = $matches[1].ToUpper(); pid = $_.ProcessId }
        }
      }
    if ($rows.Count -eq 0) { '[]' } else { $rows | ConvertTo-Json -Compress }
    """
    try:
        data = _powershell_json(ps, timeout=90.0)
    except (subprocess.CalledProcessError, json.JSONDecodeError, FileNotFoundError, subprocess.TimeoutExpired):
        return out
    if isinstance(data, dict):
        data = [data]
    for row in list(data or []):
        if not isinstance(row, dict):
            continue
        act = str(row.get("activo") or "").upper()
        pid = int(row.get("pid") or 0)
        if act and pid > 0:
            out.setdefault(act, []).append(pid)
            vivos_reg[act] = pid
    if vivos_reg:
        _guardar_pids_registro(vivos_reg)
    return out


def matar_pid(pid: int, *, dry_run: bool = False) -> bool:
    if pid <= 0:
        return False
    if dry_run:
        return True
    try:
        r = subprocess.run(
            ["taskkill", "/PID", str(int(pid)), "/F"],
            capture_output=True,
            timeout=15,
        )
        err = (r.stderr or b"").decode("utf-8", errors="replace").lower()
        out = (r.stdout or b"").decode("utf-8", errors="replace").lower()
        return r.returncode == 0 or "not found" in err or "no se" in err or "not found" in out
    except (OSError, subprocess.TimeoutExpired):
        return False


def dedupe_manos(
    vivo: dict[str, list[int]],
    *,
    dry_run: bool = False,
) -> tuple[dict[str, int], list[dict[str, Any]]]:
    """Deja 1 PID por Santo (el mas alto = mas reciente)."""
    limpio: dict[str, int] = {}
    acciones: list[dict[str, Any]] = []
    for act, pids in sorted(vivo.items()):
        uniq = sorted(set(int(p) for p in pids if int(p) > 0))
        if not uniq:
            continue
        keep = uniq[-1]
        limpio[act] = keep
        for pid in uniq[:-1]:
            ok = matar_pid(pid, dry_run=dry_run)
            acciones.append({
                "accion": "matar_duplicado",
                "activo": act,
                "pid": pid,
                "conservar": keep,
                "ok": ok,
            })
    return limpio, acciones


def internet_ok() -> tuple[bool, str]:
    try:
        from core import beru_despertar_mil_btc as dm

        px = float(dm.precio_btc_publico() or 0)
        if px > 0:
            return True, f"BTC={px:.2f}"
    except Exception as exc:
        return False, str(exc)
    return False, "sin_precio_btc"


def lanzar_manos_piedra(
    activo: str,
    *,
    continuar: bool = True,
    dry_run: bool = False,
) -> dict[str, Any]:
    act = str(activo or "").strip().upper()
    if not act:
        raise ValueError("activo vacio")
    santo_dir = RANGO_DIR / act
    santo_dir.mkdir(parents=True, exist_ok=True)
    out_log = santo_dir / "manos_piedra_stdout.log"
    err_log = santo_dir / "manos_piedra_stderr.log"
    tag = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    if dry_run:
        return {"activo": act, "dry_run": True, "continuar": continuar}

    env = {**os.environ}
    env["BERU_MAR"] = "okx"
    env["BERU_RANGO_PERFIL"] = "piedra"
    env["BERU_RANGO_MANOS"] = "true"
    env["MODO_SIMULACION"] = "false"
    env["IGRIS_FORCE_MAX_LEVERAGE"] = "true"
    env["PYTHONUTF8"] = "1"

    cmd = [
        sys.executable,
        "-u",
        str(ROOT / "scripts" / "arise_beru_rango_manos.py"),
        "--activo",
        act,
        "--perfil",
        "piedra",
        "--manos-go",
        "--continuar" if continuar else "--desde-cero",
    ]
    with out_log.open("a", encoding="utf-8") as fo, err_log.open("a", encoding="utf-8") as fe:
        fo.write(f"\n=== VIGILANTE_FLOTA {tag} continuar={continuar} ===\n")
        proc = subprocess.Popen(
            cmd,
            cwd=str(ROOT),
            env=env,
            stdout=fo,
            stderr=fe,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    manifest = LOG_DIR / "relanzos_manifest.jsonl"
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    row = {
        "ts_utc": _ahora_utc(),
        "activo": act,
        "pid": proc.pid,
        "continuar": continuar,
        "tag": tag,
    }
    with manifest.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    reg = _leer_pids_registro()
    reg[act] = int(proc.pid)
    _guardar_pids_registro(reg)
    return row


def tick_flota(
    *,
    dry_run: bool = False,
    escalon_s: float = 30.0,
    max_relanzar_por_tick: int = 15,
) -> dict[str, Any]:
    esperados = flota_esperada()
    esperado_set = set(esperados)
    net_ok, net_nota = internet_ok()

    vivo_raw = escanear_manos_piedra()
    limpio, dedupe_acciones = dedupe_manos(vivo_raw, dry_run=dry_run)

    faltan = [a for a in esperados if a not in limpio]
    extras = [a for a in limpio if a not in esperado_set]

    relanzados: list[dict[str, Any]] = []
    if net_ok and faltan and not dry_run:
        lote = faltan[: max(1, int(max_relanzar_por_tick))]
    elif net_ok and faltan and dry_run:
        lote = faltan[: max(1, int(max_relanzar_por_tick))]
    else:
        lote = []

    for i, act in enumerate(lote):
        try:
            row = lanzar_manos_piedra(act, continuar=True, dry_run=dry_run)
            relanzados.append(row)
        except Exception as exc:
            relanzados.append({"activo": act, "error": str(exc)})
        if i < len(lote) - 1 and escalon_s > 0 and not dry_run:
            time.sleep(float(escalon_s))

    informe = {
        "ts_utc": _ahora_utc(),
        "flota_esperada": len(esperados),
        "manos_vivas": len(limpio),
        "duplicados_purgados": len(dedupe_acciones),
        "faltan": faltan,
        "extras": extras,
        "internet_ok": net_ok,
        "internet_nota": net_nota,
        "relanzados_este_tick": relanzados,
        "pct_cobertura": round(100.0 * len(limpio) / max(1, len(esperados)), 1),
        "dry_run": bool(dry_run),
    }
    if not dry_run:
        INFORME_PATH.write_text(
            json.dumps(informe, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    return informe


def adquirir_lock() -> bool:
    LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    if LOCK_PATH.is_file():
        try:
            old = int(LOCK_PATH.read_text(encoding="utf-8").strip())
            # Proceso muerto -> lock obsoleto (Windows: sin psutil, intentar tasklist)
            ps = f"Get-Process -Id {old} -ErrorAction SilentlyContinue"
            chk = subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps],
                capture_output=True,
                text=True,
            )
            if chk.returncode == 0 and chk.stdout.strip():
                return False
        except (ValueError, OSError):
            pass
    LOCK_PATH.write_text(str(os.getpid()), encoding="utf-8")
    return True


def liberar_lock() -> None:
    try:
        if LOCK_PATH.is_file():
            cur = int(LOCK_PATH.read_text(encoding="utf-8").strip())
            if cur == os.getpid():
                LOCK_PATH.unlink(missing_ok=True)
    except (ValueError, OSError):
        pass


def matar_todas_manos(*, dry_run: bool = False) -> list[dict[str, Any]]:
    """Apaga manos piedra: registro local + taskkill (sin CIM lento)."""
    acciones: list[dict[str, Any]] = []
    reg = _leer_pids_registro()
    for act, pid in sorted(reg.items()):
        ok = matar_pid(int(pid), dry_run=dry_run)
        acciones.append({"accion": "matar", "activo": act, "pid": int(pid), "ok": ok})
    # Orphans: un solo wmic (mejor esfuerzo; bytes para evitar CP1252).
    if not dry_run:
        try:
            subprocess.run(
                [
                    "wmic", "process", "where",
                    "CommandLine like '%arise_beru_rango_manos%'",
                    "call", "terminate",
                ],
                capture_output=True,
                timeout=45,
            )
            acciones.append({"accion": "wmic_terminate_arise", "ok": True})
        except (OSError, subprocess.TimeoutExpired) as exc:
            acciones.append({"accion": "wmic_terminate_arise", "ok": False, "error": str(exc)})
    if not dry_run:
        _guardar_pids_registro({})
    return acciones


def reiniciar_flota(
    *,
    dry_run: bool = False,
    escalon_s: float = 1.0,
    max_por_lote: int = 25,
    pausa_entre_lotes_s: float = 3.0,
) -> dict[str, Any]:
    """Mata manos vivas y relanza toda la flota con --continuar (codigo nuevo)."""
    esperados = flota_esperada()
    net_ok, net_nota = internet_ok()
    print(f"[FLOTA] matando manos (reg={len(_leer_pids_registro())})…", flush=True)
    muertos = matar_todas_manos(dry_run=dry_run)
    print(f"[FLOTA] muertos_intentos={len(muertos)} net={'OK' if net_ok else 'NO'}", flush=True)
    if not dry_run:
        time.sleep(1.5)

    relanzados: list[dict[str, Any]] = []
    if not net_ok:
        informe = {
            "ts_utc": _ahora_utc(),
            "modo": "reinicio",
            "internet_ok": False,
            "internet_nota": net_nota,
            "muertos": len(muertos),
            "relanzados": [],
            "faltan": esperados,
            "dry_run": bool(dry_run),
        }
        if not dry_run:
            INFORME_PATH.write_text(
                json.dumps(informe, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
        return informe

    lote_n = max(1, int(max_por_lote))
    n = len(esperados)
    for i, act in enumerate(esperados):
        try:
            row = lanzar_manos_piedra(act, continuar=True, dry_run=dry_run)
            relanzados.append(row)
        except Exception as exc:
            relanzados.append({"activo": act, "error": str(exc)})
        if (i + 1) % 10 == 0 or (i + 1) == n:
            print(f"[FLOTA] lanzados {i + 1}/{n}", flush=True)
        if i < n - 1 and escalon_s > 0 and not dry_run:
            time.sleep(float(escalon_s))
        if (i + 1) % lote_n == 0 and i + 1 < n and not dry_run:
            time.sleep(max(0.0, float(pausa_entre_lotes_s)))

    # Cobertura por registro (rapido); no CIM
    reg = _leer_pids_registro()
    vivos = {a: p for a, p in reg.items() if _pid_vivo(int(p))}
    _guardar_pids_registro(vivos)
    faltan = [a for a in esperados if a not in vivos]
    informe = {
        "ts_utc": _ahora_utc(),
        "modo": "reinicio",
        "internet_ok": True,
        "internet_nota": net_nota,
        "flota_esperada": n,
        "muertos": len(muertos),
        "relanzados": len([r for r in relanzados if r.get("pid") or r.get("dry_run")]),
        "manos_vivas": len(vivos),
        "faltan": faltan,
        "pct_cobertura": round(100.0 * len(vivos) / max(1, n), 1),
        "dry_run": bool(dry_run),
        "detalle_relanzados": relanzados[:30],
    }
    if not dry_run:
        INFORME_PATH.write_text(
            json.dumps(informe, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    return informe
