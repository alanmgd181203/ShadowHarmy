"""Debug rápido WS Bybit — 10 mensajes."""
import asyncio
import json
import ssl
import websockets

URL = "wss://stream.bybit.com/v5/public/linear"
ARGS = ["tickers.LTCUSDT", "orderbook.50.LTCUSDT"]


async def main():
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    count = 0
    async with websockets.connect(URL, ssl=ctx, ping_interval=20) as ws:
        await ws.send(json.dumps({"op": "subscribe", "args": ARGS}))
        async for msg in ws:
            data = json.loads(msg)
            print(json.dumps(data)[:500])
            count += 1
            if count >= 8:
                break


asyncio.run(main())
