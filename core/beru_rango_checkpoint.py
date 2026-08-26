"""Checkpoint / continuar inteligente — Beru rango manos.

Arranque:
  · Sello fresco → retoma fiel (caza o acecho post-Oz)
  · Sello vivo pero viejo → mismo lado; wake del sello (eterno); Red del sello
  · Sin sello útil + posición Tusk → siembra acecho post-Oz (0 = last, campaña nueva)
  · Sin nada → semilla (Vacío ±1,2, sin Red)

Edades (s) por env o defaults.
"""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from core import beru_rango
from core import beru_rango_paths


# Fresco: retoma exacto. Vivo: retoma con 0 recalibrado.
SELLO_FRESCO_S = float(os.getenv("BERU_RANGO_SELLO_FRESCO_S", "900") or 900)
SELLO_VIVO_S = float(os.getenv("BERU_RANGO_SELLO_VIVO_S", "21600") or 21600)


@dataclass(frozen=True)
class PlanArranque:
    modo: str  # SEMILLA | CONTINUAR_CAZA | CONTINUAR_ACECHO | ACECHO_AJUSTE | SEMBRAR_POS
    sello: dict[str, Any] | None
    vivo: dict[str, Any]
    edad_s: float
    cero: float
    red: float
    sangre_lado: str
    hoz_dir: str
    nota: str


def sello_edad_s(sello: dict[str, Any] | None, *, ahora: float | None = None) -> float:
    if not sello:
        return 1e18
    ts = float(sello.get("ts") or 0)
    if ts <= 0:
        return 1e18
    return max(0.0, float(ahora if ahora is not None else time.time()) - ts)


def leer_sello(activo: str) -> dict[str, Any] | None:
    act = str(activo or "").upper()
    path = beru_rango_paths.resolver_manos_informe(act)
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    if str(data.get("activo") or "").upper() != act:
        return None
    vivo = (data.get("snapshot") or {}).get("vivo") or {}
    if float(vivo.get("cero") or 0) <= 0:
        return None
    return data


def _vivo(sello: dict[str, Any] | None) -> dict[str, Any]:
    return ((sello or {}).get("snapshot") or {}).get("vivo") or {}


def sello_util(vivo: dict[str, Any]) -> bool:
    """Hay combate que valga la pena retomar (no solo wake semilla vacío)."""
    if float(vivo.get("cero") or 0) <= 0:
        return False
    if str(vivo.get("estado") or "").upper() == "CAZANDO" and float(vivo.get("oz") or 0) > 0:
        return True
    if float(vivo.get("red") or 0) > 0:
        return True
    if str(vivo.get("sangre_lado") or "").upper() in ("ARRIBA", "ABAJO"):
        return True
    if int(vivo.get("cosechas") or 0) > 0 or int(vivo.get("escalones_red") or 0) > 0:
        return True
    return False


def _lado_desde_pos(posiciones: list[dict[str, Any]]) -> tuple[str, str]:
    """LONG en casa → post-Oz LONG → sangre ABAJO / Red arriba. SHORT → inverso."""
    if not posiciones:
        return "", ""
    best = max(posiciones, key=lambda p: float(p.get("masa_usd") or 0))
    lado = str(best.get("lado") or "").upper()
    if lado == "LONG":
        return "ABAJO", "LONG"
    if lado == "SHORT":
        return "ARRIBA", "SHORT"
    return "", ""


def _infer_hoz(vivo: dict[str, Any], sangre: str) -> str:
    hoz = str(vivo.get("ultima_hoz_direccion") or "").upper()
    if hoz in ("LONG", "SHORT"):
        return hoz
    d = str(vivo.get("direccion") or "").upper()
    if d in ("LONG", "SHORT"):
        return d
    if sangre == "ARRIBA":
        return "LONG"
    if sangre == "ABAJO":
        return "SHORT"
    return "LONG"


def _red_desde_ancla(ancla: float, sangre: str, hoz: str) -> float:
    """Red LONG 0,7 / SHORT 0,8 desde ancla. Sangre ABAJO → Red arriba; ARRIBA → abajo."""
    a = float(ancla or 0)
    if a <= 0:
        return 0.0
    lado = str(sangre or "").upper()
    hoz_u = str(hoz or "").upper()
    if not lado:
        lado = "ABAJO" if hoz_u == "SHORT" else "ARRIBA"
    dir_red = "SHORT" if (lado == "ABAJO" or (not sangre and hoz_u == "SHORT")) else "LONG"
    red_act = beru_rango.red_activacion_pct(dir_red)
    if dir_red == "SHORT":
        return a * (1.0 + red_act)
    return a * (1.0 - red_act)


def _red_desde_cero(cero: float, sangre: str, hoz: str) -> float:
    """Compat: sin oz_despliegue usa cero como ancla (legacy)."""
    return _red_desde_ancla(cero, sangre, hoz)


