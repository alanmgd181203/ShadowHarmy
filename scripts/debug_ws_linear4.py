import asyncio
import json
import ssl
import websockets

URL = "wss://stream.bybit.com/v5/public/linear"
ARGS = [
    "tickers.LTCUSDT", "tickers.LTCUSDC",
    "orderbook.50.LTCUSDT", "orderbook.50.LTCUSDC",
]


async def main():
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    print("connecting...")
    async with websockets.connect(URL, ssl=ctx, ping_interval=20) as ws:
        await ws.send(json.dumps({"op": "subscribe", "args": ARGS}))
        n = 0
        async for msg in ws:
            d = json.loads(msg)
            t = d.get("topic", d.get("op", "?"))
            print(n, t, str(d)[:120])
            n += 1
            if n >= 10:
                break


asyncio.run(main())
