"""Director del pase de batalla — potencia, lote por marcha, umbral Igris.

Sello mega-pre-Igris + sello 2 marchas (Monarca):
- Engorde 100% del *nocional del grado* en foco (fill_ratio=1.0).
  Capital delta_usd = peaje IM pierna a pierna (lev máx Bybit L+S); abre potencia/ranking.
  Caja = USDT. Short MNT legado no suma al presupuesto ofensivo.
  Igris planta nocional L+S del grado.
- Reserva = 1 en todas las marchas (lote hasta potencia−1).
- Operativas: **asalto** (rápido / peaje) y **personalizado** (T días / calib).
- Legado `tactico` / `marcha_forzada` → se normalizan a **asalto** (sin reescribir disco).
- Meta llena (restante≤0) → no engordar más ese foco.
"""
from __future__ import annotations

import json
import os
import time
from typing import Any, Literal

import core.config as config

MarchaId = Literal["asalto", "personalizado"]
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
    {"n": 2, "activo": "HYPE", "grado": "SOLDADO", "delta_usd": 42.0, "acum_usd": 56.0},
    {"n": 3, "activo": "XRP", "grado": "SOLDADO", "delta_usd": 20.0, "acum_usd": 76.0},
    {"n": 4, "activo": "MNT", "grado": "SOLDADO", "delta_usd": 40.0, "acum_usd": 116.0},
    {"n": 5, "activo": "LTC", "grado": "SOLDADO", "delta_usd": 27.0, "acum_usd": 143.0},
    {"n": 6, "activo": "SOL", "grado": "SOLDADO", "delta_usd": 20.0, "acum_usd": 163.0},
    {"n": 7, "activo": "LINK", "grado": "SOLDADO", "delta_usd": 47.0, "acum_usd": 210.0},
    {"n": 8, "activo": "ADA", "grado": "SOLDADO", "delta_usd": 22.0, "acum_usd": 232.0},
    {"n": 9, "activo": "BCH", "grado": "SOLDADO", "delta_usd": 47.0, "acum_usd": 279.0},
    {"n": 10, "activo": "AVAX", "grado": "SOLDADO", "delta_usd": 47.0, "acum_usd": 326.0},
    {"n": 11, "activo": "AVAX", "grado": "CAPITAN", "delta_usd": 45.0, "acum_usd": 371.0},
    {"n": 12, "activo": "FIL", "grado": "SOLDADO", "delta_usd": 60.0, "acum_usd": 431.0},
    {"n": 13, "activo": "OP", "grado": "SOLDADO", "delta_usd": 47.0, "acum_usd": 478.0},
    {"n": 14, "activo": "LINK", "grado": "CAPITAN", "delta_usd": 45.0, "acum_usd": 523.0},
    {"n": 15, "activo": "LINK", "grado": "GENERAL", "delta_usd": 92.0, "acum_usd": 615.0},
    {"n": 16, "activo": "LINK", "grado": "MARISCAL", "delta_usd": 184.0, "acum_usd": 799.0},
    {"n": 17, "activo": "SOL", "grado": "CAPITAN", "delta_usd": 19.0, "acum_usd": 818.0},
    {"n": 18, "activo": "SOL", "grado": "GENERAL", "delta_usd": 40.0, "acum_usd": 858.0},
    {"n": 19, "activo": "SOL", "grado": "MARISCAL", "delta_usd": 79.0, "acum_usd": 937.0},
    {"n": 20, "activo": "MNT", "grado": "CAPITAN", "delta_usd": 39.0, "acum_usd": 976.0},
    {"n": 21, "activo": "MNT", "grado": "GENERAL", "delta_usd": 79.0, "acum_usd": 1055.0},
    {"n": 22, "activo": "MNT", "grado": "MARISCAL", "delta_usd": 158.0, "acum_usd": 1213.0},
    {"n": 23, "activo": "AVAX", "grado": "GENERAL", "delta_usd": 92.0, "acum_usd": 1305.0},
    {"n": 24, "activo": "AVAX", "grado": "MARISCAL", "delta_usd": 184.0, "acum_usd": 1489.0},
    {"n": 25, "activo": "LTC", "grado": "CAPITAN", "delta_usd": 26.0, "acum_usd": 1515.0},
    {"n": 26, "activo": "LTC", "grado": "GENERAL", "delta_usd": 52.0, "acum_usd": 1567.0},
    {"n": 27, "activo": "LTC", "grado": "MARISCAL", "delta_usd": 106.0, "acum_usd": 1673.0},
    {"n": 28, "activo": "ADA", "grado": "CAPITAN", "delta_usd": 22.0, "acum_usd": 1695.0},
    {"n": 29, "activo": "ADA", "grado": "GENERAL", "delta_usd": 44.0, "acum_usd": 1739.0},
    {"n": 30, "activo": "ADA", "grado": "MARISCAL", "delta_usd": 87.0, "acum_usd": 1826.0},
    {"n": 31, "activo": "BCH", "grado": "CAPITAN", "delta_usd": 45.0, "acum_usd": 1871.0},
    {"n": 32, "activo": "BCH", "grado": "GENERAL", "delta_usd": 92.0, "acum_usd": 1963.0},
    {"n": 33, "activo": "BCH", "grado": "MARISCAL", "delta_usd": 184.0, "acum_usd": 2147.0},
    {"n": 34, "activo": "OP", "grado": "CAPITAN", "delta_usd": 45.0, "acum_usd": 2192.0},
    {"n": 35, "activo": "OP", "grado": "GENERAL", "delta_usd": 92.0, "acum_usd": 2284.0},
    {"n": 36, "activo": "OP", "grado": "MARISCAL", "delta_usd": 184.0, "acum_usd": 2468.0},
    {"n": 37, "activo": "ETH", "grado": "CAPITAN", "delta_usd": 12.0, "acum_usd": 2480.0},
    {"n": 38, "activo": "ETH", "grado": "GENERAL", "delta_usd": 27.0, "acum_usd": 2507.0},
    {"n": 39, "activo": "ETH", "grado": "MARISCAL", "delta_usd": 52.0, "acum_usd": 2559.0},
    {"n": 40, "activo": "AAVE", "grado": "SOLDADO", "delta_usd": 42.0, "acum_usd": 2601.0},
    {"n": 41, "activo": "AAVE", "grado": "CAPITAN", "delta_usd": 41.0, "acum_usd": 2642.0},
    {"n": 42, "activo": "FIL", "grado": "CAPITAN", "delta_usd": 58.0, "acum_usd": 2700.0},
    {"n": 43, "activo": "FIL", "grado": "GENERAL", "delta_usd": 119.0, "acum_usd": 2819.0},
    {"n": 44, "activo": "FIL", "grado": "MARISCAL", "delta_usd": 237.0, "acum_usd": 3056.0},
    {"n": 45, "activo": "AAVE", "grado": "GENERAL", "delta_usd": 84.0, "acum_usd": 3140.0},
    {"n": 46, "activo": "AAVE", "grado": "MARISCAL", "delta_usd": 166.0, "acum_usd": 3306.0},
    {"n": 47, "activo": "HYPE", "grado": "CAPITAN", "delta_usd": 41.0, "acum_usd": 3347.0},
    {"n": 48, "activo": "HYPE", "grado": "GENERAL", "delta_usd": 84.0, "acum_usd": 3431.0},
    {"n": 49, "activo": "HYPE", "grado": "MARISCAL", "delta_usd": 166.0, "acum_usd": 3597.0},
    {"n": 50, "activo": "XRP", "grado": "CAPITAN", "delta_usd": 19.0, "acum_usd": 3616.0},
    {"n": 51, "activo": "XRP", "grado": "GENERAL", "delta_usd": 40.0, "acum_usd": 3656.0},
    {"n": 52, "activo": "XRP", "grado": "MARISCAL", "delta_usd": 79.0, "acum_usd": 3735.0},
)

