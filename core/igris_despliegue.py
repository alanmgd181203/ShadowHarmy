"""
Igris — despliegue paciente del manto §E (inverse LONG + lineal SHORT).

Ask/Bid reales, umbral = fees ± urgencia (reloj invertido Kaiser),
mordida = techo_misión × fracción(confianza Greed) sin pinza 85% ni tope 1% equity.
"""
from __future__ import annotations

import time
from typing import Any

import core.config as config
from core import ancla
from core import greed_sizing as sizing


def _ticker_puerta_habilitada() -> bool:
    raw = str(getattr(config, "IGRIS_TICKER_PUERTA_SI_SIN_LIBRO", "auto") or "auto").strip().lower()
    if raw in ("0", "false", "off", "no"):
        return False
    if raw in ("1", "true", "on", "yes"):
        return True
    # auto
    if getattr(config, "MODO_SIMULACION", False) or getattr(config, "ARISE_IGRIS_SIM", False):
        return True
    if not bool(getattr(config, "BRIDGE_WS_SUBSCRIBE_BOOKS", True)):
        return True
    return False


def precio_ticker_frente(tank, frente: str) -> float:
    """Last price del frente desde Tank (lider o nodos), con reflejo si existe."""
    frentes: dict = {}
    lider = None
    if hasattr(tank, "_obtener_lider_verde"):
        try:
            lider = tank._obtener_lider_verde()
        except Exception:
            lider = None
    if lider is None and hasattr(tank, "nodos"):
        try:
            nodos = list(getattr(tank, "nodos") or [])
            nodos.sort(key=lambda n: getattr(n, "ultima_actualizacion", 0), reverse=True)
            lider = nodos[0] if nodos else None
        except Exception:
            lider = None
    if lider is not None:
        if hasattr(lider, "precios_con_reflejo"):
            try:
                frentes = dict(lider.precios_con_reflejo() or {})
            except Exception:
                frentes = dict(getattr(lider, "precios", {}) or {})
        else:
            frentes = dict(getattr(lider, "precios", {}) or {})
    if not frentes and hasattr(tank, "precios"):
        frentes = dict(getattr(tank, "precios") or {})
    return float(frentes.get(frente) or 0.0)


def libro_sintetico_ticker(
    precio: float,
    restante_usd: float,
    *,
    frente: str = "",
) -> tuple[list, list]:
    """
    Libro sintético 1-nivel desde ticker (ojos sin muros / sim).
    Inverse: qty = USD de contrato. Lineal/spot: qty = base.
    """
    px = float(precio or 0)
    if px <= 0:
        return [], []
    half = float(getattr(config, "IGRIS_TICKER_HALF_SPREAD_PCT", 0.02) or 0.02) / 100.0
    ask = px * (1.0 + half)
    bid = px * (1.0 - half)
    need = max(float(restante_usd or 0), float(getattr(config, "ANCLA_MIN_NOTIONAL_USD", 10) or 10), 25.0) * 4.0
    fu = (frente or "").upper()
    if "INVERSE" in fu:
        qty = need  # Bybit inverse: size en USD
    else:
        qty = need / px
    return [[bid, qty]], [[ask, qty]]


def libro_tank(tank, frente: str) -> tuple[list, list]:
    """Libros del nodo líder Tank; fallback a tank.libros (smokes / mocks)."""
    libros: dict = {}
    if hasattr(tank, "_obtener_lider_verde"):
        lider = tank._obtener_lider_verde()
        if lider is not None:
            libros = dict(getattr(lider, "libros", {}) or {})
        elif hasattr(tank, "nodos"):
            libros = ancla.libros_desde_lider(tank)
    if not libros:
        libros = getattr(tank, "libros", None) or {}
    libro = libros.get(frente) or {}
    return list(libro.get("bids") or []), list(libro.get("asks") or [])


def best_ask(asks: list) -> float:
    for row in asks or []:
        try:
            p, q = float(row[0]), float(row[1])
        except (IndexError, TypeError, ValueError):
            continue
        if p > 0 and q > 0:
            return p
    return 0.0


