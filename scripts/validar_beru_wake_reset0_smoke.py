"""Smoke — wake Beru no inventa 0; lo recibe del manto Igris."""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import core.config as config
from core import beru_wake
from generales.beru import BeruCazador
from generales.capitanes import CapitanNormal


def main() -> int:
    cl, cm = beru_wake.centros_al_wake(1234.5)
    assert cl == 1234.5 and cm == 0.0
    assert beru_wake.wake_reset_0_activo() is False
    assert config.BERU_WAKE_RESET_0 is False
    assert beru_wake.adn_capitan_wake() is CapitanNormal
    assert beru_wake.manos_beru_activas() is False

    s = beru_wake.crear_semilla_wake("ETH", 100.0, tier_id="PROTO1")
    assert s.centro_manto == 0.0
    assert s.modo_combate == "CAZA"

    tusk = MagicMock()
    tusk.masa_bruta_real = tusk.masa_bruta = 2200.0
    tusk.pesos = {
        "ETHUSD_INVERSE": {
            "long": 1,
            "short": 0,
            "precio_medio_long": 50.0,
            "precio_medio_short": 0,
        },
        "ETHUSDT_LINEAL": {
            "long": 0,
            "short": 1,
            "precio_medio_long": 0,
            "precio_medio_short": 50.0,
        },
    }
    tank = MagicMock()
    tank.capitan_activo = CapitanNormal
    beru = BeruCazador(tusk, MagicMock(), tank, bridge=None)

    import core.pase_director as pd
    previo = pd.director_activo
    try:
        pd.director_activo = lambda: False  # type: ignore
        sembrado = beru.plantar_semilla_adan(100.0, activo="ETH")
        sin_manto = beru.plantar_semilla_adan(1.0, activo="ADA")
    finally:
        pd.director_activo = previo

    assert sembrado is not None
    assert sembrado.centro_manto == 50.0
    assert sembrado.centro_local == 100.0
    assert sembrado.ancla_tramo == 100.0
    assert sin_manto is None

    resumen = beru_wake.resumen_cableado()
    assert resumen["wake_reset_0"] is False
    assert resumen["manos"] is False
    assert resumen["vacio_pct"] == 1.1
    assert resumen.get("sangre_pct") == 1.1
    with (
        patch("core.pase_director.director_activo", return_value=True),
        patch("core.pase_director.grado_beru_para_caza", return_value="MARISCAL"),
    ):
        assert beru_wake.tier_siembra_activo("HYPE", tusk=tusk) == "PLENO"
    with (
        patch("core.pase_director.director_activo", return_value=True),
        patch("core.pase_director.grado_beru_para_caza", return_value="SOLDADO"),
    ):
        assert beru_wake.tier_siembra_activo("OP", tusk=tusk) == "BERUBBY"

    # Integración: la flota nace con uniformes distintos según su propio manto.
    roster = BeruCazador(tusk, MagicMock(), tank, bridge=None)
    grados = {"HYPE": "MARISCAL", "DOT": "GENERAL", "OP": "SOLDADO"}
    with (
        patch("core.beru_wake.catalogo_flota", return_value=list(grados)),
        patch(
            "core.pase_director.grado_beru_para_caza",
            side_effect=lambda act, **_kw: grados[str(act).upper()],
        ),
        patch("core.beru_cazador.centro_manto_desde_tusk", return_value=100.0),
        patch("core.beru_cazador.manto_vivo", return_value=True),
    ):
        assert roster.despertar_flota_reset_0(
            {"HYPE": 100.0, "DOT": 100.0, "OP": 100.0},
            equity_usd=4000.0,
        ) == 3
    tiers = {roster._activo_de_barco(b): b.tier_id for b in roster.legion}
    assert tiers == {"HYPE": "PLENO", "DOT": "PROTO1", "OP": "BERUBBY"}, tiers
    ojos = beru_wake.catalogo_ojos_desde_foto(
        ["BTC", "ETH", "APT", "ETC", "DOT"],
        snap={
            "beru_flota": {
                "activos": [
                    {"activo": "DOT", "centro_manto": 0.76, "n_barcos": 1},
                ]
            },
            "igris_asset_details": {
                "ETH": {
                    "long": {"size_usd": 100},
                    "short": {"size_usd": 100},
                },
            },
        },
    )
    assert "DOT" in ojos
    assert "ETH" in ojos
    assert "APT" not in ojos
    assert "ETC" not in ojos
    print("validar_beru_wake_reset0_smoke: OK (metro manto · 0 local = wake)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
