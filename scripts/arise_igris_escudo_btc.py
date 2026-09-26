#!/usr/bin/env python3
"""ARISE Igris Escudo BTC — vive con la balanza de Beru (viejita).

Lee balanza L/S (sin BTC) → peldaños → meta BTC inverso OKX.
Órdenes a market por defecto (Monarca 2026-09-24). Limit solo si se fuerza.

Candados (env):
  IGRIS_ESCUDO_BTC_ACTIVO=1
  IGRIS_ESCUDO_BTC_MODO=live|sim
  IGRIS_ESCUDO_BTC_LIVE_OK=1   # obligatorio para manos reales
  IGRIS_ESCUDO_BTC_ORD_TIPO=market
  IGRIS_ESCUDO_BTC_R=dinamico
  IGRIS_ESCUDO_BTC_FRENTE=inverso

Uso::
  python scripts/arise_igris_escudo_btc.py
  python scripts/arise_igris_escudo_btc.py --intervalo 45
  python scripts/arise_igris_escudo_btc.py --sim   # fuerza papel
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

_LOG = ROOT / "data" / "logs" / "arise_igris_escudo_out.log"


def _emit(msg: str) -> None:
    """Escribe al stdout (y al log si no está ya redirigido por el ritual)."""
    print(msg, flush=True)
    # Si el ritual ya redirige stdout al log, no reabrir el mismo archivo
    # (en Windows el doble handle tumba el proceso).
    if os.environ.get("IGRIS_ESCUDO_LOG_SOLO_STDOUT", "").strip() in (
        "1",
        "true",
        "yes",
        "on",
        "si",
    ):
        return
    try:
        _LOG.parent.mkdir(parents=True, exist_ok=True)
        with _LOG.open("a", encoding="utf-8") as fh:
            fh.write(msg + "\n")
    except Exception:
        pass


def _boot_env(*, forzar_sim: bool) -> None:
    os.environ.setdefault("BERU_MAR", "okx")
    os.environ["IGRIS_ESCUDO_BTC_ACTIVO"] = "1"
    os.environ.setdefault("IGRIS_ESCUDO_BTC_R", "dinamico")
    os.environ.setdefault("IGRIS_ESCUDO_BTC_FRENTE", "inverso")
    # Monarca: entradas a mercado (fill inmediato). Limit solo si se fuerza.
    os.environ["IGRIS_ESCUDO_BTC_ORD_TIPO"] = (
        os.environ.get("IGRIS_ESCUDO_BTC_ORD_TIPO") or "market"
    )
    # Chase más ágil (solo aplica si ORD_TIPO=limit).
    os.environ.setdefault("IGRIS_ESCUDO_BTC_LIMIT_ESPERA_S", "8")
    os.environ.setdefault("IGRIS_ESCUDO_BTC_LIMIT_PASO_PCT", "0.0015")
    os.environ.setdefault("IGRIS_ESCUDO_BTC_LIMIT_MAX_DRIFT_PCT", "0.02")
    os.environ.setdefault("IGRIS_ESCUDO_BTC_LIMIT_MAX_MOVES", "40")
    os.environ.setdefault("IGRIS_ESCUDO_BTC_LIMIT_OFFSET_PCT", "0.00015")
    if forzar_sim:
        os.environ["IGRIS_ESCUDO_BTC_MODO"] = "sim"
        os.environ.pop("IGRIS_ESCUDO_BTC_LIVE_OK", None)
    else:
        # Forzar live de esta sesión (no dejar que .env viejo deje sim).
        os.environ["IGRIS_ESCUDO_BTC_MODO"] = "live"
        os.environ["IGRIS_ESCUDO_BTC_LIVE_OK"] = "1"


def main() -> int:
    ap = argparse.ArgumentParser(description="ARISE Igris Escudo BTC")
    ap.add_argument("--intervalo", type=float, default=15.0)
    ap.add_argument("--sim", action="store_true", help="Forzar papel (sin LIVE_OK)")
    ap.add_argument("--una-vez", action="store_true")
    args = ap.parse_args()

    _boot_env(forzar_sim=bool(args.sim))

    from core import beru_rango_balanza as balanza
    from core import igris_escudo_btc as escudo

    # Preferir env de esta sesión (viejita) sobre config cacheada al import.
    modo_env = str(os.environ.get("IGRIS_ESCUDO_BTC_MODO", "") or "").strip().lower()
    modo = "sim" if args.sim else (modo_env or "live")
    if modo != "live":
        modo = "sim"
    live_ok = escudo.escudo_live_permitido() if modo == "live" else False

    _emit("=" * 56)
    _emit("  ARISE IGRIS ESCUDO BTC")
    _emit(f"  frente={escudo.escudo_familia()} {escudo.inst_escudo_btc()}")
    _emit(
        f"  peldano=${escudo.escudo_peldaño_usd():.0f} arma@${escudo.escudo_activar_usd():.0f} "
        f"R={escudo.escudo_relacion():.2f} ord={escudo.escudo_ord_tipo()}"
    )
    _emit(f"  modo={modo} LIVE_OK={live_ok} intervalo={args.intervalo}s")
    _emit("=" * 56)

    if modo == "live" and not live_ok:
        _emit("FALLO: modo live sin LIVE_OK — aborto")
        return 2

    while True:
        hora = datetime.now().strftime("%H:%M:%S")
        try:
            snap = balanza.sellar_balanza()
            lat = escudo.latido_escudo(
                snap=snap,
                ojos_live=False,
                forzar_modo=modo,
                aplicar_manos=True,
            )
            frase = escudo.frase_latido(lat)
            mov = (lat.get("mover_limite") or {}).get("frase") or ""
            bal = snap.get("frase") or ""
            r_ahora = escudo.escudo_relacion()
            _emit(f"[{hora}] balanza · {bal}")
            _emit(f"[{hora}] R={r_ahora:.2f} (dinamico, viejita)")
            _emit(f"[{hora}] escudo  · {frase}")
            if mov:
                _emit(f"[{hora}] limite  · {mov}")
            manos = lat.get("manos") or {}
            if manos.get("frase") and manos.get("aplicado"):
                _emit(f"[{hora}] manos   · {manos.get('frase')}")
            elif manos.get("aviso") and not manos.get("ok"):
                _emit(f"[{hora}] manos   · {manos.get('aviso')}")
        except Exception as exc:
            _emit(f"[{hora}] error: {exc}")

        if args.una_vez:
            return 0
        time.sleep(max(10.0, float(args.intervalo)))


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\nIgris Escudo sellado.", flush=True)
        raise SystemExit(0)
