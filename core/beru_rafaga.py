"""Red de ráfaga Beru — bocados mínimos si la Hoz gorda no cabe en la bóveda.

Camino feliz: una sola Hoz condicional con toda la masa. Cero Market.
Solo si Bybit escupe por ahogo (no por qty/símbolo):

1. Hoz mínima en el altar; el resto acecha y sale en ráfaga al fill.
2. Ni el mínimo entra: radar interno. Al tocar oz, Beru dispara la ráfaga.

Empaque: tantos bocados al lote mínimo como quepan; el resto se absorbe
en los últimos (40→ocho de 5; 42→seis de 5 y dos de 6). Polvo < mínimo:
nunca se planta. Techo de bocados para no ahogar el pulso de la flota.
"""
from __future__ import annotations

import asyncio
import hashlib
import re
import time
from typing import Any

import core.config as config
from core import lote_bybit

MODO_MINIMA = "MINIMA"
MODO_RADAR = "RADAR"

# Códigos Bybit típicos de saldo/margen. Lote/mínimo NO se trocean.
AHOGO_RETCODES = frozenset({
    110007, 110012, 110014, 110044,
    170131, 170137, 170033,
    30208, 30031,
})
# 170140 = valor bajo el mínimo (casa leyó monedas como dólares, o polvo).
LOTE_RETCODES = frozenset({170140, 170134, 170124})
AHOGO_FRASES = (
    "not enough",
    "insufficient",
    "available balance",
    "ab not enough",
    "cannot afford",
    "can't afford",
    "can't open",
    "cannot open",
    "buying power",
    "not enough margin",
    "margin not enough",
    "abnormal available",
)


def modo_hoz(beru: Any) -> str:
    return str(getattr(beru, "hoz_modo", "") or "").upper()


def es_radar(beru: Any) -> bool:
    return modo_hoz(beru) == MODO_RADAR


def es_minima(beru: Any) -> bool:
    return modo_hoz(beru) == MODO_MINIMA


def masa_para_carta(beru: Any) -> float:
    """USD que debe llevar la carta condicional (no el resto en acecho)."""
    modo = modo_hoz(beru)
    if modo == MODO_RADAR:
        return 0.0
    if modo == MODO_MINIMA:
        carta = float(getattr(beru, "masa_carta_usd", 0) or 0)
        if carta > 0:
            return carta
    return float(getattr(beru, "masa", 0) or 0)


def sincronizar_masa_rafaga(beru: Any) -> None:
    """Tras engorde: la carta mínima no crece; el extra va a la ráfaga."""
    masa = float(getattr(beru, "masa", 0) or 0)
    modo = modo_hoz(beru)
    if modo == MODO_RADAR:
        beru.masa_rafaga_usd = round(masa, 6)
        beru.masa_carta_usd = 0.0
        return
    if modo == MODO_MINIMA:
        carta = float(getattr(beru, "masa_carta_usd", 0) or 0)
        beru.masa_rafaga_usd = max(0.0, round(masa - carta, 6))
        return
    beru.masa_carta_usd = masa
    beru.masa_rafaga_usd = 0.0


def marcar_hoz_completa(beru: Any, masa_carta: float) -> None:
    beru.hoz_modo = ""
    beru.masa_carta_usd = float(masa_carta or 0)
    beru.masa_rafaga_usd = 0.0
    beru.rafaga_hecha = False
    beru.qty_rafaga_acum = 0.0


def marcar_hoz_minima(beru: Any, masa_carta: float) -> None:
    carta = max(0.0, float(masa_carta or 0))
    masa = float(getattr(beru, "masa", 0) or 0)
    beru.hoz_modo = MODO_MINIMA
    beru.masa_carta_usd = carta
    beru.masa_rafaga_usd = max(0.0, round(masa - carta, 6))
    beru.rafaga_hecha = False
    beru.qty_rafaga_acum = 0.0


def activar_radar(beru: Any) -> None:
    masa = float(getattr(beru, "masa", 0) or 0)
    beru.hoz_modo = MODO_RADAR
    beru.altar_link_id = ""
    beru.altar_order_id = ""
    beru.altar_order_status = "RADAR"
    beru.masa_carta_usd = 0.0
    beru.masa_rafaga_usd = round(masa, 6)
    beru.rafaga_hecha = False
    beru.rafaga_en_curso = False
    beru.qty_rafaga_acum = 0.0


def debe_rafaga(beru: Any) -> bool:
    if bool(getattr(beru, "rafaga_hecha", False)):
        return False
    if bool(getattr(beru, "rafaga_en_curso", False)):
        return False
    modo = modo_hoz(beru)
    if modo not in {MODO_MINIMA, MODO_RADAR}:
        return False
    return float(getattr(beru, "masa_rafaga_usd", 0) or 0) > 0


