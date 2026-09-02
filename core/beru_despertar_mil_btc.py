"""Reloj BTC por mil — cola despertar piedra (1 rojo + 1 amarillo por cruce de zona).

Doctrina: cada Santo despierta en proceso propio (sin fila compartida).
"""
from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import core.config as config

DEFAULT_STATE = Path(__file__).resolve().parents[1] / "data" / "beru" / "rango" / "despertar_mil_btc.json"
DEFAULT_ASIG = Path(__file__).resolve().parents[1] / "data" / "beru" / "rango" / "piedra_asignacion.json"


def ruta_estado() -> Path:
    raw = os.getenv("BERU_DESPERTAR_MIL_BTC_PATH") or getattr(
        config, "BERU_DESPERTAR_MIL_BTC_PATH", ""
    )
    return Path(raw) if raw else DEFAULT_STATE


def ruta_asignacion() -> Path:
    raw = os.getenv("BERU_RANGO_PIEDRA_ASIGNACION_PATH") or getattr(
        config, "BERU_RANGO_PIEDRA_ASIGNACION_PATH", ""
    )
    return Path(raw) if raw else DEFAULT_ASIG


def zona_mil(precio: float) -> int:
    """Banda de mil: 78_543 → 78_000; 77_999 → 77_000."""
    p = float(precio or 0)
    if p <= 0:
        return 0
    return int(p // 1000) * 1000


def cruces_zona(
    precio_prev: float,
    precio_nuevo: float,
    *,
    paso: int = 1000,
) -> list[dict[str, Any]]:
    """Lista de cruces al cambiar de banda (cada uno dispara un par rojo+amarillo)."""
    z0 = zona_mil(precio_prev)
    z1 = zona_mil(precio_nuevo)
    if z0 <= 0 or z1 <= 0 or z0 == z1:
        return []
    out: list[dict[str, Any]] = []
    if z1 > z0:
        z = z0 + paso
        while z <= z1:
            out.append({"zona_mil": z, "direccion": "arriba", "paso_usd": paso})
            z += paso
    else:
        z = z0 - paso
        while z >= z1:
            out.append({"zona_mil": z, "direccion": "abajo", "paso_usd": paso})
            z -= paso
    return out


def _ahora_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _estado_vacio() -> dict[str, Any]:
    return {
        "meta": {
            "descripcion": "Despertar escalonado: cada cruce de mil BTC → 1 rojo + 1 amarillo.",
            "creado_utc": _ahora_utc(),
        },
        "config": {
            "activo_reloj": "BTC",
            "paso_usd": 1000,
            "modo_cruce": "cada_zona",
            "fase": "ojos",
            "mar": "okx",
            "perfil": "piedra",
        },
        "cola": {
            "rojos": [],
            "amarillos": [],
            "idx_rojo": 0,
            "idx_amarillo": 0,
        },
        "sellos_cruce": {},
        "ultimo_precio_btc": 0.0,
        "ultima_zona_mil": 0,
        "historial": [],
        "procesos_vivos": [],
    }


def cargar_estado(ruta: Path | None = None) -> dict[str, Any]:
    path = Path(ruta) if ruta else ruta_estado()
    if not path.is_file():
        return _estado_vacio()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else _estado_vacio()
    except (OSError, json.JSONDecodeError):
        return _estado_vacio()


def guardar_estado(data: dict[str, Any], ruta: Path | None = None) -> Path:
    path = Path(ruta) if ruta else ruta_estado()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)
    return path


def cola_desde_asignacion(asig_path: Path | None = None) -> tuple[list[str], list[str]]:
    path = Path(asig_path) if asig_path else ruta_asignacion()
    data = json.loads(path.read_text(encoding="utf-8"))
    rojos: list[str] = []
    amarillos: list[str] = []
    verdes: list[str] = []
    for base, row in sorted((data.get("activos") or {}).items()):
        if not isinstance(row, dict):
            continue
        sem = str(row.get("semaforo") or "").strip().lower()
        act = str(base).upper()
        if sem == "rojo":
            rojos.append(act)
        elif sem == "amarillo":
            amarillos.append(act)
        elif sem == "verde":
            verdes.append(act)
    return rojos, amarillos