def decidir_arranque(
    *,
    activo: str,
    last: float,
    posiciones: list[dict[str, Any]] | None = None,
    sello: dict[str, Any] | None = None,
    forzar_semilla: bool = False,
    forzar_continuar: bool = False,
    ahora: float | None = None,
) -> PlanArranque:
    act = str(activo or "").upper()
    px = float(last or 0)
    pos = list(posiciones or [])
    if sello is None and not forzar_semilla:
        sello = leer_sello(act)
    vivo = _vivo(sello)
    edad = sello_edad_s(sello, ahora=ahora)
    fresco = float(SELLO_FRESCO_S)
    vivo_max = float(SELLO_VIVO_S)

    if forzar_semilla:
        return PlanArranque(
            modo="SEMILLA",
            sello=sello,
            vivo=vivo,
            edad_s=edad,
            cero=px,
            red=0.0,
            sangre_lado="",
            hoz_dir="",
            nota="forzado --desde-cero",
        )

    util = sello_util(vivo)
    estado = str(vivo.get("estado") or "").upper()
    cazando = estado == "CAZANDO" and float(vivo.get("oz") or 0) > 0

    # Continuar explícito o sello fresco útil
    if util and (forzar_continuar or edad <= fresco):
        if cazando:
            return PlanArranque(
                modo="CONTINUAR_CAZA",
                sello=sello,
                vivo=vivo,
                edad_s=edad,
                cero=float(vivo.get("cero") or 0),
                red=float(vivo.get("red") or 0),
                sangre_lado=str(vivo.get("sangre_lado") or ""),
                hoz_dir=_infer_hoz(vivo, str(vivo.get("sangre_lado") or "")),
                nota=f"sello fresco {edad:.0f}s · caza fiel",
            )
        sangre = str(vivo.get("sangre_lado") or "").upper()
        hoz = _infer_hoz(vivo, sangre)
        return PlanArranque(
            modo="CONTINUAR_ACECHO",
            sello=sello,
            vivo=vivo,
            edad_s=edad,
            cero=float(vivo.get("cero") or 0),
            red=float(vivo.get("red") or 0),
            sangre_lado=sangre,
            hoz_dir=hoz,
            nota=f"sello fresco {edad:.0f}s · acecho fiel",
        )

    # Sello vivo (no fresco): conserva wake del sello; Red desde oz_despliegue si hay
    if util and edad <= vivo_max:
        sangre = str(vivo.get("sangre_lado") or "").upper()
        hoz = _infer_hoz(vivo, sangre)
        if not sangre:
            sangre = "ABAJO" if hoz == "SHORT" else "ARRIBA"
        # Wake eterno: preferir cero del sello; last solo si sello sin cero
        cero_sello = float(vivo.get("cero") or 0)
        cero = cero_sello if cero_sello > 0 else (px if px > 0 else 0.0)
        oz_dep = float(vivo.get("oz_despliegue") or 0)
        ancla = oz_dep if oz_dep > 0 else cero
        red_sello = float(vivo.get("red") or 0)
        red = red_sello if red_sello > 0 else _red_desde_ancla(ancla, sangre, hoz)
        return PlanArranque(
            modo="ACECHO_AJUSTE",
            sello=sello,
            vivo=vivo,
            edad_s=edad,
            cero=cero,
            red=red,
            sangre_lado=sangre,
            hoz_dir=hoz,
            nota=f"sello {edad:.0f}s · wake sello · Red peldaño (caza abandonada si había)",
        )

    # Sello podrido o vacío: posición manda
    sangre_p, hoz_p = _lado_desde_pos(pos)
    if sangre_p and px > 0:
        esc = int(vivo.get("escalones_red") or 0) if util else 0
        cos = int(vivo.get("cosechas") or 0) if util else 1
        return PlanArranque(
            modo="SEMBRAR_POS",
            sello=sello,
            vivo=vivo,
            edad_s=edad,
            cero=px,
            red=_red_desde_cero(px, sangre_p, hoz_p),
            sangre_lado=sangre_p,
            hoz_dir=hoz_p,
            nota=(
                f"posición {hoz_p} · 0=last · "
                f"{'sello viejo' if util else 'sin sello útil'}"
            ),
        )

    # Último recurso: sello viejo con lado pero sin posición
    if util:
        sangre = str(vivo.get("sangre_lado") or "").upper()
        hoz = _infer_hoz(vivo, sangre)
        if not sangre:
            sangre = "ABAJO" if hoz == "SHORT" else "ARRIBA"
        cero_sello = float(vivo.get("cero") or 0)
        cero = cero_sello if cero_sello > 0 else (px if px > 0 else 0.0)
        oz_dep = float(vivo.get("oz_despliegue") or 0)
        red_sello = float(vivo.get("red") or 0)
        ancla = oz_dep if oz_dep > 0 else cero
        red = red_sello if red_sello > 0 else _red_desde_ancla(ancla, sangre, hoz)
        return PlanArranque(
            modo="ACECHO_AJUSTE",
            sello=sello,
            vivo=vivo,
            edad_s=edad,
            cero=cero,
            red=red,
            sangre_lado=sangre,
            hoz_dir=hoz,
            nota=f"sello antiguo {edad:.0f}s sin posición · wake sello",
        )

    return PlanArranque(
        modo="SEMILLA",
        sello=sello,
        vivo=vivo,
        edad_s=edad,
        cero=px,
        red=0.0,
        sangre_lado="",
        hoz_dir="",
        nota="sin sello útil ni posición",
    )


def aplicar_plan(beru: Any, plan: PlanArranque) -> None:
    """Aplica CONTINUAR_ACECHO / ACECHO_AJUSTE / SEMBRAR_POS sobre el vivo ya despertado."""
    if beru is None or plan.modo in ("SEMILLA", "CONTINUAR_CAZA"):
        return
    vivo = plan.vivo or {}
    beru_rango.restaurar_acecho_post_oz(
        beru,
        cero=float(plan.cero or 0),
        red=float(plan.red or 0),
        sangre_lado=str(plan.sangre_lado or ""),
        ultima_hoz_direccion=str(plan.hoz_dir or ""),
        escalones_red=int(vivo.get("escalones_red") or 0),
        cosechas=max(1, int(vivo.get("cosechas") or 0)) if plan.modo == "SEMBRAR_POS" else int(vivo.get("cosechas") or 0),
        oz_despliegue=float(vivo.get("oz_despliegue") or 0),
        saco_long=float(vivo.get("saco_long") or 0),
        saco_short=float(vivo.get("saco_short") or 0),
    )


def path_sello(activo: str) -> Path:
    return beru_rango_paths.manos_informe(activo)