# Reserva de pasos (no abrir todo el techo de golpe) + umbral fees
# Sello 2 marchas: solo asalto + personalizado (reserva=1 · fill=1.0)
MARCHAS: dict[str, dict[str, Any]] = {
    "asalto": {
        "titulo": "Asalto Inmediato",
        "reserva_pasos": 1,
        "umbral_fees_mult": 0.0,
        "permite_urgencia": False,
        "force_market": True,
        "fill_ratio": 1.0,
    },
    "personalizado": {
        "titulo": "Marcha Personalizada",
        "reserva_pasos": 1,
        "umbral_fees_mult": -1.0,
        "permite_urgencia": False,
        "force_market": False,
        "fill_ratio": 1.0,
    },
}

# Lista canónica para altar / panel / ETA (Monarca no ve legado)
MARCHAS_UI: tuple[str, ...] = ("asalto", "personalizado")

MARCHA_DEFAULT: MarchaId = "asalto"

# Legado: tactico / marcha_forzada → asalto (JSONs viejos, ETA, CLI)
_MARCHA_ALIASES: dict[str, str] = {
    "táctico": "asalto",
    "tactico": "asalto",
    "forzada": "asalto",
    "marcha_forzada": "asalto",
    "asalto": "asalto",
    "inmediato": "asalto",
    "personalizado": "personalizado",
    "custom": "personalizado",
    "duracion": "personalizado",
    "duración": "personalizado",
}


