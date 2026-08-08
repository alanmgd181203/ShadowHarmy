#!/usr/bin/env python3
"""Sincroniza mínimos de orden Bybit → data/bybit_minimos_orden.json (+ G_min por Santo).

Solo ojos: instruments-info + tickers. SIN manos, SIN órdenes.
Reanudable: escribe al terminar; si cae a mitad, relanzar.

Uso:
  python scripts/sync_bybit_minimos_orden.py
  python scripts/sync_bybit_minimos_orden.py --flota-only
  python scripts/sync_bybit_minimos_orden.py --no-prices
  python scripts/sync_bybit_minimos_orden.py --also-parametros
  python scripts/sync_bybit_minimos_orden.py --from-parametros   # sin red: deriva de BD vieja
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT_PATH = ROOT / "data" / "bybit_minimos_orden.json"
PARAM_PATH = ROOT / "data" / "bybit_parametros_mercado.json"


def _load_bpm():
    path = ROOT / "scripts" / "bybit_parametros_mercado.py"
    spec = importlib.util.spec_from_file_location("bybit_parametros_mercado", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"no load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _f(x: Any) -> float | None:
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return v if v > 0 else None


def _slim_pierna(row: dict[str, Any] | None) -> dict[str, Any] | None:
    if not row:
        return None
    return {
        "symbol": row.get("symbol"),
        "category": row.get("category"),
        "minQty": row.get("minOrderQty"),
        "qtyStep": row.get("qtyStep"),
        "minNotional": row.get("minNotionalValue"),
        "minOrderAmt": row.get("minNotionalValue"),  # spot suele mapear aquí en lotSizeFilter
        "precio_ref": row.get("precio_ref"),
        "min_usd_est": row.get("min_usd_est"),
        "min_usd_como": row.get("min_usd_como"),
        "maxLeverage": row.get("maxLeverage"),
        "tickSize": row.get("tickSize"),
    }


def _elegir_g_min(spot: dict | None, lin: dict | None, inv: dict | None, piso: float) -> tuple[float | None, str]:
    for label, pierna in (("spot_usdt", spot), ("linear", lin), ("inverse", inv)):
        if not pierna:
            continue
        v = _f(pierna.get("min_usd_est"))
        if v is None:
            v = _f(pierna.get("minNotional")) or _f(pierna.get("minOrderAmt"))
        if v is not None:
            return max(v, piso), label
    return None, "sin_dato"


def bases_objetivo(*, flota_only: bool, db_activos: dict[str, Any]) -> set[str]:
    import core.config as config

    flota = {str(a).upper() for a in (getattr(config, "ACTIVOS_BERU_FLOTA", None) or [])}
    if flota_only:
        return flota or {"ETH", "BTC"}
    return set(db_activos.keys()) | flota


def construir_minimos_desde_parametros(
    db: dict[str, Any],
    *,
    flota_only: bool = False,
    piso: float = 1.0,
    advertencia: str | None = None,
) -> dict[str, Any]:
    activos_in = db.get("activos") or {}
    bases = sorted(bases_objetivo(flota_only=flota_only, db_activos=activos_in))
    activos_out: dict[str, Any] = {}
    for base in bases:
        fila = activos_in.get(base) or {}
        spot = _slim_pierna(fila.get("spot_usdt"))
        lin = _slim_pierna(fila.get("linear"))
        inv = _slim_pierna(fila.get("inverse"))
        g, fuente = _elegir_g_min(spot, lin, inv, piso)
        activos_out[base] = {
            "spot_usdt": spot,
            "linear": lin,
            "inverse": inv,
            "G_min": g,
            "G_min_fuente": fuente,
            "en_flota_manto": bool(fila.get("en_flota_manto")),
        }

    meta = {
        "ts_utc": datetime.now(timezone.utc).isoformat(),
        "fuente": "derivado_de_bybit_parametros_mercado" if advertencia else "Bybit instruments-info + tickers",
        "piso_configurable": piso,
        "n_activos": len(activos_out),
        "nota": (
            "G_min Beru = mínimo rail spot USDT si existe; si no, linear; piso configurable. "
            "Pase/ranking NO regenerado por este sync."
        ),
    }
    if advertencia:
        meta["advertencia"] = advertencia
        meta["ts_parametros"] = (db.get("meta") or {}).get("ts_utc")
    return {"meta": meta, "activos": activos_out}


def sync_vivo(*, flota_only: bool, no_prices: bool, piso: float, also_parametros: bool) -> dict[str, Any]:
    bpm = _load_bpm()
    print("Sync minimos — pidiendo instruments-info a Bybit...")
    t0 = time.time()
    linear = bpm.page_instruments("linear", quote_coin="USDT")
    print(f"  linear={len(linear)}")
    inverse = bpm.page_instruments("inverse")
    print(f"  inverse={len(inverse)}")
    spot_usdt = bpm.page_instruments("spot", quote_coin="USDT")
    print(f"  spot USDT={len(spot_usdt)}")
    spot_usdc = bpm.page_instruments("spot", quote_coin="USDC")
    print(f"  spot USDC={len(spot_usdc)}")

    db = bpm.construir_base_parametros(
        linear=linear,
        inverse=inverse,
        spot_usdt=spot_usdt,
        spot_usdc=spot_usdc,
        fetch_prices=not no_prices,
    )
    elapsed = time.time() - t0
    print(f"  armado BD en {elapsed:.1f}s · bases={db['meta']['n_bases']}")

    if also_parametros:
        path_p = bpm.guardar_base(db, PARAM_PATH)
        print(f"  tambien -> {path_p}")

    out = construir_minimos_desde_parametros(db, flota_only=flota_only, piso=piso)
    out["meta"]["fuente"] = "Bybit instruments-info + tickers"
    out["meta"]["sync_s"] = round(elapsed, 2)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Sync mínimos Bybit → G_min por Santo")
    ap.add_argument("--flota-only", action="store_true", help="Solo flota Beru/manto")
    ap.add_argument("--no-prices", action="store_true", help="Sin tickers (min_usd parcial)")
    ap.add_argument("--also-parametros", action="store_true", help="Actualiza también bybit_parametros_mercado.json")
    ap.add_argument("--from-parametros", action="store_true", help="Sin red: deriva de BD parametros existente")
    ap.add_argument("--piso", type=float, default=None, help="Piso G_min (default config 1.0)")
    args = ap.parse_args()

    import core.config as config

    piso = float(args.piso if args.piso is not None else getattr(config, "G_MIN_USD_PISO", 1.0))

    if args.from_parametros:
        if not PARAM_PATH.is_file():
            print(f"FAIL: no existe {PARAM_PATH}")
            return 2
        db = json.loads(PARAM_PATH.read_text(encoding="utf-8"))
        out = construir_minimos_desde_parametros(
            db,
            flota_only=args.flota_only,
            piso=piso,
            advertencia="Sin llamada Bybit — cifras de BD parametros previa (puede estar desfasada).",
        )
        print("Modo --from-parametros (sin red).")
    else:
        try:
            out = sync_vivo(
                flota_only=args.flota_only,
                no_prices=args.no_prices,
                piso=piso,
                also_parametros=args.also_parametros,
            )
        except Exception as e:
            print(f"FAIL API Bybit: {e}")
            print("Reintento local: python scripts/sync_bybit_minimos_orden.py --from-parametros")
            if PARAM_PATH.is_file():
                db = json.loads(PARAM_PATH.read_text(encoding="utf-8"))
                out = construir_minimos_desde_parametros(
                    db,
                    flota_only=args.flota_only,
                    piso=piso,
                    advertencia=f"API falló ({e!s}); derivado de parametros previos.",
                )
                print("Fallback OK desde parametros.")
            else:
                return 2

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"OK -> {OUT_PATH}")
    print(f"  activos={out['meta']['n_activos']} piso={piso}")
    if out["meta"].get("advertencia"):
        print(f"  WARN: {out['meta']['advertencia']}")

    for a in ("BTC", "ETH", "SOL", "XRP", "MNT", "LTC", "PEPE"):
        row = (out.get("activos") or {}).get(a)
        if not row:
            continue
        print(
            f"  {a}: G_min={row.get('G_min')} ({row.get('G_min_fuente')}) "
            f"spot={((row.get('spot_usdt') or {}).get('min_usd_est'))} "
            f"lin={((row.get('linear') or {}).get('min_usd_est'))} "
            f"inv={((row.get('inverse') or {}).get('min_usd_est'))}"
        )

    # Invalidar caché si el proceso importa el módulo
    try:
        from core import g_min as gm

        gm.invalidar_cache()
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
