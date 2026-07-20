"""Director del pase de batalla — potencia, lote por marcha, umbral Igris.

Doctrina Monarca 2026-07-19:
- Equity → pasos en potencia (techo teórico).
- Lote = potencia − reserva(marcha); cola fina = últimos pasos uno a uno.
- Marcha fija spread mínimo del manto: fees / ½ fees / asalto (market).
- Beru caza cuando el manto del paso está logrado.
"""
from __future__ import annotations

import json
import os
import time
from typing import Any, Literal

import core.config as config

MarchaId = Literal["tactico", "marcha_forzada", "asalto"]
GradoPase = Literal["SOLDADO", "CAPITAN", "GENERAL", "MARISCAL"]

# Caballero del pergamino = CAPITAN en motor Beru
_GRADO_UI = {
    "SOLDADO": "Soldado",
    "CAPITAN": "Caballero",
    "GENERAL": "General",
    "MARISCAL": "Mariscal",
}

# 52 pasos canónicos — migracion/PASE_BATALLA_13_SANTOS.md
PASE_PASOS: tuple[dict[str, Any], ...] = (
    {"n": 1, "activo": "ETH", "grado": "SOLDADO", "delta_usd": 14.0, "acum_usd": 14.0},
    {"n": 2, "activo": "HYPE", "grado": "SOLDADO", "delta_usd": 28.0, "acum_usd": 42.0},
    {"n": 3, "activo": "XRP", "grado": "SOLDADO", "delta_usd": 18.0, "acum_usd": 60.0},
    {"n": 4, "activo": "MNT", "grado": "SOLDADO", "delta_usd": 36.0, "acum_usd": 96.0},
    {"n": 5, "activo": "LTC", "grado": "SOLDADO", "delta_usd": 27.0, "acum_usd": 123.0},
    {"n": 6, "activo": "SOL", "grado": "SOLDADO", "delta_usd": 18.0, "acum_usd": 141.0},
    {"n": 7, "activo": "LINK", "grado": "SOLDADO", "delta_usd": 38.0, "acum_usd": 179.0},
    {"n": 8, "activo": "ADA", "grado": "SOLDADO", "delta_usd": 22.0, "acum_usd": 201.0},
    {"n": 9, "activo": "BCH", "grado": "SOLDADO", "delta_usd": 38.0, "acum_usd": 239.0},
    {"n": 10, "activo": "AVAX", "grado": "SOLDADO", "delta_usd": 38.0, "acum_usd": 277.0},
    {"n": 11, "activo": "AVAX", "grado": "CAPITAN", "delta_usd": 37.0, "acum_usd": 314.0},
    {"n": 12, "activo": "FIL", "grado": "SOLDADO", "delta_usd": 59.0, "acum_usd": 373.0},
    {"n": 13, "activo": "OP", "grado": "SOLDADO", "delta_usd": 38.0, "acum_usd": 411.0},
    {"n": 14, "activo": "LINK", "grado": "CAPITAN", "delta_usd": 37.0, "acum_usd": 448.0},
    {"n": 15, "activo": "LINK", "grado": "GENERAL", "delta_usd": 75.0, "acum_usd": 523.0},
    {"n": 16, "activo": "LINK", "grado": "MARISCAL", "delta_usd": 151.0, "acum_usd": 674.0},
    {"n": 17, "activo": "SOL", "grado": "CAPITAN", "delta_usd": 17.0, "acum_usd": 691.0},
    {"n": 18, "activo": "SOL", "grado": "GENERAL", "delta_usd": 35.0, "acum_usd": 726.0},
    {"n": 19, "activo": "SOL", "grado": "MARISCAL", "delta_usd": 70.0, "acum_usd": 796.0},
    {"n": 20, "activo": "MNT", "grado": "CAPITAN", "delta_usd": 34.0, "acum_usd": 830.0},
    {"n": 21, "activo": "MNT", "grado": "GENERAL", "delta_usd": 70.0, "acum_usd": 900.0},
    {"n": 22, "activo": "MNT", "grado": "MARISCAL", "delta_usd": 141.0, "acum_usd": 1041.0},
    {"n": 23, "activo": "AVAX", "grado": "GENERAL", "delta_usd": 75.0, "acum_usd": 1116.0},
    {"n": 24, "activo": "AVAX", "grado": "MARISCAL", "delta_usd": 151.0, "acum_usd": 1267.0},
    {"n": 25, "activo": "LTC", "grado": "CAPITAN", "delta_usd": 26.0, "acum_usd": 1293.0},
    {"n": 26, "activo": "LTC", "grado": "GENERAL", "delta_usd": 52.0, "acum_usd": 1345.0},
    {"n": 27, "activo": "LTC", "grado": "MARISCAL", "delta_usd": 106.0, "acum_usd": 1451.0},
    {"n": 28, "activo": "ADA", "grado": "CAPITAN", "delta_usd": 20.0, "acum_usd": 1471.0},
    {"n": 29, "activo": "ADA", "grado": "GENERAL", "delta_usd": 42.0, "acum_usd": 1513.0},
    {"n": 30, "activo": "ADA", "grado": "MARISCAL", "delta_usd": 84.0, "acum_usd": 1597.0},
    {"n": 31, "activo": "BCH", "grado": "CAPITAN", "delta_usd": 37.0, "acum_usd": 1634.0},
    {"n": 32, "activo": "BCH", "grado": "GENERAL", "delta_usd": 75.0, "acum_usd": 1709.0},
    {"n": 33, "activo": "BCH", "grado": "MARISCAL", "delta_usd": 151.0, "acum_usd": 1860.0},
    {"n": 34, "activo": "OP", "grado": "CAPITAN", "delta_usd": 37.0, "acum_usd": 1897.0},
    {"n": 35, "activo": "OP", "grado": "GENERAL", "delta_usd": 75.0, "acum_usd": 1972.0},
    {"n": 36, "activo": "OP", "grado": "MARISCAL", "delta_usd": 151.0, "acum_usd": 2123.0},
    {"n": 37, "activo": "ETH", "grado": "CAPITAN", "delta_usd": 12.0, "acum_usd": 2135.0},
    {"n": 38, "activo": "ETH", "grado": "GENERAL", "delta_usd": 27.0, "acum_usd": 2162.0},
    {"n": 39, "activo": "ETH", "grado": "MARISCAL", "delta_usd": 52.0, "acum_usd": 2214.0},
    {"n": 40, "activo": "AAVE", "grado": "SOLDADO", "delta_usd": 28.0, "acum_usd": 2242.0},
    {"n": 41, "activo": "AAVE", "grado": "CAPITAN", "delta_usd": 27.0, "acum_usd": 2269.0},
    {"n": 42, "activo": "FIL", "grado": "CAPITAN", "delta_usd": 58.0, "acum_usd": 2327.0},
    {"n": 43, "activo": "FIL", "grado": "GENERAL", "delta_usd": 117.0, "acum_usd": 2444.0},
    {"n": 44, "activo": "FIL", "grado": "MARISCAL", "delta_usd": 234.0, "acum_usd": 2678.0},
    {"n": 45, "activo": "AAVE", "grado": "GENERAL", "delta_usd": 56.0, "acum_usd": 2734.0},
    {"n": 46, "activo": "AAVE", "grado": "MARISCAL", "delta_usd": 111.0, "acum_usd": 2845.0},
    {"n": 47, "activo": "HYPE", "grado": "CAPITAN", "delta_usd": 27.0, "acum_usd": 2872.0},
    {"n": 48, "activo": "HYPE", "grado": "GENERAL", "delta_usd": 56.0, "acum_usd": 2928.0},
    {"n": 49, "activo": "HYPE", "grado": "MARISCAL", "delta_usd": 111.0, "acum_usd": 3039.0},
    {"n": 50, "activo": "XRP", "grado": "CAPITAN", "delta_usd": 17.0, "acum_usd": 3056.0},
    {"n": 51, "activo": "XRP", "grado": "GENERAL", "delta_usd": 35.0, "acum_usd": 3091.0},
    {"n": 52, "activo": "XRP", "grado": "MARISCAL", "delta_usd": 70.0, "acum_usd": 3161.0},
)

