"""Fusión Beru + Mega — doctrina sellada Monarca 2026-08-13.

1) Fusión por promedio: promedio de TODOS los negociadores vivos.
   Los bajo el promedio se fusionan; el promedio = llamado del mega oro.
   Los arriba siguen normales.

2) Fusión por misma carta: llamado del oro de uno + Hoz de otro al mismo
   precio → un Beru, masas sumadas, Red otra vez a 0.1%.

3) Mega fusión: al tocar el mega oro de abajo, si desde arriba ya hay Mega
   fusionado → todos en una sola mega negociación.

4) Tras negociar el Mega: ese precio = nuevo 0; tablas limpias; nace cazador
   con llamado de sangre ±0.9%.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from core import beru_negociador

if TYPE_CHECKING:
    from core.models import BeruShip

EPSILON_COLISION_PCT = 0.0001  # 0.01% — misma carta


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


def promedio_simple(valores: list[float]) -> float:
    if not valores:
        return 0.0
    return sum(valores) / len(valores)


def oz_colisionan(oz_a: float, oz_b: float) -> bool:
    if oz_a == 0 or oz_b == 0:
        return False
    # Precios absolutos o pct — comparar relativo
    ref = max(abs(oz_a), abs(oz_b), 1e-12)
    return abs(oz_a - oz_b) <= ref * EPSILON_COLISION_PCT + 1e-12


def pct_colisionan(a: float, b: float) -> bool:
    return abs(a - b) <= EPSILON_COLISION_PCT + 1e-12


def negociador_vivo(b: BeruShip) -> bool:
    return (
        b.estado in ("NEGOCIANDO", "ESPERANDO_CONDICIONAL")
        and str(getattr(b, "modo_combate", "")).upper() == "NEGOCIADOR"
        and b.estado != "FUSIONADO"
    )


def ancla_de_negociador(b: BeruShip) -> float:
    """Nivel para Mega: donde ESPERA (llamado del oro / condicional), no la Hoz vieja."""
    cond = float(getattr(b, "neg_oz_pct", 0) or 0)
    if b.estado == "ESPERANDO_CONDICIONAL":
        if cond != 0.0:
            return cond
        a = float(getattr(b, "ancla_cosecha_pct", 0) or 0)
        if a != 0.0:
            return beru_negociador.oz_condicional_pct(a)
        return 0.0
    if cond != 0.0:
        return cond
    return float(getattr(b, "ancla_cosecha_pct", 0) or 0)


def cazador_activo_colision(b: BeruShip) -> bool:
    return (
        b.estado == "NEGOCIANDO"
        and str(getattr(b, "modo_combate", "")).upper() == "CAZA"
        and float(getattr(b, "oz_adan", 0) or 0) > 0
    )


def negociador_activo_colision(b: BeruShip) -> bool:
    return (
        negociador_vivo(b)
        and b.estado == "NEGOCIANDO"
        and float(getattr(b, "neg_oz_pct", 0) or 0) != 0.0
    )


def barco_colisionable(b: BeruShip) -> bool:
    return cazador_activo_colision(b) or negociador_activo_colision(b)


def _agrupar_por_colision_oz(barcos: list[BeruShip]) -> list[list[BeruShip]]:
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
    """Misma Hoz → un agente, masa sumada."""
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
        # Ping-pong: una sola trailing — sin Red de acordeón
        lider.neg_red_pct = 0.0
        lider.neg_toques_ciclo = 0
    else:
        lider.oz_pct = promedio_ponderado(
            [(float(b.oz_pct), _masa_barco(b)) for b in grupo],
        )
        lider.red_pct = promedio_ponderado(
            [(float(b.red_pct), _masa_barco(b)) for b in grupo],
        )

    lider.es_super_beru = len(grupo) >= 2
    return lider, victimas


def fusion_oro_y_hoz(
    barcos: list[BeruShip],
    precio_pct: float,
) -> list[tuple[BeruShip, BeruShip]]:
    """Si el precio toca a la vez el llamado del oro de A y la Hoz de B → pareja fusible."""
    pares: list[tuple[BeruShip, BeruShip]] = []
    negs = [b for b in barcos if negociador_vivo(b)]
    for i, a in enumerate(negs):
        oro_a = ancla_de_negociador(a)
        if not pct_colisionan(oro_a, precio_pct) and a.estado != "ESPERANDO_CONDICIONAL":
            # También: oz absoluta del acordeón
            oz_a = float(getattr(a, "neg_oz_pct", 0) or 0)
            if not pct_colisionan(oz_a, precio_pct):
                continue
        for b in negs[i + 1:]:
            oz_b = float(getattr(b, "neg_oz_pct", 0) or 0)
            oro_b = ancla_de_negociador(b)
            # oro de uno ≈ oz del otro en este precio
            if pct_colisionan(oro_a, oz_b) or pct_colisionan(oro_b, oz_a):
                if a.direccion == b.direccion:
                    pares.append((a, b))
            elif pct_colisionan(oro_a, precio_pct) and pct_colisionan(oz_b, precio_pct):
                if a.direccion == b.direccion:
                    pares.append((a, b))
    return pares


def aplicar_fusion_misma_carta(a: BeruShip, b: BeruShip) -> tuple[BeruShip, BeruShip]:
    lider, victimas = fusionar_colision_oz([a, b])
    return lider, victimas[0]


# --- Mega por promedio (todos los negociadores) ---

def negociadores_por_direccion(barcos: list[BeruShip]) -> dict[str, list[BeruShip]]:
    por: dict[str, list[BeruShip]] = {}
    for b in barcos:
        if not negociador_vivo(b):
            continue
        if getattr(b, "estado", "") == "FUSIONADO":
            continue
        por.setdefault(b.direccion, []).append(b)
    return por


def ancla_bajo_promedio(ancla: float, prom: float) -> bool:
    if prom >= 0 and ancla >= 0:
        return ancla < prom - 1e-9
    if prom <= 0 and ancla <= 0:
        return ancla > prom + 1e-9
    return ancla < prom - 1e-9


def grupos_mega_beru(barcos: list[BeruShip]) -> list[tuple[BeruShip, list[BeruShip], float]]:
    """Promedio de TODOS los negociadores; fusiona los bajo el promedio."""
    resultados: list[tuple[BeruShip, list[BeruShip], float]] = []
    for grupo in negociadores_por_direccion(barcos).values():
        if len(grupo) < 2:
            continue
        # Promedio de anclas/condicionales de todos
        niveles = [ancla_de_negociador(b) for b in grupo]
        prom = promedio_simple(niveles)
        debajo = [b for b in grupo if ancla_bajo_promedio(ancla_de_negociador(b), prom)]
        if len(debajo) < 2:
            continue
        lider = max(debajo, key=_masa_barco)
        victimas = [b for b in debajo if b is not lider]
        resultados.append((lider, victimas, prom))
    return resultados


def aplicar_mega_beru(lider: BeruShip, victimas: list[BeruShip], prom: float, vacio: float | None = None) -> None:
    """Mega atrapado: masas sumadas; promedio = llamado del mega oro."""
    m_total = sum(_masa_barco(b) for b in [lider] + victimas)
    lider.masa_congelada = m_total
    lider.masa = m_total
    lider.ancla_cosecha_pct = prom
    # El promedio YA es el llamado del mega oro (no restar otro abismo)
    lider.neg_oz_pct = prom
    lider.neg_red_pct = 0.0
    lider.neg_toques_ciclo = 0
    lider.estado = "ESPERANDO_CONDICIONAL"
    lider.modo_combate = "NEGOCIADOR"
    lider.es_super_beru = True
    _ = vacio


def mega_fusion_arriba_abajo(
    mega_abajo: BeruShip,
    mega_arriba: BeruShip,
) -> tuple[BeruShip, BeruShip]:
    """Cuando el precio toca el mega oro y hay Mega arriba → una sola mega negociación."""
    return aplicar_fusion_misma_carta(mega_abajo, mega_arriba)


# Aliases legados
esperando_condicional = negociador_vivo
grupos_colision_oz = _agrupar_por_colision_oz
fusionar_coincidencia = fusionar_colision_oz
fusionar_coincidencia_caza = fusionar_colision_oz


def grupos_coincidencia_negociador(barcos: list[BeruShip]) -> list[list[BeruShip]]:
    return _agrupar_por_colision_oz([b for b in barcos if negociador_activo_colision(b)])


def grupos_coincidencia_caza(barcos: list[BeruShip]) -> list[list[BeruShip]]:
    return _agrupar_por_colision_oz([b for b in barcos if cazador_activo_colision(b)])
