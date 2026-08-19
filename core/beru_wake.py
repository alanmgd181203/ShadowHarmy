"""Beru wake — semilla cazadora continua.

El wake fija el 0 local con el precio del momento. El plantador hidrata el
metro (0 del manto) desde el promedio L+S de Igris. Capitán Normal / Vacío
de Adán 1,1 % · manos aparte (BERU_MANOS).
"""
from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any

import core.config as config
from core.models import BeruShip

ROOT = Path(__file__).resolve().parents[1]
WAKE_RITUAL = ROOT / "data" / "beru" / "wake_ritual.json"
_UID_SEMILLA_NS = re.compile(r"BERU_SEM_[A-Z0-9]+_(\d{16,})$")


def wake_reset_0_activo() -> bool:
    return False


def manos_beru_activas() -> bool:
    """Órdenes spot reales solo si BERU_MANOS=true (default OFF = cableado dormido)."""
    return bool(getattr(config, "BERU_MANOS", False))


def manos_fantasma_activas() -> bool:
    """Nivel 2: registra disparos sin place_order (BERU_MANOS_FANTASMA)."""
    return bool(getattr(config, "BERU_MANOS_FANTASMA", False))


def _lista_activos(raw: str) -> list[str]:
    out: list[str] = []
    for part in str(raw or "").split(","):
        u = part.strip().upper()
        if u and u not in out:
            out.append(u)
    return out


def activos_manos_reales() -> list[str]:
    """Santos con Hoz en Bybit. Vacío = ley global (todos o ninguno)."""
    return _lista_activos(getattr(config, "BERU_MANOS_ACTIVOS", "") or "")


def manos_reales_de_activo(activo: str) -> bool:
    """¿Este Santo planta carta real? El resto puede seguir en fantasma."""
    if not manos_beru_activas():
        return False
    act = str(activo or "").upper()
    if not act:
        return False
    listed = activos_manos_reales()
    if listed:
        return act in listed
    return not manos_fantasma_activas()


def tier_manos_exigido(activo: str) -> str | None:
    """Uniforme mínimo al nacer con manos reales. AUTO/vacío = el manto dicta."""
    act = str(activo or "").upper()
    if act not in activos_manos_reales():
        return None
    tid = str(getattr(config, "BERU_MANOS_EXIGIR_TIER", "") or "").upper().strip()
    if tid in ("", "NONE", "AUTO", "NO", "OFF"):
        return None
    return tid


def ensayo_nivel3_activo() -> bool:
    """Nivel 3: manos chiquitas reales con techos (BERU_ENSAYO_NIVEL3)."""
    return bool(getattr(config, "BERU_ENSAYO_NIVEL3", False))


def siembra_sin_candado_pase() -> bool:
    """Fantasma o ensayo nivel 3: Santos elegidos sin esperar sellos Igris."""
    return manos_fantasma_activas() or ensayo_nivel3_activo()


def siembra_flota_activa() -> bool:
    return bool(getattr(config, "BERU_SIEMBRA_FLOTA", True))


def adn_capitan_wake():
    """Wake fuerza Normal 1,1 % — no Ansiedad 1,2 %."""
    from generales.capitanes import CapitanAnsiedad, CapitanNormal

    modo = str(getattr(config, "BERU_CAPITAN_WAKE", "NORMAL") or "NORMAL").upper()
    if modo in ("ANSIEDAD", "ANXIETY", "1.2", "012"):
        return CapitanAnsiedad
    return CapitanNormal


def vacio_wake_pct() -> float:
    adn = adn_capitan_wake()
    return float(getattr(adn, "vacio_adan", 0.011) or 0.011)


def centros_al_wake(precio_actual: float) -> tuple[float, float]:
    """0 local = spot de wake; el manto lo rellena el plantador desde Tusk."""
    px = float(precio_actual or 0.0)
    if px <= 0:
        return 0.0, 0.0
    return px, 0.0


def catalogo_flota() -> list[str]:
    raw = getattr(config, "ACTIVOS_BERU_FLOTA", None) or []
    out: list[str] = []
    for a in raw:
        u = str(a or "").upper().strip()
        if u and u not in out:
            out.append(u)
    if not out:
        out = [str(getattr(config, "BERU_ACTIVO_SEMILLA", "ETH") or "ETH").upper()]
    return out


def _solo_con_manto(activos: list[str], tusk=None) -> list[str]:
    """Sin metro de Igris no se siembra."""
    if tusk is None:
        return list(activos)
    from core import beru_cazador as bc

    return [a for a in activos if bc.manto_vivo(tusk, a)]


def _leer_estado_vivo() -> dict[str, Any]:
    path = ROOT / "data" / "estado_vivo.json"
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, TypeError):
        return {}