# Reserva de pasos (no abrir todo el techo de golpe) + umbral fees
MARCHAS: dict[str, dict[str, Any]] = {
    "tactico": {
        "titulo": "Despliegue Tactico",
        "reserva_pasos": 3,
        "umbral_fees_mult": 1.0,
        "permite_urgencia": False,
        "force_market": False,
        "fill_ratio": 0.90,
    },
    "marcha_forzada": {
        "titulo": "Marcha Forzada",
        "reserva_pasos": 2,
        "umbral_fees_mult": 0.5,
        "permite_urgencia": True,
        "force_market": False,
        "fill_ratio": 0.85,
    },
    "asalto": {
        "titulo": "Asalto Inmediato",
        "reserva_pasos": 0,
        "umbral_fees_mult": 0.0,
        "permite_urgencia": False,
        "force_market": True,
        "fill_ratio": 0.75,
    },
}

MARCHA_DEFAULT: MarchaId = "marcha_forzada"


def director_activo() -> bool:
    return bool(getattr(config, "PASE_DIRECTOR_ACTIVO", True))


def _ruta_base() -> str:
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _ruta_marcha() -> str:
    return os.path.join(_ruta_base(), "data", "marcha_despliegue.json")


def _ruta_progreso() -> str:
    return os.path.join(_ruta_base(), "data", "pase_progreso.json")