def director_activo() -> bool:
    return bool(getattr(config, "PASE_DIRECTOR_ACTIVO", True))


def _ruta_base() -> str:
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _ruta_marcha() -> str:
    return os.path.join(_ruta_base(), "data", "marcha_despliegue.json")


def _ruta_progreso() -> str:
    """Libro canónico del pase — solo campo de guerra mainnet."""
    return os.path.join(_ruta_base(), "data", "pase_progreso.json")


def _progreso_forzar_escritura() -> bool:
    """Escape para smokes/fríos que tocan el archivo sin Bybit."""
    return str(os.getenv("PASE_PROGRESO_FORCE_WRITE", "")).lower() in (
        "1",
        "true",
        "yes",
    )


def es_mainnet_pase() -> bool:
    """True en cuenta de guerra real (no sim). Mundo A DEMO no cuenta."""
    if _progreso_forzar_escritura():
        return True
    if bool(getattr(config, "MODO_SIMULACION", True)):
        return False
    if bool(getattr(config, "ARISE_IGRIS_SIM", False)):
        return False
    if bool(getattr(config, "ARENA_IGRIS_ACTIVA", False)):
        return False
    return True


def normalizar_marcha(mid: str | None) -> MarchaId:
    raw = (mid or "").strip().lower()
    m = _MARCHA_ALIASES.get(raw, raw)
    # Mega-cirugía Igris: solo Asalto gobierna el Escudo
    if bool(getattr(config, "IGRIS_SOLO_ASALTO", True)):
        if m == "personalizado":
            return "asalto"
        # cualquier desconocido → asalto
    if m in MARCHAS:
        if bool(getattr(config, "IGRIS_SOLO_ASALTO", True)) and m != "asalto":
            return "asalto"
        return m  # type: ignore[return-value]
    env = str(getattr(config, "MARCHA_DESPLIEGUE", MARCHA_DEFAULT) or MARCHA_DEFAULT).lower()
    env = _MARCHA_ALIASES.get(env, env)
    if bool(getattr(config, "IGRIS_SOLO_ASALTO", True)):
        return "asalto"
    if env in MARCHAS:
        return env  # type: ignore[return-value]
    return MARCHA_DEFAULT


def perfil_marcha(mid: str | None = None) -> dict[str, Any]:
    """Perfil activo: si mid es None, lee data/marcha_despliegue.json."""
    m = cargar_marcha() if mid is None else normalizar_marcha(mid)
    if bool(getattr(config, "IGRIS_SOLO_ASALTO", True)):
        m = "asalto"
    return {"id": m, **MARCHAS[m]}


