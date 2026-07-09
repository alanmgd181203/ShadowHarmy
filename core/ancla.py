"""
Ancla de Realidad — slippage y tamaño de mordida desde orderbook vivo.
Capa 1: solo muro (sin perfiles). Capa 2: entrada segura vía Kaiser.
"""
from __future__ import annotations

from typing import Any

import core.config as config


def min_order_usd_frente(frente: str) -> float:
    mp = getattr(config, "MIN_ORDER_USD_BY_FRENTE", {}) or {}
    default = float(getattr(config, "MIN_ORDER_USD_DEFAULT", 5.0))
    return float(mp.get(frente, default))


def fees_total_cruce(frente_compra: str, frente_venta: str) -> float:
    if frente_compra == frente_venta:
        return _fee_pct_frente(frente_compra) * 2
    return _fee_pct_frente(frente_compra) + _fee_pct_frente(frente_venta)


def neto_minimo_requerido(fees_total_pct: float) -> float:
    """Neto mínimo = fees × factor (1.0 → ganamos al menos lo que pagamos)."""
    factor = float(getattr(config, "ANCLA_NETO_MIN_VS_FEES", 1.0))
    return fees_total_pct * factor


def cumple_regla_neto_vs_fees(regalo_neto_pct: float, fees_total_pct: float) -> bool:
    if regalo_neto_pct is None:
        return False
    return float(regalo_neto_pct) >= neto_minimo_requerido(fees_total_pct)


def cumple_reglas_alerta_greed(
    op: dict,
    *,
    pipeline_ms: float,
    tank_semaforo: str,
    spread_estable: bool,
    spread_estable_motivo: str = "",
) -> tuple[bool, str]:
    """Filtros Kaiser → Greed (sin segura rígida)."""
    if tank_semaforo == "ROJO":
        return False, "TANK_ROJO"

    pipeline_max = float(getattr(config, "PIPELINE_MAX_MS", 500))
    if pipeline_ms > pipeline_max:
        return False, f"PIPELINE_LENTO_{pipeline_ms:.0f}ms"

    max_u = float(op.get("entrada_maxima_usd") or 0)
    min_ord = float(op.get("min_order_usd_cruce") or 0)
    if max_u < min_ord:
        return False, "BAJO_MIN_PAR"

    neto = float(op.get("regalo_neto_pct_est") or 0)
    fees = float(op.get("fees_total_pct") or 0)
    if not cumple_regla_neto_vs_fees(neto, fees):
        return False, "NETO_NO_CUBRE_FEES_X2"

    if not spread_estable:
        return False, spread_estable_motivo or "SPREAD_INESTABLE"

    return True, "OK"


def min_order_usd_cruce(frentes: list[str]) -> float:
    """Mínimo USD exigido por el cruce (pierna más exigente)."""
    if not frentes:
        return float(getattr(config, "MIN_ORDER_USD_DEFAULT", 5.0))
    return max(min_order_usd_frente(f) for f in frentes if f)


def _niveles_validos(niveles: list) -> list[tuple[float, float]]:
    out: list[tuple[float, float]] = []
    for row in niveles or []:
        try:
            p, q = float(row[0]), float(row[1])
        except (IndexError, TypeError, ValueError):
            continue
        if p > 0 and q > 0:
            out.append((p, q))
    return out


def _es_inverse(frente: str) -> bool:
    return frente.endswith("_INVERSE")


def _fee_pct_frente(frente: str) -> float:
    if frente.endswith("_SPOT"):
        return getattr(config, "ANCLA_FEE_SPOT_PCT", 0.10)
    if frente.endswith("_INVERSE"):
        return getattr(config, "ANCLA_FEE_INVERSE_TAKER_PCT", 0.055)
    return getattr(config, "ANCLA_FEE_LINEAR_TAKER_PCT", 0.055)


def _mid_desde_libro(bids: list, asks: list) -> float:
    bb = _niveles_validos(bids)
    aa = _niveles_validos(asks)
    if not bb or not aa:
        return 0.0
    return (bb[0][0] + aa[0][0]) / 2.0