def normalizar_marcha(mid: str | None) -> MarchaId:
    m = (mid or "").strip().lower()
    if m in MARCHAS:
        return m  # type: ignore[return-value]
    env = str(getattr(config, "MARCHA_DESPLIEGUE", MARCHA_DEFAULT) or MARCHA_DEFAULT).lower()
    if env in MARCHAS:
        return env  # type: ignore[return-value]
    return MARCHA_DEFAULT


def perfil_marcha(mid: str | None = None) -> dict[str, Any]:
    """Perfil activo: si mid es None, lee data/marcha_despliegue.json."""
    m = cargar_marcha() if mid is None else normalizar_marcha(mid)
    return {"id": m, **MARCHAS[m]}


def cargar_marcha() -> MarchaId:
    ruta = _ruta_marcha()
    if os.path.exists(ruta):
        try:
            with open(ruta, encoding="utf-8") as f:
                data = json.load(f)
            got = str(data.get("marcha_id") or data.get("id") or "").strip().lower()
            if got in MARCHAS:
                return got  # type: ignore[return-value]
        except (json.JSONDecodeError, OSError, TypeError):
            pass
    return normalizar_marcha(None)


def guardar_marcha(marcha_id: str) -> dict[str, Any]:
    mid = normalizar_marcha(marcha_id)
    ruta = _ruta_marcha()
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    payload = {
        "marcha_id": mid,
        "titulo": MARCHAS[mid]["titulo"],
        "ts": time.time(),
        **{k: MARCHAS[mid][k] for k in (
            "reserva_pasos", "umbral_fees_mult", "force_market", "permite_urgencia",
        )},
    }
    tmp = ruta + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    if os.path.exists(ruta):
        os.remove(ruta)
    os.rename(tmp, ruta)
    return payload


def cargar_progreso() -> dict[str, Any]:
    ruta = _ruta_progreso()
    if not os.path.exists(ruta):
        return {"pasos_logrados": [], "ts": 0}
    try:
        with open(ruta, encoding="utf-8") as f:
            data = json.load(f)
        logs = [int(x) for x in (data.get("pasos_logrados") or []) if int(x) >= 1]
        return {"pasos_logrados": sorted(set(logs)), "ts": float(data.get("ts") or 0)}
    except (json.JSONDecodeError, OSError, TypeError, ValueError):
        return {"pasos_logrados": [], "ts": 0}


def guardar_progreso(pasos_logrados: list[int]) -> dict[str, Any]:
    logs = sorted({int(x) for x in pasos_logrados if int(x) >= 1})
    ruta = _ruta_progreso()
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    payload = {"pasos_logrados": logs, "ts": time.time()}
    tmp = ruta + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    if os.path.exists(ruta):
        os.remove(ruta)
    os.rename(tmp, ruta)
    return payload


