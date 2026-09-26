"""Manos OKX del escudo BTC — BTC-USD-SWAP.

Oficio aparte del altar Beru (lineal USDT).
Monarca 2026-09-24: entradas por defecto a **market**; limit opcional.
Candado: el llamador exige ``IGRIS_ESCUDO_BTC_LIVE_OK`` antes de invocar.
"""
from __future__ import annotations

import math
import time
import uuid
from typing import Any

from core import okx_rest
from core.igris_escudo_btc import (
    LimiteEscudoPendiente,
    MetaEscudoBtc,
    LibroEscudoSim,
    escudo_familia,
    escudo_ord_tipo,
    escudo_veda_s,
    filtros_escudo_btc,
    inst_escudo_btc,
    masa_a_qty_escudo,
    mirar_escudo_btc_detalle_okx,
    mirar_escudo_btc_vivo_okx,
    precio_limite_inicial,
)


def _tick_sz() -> float:
    f = filtros_escudo_btc("inverso")
    return max(0.1, float(f.get("tickSz") or 0.1))


def cuantizar_px_escudo(px: float) -> float:
    """Tick OKX BTC-USD-SWAP = 0.1."""
    tick = _tick_sz()
    if tick <= 0 or px <= 0:
        return 0.0
    return math.floor(float(px) / tick + 1e-12) * tick


def mid_btc_escudo() -> float:
    """Last/mid público del frente del escudo (default inverso)."""
    inst = inst_escudo_btc()
    try:
        row = okx_rest.ticker_swap(inst)
        last = float(row.get("last") or 0)
        if last > 0:
            return last
        bid = float(row.get("bidPx") or 0)
        ask = float(row.get("askPx") or 0)
        if bid > 0 and ask > 0:
            return (bid + ask) / 2.0
        return bid or ask or 0.0
    except Exception:
        return 0.0


def _cl_ord_id(prefix: str = "ESC") -> str:
    # OKX: alfanumérico ≤32
    return f"{prefix}{uuid.uuid4().hex[:16]}"[:32]


def _pos_side_para(lado: str, *, reduce: bool) -> str | None:
    """En piernas: long/short. Si la cuenta está en neto, el llamador omite."""
    lado_u = str(lado or "").upper()
    if lado_u == "LONG":
        return "long"
    if lado_u == "SHORT":
        return "short"
    return None


def _cuenta_en_piernas() -> bool:
    try:
        rows = okx_rest.get_private("/api/v5/account/config")
        row = (list(rows or []) or [{}])[0]
        return str(row.get("posMode") or "") == "long_short_mode"
    except Exception:
        return True  # Beru fuerza piernas; asumir sí


def cancelar_orden_escudo(
    *,
    ord_id: str = "",
    cl_ord_id: str = "",
) -> dict[str, Any]:
    inst = inst_escudo_btc()
    body: dict[str, Any] = {"instId": inst}
    if ord_id:
        body["ordId"] = str(ord_id)
    elif cl_ord_id:
        body["clOrdId"] = str(cl_ord_id)
    else:
        return {"ok": False, "aviso": "sin_id"}
    try:
        data = okx_rest.post_private("/api/v5/trade/cancel-order", body)
        return {"ok": True, "data": data}
    except okx_rest.OkxRestError as exc:
        msg = str(exc)
        # Ya inexistente / filled → ok blando
        if any(x in msg.lower() for x in ("51400", "not exist", "already", "51603")):
            return {"ok": True, "aviso": "ya_fuera", "msg": msg}
        return {"ok": False, "aviso": msg}