def simular_compra_notional_usd(
    asks: list,
    notional_usd: float,
    *,
    inverse: bool = False,
) -> dict[str, Any]:
    """Market buy: gastar hasta notional_usd contra asks."""
    niveles = _niveles_validos(asks)
    if not niveles or notional_usd <= 0:
        return _fill_vacio()

    best = niveles[0][0]
    restante = notional_usd
    costo = 0.0
    qty_base = 0.0
    niveles_tocados = 0

    for price, qty in niveles:
        if restante <= 0:
            break
        if inverse:
            # Bybit inverse: size en USD de contrato
            tomar_usd = min(restante, qty)
            costo += tomar_usd
            qty_base += tomar_usd / price if price > 0 else 0
            restante -= tomar_usd
        else:
            costo_nivel = price * qty
            tomar_usd = min(restante, costo_nivel)
            tomar_base = tomar_usd / price if price > 0 else 0
            costo += tomar_usd
            qty_base += tomar_base
            restante -= tomar_usd
        niveles_tocados += 1

    llenado_usd = costo
    if llenado_usd <= 0 or qty_base <= 0:
        return _fill_vacio()

    avg = costo / qty_base
    slippage_pct = ((avg - best) / best * 100) if best > 0 else 0.0
    return {
        "llenado_usd": round(llenado_usd, 4),
        "qty_base": round(qty_base, 8),
        "precio_promedio": round(avg, 8),
        "mejor_precio": round(best, 8),
        "slippage_pct": round(max(0.0, slippage_pct), 4),
        "niveles_tocados": niveles_tocados,
        "agotado": restante > 1e-6,
    }


def simular_venta_base(
    bids: list,
    qty_base: float,
    *,
    inverse: bool = False,
) -> dict[str, Any]:
    """Market sell: vender qty_base contra bids."""
    niveles = _niveles_validos(bids)
    if not niveles or qty_base <= 0:
        return _fill_vacio()

    best = niveles[0][0]
    restante = qty_base
    proceeds = 0.0
    vendido_base = 0.0
    niveles_tocados = 0

    for price, qty in niveles:
        if restante <= 0:
            break
        if inverse:
            # qty nivel en USD; convertir a base para comparar
            base_en_nivel = qty / price if price > 0 else 0
            tomar_base = min(restante, base_en_nivel)
            tomar_usd = tomar_base * price
        else:
            tomar_base = min(restante, qty)
            tomar_usd = tomar_base * price
        proceeds += tomar_usd
        vendido_base += tomar_base
        restante -= tomar_base
        niveles_tocados += 1

    if vendido_base <= 0:
        return _fill_vacio()

    avg = proceeds / vendido_base
    slippage_pct = ((best - avg) / best * 100) if best > 0 else 0.0
    return {
        "llenado_usd": round(proceeds, 4),
        "qty_base": round(vendido_base, 8),
        "precio_promedio": round(avg, 8),
        "mejor_precio": round(best, 8),
        "slippage_pct": round(max(0.0, slippage_pct), 4),
        "niveles_tocados": niveles_tocados,
        "agotado": restante > 1e-9,
    }


def _fill_vacio() -> dict[str, Any]:
    return {
        "llenado_usd": 0.0,
        "qty_base": 0.0,
        "precio_promedio": 0.0,
        "mejor_precio": 0.0,
        "slippage_pct": 0.0,
        "niveles_tocados": 0,
        "agotado": True,
    }


def profundidad_usd_libro(bids: list, asks: list, frente: str) -> dict[str, float]:
    """Techo visible: cuánto USD aguantan bid/ask por separado."""
    inv = _es_inverse(frente)
    bid_usd = 0.0
    for price, qty in _niveles_validos(bids):
        bid_usd += qty if inv else price * qty
    ask_usd = 0.0
    for price, qty in _niveles_validos(asks):
        ask_usd += qty if inv else price * qty
    return {"bid_usd": round(bid_usd, 2), "ask_usd": round(ask_usd, 2)}