def marcar_paso_logrado(n: int) -> dict[str, Any]:
    prog = cargar_progreso()
    logs = list(prog.get("pasos_logrados") or [])
    ni = int(n)
    if ni not in logs:
        logs.append(ni)
    return guardar_progreso(logs)


def paso_por_n(n: int) -> dict[str, Any] | None:
    for p in PASE_PASOS:
        if int(p["n"]) == int(n):
            return dict(p)
    return None


def potencia_n(equity_usd: float) -> int:
    """Cuántos pasos del pase caben en potencia con este equity."""
    eq = max(0.0, float(equity_usd))
    n = 0
    for p in PASE_PASOS:
        if eq + 1e-9 >= float(p["acum_usd"]):
            n = int(p["n"])
        else:
            break
    return n


def pasos_en_potencia(equity_usd: float) -> list[dict[str, Any]]:
    n = potencia_n(equity_usd)
    return [dict(p) for p in PASE_PASOS if int(p["n"]) <= n]


def _ordenar_logrados(pasos_logrados: list[int] | None) -> list[int]:
    return sorted({int(x) for x in (pasos_logrados or []) if int(x) >= 1})


def plan_lote(
    equity_usd: float,
    *,
    marcha_id: str | None = None,
    pasos_logrados: list[int] | None = None,
) -> dict[str, Any]:
    """
    Con N en potencia y reserva R:
    - lote paralelo = primeros max(0, N−R) pasos aún no logrados (y ≤ N−R)
    - cola fina = pasos (N−R+1)…N uno a uno tras cerrar el lote
    """
    mid = normalizar_marcha(marcha_id or cargar_marcha())
    perfil = MARCHAS[mid]
    n_pot = potencia_n(equity_usd)
    reserva = int(perfil["reserva_pasos"])
    n_lote_techo = max(0, n_pot - reserva) if n_pot > 0 else 0
    logrados = set(_ordenar_logrados(pasos_logrados if pasos_logrados is not None else cargar_progreso()["pasos_logrados"]))

    lote: list[dict[str, Any]] = []
    cola: list[dict[str, Any]] = []
    for p in PASE_PASOS:
        pn = int(p["n"])
        if pn > n_pot:
            break
        row = {**dict(p), "logrado": pn in logrados, "etiqueta": f"{p['activo']} {_GRADO_UI.get(p['grado'], p['grado'])}"}
        if pn <= n_lote_techo:
            lote.append(row)
        else:
            cola.append(row)

    incompletos_lote = [p for p in lote if not p["logrado"]]
    lote_lleno = bool(lote) and not incompletos_lote
    # Cola: solo el primero incompleto si el lote ya está lleno (o no hay lote)
    cola_activa: list[dict[str, Any]] = []
    if lote_lleno or n_lote_techo == 0:
        for p in cola:
            if not p["logrado"]:
                cola_activa = [p]
                break

    trabajo = incompletos_lote if incompletos_lote else cola_activa
    foco = trabajo[0] if trabajo else None

    return {
        "marcha_id": mid,
        "marcha_titulo": perfil["titulo"],
        "reserva_pasos": reserva,
        "potencia_n": n_pot,
        "lote_techo_n": n_lote_techo,
        "pasos_logrados": sorted(logrados),
        "n_logrados": len(logrados),
        "lote": lote,
        "cola_fina": cola,
        "trabajo": trabajo,
        "foco": foco,
        "lote_lleno": lote_lleno,
        "activos_trabajo": sorted({str(p["activo"]) for p in trabajo}),
        "umbral_fees_mult": float(perfil["umbral_fees_mult"]),
        "force_market": bool(perfil["force_market"]),
        "permite_urgencia": bool(perfil["permite_urgencia"]),
        "fill_ratio": float(perfil["fill_ratio"]),
    }


