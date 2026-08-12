"""Smoke frío — Beru manos fantasma (nivel 2)."""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import core.config as config
from core import beru_fantasma
from core import beru_wake
from generales.beru import BeruCazador


def test_flags_fantasma_default_off():
    assert config.BERU_MANOS_FANTASMA is False
    assert beru_fantasma.activo() is False


def test_ampliar_ojos():
    fr = beru_fantasma.ampliar_ojos_spot(["ADA", "BCH", "MNT"])
    assert "ADAUSDT_SPOT" in fr
    assert "ADAUSDT_SPOT" in config.FRENTES_BERU_VIGILANCIA
    assert "MNTUSDT_SPOT" in config.FRENTES_RESONANCIA_TANK


def test_estrechar_ojos_bridge():
    prev_bases = list(getattr(config, "BRIDGE_WS_BASES", None) or [])
    prev_books = bool(getattr(config, "BRIDGE_WS_SUBSCRIBE_BOOKS", True))
    prev_sem = getattr(config, "BERU_ACTIVO_SEMILLA", None)
    prev_tick = getattr(config, "TICKER_BASE", None)
    try:
        config.BERU_ACTIVO_SEMILLA = "ADA"
        config.TICKER_BASE = "ADA"
        bases = beru_fantasma.estrechar_ojos_bridge(["ADA", "BCH", "MNT"])
        assert bases == ["ADA", "BCH", "MNT"]
        assert config.BRIDGE_WS_BASES == ["ADA", "BCH", "MNT"]
        assert config.BRIDGE_WS_SUBSCRIBE_BOOKS is False
        src = (ROOT / "scripts" / "arise_beru_fantasma.py").read_text(encoding="utf-8")
        assert "estrechar_ojos_bridge" in src
        assert "BRIDGE_WS_SUBSCRIBE_BOOKS" in src
    finally:
        config.BRIDGE_WS_BASES = prev_bases
        config.BRIDGE_WS_SUBSCRIBE_BOOKS = prev_books
        if prev_sem is not None:
            config.BERU_ACTIVO_SEMILLA = prev_sem
        if prev_tick is not None:
            config.TICKER_BASE = prev_tick


def test_siembra_fantasma_sin_candado_pase():
    """Fantasma siembra flota aunque el pase no marque pasos logrados."""
    prev_f = bool(getattr(config, "BERU_MANOS_FANTASMA", False))
    prev_flota = list(getattr(config, "ACTIVOS_BERU_FLOTA", None) or [])
    try:
        config.BERU_MANOS_FANTASMA = True
        config.ACTIVOS_BERU_FLOTA = ["ADA", "BCH", "MNT"]
        ok = beru_wake.activos_siembra_permitidos(2000.0, pasos_logrados=[])
        assert ok == ["ADA", "BCH", "MNT"]

        from core.bellion import BellionAuditor
        from generales.tusk import TuskBoveda
        from generales.capitanes import CapitanNormal

        bel = BellionAuditor()
        tusk = TuskBoveda(bel)
        tusk.masa_bruta_real = 2200.0
        tank = MagicMock()
        tank.capitan_activo = CapitanNormal
        tank.nodos = []
        tank._obtener_lider_verde = MagicMock(return_value=None)
        beru = BeruCazador(tusk, bel, tank, bridge=MagicMock())
        n = beru.despertar_flota_reset_0({"ADA": 0.18, "BCH": 210.0, "MNT": 0.45})
        assert n == 3
        assert len(beru.legion) == 3
    finally:
        config.BERU_MANOS_FANTASMA = prev_f
        config.ACTIVOS_BERU_FLOTA = prev_flota


def test_registrar_escribe(tmp_path, monkeypatch=None):
    # Usa log real bajo data/ — ok en smoke
    beru_fantasma.registrar("SMOKE_TEST", detalle="ok", qty=1.5, precio=100.0)
    assert beru_fantasma.LOG_PATH.exists()
    text = beru_fantasma.LOG_PATH.read_text(encoding="utf-8")
    assert "SMOKE_TEST" in text


def test_wake_conoce_fantasma():
    config.BERU_MANOS_FANTASMA = True
    try:
        assert beru_wake.manos_fantasma_activas() is True
        r = beru_wake.resumen_cableado()
        assert r.get("manos_fantasma") is True
    finally:
        config.BERU_MANOS_FANTASMA = False