def entrada_maxima_desde_libro(
    bids: list,
    asks: list,
    frente: str,
    lado: str,
    *,
    spread_bruto_pct: float = 0.0,
) -> dict[str, Any]:
    """
    Recorre el libro hasta agotarlo o hasta que regalo neto <= 0.
    lado: BUY (asks) o SELL (bids) para la pierna principal.
    """
    inv = _es_inverse(frente)
    prof = profundidad_usd_libro(bids, asks, frente)
    techo_usd = prof["ask_usd"] if lado == "BUY" else prof["bid_usd"]
    if techo_usd <= 0:
        return {"entrada_maxima_usd": 0.0, "detalle": {}, "motivo": "SIN_LIBRO"}

    paso = getattr(config, "ANCLA_PASO_BUSQUEDA_USD", 25.0)
    min_usd = getattr(config, "ANCLA_MIN_NOTIONAL_USD", 10.0)
    fee = _fee_pct_frente(frente)
    fees_total = fee * 2 if spread_bruto_pct > 0 else fee
    min_neto_req = neto_minimo_requerido(fees_total)

    mejor_neto = -999.0
    max_usd_neto_positivo = 0.0
    mejor_det: dict = {}

    usd = min_usd
    while usd <= techo_usd + 1e-6:
        if lado == "BUY":
            fill = simular_compra_notional_usd(asks, usd, inverse=inv)
        else:
            mid_guess = _mid_desde_libro(bids, asks) or (bids[0][0] if bids else 0)
            qty = usd / mid_guess if mid_guess > 0 else 0
            fill = simular_venta_base(bids, qty, inverse=inv)

        slip = float(fill.get("slippage_pct") or 0)
        llenado = float(fill.get("llenado_usd") or 0)

        if spread_bruto_pct > 0:
            neto_pct = spread_bruto_pct - slip - fees_total
        else:
            neto_pct = -slip

        if neto_pct > mejor_neto:
            mejor_neto = neto_pct
            mejor_det = dict(fill)

        if spread_bruto_pct <= 0 or neto_pct >= min_neto_req:
            max_usd_neto_positivo = llenado or usd

        if spread_bruto_pct > 0 and neto_pct < min_neto_req:
            break
        if fill.get("agotado") and llenado < usd * 0.99:
            break
        usd += paso

    max_libro = techo_usd
    if spread_bruto_pct <= 0:
        max_util = max_libro
    else:
        max_util = max_usd_neto_positivo if max_usd_neto_positivo > 0 else 0.0

    return {
        "entrada_maxima_usd": round(max_util, 2),
        "entrada_maxima_teorica_libro_usd": round(max_libro, 2),
        "regalo_neto_pct_est": round(mejor_neto, 4) if spread_bruto_pct > 0 else None,
        "slippage_pct": mejor_det.get("slippage_pct", 0),
        "detalle_fill": mejor_det,
        "fee_pct_pierna": fee,
        "fees_total_pct": round(fees_total, 4),
        "neto_min_requerido_pct": round(min_neto_req, 4),
        "lado": lado,
        "frente": frente,
    }


def simular_arbitraje_dos_piernas(
    frente_compra: str,
    frente_venta: str,
    libro_compra: dict,
    libro_venta: dict,
    notional_usd: float,
    spread_bruto_pct: float,
) -> dict[str, Any]:
    """Dos piernas: comprar barato, vender caro."""
    inv_c = _es_inverse(frente_compra)
    inv_v = _es_inverse(frente_venta)
    buy = simular_compra_notional_usd(
        libro_compra.get("asks") or [], notional_usd, inverse=inv_c,
    )
    qty = float(buy.get("qty_base") or 0)
    if qty <= 0:
        return {"ok": False, "motivo": "PIERNA_COMPRA_VACIA", "llenado_usd": 0.0}

    sell = simular_venta_base(
        libro_venta.get("bids") or [], qty, inverse=inv_v,
    )
    llenado = min(float(buy.get("llenado_usd") or 0), float(sell.get("llenado_usd") or 0))
    slip_total = float(buy.get("slippage_pct") or 0) + float(sell.get("slippage_pct") or 0)
    fee = _fee_pct_frente(frente_compra) + _fee_pct_frente(frente_venta)
    neto = spread_bruto_pct - slip_total - fee

    return {
        "ok": llenado > 0,
        "llenado_usd": round(llenado, 2),
        "slippage_total_pct": round(slip_total, 4),
        "regalo_neto_pct": round(neto, 4),
        "compra": buy,
        "venta": sell,
        "frente_compra": frente_compra,
        "frente_venta": frente_venta,
    }