_RE_ERRCODE = re.compile(r"ErrCode:\s*(\d+)", re.I)
_RE_RETCODE = re.compile(r"retCode['\"]?\s*[:=]\s*(\d+)")
LOTE_FRASES = (
    "exceeded lower limit",
    "order value exceeded",
    "qty invalid",
    "quantity is invalid",
)


def retcode_de_texto(texto: str) -> int | None:
    t = str(texto or "")
    m = _RE_ERRCODE.search(t)
    if m:
        return int(m.group(1))
    m = _RE_RETCODE.search(t)
    if m:
        return int(m.group(1))
    return None


def retcode_de_resultado(resultado: Any) -> int | None:
    datos = getattr(resultado, "datos", None) or {}
    if isinstance(datos, dict) and datos.get("retCode") is not None:
        try:
            return int(datos["retCode"])
        except (TypeError, ValueError):
            pass
    return retcode_de_texto(getattr(resultado, "mensaje", "") or "")


def resultado_es_lote(resultado: Any) -> bool:
    """True si la casa escupe por valor/qty mínimo — no es ahogo de bóveda."""
    if resultado is None or bool(getattr(resultado, "exito", False)):
        return False
    code = retcode_de_resultado(resultado)
    if code in LOTE_RETCODES:
        return True
    texto = str(getattr(resultado, "mensaje", "") or "").lower()
    return any(f in texto for f in LOTE_FRASES)


def resultado_es_ahogo(resultado: Any) -> bool:
    """True solo si la casa escupió por bóveda/margen, no por lote o símbolo."""
    if resultado is None or bool(getattr(resultado, "exito", False)):
        return False
    if resultado_es_lote(resultado):
        return False
    code = retcode_de_resultado(resultado)
    if code is not None:
        return code in AHOGO_RETCODES
    texto = str(getattr(resultado, "mensaje", "") or "").lower()
    return any(f in texto for f in AHOGO_FRASES)