def best_bid(bids: list) -> float:
    for row in bids or []:
        try:
            p, q = float(row[0]), float(row[1])
        except (IndexError, TypeError, ValueError):
            continue
        if p > 0 and q > 0:
            return p
    return 0.0


def spread_ejecutable_pct(ask_long: float, bid_short: float) -> float:
    """Spread a favor (%). Long@Ask, Short@Bid. Positivo = asimetría a favor."""
    if ask_long <= 0 or bid_short <= 0:
        return float("-inf")
    mid = (ask_long + bid_short) / 2.0
    if mid <= 0:
        return float("-inf")
    return (bid_short - ask_long) / mid * 100.0


def fees_break_even_pct(frente_long: str, frente_short: str) -> float:
    fees = ancla.fees_total_cruce(frente_long, frente_short)
    return ancla.neto_minimo_requerido(fees)


def pct_tiempo_sobre_umbral(perfil_edge: dict | None) -> float | None:
    """Frecuencia de oportunidad Kaiser (plazo mediano). None = sin datos."""
    if not perfil_edge:
        return None
    plazos = perfil_edge.get("plazos") or {}
    med = plazos.get("mediano") or {}
    tags = med.get("etiquetas") or []
    if "DATOS_INSUFICIENTES" in tags:
        return None
    m = med.get("metricas") or {}
    if int(m.get("n_muestras") or 0) <= 0:
        return None
    return float(m.get("pct_tiempo_sobre_umbral") or 0.0)


def tau_paciencia_horas(
    perfil_edge: dict | None,
    *,
    base: str | None = None,
) -> dict[str, Any]:
    """
    Reloj invertido (costo de oportunidad):

      tau = tau_min + (tau_max − tau_min) × pct_frecuencia

    Preferencia (Monarca 2026-07-24): `manto_frecuencia` — 4 umbrales
    (fees / ½ fees / tablas / morado) × plazos (corto 50% · mediano 40% · anual 10%).
    Fallback: pct_tiempo_sobre_umbral del perfil Kaiser (umbral evento genérico).
    Alta frecuencia → tau grande → degradación LENTA.
    Baja frecuencia → tau chico → degradación RÁPIDA.
    """
    tau_base = float(getattr(config, "IGRIS_URGENCIA_TAU_HORAS", 8.0) or 8.0)
    tau_min = float(getattr(config, "IGRIS_URGENCIA_TAU_MIN_HORAS", 1.0) or 1.0)
    tau_max = float(getattr(config, "IGRIS_URGENCIA_TAU_MAX_HORAS", 24.0) or 24.0)
    if tau_max < tau_min:
        tau_max = tau_min

    bu = (base or (perfil_edge or {}).get("base") or "").upper()
    if bu and getattr(config, "MANTO_FREQ_ACTIVA", True):
        try:
            from core import manto_frecuencia as mf

            freq = mf.frecuencia_activo(bu)
            if freq.get("ok") and freq.get("score_paciencia") is not None:
                info = mf.tau_desde_score(float(freq["score_paciencia"]))
                info["modo_sugerido"] = freq.get("modo_sugerido")
                info["contadores"] = {
                    k: (freq.get("contadores") or {}).get(k, {}).get("pct_blend")
                    for k in ("fees", "medio_fees", "tablas", "morado")
                }
                return info
        except Exception:
            pass

    pct = pct_tiempo_sobre_umbral(perfil_edge)
    if pct is None:
        return {
            "tau_h": tau_base,
            "pct_frecuencia": None,
            "modo": "fallback_estatico",
        }
    pct = max(0.0, min(1.0, pct))
    tau = tau_min + (tau_max - tau_min) * pct
    return {
        "tau_h": round(tau, 4),
        "pct_frecuencia": round(pct, 4),
        "modo": "kaiser_invertido",
    }


