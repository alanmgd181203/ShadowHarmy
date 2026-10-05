"""Vigía de palanca — recorre los pares vivos y pide el máximo.

No reinicia cazadores y no toca sus Órdenes Oz. Solo mira la palanca
de cada par y, si no es el techo, la sube de uno en uno.
"""
from __future__ import annotations

import asyncio
import json
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from core import beru_leverage as blev
_PAUSA_PAR_S = 0.4
_RONDA_S = 600.0


def _nombres() -> list[str]:
    vistos: set[str] = set()
    out: list[str] = []

    def _sumar(nombre: str) -> None:
        u = str(nombre or "").strip().upper()
        if not u or u in vistos or u == "BTC":
            return
        vistos.add(u)
        out.append(u)

    asig = RAIZ / "data" / "beru" / "rango" / "piedra_asignacion.json"
    try:
        doc = json.loads(asig.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        doc = {}
    activos = doc.get("activos") if isinstance(doc, dict) else None
    if isinstance(activos, dict):
        for nombre in activos:
            _sumar(nombre)
    try:
        from cirugias.escudo_dual.bolsa import SALAS
    except Exception:
        SALAS = {}
    for nombre in SALAS:
        _sumar(nombre)
    return out


async def _una_ronda(nombres: list[str]) -> str:
    class _Puente:
        async def set_leverage(self, inst: str, lev: int, category: str = "linear"):
            from core.bridge import OrdenResultado
            from core import okx_rest

            try:
                await asyncio.to_thread(
                    okx_rest.post_private,
                    "/api/v5/account/set-leverage",
                    {"instId": inst, "lever": str(int(lev)), "mgnMode": "cross"},
                )
                return OrdenResultado(True, mensaje="OK")
            except okx_rest.OkxRestError as exc:
                msg = str(exc)
                if "leverage" in msg.lower() and "same" in msg.lower():
                    return OrdenResultado(True, mensaje=msg)
                return OrdenResultado(False, mensaje=msg)

    puente = _Puente()
    techo = 0
    subio = 0
    quieto = 0
    print(f"[PALANCA] ronda {len(nombres)} pares", flush=True)
    for i, nombre in enumerate(nombres, start=1):
        try:
            out = await blev.forzar_max_leverage_activo(puente, None, nombre)
        except Exception as exc:
            quieto += 1
            if quieto <= 5:
                print(f"[PALANCA] {nombre} tropiezo {exc}", flush=True)
            await asyncio.sleep(_PAUSA_PAR_S)
            continue
        pierna = (out.get("piernas") or [{}])[0]
        antes = pierna.get("antes")
        aplicado = pierna.get("aplicado")
        pedido = pierna.get("pedido")
        if aplicado and pedido and int(aplicado) >= int(pedido):
            techo += 1
        elif aplicado and (antes is None or int(aplicado) > int(antes or 0)):
            subio += 1
            print(f"[PALANCA] {nombre} {antes or 0}x → {aplicado}x (techo {pedido}x)", flush=True)
        else:
            quieto += 1
            if quieto <= 8:
                aviso = (out.get("avisos") or ["sin aviso"])[0]
                print(f"[PALANCA] {nombre} quieto {aviso}", flush=True)
        if i % 40 == 0:
            print(f"[PALANCA] van {i}/{len(nombres)}", flush=True)
        await asyncio.sleep(_PAUSA_PAR_S)
    return f"techo {techo} · subieron {subio} · quietos {quieto} · pares {len(nombres)}"


async def _main() -> None:
    while True:
        t0 = time.time()
        nombres = _nombres()
        linea = await _una_ronda(nombres)
        print(f"[PALANCA] {time.strftime('%H:%M:%S')} {linea}", flush=True)
        espera = max(30.0, _RONDA_S - (time.time() - t0))
        await asyncio.sleep(espera)


if __name__ == "__main__":
    asyncio.run(_main())