def manto_en_foto_estado(activo: str, snap: dict[str, Any] | None = None) -> bool:
    """¿Esta tierra tiene metro en la última foto?"""
    act = str(activo or "").upper()
    if not act:
        return False
    data = snap if isinstance(snap, dict) else _leer_estado_vivo()
    if not data:
        return False
    for row in (data.get("beru_flota") or {}).get("activos") or []:
        if str(row.get("activo") or "").upper() != act:
            continue
        if float(row.get("centro_manto") or 0) > 0:
            return True
    det = (data.get("igris_asset_details") or {}).get(act) or {}
    long_usd = float((det.get("long") or {}).get("size_usd") or 0)
    short_usd = float((det.get("short") or {}).get("size_usd") or 0)
    return long_usd > 0 and short_usd > 0


def catalogo_ojos_desde_foto(
    candidatos: list[str] | None = None,
    *,
    snap: dict[str, Any] | None = None,
) -> list[str]:
    """Ojos Beru: Santos con manto o Beru vivo. El ticker de casa se queda.

    Tierras sin metro (BTC/APT/ETC en este arise) no ensucian el río.
    """
    cand = list(candidatos or catalogo_flota())
    data = snap if isinstance(snap, dict) else _leer_estado_vivo()
    ticker = str(
        getattr(config, "TICKER_BASE", "")
        or getattr(config, "BERU_ACTIVO_SEMILLA", "")
        or ""
    ).upper()
    vivos: set[str] = set()
    for row in (data.get("beru_flota") or {}).get("activos") or []:
        u = str(row.get("activo") or "").upper()
        if (
            u
            and float(row.get("centro_manto") or 0) > 0
            and int(row.get("n_barcos") or 0) > 0
        ):
            vivos.add(u)
    out: list[str] = []
    seen: set[str] = set()
    for a in cand:
        u = str(a or "").upper()
        if not u or u in seen:
            continue
        if u == ticker or u in vivos or manto_en_foto_estado(u, data):
            seen.add(u)
            out.append(u)
    if ticker and ticker not in seen:
        out.insert(0, ticker)
    return out


def activos_siembra_permitidos(
    equity_usd: float,
    *,
    pasos_logrados: list[int] | None = None,
    exigir_candado: bool = True,
    tusk=None,
) -> list[str]:
    """Santos de la flota donde Beru puede nacer (candado pase si director on).

    Fantasma / ensayo nivel 3: sin candado de pasos — Santos elegidos aunque
    el libro de progreso no marque Mariscal sellado.
    """
    from core import pase_director as pd

    flota = catalogo_flota()
    if siembra_sin_candado_pase():
        return _solo_con_manto(list(flota), tusk)
    if not exigir_candado or not pd.director_activo():
        return _solo_con_manto(list(flota), tusk)
    ok: list[str] = []
    for act in flota:
        if pd.beru_puede_cazar(
            act,
            float(equity_usd),
            pasos_logrados=pasos_logrados,
            tusk=tusk,
        ):
            ok.append(act)
    return _solo_con_manto(ok, tusk)


def tier_siembra_activo(
    activo: str,
    *,
    tusk=None,
    pasos_logrados: list[int] | None = None,
) -> str | None:
    """Uniforme del Beru según el mayor grado sostenido por su manto."""
    from core import beru_capital as bc
    from core import pase_director as pd

    if (
        siembra_sin_candado_pase()
        or not pd.director_activo()
        or getattr(config, "LIVE_BERU_TESTNET", False)
    ):
        grado = None
        if tusk is not None:
            grado = pd.grado_beru_para_caza(
                activo,
                tusk=tusk,
                pasos_logrados=pasos_logrados,
            )
        if grado:
            return bc.tier_id_desde_grado(grado)
        return str(getattr(config, "BERU_TIER_DEFAULT", "PROTO1") or "PROTO1").upper()
    grado = pd.grado_beru_para_caza(
        activo,
        tusk=tusk,
        pasos_logrados=pasos_logrados,
    )
    return bc.tier_id_desde_grado(grado) if grado else None


def sellar_wake_ritual(ts: float | None = None, *, force: bool = False) -> float:
    """Corta la memoria corta: × y cazas solo desde este arise."""
    t = float(ts or time.time())
    if not force:
        prev = leer_wake_ritual()
        if prev > 0:
            return prev
    WAKE_RITUAL.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "ts": t,
        "iso": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(t)),
    }
    WAKE_RITUAL.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return t


