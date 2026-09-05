#!/usr/bin/env python3
"""Vigila BTC por mil — cada cruce despierta 1 rojo + 1 amarillo (proceso propio c/u).

Sin fila API compartida: cada Santo = subprocess independiente.

Arranque:
  python scripts/inicializar_cola_despertar_mil_btc.py
  python scripts/vigilar_btc_mil_despertar.py

Manos (solo con GO):
  python scripts/inicializar_cola_despertar_mil_btc.py --fase manos
  python scripts/vigilar_btc_mil_despertar.py --manos-go

Uso:
  python scripts/vigilar_btc_mil_despertar.py --intervalo 30
  python scripts/vigilar_btc_mil_despertar.py --una-vez --dry-run
"""
from __future__ import annotations

import argparse
import os
import signal
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

os.environ.setdefault("BERU_MAR", "okx")
os.environ.setdefault("BERU_RANGO_PERFIL", "piedra")

from core import beru_despertar_mil_btc as dm


def _despertar_evento(ev: dict, *, manos_go: bool, dry_run: bool, solo_rojos: bool = False) -> list[dict]:
    fase = str(ev.get("fase") or "ojos")
    if manos_go:
        fase = "manos"
    pids: list[dict] = []
    colores = ("rojo",) if solo_rojos else ("rojo", "amarillo")
    for color in colores:
        act = ev.get(color)
        if not act:
            continue
        if dry_run:
            print(f"  [DRY] {fase} {color} -> {act}")
            pids.append({"activo": act, "fase": fase, "dry_run": True})
            continue
        row = dm.lanzar_santo_proceso(
            str(act), fase=fase, manos_go=manos_go and fase == "manos"
        )
        print(f"  [{fase.upper()}] {act} pid={row.get('pid')}")
        pids.append(row)
        time.sleep(0.5)
    return pids


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--intervalo", type=float, default=30.0, help="Segundos entre polls BTC")
    ap.add_argument("--una-vez", action="store_true", help="Un tick y sale")
    ap.add_argument("--dry-run", action="store_true", help="No lanza procesos")
    ap.add_argument("--manos-go", action="store_true", help="Fase manos con GO (capital real)")
    ap.add_argument("--init", action="store_true", help="Re-inicializa cola si falta estado")
    args = ap.parse_args()

    path = dm.ruta_estado()
    if not path.is_file():
        if args.init:
            st = dm.inicializar_estado(precio_btc=dm.precio_btc_publico())
            dm.guardar_estado(st, path)
            print(f"Estado creado: {path}")
        else:
            print(f"Falta {path} — corre inicializar_cola_despertar_mil_btc.py", file=sys.stderr)
            return 1

    stop = False

    def _sig(*_a):
        nonlocal stop
        stop = True

    signal.signal(signal.SIGINT, _sig)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, _sig)

    print("=" * 56)
    print("  VIGILANTE BTC MIL — despertar escalonado piedra OKX")
    print(f"  Estado: {path}")
    print(f"  Intervalo: {args.intervalo}s · manos_go={args.manos_go} · dry_run={args.dry_run}")
    st0 = dm.cargar_estado(path)
    if dm.rojos_manos_total(st0):
        print("  Modo: COLA COMPLETA — flota piedra ya despertada")
    elif dm.amarillos_manos_total(st0):
        print("  Modo: SOLO ROJOS (ojos) — amarillos ya con manos total")
    else:
        print("  Cada cruce: 1 rojo + 1 amarillo · proceso PROPIO por Santo")
    print("=" * 56)

    while not stop:
        st = dm.cargar_estado(path)
        if args.manos_go:
            st.setdefault("config", {})["fase"] = "manos"

        try:
            px = dm.precio_btc_publico()
        except Exception as exc:
            print(f"[MIL] precio BTC error: {exc}", flush=True)
            px = 0.0

        if px <= 0:
            print("[MIL] sin precio BTC — reintento", flush=True)
        else:
            zona = dm.zona_mil(px)
            eventos = dm.procesar_tick(st, px)
            if eventos:
                print(
                    f"\n[MIL] BTC={px:.2f} zona={zona} · {len(eventos)} cruce(s)",
                    flush=True,
                )
                for ev in eventos:
                    if ev.get("nota") == "cola_agotada":
                        print("  [MIL] Cola agotada — no hay más Santos", flush=True)
                        dm.guardar_estado(st, path)
                        return 0
                    print(
                        f"  cruce z={ev.get('zona_mil')} {ev.get('direccion')} "
                        f"-> rojo={ev.get('rojo')}"
                        + ("" if dm.amarillos_manos_total(st) else f" amarillo={ev.get('amarillo')}"),
                        flush=True,
                    )
                    pids = _despertar_evento(
                        ev,
                        manos_go=bool(args.manos_go),
                        dry_run=bool(args.dry_run),
                        solo_rojos=dm.amarillos_manos_total(st) and not dm.rojos_manos_total(st),
                    )
                    dm.registrar_evento(st, ev, pids=pids)
                dm.guardar_estado(st, path)
            else:
                print(
                    f"[MIL] BTC={px:.2f} zona={zona} · sin cruce",
                    flush=True,
                )
                dm.guardar_estado(st, path)

        if args.una_vez:
            break
        try:
            time.sleep(max(5.0, float(args.intervalo)))
        except KeyboardInterrupt:
            break

    print("\n[MIL] Vigilante sellado.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
