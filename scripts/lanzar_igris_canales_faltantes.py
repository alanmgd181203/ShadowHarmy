#!/usr/bin/env python3
"""Lanza Igris 1-en-1 sobre Santos faltantes (serie, no paralelo).

Orden Monarca 2026-08-11 noche: ADA → BCH → MNT.
Cierra grados del Santo activo antes de pasar al siguiente (oxígeno justo).
No cancela posiciones; no toca bóveda MNTPERP/MNTUSDC.
"""
from __future__ import annotations

import argparse
import os
import signal
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# Casi llenos primero; MNT Cap/Gen/Mar al final (más nocional).
ORDEN_SERIE = ("ADA", "BCH", "MNT")
POLL_S = 45


def _base_env() -> dict[str, str]:
    env = os.environ.copy()
    for k in list(env):
        if "proxy" in k.lower():
            env.pop(k, None)
    env.update(
        {
            "PYTHONUNBUFFERED": "1",
            "IGRIS_BOVEDA_EN_LOTE": "true",
            "IGRIS_BOVEDA_BASES": "",
            "IGRIS_PROTEGER_BASES": "",
            "IGRIS_PROTEGER_SYMBOLS": "MNTPERP,MNTUSDC",
            "IGRIS_MNT_HEDGE_OBLIGATORIO": "false",
            "IGRIS_LIBRO_STALE_S": "45",
            "IGRIS_LIBRO_REST_FALLBACK": "true",
            "IGRIS_LIBRO_REST_COOLDOWN_S": "8",
            "IGRIS_LIBRO_DIVERGENCIA_ASALTO_PCT": "2.5",
            "IGRIS_MASA_ASIMETRIA_ASALTO_PCT": "0.12",
            "IGRIS_ASALTO_OVERSHOOT_META": "true",
            "IGRIS_FORCE_MAX_LEVERAGE": "true",
            "IGRIS_PODA_AUTO": "false",
            "IGRIS_ENGORDE_RITMO_S": "2",
            "ARISE_IGRIS_CALENTAMIENTO_S": "120",
            "BRIDGE_WS_OPEN_TIMEOUT_S": "60",
            "BRIDGE_WS_INVALIDAR_ON_DROP": "true",
            "BRIDGE_WS_SUBSCRIBE_BOOKS": "true",
            "ESCALERA_IGRIS_ACTIVA": "false",
            "MODO_TESTNET": "False",
            "MODO_SIMULACION": "False",
        }
    )
    return env


def _py() -> str:
    cand = ROOT / ".venv" / "bin" / "python3"
    return str(cand) if cand.exists() else sys.executable


def _log_dir(act: str) -> Path:
    d = ROOT / "data" / "logs" / "arise_igris" / act
    d.mkdir(parents=True, exist_ok=True)
    return d


def _pid_path(act: str) -> Path:
    return _log_dir(act) / "orquestador.pid"


def _stamp(act: str, msg: str) -> None:
    p = _log_dir(act) / "orquestador.log"
    with p.open("a", encoding="utf-8") as f:
        f.write(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] [MONARCA] {msg}\n")


def _leer_pid(act: str) -> int | None:
    f = _pid_path(act)
    if not f.exists():
        return None
    try:
        return int(f.read_text(encoding="utf-8").strip().split()[0])
    except Exception:
        return None


def _vivo(pid: int | None) -> bool:
    if not pid:
        return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def detener_canal(act: str) -> None:
    """Solo ritual Igris — no toca Bybit."""
    pid = _leer_pid(act)
    kids: list[int] = []
    if pid and _vivo(pid):
        try:
            out = subprocess.check_output(["pgrep", "-P", str(pid)], text=True)
            kids = [int(x) for x in out.split() if x.strip().isdigit()]
        except Exception:
            kids = []
        for p in [pid] + kids:
            try:
                os.kill(p, signal.SIGTERM)
            except OSError:
                pass
        time.sleep(1.5)
        for p in [pid] + kids:
            if _vivo(p):
                try:
                    os.kill(p, signal.SIGKILL)
                except OSError:
                    pass
    # Barrido por heartbeat pid
    hb = _log_dir(act) / "heartbeat.json"
    if hb.exists():
        try:
            import json

            hpid = int((json.loads(hb.read_text(encoding="utf-8")) or {}).get("pid") or 0)
            if hpid and _vivo(hpid) and hpid != pid:
                os.kill(hpid, signal.SIGTERM)
                time.sleep(1)
                if _vivo(hpid):
                    os.kill(hpid, signal.SIGKILL)
        except Exception:
            pass
    _pid_path(act).unlink(missing_ok=True)
    _stamp(act, f"SERIE: canal {act} detenido.")


def lanzar_canal(act: str, deadline: str) -> int:
    env = _base_env()
    env["IGRIS_FORZAR_EXCLUSIVOS"] = act
    env["ARISE_CANAL"] = act
    log_path = _log_dir(act) / "orquestador.log"
    cmd = [
        "caffeinate",
        "-i",
        _py(),
        "-u",
        str(ROOT / "scripts" / "arise_igris.py"),
        "--durar-hasta",
        deadline,
        "--permitir-mainnet-manos",
    ]
    fout = open(log_path, "a", encoding="utf-8")
    fout.write(
        f"\n##### LANZADOR_SERIE {time.strftime('%Y-%m-%d %H:%M:%S')} {act} #####\n"
    )
    fout.flush()
    proc = subprocess.Popen(
        cmd,
        cwd=str(ROOT),
        stdout=fout,
        stderr=subprocess.STDOUT,
        env=env,
        start_new_session=True,
    )
    _pid_path(act).write_text(str(proc.pid) + "\n", encoding="utf-8")
    _stamp(act, f"SERIE: canal {act} lanzado pid={proc.pid}")
    print(f"lanzado {act} pid={proc.pid} log={log_path}", flush=True)
    return proc.pid