def factor_urgencia(
    t0: float,
    *,
    perfil_edge: dict | None = None,
    ahora: float | None = None,
    base: str | None = None,
) -> dict[str, Any]:
    """factor ∈ [0,1] = edad_h / tau_h (tau dinámico invertido)."""
    ahora = ahora if ahora is not None else time.time()
    info = tau_paciencia_horas(perfil_edge, base=base)
    tau_h = float(info["tau_h"]) or 1.0
    edad_h = max(0.0, (ahora - float(t0 or ahora)) / 3600.0)
    factor = min(1.0, edad_h / tau_h)
    return {
        "factor": factor,
        "edad_h": edad_h,
        **info,
    }


def umbral_urgencia_pct(
    fees_be: float,
    t0: float,
    *,
    perfil_edge: dict | None = None,
    ahora: float | None = None,
    base: str | None = None,
) -> dict[str, float]:
    """umbral = fees_be − factor × (fees_be + holgura_max)."""
    ahora = ahora if ahora is not None else time.time()
    holgura = float(getattr(config, "IGRIS_URGENCIA_HOLGURA_MAX_PCT", 0.05) or 0.0)
    urg = factor_urgencia(t0, perfil_edge=perfil_edge, ahora=ahora, base=base)
    factor = float(urg["factor"])
    umbral = fees_be - factor * (fees_be + holgura)
    return {
        "umbral_pct": round(umbral, 6),
        "fees_be_pct": round(fees_be, 6),
        "factor": round(factor, 4),
        "edad_h": round(float(urg["edad_h"]), 4),
        "tau_h": float(urg["tau_h"]),
        "pct_frecuencia": urg.get("pct_frecuencia"),
        "modo_paciencia": urg.get("modo"),
        "holgura_max_pct": holgura,
    }


def fraccion_mordida_igris(
    op: dict,
    *,
    perfiles: dict | None = None,
    tank_semaforo: str = "VERDE",
    pipeline_ms: float | None = None,
    margen_ocupado_pct: float = 0.0,
) -> dict[str, Any]:
    """
    Reusa calcular_confianza de Greed, pero:
    - pinza superior = 1.0 (no GREED_FRACCION_MAX 0.85)
    - piso = GREED_FRACCION_MIN (default 0.05)
    """
    conf = sizing.calcular_confianza(
        op,
        perfiles=perfiles,
        tank_semaforo=tank_semaforo,
        pipeline_ms=pipeline_ms,
        margen_ocupado_pct=margen_ocupado_pct,
    )
    confianza = float(conf["confianza"])
    calor = float(conf["calor"])
    mod = float(getattr(config, "GREED_CALOR_MODULO", 0.5))
    fraccion = confianza * (mod + (1.0 - mod) * calor)
    f_min = float(getattr(config, "GREED_FRACCION_MIN", 0.05))
    # Sin pinza 0.85: autorizado a 100% del techo de misión
    fraccion = max(f_min, min(1.0, fraccion))

    # Huérfana sin perfil: conservar cap doctrinal Greed (30%)
    if conf.get("huerfana") and conf.get("sin_perfil"):
        cap_h = float(getattr(config, "GREED_HUERFANA_SIN_PERFIL_FRACCION_MAX", 0.30))
        fraccion = min(fraccion, cap_h)

    out = dict(conf)
    out["fraccion"] = round(fraccion, 4)
    out["fraccion_sin_pinza_85"] = True
    return out


def techo_mision_usd(
    *,
    bids_long: list,
    asks_long: list,
    bids_short: list,
    asks_short: list,
    frente_long: str,
    frente_short: str,
    restante_mision_usd: float,
) -> dict[str, Any]:
    """
    Techo Igris = min(liquidez Ancla Ask L, Bid S, restante misión Beru/horizonte).
    Sin tope 1% equity ni IGRIS_MICRO_MAX_USD.
    """
    prof_l = ancla.profundidad_usd_libro(bids_long, asks_long, frente_long)
    prof_s = ancla.profundidad_usd_libro(bids_short, asks_short, frente_short)
    techo_ask = float(prof_l.get("ask_usd") or 0)
    techo_bid = float(prof_s.get("bid_usd") or 0)
    techo_libro = min(techo_ask, techo_bid) if techo_ask > 0 and techo_bid > 0 else 0.0
    restante = max(0.0, float(restante_mision_usd))
    techo = min(techo_libro, restante) if restante > 0 and techo_libro > 0 else 0.0
    min_par = ancla.min_order_usd_cruce([frente_long, frente_short])
    return {
        "techo_usd": round(techo, 4),
        "techo_libro_usd": round(techo_libro, 4),
        "techo_ask_usd": techo_ask,
        "techo_bid_usd": techo_bid,
        "restante_mision_usd": restante,
        "min_par_usd": min_par,
        "ok_techo": techo + 1e-9 >= min_par and techo > 0,
    }


