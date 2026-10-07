"""Manos del escudo de dos metales. Rey e reina, cada uno su inverso.

No abre si no hay capa que sentar. Si la casa no responde, no inventa un cero.
Si el lado voltea, este latido solo sienta en cero.
"""
from __future__ import annotations

import time
import uuid

REINA = "ETH-USD-SWAP"
REY = "BTC-USD-SWAP"
INST = REINA

_FILTROS_CACHE: dict[str, tuple[float, dict]] = {}
_PIERNAS_CACHE: tuple[float, bool] | None = None
_FILTROS_TTL = 300.0
_PIERNAS_TTL = 120.0
_REINTENTOS = 5


def sentado(inst: str) -> float | None:
    """Dólares firmados del metal. None si el ojo no ve."""
    pares = sentados((inst,))
    return pares.get(inst)


def sentados(insts: tuple[str, ...] | list[str] | None = None) -> dict[str, float | None]:
    """Lee varios metales con menos golpes a la casa.

    Una sola foto de piernas SWAP cuando se puede. Reintenta si la casa
    aprieta (50011). None = ciego de verdad, no un cero inventado.
    """
    from core import okx_rest

    pedidos = tuple(insts) if insts is not None else (REY, REINA)
    out: dict[str, float | None] = {inst: None for inst in pedidos}
    if not okx_rest.credenciales_ok():
        return out

    filtros: dict[str, dict] = {}
    for inst in pedidos:
        f = _filtros(okx_rest, inst)
        if f is None:
            out[inst] = None
        else:
            filtros[inst] = f

    vivos = _vivos_lote(okx_rest, tuple(filtros.keys()))
    for inst, f in filtros.items():
        if inst not in vivos:
            out[inst] = None
        else:
            out[inst] = float(vivos[inst]) * f["ct"]
    return out


def ajustar(meta_signed_usd: float, inst: str = INST) -> dict:
    """Acerca ese metal a la meta. Cero contra cero no manda orden."""
    from core import okx_rest

    if not okx_rest.credenciales_ok():
        return {"aplicado": False, "frase": "sin llaves"}
    filtros = _filtros(okx_rest, inst)
    if filtros is None:
        return {"aplicado": False, "frase": "sin talla"}
    vivos = _vivos_lote(okx_rest, (inst,))
    if inst not in vivos:
        return {"aplicado": False, "frase": "ojo ciego, no planta"}
    vivo = float(vivos[inst] or 0) * filtros["ct"]
    meta = float(meta_signed_usd or 0)
    paso = filtros["ct"] * filtros["lot"]
    if vivo * meta < 0 and abs(vivo) > paso * 0.5:
        meta = 0.0
    if abs(meta - vivo) + 1e-9 < max(paso * 0.5, 1.0):
        return {"aplicado": False, "frase": "ya en la capa", "vivo": vivo}
    boc = meta - vivo
    pasos = int(abs(boc) / paso + 1e-9)
    qty = pasos * filtros["lot"]
    if qty + 1e-12 < filtros["min"]:
        return {"aplicado": False, "frase": "no alcanza un contrato", "vivo": vivo}
    reduce = (vivo > 0 and boc < 0) or (vivo < 0 and boc > 0)
    if reduce and abs(meta) > abs(vivo) + 1e-9:
        reduce = False
    nombre = "reina" if inst == REINA else "rey"
    cuerpo = {
        "instId": inst,
        "tdMode": "cross",
        "side": "buy" if boc > 0 else "sell",
        "ordType": "market",
        "sz": f"{qty:.8f}".rstrip("0").rstrip("."),
        "clOrdId": ((nombre[:3].upper() + uuid.uuid4().hex)[:32]),
    }
    if reduce:
        cuerpo["reduceOnly"] = True
    if _en_piernas(okx_rest):
        if vivo > 0:
            cuerpo["posSide"] = "long"
        elif vivo < 0:
            cuerpo["posSide"] = "short"
        elif boc > 0:
            cuerpo["posSide"] = "long"
        else:
            cuerpo["posSide"] = "short"
    else:
        cuerpo["posSide"] = "net"
    try:
        data = _con_reintento(
            lambda: okx_rest.post_private("/api/v5/trade/order", cuerpo)
        )
    except Exception as exc:
        code = str(getattr(exc, "code", "") or "")
        return {
            "aplicado": False,
            "frase": f"la casa no respondió ({code or type(exc).__name__})",
            "vivo": vivo,
        }
    fila = (list(data or [{}]) or [{}])[0]
    if str((fila or {}).get("sCode") or "0") not in ("0", ""):
        msg = str((fila or {}).get("sMsg") or "rechazo")
        return {"aplicado": False, "frase": f"la casa rechazó ({msg})", "vivo": vivo}
    return {"aplicado": True, "frase": f"{nombre} {cuerpo['side']} {cuerpo['sz']}", "vivo": vivo}