def enmendar_px_escudo(
    *,
    ord_id: str,
    nuevo_px: float,
    cl_ord_id: str = "",
) -> dict[str, Any]:
    """Amend precio — sigue siendo limit."""
    inst = inst_escudo_btc()
    px = cuantizar_px_escudo(nuevo_px)
    if px <= 0:
        return {"ok": False, "aviso": "px_invalido"}
    body: dict[str, Any] = {
        "instId": inst,
        "ordId": str(ord_id),
        "newPx": str(px),
    }
    if cl_ord_id:
        body["clOrdId"] = str(cl_ord_id)
    try:
        data = okx_rest.post_private("/api/v5/trade/amend-order", body)
        return {"ok": True, "px": px, "data": data, "ordType": "limit"}
    except okx_rest.OkxRestError as exc:
        return {"ok": False, "aviso": str(exc), "px": px}


def plantar_limit_escudo_okx(
    *,
    lado: str,
    qty: float,
    mid: float,
    reduce_only: bool = False,
    meta_usd: float = 0.0,
) -> dict[str, Any]:
    """Planta límite maker en BTC-USD-SWAP."""
    if not okx_rest.credenciales_ok():
        return {"ok": False, "aviso": "sin_credenciales_okx"}
    lado_u = str(lado or "").upper()
    if lado_u not in ("LONG", "SHORT"):
        return {"ok": False, "aviso": "lado_invalido"}
    q = float(qty or 0)
    if q <= 0:
        return {"ok": False, "aviso": "qty_cero"}
    mid_f = float(mid or 0) or mid_btc_escudo()
    if mid_f <= 0:
        return {"ok": False, "aviso": "sin_mid"}

    px = cuantizar_px_escudo(precio_limite_inicial(lado_u, mid_f))
    if px <= 0:
        return {"ok": False, "aviso": "px_cero"}

    side_okx = "buy" if lado_u == "LONG" else "sell"
    cl = _cl_ord_id()
    # sz: contratos OKX — string limpio
    f = filtros_escudo_btc()
    lot = float(f.get("lotSz") or 0.1)
    # redondeo a lot
    n_lots = math.floor(q / lot + 1e-12)
    if n_lots <= 0:
        return {"ok": False, "aviso": "qty_bajo_lot", "lot": lot}
    sz = n_lots * lot
    # evitar basura float
    sz_s = f"{sz:.8f}".rstrip("0").rstrip(".")

    body: dict[str, Any] = {
        "instId": inst_escudo_btc(),
        "tdMode": "cross",
        "side": side_okx,
        "ordType": "limit",
        "sz": sz_s,
        "px": str(px),
        "clOrdId": cl,
    }
    if _cuenta_en_piernas():
        ps = _pos_side_para(lado_u, reduce=reduce_only)
        if ps:
            body["posSide"] = ps
    if reduce_only:
        body["reduceOnly"] = True

    try:
        data = okx_rest.post_private("/api/v5/trade/order", body)
        rows = list(data or [])
        oid = str((rows[0] if rows else {}).get("ordId") or "")
        pend = LimiteEscudoPendiente(
            lado=lado_u,
            qty=float(sz),
            px=float(px),
            px_origen=float(px),
            ts_planta=time.time(),
            ts_ultimo_mov=time.time(),
            n_moves=0,
            meta_usd=float(meta_usd or 0),
        )
        return {
            "ok": True,
            "modo": "live",
            "ordType": "limit",
            "order_id": oid,
            "clOrdId": cl,
            "lado": lado_u,
            "qty": float(sz),
            "px": float(px),
            "mid": mid_f,
            "reduce_only": bool(reduce_only),
            "instId": inst_escudo_btc(),
            "familia": escudo_familia(),
            "pendiente": pend,
            "frase": f"limit {lado_u} sz={sz_s} @ {px} (maker)",
        }
    except okx_rest.OkxRestError as exc:
        return {
            "ok": False,
            "modo": "live",
            "ordType": "limit",
            "aviso": str(exc),
            "frase": f"OKX rechazó limit: {exc}",
        }


