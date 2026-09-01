#!/usr/bin/env python3
"""Sync mínimos fraccionales OKX SWAP — Santos Beru (primer ritual antes de manos).

Público: minSz, lotSz, ctVal, tickSz + last → min_usd_est (no gasta cuota de trading).
Opcional: ping cuenta con API key para confirmar .env.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core import beru_mar  # noqa: E402
from core import lote_okx  # noqa: E402
from core import okx_rest  # noqa: E402

OUT_CATALOGO = ROOT / "data" / "okx_parametros_mercado.json"
OUT_MINIMOS = ROOT / "data" / "okx_minimos_orden.json"

SANTOS_DEFAULT: tuple[str, ...] = (
    "BTC", "ETH", "SOL", "XRP", "ADA", "DOGE", "DOT", "LTC", "AAVE", "HYPE",
    "MNT", "AVAX", "LINK", "NEAR", "OP", "SUI", "UNI", "XLM", "FIL",
    "WLD", "ONDO",
)


def _f(x, default=0.0) -> float:
    try:
        v = float(x)
    except (TypeError, ValueError):
        return default
    return v if v > 0 else default


def _santos_list(raw: str | None) -> list[str]:
    if raw and str(raw).strip():
        return [a.strip().upper() for a in str(raw).split(",") if a.strip()]
    env = str(os.getenv("BERU_RANGO_SANTOS", "") or "").strip()
    if env:
        return [a.strip().upper() for a in env.split(",") if a.strip()]
    return list(SANTOS_DEFAULT)


def _fila_instrumento(row: dict, tickers: dict[str, dict]) -> dict | None:
    inst = str(row.get("instId") or "")
    if not inst.endswith("-USDT-SWAP"):
        return None
    state = str(row.get("state") or "live").lower()
    if state not in ("live", "trading", ""):
        return None
    act = beru_mar.inst_id_a_activo(inst)
    min_sz = _f(row.get("minSz"), 0)
    lot_sz = _f(row.get("lotSz"), min_sz)
    ct = _f(row.get("ctVal"), 0)
    tick = _f(row.get("tickSz"), 0.01)
    lev = _f(row.get("lever"), 0)
    if min_sz <= 0 or ct <= 0:
        return None
    trow = tickers.get(inst) or {}
    px = _f(trow.get("last"), 0)
    min_usd = min_sz * ct * px if px > 0 else min_sz * ct
    base_por_contrato = ct
    min_base = min_sz * ct
    return {
        "instId": inst,
        "symbol": beru_mar.symbol_legacy(act),
        "frente": beru_mar.frente_lineal(act),
        "minSz": min_sz,
        "lotSz": lot_sz,
        "ctVal": ct,
        "tickSz": tick,
        "maxLever": lev,
        "precio_ref": round(px, 8) if px > 0 else None,
        "min_contratos": min_sz,
        "min_base_asset": round(min_base, 8),
        "min_usd_est": round(min_usd, 4),
        "min_usd_como": "minSz_x_ctVal_x_last" if px > 0 else "minSz_x_ctVal_sin_precio",
        "G_min": round(min_usd, 4),
        "G_min_fuente": "okx_swap",
        "en_flota_beru": True,
    }


def _cargar_tickers() -> dict[str, dict]:
    out: dict[str, dict] = {}
    for t in okx_rest.tickers_swap_usdt():
        inst = str(t.get("instId") or "")
        if inst:
            out[inst] = t
    return out


def _ping_cuenta() -> tuple[bool, str]:
    if not okx_rest.credenciales_ok():
        return False, "sin_credenciales"
    try:
        data = okx_rest.get_private("/api/v5/account/balance")
        rows = list(data or [])
        if not rows:
            return True, "cuenta_ok_sin_filas"
        total = str((rows[0] or {}).get("totalEq") or "?")
        return True, f"cuenta_ok totalEq={total}"
    except okx_rest.OkxRestError as exc:
        return False, str(exc)


def main() -> int:
    ap = argparse.ArgumentParser(description="Mínimos fraccionales OKX — Santos Beru")
    ap.add_argument(
        "--santos",
        default="",
        help="Lista coma: HYPE,UNI,WLD (default BERU_RANGO_SANTOS o lote 21)",
    )
    ap.add_argument("--sin-ping", action="store_true", help="No probar API key privada")
    ap.add_argument("--solo-reporte", action="store_true", help="No escribir JSON")
    args = ap.parse_args()

    santos = _santos_list(args.santos)
    print(f"[okx_minimos] Santuarios: {len(santos)}", flush=True)

    rows = okx_rest.instruments_swap()
    tickers = _cargar_tickers()
    catalogo: dict[str, dict] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        pack = _fila_instrumento(row, tickers)
        if pack:
            act = beru_mar.inst_id_a_activo(pack["instId"])
            catalogo[act] = pack

    seleccion: dict[str, dict] = {}
    ausentes: list[str] = []
    for act in santos:
        if act in catalogo:
            seleccion[act] = catalogo[act]
        else:
            ausentes.append(act)

    if not args.sin_ping:
        ok_ping, msg_ping = _ping_cuenta()
        print(f"[okx_minimos] API privada: {'OK' if ok_ping else 'FALLO'} — {msg_ping}", flush=True)

    print(f"[okx_minimos] Catalogo SWAP USDT vivo: {len(catalogo)} pares", flush=True)
    print("", flush=True)
    print(f"{'SANTO':<8} {'minSz':>8} {'lotSz':>8} {'ctVal':>8} {'~USD':>9} {'last':>12} instId", flush=True)
    print("-" * 72, flush=True)
    for act in santos:
        if act not in seleccion:
            print(f"{act:<8} {'—':>8} {'—':>8} {'—':>8} {'—':>9} {'—':>12} NO_LISTADO", flush=True)
            continue
        p = seleccion[act]
        px = p.get("precio_ref") or 0
        print(
            f"{act:<8} {p['minSz']:>8g} {p['lotSz']:>8g} {p['ctVal']:>8g} "
            f"{p['min_usd_est']:>9.4f} {float(px):>12.4g} {p['instId']}",
            flush=True,
        )
        # Peldaño $0.25 doctrinal: cuántos contratos mínimo vs rampa
        if px > 0:
            pack25 = lote_okx.asegurar_qty_min_notional(
                lote_okx.masa_a_contratos(0.25, px, p["frente"]),
                px,
                p["frente"],
                mode="ceil",
            )
            if pack25.get("ok"):
                notional25 = float(pack25.get("notional_usd") or 0)
                print(
                    f"         peldaño $0.25 -> sube a ~${notional25:.2f} "
                    f"({pack25.get('qty')} contratos)",
                    flush=True,
                )

    if ausentes:
        print(f"\n[okx_minimos] AVISO sin SWAP USDT: {', '.join(ausentes)}", flush=True)

    if args.solo_reporte:
        return 0

    ts = datetime.now(timezone.utc).isoformat()
    OUT_MINIMOS.parent.mkdir(parents=True, exist_ok=True)
    OUT_MINIMOS.write_text(
        json.dumps(
            {
                "meta": {
                    "ts_utc": ts,
                    "fuente": "okx_public_instruments+tickers",
                    "mar": "okx",
                    "n_activos": len(seleccion),
                    "santos_pedidos": santos,
                    "santos_ausentes": ausentes,
                    "nota": "G_min Beru OKX = minSz x ctVal x last. Ritual previo a manos.",
                },
                "activos": seleccion,
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    print(f"\n[okx_minimos] Escrito {OUT_MINIMOS}", flush=True)

    # Refrescar catálogo completo (lote_okx cache)
    if catalogo:
        OUT_CATALOGO.write_text(
            json.dumps(
                {
                    "meta": {
                        "ts_utc": ts,
                        "fuente": "okx_public_instruments",
                        "mar": "okx",
                        "n_activos": len(catalogo),
                    },
                    "activos": catalogo,
                },
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        lote_okx.invalidar_cache_bd()
        print(f"[okx_minimos] Catalogo {len(catalogo)} pares -> {OUT_CATALOGO}", flush=True)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
