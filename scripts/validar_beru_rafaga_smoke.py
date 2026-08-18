#!/usr/bin/env python3
"""Smoke frío — empaque de bocados y red de ráfaga (mínima / radar)."""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import core.config as config
from core import beru_rafaga
from core.bridge import OrdenResultado
from core.models import BeruShip
from generales.beru import BeruCazador
from generales.capitanes import CapitanNormal


def _assert_empacar() -> None:
    a = beru_rafaga.empacar_bocados_usd(40, 5)
    assert a == [5.0] * 8, a
    b = beru_rafaga.empacar_bocados_usd(42, 5)
    assert b[:6] == [5.0] * 6, b
    assert b[6:] == [6.0, 6.0], b
    assert abs(sum(b) - 42) < 1e-9
    c = beru_rafaga.empacar_bocados_usd(42.4, 5)
    assert abs(sum(c) - 42.4) < 1e-6, c
    assert all(x + 1e-9 >= 5 for x in c), c
    d = beru_rafaga.empacar_bocados_usd(7, 5)
    assert d == [7.0], d
    assert beru_rafaga.empacar_bocados_usd(4.9, 5) == []
    assert beru_rafaga.empacar_bocados_usd(10, 5) == [5.0, 5.0]
    gordo = beru_rafaga.empacar_bocados_usd(200, 5, max_bocados=24)
    assert len(gordo) <= 24, gordo
    assert all(x + 1e-9 >= 5 for x in gordo)
    assert abs(sum(gordo) - 200) < 0.02, gordo
    print("  empacar USD OK", a, b)


def _assert_ahogo() -> None:
    ok = OrdenResultado(
        False, mensaje="Insufficient available balance",
        datos={"retCode": 110007},
    )
    assert beru_rafaga.resultado_es_ahogo(ok)
    qty = OrdenResultado(
        False, mensaje="Order quantity is invalid",
        datos={"retCode": 10001},
    )
    assert not beru_rafaga.resultado_es_ahogo(qty)
    assert beru_rafaga.resultado_es_lote(qty)
    sym = OrdenResultado(False, mensaje="symbol not support", datos={"retCode": 10001})
    assert not beru_rafaga.resultado_es_ahogo(sym)
    assert not beru_rafaga.resultado_es_ahogo(OrdenResultado(True, mensaje="OK"))
    # Dump de excepción con JSON (qty/symbol) no se confunde con ahogo.
    aave = OrdenResultado(
        False,
        mensaje=(
            'ErrCode: 170140. Order value exceeded lower limit. '
            '{"qty":"0.28","symbol":"AAVEUSDT"}'
        ),
        datos={},
    )
    assert beru_rafaga.resultado_es_lote(aave)
    assert not beru_rafaga.resultado_es_ahogo(aave)
    assert beru_rafaga.retcode_de_resultado(aave) == 170140
    print("  rechazo ahogo vs lote OK")


class BridgeCapa:
    """Acepta o escupe según techo USD. Markets no llevan gatillo."""

    def __init__(self, *, techo_usd: float = 10.0, min_ok: bool = True) -> None:
        self.techo_usd = techo_usd
        self.min_ok = min_ok
        self.ordenes: dict[str, dict] = {}
        self.creadas: list[dict] = []
        self.n = 0

    async def get_order_status(self, symbol, *, link_id, category, order_filter=None):
        orden = self.ordenes.get(link_id)
        if orden is None:
            return OrdenResultado(
                False, link_id=link_id, mensaje="orden_no_encontrada",
                datos={"not_found": True},
            )
        return OrdenResultado(
            True, order_id=orden["orderId"], link_id=link_id,
            mensaje=orden["orderStatus"], datos=dict(orden),
        )

    async def place_order(self, symbol, side, qty, **kwargs):
        self.n += 1
        px = float(kwargs.get("trigger_price") or 100.0)
        usd = float(qty) * px
        rec = {
            "qty": float(qty),
            "trigger_price": kwargs.get("trigger_price"),
            "order_filter": kwargs.get("order_filter"),
            "order_type": kwargs.get("order_type", "Market"),
            "market_unit": kwargs.get("market_unit"),
            "link_id": kwargs.get("link_id"),
            "usd": usd,
        }
        if kwargs.get("trigger_price") is not None:
            if usd > self.techo_usd + 0.01:
                return OrdenResultado(
                    False, link_id=kwargs.get("link_id"),
                    mensaje="Insufficient available balance",
                    datos={"retCode": 110007},
                )
            if not self.min_ok:
                return OrdenResultado(
                    False, link_id=kwargs.get("link_id"),
                    mensaje="ab not enough for new order",
                    datos={"retCode": 170131},
                )
        link = kwargs.get("link_id") or f"L-{self.n}"
        orden = {
            "orderId": f"O-{self.n}",
            "orderLinkId": link,
            "orderStatus": "Untriggered" if kwargs.get("trigger_price") else "Filled",
            "symbol": symbol,
            "side": side,
            "qty": qty,
            "avgPrice": 100.0,
            "cumExecQty": qty,
        }
        self.ordenes[link] = orden
        rec["orderId"] = orden["orderId"]
        self.creadas.append(rec)
        return OrdenResultado(True, order_id=orden["orderId"], link_id=link, datos=orden)

    async def esperar_fill(self, symbol, **kwargs):
        link = kwargs.get("link_id")
        orden = self.ordenes.get(link) or {}
        return OrdenResultado(
            True, order_id=orden.get("orderId", ""), link_id=link,
            datos={
                "avgPrice": 100.0,
                "cumExecQty": float(orden.get("qty") or 0),
                "orderStatus": "Filled",
            },
        )