def inicializar_estado(
    *,
    asig_path: Path | None = None,
    paso_usd: int = 1000,
    modo_cruce: str = "cada_zona",
    fase: str = "ojos",
    precio_btc: float | None = None,
) -> dict[str, Any]:
    rojos, amarillos = cola_desde_asignacion(asig_path)
    st = _estado_vacio()
    st["config"]["paso_usd"] = int(paso_usd)
    st["config"]["modo_cruce"] = str(modo_cruce or "cada_zona")
    st["config"]["fase"] = str(fase or "ojos")
    st["cola"]["rojos"] = rojos
    st["cola"]["amarillos"] = amarillos
    st["cola"]["idx_rojo"] = 0
    st["cola"]["idx_amarillo"] = 0
    st["meta"]["n_rojos"] = len(rojos)
    st["meta"]["n_amarillos"] = len(amarillos)
    st["meta"]["inicializado_utc"] = _ahora_utc()
    if precio_btc and float(precio_btc) > 0:
        st["ultimo_precio_btc"] = float(precio_btc)
        st["ultima_zona_mil"] = zona_mil(float(precio_btc))
    return st


def _cruce_permitido(st: dict[str, Any], cruce: dict[str, Any]) -> bool:
    modo = str((st.get("config") or {}).get("modo_cruce") or "cada_zona")
    if modo == "cada_zona":
        return True
    sellos = st.get("sellos_cruce") or {}
    if modo == "unico":
        key = f"z{int(cruce.get('zona_mil') or 0)}"
    else:
        key = f"z{int(cruce.get('zona_mil') or 0)}:{cruce.get('direccion')}"
    return not bool(sellos.get(key))


def _marcar_sello(st: dict[str, Any], cruce: dict[str, Any]) -> None:
    modo = str((st.get("config") or {}).get("modo_cruce") or "cada_zona")
    if modo == "cada_zona":
        return
    sellos = st.setdefault("sellos_cruce", {})
    if modo == "unico":
        key = f"z{int(cruce.get('zona_mil') or 0)}"
    else:
        key = f"z{int(cruce.get('zona_mil') or 0)}:{cruce.get('direccion')}"
    sellos[key] = _ahora_utc()


def siguiente_par(st: dict[str, Any]) -> tuple[str | None, str | None]:
    cola = st.get("cola") or {}
    rojos = list(cola.get("rojos") or [])
    amarillos = list(cola.get("amarillos") or [])
    ir = int(cola.get("idx_rojo") or 0)
    ia = int(cola.get("idx_amarillo") or 0)
    rojo = rojos[ir] if ir < len(rojos) else None
    amarillo = amarillos[ia] if ia < len(amarillos) else None
    return rojo, amarillo


def avanzar_cola(st: dict[str, Any]) -> None:
    cola = st.setdefault("cola", {})
    ir = int(cola.get("idx_rojo") or 0)
    ia = int(cola.get("idx_amarillo") or 0)
    if ir < len(cola.get("rojos") or []):
        cola["idx_rojo"] = ir + 1
    if ia < len(cola.get("amarillos") or []):
        cola["idx_amarillo"] = ia + 1


def procesar_tick(
    st: dict[str, Any],
    precio_btc: float,
) -> list[dict[str, Any]]:
    """Evalúa cruce vs último precio; devuelve eventos a despertar (sin mutar cola)."""
    prev = float(st.get("ultimo_precio_btc") or 0)
    px = float(precio_btc or 0)
    if px <= 0:
        return []
    if prev <= 0:
        st["ultimo_precio_btc"] = px
        st["ultima_zona_mil"] = zona_mil(px)
        return []

    paso = int((st.get("config") or {}).get("paso_usd") or 1000)
    cruces = cruces_zona(prev, px, paso=paso)
    st["ultimo_precio_btc"] = px
    st["ultima_zona_mil"] = zona_mil(px)

    eventos: list[dict[str, Any]] = []
    for cruce in cruces:
        if not _cruce_permitido(st, cruce):
            continue
        rojo, amarillo = siguiente_par(st)
        if not rojo and not amarillo:
            cruce["nota"] = "cola_agotada"
            eventos.append(cruce)
            break
        ev = {
            **cruce,
            "ts_utc": _ahora_utc(),
            "precio_btc": px,
            "rojo": rojo,
            "amarillo": amarillo,
            "fase": str((st.get("config") or {}).get("fase") or "ojos"),
        }
        eventos.append(ev)
        _marcar_sello(st, cruce)
        avanzar_cola(st)
    return eventos


