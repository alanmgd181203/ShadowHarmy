#!/usr/bin/env python3
"""Smoke Ley de la Masa — Alfa Lineal, espejo Inverso, candado asimetría 5%."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core import lote_bybit as lote
import core.config as config


def test_alfa_eth_lineal_dicta():
    """Con ETH ~1919, 0.01 min → Alfa ~$19 → Inverso qty≈19, no $5."""
    fl, fs = "ETHUSD_INVERSE", "ETHUSDT_LINEAL"
    px_inv, px_lin = 1919.0, 1919.5
    # Deseado $5 (piso viejo del inverso): debe subir a Alfa lineal
    ley = lote.ley_de_la_masa_dual(fl, fs, px_inv, px_lin, 5.0)
    assert ley["ok"] is True, ley
    assert ley["frente_lineal"] == fs
    assert float(ley["alfa_usd"]) >= 18.0, ley  # 0.01 * ~1919
    assert float(ley["masa_absoluta_usd"]) >= float(ley["alfa_usd"]) - 1e-6
    # Inverso espeja USD efectivo del lineal (~19), no pelea solo su $5
    assert float(ley["qty_a"]) >= 18.0, ley
    assert abs(float(ley["usd_a"]) - float(ley["usd_b"])) / float(ley["masa_absoluta_usd"]) <= 0.05
    assert float(ley["asim_pct"]) <= 5.0 + 1e-6
    # Espejo cercano: con step 1 USD, asim típica ~1% (19 vs 19.19), no 117%
    assert float(ley["asim_pct"]) < 3.0, ley
    print(
        "  Alfa ETH OK · Alfa$", round(ley["alfa_usd"], 2),
        "inv", ley["qty_a"], "lin", ley["qty_b"],
        "USD", ley["usd_a"], "/", ley["usd_b"],
        "asim%", ley["asim_pct"],
    )


def test_candado_5_pct():
    """Si forzamos asimetría absurda, el candado debe denegar (mock lim)."""
    fl, fs = "ETHUSD_INVERSE", "ETHUSDT_LINEAL"
    ley = lote.ley_de_la_masa_dual(fl, fs, 1919.0, 1919.5, 5.0, asim_max_pct=0.00001)
    # Con paso 1 USD vs 0.01 ETH suele quedar ~1% — lim ultra-estricto → bloqueo
    if float(ley.get("asim_pct") or 0) > 0.001:
        assert ley["ok"] is False
        assert ley["motivo"] == "asimetr_masa_usd"
        print("  candado ultra-estricto bloquea OK · asim%", ley["asim_pct"])
    else:
        # Si por casualidad cae exacto, sigue OK con lim default
        ley2 = lote.ley_de_la_masa_dual(fl, fs, 1919.0, 1919.5, 5.0)
        assert ley2["ok"] is True
        print("  candado default OK (asim casi 0) · asim%", ley2["asim_pct"])


def test_reconstruye_fuga_5_vs_19():
    """La fuga histórica: misma 'masa' coin → $5 inv / $19 lin. Ley la cierra."""
    px = 1919.0
    # Viejo path roto: masa = 5/px ≈ 0.0026 como qty en ambos
    masa_vieja = 5.0 / px
    aseg_inv = lote.asegurar_qty_min_notional(masa_vieja, px, "ETHUSD_INVERSE")
    aseg_lin = lote.asegurar_qty_min_notional(masa_vieja, px, "ETHUSDT_LINEAL")
    usd_inv_viejo = float(aseg_inv["usd"])
    usd_lin_viejo = float(aseg_lin["usd"])
    fuga = abs(usd_inv_viejo - usd_lin_viejo) / max((usd_inv_viejo + usd_lin_viejo) / 2, 1e-9)
    assert fuga > 0.05, (usd_inv_viejo, usd_lin_viejo, fuga)  # documenta la fuga

    ley = lote.ley_de_la_masa_dual(
        "ETHUSD_INVERSE", "ETHUSDT_LINEAL", px, px, 5.0,
    )
    assert ley["ok"] is True
    fuga2 = abs(float(ley["usd_a"]) - float(ley["usd_b"])) / max(
        float(ley["masa_absoluta_usd"]), 1e-9,
    )
    assert fuga2 <= float(config.IGRIS_MASA_ASIMETRIA_MAX_PCT) + 1e-9
    print(
        "  fuga documentada $%.2f vs $%.2f (%.0f%%) → Ley $%.2f/$%.2f (%.2f%%)"
        % (usd_inv_viejo, usd_lin_viejo, fuga * 100, ley["usd_a"], ley["usd_b"], fuga2 * 100)
    )


def test_duda_redondeo_favor_long():
    """
    Ante duda (ceil/floor casi equidistantes) → más USD en Inverso (long).

    Con ETH ~1919.5 y masa ~2×Alfa, el espejo cae cerca del punto medio
    entre dos contratos USD del Inverso: floor estaba un poco más cerca,
    pero la diferencia de cercanía < medio step → doctrina elige ceil (long).
    """
    fl, fs = "ETHUSD_INVERSE", "ETHUSDT_LINEAL"
    px = 1919.5
    ley = lote.ley_de_la_masa_dual(fl, fs, px, px, 20.0)
    assert ley["ok"] is True, ley
    assert ley["frente_inverso"] == fl
    usd_esp = float(ley["usd_espejo"])
    conv_ceil = lote.cuantizar_presupuesto_usd(usd_esp, px, fl, mode="ceil")
    conv_floor = lote.cuantizar_presupuesto_usd(usd_esp, px, fl, mode="floor")
    assert conv_ceil.get("ok") and conv_floor.get("ok"), (conv_ceil, conv_floor)
    usd_ceil = float(conv_ceil["usd"])
    usd_floor = float(conv_floor["usd"])
    assert usd_ceil > usd_floor, (usd_ceil, usd_floor)
    d_ceil = abs(usd_ceil - usd_esp)
    d_floor = abs(usd_floor - usd_esp)
    step = usd_ceil - usd_floor
    # Condición de duda: floor un poco más cerca, pero Δ ≤ medio step
    assert d_floor < d_ceil, (d_floor, d_ceil, usd_esp)
    assert abs(d_ceil - d_floor) <= 0.5 * step + 1e-9, (d_ceil, d_floor, step)
    # qty_a / usd_a = Inverso (frente_a) → debe ser el ceil (más USD long)
    assert float(ley["usd_a"]) == usd_ceil, ley
    assert float(ley["qty_a"]) == float(conv_ceil["qty"]), ley
    print(
        "  duda→long OK · espejo$", round(usd_esp, 3),
        "floor$", usd_floor, f"(d={d_floor:.3f})",
        "ceil$", usd_ceil, f"(d={d_ceil:.3f})",
        "→ eligió$", ley["usd_a"],
    )


def main():
    print("[SMOKE] Ley de la Masa")
    bd = Path("data/bybit_parametros_mercado.json")
    if not bd.exists():
        print("[SKIP] sin BD bybit_parametros_mercado.json")
        return 0
    test_alfa_eth_lineal_dicta()
    test_candado_5_pct()
    test_reconstruye_fuga_5_vs_19()
    test_duda_redondeo_favor_long()
    # Asalto: techo holgado (no cacería)
    config.IGRIS_MASA_ASIMETRIA_ASALTO_PCT = 0.12
    lim_a = lote.asim_masa_lim_activo(marcha_asalto=True)
    lim_p = lote.asim_masa_lim_activo(marcha_asalto=False)
    assert abs(lim_a - 0.12) < 1e-9, lim_a
    assert abs(lim_p - float(config.IGRIS_MASA_ASIMETRIA_MAX_PCT)) < 1e-9, lim_p
    print("  asim Asalto 12% / personalizado 5% OK")
    print("[OK] ley_masa smoke completo")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
