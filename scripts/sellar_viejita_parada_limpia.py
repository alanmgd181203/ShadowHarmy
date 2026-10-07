#!/usr/bin/env python3
"""Sellar viejita PARADA y LIMPIA — cableado OK, todo OFF, sin memoria de escudo.

NO despierta Santos. NO abre manos. NO enciende LIVE_OK ni ACTIVO.

Uso (al prender la lap, antes de cualquier arise)::

  python scripts/sellar_viejita_parada_limpia.py
"""
from __future__ import annotations

import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Limpiar knobs de sesión que pudieran haber quedado de un ritual previo
for _k in list(os.environ.keys()):
    if _k.startswith("IGRIS_ESCUDO") or _k == "IGRIS_ESCUDO_BTC_LIVE_OK":
        # No borrar del .env; solo no forzar ON en este proceso
        pass


def main() -> int:
    from core import config as cfg
    from core import igris_escudo_btc as escudo
    from core import beru_rango_paths as paths

    # Memoria del manto → 0
    libro = escudo.resetear_libro_escudo(motivo="viejita_parada_limpia")

    # Verificar manos cableadas (import) sin disparar
    manos_ok = False
    try:
        from core import igris_escudo_manos_okx  # noqa: F401

        manos_ok = True
    except Exception as exc:
        print(f"AVISO: manos OKX no importan: {exc}", flush=True)

    hora = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    activo = bool(getattr(cfg, "IGRIS_ESCUDO_BTC_ACTIVO", False))
    modo = str(getattr(cfg, "IGRIS_ESCUDO_BTC_MODO", "sim") or "sim")
    live = escudo.escudo_live_permitido()
    live_env = str(os.getenv("IGRIS_ESCUDO_BTC_LIVE_OK", "") or "")

    print("", flush=True)
    print("=" * 56, flush=True)
    print("  VIEJITA — PARADA · LIMPIA · CABLEADA", flush=True)
    print(f"  {hora}", flush=True)
    print("=" * 56, flush=True)
    print("", flush=True)
    print("Memoria escudo:", flush=True)
    print(f"  · Libro en 0 · peldaño_armado=False · sin límite pendiente", flush=True)
    print(f"  · {paths.escudo_btc_sim()}", flush=True)
    print("", flush=True)
    print("Cableado (listo, dormido):", flush=True)
    print(f"  · Frente {escudo.escudo_familia()} → {escudo.inst_escudo_btc()}", flush=True)
    print(
        f"  · Peldaños ${escudo.escudo_peldaño_usd():.0f} · arma @ ${escudo.escudo_activar_usd():.0f}",
        flush=True,
    )
    print(
        f"  · Órdenes {escudo.escudo_ord_tipo()} · mover si no llena="
        f"{escudo.escudo_limit_mover_activo()}",
        flush=True,
    )
    print(f"  · Manos OKX cableadas: {'sí' if manos_ok else 'NO'}", flush=True)
    print(f"  · R: poner dinamico al despertar con --con-escudo", flush=True)
    print("", flush=True)
    print("Apagado (debe ser todo OFF ahora):", flush=True)
    print(f"  · ACTIVO escudo = {activo}  (debe False)", flush=True)
    print(f"  · MODO = {modo}  (debe sim)", flush=True)
    print(f"  · LIVE_OK = {bool(live)} env={live_env!r}  (debe vacío/False)", flush=True)
    print(f"  · Libro papel = {libro.escudo_signed_usd}", flush=True)
    print("", flush=True)

    fallos = []
    if activo:
        fallos.append("ACTIVO sigue ON — apaga IGRIS_ESCUDO_BTC_ACTIVO")
    if modo == "live":
        fallos.append("MODO=live — vuelve a sim")
    if live or live_env.strip() in ("1", "true", "yes", "si"):
        fallos.append("LIVE_OK encendido — quítalo del entorno/.env")
    if not manos_ok:
        fallos.append("manos OKX no cargan")

    if fallos:
        print("NO LISTO:", flush=True)
        for f in fallos:
            print(f"  · {f}", flush=True)
        print("=" * 56, flush=True)
        return 2

    print("Estado: ejercito DORMIDO · escudo CABLEADO · sin memoria · sin peaje.", flush=True)
    print("", flush=True)
    print("Cuando el Monarca diga GO (despertar limpio en papel primero):", flush=True)
    print(
        "  python scripts/arise_beru_rango_campamento.py "
        "--santos A,B,... --manos-go --desde-cero --con-escudo",
        flush=True,
    )
    print("  (BTC real: solo con LIVE_OK=1 + MODO=live + orden explicita)", flush=True)
    print("=" * 56, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