def _buscar_max_arbitraje(
    frente_c: str,
    frente_v: str,
    libro_c: dict,
    libro_v: dict,
    spread_bruto_pct: float,
) -> dict[str, Any]:
    prof_c = profundidad_usd_libro(
        libro_c.get("bids") or [], libro_c.get("asks") or [], frente_c,
    )
    prof_v = profundidad_usd_libro(
        libro_v.get("bids") or [], libro_v.get("asks") or [], frente_v,
    )
    techo = min(prof_c["ask_usd"], prof_v["bid_usd"])
    if techo <= 0:
        return {"entrada_maxima_usd": 0.0, "motivo": "SIN_LIBRO"}

    paso = getattr(config, "ANCLA_PASO_BUSQUEDA_USD", 25.0)
    min_usd = getattr(config, "ANCLA_MIN_NOTIONAL_USD", 10.0)
    fees_total = fees_total_cruce(frente_c, frente_v)
    min_neto_req = neto_minimo_requerido(fees_total)
    mejor_neto = -999.0
    max_usd_neto_positivo = 0.0
    mejor_sim: dict = {}

    usd = min_usd
    while usd <= techo + 1e-6:
        sim = simular_arbitraje_dos_piernas(
            frente_c, frente_v, libro_c, libro_v, usd, spread_bruto_pct,
        )
        neto = float(sim.get("regalo_neto_pct") or -999)
        llenado = float(sim.get("llenado_usd") or 0)
        if neto > mejor_neto:
            mejor_neto = neto
            mejor_sim = sim
        if spread_bruto_pct <= 0 or neto >= min_neto_req:
            max_usd_neto_positivo = llenado or usd
        if neto < min_neto_req and spread_bruto_pct > 0:
            break
        if llenado < usd * 0.95:
            break
        usd += paso

    return {
        "entrada_maxima_usd": round(max_usd_neto_positivo if max_usd_neto_positivo > 0 else 0, 2),
        "entrada_maxima_teorica_libro_usd": round(techo, 2),
        "regalo_neto_pct_est": round(mejor_neto, 4),
        "simulacion": mejor_sim,
        "frente_compra": frente_c,
        "frente_venta": frente_v,
        "fees_total_pct": round(fees_total, 4),
        "neto_min_requerido_pct": round(min_neto_req, 4),
    }


def frentes_desde_fila_matriz(base: str, tipo: str, row: dict) -> tuple[str, str] | None:
    """Par compra/venta para arbitraje según tipo de spread."""
    b = base.upper()
    if tipo == "usdt_vs_usdc":
        pu = float(row.get("precio_usdt") or 0)
        pc = float(row.get("precio_usdc") or 0)
        fu = f"{b}USDT_SPOT"
        fc = f"{b}USDC_SPOT"
        if pu <= 0:
            fu = f"{b}USDT_LINEAL"
        if pc <= 0:
            return fu, fc
        if pu <= pc:
            return fu, fc
        return fc, fu
    if tipo == "spot_vs_perp":
        ps = float(row.get("precio_spot") or 0)
        pp = float(row.get("precio_perp") or 0)
        fs, fp = f"{b}USDT_SPOT", f"{b}USDT_LINEAL"
        if ps > 0 and pp > 0:
            return (fs, fp) if ps < pp else (fp, fs)
        return fs, fp
    if tipo == "lineal_vs_inverse":
        pl = float(row.get("precio_lineal") or 0)
        pi = float(row.get("precio_inverse") or 0)
        fl, fi = f"{b}USDT_LINEAL", f"{b}USD_INVERSE"
        if pl > 0 and pi > 0:
            return (fl, fi) if pl < pi else (fi, fl)
        return fl, fi
    if tipo == "perp_vs_index":
        return f"{b}USDT_LINEAL", f"{b}USDT_LINEAL"
    if tipo == "spot_vs_index":
        return f"{b}USDT_SPOT", f"{b}USDT_SPOT"
    if str(tipo).startswith("multicruce_"):
        piernas = row.get("piernas") or []
        if len(piernas) >= 2:
            return str(piernas[0]["frente"]), str(piernas[-1]["frente"])
    return None


