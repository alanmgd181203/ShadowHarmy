"""Smoke — Beru wake reset-0 flota · Normal 1.6 · manos OFF."""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import core.config as config
from core import beru_wake
from core import beru_cazador
from generales.beru import BeruCazador
from generales.capitanes import CapitanNormal, CapitanAnsiedad


def test_centros_reset_0():
    cl, cm = beru_wake.centros_al_wake(1234.5)
    assert cl == 1234.5
    assert cm == 1234.5


def test_capitan_normal_1_6():
    adn = beru_wake.adn_capitan_wake()
    assert adn is CapitanNormal
    assert abs(float(adn.vacio_adan) - 0.016) < 1e-9
    assert adn is not CapitanAnsiedad
    assert abs(beru_wake.vacio_wake_pct() - 0.016) < 1e-9


def test_manos_off_por_default():
    assert config.BERU_MANOS is False
    assert beru_wake.manos_beru_activas() is False
    assert config.BERU_HILO_ENABLED is False


def test_semilla_wake_ambos_centros():
    s = beru_wake.crear_semilla_wake("ADA", 0.19, tier_id="PROTO1")
    assert s.masa == 0.0
    assert s.centro_local == 0.19
    assert s.centro_manto == 0.19
    assert s.estado == "ACECHANDO"
    assert "ADA" in s.uid
    assert s.adn_capitan is CapitanNormal


def test_plantar_no_usa_promedio_tusk():
    tusk = MagicMock()
    tusk.masa_bruta_real = 2200.0
    tusk.masa_bruta = 2200.0
    tusk.precio_spot = 100.0
    tusk.ultimo_precio = 100.0
    tusk.pesos = {
        "XUSDT_LINEAL": {"long": 0, "short": 1, "precio_medio_long": 0, "precio_medio_short": 50.0},
        "XUSD_INVERSE": {"long": 1, "short": 0, "precio_medio_long": 50.0, "precio_medio_short": 0},
    }
    # Promedio Tusk sería 50; wake debe clavar 100
    assert abs(beru_cazador.centro_manto_desde_tusk(tusk) - 50.0) < 1e-6

    tank = MagicMock()
    tank.capitan_activo = CapitanAnsiedad  # se fuerza a Normal al init
    bel = MagicMock()
    beru = BeruCazador(tusk, bel, tank, bridge=None)
    # Sin director: permite caza
    import core.pase_director as pd
    prev = getattr(pd, "director_activo", None)
    try:
        pd.director_activo = lambda: False  # type: ignore
        s = beru.plantar_semilla_adan(100.0, activo="ETH")
    finally:
        if prev is not None:
            pd.director_activo = prev
    assert s is not None
    assert s.centro_manto == 100.0
    assert s.centro_local == 100.0
    assert tank.capitan_activo is CapitanNormal


def test_flota_siembra_varios():
    tusk = MagicMock()
    tusk.masa_bruta_real = 2200.0
    tusk.masa_bruta = 2200.0
    tusk.precio_spot = 0.0
    tusk.ultimo_precio = 0.0
    tank = MagicMock()
    tank.capitan_activo = CapitanNormal
    beru = BeruCazador(tusk, MagicMock(), tank, bridge=None)
    import core.pase_director as pd
    prev = pd.director_activo
    try:
        pd.director_activo = lambda: False  # type: ignore
        precios = {"ETH": 3000.0, "ADA": 0.18, "BCH": 210.0, "MNT": 0.43}
        n = beru.despertar_flota_reset_0(precios, equity_usd=2200.0)
    finally:
        pd.director_activo = prev
    assert n >= 3
    centros = {(b.uid.split("_")[2], b.centro_manto) for b in beru.legion}
    assert any(a == "ETH" and c == 3000.0 for a, c in centros)
    assert any(a == "ADA" and abs(c - 0.18) < 1e-9 for a, c in centros)


def test_resumen_cableado():
    r = beru_wake.resumen_cableado()
    assert r["wake_reset_0"] is True
    assert r["manos"] is False
    assert r["vacio_pct"] == 1.6
    assert r["n_flota_catalogo"] >= 10


def main() -> int:
    test_centros_reset_0()
    test_capitan_normal_1_6()
    test_manos_off_por_default()
    test_semilla_wake_ambos_centros()
    test_plantar_no_usa_promedio_tusk()
    test_flota_siembra_varios()
    test_resumen_cableado()
    print("validar_beru_wake_reset0_smoke: OK (7 checks)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