def plantar_market_escudo_okx(
    *,
    lado: str,
    qty: float,
    mid: float = 0.0,
    reduce_only: bool = False,
    meta_usd: float = 0.0,
) -> dict[str, Any]:
    """Planta market (taker) en BTC-USD-SWAP — fill inmediato."""
    if not okx_rest.credenciales_ok():
        return {"ok": False, "aviso": "sin_credenciales_okx"}
    lado_u = str(lado or "").upper()
    if lado_u not in ("LONG", "SHORT"):
        return {"ok": False, "aviso": "lado_invalido"}
    q = float(qty or 0)
    if q <= 0:
        return {"ok": False, "aviso": "qty_cero"}
    mid_f = float(mid or 0) or mid_btc_escudo()

    side_okx = "buy" if lado_u == "LONG" else "sell"
    cl = _cl_ord_id()
    f = filtros_escudo_btc()
    lot = float(f.get("lotSz") or 0.1)
    n_lots = math.floor(q / lot + 1e-12)
    if n_lots <= 0:
        return {"ok": False, "aviso": "qty_bajo_lot", "lot": lot}
    sz = n_lots * lot
    sz_s = f"{sz:.8f}".rstrip("0").rstrip(".")

    body: dict[str, Any] = {
        "instId": inst_escudo_btc(),
        "tdMode": "cross",
        "side": side_okx,
        "ordType": "market",
        "sz": sz_s,
        "clOrdId": cl,
    }
    if _cuenta_en_piernas():
        ps = _pos_side_para(lado_u, reduce=reduce_only)
        if ps:
            body["posSide"] = ps
    if reduce_only:
        body["reduceOnly"] = True

    try:
        data = okx_rest.post_private("/api/v5/trade/order", body)
        rows = list(data or [])
        oid = str((rows[0] if rows else {}).get("ordId") or "")
        return {
            "ok": True,
            "modo": "live",
            "ordType": "market",
            "order_id": oid,
            "clOrdId": cl,
            "lado": lado_u,
            "qty": float(sz),
            "px": float(mid_f or 0),
            "mid": mid_f,
            "reduce_only": bool(reduce_only),
            "instId": inst_escudo_btc(),
            "familia": escudo_familia(),
            "pendiente": None,
            "frase": f"market {lado_u} sz={sz_s} (taker)",
        }
    except okx_rest.OkxRestError as exc:
        return {
            "ok": False,
            "modo": "live",
            "ordType": "market",
            "aviso": str(exc),
            "frase": f"OKX rechazó market: {exc}",
        }


def _confirmar_vivo_post_market(
    *,
    esperado_signed: float,
    tolerancia_usd: float = 80.0,
    intentos: int = 5,
    pausa_s: float = 0.45,
) -> dict[str, Any]:
    """Relee el ojo hasta ver fill o declarar ciego (no inventar 0)."""
    ultimo: dict[str, Any] = {"ciego": True, "signed": None}
    for _ in range(max(1, intentos)):
        time.sleep(max(0.1, pausa_s))
        ultimo = mirar_escudo_btc_detalle_okx()
        if ultimo.get("ciego"):
            continue
        vivo = float(ultimo.get("signed") or 0)
        if abs(vivo - float(esperado_signed)) <= float(tolerancia_usd):
            return {
                "ok": True,
                "ciego": False,
                "vivo": vivo,
                "confirmado": True,
                "aviso": "",
            }
        # Fill parcial / lag: si ya no es 0 y se movió hacia la meta, aceptar
        if abs(vivo) > 1e-9 or abs(esperado_signed) < 1e-9:
            return {
                "ok": True,
                "ciego": False,
                "vivo": vivo,
                "confirmado": abs(vivo - float(esperado_signed))
                <= float(tolerancia_usd) * 2,
                "aviso": "lag_parcial",
            }
    if ultimo.get("ciego"):
        return {
            "ok": False,
            "ciego": True,
            "vivo": None,
            "confirmado": False,
            "aviso": str(ultimo.get("aviso") or "ojo_ciego_post_fill"),
        }
    return {
        "ok": True,
        "ciego": False,
        "vivo": float(ultimo.get("signed") or 0),
        "confirmado": False,
        "aviso": "sin_confirmacion_estrecha",
    }


