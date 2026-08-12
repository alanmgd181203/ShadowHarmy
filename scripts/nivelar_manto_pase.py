#!/usr/bin/env python3
"""Bisturí de nivelación — recorta glotones al nocional del grado del pase.

Doctrina Monarca 2026-08-11:
- Medir nocional con positionValue (validado vs IM×lev).
- Solo reduceOnly Market; no engorda; MNT intocable (bóveda + cualquier pata).
- Arise / Igris manos OFF — este ritual es cirujano, no Asalto.

Uso:
  .venv/bin/python3 scripts/nivelar_manto_pase.py --dry-run
  .venv/bin/python3 scripts/nivelar_manto_pase.py --confirmar-go --permitir-mainnet
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ.setdefault("MODO_SIMULACION", "False")

import core.config as config
from core.pase_director import PASE_PASOS, need_notional_grado_usd, need_notional_por_pierna_usd
from pybit.unified_trading import HTTP

# Holgura mínima por pasos de lote / ruido de cotización (no “un dólar de gracia” doctrinal;
# solo evita rebanar polvo irreductible del exchange).
_EPS_USD = 2.0
_TOL_OVER_PCT = 0.01  # glotón si L+S > need × 1.01


def _f(x: Any, default: float = 0.0) -> float:
    try:
        if x in ("", None):
            return default
        return float(x)
    except (TypeError, ValueError):
        return default


def _load_dotenv() -> None:
    env = ROOT / ".env"
    if not env.exists():
        return
    for line in env.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def _grado_por_activo(pasos: set[int]) -> dict[str, str]:
    order = {"SOLDADO": 1, "CAPITAN": 2, "GENERAL": 3, "MARISCAL": 4}
    nivel: dict[str, str] = {}
    for p in PASE_PASOS:
        if int(p["n"]) not in pasos:
            continue
        act = str(p["activo"]).upper()
        g = str(p["grado"]).upper()
        if act not in nivel or order.get(g, 0) > order.get(nivel[act], 0):
            nivel[act] = g
    return nivel


def _base_de_symbol(symbol: str) -> str:
    s = str(symbol or "").upper()
    for suf in ("USDT", "USDC", "USD"):
        if s.endswith(suf) and len(s) > len(suf):
            return s[: -len(suf)]
    return s


def _nocional_usd(pos: dict[str, Any]) -> tuple[float, str]:
    """Nocional USD económico (anti-inflado).

    InversePerpetual Bybit: size = USD face. positionValue = coins (size/mark) — NO USD.
    Linear: abs(positionValue) o IM×lev si cuadra.
    """
    from core import lote_bybit as lote

    cat = str(pos.get("_category") or pos.get("category") or "")
    n = lote.nocional_usd_posicion_bybit(
        size=_f(pos.get("size")),
        mark_price=_f(pos.get("markPrice")),
        position_value=_f(pos.get("positionValue")) or None,
        category=cat,
    )
    fuente = "size_usd_face" if cat == "inverse" else "positionValue_or_size"
    return n, fuente


def _qty_step_info(session: HTTP, category: str, symbol: str) -> dict[str, float]:
    r = session.get_instruments_info(category=category, symbol=symbol)
    lst = ((r.get("result") or {}).get("list") or [])
    if not lst:
        return {"minOrderQty": 0.0, "qtyStep": 0.0}
    lot = lst[0].get("lotSizeFilter") or {}
    return {
        "minOrderQty": _f(lot.get("minOrderQty")),
        "qtyStep": _f(lot.get("qtyStep")),
    }


def _floor_qty(qty: float, step: float, min_qty: float) -> float:
    q = float(qty)
    if q <= 0:
        return 0.0
    if step > 0:
        q = math.floor(q / step + 1e-12) * step
        # evitar basura float
        dec = max(0, min(10, -int(math.floor(math.log10(step))) if step < 1 else 0))
        q = round(q, dec + 2)
    if min_qty > 0 and 0 < q < min_qty:
        return 0.0
    return q


def _pull_positions(session: HTTP) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for cat, kw in (
        ("linear", {"settleCoin": "USDT"}),
        ("inverse", {}),
    ):
        r = session.get_positions(category=cat, **kw)
        if r.get("retCode") != 0:
            raise RuntimeError(f"get_positions {cat}: {r.get('retMsg')}")
        for p in (r.get("result") or {}).get("list") or []:
            if _f(p.get("size")) <= 0:
                continue
            row = dict(p)
            row["_category"] = cat
            out.append(row)
    return out


def _wallet(session: HTTP) -> dict[str, Any]:
    r = session.get_wallet_balance(accountType="UNIFIED")
    if r.get("retCode") != 0:
        raise RuntimeError(f"wallet: {r.get('retMsg')}")
    lista = ((r.get("result") or {}).get("list") or [{}])
    return lista[0] if lista else {}


def planificar(
    posiciones: list[dict[str, Any]],
    grados: dict[str, str],
    session: HTTP | None,
) -> list[dict[str, Any]]:
    """Devuelve cortes planeados (uno por pierna glotona)."""
    # agrupar por activo
    by_act: dict[str, list[dict[str, Any]]] = {}
    for p in posiciones:
        base = _base_de_symbol(str(p.get("symbol") or ""))
        if not base:
            continue
        if base == "MNT":
            continue  # intocable
        by_act.setdefault(base, []).append(p)

    cortes: list[dict[str, Any]] = []
    for act, legs in sorted(by_act.items()):
        grado = grados.get(act)
        if not grado:
            # Santo abierto sin sello de pase: no inventar meta; saltar
            continue
        need_ls = need_notional_grado_usd(act, grado)
        need_leg = need_notional_por_pierna_usd(act, grado)
        leg_info = []
        total_n = 0.0
        total_im = 0.0
        for p in legs:
            n, fuente = _nocional_usd(p)
            im = _f(p.get("positionIM"))
            total_n += n
            total_im += im
            leg_info.append({"pos": p, "nocional": n, "fuente": fuente, "im": im})

        if total_n <= need_ls * (1.0 + _TOL_OVER_PCT) + _EPS_USD:
            continue  # no glotón

        # Rebanar cada pierna que exceda meta/pata (espejo doctrinal L≈S)
        for info in leg_info:
            p = info["pos"]
            n = info["nocional"]
            if n <= need_leg + _EPS_USD:
                continue
            excess_usd = n - need_leg
            size = _f(p.get("size"))
            if size <= 0 or n <= 0:
                continue
            # qty proporcional al excedente de nocional
            qty_raw = size * (excess_usd / n)
            cat = str(p["_category"])
            sym = str(p.get("symbol"))
            step_info = (
                _qty_step_info(session, cat, sym)
                if session is not None
                else {"minOrderQty": 0.0, "qtyStep": 0.0}
            )
            qty = _floor_qty(qty_raw, step_info["qtyStep"], step_info["minOrderQty"])
            if qty <= 0:
                continue
            # IM liberado estimado (proporcional)
            im_free = info["im"] * (qty / size) if size > 0 else 0.0
            side = str(p.get("side") or "")
            if side in ("Buy", "Long"):
                close_side = "Sell"
            else:
                close_side = "Buy"
            cortes.append(
                {
                    "activo": act,
                    "grado": grado,
                    "symbol": sym,
                    "category": cat,
                    "side_pos": side,
                    "close_side": close_side,
                    "size_antes": size,
                    "nocional_antes": round(n, 4),
                    "nocional_meta_pata": round(need_leg, 4),
                    "nocional_need_ls": round(need_ls, 4),
                    "nocional_total_antes": round(total_n, 4),
                    "exceso_usd": round(excess_usd, 4),
                    "qty_reduce": qty,
                    "im_antes": round(info["im"], 4),
                    "im_liberar_est": round(im_free, 4),
                    "fuente_nocional": info["fuente"],
                    "lev": _f(p.get("leverage")),
                    "mark": _f(p.get("markPrice")),
                    "qty_step": step_info["qtyStep"],
                    "min_qty": step_info["minOrderQty"],
                }
            )
    return cortes


def ejecutar_corte(session: HTTP, corte: dict[str, Any], *, dry: bool) -> dict[str, Any]:
    params = {
        "category": corte["category"],
        "symbol": corte["symbol"],
        "side": corte["close_side"],
        "orderType": "Market",
        "qty": str(corte["qty_reduce"]),
        "reduceOnly": True,
        "orderLinkId": f"SA-NIV-{corte['activo'][:3]}-{int(time.time() * 1000) % 10_000_000}",
    }
    if dry:
        return {"ok": True, "dry": True, "params": params}
    out = session.place_order(**params)
    ok = out.get("retCode") == 0
    return {
        "ok": ok,
        "dry": False,
        "retMsg": out.get("retMsg"),
        "orderId": ((out.get("result") or {}).get("orderId")),
        "raw": out,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Nivelar manto al nocional del pase (bisturí)")
    ap.add_argument("--dry-run", action="store_true", help="Solo plan; default si no hay --confirmar-go")
    ap.add_argument("--confirmar-go", action="store_true")
    ap.add_argument("--permitir-mainnet", action="store_true")
    ap.add_argument(
        "--solo",
        default="",
        help="CSV de bases a tocar (vacío = todos los glotones; MNT siempre excluido)",
    )
    args = ap.parse_args()

    dry = True
    if args.confirmar_go or args.permitir_mainnet:
        if not (args.confirmar_go and args.permitir_mainnet):
            print("ABORT: mainnet exige --confirmar-go y --permitir-mainnet juntos")
            return 2
        dry = False
    if args.dry_run:
        dry = True

    _load_dotenv()
    # reload config after dotenv
    import importlib
    importlib.reload(config)

    if bool(getattr(config, "TESTNET", False)):
        print("ABORT: Mundo A / DEMO activo — imposible")
        return 2
    if not config.API_KEY or not config.API_SECRET:
        print("ABORT: sin API keys")
        return 2

    prog_path = ROOT / "data" / "pase_progreso.json"
    pasos = set(int(x) for x in json.loads(prog_path.read_text()).get("pasos_logrados") or [])
    grados = _grado_por_activo(pasos)

    session = HTTP(
        testnet=False,
        api_key=config.API_KEY,
        api_secret=config.API_SECRET,
    )

    modo = "DRY-RUN (sin órdenes)" if dry else "LIVE MAINNET reduceOnly"
    print("=" * 72)
    print(f"RITUAL NIVELAR MANTO · {modo}")
    print(f"pasos sellados: {len(pasos)} · MNT intocable · Arise OFF")
    print("=" * 72)

    wb0 = _wallet(session)
    eq0 = _f(wb0.get("totalEquity"))
    disp0 = _f(wb0.get("totalAvailableBalance"))
    im0 = _f(wb0.get("totalInitialMargin"))
    o2_0 = min(disp0, eq0 * 0.95) if eq0 > 0 else disp0
    print(f"ANTES  equity=${eq0:.4f}  IM=${im0:.4f}  disponible=${disp0:.4f}  O₂≈${o2_0:.4f}")
    print(f"       IM rate={_f(wb0.get('accountIMRate'))*100:.2f}%")

    posiciones = _pull_positions(session)
    print(f"posiciones abiertas: {len(posiciones)}")

    # radar MNT (solo lectura, no tocar)
    mnt_legs = [p for p in posiciones if _base_de_symbol(str(p.get("symbol"))) == "MNT"]
    if mnt_legs:
        for p in mnt_legs:
            n, fnt = _nocional_usd(p)
            print(
                f"  [SKIP MNT] {p.get('symbol')} {p.get('side')} "
                f"n≈${n:.2f} ({fnt}) IM=${_f(p.get('positionIM')):.2f}"
            )

    cortes = planificar(posiciones, grados, session)
    solo = {x.strip().upper() for x in args.solo.split(",") if x.strip()}
    if solo:
        cortes = [c for c in cortes if c["activo"] in solo]

    if not cortes:
        print("\nSin glotones sobre meta de grado. Nada que rebanar.")
        return 0

    print("\n--- CORTES PLANIFICADOS ---")
    print(
        f"{'ACT':5} {'SYM':12} {'cat':7} {'side':4} "
        f"{'n_antes':>10} {'meta':>8} {'exceso':>10} {'qty↓':>12} {'IM↓est':>9} {'src':12}"
    )
    im_lib = 0.0
    exceso_total = 0.0
    by_act: dict[str, float] = {}
    for c in cortes:
        print(
            f"{c['activo']:5} {c['symbol']:12} {c['category']:7} {str(c['side_pos'])[:4]:4} "
            f"{c['nocional_antes']:10.2f} {c['nocional_meta_pata']:8.2f} "
            f"{c['exceso_usd']:10.2f} {c['qty_reduce']:12} "
            f"{c['im_liberar_est']:9.2f} {c['fuente_nocional']:12}"
        )
        im_lib += float(c["im_liberar_est"])
        exceso_total += float(c["exceso_usd"])
        by_act[c["activo"]] = by_act.get(c["activo"], 0.0) + float(c["exceso_usd"])

    print("\n--- POR SANTO (nocional a rebanar) ---")
    for act, ex in sorted(by_act.items(), key=lambda x: -x[1]):
        g = grados.get(act, "?")
        print(f"  {act} ({g}): −${ex:.2f} nocional excedente")

    print("\n--- PROYECCIÓN OXÍGENO ---")
    print(f"  Exceso nocional total a cortar: ${exceso_total:.2f}")
    print(f"  IM estimado a liberar:          ${im_lib:.2f}")
    print(f"  disponible proyectado:          ${disp0 + im_lib:.2f}")
    print(f"  O₂ guerra proyectado:           ${min(disp0 + im_lib, eq0 * 0.95):.4f}")
    print("  (proyección lineal; fills Market / mark real pueden ±unos USD)")

    if dry:
        print("\nDRY-RUN completo. Sin órdenes enviadas.")
        print("Para mainnet: --confirmar-go --permitir-mainnet")
        return 0

    print("\n--- EJECUCIÓN LIVE ---")
    ok_n = fail_n = 0
    for c in cortes:
        print(
            f"REDUCE {c['category']} {c['symbol']} {c['close_side']} "
            f"qty={c['qty_reduce']} reduceOnly (era n=${c['nocional_antes']:.2f})"
        )
        res = ejecutar_corte(session, c, dry=False)
        if res.get("ok"):
            print(f"  OK orderId={res.get('orderId')}")
            ok_n += 1
        else:
            print(f"  FAIL {res.get('retMsg')}")
            fail_n += 1
        time.sleep(0.35)

    time.sleep(1.5)
    wb1 = _wallet(session)
    eq1 = _f(wb1.get("totalEquity"))
    disp1 = _f(wb1.get("totalAvailableBalance"))
    im1 = _f(wb1.get("totalInitialMargin"))
    o2_1 = min(disp1, eq1 * 0.95) if eq1 > 0 else disp1
    print("\n--- DESPUÉS ---")
    print(f"equity=${eq1:.4f}  IM=${im1:.4f}  disponible=${disp1:.4f}  O₂≈${o2_1:.4f}")
    print(f"ΔIM={im0 - im1:+.4f}  Δdisponible={disp1 - disp0:+.4f}  ΔO₂={o2_1 - o2_0:+.4f}")
    print(f"fills ok={ok_n} fail={fail_n}")
    return 0 if fail_n == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