def activo_manto_foco(
    equity_usd: float,
    *,
    marcha_id: str | None = None,
    pasos_logrados: list[int] | None = None,
    tusk=None,
) -> str:
    """Activo que Igris debe engordar: entre el lote abierto, el más atrasado."""
    plan = plan_lote(equity_usd, marcha_id=marcha_id, pasos_logrados=pasos_logrados)
    trabajo = list(plan.get("trabajo") or [])
    if not trabajo:
        from core import plan_crecimiento as pc
        return pc.activo_manto_preferido(equity_usd)
    if tusk is None or len(trabajo) == 1:
        return str(trabajo[0]["activo"]).upper()
    best = trabajo[0]
    best_ratio = 1e18
    for p in trabajo:
        act = str(p["activo"]).upper()
        need = max(float(p["delta_usd"]), 1.0)
        have = notional_manto_usd(tusk, act)
        ratio = have / need
        if ratio < best_ratio:
            best_ratio = ratio
            best = p
    return str(best["activo"]).upper()


def activos_lote_abiertos(
    equity_usd: float,
    *,
    marcha_id: str | None = None,
    pasos_logrados: list[int] | None = None,
) -> list[str]:
    plan = plan_lote(equity_usd, marcha_id=marcha_id, pasos_logrados=pasos_logrados)
    return list(plan.get("activos_trabajo") or [])


def umbral_por_marcha(
    fees_be_pct: float,
    *,
    marcha_id: str | None = None,
    t0_paciencia: float | None = None,
    perfil_edge: dict | None = None,
    ahora: float | None = None,
) -> dict[str, Any]:
    """
    Táctico: umbral = fees (sin degradar).
    Forzada: piso = ½ fees; urgencia Kaiser puede bajar hasta ese piso.
    Asalto: umbral = 0 (entra ya / market).
    """
    mid = cargar_marcha() if marcha_id is None else normalizar_marcha(marcha_id)
    perfil = MARCHAS[mid]
    fees = max(0.0, float(fees_be_pct))
    mult = float(perfil["umbral_fees_mult"])
    piso = fees * mult

    if mid == "asalto" or mult <= 0:
        return {
            "umbral_pct": 0.0,
            "fees_be_pct": round(fees, 6),
            "factor": 1.0,
            "modo_paciencia": "marcha_asalto",
            "marcha_id": mid,
            "force_market": True,
            "piso_fees_mult": mult,
        }

    if not perfil["permite_urgencia"] or t0_paciencia is None:
        return {
            "umbral_pct": round(piso, 6),
            "fees_be_pct": round(fees, 6),
            "factor": 0.0,
            "modo_paciencia": f"marcha_{mid}",
            "marcha_id": mid,
            "force_market": False,
            "piso_fees_mult": mult,
        }

    # Urgencia: parte de fees y baja hacia el piso (½ fees), no por debajo
    from core import igris_despliegue as ides
    urg = ides.umbral_urgencia_pct(
        fees, float(t0_paciencia), perfil_edge=perfil_edge, ahora=ahora,
    )
    umbral_dyn = float(urg.get("umbral_pct") or fees)
    umbral = max(piso, umbral_dyn) if piso > 0 else umbral_dyn
    # Si el reloj ya bajó bajo el piso, respetar piso; si empieza en fees, ok
    if umbral_dyn > fees:
        umbral = max(piso, fees)
    return {
        **urg,
        "umbral_pct": round(umbral, 6),
        "fees_be_pct": round(fees, 6),
        "modo_paciencia": f"marcha_{mid}_urgencia",
        "marcha_id": mid,
        "force_market": False,
        "piso_fees_mult": mult,
        "piso_pct": round(piso, 6),
    }


def beru_puede_cazar(
    activo: str,
    equity_usd: float,
    *,
    marcha_id: str | None = None,
    pasos_logrados: list[int] | None = None,
) -> bool:
    """Beru caza en un Santo solo si hay al menos un paso logrado de ese activo."""
    if not director_activo():
        return True
    if getattr(config, "LIVE_BERU_TESTNET", False):
        return True
    act = (activo or "").upper()
    logrados = set(_ordenar_logrados(pasos_logrados if pasos_logrados is not None else cargar_progreso()["pasos_logrados"]))
    if not logrados:
        # Sin manto logrado aún: no caza (espera Igris)
        return False
    for p in PASE_PASOS:
        if int(p["n"]) in logrados and str(p["activo"]).upper() == act:
            return True
    return False