def calcular_entrada_segura(
    entrada_max_usd: float,
    *,
    tank_semaforo: str = "VERDE",
    latencia_ms: float = 0.0,
    slippage_pct: float = 0.0,
    niveles_tocados: int = 0,
    perfil_tags: list[str] | None = None,
    libro: dict | None = None,
    frente: str = "",
    lado: str = "BUY",
    spread_bruto_pct: float = 0.0,
) -> dict[str, Any]:
    """Recomendación Kaiser — por debajo de la máxima del libro."""
    perfil_tags = perfil_tags or []
    frac = getattr(config, "ANCLA_SEGURA_FRACCION_MAX", 0.30)
    motivos: list[str] = []

    if tank_semaforo == "ROJO":
        frac *= 0.25
        motivos.append("TANK_ROJO")
    elif tank_semaforo == "AMARILLO":
        frac *= 0.60
        motivos.append("TANK_AMARILLO")
    elif latencia_ms > getattr(config, "UMBRAL_AMARILLO_MS", 800):
        frac *= 0.70
        motivos.append("LATENCIA_ALTA")

    if slippage_pct > getattr(config, "ANCLA_SEGURA_SLIPPAGE_PCT", 0.05):
        frac *= 0.50
        motivos.append("SLIPPAGE_VISIBLE")

    if niveles_tocados >= 3:
        frac *= 0.75
        motivos.append("MURO_FINO")

    if "DATOS_INSUFICIENTES" in perfil_tags or "SIN_CONSENSO" in perfil_tags:
        frac *= 0.35
        motivos.append("PERFIL_SIN_DATOS")
    if "RUIDOSO" in perfil_tags:
        frac *= 0.70
        motivos.append("PERFIL_RUIDOSO")
    if "SHORT_HUMO" in perfil_tags or "LONG_HUMO" in perfil_tags:
        frac *= 0.60
        motivos.append("PERFIL_HUMO")

    # Tope por slippage conservador en libro
    segura_por_slip = entrada_max_usd
    if libro and frente and spread_bruto_pct > 0:
        segura_por_slip = _max_usd_slippage_bajo(
            libro, frente, lado, spread_bruto_pct,
            getattr(config, "ANCLA_SEGURA_SLIPPAGE_PCT", 0.05),
        )

    segura_frac = entrada_max_usd * max(0.05, min(1.0, frac))
    segura = min(entrada_max_usd, segura_frac, segura_por_slip)
    min_usd = getattr(config, "ANCLA_MIN_NOTIONAL_USD", 10.0)
    if segura < min_usd and entrada_max_usd >= min_usd:
        segura = min_usd
    if entrada_max_usd < min_usd:
        segura = 0.0
        motivos.append("BAJO_MINIMO")

    return {
        "entrada_segura_usd": round(max(0.0, segura), 2),
        "fraccion_aplicada": round(frac, 3),
        "motivos_segura": motivos,
    }


def _max_usd_slippage_bajo(
    libro: dict,
    frente: str,
    lado: str,
    spread_bruto_pct: float,
    slip_max: float,
) -> float:
    paso = getattr(config, "ANCLA_PASO_BUSQUEDA_USD", 25.0)
    min_usd = getattr(config, "ANCLA_MIN_NOTIONAL_USD", 10.0)
    inv = _es_inverse(frente)
    bids = libro.get("bids") or []
    asks = libro.get("asks") or []
    techo = profundidad_usd_libro(bids, asks, frente)
    max_usd = techo["ask_usd"] if lado == "BUY" else techo["bid_usd"]
    ultimo_ok = 0.0
    usd = min_usd
    while usd <= max_usd:
        if lado == "BUY":
            fill = simular_compra_notional_usd(asks, usd, inverse=inv)
        else:
            mid = _mid_desde_libro(bids, asks) or 1.0
            fill = simular_venta_base(bids, usd / mid, inverse=inv)
        if float(fill.get("slippage_pct") or 0) <= slip_max:
            ultimo_ok = float(fill.get("llenado_usd") or usd)
        else:
            break
        usd += paso
    return ultimo_ok


