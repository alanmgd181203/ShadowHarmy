"""Cierra TODAS las posiciones SWAP y cancela órdenes pendientes.

NO toca spot / margen spot de BTC.
Corre en la viejita con el ejército ya apagado.
"""
from __future__ import annotations

import os
import sys
import time
import uuid
from pathlib import Path

ROOT = Path(r"C:\Users\lenovo\ShadowHarmy")
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))
os.environ.setdefault("BERU_MAR", "okx")

from core import okx_rest


def _retry(fn, intentos: int = 8):
    ultimo = None
    for i in range(intentos):
        try:
            return fn()
        except Exception as exc:
            ultimo = exc
            texto = str(exc).lower()
            if "50011" in texto or "rate" in texto or "too many" in texto:
                time.sleep(0.7 * (intento := i + 1))
                continue
            time.sleep(0.4 * (i + 1))
    raise ultimo  # type: ignore[misc]


def _cl(pref: str) -> str:
    return (pref + uuid.uuid4().hex)[:32]


def cancelar_pendientes() -> int:
    n = 0
    # Órdenes normales
    try:
        pend = _retry(
            lambda: okx_rest.get_private(
                "/api/v5/trade/orders-pending",
                params={"instType": "SWAP"},
            )
            or []
        )
    except Exception as exc:
        print("PEND_FALLO", str(exc)[:100])
        pend = []
    for o in pend:
        if not isinstance(o, dict):
            continue
        inst = str(o.get("instId") or "")
        oid = str(o.get("ordId") or "")
        if not inst or not oid:
            continue
        try:
            _retry(
                lambda i=inst, o=oid: okx_rest.post_private(
                    "/api/v5/trade/cancel-order",
                    {"instId": i, "ordId": o},
                )
            )
            n += 1
            print("CANCEL_ORD", inst, oid)
        except Exception as exc:
            print("CANCEL_ORD_FALLO", inst, str(exc)[:80])
        time.sleep(0.15)

    # Algos / triggers
    for ord_type in ("conditional", "trigger", "oco", "move_order_stop", "chase"):
        try:
            algos = _retry(
                lambda ot=ord_type: okx_rest.get_private(
                    "/api/v5/trade/orders-algo-pending",
                    params={"instType": "SWAP", "ordType": ot},
                )
                or []
            )
        except Exception:
            algos = []
        for o in algos:
            if not isinstance(o, dict):
                continue
            inst = str(o.get("instId") or "")
            aid = str(o.get("algoId") or "")
            if not inst or not aid:
                continue
            try:
                _retry(
                    lambda i=inst, a=aid: okx_rest.post_private(
                        "/api/v5/trade/cancel-algos",
                        [{"instId": i, "algoId": a}],
                    )
                )
                n += 1
                print("CANCEL_ALGO", inst, aid, ord_type)
            except Exception as exc:
                print("CANCEL_ALGO_FALLO", inst, str(exc)[:80])
            time.sleep(0.15)
    return n