def _filtros(okx, inst: str = INST) -> dict | None:
    ahora = time.time()
    cached = _FILTROS_CACHE.get(inst)
    if cached is not None and ahora - cached[0] < _FILTROS_TTL:
        return dict(cached[1])
    try:
        pub = _con_reintento(
            lambda: okx.get_public(
                "/api/v5/public/instruments",
                params={"instType": "SWAP", "instId": inst},
            )
            or []
        )
    except Exception:
        return None
    if not pub or not isinstance(pub[0], dict):
        return None
    fila = pub[0]
    try:
        ct = float(fila.get("ctVal") or 0)
        lot = float(fila.get("lotSz") or 0)
        minimo = float(fila.get("minSz") or lot)
    except (TypeError, ValueError):
        return None
    if ct <= 0 or lot <= 0 or minimo <= 0:
        return None
    out = {"ct": ct, "lot": lot, "min": minimo}
    _FILTROS_CACHE[inst] = (ahora, out)
    return dict(out)


def _pos_firmada(fila: dict) -> float | None:
    """Contratos firmados. En piernas, pos es magnitud y el lado manda el signo."""
    try:
        qty = float(fila.get("pos") or 0)
    except (TypeError, ValueError):
        return None
    lado = str(fila.get("posSide") or "net").strip().lower()
    if lado == "short":
        return -abs(qty)
    if lado == "long":
        return abs(qty)
    return qty


def _vivos_lote(okx, insts: tuple[str, ...]) -> dict[str, float]:
    """Contratos firmados por instId. Clave ausente = ciego. 0.0 = plano."""
    if not insts:
        return {}
    for intento in range(_REINTENTOS):
        try:
            filas = okx.get_private(
                "/api/v5/account/positions",
                params={"instType": "SWAP"},
            ) or []
        except Exception as exc:
            if _es_atasco(exc) and intento + 1 < _REINTENTOS:
                time.sleep(0.45 * (intento + 1))
                continue
            return _vivos_uno_a_uno(okx, insts)
        hallados: dict[str, float] = {inst: 0.0 for inst in insts}
        rotos: set[str] = set()
        for fila in filas:
            if not isinstance(fila, dict):
                continue
            inst = str(fila.get("instId") or "")
            if inst not in hallados:
                continue
            firmada = _pos_firmada(fila)
            if firmada is None:
                rotos.add(inst)
                continue
            hallados[inst] = float(hallados.get(inst) or 0) + firmada
        for inst in rotos:
            hallados.pop(inst, None)
        return hallados
    return {}


def _vivos_uno_a_uno(okx, insts: tuple[str, ...]) -> dict[str, float]:
    hallados: dict[str, float] = {}
    for inst in insts:
        for intento in range(_REINTENTOS):
            try:
                filas = okx.get_private(
                    "/api/v5/account/positions",
                    params={"instType": "SWAP", "instId": inst},
                ) or []
            except Exception as exc:
                if _es_atasco(exc) and intento + 1 < _REINTENTOS:
                    time.sleep(0.45 * (intento + 1))
                    continue
                break
            total = 0.0
            roto = False
            for fila in filas:
                if not isinstance(fila, dict) or str(fila.get("instId")) != inst:
                    continue
                firmada = _pos_firmada(fila)
                if firmada is None:
                    roto = True
                    break
                total += firmada
            if not roto:
                hallados[inst] = total
            break
    return hallados


def _en_piernas(okx) -> bool:
    global _PIERNAS_CACHE
    ahora = time.time()
    if _PIERNAS_CACHE is not None and ahora - _PIERNAS_CACHE[0] < _PIERNAS_TTL:
        return _PIERNAS_CACHE[1]
    try:
        filas = _con_reintento(lambda: okx.get_private("/api/v5/account/config") or [])
        modo = str((list(filas) or [{}])[0].get("posMode") or "")
    except Exception:
        return False
    ok = modo == "long_short_mode"
    _PIERNAS_CACHE = (ahora, ok)
    return ok


def _con_reintento(fn):
    ultimo = None
    for intento in range(_REINTENTOS):
        try:
            return fn()
        except Exception as exc:
            ultimo = exc
            if _es_atasco(exc) and intento + 1 < _REINTENTOS:
                time.sleep(0.45 * (intento + 1))
                continue
            raise
    raise ultimo  # type: ignore[misc]


def _es_atasco(exc: BaseException) -> bool:
    texto = str(exc).lower()
    code = str(getattr(exc, "code", "") or "")
    return code == "50011" or "50011" in texto or "rate" in texto or "too many" in texto