def empacar_bocados_usd(
    usd: float,
    min_usd: float,
    *,
    max_bocados: int | None = None,
) -> list[float]:
    """Parte USD en bocados ≥ mínimo. El resto se absorbe desde el final.

    40 / 5 → ocho de 5.  42 / 5 → seis de 5 y dos de 6.
    Por debajo del mínimo → lista vacía (polvo: no se planta).
    Si cabrían más bocados que el techo, el bocado sube (anti-tumor del pulso).
    """
    usd = round(float(usd or 0), 6)
    min_u = round(float(min_usd or 0), 6)
    if usd <= 0 or min_u <= 0 or usd + 1e-9 < min_u:
        return []
    techo = int(max_bocados if max_bocados is not None else getattr(
        config, "BERU_RAFAGA_MAX_BOCADOS", 24,
    ) or 24)
    techo = max(1, techo)
    n = int(usd // min_u)
    if n < 1:
        return []
    if n > techo:
        base = round(usd / techo, 6)
        if base + 1e-9 < min_u:
            return []
        bocados = [base] * techo
        bocados[-1] = round(usd - sum(bocados[:-1]), 6)
        if bocados[-1] + 1e-9 < min_u:
            # El último quedó corto por redondeo: se fusiona hacia atrás.
            if techo == 1:
                return []
            cabeza = bocados[:-1]
            cabeza[-1] = round(cabeza[-1] + bocados[-1], 6)
            return cabeza
        return bocados

    resto = round(usd - n * min_u, 6)
    bocados = [min_u] * n
    if resto <= 1e-9:
        return bocados
    # $42 → resto 2 → últimos 2 bocados +1. Fracción <1 se va al último.
    k = max(1, min(n, int(resto) if resto >= 1.0 else 1))
    share = round(resto / k, 6)
    for j in range(k):
        bocados[n - 1 - j] = round(bocados[n - 1 - j] + share, 6)
    diff = round(usd - sum(bocados), 6)
    if abs(diff) >= 1e-9:
        bocados[-1] = round(bocados[-1] + diff, 6)
    return [b for b in bocados if b + 1e-9 >= min_u]


def empacar_bocados(
    usd: float,
    precio: float,
    frente: str,
    *,
    direccion: str,
    max_bocados: int | None = None,
) -> tuple[list[dict[str, float]], float]:
    """Bocados ya cuantizados al lote del frente. Devuelve (lista, polvo USD).

    Ningún bocado sale por debajo del notional mínimo. El polvo se loguea;
    no viaja al altar.
    """
    px = float(precio or 0)
    frente_u = str(frente or "").upper()
    if px <= 0 or not frente_u:
        return [], round(float(usd or 0), 6)
    min_u = float(lote_bybit.paso_minimo_usd(frente_u, px) or 0)
    if min_u <= 0:
        min_u = float(getattr(config, "MIN_ORDER_USD_DEFAULT", 5.0) or 5.0)
    crudos = empacar_bocados_usd(usd, min_u, max_bocados=max_bocados)
    if not crudos:
        return [], round(float(usd or 0), 6)

    modo: lote_bybit.ModoRedondeo = (
        "ceil" if str(direccion or "").upper() == "LONG" else "floor"
    )
    out: list[dict[str, float]] = []
    leftover = 0.0
    for u in crudos:
        want = round(float(u) + leftover, 6)
        leftover = 0.0
        conv = lote_bybit.cuantizar_presupuesto_usd(want, px, frente_u, mode=modo)
        if not conv.get("ok"):
            leftover = round(leftover + want, 6)
            continue
        usd_eff = float(conv["usd"])
        qty_eff = float(conv["qty"])
        if usd_eff + 1e-9 < min_u * 0.99 or qty_eff <= 0:
            leftover = round(leftover + want, 6)
            continue
        out.append({"usd": round(usd_eff, 6), "qty": qty_eff})
        spilled = round(want - usd_eff, 6)
        if spilled > 1e-9:
            leftover = round(leftover + spilled, 6)

    if leftover >= 0.01 and out:
        last = out[-1]
        conv = lote_bybit.cuantizar_presupuesto_usd(
            last["usd"] + leftover, px, frente_u, mode=modo,
        )
        if conv.get("ok") and float(conv["usd"]) + 1e-9 >= min_u:
            out[-1] = {
                "usd": round(float(conv["usd"]), 6),
                "qty": float(conv["qty"]),
            }
            leftover = 0.0
    polvo = round(max(0.0, leftover), 6)
    if polvo + 1e-9 >= min_u and not out:
        # Un solo bocado falló el lote: no inventar orden inválida.
        return [], polvo
    return out, polvo


def min_carta_usd(frente: str, precio: float, direccion: str) -> float:
    """USD efectivo de UNA carta mínima válida en ese frente."""
    px = float(precio or 0)
    frente_u = str(frente or "").upper()
    if px <= 0 or not frente_u:
        return float(getattr(config, "MIN_ORDER_USD_DEFAULT", 5.0) or 5.0)
    min_u = float(lote_bybit.paso_minimo_usd(frente_u, px) or 0)
    modo: lote_bybit.ModoRedondeo = (
        "ceil" if str(direccion or "").upper() == "LONG" else "floor"
    )
    conv = lote_bybit.cuantizar_presupuesto_usd(min_u, px, frente_u, mode=modo)
    if conv.get("ok"):
        return float(conv["usd"])
    return min_u


def link_id_rafaga(beru: Any, indice: int) -> str:
    rev = int(getattr(beru, "altar_revision", 0) or 0)
    uid = str(getattr(beru, "uid", "") or "")
    semilla = f"{uid}|{rev}|RAF|{int(indice)}"
    digest = hashlib.sha256(semilla.encode("utf-8")).hexdigest()[:8]
    return f"BERU-RAF-{rev}-{int(indice)}-{digest}"[:36]


def _latencia_s() -> float:
    return max(0.0, float(getattr(config, "BERU_RAFAGA_LATENCIA_S", 0.25) or 0))


def _fill_timeout_s() -> float:
    return max(0.0, float(getattr(config, "BERU_RAFAGA_FILL_TIMEOUT_S", 2.0) or 0))


def _cooldown_s() -> float:
    return max(0.0, float(getattr(config, "BERU_RAFAGA_COOLDOWN_S", 3.0) or 0))


def en_cooldown(beru: Any) -> bool:
    ultimo = float(getattr(beru, "rafaga_ultimo_ts", 0) or 0)
    if ultimo <= 0:
        return False
    return (time.time() - ultimo) < _cooldown_s()


async def disparar_rafaga(
    bridge: Any,
    beru: Any,
    *,
    activo: str,
    usd: float,
    precio: float,
    is_leverage: int = 1,
    sleep_fn=asyncio.sleep,
) -> dict[str, Any]:
    """Market de uno en uno, ≥ latencia entre bocados. Cero trigger.

    No dispara en paralelo. Si un bocado ahoga, se detiene y anota el resto.
    """
    act = str(activo or "").upper()
    direccion = str(getattr(beru, "direccion", "") or "").upper()
    px = float(precio or 0)
    frente = f"{act}USDT_SPOT"
    side = "Buy" if direccion == "LONG" else "Sell"
    vacio = {
        "ok": False,
        "bocados_ok": 0,
        "bocados_fail": 0,
        "qty_total": 0.0,
        "usd_filled": 0.0,
        "usd_restante": round(float(usd or 0), 6),
        "polvo_usd": 0.0,
        "n_plan": 0,
        "mensajes": [],
    }
    if not act or direccion not in ("LONG", "SHORT") or px <= 0:
        vacio["mensajes"].append("rafaga_incompleta")
        return vacio

    bocados, polvo = empacar_bocados(
        usd, px, frente, direccion=direccion,
    )
    vacio["polvo_usd"] = polvo
    vacio["n_plan"] = len(bocados)
    if not bocados:
        min_u = float(lote_bybit.paso_minimo_usd(frente, px) or 5.0)
        # Polvo < mínimo: no hay nada que plantar. USD gordo vacío = fallo de lote.
        vacio["ok"] = float(usd or 0) + 1e-9 < min_u
        vacio["mensajes"].append("sin_bocados_validos")
        return vacio

    qty_total = 0.0
    usd_filled = 0.0
    ok_n = 0
    fail_n = 0
    msgs: list[str] = []
    if polvo > 0:
        msgs.append(f"polvo={polvo:.4f}")
    lat = _latencia_s()
    fill_to = _fill_timeout_s()
    symbol = f"{act}USDT"

    for i, bocado in enumerate(bocados):
        link = link_id_rafaga(beru, i)
        t0 = time.monotonic()
        previa = None
        try:
            previa = await bridge.get_order_status(
                symbol, link_id=link, category="spot",
            )
        except Exception:
            previa = None
        ya = bool(getattr(previa, "exito", False)) if previa is not None else False
        if ya:
            datos = dict(getattr(previa, "datos", None) or {})
            qty_i = float(datos.get("cumExecQty") or bocado["qty"] or 0)
            usd_i = float(datos.get("avgPrice") or px) * qty_i if qty_i else float(bocado["usd"])
            qty_total += qty_i
            usd_filled += usd_i
            ok_n += 1
        else:
            creada = await bridge.place_order(
                symbol,
                side,
                bocado["qty"],
                order_type="Market",
                link_id=link,
                category="spot",
                market_unit="baseCoin",
                is_leverage=int(is_leverage),
            )
            if not getattr(creada, "exito", False):
                fail_n += 1
                msgs.append(str(getattr(creada, "mensaje", "") or "market_rechazado"))
                if resultado_es_ahogo(creada) or resultado_es_lote(creada):
                    resto = sum(x["usd"] for x in bocados[i:])
                    return {
                        "ok": ok_n > 0 and fail_n == 0,
                        "bocados_ok": ok_n,
                        "bocados_fail": fail_n + (len(bocados) - i - 1),
                        "qty_total": qty_total,
                        "usd_filled": round(usd_filled, 6),
                        "usd_restante": round(resto, 6),
                        "polvo_usd": polvo,
                        "n_plan": len(bocados),
                        "mensajes": msgs,
                    }
                resto = sum(x["usd"] for x in bocados[i:])
                return {
                    "ok": False,
                    "bocados_ok": ok_n,
                    "bocados_fail": fail_n + (len(bocados) - i - 1),
                    "qty_total": qty_total,
                    "usd_filled": round(usd_filled, 6),
                    "usd_restante": round(resto, 6),
                    "polvo_usd": polvo,
                    "n_plan": len(bocados),
                    "mensajes": msgs,
                }
            qty_i = float(bocado["qty"])
            usd_i = float(bocado["usd"])
            if fill_to > 0 and hasattr(bridge, "esperar_fill"):
                try:
                    fill = await bridge.esperar_fill(
                        symbol,
                        order_id=getattr(creada, "order_id", "") or None,
                        link_id=link,
                        category="spot",
                        timeout_s=fill_to,
                        intervalo_s=min(0.2, max(0.05, fill_to / 8.0)),
                    )
                    if getattr(fill, "exito", False):
                        datos = dict(getattr(fill, "datos", None) or {})
                        qty_i = float(datos.get("cumExecQty") or qty_i)
                        avg = float(datos.get("avgPrice") or 0)
                        if avg > 0 and qty_i > 0:
                            usd_i = avg * qty_i
                except Exception as exc:
                    msgs.append(f"fill_poll:{exc}")
            qty_total += qty_i
            usd_filled += usd_i
            ok_n += 1

        if i < len(bocados) - 1 and lat > 0:
            elapsed = time.monotonic() - t0
            falta = lat - elapsed
            if falta > 0:
                await sleep_fn(falta)

    resto = max(0.0, round(float(usd or 0) - usd_filled - polvo, 6))
    return {
        "ok": fail_n == 0 and ok_n == len(bocados),
        "bocados_ok": ok_n,
        "bocados_fail": fail_n,
        "qty_total": qty_total,
        "usd_filled": round(usd_filled, 6),
        "usd_restante": resto if resto >= 0.01 else 0.0,
        "polvo_usd": polvo,
        "n_plan": len(bocados),
        "mensajes": msgs,
    }