def notional_manto_usd(tusk, activo: str) -> float:
    """Estima USD desplegados L+S del manto de un activo (promedio × masa)."""
    try:
        from core import igris_manto as im
        fl, fs = im.frentes_bootstrap(activo)
    except Exception:
        return 0.0
    pesos = getattr(tusk, "pesos", None) or {}
    total = 0.0
    for frente, lado in ((fl, "long"), (fs, "short")):
        p = pesos.get(frente) or {}
        masa = float(p.get(lado) or 0)
        if masa <= 0:
            continue
        key = "precio_medio_long" if lado == "long" else "precio_medio_short"
        px = float(p.get(key) or 0)
        if px <= 0:
            px = float(p.get("precio_medio_long") or p.get("precio_medio_short") or 0)
        if px > 0:
            total += abs(masa) * px
        else:
            # fallback: masa ya en USD en algunos caminos
            total += abs(masa)
    return total


def sincronizar_logrados_desde_tusk(
    tusk,
    equity_usd: float,
    *,
    marcha_id: str | None = None,
) -> dict[str, Any]:
    """Marca pasos logrados si el manto del activo cubre el Δ acumulado del Santo (fill_ratio)."""
    mid = normalizar_marcha(marcha_id or cargar_marcha())
    fill = float(MARCHAS[mid]["fill_ratio"])
    n_pot = potencia_n(equity_usd)
    prog = cargar_progreso()
    logs = set(int(x) for x in (prog.get("pasos_logrados") or []))
    desplegado: dict[str, float] = {}
    need_por_activo: dict[str, float] = {}
    changed = False

    for p in PASE_PASOS:
        pn = int(p["n"])
        if pn > n_pot:
            break
        act = str(p["activo"]).upper()
        if act not in desplegado:
            desplegado[act] = notional_manto_usd(tusk, act)
        need_por_activo[act] = need_por_activo.get(act, 0.0) + float(p["delta_usd"])
        if pn in logs:
            continue
        # Encadenado: paso anterior global logrado (o n==1)
        if pn > 1 and (pn - 1) not in logs:
            continue
        if desplegado.get(act, 0.0) + 1e-6 >= need_por_activo[act] * fill:
            logs.add(pn)
            changed = True

    if changed:
        guardar_progreso(sorted(logs))
    return plan_lote(equity_usd, marcha_id=mid, pasos_logrados=sorted(logs))


def marcar_foco_si_bloque_completo(
    equity_usd: float,
    activo: str,
    *,
    marcha_id: str | None = None,
) -> dict[str, Any] | None:
    """Tras misión/bloque Igris: marca el foco actual si coincide el activo."""
    plan = plan_lote(equity_usd, marcha_id=marcha_id)
    foco = plan.get("foco")
    if not foco:
        return None
    if str(foco["activo"]).upper() != str(activo or "").upper():
        return None
    return marcar_paso_logrado(int(foco["n"]))


def resumen_director(equity_usd: float) -> dict[str, Any]:
    mid = cargar_marcha()
    plan = plan_lote(equity_usd, marcha_id=mid)
    foco = plan.get("foco")
    return {
        "activo": director_activo(),
        "marcha_id": plan["marcha_id"],
        "marcha_titulo": plan["marcha_titulo"],
        "potencia_n": plan["potencia_n"],
        "reserva_pasos": plan["reserva_pasos"],
        "lote_techo_n": plan["lote_techo_n"],
        "n_logrados": plan["n_logrados"],
        "pasos_logrados": plan["pasos_logrados"],
        "lote_lleno": plan["lote_lleno"],
        "activos_trabajo": plan["activos_trabajo"],
        "foco": foco,
        "umbral_fees_mult": plan["umbral_fees_mult"],
        "force_market": plan["force_market"],
        "equity_usd": round(max(0.0, float(equity_usd)), 2),
    }