def equity_desde_estado(estado: dict | None = None) -> float:
    """Lee equity vivo de estado_vivo (bóveda) o dict pasado."""
    data = estado
    if data is None:
        ruta = os.path.join(_ruta_base(), "data", "estado_vivo.json")
        if os.path.exists(ruta):
            try:
                with open(ruta, encoding="utf-8") as f:
                    data = json.load(f)
            except (json.JSONDecodeError, OSError, TypeError):
                data = {}
        else:
            data = {}
    if not isinstance(data, dict):
        return 0.0
    boveda = data.get("boveda") if isinstance(data.get("boveda"), dict) else {}
    for src in (boveda, data):
        for k in ("masa_bruta_real", "masa_bruta", "equity_usd", "equity"):
            try:
                v = float(src.get(k) or 0)
            except (TypeError, ValueError, AttributeError):
                v = 0.0
            if v > 0:
                return v
    return 0.0


def cargar_marcha_payload() -> dict[str, Any] | None:
    """Payload completo de data/marcha_despliegue.json (o None)."""
    ruta = _ruta_marcha()
    if not os.path.exists(ruta):
        return None
    try:
        with open(ruta, encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else None
    except (json.JSONDecodeError, OSError, TypeError):
        return None


def cargar_marcha() -> MarchaId:
    data = cargar_marcha_payload()
    if data:
        got = str(data.get("marcha_id") or data.get("id") or "").strip().lower()
        got = _MARCHA_ALIASES.get(got, got)
        if got in MARCHAS:
            return got  # type: ignore[return-value]
    return normalizar_marcha(None)


def guardar_marcha(
    marcha_id: str,
    *,
    duracion_dias: float | None = None,
    equity_usd: float | None = None,
) -> dict[str, Any]:
    """
    Persiste marcha activa. personalizado exige duracion_dias > 0
    y calibra umbrales vía marcha_duracion.calibrar_lote.
    """
    mid = normalizar_marcha(marcha_id)
    perfil = MARCHAS[mid]
    ruta = _ruta_marcha()
    os.makedirs(os.path.dirname(ruta), exist_ok=True)

    eq = float(equity_usd) if equity_usd is not None else equity_desde_estado()
    if eq <= 0:
        eq = float(getattr(config, "EQUITY_FALLBACK_USD", 1500) or 1500)

    payload: dict[str, Any] = {
        "marcha_id": mid,
        "titulo": perfil["titulo"],
        "ts": time.time(),
        "reserva_pasos": int(perfil["reserva_pasos"]),
        "umbral_fees_mult": float(perfil["umbral_fees_mult"]),
        "force_market": bool(perfil["force_market"]),
        "permite_urgencia": bool(perfil["permite_urgencia"]),
        "fill_ratio": float(perfil["fill_ratio"]),
        "equity_usd": round(eq, 4),
    }

    if mid == "personalizado":
        dias = float(duracion_dias) if duracion_dias is not None else 0.0
        if dias <= 0:
            raise ValueError("personalizado exige duracion_dias > 0")
        payload["duracion_dias"] = dias
        # Metas del lote abierto para calibrar
        plan = plan_lote(eq, marcha_id=mid, pasos_logrados=cargar_progreso()["pasos_logrados"])
        metas: dict[str, float] = {}
        for p in list(plan.get("trabajo") or []) or list(plan.get("lote") or []):
            act = str(p["activo"]).upper()
            metas[act] = metas.get(act, 0.0) + float(p.get("delta_usd") or 0)
        if not metas and plan.get("foco"):
            f = plan["foco"]
            metas[str(f["activo"]).upper()] = float(f.get("delta_usd") or 0)
        from core import marcha_duracion as mdur

        cal = mdur.calibrar_lote(metas, dias, eq)
        payload["umbrales_calibrados"] = bool(cal.get("por_base"))
        payload["calibrado_ts"] = cal.get("calibrado_ts")
    elif duracion_dias is not None:
        payload["duracion_dias"] = float(duracion_dias)

    tmp = ruta + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    if os.path.exists(ruta):
        os.remove(ruta)
    os.rename(tmp, ruta)
    return payload


def cargar_progreso() -> dict[str, Any]:
    """Lee pasos logrados del libro mainnet. En testnet/demo → vacío (no hereda demo)."""
    vacio: dict[str, Any] = {
        "pasos_logrados": [],
        "pasos_forzados": [],
        "ts": 0,
        "red": "mainnet",
    }
    if not es_mainnet_pase():
        return vacio
    ruta = _ruta_progreso()
    if not os.path.exists(ruta):
        return vacio
    try:
        with open(ruta, encoding="utf-8") as f:
            data = json.load(f)
        # Defensa: si alguien etiquetó testnet, ignorar
        if str(data.get("red") or "mainnet").lower() == "testnet":
            return vacio
        logs = [int(x) for x in (data.get("pasos_logrados") or []) if int(x) >= 1]
        forz = [int(x) for x in (data.get("pasos_forzados") or []) if int(x) >= 1]
        return {
            "pasos_logrados": sorted(set(logs) | set(forz)),
            "pasos_forzados": sorted(set(forz)),
            "ts": float(data.get("ts") or 0),
            "red": "mainnet",
            "nota_forzados": data.get("nota_forzados"),
        }
    except (json.JSONDecodeError, OSError, TypeError, ValueError):
        return vacio


def guardar_progreso(
    pasos_logrados: list[int],
    *,
    pasos_forzados: list[int] | None = None,
    nota_forzados: str | None = None,
) -> dict[str, Any]:
    """Persiste solo en mainnet. Testnet/demo no toca el libro de guerra.

    Si pasos_forzados es None, preserva los forzados ya en disco.
    """
    prev = {}
    ruta = _ruta_progreso()
    if os.path.exists(ruta):
        try:
            with open(ruta, encoding="utf-8") as f:
                prev = json.load(f) or {}
        except (json.JSONDecodeError, OSError, TypeError):
            prev = {}
    if pasos_forzados is None:
        forz = [int(x) for x in (prev.get("pasos_forzados") or []) if int(x) >= 1]
    else:
        forz = [int(x) for x in pasos_forzados if int(x) >= 1]
    logs = sorted({int(x) for x in pasos_logrados if int(x) >= 1} | set(forz))
    nota = nota_forzados
    if nota is None:
        nota = prev.get("nota_forzados")
    payload: dict[str, Any] = {
        "pasos_logrados": logs,
        "pasos_forzados": sorted(set(forz)),
        "ts": time.time(),
        "red": "mainnet",
    }
    if nota:
        payload["nota_forzados"] = nota
    if not es_mainnet_pase():
        return payload
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    tmp = ruta + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
        f.write("\n")
    if os.path.exists(ruta):
        os.remove(ruta)
    os.rename(tmp, ruta)
    return payload


def marcar_paso_logrado(n: int) -> dict[str, Any]:
    if not es_mainnet_pase():
        # Demo: no sellar el libro; reportar solo en memoria
        return {
            "pasos_logrados": [],
            "ts": time.time(),
            "red": "testnet",
            "omitido": "testnet_no_escribe_progreso",
        }
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


def need_acum_activo_hasta_paso(activo: str, paso_n: int) -> float:
    """Suma de *capital* (delta_usd) del mismo activo hasta el paso N (inclusive).

    Sirve a potencia/equity del ranking. Igris NO planta con este número:
    usa need_notional_grado_usd (tamaño real L+S del grado).
    """
    act = str(activo or "").upper()
    pn = int(paso_n)
    total = 0.0
    for p in PASE_PASOS:
        if int(p["n"]) > pn:
            break
        if str(p["activo"]).upper() == act:
            total += float(p["delta_usd"])
    return total


def need_notional_grado_usd(activo: str, grado: str) -> float:
    """Meta nocional L+S del manto para (activo, grado) — peaje ÷ fricción × 2."""
    from core import beru_capital as bc

    return float(bc.notional_manto_ls_grado(activo, grado))


def need_notional_por_pierna_usd(activo: str, grado: str) -> float:
    """Meta nocional de una pierna (L o S) para el grado."""
    from core import beru_capital as bc

    return float(bc.notional_por_pierna_grado(activo, grado))


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
        need = max(need_notional_grado_usd(act, str(p.get("grado") or "SOLDADO")), 1.0)
        have = notional_manto_usd(tusk, act)
        ratio = have / need
        if ratio < best_ratio:
            best_ratio = ratio
            best = p
    return str(best["activo"]).upper()


def meta_engorde_usd(
    equity_usd: float,
    activo: str | None = None,
    *,
    tusk=None,
    marcha_id: str | None = None,
    pasos_logrados: list[int] | None = None,
) -> dict[str, Any]:
    """
    Meta de engorde del paso en trabajo.

    Capas:
    - capital (delta_usd / need_capital_*): ranking de equity / potencia.
    - nocional (need_usd / restante_usd): tamaño real L+S del *grado* en foco.
      Igris planta con restante_usd (p.ej. ETH Soldado ~1250 L+S → ~625/pierna).

    Si restante ≤ 0 → Igris no engorda más ese foco (solo ventana/corrección).
    """
    plan = plan_lote(equity_usd, marcha_id=marcha_id, pasos_logrados=pasos_logrados)
    trabajo = list(plan.get("trabajo") or [])
    _vacio = {
        "ok": False,
        "motivo": "sin_trabajo",
        "activo": (activo or "").upper() or None,
        "need_usd": 0.0,
        "need_fill_usd": 0.0,
        "have_usd": 0.0,
        "restante_usd": 0.0,
        "need_capital_usd": 0.0,
        "need_notional_pierna_usd": 0.0,
        "paso_n": None,
        "delta_paso_usd": 0.0,
        "mitad_alcanzada": False,
        "fill_ratio": float(plan.get("fill_ratio") or 1.0),
    }
    if not trabajo:
        return _vacio

    act = (activo or "").upper()
    if act:
        candidatos = [p for p in trabajo if str(p["activo"]).upper() == act]
        if not candidatos:
            have = notional_manto_usd(tusk, act) if tusk is not None else 0.0
            out = dict(_vacio)
            out.update({
                "motivo": "activo_fuera_trabajo",
                "activo": act,
                "have_usd": round(have, 4),
            })
            return out
        paso = candidatos[0]
    else:
        if tusk is not None and len(trabajo) > 1:
            act = activo_manto_foco(
                equity_usd, marcha_id=marcha_id, pasos_logrados=pasos_logrados, tusk=tusk,
            )
            paso = next(p for p in trabajo if str(p["activo"]).upper() == act)
        else:
            paso = trabajo[0]
            act = str(paso["activo"]).upper()

    fill = float(plan.get("fill_ratio") or 1.0)
    grado = str(paso.get("grado") or "SOLDADO").upper()
    delta_paso = float(paso["delta_usd"])
    need_capital = need_acum_activo_hasta_paso(act, int(paso["n"]))
    need = need_notional_grado_usd(act, grado)
    pierna = need_notional_por_pierna_usd(act, grado)
    need_fill = need * fill
    have = notional_manto_usd(tusk, act) if tusk is not None else 0.0
    # Candado frío ranking: si already have > meta del grado → no proyectar engorde.
    overshoot = have > need_fill + 1e-9
    restante = 0.0 if overshoot else max(0.0, need_fill - have)
    return {
        "ok": True,
        "motivo": "OVERSHOOT_RANKING" if overshoot else "ok",
        "activo": act,
        "need_usd": round(need, 4),
        "need_fill_usd": round(need_fill, 4),
        "have_usd": round(have, 4),
        "restante_usd": round(restante, 4),
        "need_capital_usd": round(need_capital, 4),
        "need_notional_pierna_usd": round(pierna, 4),
        "paso_n": int(paso["n"]),
        "grado": grado,
        "delta_paso_usd": round(delta_paso, 4),
        "mitad_alcanzada": have + 1e-9 >= need_fill * 0.5,
        "fill_ratio": fill,
        "marcha_id": plan.get("marcha_id"),
        "meta_llena": restante <= 1e-9,
        "overshoot_ranking": overshoot,
        "telemetria": "OVERSHOOT_RANKING" if overshoot else None,
    }


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
    base: str | None = None,
) -> dict[str, Any]:
    """
    Asalto: umbral 0 + market (despliegue rápido; peaje aceptado).
    Personalizado: umbral_activo de marcha_duracion (calib ~T).
    Legado tactico/forzada llega aquí ya normalizado a asalto.
    """
    mid = cargar_marcha() if marcha_id is None else normalizar_marcha(marcha_id)
    perfil = MARCHAS[mid]
    fees = max(0.0, float(fees_be_pct))
    mult = float(perfil["umbral_fees_mult"])

    if mid == "personalizado":
        from core import marcha_duracion as mdur

        ua = mdur.umbral_activo(base or "", reajustar=True) if base else {
            "umbral_pct": 0.0, "ok": False, "modo": "personalizado",
        }
        return {
            "umbral_pct": round(float(ua.get("umbral_pct") or 0.0), 6),
            "fees_be_pct": round(fees, 6),
            "factor": 0.0,
            "modo_paciencia": "marcha_personalizado",
            "marcha_id": mid,
            "force_market": False,
            "piso_fees_mult": mult,
            "duracion_dias": ua.get("duracion_dias"),
        }

    # asalto (único resto operativo) o mult≤0
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

    piso = fees * mult
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

    from core import igris_despliegue as ides
    urg = ides.umbral_urgencia_pct(
        fees, float(t0_paciencia), perfil_edge=perfil_edge, ahora=ahora, base=base,
    )
    umbral_dyn = float(urg.get("umbral_pct") or fees)
    umbral = max(piso, umbral_dyn) if piso > 0 else umbral_dyn
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