async def test_caza_fantasma_no_place_order():
    config.BERU_MANOS_FANTASMA = True
    config.MODO_SIMULACION = True
    config.BERU_MANOS = False
    try:
        from core.models import MarketContext
        from core.bellion import BellionAuditor
        from generales.tusk import TuskBoveda
        from generales.capitanes import CapitanNormal

        bel = BellionAuditor()
        tusk = TuskBoveda(bel)
        tusk.masa_autorizada = 500.0
        tank = MagicMock()
        tank.capitan_activo = CapitanNormal
        tank.nodos = []
        ctx = {
            "ADAUSDT_SPOT": MarketContext(
                symbol="ADAUSDT", market_type="SPOT",
                last_price=0.5, spread=0.01,
                depth_ask=1e6, depth_bid=1e6,
                volatilidad=0.01, timestamp=0, local_arrival=0,
                muro_ask_volumen=1e6, muro_bid_volumen=1e6,
            )
        }
        tank.vision_especulativa = AsyncMock(return_value=(ctx, "VERDE_SEGURO"))
        tank._obtener_lider_verde = MagicMock(return_value=MagicMock(libros={}, precios={"ADAUSDT_SPOT": 0.5}, precios_con_reflejo=lambda: {"ADAUSDT_SPOT": 0.5}))

        bridge = MagicMock()
        bridge.place_order = AsyncMock()
        beru = BeruCazador(tusk, bel, tank, bridge=bridge)
        # Forzar casa ADA
        beru._activo_casa = lambda: "ADA"
        beru._precio_casa = lambda: 0.5
        beru._beru_caza_permitida = lambda *a, **k: True

        from core.models import BeruShip
        ship = BeruShip(
            uid="BERU_SEM_ADA_SMOKE",
            centro_local=0.5,
            centro_manto=0.5,
            masa=10.0,
            direccion="LONG",
            estado="ESPERANDO_MATERIALIZACION",
            adn_capitan=CapitanNormal,
            modo_combate="CAZA",
        )
        await tusk.solicitar_reserva(ship.uid, 10.0, "BERU", "LONG", consumir_auth=False)
        await beru._ejecutar_caza(ship)
        bridge.place_order.assert_not_called()
        assert ship.estado == "NEGOCIANDO"
        assert ship.precio_entrada_real > 0
    finally:
        config.BERU_MANOS_FANTASMA = False


async def test_caza_barco_bch_no_ada():
    """Barco SEM_BCH debe rail/bitácora en BCH, no en casa ADA."""
    config.BERU_MANOS_FANTASMA = True
    config.MODO_SIMULACION = True
    config.BERU_MANOS = False
    try:
        from core.models import MarketContext, BeruShip
        from core.bellion import BellionAuditor
        from generales.tusk import TuskBoveda
        from generales.capitanes import CapitanNormal

        bel = BellionAuditor()
        tusk = TuskBoveda(bel)
        tusk.masa_autorizada = 500.0
        tank = MagicMock()
        tank.capitan_activo = CapitanNormal
        tank.nodos = []
        precios = {"BCHUSDT_SPOT": 200.0, "ADAUSDT_SPOT": 0.5}
        ctx = {
            "BCHUSDT_SPOT": MarketContext(
                symbol="BCHUSDT", market_type="SPOT",
                last_price=200.0, spread=0.01,
                depth_ask=1e6, depth_bid=1e6,
                volatilidad=0.01, timestamp=0, local_arrival=0,
                muro_ask_volumen=1e6, muro_bid_volumen=1e6,
            )
        }
        tank.vision_especulativa = AsyncMock(return_value=(ctx, "VERDE_SEGURO"))
        lider = MagicMock(libros={}, precios=precios, precios_con_reflejo=lambda: precios)
        tank._obtener_lider_verde = MagicMock(return_value=lider)
        bridge = MagicMock()
        bridge.place_order = AsyncMock()
        beru = BeruCazador(tusk, bel, tank, bridge=bridge)
        beru._activo_casa = lambda: "ADA"
        beru._precio_casa = lambda: 0.5
        beru._beru_caza_permitida = lambda *a, **k: True

        ship = BeruShip(
            uid="BERU_SEM_BCH_SMOKE",
            centro_local=200.0,
            centro_manto=200.0,
            masa=5.0,
            direccion="LONG",
            estado="ESPERANDO_MATERIALIZACION",
            adn_capitan=CapitanNormal,
            modo_combate="CAZA",
        )
        assert beru._activo_de_barco(ship) == "BCH"
        await tusk.solicitar_reserva(ship.uid, 5.0, "BERU", "LONG", consumir_auth=False)
        await beru._ejecutar_caza(ship)
        bridge.place_order.assert_not_called()
        text = beru_fantasma.LOG_PATH.read_text(encoding="utf-8")
        assert "BERU_SEM_BCH_SMOKE" in text
        assert "symbol=BCHUSDT" in text or '"symbol": "BCHUSDT"' in text
        assert "activo=BCH" in text or '"activo": "BCH"' in text
    finally:
        config.BERU_MANOS_FANTASMA = False


def test_ritual_cancela_y_muleta():
    src = (ROOT / "scripts" / "arise_beru_fantasma.py").read_text(encoding="utf-8")
    assert "_muleta_ojos_rest" in src
    assert "t.cancel()" in src
    assert "beru_ojos" in src
    from core import beru_ojos
    assert beru_ojos.rest_fallback_activo() is True


def main() -> int:
    import asyncio

    test_flags_fantasma_default_off()
    test_ampliar_ojos()
    test_estrechar_ojos_bridge()
    test_siembra_fantasma_sin_candado_pase()
    test_ritual_cancela_y_muleta()
    test_registrar_escribe(None)
    test_wake_conoce_fantasma()
    asyncio.run(test_caza_fantasma_no_place_order())
    asyncio.run(test_caza_barco_bch_no_ada())
    print("validar_beru_fantasma_smoke: OK (9 checks)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
