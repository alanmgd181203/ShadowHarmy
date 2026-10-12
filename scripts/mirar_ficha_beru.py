#!/usr/bin/env python3
"""Mirar fichas de auditoría Beru (una o flota con alertas).

Uso:
  python scripts/mirar_ficha_beru.py RSR
  python scripts/mirar_ficha_beru.py --alertas
  python scripts/mirar_ficha_beru.py --regenerar --alertas
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core import beru_rango_ficha as ficha
from core import beru_rango_paths as paths


def _regenerar(act: str) -> dict:
    inf = paths.manos_piedra_informe(act)
    informe = None
    if inf.is_file():
        try:
            informe = json.loads(inf.read_text(encoding="utf-8"))
        except Exception:
            informe = None
    ficha.escribir_ficha(act, informe=informe, perfil="piedra")
    return ficha.leer_ficha(act)


def _print_one(d: dict) -> None:
    if not d:
        print("(sin ficha)")
        return
    u = d.get("ultima_orden_ejecutada") or {}
    du = d.get("desde_ultima_orden") or {}
    c = d.get("campana") or {}
    q = d.get("calidad_fills") or {}
    ir = d.get("iron") or {}
    print(
        f"{d.get('activo')} {d.get('estado')} origen={d.get('origen_tramo')} "
        f"redes={c.get('redes_consecutivas')} mem={c.get('engorde_memoria_peldaños')} "
        f"off={c.get('engorde_peldaño_offset')}"
    )
    print(
        f"  ultima_oz edad={u.get('edad_s')}s dir={u.get('dir')} px={u.get('precio')} "
        f"masa={u.get('masa')} | lejos={du.get('pct_humano')}% "
        f"(last={du.get('last')} ref={du.get('precio_ref')})"
    )
    print(
        f"  spread_oz_fill≈{q.get('spread_oz_fill_prom_pct')}% "
        f"camino_oz≈{q.get('camino_entre_oz_prom_pct')}% "
        f"Iron={ir.get('campo')}x{ir.get('factor')} g={ir.get('ganancia_pct')}% "
        f"prox_redΔ={((d.get('masa') or {}).get('proxima_red_delta_est'))}"
    )
    al = d.get("alertas") or []
    print(f"  alertas={al or 'ninguna'} ok={d.get('ok_auditoria')}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("activos", nargs="*", help="Santos (RSR MAGIC …)")
    ap.add_argument("--alertas", action="store_true", help="Solo los que tienen alertas")
    ap.add_argument("--regenerar", action="store_true", help="Reescribe ficha desde informe+eventos")
    ap.add_argument("--limite", type=int, default=40)
    args = ap.parse_args()

    if args.activos:
        acts = [a.strip().upper() for a in args.activos if a.strip()]
    else:
        acts = sorted(
            p.name
            for p in paths.RANGO_DIR.iterdir()
            if p.is_dir() and (p / "manos_piedra_informe.json").is_file()
        )

    n = 0
    for act in acts:
        d = _regenerar(act) if args.regenerar else ficha.leer_ficha(act)
        if args.regenerar is False and not d:
            d = _regenerar(act)
        if args.alertas and not (d.get("alertas") or []):
            continue
        _print_one(d)
        n += 1
        if n >= args.limite:
            break
    if n == 0:
        print("(ninguno)" if args.alertas else "(sin fichas)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