def cerrar_swaps() -> tuple[int, int]:
    """Cierra todo SWAP. No mira spot."""
    ok = fallos = 0
    try:
        filas = _retry(
            lambda: okx_rest.get_private(
                "/api/v5/account/positions",
                params={"instType": "SWAP"},
            )
            or []
        )
    except Exception as exc:
        print("POS_FALLO", str(exc)[:120])
        return 0, 1

    # Config modo
    try:
        cfg = _retry(lambda: okx_rest.get_private("/api/v5/account/config") or [])
        modo = str((list(cfg) or [{}])[0].get("posMode") or "")
    except Exception:
        modo = ""
    piernas = modo == "long_short_mode"
    print("posMode=", modo)

    for f in filas:
        if not isinstance(f, dict):
            continue
        inst = str(f.get("instId") or "")
        if not inst:
            continue
        # Nunca tocar spot aquí: este endpoint es SWAP. BTC spot margen queda fuera.
        try:
            pos = float(f.get("pos") or 0)
        except (TypeError, ValueError):
            continue
        if abs(pos) < 1e-12:
            continue
        side_pos = str(f.get("posSide") or "net").lower()
        qty = abs(pos)
        if piernas and side_pos in ("long", "short"):
            # cerrar long = sell; cerrar short = buy
            side = "sell" if side_pos == "long" else "buy"
            cuerpo = {
                "instId": inst,
                "tdMode": "cross",
                "side": side,
                "ordType": "market",
                "sz": f"{qty:.8f}".rstrip("0").rstrip("."),
                "reduceOnly": True,
                "posSide": side_pos,
                "clOrdId": _cl("APL"),
            }
        else:
            # neto: pos>0 long → sell; pos<0 short → buy
            side = "sell" if pos > 0 else "buy"
            cuerpo = {
                "instId": inst,
                "tdMode": "cross",
                "side": side,
                "ordType": "market",
                "sz": f"{qty:.8f}".rstrip("0").rstrip("."),
                "reduceOnly": True,
                "clOrdId": _cl("APL"),
            }
            if piernas:
                cuerpo["posSide"] = "long" if pos > 0 else "short"

        for intento in range(5):
            try:
                data = okx_rest.post_private("/api/v5/trade/order", cuerpo)
                fila = (list(data or [{}]) or [{}])[0]
                sc = str((fila or {}).get("sCode") or "0")
                if sc not in ("0", ""):
                    print("CIERRE_RECHAZO", inst, side_pos, fila.get("sMsg"))
                    fallos += 1
                else:
                    print(
                        "CIERRE_OK",
                        inst,
                        side_pos or "net",
                        "sz=",
                        cuerpo["sz"],
                        "ord=",
                        fila.get("ordId"),
                    )
                    ok += 1
                break
            except Exception as exc:
                if "50011" in str(exc) and intento + 1 < 5:
                    time.sleep(0.8 * (intento + 1))
                    continue
                print("CIERRE_FALLO", inst, str(exc)[:100])
                fallos += 1
                break
        time.sleep(0.2)
    return ok, fallos


def verificar() -> None:
    try:
        filas = _retry(
            lambda: okx_rest.get_private(
                "/api/v5/account/positions",
                params={"instType": "SWAP"},
            )
            or []
        )
    except Exception as exc:
        print("VERIFY_FALLO", str(exc)[:100])
        return
    vivos = []
    for f in filas:
        if not isinstance(f, dict):
            continue
        try:
            pos = float(f.get("pos") or 0)
        except (TypeError, ValueError):
            continue
        if abs(pos) > 1e-12:
            vivos.append(
                (
                    f.get("instId"),
                    f.get("posSide"),
                    f.get("pos"),
                    f.get("notionalUsd"),
                )
            )
    print("SWAP_VIVOS_TRAS_CIERRE", len(vivos))
    for v in vivos[:30]:
        print("  QUEDA", v)

    # Spot BTC: solo informar, no tocar
    try:
        bals = _retry(
            lambda: okx_rest.get_private(
                "/api/v5/account/balance",
                params={"ccy": "BTC"},
            )
            or []
        )
        print("BTC_SPOT_MARGEN_NO_TOCADO balance_vista=", bals[:1] if bals else bals)
    except Exception as exc:
        print("BTC_BAL_INFO", str(exc)[:80])


def main() -> None:
    print("=== CANCELAR PENDIENTES SWAP ===")
    n = cancelar_pendientes()
    print("CANCELADAS", n)
    print("=== CERRAR POSICIONES SWAP ===")
    ok, fallos = cerrar_swaps()
    print("CIERRES_OK", ok, "FALLOS", fallos)
    time.sleep(2)
    # segunda pasada por si quedó polvo
    print("=== SEGUNDA PASADA ===")
    cancelar_pendientes()
    ok2, fallos2 = cerrar_swaps()
    print("CIERRES_OK2", ok2, "FALLOS2", fallos2)
    time.sleep(2)
    print("=== VERIFICAR ===")
    verificar()
    print("HECHO_salvo_BTC_spot")


if __name__ == "__main__":
    main()