def evaluar_fila_matriz(
    row: dict,
    libros: dict[str, dict],
    *,
    tank_semaforo: str = "VERDE",
    latencia_ms: float = 0.0,
    pipeline_ms: float = 0.0,
    spread_estable: bool = True,
    spread_estable_motivo: str = "OK",
) -> dict[str, Any] | None:
    spread = float(row.get("spread_pct") or 0)
    if spread <= 0:
        return None

    base = str(row.get("base", "")).upper()
    tipo = str(row.get("tipo", ""))
    par = frentes_desde_fila_matriz(base, tipo, row)

    if not par:
        return None

    fc, fv = par
    piernas = row.get("piernas") if str(tipo).startswith("multicruce_") else None

    if piernas:
        max_usd_leg = float("inf")
        slip_total = 0.0
        fees_total = 0.0
        for leg in piernas:
            f = str(leg["frente"])
            side = str(leg.get("side", "Buy"))
            libro = libros.get(f) or {}
            if not libro.get("asks") and not libro.get("bids"):
                return None
            lado = "BUY" if side.upper() == "BUY" else "SELL"
            leg_info = entrada_maxima_desde_libro(
                libro.get("bids") or [],
                libro.get("asks") or [],
                f,
                lado,
                spread_bruto_pct=spread / max(len(piernas), 1),
            )
            leg_max = float(leg_info.get("entrada_maxima_usd") or 0)
            if leg_max <= 0:
                return None
            max_usd_leg = min(max_usd_leg, leg_max)
            slip_total += float(
                (leg_info.get("simulacion") or {}).get("slippage_pct")
                or leg_info.get("slippage_pct")
                or 0
            )
            fees_total += float(leg_info.get("fees_total_pct") or fees_total_cruce(f, f))
        max_usd = max_usd_leg if max_usd_leg != float("inf") else 0.0
        neto = round(spread - slip_total, 4)
        max_info = {
            "entrada_maxima_usd": max_usd,
            "regalo_neto_pct_est": neto,
            "fees_total_pct": round(fees_total, 4),
            "simulacion": {"slippage_total_pct": round(slip_total, 4)},
        }
        frentes_cruce = list(dict.fromkeys(str(p["frente"]) for p in piernas))
        min_ord = min_order_usd_cruce(frentes_cruce)
        fc, fv = frentes_cruce[0], frentes_cruce[-1]
    elif tipo in ("usdt_vs_usdc", "spot_vs_perp", "lineal_vs_inverse"):
        libro_c = libros.get(fc) or {}
        libro_v = libros.get(fv) or {}
        if not libro_c.get("asks") and not libro_c.get("bids"):
            return None
        if fc != fv and not libro_v.get("bids") and not libro_v.get("asks"):
            return None
        if fc == fv:
            max_info = entrada_maxima_desde_libro(
                libro_c.get("bids") or [],
                libro_c.get("asks") or [],
                fc,
                "BUY",
                spread_bruto_pct=spread,
            )
        else:
            max_info = _buscar_max_arbitraje(fc, fv, libro_c, libro_v, spread)
    else:
        frente = fc
        libro = libros.get(fc) or {}
        max_info = entrada_maxima_desde_libro(
            libro.get("bids") or [],
            libro.get("asks") or [],
            frente,
            "BUY",
            spread_bruto_pct=spread,
        )

    max_usd = float(max_info.get("entrada_maxima_usd") or 0)
    if max_usd <= 0:
        return None

    if not piernas:
        frentes_cruce = list(dict.fromkeys([fc, fv]))
        min_ord = min_order_usd_cruce(frentes_cruce)
    fees_total = float(
        max_info.get("fees_total_pct") or fees_total_cruce(fc, fv)
    )

    sim = max_info.get("simulacion") or {}
    slip = float(
        sim.get("slippage_total_pct")
        or max_info.get("slippage_pct")
        or (max_info.get("detalle_fill") or {}).get("slippage_pct")
        or 0
    )
    neto = float(max_info.get("regalo_neto_pct_est") or 0)

    op = {
        "base": base,
        "tipo_spread": tipo,
        "spread_bruto_pct": spread,
        "entrada_maxima_usd": max_usd,
        "min_order_usd_cruce": round(min_ord, 2),
        "entrada_maxima_teorica_libro_usd": max_info.get("entrada_maxima_teorica_libro_usd"),
        "regalo_neto_pct_est": neto,
        "fees_total_pct": round(fees_total, 4),
        "neto_min_requerido_pct": max_info.get("neto_min_requerido_pct"),
        "slippage_pct": slip,
        "frentes": dict(row.get("frentes") or {"compra": fc, "venta": fv}),
        "capa": "ANCLA",
        "pipeline_ms": round(pipeline_ms, 2),
    }
    if piernas:
        op["piernas"] = list(piernas)
        op["n_piernas"] = len(piernas)
        op["via_quote"] = row.get("via_quote")
        op["ruta_id"] = row.get("ruta_id")

    ok, motivo = cumple_reglas_alerta_greed(
        op,
        pipeline_ms=pipeline_ms,
        tank_semaforo=tank_semaforo,
        spread_estable=spread_estable,
        spread_estable_motivo=spread_estable_motivo,
    )
    if not ok:
        return None

    op["filtro_ok"] = motivo
    return op