def usd_piernas_manto_activo(tusk, activo: str) -> tuple[float, float]:
    """(USD long, USD short) del manto §E del Santo; excluye short inverso legado.

    Unidades: inverso = size (cara USD); lineal = qty×entrada.
    Portado de Jess (campo 2026-08-12) — alimenta bocado / ranking.
    """
    try:
        from core import igris_manto as im
        from core import lote_bybit as lote
        from core import mnt_manto_hedge as mmh

        fl, fs = im.frentes_bootstrap(activo)
    except Exception:
        return 0.0, 0.0
    act = str(activo or "").upper()
    pesos = getattr(tusk, "pesos", None) or {}
    usd_l = 0.0
    usd_s = 0.0
    for frente, lado in ((fl, "long"), (fs, "short"), (fl, "short"), (fs, "long")):
        if not mmh.lado_cuenta_como_manto(act, frente, lado):
            continue
        p = pesos.get(frente) or {}
        masa = float(p.get(lado) or 0)
        if masa <= 0:
            continue
        key = "precio_medio_long" if lado == "long" else "precio_medio_short"
        px = float(p.get(key) or 0)
        if px <= 0:
            px = float(p.get("precio_medio_long") or p.get("precio_medio_short") or 0)
        fu = str(frente or "").upper()
        try:
            filt = lote.filtros_lote(frente)
            usd = float(lote.qty_a_usd(abs(masa), px if px > 0 else 1.0, filt))
        except Exception:
            if "INVERSE" in fu or (
                hasattr(lote, "clave_mercado_desde_frente")
                and lote.clave_mercado_desde_frente(frente) == "inverse"
            ):
                usd = abs(masa)
            elif px > 0:
                usd = abs(masa) * px
            else:
                usd = abs(masa)
        if lado == "long":
            usd_l += usd
        else:
            usd_s += usd
    return usd_l, usd_s