def leer_wake_ritual() -> float:
    if not WAKE_RITUAL.is_file():
        return 0.0
    try:
        data = json.loads(WAKE_RITUAL.read_text(encoding="utf-8"))
        return float(data.get("ts") or 0)
    except (OSError, TypeError, ValueError, json.JSONDecodeError):
        return 0.0


def ts_wake_de_uid(uid: str) -> float:
    """Ns del uid de semilla (no del hijo _R2_). Unix segundos."""
    m = _UID_SEMILLA_NS.search(str(uid or ""))
    if not m:
        return 0.0
    try:
        return int(m.group(1)) / 1e9
    except (TypeError, ValueError):
        return 0.0


def ts_corte_memoria(barcos: list | None = None, cronica: list | None = None) -> float:
    """Desde cuándo cuenta esta vida: sello de arise, o la semilla más nueva."""
    ritual = leer_wake_ritual()
    if ritual > 0:
        return ritual
    vals: list[float] = []
    for b in barcos or []:
        if isinstance(b, dict):
            t = float(b.get("ts_wake") or 0)
            uid = str(b.get("uid") or "")
        else:
            t = float(getattr(b, "ts_wake", 0) or 0)
            uid = str(getattr(b, "uid", "") or "")
        if t > 0:
            vals.append(t)
        u = ts_wake_de_uid(uid)
        if u > 0:
            vals.append(u)
    for r in cronica or []:
        u = ts_wake_de_uid(str((r or {}).get("uid") or ""))
        if u > 0:
            vals.append(u)
    return max(vals) if vals else 0.0


def crear_semilla_wake(
    activo: str,
    precio_nuevo_0: float,
    *,
    tier_id: str | None = None,
    generacion: int = 1,
    uid: str | None = None,
) -> BeruShip:
    """Semilla continua: masa 0; 0 local = wake; el metro Igris lo inyecta el plantador."""
    act = str(activo or "").upper()
    cl, cm = centros_al_wake(precio_nuevo_0)
    adn = adn_capitan_wake()
    tid = str(tier_id or getattr(config, "BERU_TIER_DEFAULT", "PROTO1") or "PROTO1")
    uid_f = uid or f"BERU_SEM_{act}_{time.time_ns()}"
    return BeruShip(
        uid=uid_f,
        centro_local=cl,
        centro_manto=cm,
        ancla_tramo=cl,
        masa=0.0,
        direccion="LONG",
        estado="ACECHANDO",
        generacion=int(generacion),
        adn_capitan=adn,
        tier_id=tid,
        modo_combate="CAZA",
        ciclo_infinito=False,
        neg_post_cazador=False,
        es_super_beru=False,
        masa_congelada=0.0,
        sangre_vista_dentro=True,
        ts_wake=float(leer_wake_ritual() or time.time()),
    )


def aplicar_centro_manto_wake(semilla: BeruShip, precio_actual: float, tusk_centro: float = 0.0) -> BeruShip:
    """Metro = Tusk. 0 local de acecho = precio de wake. Sin manto no hay semilla."""
    px = float(precio_actual or 0.0)
    centro = float(tusk_centro or 0.0)
    semilla.centro_manto = centro
    if px > 0:
        semilla.centro_local = px
        semilla.ancla_tramo = px
    semilla.sangre_vista_dentro = True
    return semilla


def manto_bellion_usable(tusk, activo: str) -> bool:
    """¿Hay metro L+S en Bellion/Tusk para sembrar sin reconcile live?"""
    from core import beru_cazador as bc

    return bc.manto_vivo(tusk, activo)


def resumen_cableado() -> dict[str, Any]:
    from core import beru_ley
    from core import beru_fantasma
    from core import beru_ensayo

    base = {
        "wake_reset_0": wake_reset_0_activo(),
        "siembra_flota": siembra_flota_activa(),
        "capitan_wake": str(getattr(config, "BERU_CAPITAN_WAKE", "NORMAL")),
        "vacio_pct": round(vacio_wake_pct() * 100, 4),
        "sangre_pct": round(float(
            getattr(config, "BERU_LLAMADO_SANGRE_PCT", 0.011) or 0.011
        ) * 100, 4),
        "manos": manos_beru_activas(),
        "manos_fantasma": manos_fantasma_activas(),
        "manos_activos": activos_manos_reales(),
        "ensayo_nivel3": ensayo_nivel3_activo(),
        "hilo_enabled": bool(getattr(config, "BERU_HILO_ENABLED", False)),
        "n_flota_catalogo": len(catalogo_flota()),
    }
    base.update(beru_ley.resumen_ley())
    if manos_fantasma_activas():
        base.update(beru_fantasma.resumen_modo())
    if ensayo_nivel3_activo():
        base.update(beru_ensayo.resumen_modo())
    return base
