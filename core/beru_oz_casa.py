"""Última Oz de la casa: fill spot cobrado, no polvo ni Stop cancelado."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / "data" / "beru" / "ultima_oz_spot.json"
CRONICAS = ROOT / "data" / "beru" / "cronicas"


def piso_ts_cronica(activo: str) -> float:
    """Última cosecha anotada del General: el polvo viejo queda debajo."""
    path = CRONICAS / f"{str(activo or '').upper()}.jsonl"
    if not path.exists():
        return 0.0
    ultimo = 0.0
    try:
        with path.open(encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    ev = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if str(ev.get("tipo") or "").upper() != "COSECHA":
                    continue
                ultimo = max(ultimo, float(ev.get("ts") or 0))
    except OSError:
        return 0.0
    return ultimo


def cargar_snapshot() -> dict[str, dict]:
    if not SNAPSHOT.exists():
        return {}
    try:
        raw = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    fills = raw.get("fills") if isinstance(raw, dict) else raw
    if not isinstance(fills, dict):
        return {}
    out: dict[str, dict] = {}
    for k, v in fills.items():
        if isinstance(v, dict):
            out[str(k).upper()] = dict(v)
    return out


def guardar_snapshot(fills: dict[str, dict], *, via: str = "") -> None:
    SNAPSHOT.parent.mkdir(parents=True, exist_ok=True)
    import time

    payload = {
        "ts_escrito": time.time(),
        "via": via,
        "fills": {str(k).upper(): v for k, v in fills.items()},
    }
    SNAPSHOT.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _fill_cobrado(orden: dict) -> dict | None:
    status = str(orden.get("orderStatus") or "")
    try:
        qty = float(orden.get("cumExecQty") or 0)
    except (TypeError, ValueError):
        qty = 0.0
    if status != "Filled" and not (qty > 0 and status in {"Filled", "PartiallyFilledCanceled"}):
        return None
    if qty <= 0:
        return None
    create = str(orden.get("createType") or orden.get("placeType") or "")
    if "CONVERT" in create.upper():
        return None
    try:
        px = float(orden.get("avgPrice") or orden.get("price") or 0)
    except (TypeError, ValueError):
        px = 0.0
    if px <= 0:
        return None
    try:
        ts_raw = float(orden.get("updatedTime") or orden.get("createdTime") or 0)
    except (TypeError, ValueError):
        ts_raw = 0.0
    ts = ts_raw / 1000.0 if ts_raw > 1e12 else ts_raw
    return {
        "side": str(orden.get("side") or ""),
        "precio": px,
        "qty": qty,
        "ts": ts,
        "order_id": str(orden.get("orderId") or ""),
        "create_type": create,
        "order_type": str(orden.get("orderType") or ""),
        "via": "spot_history",
    }


def leer_fills_spot_casa(activos: list[str]) -> dict[str, dict]:
    """Lectura de historial spot. No planta ni cancela. None si no hay sesión."""
    import core.config as config
    from pybit.unified_trading import HTTP

    if not (getattr(config, "API_KEY", "") and getattr(config, "API_SECRET", "")):
        return {}
    session = HTTP(
        testnet=False,
        api_key=config.API_KEY,
        api_secret=config.API_SECRET,
        recv_window=60000,
    )
    out: dict[str, dict] = {}
    for act in activos:
        u = str(act or "").upper()
        if not u:
            continue
        piso = piso_ts_cronica(u)
        try:
            r = session.get_order_history(
                category="spot",
                symbol=f"{u}USDT",
                limit=50,
            )
        except Exception:
            continue
        if r.get("retCode") != 0:
            continue
        elegido = None
        for orden in (r.get("result") or {}).get("list") or []:
            hit = _fill_cobrado(orden)
            if not hit:
                continue
            if piso > 0 and float(hit["ts"] or 0) <= piso:
                continue
            if elegido is None or float(hit["ts"] or 0) > float(elegido["ts"] or 0):
                elegido = hit
        if elegido:
            elegido["piso_ts"] = piso
            out[u] = elegido
        else:
            out[u] = {"precio": 0.0, "piso_ts": piso, "via": "sin_fill_posterior"}
    return out


def fills_para_preparar(activos: list[str]) -> dict[str, dict]:
    """Snapshot si existe; si no, vacío (la caza huérfana igual se desarma)."""
    snap = cargar_snapshot()
    if not snap:
        return {}
    out: dict[str, dict] = {}
    for act in activos:
        u = str(act or "").upper()
        if u in snap:
            row = dict(snap[u])
            if "piso_ts" not in row:
                row["piso_ts"] = piso_ts_cronica(u)
            out[u] = row
    return out


def simular_legion_foto(
    items: list[dict],
    fills: dict[str, dict],
) -> list[dict]:
    """Clona barcos de foto, aplica Oz de casa, devuelve geometría antes/después."""
    from core.models import BeruShip
    from core import beru_continuo as bc
    from generales.capitanes import CapitanNormal

    filas = []
    legion: list[Any] = []
    for item in items:
        b = BeruShip(
            uid=str(item.get("uid") or "BERU_SEM_X"),
            centro_local=float(item.get("centro_local") or 0),
            centro_manto=float(item.get("centro_manto") or 0),
            ancla_tramo=float(item.get("ancla_tramo") or item.get("centro_local") or 0),
            masa=float(item.get("masa") or 0),
            direccion=str(item.get("direccion") or "LONG"),
            estado=str(item.get("estado") or "ACECHANDO"),
            oz_adan=float(item.get("oz_adan") or 0),
            red_adan=float(item.get("red_adan") or 0),
            frente_asignado=str(item.get("frente_asignado") or ""),
            tier_id=str(item.get("tier_id") or ""),
            modo_combate="CAZA",
            ultima_hoz_tocada_precio=float(item.get("ultima_hoz_tocada_precio") or 0),
            ultima_hoz_tocada_pct=float(item.get("ultima_hoz_tocada_pct") or 0),
            ultima_red_tocada_precio=float(item.get("ultima_red_tocada_precio") or 0),
            ultima_red_tocada_pct=float(item.get("ultima_red_tocada_pct") or 0),
            es_relevo_cazador=bool(item.get("es_relevo_cazador")),
            altar_link_id=str(item.get("altar_link_id") or ""),
            adn_capitan=CapitanNormal,
            ts_wake=float(item.get("ts_wake") or 0),
        )
        act = bc.activo_de_barco(b)
        antes = {
            "activo": act,
            "estado": b.estado,
            "dir": b.direccion,
            "masa": b.masa,
            "oz": b.oz_adan,
            "hoz": b.ultima_hoz_tocada_precio,
            "dual": bc.sangre_dual(b),
            "altar": b.altar_link_id,
        }
        legion.append(b)
        filas.append({"antes": antes, "barco": b})
    informe = bc.preparar_legion_tras_manos_casa(legion, fills)
    out = []
    for fila, b in zip(filas, legion):
        act = fila["antes"]["activo"]
        sangre = bc.precio_sangre_contraria(b) if not bc.sangre_dual(b) else 0.0
        red = bc.precio_oreja_red(b)
        out.append({
            "activo": act,
            "veredicto": informe.get(act, ""),
            "antes": fila["antes"],
            "despues": {
                "estado": b.estado,
                "dir": b.direccion,
                "masa": b.masa,
                "oz": b.oz_adan,
                "hoz": b.ultima_hoz_tocada_precio,
                "dual": bc.sangre_dual(b),
                "relevo": bool(b.es_relevo_cazador),
                "sangre": sangre,
                "red": red,
                "altar": b.altar_link_id,
            },
        })
    return out