def precio_btc_publico() -> float:
    """Last BTC SWAP USDT público (OKX o Bybit según BERU_MAR)."""
    from core import beru_mar
    from core import beru_rango_ojos as ojos

    sym = "BTCUSDT"
    if beru_mar.es_okx():
        return float(ojos._ticker_publico(sym, mercado="linear") or 0)
    return float(ojos._ticker_publico(sym, mercado="linear") or 0)


def registrar_evento(st: dict[str, Any], ev: dict[str, Any], *, pids: list[dict] | None = None) -> None:
    hist = st.setdefault("historial", [])
    row = dict(ev)
    if pids:
        row["procesos"] = pids
        pv = st.setdefault("procesos_vivos", [])
        pv.extend(pids)
    hist.append(row)
    if len(hist) > 500:
        st["historial"] = hist[-500:]


def lanzar_santo_proceso(
    activo: str,
    *,
    fase: str = "ojos",
    manos_go: bool = False,
    segundos: float = 0,
    log_dir: Path | None = None,
) -> dict[str, Any]:
    """Un Santo = un subprocess (ojos o manos). Sin fila API compartida."""
    import subprocess
    from datetime import datetime, timezone

    root = Path(__file__).resolve().parents[1]
    act = str(activo or "").strip().upper()
    if not act:
        raise ValueError("activo vacío")
    fase = str(fase or "ojos").lower()
    log_dir = Path(log_dir) if log_dir else root / "data" / "beru" / "rango" / "despertar_mil"
    log_dir.mkdir(parents=True, exist_ok=True)
    manifest = log_dir / "procesos_manifest.jsonl"
    tag = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out = log_dir / f"{fase}_{act}_{tag}_stdout.log"
    err = log_dir / f"{fase}_{act}_{tag}_stderr.log"

    env = {**os.environ}
    env["BERU_MAR"] = str(env.get("BERU_MAR") or "okx")
    env["BERU_RANGO_PERFIL"] = str(env.get("BERU_RANGO_PERFIL") or "piedra")
    env["PYTHONUTF8"] = "1"
    if fase == "manos" and manos_go:
        env["BERU_RANGO_MANOS"] = "true"
        env["MODO_SIMULACION"] = str(env.get("MODO_SIMULACION") or "false")
    else:
        env["BERU_RANGO_MANOS"] = "false"
        env["MODO_SIMULACION"] = "true"

    if fase == "manos":
        if not manos_go:
            raise ValueError("manos requiere manos_go=True")
        script = root / "scripts" / "arise_beru_rango_manos.py"
        cmd = [sys.executable, "-u", str(script), "--activo", act, "--manos-go"]
    else:
        script = root / "scripts" / "arise_beru_rango_ojos.py"
        cmd = [sys.executable, "-u", str(script), "--activo", act]
    if segundos > 0:
        cmd.extend(["--segundos", str(segundos)])

    proc = subprocess.Popen(
        cmd,
        cwd=str(root),
        env=env,
        stdout=out.open("a", encoding="utf-8"),
        stderr=err.open("a", encoding="utf-8"),
    )
    row = {
        "ts_utc": datetime.now(timezone.utc).isoformat(),
        "activo": act,
        "fase": fase,
        "pid": proc.pid,
        "stdout": str(out),
        "stderr": str(err),
    }
    with manifest.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    return row