def notional_manto_usd(tusk, activo: str) -> float:
    """USD desplegados del *manto de ranking* L+S.

    MNT inverso short = legado sucio → no suma al have.
    MNT inverso long + lineal short = manto Santo.
    """
    usd_l, usd_s = usd_piernas_manto_activo(tusk, activo)
    return float(usd_l) + float(usd_s)


def sincronizar_logrados_desde_tusk(
    tusk,
    equity_usd: float,
    *,
    marcha_id: str | None = None,
) -> dict[str, Any]:
    """Marca pasos logrados si el manto cubre el nocional del *grado* (fill_ratio).

    Compara have (nocional L+S) vs meta del grado — no vs capital delta_usd.
    Soldado ETH ~1250 L+S; Capitán ~2500; etc. (peaje ÷ fricción × 2).

    Dentro del lote paralelo (≤ lote_techo): cada Santo se marca por su cobertura,
    sin cola forzada 1→2→3. En la cola fina (pasos de reserva): sigue el orden.

    Solo persiste en mainnet. En testnet/demo calcula en memoria y no toca el libro.
    """
    mid = normalizar_marcha(marcha_id or cargar_marcha())
    fill = float(MARCHAS[mid]["fill_ratio"])
    n_pot = potencia_n(equity_usd)
    reserva = int(MARCHAS[mid]["reserva_pasos"])
    n_lote_techo = max(0, n_pot - reserva) if n_pot > 0 else 0
    prog = cargar_progreso()
    forzados = set(int(x) for x in (prog.get("pasos_forzados") or []))
    logs = set(int(x) for x in (prog.get("pasos_logrados") or [])) | set(forzados)
    desplegado: dict[str, float] = {}
    changed = False
    puede_escribir = es_mainnet_pase()

    for p in PASE_PASOS:
        pn = int(p["n"])
        # Encima de potencia: solo procesa sellos Monarca (forzados); no engorda cola.
        if pn > n_pot and pn not in forzados:
            continue
        act = str(p["activo"]).upper()
        if act not in desplegado:
            desplegado[act] = notional_manto_usd(tusk, act)
        need = need_notional_grado_usd(act, str(p.get("grado") or "SOLDADO"))
        have = float(desplegado.get(act, 0.0))
        # Sello Monarca (pasos_forzados): no auto-desmarcar aunque have < need / potencia.
        if pn in forzados:
            if pn not in logs:
                logs.add(pn)
                changed = True
            continue
        # Desmarca sello falso solo si el Santo tiene masa en Tusk y no cubre meta
        # (nocional inflado corregido, o bóveda MNT contada como manto). No borra
        # la cadena de otros Santos sin posiciones (cola del lote).
        if pn in logs and have + 1e-6 < need * fill:
            tiene_masa = False
            try:
                from core import igris_manto as im

                fl0, fs0 = im.frentes_bootstrap(act)
                for fr in (fl0, fs0):
                    row = (getattr(tusk, "pesos", None) or {}).get(fr) or {}
                    if float(row.get("long") or 0) > 0 or float(row.get("short") or 0) > 0:
                        tiene_masa = True
                        break
            except Exception:
                tiene_masa = have > 0
            if tiene_masa or have > 0:
                logs.discard(pn)
                changed = True
            continue
        if pn in logs:
            continue
        if pn > n_pot:
            continue
        # Lote paralelo: sin cadena forzada. Cola fina: paso anterior obligatorio.
        if pn > n_lote_techo and pn > 1 and (pn - 1) not in logs:
            continue
        if have + 1e-6 >= need * fill:
            logs.add(pn)
            changed = True

    # Reafirma forzados (p.ej. OP Cap/Gen por encima de potencia de cuenta)
    if forzados - logs:
        logs |= forzados
        changed = True

    if changed and puede_escribir:
        guardar_progreso(sorted(logs))
    return plan_lote(equity_usd, marcha_id=mid, pasos_logrados=sorted(logs))


def marcar_foco_si_bloque_completo(
    equity_usd: float,
    activo: str,
    *,
    marcha_id: str | None = None,
    tusk=None,
) -> dict[str, Any] | None:
    """Tras bloque Igris: solo sella si el nocional del grado ya cubre la meta (vía sync)."""
    if not es_mainnet_pase():
        return None
    if tusk is None:
        return None
    _ = activo  # sync revisa cobertura real de todos los Santos en potencia
    return sincronizar_logrados_desde_tusk(tusk, equity_usd, marcha_id=marcha_id)

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