def masa_desde_usd(usd: float, precio: float) -> float:
    if usd <= 0 or precio <= 0:
        return 0.0
    return usd / precio


def filtrar_alertas_jurisdiccion(
    alertas: list[dict],
    activo: str,
    *,
    tipos_ok: frozenset[str] | None = None,
) -> list[dict]:
    """Solo alertas del activo del manto; preferir lineal_vs_inverse / MATRIZ."""
    activo_u = (activo or "").upper()
    tipos = tipos_ok or frozenset({
        "MATRIZ_SPREAD", "OPORTUNIDAD_MANTO", "FUNDING", "ALERTA", "DESVIO_INDICE",
    })
    out: list[dict] = []
    for a in alertas or []:
        base = str(a.get("base") or "").upper()
        if base and base != activo_u:
            continue
        tipo = str(a.get("tipo") or "")
        if tipo and tipo not in tipos:
            # Permitir si el payload es lineal_vs_inverse
            meta = a.get("meta") or a.get("detalle") or {}
            if str(meta.get("tipo") or "") != "lineal_vs_inverse":
                continue
        meta = a.get("meta") or a.get("detalle") or {}
        tipo_sp = str(meta.get("tipo") or "")
        if tipo == "MATRIZ_SPREAD" and tipo_sp and tipo_sp != "lineal_vs_inverse":
            continue
        out.append(a)
    return out