class Bel:
    def __init__(self) -> None:
        self.tags: list[str] = []

    async def anotar(self, _g, tag, _msg):
        self.tags.append(str(tag))


class Tank:
    capitan_activo = CapitanNormal
    precios = {"ETHUSDT_SPOT": 100.0}


class Tusk:
    pesos = {}
    masa_autorizada = 0.0
    masa_bruta_real = 0.0
    masa_bruta = 0.0

    async def solicitar_reserva(self, *args, **kwargs):
        return True

    async def liberar_reserva(self, *args, **kwargs):
        return None

    async def consumar_cosecha_atomica(self, *args, **kwargs):
        return None


def _barco(masa: float = 40.0) -> BeruShip:
    return BeruShip(
        uid="SEM_ETH_L",
        centro_local=100.0,
        masa=masa,
        direccion="LONG",
        estado="CAZANDO",
        oz_adan=100.0,
        frente_asignado="ETHUSDT_SPOT",
        tier_id="PROTO1",
        modo_combate="CAZA",
    )


def _general(bridge) -> BeruCazador:
    g = BeruCazador(Tusk(), Bel(), Tank(), bridge=bridge)
    g._manos_exchange = lambda beru=None: True  # type: ignore[method-assign]
    g._activo_de_barco = lambda beru=None: "ETH"  # type: ignore[method-assign]
    g._precio_de_barco = lambda beru=None: 100.0  # type: ignore[method-assign]
    g._bitacora = lambda *a, **k: None  # type: ignore[method-assign]
    return g


async def _capas() -> None:
    config.BERU_RAFAGA_LATENCIA_S = 0.0
    config.BERU_RAFAGA_FILL_TIMEOUT_S = 0.0
    config.BERU_RAFAGA_COOLDOWN_S = 0.0

    feliz = BridgeCapa(techo_usd=10_000)
    g = _general(feliz)
    b = _barco()
    ok = await g._plantar_hoz_nativa(b)
    assert ok, "camino feliz debe plantar"
    assert b.hoz_modo == "", b.hoz_modo
    assert b.masa_rafaga_usd == 0
    assert all(c.get("trigger_price") is not None for c in feliz.creadas), feliz.creadas
    assert len(feliz.creadas) == 1
    print("  capa 1 feliz: una Hoz gorda, cero market")

    mini = BridgeCapa(techo_usd=10.0, min_ok=True)
    g = _general(mini)
    b = _barco(40)
    ok = await g._plantar_hoz_nativa(b)
    assert ok
    assert b.hoz_modo == "MINIMA", b.hoz_modo
    assert b.masa_carta_usd + 1e-9 >= 5
    assert b.masa_rafaga_usd + 1e-9 >= 20, b.masa_rafaga_usd
    stops = [c for c in mini.creadas if c.get("trigger_price") is not None]
    markets = [c for c in mini.creadas if c.get("trigger_price") is None]
    assert len(stops) == 1, stops
    assert markets == [], markets
    print("  capa 2 mínima: una carta chica, resto acecha")

    radar = BridgeCapa(techo_usd=0.0, min_ok=False)
    g = _general(radar)
    b = _barco(40)
    ok = await g._plantar_hoz_nativa(b)
    assert ok
    assert b.hoz_modo == "RADAR", b.hoz_modo
    assert not b.altar_link_id
    assert abs(b.masa_rafaga_usd - 40) < 0.01
    assert radar.creadas == []
    print("  capa 3 radar: cero carta en la casa")

    qty = BridgeCapa(techo_usd=10_000)
    async def _qty_fail(symbol, side, qty, **kwargs):
        return OrdenResultado(
            False, mensaje="Order quantity is invalid",
            datos={"retCode": 10001},
        )
    qty.place_order = _qty_fail  # type: ignore[method-assign]
    g = _general(qty)
    b = _barco(40)
    ok = await g._plantar_hoz_nativa(b)
    assert not ok
    assert b.hoz_modo == ""
    print("  rechazo de lote no se trocea")

    lote_b = BridgeCapa(techo_usd=10_000)
    async def _lote_fail(symbol, side, qty, **kwargs):
        lote_b.n += 1
        return OrdenResultado(
            False,
            mensaje='ErrCode: 170140. Order value exceeded lower limit.',
            datos={"retCode": 170140},
        )
    lote_b.place_order = _lote_fail  # type: ignore[method-assign]
    g = _general(lote_b)
    b = _barco(25)
    ok = await g._plantar_hoz_nativa(b)
    assert not ok
    assert b.altar_lote_bloqueado
    assert b.hoz_modo == ""
    n1 = lote_b.n
    ok2 = await g._plantar_hoz_nativa(b)
    assert not ok2
    assert lote_b.n == n1
    print("  170140 sella lote y calla el martillo")

    # Ráfaga: markets sin gatillo, uno tras otro, ninguno < mínimo.
    g = _general(mini)
    b = _barco(40)
    b.hoz_modo = "MINIMA"
    b.masa_carta_usd = 5.0
    b.masa_rafaga_usd = 35.0
    mini.creadas.clear()
    res = await beru_rafaga.disparar_rafaga(
        mini, b, activo="ETH", usd=35.0, precio=100.0, is_leverage=1,
    )
    assert res["bocados_ok"] >= 1, res
    for c in mini.creadas:
        assert c.get("trigger_price") is None, c
        assert c.get("order_filter") in (None, "")
        assert c.get("market_unit") == "baseCoin", c
        assert c["usd"] + 1e-9 >= 5, c
    print("  ráfaga: markets sin gatillo, bocados ≥ mínimo")


def main() -> int:
    print("[SMOKE] beru ráfaga / empaque")
    _assert_empacar()
    _assert_ahogo()
    asyncio.run(_capas())
    print("OK validar_beru_rafaga_smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
