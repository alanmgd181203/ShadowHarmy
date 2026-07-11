"""Fusión Beru — colisión estricta oz + Mega Beru (promedio manto)."""
from __future__ import annotations

from typing import TYPE_CHECKING

from core import beru_negociador

if TYPE_CHECKING:
    from core.models import BeruShip

# Coincidencia exacta de hoz (doctrina Monarca); ε solo por float
EPSILON_COLISION_PCT = 0.0


def _masa_barco(b: BeruShip) -> float:
    m = float(getattr(b, "masa_congelada", 0) or 0)
    if m <= 0:
        m = float(getattr(b, "masa", 0) or 0)
    return max(m, 1e-9)


def promedio_ponderado(pares: list[tuple[float, float]]) -> float:
    if not pares:
        return 0.0
    total = sum(m for _, m in pares)
    if total <= 0:
        return pares[0][0]
    return sum(v * m for v, m in pares) / total


def oz_colisionan(oz_a: float, oz_b: float) -> bool:
    if oz_a <= 0 or oz_b <= 0:
        return False
    return abs(oz_a - oz_b) <= max(oz_a, oz_b) * 1e-12 + 1e-8


def cazador_activo_colision(b: BeruShip) -> bool:
    return (
        b.estado == "NEGOCIANDO"
        and str(getattr(b, "modo_combate", "")).upper() == "CAZA"
        and float(getattr(b, "oz_adan", 0) or 0) > 0
        and (
            getattr(b, "ciclo_infinito", False)
            or (
                float(getattr(b, "oz_pct", 0) or 0) != 0.0
                and float(getattr(b, "red_pct", 0) or 0) != 0.0
            )
        )
    )


def negociador_activo_colision(b: BeruShip) -> bool:
    return (
        getattr(b, "ciclo_infinito", False)
        and b.estado == "NEGOCIANDO"
        and str(getattr(b, "modo_combate", "")).upper() == "NEGOCIADOR"
        and float(getattr(b, "neg_red_pct", 0) or 0) != 0.0
        and float(getattr(b, "oz_adan", 0) or 0) > 0
    )


def barco_colisionable(b: BeruShip) -> bool:
    return cazador_activo_colision(b) or negociador_activo_colision(b)


def _agrupar_por_colision_oz(barcos: list[BeruShip]) -> list[list[BeruShip]]:
    """Union-find por dirección + oz_adan dentro de ε."""
    activos = [b for b in barcos if barco_colisionable(b)]
    grupos: list[list[BeruShip]] = []
    for b in activos:
        oz_b = float(b.oz_adan)
        fundido = False
        for grupo in grupos:
            if grupo[0].direccion != b.direccion:
                continue
            if oz_colisionan(float(grupo[0].oz_adan), oz_b):
                grupo.append(b)
                fundido = True
                break
        if not fundido:
            grupos.append([b])
    return [g for g in grupos if len(g) >= 2]


def fusionar_colision_oz(grupo: list[BeruShip]) -> tuple[BeruShip, list[BeruShip]]:
    """Colisión estricta de Hoz → un agente, masa sumada, red/ancla promedio."""
    lider = max(grupo, key=_masa_barco)
    victimas = [b for b in grupo if b is not lider]
    m_total = sum(_masa_barco(b) for b in grupo)
    lider.masa_congelada = m_total
    lider.masa = m_total

    if str(getattr(lider, "modo_combate", "")).upper() == "NEGOCIADOR":
        lider.ancla_cosecha_pct = promedio_ponderado(
            [(float(b.ancla_cosecha_pct), _masa_barco(b)) for b in grupo],
        )
        lider.neg_oz_pct = promedio_ponderado(
            [(float(b.neg_oz_pct), _masa_barco(b)) for b in grupo],
        )
        lider.neg_red_pct = promedio_ponderado(
            [(float(b.neg_red_pct), _masa_barco(b)) for b in grupo],
        )
        lider.neg_toques_ciclo = max(int(getattr(b, "neg_toques_ciclo", 0) or 0) for b in grupo)
    else:
        lider.oz_pct = promedio_ponderado(
            [(float(b.oz_pct), _masa_barco(b)) for b in grupo],
        )
        lider.red_pct = promedio_ponderado(
            [(float(b.red_pct), _masa_barco(b)) for b in grupo],
        )

    lider.es_super_beru = len(grupo) > 2
    return lider, victimas


# --- Mega Beru (sagrado — no modificar lógica) ---

def esperando_condicional(b: BeruShip) -> bool:
    return (
        getattr(b, "ciclo_infinito", False)
        and b.estado == "ESPERANDO_CONDICIONAL"
    )


def ancla_bajo_promedio(ancla: float, prom: float) -> bool:
    if prom >= 0 and ancla >= 0:
        return ancla < prom - 1e-9
    if prom <= 0 and ancla <= 0:
        return ancla > prom + 1e-9
    return ancla < prom - 1e-9


def grupos_mega_beru(barcos: list[BeruShip]) -> list[tuple[BeruShip, list[BeruShip], float]]:
    resultados: list[tuple[BeruShip, list[BeruShip], float]] = []
    por_dir: dict[str, list[BeruShip]] = {}
    for b in barcos:
        if not esperando_condicional(b):
            continue
        por_dir.setdefault(b.direccion, []).append(b)
    for grupo in por_dir.values():
        if len(grupo) < 2:
            continue
        prom = promedio_ponderado(
            [(float(b.ancla_cosecha_pct), _masa_barco(b)) for b in grupo],
        )
        debajo = [b for b in grupo if ancla_bajo_promedio(float(b.ancla_cosecha_pct), prom)]
        if len(debajo) < 2:
            continue
        lider = max(debajo, key=lambda b: _masa_barco(b))
        victimas = [b for b in debajo if b is not lider]
        resultados.append((lider, victimas, prom))
    return resultados


def aplicar_mega_beru(lider: BeruShip, victimas: list[BeruShip], prom: float, vacio: float) -> None:
    m_total = sum(_masa_barco(b) for b in [lider] + victimas)
    lider.masa_congelada = m_total
    lider.masa = m_total
    lider.ancla_cosecha_pct = prom
    lider.neg_oz_pct = beru_negociador.oz_condicional_pct(prom, vacio)
    lider.neg_red_pct = 0.0
    lider.neg_toques_ciclo = 0
    lider.estado = "ESPERANDO_CONDICIONAL"
    lider.modo_combate = "NEGOCIADOR"
    lider.es_super_beru = True


# Aliases legados para smokes que importen nombres viejos
grupos_colision_oz = _agrupar_por_colision_oz
fusionar_coincidencia = fusionar_colision_oz
fusionar_coincidencia_caza = fusionar_colision_oz

def grupos_coincidencia_negociador(barcos: list[BeruShip]) -> list[list[BeruShip]]:
    return _agrupar_por_colision_oz([b for b in barcos if negociador_activo_colision(b)])


def grupos_coincidencia_caza(barcos: list[BeruShip]) -> list[list[BeruShip]]:
    return _agrupar_por_colision_oz([b for b in barcos if cazador_activo_colision(b)])