def evaluar_puerta_se(
    tank,
    frente_long: str,
    frente_short: str,
    *,
    t0_paciencia: float,
    restante_usd: float,
    activo: str = "",
    perfiles: dict | None = None,
    tank_semaforo: str = "VERDE",
    pipeline_ms: float | None = None,
    margen_ocupado_pct: float = 0.0,
    ahora: float | None = None,
) -> dict[str, Any]:
    """
    Puerta §E: Ask/Bid, umbral fees±urgencia invertida, mordida = techo_misión × fracción.
    """
    ahora = ahora if ahora is not None else time.time()
    bids_l, asks_l = libro_tank(tank, frente_long)
    bids_s, asks_s = libro_tank(tank, frente_short)
    ask_l = best_ask(asks_l)
    bid_s = best_bid(bids_s)
    fuente_libro = "orderbook"
    sin_libro_real = ask_l <= 0 or bid_s <= 0

    if sin_libro_real and _ticker_puerta_habilitada():
        px_l = precio_ticker_frente(tank, frente_long)
        px_s = precio_ticker_frente(tank, frente_short)
        if px_l <= 0:
            px_l = px_s
        if px_s <= 0:
            px_s = px_l
        if px_l > 0 and px_s > 0:
            # Ask del LONG (inverse) y Bid del SHORT (lineal) desde tickers
            bids_l, asks_l = libro_sintetico_ticker(px_l, restante_usd, frente=frente_long)
            bids_s, asks_s = libro_sintetico_ticker(px_s, restante_usd, frente=frente_short)
            ask_l = best_ask(asks_l)
            bid_s = best_bid(bids_s)
            fuente_libro = "ticker_sim"
            sin_libro_real = False

    if ask_l <= 0 or bid_s <= 0:
        return {
            "ok": False,
            "motivo": "sin_ask_bid_libro",
            "ask_long": ask_l,
            "bid_short": bid_s,
            "fuente_libro": fuente_libro,
        }

    # Candado ojos: solo con orderbook real (no engaña ticker_sim de arena/sim)
    if fuente_libro == "orderbook":
        from core import igris_ojos as ojos

        meta_l = ojos.meta_libro(tank, frente_long, ahora=ahora)
        meta_s = ojos.meta_libro(tank, frente_short, ahora=ahora)
        if meta_l.get("stale") or meta_s.get("stale"):
            return {
                "ok": False,
                "motivo": "libro_stale",
                "ask_long": ask_l,
                "bid_short": bid_s,
                "fuente_libro": fuente_libro,
                "edad_libro_long_s": meta_l.get("edad_s"),
                "edad_libro_short_s": meta_s.get("edad_s"),
                "stale_lim_s": meta_l.get("stale_lim_s"),
            }
        for fr in (frente_long, frente_short):
            div = ojos.divergencia_libro_vs_ticker(tank, fr)
            if not div.get("ok") and div.get("motivo") == "divergencia_ticker":
                return {
                    "ok": False,
                    "motivo": "libro_divergente_ticker",
                    "ask_long": ask_l,
                    "bid_short": bid_s,
                    "fuente_libro": fuente_libro,
                    "divergencia": div,
                    "frente_div": fr,
                }

    base = (activo or "").upper()
    if not base:
        base = frente_long.replace("USD_INVERSE", "").replace("USDT_LINEAL", "")

    perfil = None
    if perfiles:
        perfil = (perfiles.get(base) or {}).get("lineal_vs_inverse")

    spread = spread_ejecutable_pct(ask_l, bid_s)
    fees_be = fees_break_even_pct(frente_long, frente_short)

    sin_paciencia = (
        getattr(config, "ARENA_IGRIS_ACTIVA", False)
        and getattr(config, "ARENA_IGRIS_SIN_PACIENCIA", False)
    )
    if sin_paciencia:
        umbral_micro = float(getattr(config, "ARENA_IGRIS_UMBRAL_PCT", 0.01))
        urg = {
            "umbral_pct": umbral_micro,
            "factor": 0.0,
            "modo_paciencia": "arena_sin_paciencia",
            "fees_be_pct": fees_be,
            "spread_pct": round(spread, 6),
        }
        umbral = umbral_micro
    elif getattr(config, "PASE_DIRECTOR_ACTIVO", True):
        from core import pase_director as pd
        urg = pd.umbral_por_marcha(
            fees_be,
            t0_paciencia=t0_paciencia,
            perfil_edge=perfil,
            ahora=ahora,
            base=base,
        )
        umbral = float(urg["umbral_pct"])
    else:
        urg = umbral_urgencia_pct(
            fees_be, t0_paciencia, perfil_edge=perfil, ahora=ahora, base=base,
        )
        umbral = urg["umbral_pct"]

    # Cero estructural: no abrir el manto solo por el gap eterno
    from core import kaiser_sesgo_index as ksi
    cero_info = ksi.cero_estructural_manto(base)
    cero = cero_info.get("cero_pct") if cero_info.get("ok") else None
    umbral_fees = float(umbral)
    umbral = ksi.umbral_manto_con_cero(umbral_fees, cero)
    # Ojos sin muros: el ticker no mide edge real — no esperar spread vivo
    if fuente_libro == "ticker_sim":
        umbral = 0.0
    urg = {
        **urg,
        "umbral_fees_pct": round(umbral_fees, 6),
        "cero_estructural_pct": cero,
        "cero_fuente": cero_info.get("fuente"),
        "umbral_pct": round(umbral, 6),
        "exceso_vs_cero_pct": round(ksi.exceso_vs_cero(spread, cero), 6),
        "fuente_libro": fuente_libro,
    }

    if spread < umbral:
        return {
            "ok": False,
            "motivo": "spread_bajo_umbral",
            "ask_long": ask_l,
            "bid_short": bid_s,
            "spread_pct": round(spread, 6),
            **urg,
        }

    techo_info = techo_mision_usd(
        bids_long=bids_l,
        asks_long=asks_l,
        bids_short=bids_s,
        asks_short=asks_s,
        frente_long=frente_long,
        frente_short=frente_short,
        restante_mision_usd=restante_usd,
    )
    if not techo_info["ok_techo"]:
        return {
            "ok": False,
            "motivo": "bajo_min_order_o_sin_libro",
            "ask_long": ask_l,
            "bid_short": bid_s,
            "spread_pct": round(spread, 6),
            **urg,
            **techo_info,
        }

    op = {
        "base": base,
        "tipo_spread": "lineal_vs_inverse",
        "entrada_maxima_usd": techo_info["techo_usd"],
        "frentes": {"compra": frente_long, "venta": frente_short, "todos": [frente_long, frente_short]},
        "regalo_neto_pct_est": max(0.0, spread - fees_be),
    }
    frac_info = fraccion_mordida_igris(
        op,
        perfiles=perfiles,
        tank_semaforo=tank_semaforo,
        pipeline_ms=pipeline_ms,
        margen_ocupado_pct=margen_ocupado_pct,
    )
    fraccion = float(frac_info["fraccion"])
    if getattr(config, "ARENA_IGRIS_ACTIVA", False):
        mordida = float(getattr(config, "ARENA_IGRIS_MORDIDA_USD", 5.0))
        mordida = min(mordida, float(techo_info["techo_usd"]), float(restante_usd))
    else:
        mordida = round(float(techo_info["techo_usd"]) * fraccion, 4)
    min_par = float(techo_info["min_par_usd"])
    # Si la fracción queda bajo minBybit pero el techo alcanza → subir a min_par
    if mordida + 1e-9 < min_par:
        techo = float(techo_info["techo_usd"] or 0)
        if techo + 1e-9 >= min_par:
            mordida = round(min(techo, float(restante_usd), min_par), 4)
    if mordida + 1e-9 < min_par:
        return {
            "ok": False,
            "motivo": "mordida_bajo_min_order",
            "ask_long": ask_l,
            "bid_short": bid_s,
            "spread_pct": round(spread, 6),
            "micro_usd": mordida,
            "fraccion": fraccion,
            **urg,
            **techo_info,
            **{k: frac_info[k] for k in ("confianza", "calor") if k in frac_info},
        }

    precio_ref = (ask_l + bid_s) / 2.0
    # Ley de la Masa: Alfa = Lineal; Inverso espeja USD; candado asimetría
    from core import lote_bybit as lote

    ley = lote.ley_de_la_masa_dual(
        frente_long, frente_short, ask_l, bid_s, mordida,
    )
    if not ley.get("ok"):
        return {
            "ok": False,
            "motivo": str(ley.get("motivo") or "ley_masa_fallida"),
            "ask_long": ask_l,
            "bid_short": bid_s,
            "spread_pct": round(spread, 6),
            "micro_usd": mordida,
            "fraccion": fraccion,
            "ley_masa": ley,
            **urg,
            **techo_info,
            **{k: frac_info[k] for k in ("confianza", "calor") if k in frac_info},
        }

    usd_dual = float(ley["masa_absoluta_usd"])
    masa_l = float(ley["qty_a"])
    masa_s = float(ley["qty_b"])
    # Compat: masa promedio en coin-eq solo para reservas Tusk/delta en USD usamos usd_dual
    masa = masa_desde_usd(usd_dual, precio_ref) if precio_ref > 0 else 0.0
    if masa_l <= 0 or masa_s <= 0:
        return {
            "ok": False,
            "motivo": "masa_micro_cero",
            "ask_long": ask_l,
            "bid_short": bid_s,
            "spread_pct": round(spread, 6),
            "ley_masa": ley,
            **urg,
        }

    return {
        "ok": True,
        "motivo": "OK" if fuente_libro == "orderbook" else "OK_ticker_sim",
        "ask_long": ask_l,
        "bid_short": bid_s,
        "precio_ref": precio_ref,
        "spread_pct": round(spread, 6),
        "micro_usd": usd_dual,
        "masa": masa,
        "masa_long": masa_l,
        "masa_short": masa_s,
        "usd_long": float(ley["usd_a"]),
        "usd_short": float(ley["usd_b"]),
        "alfa_usd": float(ley["alfa_usd"]),
        "ley_masa": ley,
        "fraccion": fraccion,
        "confianza": frac_info.get("confianza"),
        "calor": frac_info.get("calor"),
        "min_par_usd": min_par,
        **techo_info,
        **urg,
    }
