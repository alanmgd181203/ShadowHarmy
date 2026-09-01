#!/usr/bin/env python3
"""Catalogo OKX completo via API publica — minimos de todo lo negociable.

instType: SPOT, MARGIN, SWAP, FUTURES, OPTION (+ EVENTS omitido v1).
Sin manos. Escribe data/okx_catalogo_completo.json
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core import beru_mar  # noqa: E402
from core import lote_okx  # noqa: E402
from core import okx_rest  # noqa: E402

OUT = ROOT / "data" / "okx_catalogo_completo.json"
OUT_SWAP_USDT = ROOT / "data" / "okx_parametros_mercado.json"

INST_TYPES = ("SPOT", "MARGIN", "SWAP", "FUTURES", "OPTION", "EVENTS")

TRADEFI_HINTS = (
    "AAPL", "TSLA", "NVDA", "AMZN", "META", "GOOG", "MSFT", "COIN", "MSTR",
    "SPX", "NDX", "HYUNDAI", "XAU", "XAG", "GOLD", "SILVER", "OIL", "BRENT",
    "WTI", "TRUMP",
)


def _f(x, default=0.0) -> float:
    try:
        v = float(x)
    except (TypeError, ValueError):
        return default
    return v


def _clase_visual(inst_id: str, inst_type: str, row: dict) -> str:
    u = str(inst_id or "").upper()
    base = str(row.get("baseCcy") or "").upper()
    if inst_type == "OPTION":
        return "opcion"
    if inst_type == "FUTURES":
        return "futuro_dated"
    if inst_type in ("SPOT", "MARGIN"):
        if base in TRADEFI_HINTS or any(h in base for h in TRADEFI_HINTS):
            return "spot_tradefi"
        return "spot_crypto"
    if inst_type == "SWAP":
        if u.endswith("-USD-SWAP"):
            return "perp_inverse_usd"
        if u.endswith("-USDT-SWAP"):
            act = beru_mar.inst_id_a_activo(u)
            if act in TRADEFI_HINTS or any(h in act for h in TRADEFI_HINTS):
                return "perp_tradefi"
            return "perp_linear_usdt"
        if u.endswith("-USDC-SWAP"):
            return "perp_linear_usdc"
        return "perp_otro"
    if inst_type == "EVENTS":
        return "evento"
    return "otro"


def _precio_ref(ticker: dict | None) -> float:
    if not ticker:
        return 0.0
    for k in ("last", "idxPx", "markPx"):
        px = _f(ticker.get(k), 0)
        if px > 0:
            return px
    return 0.0


def _min_usd_est(row: dict, inst_type: str, px: float) -> tuple[float, str]:
    min_sz = _f(row.get("minSz"), 0)
    ct_val = _f(row.get("ctVal"), 0)
    ct_type = str(row.get("ctType") or "").lower()
    inst_id = str(row.get("instId") or "")

    if min_sz <= 0:
        return 0.0, "sin_minSz"

    if inst_type in ("SPOT", "MARGIN"):
        if px > 0:
            return round(min_sz * px, 6), "minSz_x_last_quote"
        return 0.0, "minSz_sin_precio"

    if inst_type in ("SWAP", "FUTURES", "OPTION"):
        if ct_type == "linear" or inst_id.endswith(("-USDT-SWAP", "-USDC-SWAP")):
            if ct_val > 0 and px > 0:
                return round(min_sz * ct_val * px, 6), "minSz_x_ctVal_x_last"
            if ct_val > 0:
                return round(min_sz * ct_val, 6), "minSz_x_ctVal_sin_precio"
        if ct_type == "inverse" or inst_id.endswith("-USD-SWAP"):
            if ct_val > 0:
                return round(min_sz * ct_val, 6), "minSz_x_ctVal_usd_face"
        if px > 0 and ct_val > 0:
            return round(min_sz * ct_val * px, 6), "minSz_x_ctVal_x_last_fallback"
        return round(min_sz, 6), "minSz_contratos"

    return 0.0, "no_calculado"


def _normalizar(row: dict, inst_type: str, ticker: dict | None) -> dict:
    inst_id = str(row.get("instId") or "")
    px = _precio_ref(ticker)
    min_usd, min_como = _min_usd_est(row, inst_type, px)
    clase = _clase_visual(inst_id, inst_type, row)
    return {
        "instId": inst_id,
        "instType": inst_type,
        "clase": clase,
        "state": str(row.get("state") or ""),
        "baseCcy": row.get("baseCcy"),
        "quoteCcy": row.get("quoteCcy"),
        "settleCcy": row.get("settleCcy"),
        "ctType": row.get("ctType"),
        "ctVal": _f(row.get("ctVal"), 0) or None,
        "ctMult": row.get("ctMult"),
        "ctValCcy": row.get("ctValCcy"),
        "minSz": _f(row.get("minSz"), 0),
        "lotSz": _f(row.get("lotSz"), 0),
        "tickSz": _f(row.get("tickSz"), 0),
        "lever": _f(row.get("lever"), 0) or None,
        "expTime": row.get("expTime"),
        "listTime": row.get("listTime"),
        "instFamily": row.get("instFamily"),
        "uly": row.get("uly"),
        "precio_ref": round(px, 8) if px > 0 else None,
        "min_usd_est": min_usd,
        "min_usd_como": min_como,
        "maxMktSz": row.get("maxMktSz"),
        "maxLmtSz": row.get("maxLmtSz"),
        "maxMktAmt": row.get("maxMktAmt"),
        "maxLmtAmt": row.get("maxLmtAmt"),
    }


def _underlying_families(inst_type: str) -> list[str]:
    try:
        data = okx_rest.get_public(
            "/api/v5/public/underlying",
            params={"instType": inst_type},
        )
    except okx_rest.OkxRestError:
        return []
    out: list[str] = []
    for block in data or []:
        if isinstance(block, list):
            out.extend(str(x) for x in block if x)
        elif isinstance(block, str):
            out.append(block)
    return list(dict.fromkeys(out))


def _cargar_tickers(inst_type: str, errores: list[str]) -> dict[str, dict]:
    tipo = "SPOT" if inst_type == "MARGIN" else inst_type
    try:
        return {str(t.get("instId") or ""): t for t in okx_rest.tickers(tipo)}
    except okx_rest.OkxRestError as exc:
        errores.append(f"tickers_{tipo}: {exc}")
        return {}


def _ingestar_rows(
    rows: list[dict],
    inst_type: str,
    ticks: dict[str, dict],
    catalogo: dict[str, dict],
    resumen_clase: Counter[str],
) -> int:
    n = 0
    for row in rows:
        if not isinstance(row, dict):
            continue
        inst_id = str(row.get("instId") or "")
        if not inst_id:
            continue
        state = str(row.get("state") or "live").lower()
        if state not in ("live", "trading", "preopen", ""):
            continue
        key = f"{inst_type}:{inst_id}"
        norm = _normalizar(row, inst_type, ticks.get(inst_id))
        catalogo[key] = norm
        resumen_clase[norm["clase"]] += 1
        n += 1
    return n


def main() -> int:
    catalogo: dict[str, dict] = {}
    resumen_tipo: dict[str, int] = {}
    resumen_clase: Counter[str] = Counter()
    errores: list[str] = []

    for inst_type in INST_TYPES:
        if inst_type == "OPTION":
            familias = _underlying_families("OPTION")
            if not familias:
                errores.append("OPTION: sin instFamily")
                continue
            ticks = _cargar_tickers("OPTION", errores)
            n = 0
            for fam in familias:
                try:
                    rows = okx_rest.get_public(
                        "/api/v5/public/instruments",
                        params={"instType": "OPTION", "instFamily": fam},
                    )
                except okx_rest.OkxRestError as exc:
                    errores.append(f"OPTION:{fam}: {exc}")
                    continue
                n += _ingestar_rows(list(rows or []), "OPTION", ticks, catalogo, resumen_clase)
            resumen_tipo["OPTION"] = n
            print(f"[okx_catalogo] OPTION: {n} ({len(familias)} familias)", flush=True)
            continue

        if inst_type == "EVENTS":
            errores.append("EVENTS: requiere seriesId — omitido v1")
            continue

        try:
            rows = okx_rest.instruments(inst_type)
        except okx_rest.OkxRestError as exc:
            errores.append(f"{inst_type}: {exc}")
            continue
        if not rows:
            errores.append(f"{inst_type}: vacio")
            continue

        ticks = _cargar_tickers(inst_type, errores)
        n = _ingestar_rows(rows, inst_type, ticks, catalogo, resumen_clase)
        resumen_tipo[inst_type] = n
        print(f"[okx_catalogo] {inst_type}: {n} instrumentos", flush=True)

    swap_usdt: dict[str, dict] = {}
    for key, row in catalogo.items():
        if not key.startswith("SWAP:"):
            continue
        inst = row["instId"]
        if not str(inst).endswith("-USDT-SWAP"):
            continue
        act = beru_mar.inst_id_a_activo(inst)
        swap_usdt[act] = {
            "instId": inst,
            "symbol": beru_mar.symbol_legacy(act),
            "frente": beru_mar.frente_lineal(act),
            "minSz": row["minSz"],
            "lotSz": row["lotSz"],
            "ctVal": row["ctVal"],
            "tickSz": row["tickSz"],
            "maxLever": row.get("lever"),
            "precio_ref": row.get("precio_ref"),
            "min_usd_est": row.get("min_usd_est"),
            "min_usd_como": row.get("min_usd_como"),
            "clase": row.get("clase"),
            "G_min": row.get("min_usd_est"),
            "G_min_fuente": "okx_swap_usdt",
        }

    ts = datetime.now(timezone.utc).isoformat()
    payload = {
        "meta": {
            "ts_utc": ts,
            "fuente": "okx_api_v5_public",
            "endpoint_instruments": "/api/v5/public/instruments",
            "endpoint_tickers": "/api/v5/market/tickers",
            "inst_types_pedidos": list(INST_TYPES),
            "n_total": len(catalogo),
            "por_instType": resumen_tipo,
            "por_clase": dict(resumen_clase),
            "n_swap_usdt": len(swap_usdt),
            "errores": errores,
            "nota": "Catalogo completo OKX. min_usd_est estimado con last/idx/mark.",
        },
        "instrumentos": catalogo,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[okx_catalogo] TOTAL {len(catalogo)} -> {OUT}", flush=True)

    OUT_SWAP_USDT.write_text(
        json.dumps(
            {
                "meta": {
                    "ts_utc": ts,
                    "fuente": "derivado_okx_catalogo_completo",
                    "mar": "okx",
                    "n_activos": len(swap_usdt),
                },
                "activos": swap_usdt,
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    lote_okx.invalidar_cache_bd()
    print(f"[okx_catalogo] SWAP USDT {len(swap_usdt)} -> {OUT_SWAP_USDT}", flush=True)

    print("\nPor clase:", flush=True)
    for clase, cnt in sorted(resumen_clase.items(), key=lambda x: -x[1]):
        print(f"  {clase}: {cnt}", flush=True)

    if okx_rest.credenciales_ok():
        ok, msg = True, "credenciales_presentes"
        try:
            okx_rest.get_private("/api/v5/account/config")
            msg = "cuenta_config_ok"
        except okx_rest.OkxRestError as exc:
            ok, msg = False, str(exc)
        print(f"\n[okx_catalogo] API privada: {'OK' if ok else 'FALLO'} — {msg}", flush=True)
    else:
        print("\n[okx_catalogo] API privada: sin credenciales (catalogo publico OK)", flush=True)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