def escanear_oportunidades_ancla(
    matriz_filas: list[dict],
    libros: dict[str, dict],
    *,
    tank_semaforo: str = "VERDE",
    latencia_ms: float = 0.0,
    pipeline_ms: float = 0.0,
    rastreador=None,
    top_n: int | None = None,
) -> list[dict]:
    top_n = top_n or getattr(config, "ANCLA_TOP_N", 15)
    out: list[dict] = []

    for row in matriz_filas:
        base = str(row.get("base", "")).upper()
        tipo = str(row.get("tipo", ""))
        spread = float(row.get("spread_pct") or 0)
        clave = f"{base}:{tipo}"
        estable, mot_est = True, "OK"
        if rastreador is not None:
            estable, mot_est = rastreador.spread_estable_para_pipeline(
                clave, spread, pipeline_ms,
            )
        ev = evaluar_fila_matriz(
            row, libros,
            tank_semaforo=tank_semaforo,
            latencia_ms=latencia_ms,
            pipeline_ms=pipeline_ms,
            spread_estable=estable,
            spread_estable_motivo=mot_est,
        )
        if ev:
            out.append(ev)
            if rastreador is not None:
                rastreador.registrar(clave, spread)

    out.sort(
        key=lambda x: float(x.get("entrada_maxima_usd") or 0) * float(x.get("regalo_neto_pct_est") or 0),
        reverse=True,
    )
    return out[:top_n]


