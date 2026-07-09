"""Periscopio Binance — bookTicker spot (solo ojos, sin manos)."""
from __future__ import annotations

import asyncio
import json
import ssl
import time

import websockets

from core.activo import pares_binance_vigilancia
import core.config as config

BINANCE_WS = "wss://stream.binance.com:9443/stream"
CHUNK_SIZE = 80


class BinanceRefBridge:
    def __init__(self, tank, bellion):
        self.tank = tank
        self.bel = bellion
        self._base_por_stream: dict[str, str] = {}

    def _armar_streams(self) -> list[str]:
        pares = pares_binance_vigilancia()
        self._base_por_stream = {stream: base for base, stream in pares}
        return [f"{stream}@bookTicker" for _, stream in pares]

    async def conectar(self):
        if not getattr(config, "BINANCE_REF_ENABLED", True):
            return
        streams = self._armar_streams()
        if not streams:
            await self.bel.anotar("TANK", "BINANCE_REF", "Sin símbolos para vigilar.")
            return
        await self.bel.anotar(
            "TANK", "BINANCE_REF",
            f"Segundo mar: {len(streams)} bookTicker Binance spot.",
        )
        chunks = [streams[i : i + CHUNK_SIZE] for i in range(0, len(streams), CHUNK_SIZE)]
        await asyncio.gather(*[self._loop_chunk(chunk) for chunk in chunks])

    async def _loop_chunk(self, stream_names: list[str]):
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        query = "/".join(stream_names)
        url = f"{BINANCE_WS}?streams={query}"

        while True:
            try:
                async with websockets.connect(
                    url, ssl=ssl_context, ping_interval=20, open_timeout=15
                ) as ws:
                    async for raw in ws:
                        msg = json.loads(raw)
                        data = msg.get("data") or msg
                        await self._procesar_ticker(data)
            except Exception as e:
                await self.bel.anotar("TANK", "BINANCE_RECON", str(e)[:120])
                await asyncio.sleep(5)

    async def _procesar_ticker(self, data: dict):
        sym = (data.get("s") or "").lower()
        base = self._base_por_stream.get(sym)
        if not base:
            return
        try:
            bid = float(data.get("b") or 0)
            ask = float(data.get("a") or 0)
        except (TypeError, ValueError):
            return
        if bid <= 0 or ask <= 0:
            return
        mid = (bid + ask) / 2.0
        self.tank.inyectar_ref_binance(base, mid, time.time())