def aplicar_meta_live_okx(
    libro: LibroEscudoSim,
    meta: MetaEscudoBtc,
    *,
    precio: float | None = None,
) -> dict[str, Any]:
    """Ajusta el escudo vivo hacia la meta (market por defecto; limit opcional).

    Cirugía 2026-09-24:
    - Ojo ciego ≠ vacío: no planta.
    - Veda post-planta: no ida-vuelta en el mismo aliento.
    - ``aplicado`` solo si hubo orden real.
    """
    tipo = escudo_ord_tipo()
    if not okx_rest.credenciales_ok():
        return {
            "ok": False,
            "modo": "live",
            "aplicado": False,
            "bloqueado": False,
            "aviso": "sin_credenciales_okx",
            "ordType": tipo,
            "frase": "sin llaves OKX para el escudo",
        }

    ahora = time.time()
    veda_hasta = float(getattr(libro, "veda_hasta_ts", 0) or 0)
    if veda_hasta > ahora:
        resto = veda_hasta - ahora
        return {
            "ok": True,
            "modo": "live",
            "aplicado": False,
            "aviso": "veda_post_planta",
            "veda_s": round(resto, 1),
            "vivo": float(libro.escudo_signed_usd),
            "ordType": tipo,
            "frase": f"veda {resto:.0f}s tras último asalto — no planta",
        }

    mid = float(precio or 0) or mid_btc_escudo()
    if mid <= 0:
        return {
            "ok": False,
            "modo": "live",
            "aplicado": False,
            "aviso": "sin_precio_btc",
            "ordType": tipo,
            "frase": "ciego al mid BTC — no plantó",
        }

    # Cancelar pendiente anterior (si hay ids en historial reciente / campo extra)
    prev = libro.limite_pendiente
    cancel_info: dict[str, Any] = {"ok": True, "aviso": "sin_prev"}
    prev_oid = ""
    prev_cl = ""
    if isinstance(getattr(libro, "historial", None), list) and libro.historial:
        last = libro.historial[-1] if libro.historial else {}
        if isinstance(last, dict):
            prev_oid = str(last.get("order_id") or "")
            prev_cl = str(last.get("clOrdId") or "")
    if prev is not None:
        prev_oid = str(getattr(prev, "order_id", "") or prev_oid)
        prev_cl = str(getattr(prev, "cl_ord_id", "") or prev_cl)
    if prev_oid or prev_cl:
        cancel_info = cancelar_orden_escudo(ord_id=prev_oid, cl_ord_id=prev_cl)
        if prev is not None:
            prev.cancelado = True
        libro.limite_pendiente = None

    det = mirar_escudo_btc_detalle_okx()
    if det.get("ciego"):
        # Conservar último bueno — jamás asumir 0
        vivo_hold = (
            float(libro.vivo_ultimo_ok)
            if libro.vivo_ultimo_ok is not None
            else float(libro.escudo_signed_usd)
        )
        return {
            "ok": False,
            "modo": "live",
            "aplicado": False,
            "aviso": "ojo_ciego",
            "ciego": True,
            "vivo": vivo_hold,
            "ordType": tipo,
            "cancel": cancel_info,
            "frase": f"ojo ciego ({det.get('aviso')}) — no plantó",
        }
    vivo = float(det.get("signed") or 0.0)
    libro.vivo_ultimo_ok = vivo

    # Meta redondeada al frente
    if not meta.lado or abs(meta.usd) < 1e-12:
        target_signed = 0.0
    else:
        r = masa_a_qty_escudo(abs(meta.usd), mid, familia="inverso", modo="floor")
        if not r.get("ok"):
            return {
                "ok": False,
                "modo": "live",
                "aplicado": False,
                "aviso": "redondeo_qty_cero",
                "vivo": vivo,
                "meta": meta.usd,
                "ordType": tipo,
                "cancel": cancel_info,
                "frase": "meta no alcanza 1 paso del inverso — espera",
            }
        signo = 1.0 if meta.lado == "LONG" else -1.0
        target_signed = signo * float(r.get("notional_usd") or 0)

    boc = float(target_signed) - float(vivo)
    paso = float(filtros_escudo_btc("inverso").get("ctVal") or 100) * float(
        filtros_escudo_btc("inverso").get("lotSz") or 0.1
    )
    if abs(boc) + 1e-9 < max(paso * 0.5, 5.0):
        libro.escudo_signed_usd = vivo
        libro.meta_lado = meta.lado
        libro.meta_usd = float(meta.usd or 0)
        libro.limite_pendiente = None
        return {
            "ok": True,
            "modo": "live",
            "aplicado": False,
            "aviso": "ya_en_meta",
            "vivo": vivo,
            "target": target_signed,
            "ordType": tipo,
            "cancel": cancel_info,
            "frase": f"escudo vivo {vivo:+.0f} ≈ meta {target_signed:+.0f}",
        }

    # Candado: no abrir de nuevo el mismo sentido si el libro ya tenía masa
    # y el ojo acaba de "aparecer vacío" (desconfianza residual).
    if (
        abs(vivo) < 1e-9
        and abs(float(libro.escudo_signed_usd) or 0) > max(paso, 50.0)
        and (ahora - float(libro.ts_ultima_planta or 0)) < max(escudo_veda_s() * 2, 40.0)
    ):
        return {
            "ok": False,
            "modo": "live",
            "aplicado": False,
            "aviso": "sospecha_ojo_vacio",
            "vivo": vivo,
            "papel": float(libro.escudo_signed_usd),
            "ordType": tipo,
            "frase": "ojo dice 0 pero el libro aún tiene escudo — no dobla",
        }

    lado = "LONG" if boc > 0 else "SHORT"
    reduce = False
    if abs(vivo) > 1e-9:
        mismo = (vivo > 0 and boc < 0) or (vivo < 0 and boc > 0)
        if mismo and abs(target_signed) < abs(vivo) - 1e-9:
            reduce = True
        if abs(target_signed) < 1e-9:
            reduce = True

    qty_info = masa_a_qty_escudo(abs(boc), mid, familia="inverso", modo="floor")
    if not qty_info.get("ok"):
        return {
            "ok": False,
            "modo": "live",
            "aplicado": False,
            "aviso": "bocado_bajo_paso",
            "bocado": boc,
            "ordType": tipo,
            "cancel": cancel_info,
            "frase": "bocado no alcanza 1 contrato — espera",
        }

    if tipo == "market":
        plant = plantar_market_escudo_okx(
            lado=lado,
            qty=float(qty_info.get("qty") or 0),
            mid=mid,
            reduce_only=reduce,
            meta_usd=float(meta.usd or 0),
        )
    else:
        plant = plantar_limit_escudo_okx(
            lado=lado,
            qty=float(qty_info.get("qty") or 0),
            mid=mid,
            reduce_only=reduce,
            meta_usd=float(meta.usd or 0),
        )
    if not plant.get("ok"):
        plant["cancel"] = cancel_info
        plant["vivo"] = vivo
        plant["bocado"] = boc
        plant["aplicado"] = False
        return plant

    libro.limite_pendiente = None
    esperado = float(vivo) + float(boc)
    if tipo == "limit":
        pend = plant.get("pendiente")
        if isinstance(pend, LimiteEscudoPendiente):
            setattr(pend, "order_id", plant.get("order_id") or "")
            setattr(pend, "cl_ord_id", plant.get("clOrdId") or "")
            libro.limite_pendiente = pend
        libro.escudo_signed_usd = vivo
    else:
        conf = _confirmar_vivo_post_market(
            esperado_signed=esperado,
            tolerancia_usd=max(paso * 2, 50.0),
        )
        if conf.get("ciego") or conf.get("vivo") is None:
            # Fill enviado pero ojo ciego: confiar en esperado + veda dura
            libro.escudo_signed_usd = esperado
            libro.vivo_ultimo_ok = esperado
            vivo = esperado
            plant["confirm"] = conf
        else:
            vivo2 = float(conf.get("vivo") or 0)
            libro.escudo_signed_usd = vivo2
            libro.vivo_ultimo_ok = vivo2
            vivo = vivo2
            plant["confirm"] = conf

    # Veda anti ida-vuelta
    veda = escudo_veda_s()
    libro.ts_ultima_planta = ahora
    libro.veda_hasta_ts = ahora + veda
    libro.lado_ultima_planta = lado

    libro.meta_lado = meta.lado
    libro.meta_usd = float(meta.usd or 0)
    libro.n_ajustes = int(libro.n_ajustes) + 1
    libro.ts = time.time()
    libro.historial.append(
        {
            "ts": time.time(),
            "evento": "plant_market_live" if tipo == "market" else "plant_limit_live",
            "lado": lado,
            "qty": plant.get("qty"),
            "px": plant.get("px"),
            "order_id": plant.get("order_id"),
            "clOrdId": plant.get("clOrdId"),
            "bocado": boc,
            "vivo_pre": float(det.get("signed") or 0),
            "vivo": vivo,
            "target": target_signed,
            "reduce_only": reduce,
            "ordType": tipo,
            "veda_s": veda,
        }
    )
    libro.historial = libro.historial[-40:]

    return {
        "ok": True,
        "modo": "live",
        "aplicado": True,
        "bloqueado": False,
        "ordType": tipo,
        "vivo": vivo,
        "target": target_signed,
        "bocado": boc,
        "orden": plant,
        "cancel": cancel_info,
        "veda_s": veda,
        "frase": plant.get("frase") or f"{tipo} {lado} plantado",
    }