def consultar_liquidez_intencion(
    intencion: dict,
    libros: dict[str, dict],
    *,
    tank_semaforo: str = "VERDE",
    latencia_ms: float = 0.0,
    precios: dict | None = None,
) -> dict[str, Any]:
    """
    Respuesta a intención de general: ¿cuánto aguanta el muro?
    intencion: general, tipo, masa (USD), direccion, frente / frente_compra / frente_venta
    """
    masa = float(intencion.get("masa") or intencion.get("notional_usd") or 0)
    frente = intencion.get("frente") or intencion.get("frente_compra")
    fc = intencion.get("frente_compra") or frente
    fv = intencion.get("frente_venta")

    if fc and fv and fc != fv:
        lc = libros.get(str(fc)) or {}
        lv = libros.get(str(fv)) or {}
        spread = 0.0
        if precios:
            pc = precios.get(fc, 0)
            pv = precios.get(fv, 0)
            if pc > 0 and pv > 0:
                spread = abs(pc - pv) / min(pc, pv) * 100
        max_info = _buscar_max_arbitraje(str(fc), str(fv), lc, lv, spread)
        max_usd = float(max_info.get("entrada_maxima_usd") or 0)
        sim_masa = simular_arbitraje_dos_piernas(
            str(fc), str(fv), lc, lv, masa, spread,
        ) if masa > 0 else {}
        seg = calcular_entrada_segura(
            max_usd, tank_semaforo=tank_semaforo, latencia_ms=latencia_ms,
            spread_bruto_pct=spread,
        )
        fees_total = float(max_info.get("fees_total_pct") or fees_total_cruce(str(fc), str(fv)))
        neto_est = float(max_info.get("regalo_neto_pct_est") or 0)
        min_ord = min_order_usd_cruce([str(fc), str(fv)])
        ok = max_usd >= min_ord and cumple_regla_neto_vs_fees(neto_est, fees_total)
        masa_ok = masa <= max_usd if masa > 0 else None
        if masa > 0 and masa_ok and spread > 0:
            sim_chk = simular_arbitraje_dos_piernas(
                str(fc), str(fv), lc, lv, masa, spread,
            )
            neto_m = float(sim_chk.get("regalo_neto_pct") or 0)
            masa_ok = masa_ok and cumple_regla_neto_vs_fees(neto_m, fees_total)
        r = {
            "ok": ok,
            "entrada_maxima_usd": max_usd,
            "entrada_segura_usd": seg["entrada_segura_usd"],
            "hint_greed_usd": seg["entrada_segura_usd"],
            "masa_solicitada_usd": masa,
            "masa_viable": masa_ok,
            "simulacion_masa": sim_masa,
            "motivos_segura": seg["motivos_segura"],
            "frente_compra": fc,
            "frente_venta": fv,
            "fees_total_pct": fees_total,
            "regalo_neto_pct_est": neto_est,
            "min_order_usd_cruce": min_ord,
        }
        if max_usd < min_ord:
            r["ok"] = False
            r["motivo"] = "BAJO_MIN_ORDEN_PAR"
        elif not cumple_regla_neto_vs_fees(neto_est, fees_total):
            r["ok"] = False
            r["motivo"] = "NETO_NO_CUBRE_FEES"
        return r

    if not frente:
        return {"ok": False, "motivo": "SIN_FRENTE"}

    libro = libros.get(str(frente)) or {}
    lado = "BUY" if str(intencion.get("direccion", "LONG")).upper() in ("LONG", "BUY") else "SELL"
    max_info = entrada_maxima_desde_libro(
        libro.get("bids") or [],
        libro.get("asks") or [],
        str(frente),
        lado,
    )
    max_usd = float(max_info.get("entrada_maxima_usd") or 0)
    seg = calcular_entrada_segura(
        max_usd, tank_semaforo=tank_semaforo, latencia_ms=latencia_ms,
        libro=libro, frente=str(frente), lado=lado,
    )
    fill = {}
    if masa > 0:
        inv = _es_inverse(str(frente))
        if lado == "BUY":
            fill = simular_compra_notional_usd(libro.get("asks") or [], masa, inverse=inv)
        else:
            mid = _mid_desde_libro(libro.get("bids") or [], libro.get("asks") or []) or 1.0
            fill = simular_venta_base(libro.get("bids") or [], masa / mid, inverse=inv)

    min_ord = min_order_usd_frente(str(frente))
    ok = max_usd >= min_ord
    masa_ok = masa <= max_usd if masa > 0 else None
    return {
        "ok": ok,
        "frente": frente,
        "lado": lado,
        "entrada_maxima_usd": max_usd,
        "entrada_segura_usd": seg["entrada_segura_usd"],
        "hint_greed_usd": seg["entrada_segura_usd"],
        "min_order_usd_cruce": min_ord,
        "masa_solicitada_usd": masa,
        "masa_viable": masa_ok,
        "simulacion_masa": fill,
        "motivos_segura": seg["motivos_segura"],
        "motivo": None if ok else "BAJO_MIN_ORDEN_PAR",
    }


def libros_desde_lider(tank) -> dict[str, dict]:
    """Snapshot de libros del nodo líder Tank."""
    lider = tank._obtener_lider_verde()
    if not lider:
        candidatos = sorted(tank.nodos, key=lambda n: n.ultima_actualizacion, reverse=True)
        lider = candidatos[0] if candidatos else None
    if not lider:
        return {}
    return dict(getattr(lider, "libros", {}) or {})
