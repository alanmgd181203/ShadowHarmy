import asyncio
import json
import ssl
import websockets

async def main():
    print("start", flush=True)
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    async with websockets.connect(
        "wss://stream.bybit.com/v5/public/linear", ssl=ctx, open_timeout=15, ping_interval=20
    ) as ws:
        await ws.send(json.dumps({"op": "subscribe", "args": ["tickers.LTCUSDT", "tickers.LTCUSDC"]}))
        for _ in range(5):
            msg = await asyncio.wait_for(ws.recv(), timeout=15)
            d = json.loads(msg)
            print(d.get("topic", d.get("op")), d.get("data", {}).get("lastPrice") if isinstance(d.get("data"), dict) else "", flush=True)

asyncio.run(main())
