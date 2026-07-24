"""Beru — Sub-Santuario por activo (flota + ficha + red engorde).

Espejo doctrinal de `igris_asset_detail`: lista por moneda → detalle de legión.
Solo lectura. PnL estimado vs centro 0 (doctrina provisional).
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import core.config as config
from core import beru_cazador
from core import beru_rail

ROOT = Path(__file__).resolve().parents[1]
CRONICA_DIR = ROOT / "data" / "beru" / "cronicas"


def _modo_caza(b: Any) -> str:
    if getattr(b, "ciclo_infinito", False):
        return "CICLO_INFINITO"
    if getattr(b, "neg_post_cazador", False):
        return "NEGOCIADOR"
    est = str(getattr(b, "estado", "") or "")
    if est in ("ACECHANDO",):
        return "ACECHANDO"
    if est in ("ESPERANDO_CONDICIONAL",):
        return "NEGOCIADOR"
    if est in ("NEGOCIANDO", "ESPERANDO_MATERIALIZACION", "ESPERANDO_ABISMO"):
        # Negociando puede ser caza o neg
        if getattr(b, "neg_post_cazador", False) or getattr(b, "ciclo_infinito", False):
            return "NEGOCIADOR"
        return "CAZA"
    if est == "FUSIONADO":
        return "FUSIONADO"
    return est or "OTRO"


def _activo_de_uid(uid: str, fallback: str = "") -> str:
    u = str(uid or "")
    # BERU_SEM_ETH_… · BERU_CAPA2_SOL_…
    parts = u.split("_")
    for i, p in enumerate(parts):
        if p in ("SEM", "CAPA1", "CAPA2", "CAPA3", "CAPA4", "CAPA5") and i + 1 < len(parts):
            cand = parts[i + 1]
            if cand.isalpha() and len(cand) <= 12:
                return cand.upper()
        if p.startswith("CAPA") and i + 1 < len(parts):
            cand = parts[i + 1]
            if cand.isalpha() and len(cand) <= 12:
                return cand.upper()
    # frente_asignado ETHUSDT_SPOT
    return (fallback or "").upper()


def activo_de_legionario(b: Any, semilla: str = "") -> str:
    """Activo (ETH, BTC…) de un barco Beru — público para crónica / panel."""
    return _activo_barco(b, semilla)


def _activo_barco(b: Any, semilla: str = "") -> str:
    frente = str(getattr(b, "frente_asignado", "") or "")
    if frente and frente != "INDEFINIDO":
        for q in ("USDT", "USDC", "USDE", "USD1"):
            if frente.upper().endswith(f"{q}_SPOT"):
                return frente.upper().replace(f"{q}_SPOT", "")
            if f"{q}_SPOT" in frente.upper():
                base = frente.upper().split(f"{q}_SPOT")[0]
                if base:
                    return base
    uid_act = _activo_de_uid(getattr(b, "uid", ""), semilla)
    if uid_act:
        return uid_act
    return (semilla or beru_rail.activo_semilla()).upper()


def _quote_de_frente(frente: str) -> str | None:
    f = (frente or "").upper()
    for q in ("USDT", "USDC", "USDE", "USD1"):
        if f.endswith(f"{q}_SPOT") or f"{q}_SPOT" in f:
            return q
    return None


def _pct_desde_centro(centro: float, precio: float) -> float | None:
    if centro <= 0 or precio <= 0:
        return None
    return round((precio - centro) / centro * 100.0, 4)


def _es_caza_activa(b: Any) -> bool:
    return _modo_caza(b) == "CAZA"


def _es_negociando(b: Any) -> bool:
    m = _modo_caza(b)
    return m in ("NEGOCIADOR", "CICLO_INFINITO") or (
        str(getattr(b, "estado", "")) == "ESPERANDO_CONDICIONAL"
    )


def red_engorde_de_legion(legion: list[Any], activo: str) -> dict[str, Any] | None:
    """Red que permite engordar (frontera) para el activo."""
    ships = [b for b in legion if _activo_barco(b) == activo.upper()]
    if not ships:
        return None

    def modo_fn(b):
        return "CAZA" if _es_caza_activa(b) else "NEGOCIADOR"

    candidatos = [
        b for b in ships
        if str(getattr(b, "estado", "")) == "NEGOCIANDO"
        and _es_caza_activa(b)
        and not getattr(b, "ciclo_infinito", False)
        and float(getattr(b, "red_adan", 0) or 0) > 0
    ]
    if not candidatos:
        # Fallback: cualquier caza con red
        candidatos = [
            b for b in ships
            if _es_caza_activa(b) and float(getattr(b, "red_adan", 0) or 0) > 0
        ]
    frontera = None
    for b in candidatos:
        if beru_cazador.es_frontera_red(b, ships, modo_fn):
            frontera = b
            break
    if frontera is None and candidatos:
        # LONG: red más baja; SHORT: más alta
        longs = [b for b in candidatos if getattr(b, "direccion", "LONG") == "LONG"]
        shorts = [b for b in candidatos if getattr(b, "direccion", "") == "SHORT"]
        if longs:
            frontera = min(longs, key=lambda x: float(x.red_adan))
        elif shorts:
            frontera = max(shorts, key=lambda x: float(x.red_adan))

    if frontera is None:
        return None
    centro = float(getattr(frontera, "centro_manto", 0) or getattr(frontera, "centro_local", 0) or 0)
    red_p = float(getattr(frontera, "red_adan", 0) or 0)
    red_pct = float(getattr(frontera, "red_pct", 0) or 0)
    return {
        "uid": getattr(frontera, "uid", ""),
        "precio": red_p,
        "pct_vs_centro": _pct_desde_centro(centro, red_p) if red_p > 0 else (
            round(red_pct * 100.0, 4) if red_pct else None
        ),
        "direccion": getattr(frontera, "direccion", "LONG"),
        "centro_0": centro,
        "nota": "Solo esta red de frontera puede engordar (+$5 / 0.1%).",
    }


def _barco_fila(b: Any, activo: str, precio_mark: float = 0.0) -> dict[str, Any]:
    centro = float(getattr(b, "centro_manto", 0) or getattr(b, "centro_local", 0) or 0)
    oz = float(getattr(b, "oz_adan", 0) or 0)
    red = float(getattr(b, "red_adan", 0) or 0)
    masa = float(getattr(b, "masa", 0) or getattr(b, "masa_congelada", 0) or 0)
    entrada = float(getattr(b, "precio_entrada_real", 0) or 0)
    mark = precio_mark or entrada or centro
    # PnL provisional: LONG (mark-entry)/entry * masa; SHORT inverso
    pnl = None
    if entrada > 0 and mark > 0 and masa > 0:
        dir_ = str(getattr(b, "direccion", "LONG") or "LONG").upper()
        ret = (mark - entrada) / entrada
        if dir_ == "SHORT":
            ret = -ret
        pnl = round(ret * masa, 4)

    frente = str(getattr(b, "frente_asignado", "") or "")
    return {
        "uid": getattr(b, "uid", ""),
        "estado": getattr(b, "estado", ""),
        "modo": _modo_caza(b),
        "direccion": getattr(b, "direccion", "LONG"),
        "masa": round(masa, 6),
        "centro_0": centro,
        "centro_local": float(getattr(b, "centro_local", 0) or 0),
        "oz_precio": oz,
        "oz_pct": round(float(getattr(b, "oz_pct", 0) or 0) * 100.0, 4),
        "red_precio": red,
        "red_pct": round(float(getattr(b, "red_pct", 0) or 0) * 100.0, 4),
        "oz_vs_centro_pct": _pct_desde_centro(centro, oz),
        "red_vs_centro_pct": _pct_desde_centro(centro, red),
        "tier_id": getattr(b, "tier_id", "") or "",
        "modo_combate": getattr(b, "modo_combate", "") or "",
        "capa": int(getattr(b, "capa", 1) or 1),
        "generacion": int(getattr(b, "generacion", 1) or 1),
        "es_super": bool(getattr(b, "es_super_beru", False)),
        "ciclo_infinito": bool(getattr(b, "ciclo_infinito", False)),
        "neg_toques_ciclo": int(getattr(b, "neg_toques_ciclo", 0) or 0),
        "ancla_cosecha_pct": round(float(getattr(b, "ancla_cosecha_pct", 0) or 0) * 100.0, 4),
        "frente": frente if frente != "INDEFINIDO" else None,
        "rail_quote": _quote_de_frente(frente),
        "precio_entrada": entrada or None,
        "precio_salida": float(getattr(b, "precio_salida_real", 0) or 0) or None,
        "max_favor_pct": round(float(getattr(b, "max_favor", 0) or 0) * 100.0, 4),
        "pnl_est_usd": pnl,
        "fees_paid_usd": None,  # sin ledger aún — hueco preparado
    }


def _niveles_grafica(barcos: list[dict], red_engorde: dict | None, centro: float) -> dict[str, Any]:
    """Puntos para gráfica: centro, oz/red por barco, red engorde."""
    niveles = []
    if centro > 0:
        niveles.append({"id": "centro_0", "precio": centro, "pct": 0.0, "rol": "centro"})
    for b in barcos:
        if b.get("oz_precio"):
            niveles.append({
                "id": f"oz_{b['uid'][:12]}",
                "precio": b["oz_precio"],
                "pct": b.get("oz_vs_centro_pct"),
                "rol": "oz",
                "uid": b["uid"],
            })
        if b.get("red_precio"):
            niveles.append({
                "id": f"red_{b['uid'][:12]}",
                "precio": b["red_precio"],
                "pct": b.get("red_vs_centro_pct"),
                "rol": "red",
                "uid": b["uid"],
            })
    if red_engorde and red_engorde.get("precio"):
        niveles.append({
            "id": "red_engorde",
            "precio": red_engorde["precio"],
            "pct": red_engorde.get("pct_vs_centro"),
            "rol": "red_engorde",
            "uid": red_engorde.get("uid"),
        })
    return {"centro_0": centro, "niveles": niveles}


def _cargar_cronica(activo: str, limit: int = 40) -> list[dict[str, Any]]:
    path = CRONICA_DIR / f"{activo.upper()}.jsonl"
    if not path.is_file():
        return []
    rows: list[dict[str, Any]] = []
    try:
        for ln in path.read_text(encoding="utf-8").splitlines():
            if not ln.strip():
                continue
            rows.append(json.loads(ln))
    except (OSError, json.JSONDecodeError):
        return []
    return rows[-limit:]


def append_cronica(activo: str, evento: dict[str, Any]) -> None:
    """Append evento de ciclo (caza/cosecha/mega/reset). Llamar desde Beru/Bellion."""
    CRONICA_DIR.mkdir(parents=True, exist_ok=True)
    path = CRONICA_DIR / f"{(activo or 'UNK').upper()}.jsonl"
    row = {"ts": time.time(), "activo": (activo or "").upper(), **evento}
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
    # trim
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
        if len(lines) > 500:
            path.write_text("\n".join(lines[-400:]) + "\n", encoding="utf-8")
    except OSError:
        pass


def snapshot_activo(
    activo: str,
    legion: list[Any],
    *,
    precio_mark: float = 0.0,
    semilla: str | None = None,
) -> dict[str, Any]:
    act = (activo or "").upper()
    ships_raw = [b for b in (legion or []) if _activo_barco(b, semilla or "") == act]
    # Si no hay match por activo, y es la semilla, tomar toda la legión sin tag
    if not ships_raw and act == (semilla or beru_rail.activo_semilla()).upper():
        ships_raw = [
            b for b in (legion or [])
            if _activo_barco(b, semilla or "") in (act, "", (semilla or "").upper())
        ]

    barcos = [_barco_fila(b, act, precio_mark) for b in ships_raw]
    n_caza = sum(1 for x in barcos if x["modo"] == "CAZA")
    n_neg = sum(1 for x in barcos if x["modo"] in ("NEGOCIADOR", "CICLO_INFINITO"))
    n_acech = sum(1 for x in barcos if x["modo"] == "ACECHANDO")
    n_mega = sum(1 for x in barcos if x.get("es_super"))
    masa_total = round(sum(float(x.get("masa") or 0) for x in barcos), 6)
    pnl_sum = sum(float(x["pnl_est_usd"]) for x in barcos if x.get("pnl_est_usd") is not None)

    centros = [float(x["centro_0"]) for x in barcos if x.get("centro_0")]
    centro_0 = centros[0] if centros else 0.0
    # Preferir centro del Mega si existe
    for x in barcos:
        if x.get("es_super") and x.get("centro_0"):
            centro_0 = float(x["centro_0"])
            break

    red_eng = red_engorde_de_legion(ships_raw, act)
    rails = sorted({x["rail_quote"] for x in barcos if x.get("rail_quote")})
    frentes_casa = beru_rail.frentes_casa_estables(act)

    total = max(len(barcos), 1)
    return {
        "symbol": act,
        "fuente": "legion" if barcos else "cero",
        "n_barcos": len(barcos),
        "n_caza": n_caza,
        "n_negociando": n_neg,
        "n_acechando": n_acech,
        "n_mega": n_mega,
        "masa_total_usd": masa_total,
        "pnl_est_usd": round(pnl_sum, 4) if barcos else 0.0,
        "fees_paid_usd": None,
        "centro_0": centro_0,
        "composicion": {
            "caza": n_caza,
            "negociando": n_neg,
            "acechando": n_acech,
            "otros": max(0, len(barcos) - n_caza - n_neg - n_acech),
            "pct_caza": round(n_caza / total * 100.0, 1),
            "pct_negociando": round(n_neg / total * 100.0, 1),
        },
        "red_engorde": red_eng,
        "rails_vivos": rails,
        "rails_disponibles": [
            {"frente": f, "quote": _quote_de_frente(f)} for f in frentes_casa
        ],
        "barcos": barcos,
        "grafica": _niveles_grafica(barcos, red_eng, centro_0),
        "cronica": _cargar_cronica(act),
        "nota_pnl": (
            "PnL estimado = retorno vs precio_entrada × masa. "
            "Fees ledger aún no cableado (hueco preparado)."
        ),
    }


def snapshot_cero(activo: str) -> dict[str, Any]:
    act = (activo or "ETH").upper()
    return {
        "symbol": act,
        "fuente": "cero",
        "n_barcos": 0,
        "n_caza": 0,
        "n_negociando": 0,
        "n_acechando": 0,
        "n_mega": 0,
        "masa_total_usd": 0.0,
        "pnl_est_usd": 0.0,
        "fees_paid_usd": None,
        "centro_0": 0.0,
        "composicion": {
            "caza": 0, "negociando": 0, "acechando": 0, "otros": 0,
            "pct_caza": 0.0, "pct_negociando": 0.0,
        },
        "red_engorde": None,
        "rails_vivos": [],
        "rails_disponibles": [
            {"frente": f, "quote": _quote_de_frente(f)}
            for f in beru_rail.frentes_casa_estables(act)
        ],
        "barcos": [],
        "grafica": {"centro_0": 0.0, "niveles": []},
        "cronica": [],
        "nota_pnl": "Sin barcos — legión en reposo.",
    }


def flota_resumen(legion: list[Any], *, semilla: str | None = None) -> dict[str, Any]:
    """Lista por activo para panel / Pergamino."""
    sem = (semilla or beru_rail.activo_semilla()).upper()
    by_act: dict[str, list] = {}
    for b in legion or []:
        act = _activo_barco(b, sem) or sem
        by_act.setdefault(act, []).append(b)

    # Asegurar semilla en lista aunque vacía
    if sem not in by_act:
        by_act[sem] = []

    activos = []
    for act in sorted(by_act.keys()):
        snap = snapshot_activo(act, by_act[act], semilla=sem)
        activos.append({
            "activo": act,
            "n_barcos": snap["n_barcos"],
            "n_caza": snap["n_caza"],
            "n_negociando": snap["n_negociando"],
            "n_acechando": snap["n_acechando"],
            "n_mega": snap["n_mega"],
            "masa_total_usd": snap["masa_total_usd"],
            "pnl_est_usd": snap["pnl_est_usd"],
            "centro_0": snap["centro_0"],
            "composicion": snap["composicion"],
            "red_engorde_pct": (snap.get("red_engorde") or {}).get("pct_vs_centro"),
            "red_engorde_precio": (snap.get("red_engorde") or {}).get("precio"),
            "rails_vivos": snap["rails_vivos"],
            "es_semilla": act == sem,
        })

    return {
        "ts": time.time(),
        "semilla": sem,
        "n_activos": len(activos),
        "n_barcos_total": sum(a["n_barcos"] for a in activos),
        "activos": activos,
    }


def mapa_asset_details(
    legion: list[Any],
    *,
    precios: dict[str, float] | None = None,
    semilla: str | None = None,
) -> dict[str, dict[str, Any]]:
    """Mapa activo → ficha completa (para estado_vivo.beru_asset_details)."""
    sem = (semilla or beru_rail.activo_semilla()).upper()
    flota = flota_resumen(legion, semilla=sem)
    out: dict[str, dict[str, Any]] = {}
    precios = precios or {}
    by_act: dict[str, list] = {}
    for b in legion or []:
        act = _activo_barco(b, sem) or sem
        by_act.setdefault(act, []).append(b)
    for row in flota["activos"]:
        act = row["activo"]
        mark = float(precios.get(act) or precios.get(f"{act}USDT_SPOT") or 0)
        out[act] = snapshot_activo(act, by_act.get(act) or [], precio_mark=mark, semilla=sem)
    return out


def enriquecer_legion_resumen(legion: list[Any], semilla: str | None = None) -> list[dict[str, Any]]:
    """Filas ricas para estado_vivo.legion (compat + campos nuevos)."""
    sem = semilla or beru_rail.activo_semilla()
    out = []
    for b in legion or []:
        act = _activo_barco(b, sem)
        fila = _barco_fila(b, act)
        fila["activo"] = act
        fila["centro"] = fila["centro_0"] or fila["centro_local"]  # compat panel viejo
        fila["es_super"] = fila["es_super"]
        out.append(fila)
    return out
