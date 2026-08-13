"""Igris — sueño + misiones (mega-cirugía 2026-08-12).

Ley: Igris duerme; el sargento encola misiones; el brazo ejecuta y vuelve a dormir.
No asumir parámetros abiertos — ver migracion/DUDAS_CIRUGIAS_MENORES_2026-08-12.md
"""
from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any, Literal

import core.config as config

TipoMision = Literal[
    "sembrar",
    "engordar",
    "corregir",
    "reducir",
    "dormir",
]

_cola: asyncio.Queue | None = None
_estado_sueno = True
_mision_activa: dict[str, Any] | None = None


def sueno_mision_activo() -> bool:
    return bool(getattr(config, "IGRIS_SUENO_MISION", True))


def sargento_auto() -> bool:
    return bool(getattr(config, "IGRIS_SARGENTO_AUTO", True))


def solo_asalto() -> bool:
    return bool(getattr(config, "IGRIS_SOLO_ASALTO", True))


def poll_sueno_s() -> float:
    return float(getattr(config, "IGRIS_SUENO_POLL_S", 2.0) or 2.0)


def _cola_misiones() -> asyncio.Queue:
    global _cola
    if _cola is None:
        _cola = asyncio.Queue()
    return _cola


def esta_dormido() -> bool:
    return bool(_estado_sueno)


def marcar_sueno(dormido: bool = True) -> None:
    global _estado_sueno
    _estado_sueno = bool(dormido)


def mision_activa() -> dict[str, Any] | None:
    return dict(_mision_activa) if _mision_activa else None


def set_mision_activa(m: dict[str, Any] | None) -> None:
    global _mision_activa
    _mision_activa = dict(m) if m else None


@dataclass
class MisionIgris:
    tipo: TipoMision
    activo: str | None = None
    usd_objetivo: float = 0.0
    confirmado: bool = False
    origen: str = "sargento"
    meta: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "tipo": self.tipo,
            "activo": (self.activo or "").upper() or None,
            "usd_objetivo": float(self.usd_objetivo or 0),
            "confirmado": bool(self.confirmado),
            "origen": self.origen,
            "meta": dict(self.meta or {}),
            "ts": time.time(),
        }


async def encolar(mision: MisionIgris | dict[str, Any]) -> None:
    if isinstance(mision, MisionIgris):
        payload = mision.as_dict()
    else:
        payload = dict(mision)
        payload.setdefault("ts", time.time())
        if payload.get("activo"):
            payload["activo"] = str(payload["activo"]).upper()
    await _cola_misiones().put(payload)
    marcar_sueno(False)


def encolar_sync(mision: MisionIgris | dict[str, Any]) -> None:
    """Desde hilos sync / Arise: programa encolar en el loop si existe."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        # Sin loop: deja pendiente en cola creando una nueva (próximo await la consume)
        q = _cola_misiones()
        if isinstance(mision, MisionIgris):
            q.put_nowait(mision.as_dict())
        else:
            d = dict(mision)
            d.setdefault("ts", time.time())
            q.put_nowait(d)
        marcar_sueno(False)
        return
    loop.create_task(encolar(mision))


async def sacar_mision(timeout: float | None = None) -> dict[str, Any] | None:
    q = _cola_misiones()
    try:
        if timeout is None:
            return await q.get()
        return await asyncio.wait_for(q.get(), timeout=float(timeout))
    except asyncio.TimeoutError:
        return None


def vaciar_cola() -> int:
    q = _cola_misiones()
    n = 0
    while not q.empty():
        try:
            q.get_nowait()
            n += 1
        except Exception:
            break
    return n


def reducir_requiere_confirma() -> bool:
    return bool(getattr(config, "IGRIS_REDUCIR_REQUIERE_CONFIRMA", True))


def reducir_permitido(m: dict[str, Any]) -> tuple[bool, str]:
    """Ante duda no ejecutar reducir sin confirmación explícita."""
    if str(m.get("tipo") or "") != "reducir":
        return True, "ok"
    if not reducir_requiere_confirma():
        return True, "confirma_desactivada"
    if m.get("confirmado") or getattr(config, "IGRIS_REDUCIR_CONFIRMADO", False):
        return True, "confirmado"
    return False, "REDUCIR_ESPERA_CONFIRMA"


def construir_misiones_sargento(tusk, *, marcha_id: str | None = None) -> list[MisionIgris]:
    """Arma misiones sembrar/engordar desde pase + have/need (observador)."""
    from core import igris_proteccion as iprot
    from core import pase_director as pd

    out: list[MisionIgris] = []
    eq = float(getattr(tusk, "masa_bruta_real", 0) or getattr(tusk, "masa_bruta", 0) or 0)
    if eq <= 0:
        return out

    mid = marcha_id
    if solo_asalto():
        mid = "asalto"

    try:
        activos = pd.activos_lote_abiertos(eq, marcha_id=mid) if pd.director_activo() else []
    except Exception:
        activos = []
    if not activos:
        try:
            from core import plan_crecimiento as pc
            if pc.rank_gate_activo():
                pref = pc.activo_manto_preferido(eq)
                activos = [pref] if pref else []
        except Exception:
            pass
    if not activos:
        activos = [str(getattr(config, "TICKER_BASE", "ETH") or "ETH").upper()]

    activos = iprot.filtrar_activos_trabajo(activos)
    for act in activos:
        act_u = str(act).upper()
        have = 0.0
        need = 0.0
        restante = 0.0
        try:
            if pd.director_activo():
                meta = pd.meta_engorde_usd(eq, act_u, tusk=tusk, marcha_id=mid)
                if meta.get("overshoot_ranking") or float(meta.get("restante_usd") or 0) <= 0:
                    continue
                restante = float(meta.get("restante_usd") or 0)
                have = float(meta.get("have_usd") or 0)
                need = float(meta.get("need_fill_usd") or meta.get("need_usd") or 0)
            else:
                restante = float(getattr(tusk, "masa_autorizada", 0) or 0)
        except Exception:
            continue
        tipo: TipoMision = "sembrar" if have <= 1e-6 else "engordar"
        out.append(
            MisionIgris(
                tipo=tipo,
                activo=act_u,
                usd_objetivo=restante,
                origen="sargento_auto",
                meta={"have_usd": have, "need_usd": need, "equity_usd": eq},
            )
        )
    return out


def snapshot_telemetria() -> dict[str, Any]:
    return {
        "sueno_mision": sueno_mision_activo(),
        "dormido": esta_dormido(),
        "sargento_auto": sargento_auto(),
        "solo_asalto": solo_asalto(),
        "cola_approx": _cola.qsize() if _cola is not None else 0,
        "mision_activa": mision_activa(),
        "vision_modo": getattr(config, "IGRIS_VISION_MODO", "last_price"),
    }