def _equity_approx() -> float:
    try:
        sys.path.insert(0, str(ROOT))
        for k in list(os.environ):
            if "proxy" in k.lower():
                del os.environ[k]
        import core.config as config
        from pybit.unified_trading import HTTP

        s = HTTP(testnet=False, api_key=config.API_KEY, api_secret=config.API_SECRET)
        if hasattr(s, "client"):
            s.client.trust_env = False
            s.client.proxies = {}
        a = ((s.get_wallet_balance(accountType="UNIFIED").get("result") or {}).get("list") or [{}])[0]
        return float(a.get("totalEquity") or 0)
    except Exception as e:
        print(f"equity_fallback err={e}", flush=True)
        return 2200.0


def trabajo_pendiente(act: str, equity: float | None = None) -> list[dict]:
    sys.path.insert(0, str(ROOT))
    from core import pase_director as pd

    eq = float(equity if equity is not None else _equity_approx())
    prog = pd.cargar_progreso()
    logs = list(prog.get("pasos_logrados") or [])
    plan = pd.plan_lote(eq, marcha_id="asalto", pasos_logrados=logs)
    return [p for p in (plan.get("trabajo") or []) if str(p.get("activo") or "").upper() == act.upper()]


def asegurar_solo(act: str, deadline: str, otros: tuple[str, ...]) -> None:
    for o in otros:
        if o != act:
            detener_canal(o)
    pid = _leer_pid(act)
    if not _vivo(pid):
        # heartbeat may own the real python pid
        hb = _log_dir(act) / "heartbeat.json"
        hpid = None
        if hb.exists():
            try:
                import json

                hpid = int((json.loads(hb.read_text(encoding="utf-8")) or {}).get("pid") or 0)
            except Exception:
                hpid = None
        if _vivo(hpid):
            _pid_path(act).write_text(str(hpid) + "\n", encoding="utf-8")
            print(f"reusando {act} pid={hpid}", flush=True)
        else:
            lanzar_canal(act, deadline)


def run_serie(orden: tuple[str, ...], hours: float, solo_ahora: str | None) -> int:
    deadline = (datetime.now() + timedelta(hours=hours)).strftime("%Y-%m-%dT%H:%M:%S")
    print(f"deadline={deadline} orden={','.join(orden)} modo=serie", flush=True)

    if solo_ahora:
        act = solo_ahora.upper()
        asegurar_solo(act, deadline, orden)
        print(f"solo_ahora={act} (sin relevo auto)", flush=True)
        return 0

    for act in orden:
        eq = _equity_approx()
        pend = trabajo_pendiente(act, eq)
        if not pend:
            print(f"{act}: sin trabajo pendiente — salto", flush=True)
            detener_canal(act)
            continue
        print(f"{act}: pendiente {[p.get('etiqueta') or p.get('n') for p in pend]}", flush=True)
        asegurar_solo(act, deadline, orden)
        # Espera a que el libro selle todos los pasos de este Santo en el trabajo
        while True:
            time.sleep(POLL_S)
            eq = _equity_approx()
            pend = trabajo_pendiente(act, eq)
            vivo = _vivo(_leer_pid(act))
            print(
                f"[{time.strftime('%H:%M:%S')}] {act} vivo={vivo} pend={len(pend)} "
                f"{[p.get('n') for p in pend]} eq={eq:.1f}",
                flush=True,
            )
            if not pend:
                print(f"{act}: completo — relevo", flush=True)
                detener_canal(act)
                break
            if not vivo:
                print(f"{act}: proceso caído con pendiente — relanzo", flush=True)
                lanzar_canal(act, deadline)

    print("serie terminada (o sin más trabajo)", flush=True)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Igris canales faltantes en serie")
    ap.add_argument(
        "--orden",
        default=",".join(ORDEN_SERIE),
        help="Orden de Santos (default ADA,BCH,MNT)",
    )
    ap.add_argument("--horas", type=float, default=12.0)
    ap.add_argument(
        "--solo",
        default="",
        help="Solo arranca este Santo ahora (sin bucle de relevo)",
    )
    ap.add_argument(
        "--paralelo",
        action="store_true",
        help="LEGADO: lanza todos a la vez (no recomendado con O₂ bajo)",
    )
    args = ap.parse_args()
    orden = tuple(a.strip().upper() for a in args.orden.split(",") if a.strip())

    if args.paralelo:
        deadline = (datetime.now() + timedelta(hours=args.horas)).strftime(
            "%Y-%m-%dT%H:%M:%S"
        )
        print(f"deadline={deadline} modo=paralelo (legado)", flush=True)
        pids = []
        for act in orden:
            pids.append((act, lanzar_canal(act, deadline)))
            time.sleep(2)
        print("pids=" + ",".join(f"{a}:{p}" for a, p in pids), flush=True)
        return 0

    return run_serie(orden, args.horas, args.solo or None)


if __name__ == "__main__":
    raise SystemExit(main())