def mover_limite_live_okx(
    libro: LibroEscudoSim,
    mid: float | None = None,
) -> dict[str, Any]:
    """Si hay límite pendiente sin fill, acerca el px (amend). No-op en market."""
    if escudo_ord_tipo() == "market":
        if libro.limite_pendiente is not None:
            libro.limite_pendiente = None
        return {
            "ok": True,
            "movido": False,
            "aviso": "modo_market",
            "ordType": "market",
            "frase": "market — sin chase de limit",
        }
    from core.igris_escudo_btc import decidir_mover_limite, aplicar_mover_limite

    pend = libro.limite_pendiente
    if pend is None or not pend.vivo():
        return {"ok": True, "movido": False, "aviso": "sin_pendiente", "ordType": "limit"}
    mid_f = float(mid or 0) or mid_btc_escudo()
    decision = decidir_mover_limite(pend, mid_f)
    if not decision.get("mover"):
        return {
            "ok": True,
            "movido": False,
            "decision": decision,
            "ordType": "limit",
            "frase": f"limit quieto [{decision.get('motivo')}]",
        }
    oid = str(getattr(pend, "order_id", "") or "")
    if not oid:
        # sin id no se puede amend en vivo — solo memoria
        aplicar_mover_limite(pend, decision)
        libro.limite_pendiente = pend
        return {
            "ok": True,
            "movido": True,
            "aviso": "solo_memoria_sin_ord_id",
            "decision": decision,
            "ordType": "limit",
        }
    en = enmendar_px_escudo(ord_id=oid, nuevo_px=float(decision["px_nuevo"]))
    if not en.get("ok"):
        return {
            "ok": False,
            "movido": False,
            "aviso": en.get("aviso"),
            "decision": decision,
            "ordType": "limit",
            "frase": f"amend falló: {en.get('aviso')}",
        }
    aplicar_mover_limite(pend, decision)
    pend.px = float(en.get("px") or pend.px)
    libro.limite_pendiente = pend
    return {
        "ok": True,
        "movido": True,
        "decision": decision,
        "amend": en,
        "ordType": "limit",
        "frase": decision.get("frase"),
    }
