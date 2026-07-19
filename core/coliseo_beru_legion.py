"""Beru Fantasma — Legión (Coliseo mega): capas, fusión hoz, Mega, tiers, malla ×N.

Contabilidad: masa spot seca (fee = fee_pct × masa × 2). No nocional Igris.
Indicador pase de batalla: calor 3d 20% · mes 50% · año 30%.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Literal

from core import beru_tier
from core.coliseo_beru_fantasma import (
    FEE_PCT,
    MORDIDA_USD,
    STEP_LATIDO,
    FantasmaResult,
    PathPolicy,
    _latidos_velas,
    apply_slip,
    _cobrar,
)

# Pase de batalla (Monarca): 3 días / mes / año
PESOS_PASE_BATALLA = (0.20, 0.50, 0.30)  # 3d · mes · año
FUSION_EPS = 0.0001  # 0.01%
MAX_SHIPS_DEFAULT = 16
TIERS_ORDEN = ("BERUBBY", "PROTO2", "PROTO1", "PLENO")  # Soldado → Mariscal


@dataclass
class LegionResult(FantasmaResult):
    n_ships_max: int = 0
    n_capas: int = 0
    n_fusiones: int = 0
    n_megas: int = 0
    masa_max: float = 0.0
    masa_cap_hits: int = 0
    tier_id: str = "PLENO"
    malla_scale: float = 1.0
    rango: str = "Mariscal"


@dataclass
class _Ship:
    uid: str
    centro: float
    modo: str = "espera"
    lado: str = ""
    oz: float = 0.0
    red: float = 0.0
    masa: float = 0.0
    entry: float = 0.0
    ancla: float = 0.0
    oz_cond: float = 0.0
    neg_toques: int = 0
    masa_congelada: bool = False
    red_residual: float = 0.0
    tiene_residual: bool = False
    es_mega: bool = False
    capa: int = 1


def calor_pase(
    efi_3d: float | None,
    efi_mes: float | None,
    efi_anio: float | None,
    *,
    pesos: tuple[float, float, float] = PESOS_PASE_BATALLA,
) -> float:
    vals = [efi_3d, efi_mes, efi_anio]
    acc = 0.0
    wsum = 0.0
    for v, w in zip(vals, pesos):
        if v is None:
            continue
        acc += float(v) * w
        wsum += w
    if wsum <= 0:
        return 0.0
    return round(acc / wsum, 6)


def _grid_params(tier_id: str, malla_scale: float) -> dict[str, float]:
    t = beru_tier.tier_por_id(tier_id)
    s = max(0.5, float(malla_scale))
    oz_n, red_n = t.pasos("NEGOCIADOR")
    return {
        "paso_trailing": t.paso_oz_caza * s,
        "clon_red": t.distancia_clon_pct * s,
        "paso_oz_neg": oz_n * s,
        "paso_red_neg": red_n * s,
        "escala_manto": t.escala_manto,
        "rango": t.rango,
    }


def simular_beru_legion(
    precios: Iterable[float],
    *,
    activo: str = "?",
    vacio: float = 0.014,
    margen_usd: float = 12.5,
    fee_pct: float = FEE_PCT,
    mordida_usd: float = MORDIDA_USD,
    slip_bps: float = 2.0,
    abismo: float | None = None,
    tier_id: str = "PLENO",
    malla_scale: float = 1.0,
    masa_cap: float | None = None,
    max_ships: int = MAX_SHIPS_DEFAULT,
) -> LegionResult:
    """Legión al máximo potencial en un stream de precios."""
    g = _grid_params(tier_id, malla_scale)
    paso_trailing = g["paso_trailing"]
    clon_red = g["clon_red"]
    paso_oz_neg = g["paso_oz_neg"]
    paso_red_neg = g["paso_red_neg"]
    gatillo = vacio * 0.5
    ab = float(abismo) if abismo is not None else float(vacio)
    # Oxígeno de teatro: tope de masa por barco (evita outliers absurdos tipo BCH)
    if masa_cap is None:
        masa_cap = max(80.0, float(margen_usd) * 8.0 / max(g["escala_manto"], 1.0))

    ships: list[_Ship] = []
    next_id = 1
    bruto = 0.0
    fees = 0.0
    cosechas = 0
    toques_neg = 0
    ciclos = 0
    n_capas = 0
    n_fusiones = 0
    n_megas = 0
    masa_max = 0.0
    masa_cap_hits = 0
    n = 0
    centro_manto = 0.0

    def _new_uid(prefix: str = "B") -> str:
        nonlocal next_id
        uid = f"{prefix}{next_id}"
        next_id += 1
        return uid

    def _cap_masa(m: float) -> float:
        nonlocal masa_cap_hits
        if m > masa_cap:
            masa_cap_hits += 1
            return masa_cap
        return m

    def _arm_caza(sh: _Ship, px: float, lado: str, engorde: bool, masa: float) -> None:
        sh.modo = "caza_real" if engorde else "caza_fantasma"
        sh.lado = lado
        sh.entry = px
        sh.masa = _cap_masa(masa)
        sh.masa_congelada = not engorde
        if lado == "up":
            sh.oz = px * (1.0 - paso_trailing)
            sh.red = px * (1.0 + clon_red)
        else:
            sh.oz = px * (1.0 + paso_trailing)
            sh.red = px * (1.0 - clon_red)

    def _entrar_neg(sh: _Ship, px: float, lado: str, masa: float) -> None:
        sh.modo = "negociador"
        sh.lado = lado
        sh.entry = px
        sh.ancla = px
        sh.masa = masa
        sh.masa_congelada = True
        sh.neg_toques = 1
        if lado == "up":
            sh.oz_cond = px * (1.0 - ab)
            sh.oz = sh.oz_cond * (1.0 - paso_oz_neg)
            sh.red = sh.oz_cond * (1.0 + paso_oz_neg)
        else:
            sh.oz_cond = px * (1.0 + ab)
            sh.oz = sh.oz_cond * (1.0 + paso_oz_neg)
            sh.red = sh.oz_cond * (1.0 - paso_oz_neg)

    def _harvest(sh: _Ship, px: float, lado: str) -> None:
        nonlocal bruto, fees, cosechas, toques_neg
        fill = apply_slip(px, lado, slip_bps)
        pnl, fee = _cobrar(
            entry=sh.entry,
            exit_px=fill,
            masa=sh.masa,
            fee_pct=fee_pct,
            paso_trailing=paso_trailing,
        )
        bruto += pnl
        fees += fee
        cosechas += 1
        if sh.modo == "negociador":
            toques_neg += 1

    def _extreme_red_ship() -> _Ship | None:
        caza = [s for s in ships if s.modo == "caza_real" and not s.masa_congelada]
        if not caza:
            return None
        # más extrema = más lejos del centro en dirección de la red
        def score(s: _Ship) -> float:
            if s.lado == "up":
                return s.red
            return -s.red
        return max(caza, key=score)

    def _try_fusion() -> None:
        nonlocal n_fusiones
        activos = [s for s in ships if s.modo in ("negociador", "caza_real", "caza_fantasma") and s.oz > 0]
        if len(activos) < 2:
            return
        used: set[str] = set()
        nuevos: list[_Ship] = []
        for i, a in enumerate(activos):
            if a.uid in used:
                continue
            group = [a]
            for b in activos[i + 1 :]:
                if b.uid in used:
                    continue
                if a.oz <= 0 or b.oz <= 0:
                    continue
                if abs(a.oz - b.oz) / max(a.oz, b.oz) <= FUSION_EPS:
                    group.append(b)
            if len(group) >= 2:
                for gship in group:
                    used.add(gship.uid)
                leader = group[0]
                masa = _cap_masa(sum(x.masa for x in group))
                leader.masa = masa
                leader.oz = sum(x.oz * x.masa for x in group) / max(masa, 1e-9)
                leader.red = sum(x.red * x.masa for x in group) / max(masa, 1e-9)
                leader.ancla = sum(x.ancla * x.masa for x in group) / max(masa, 1e-9)
                n_fusiones += 1
                # quitar fusionados del roster
                kill = {x.uid for x in group[1:]}
                for s in ships:
                    if s.uid not in kill:
                        nuevos.append(s)
                ships[:] = nuevos
                return
        return

    def _try_mega() -> None:
        nonlocal n_megas
        cands = [s for s in ships if s.modo == "negociador" and not s.es_mega]
        if len(cands) < 2 or centro_manto <= 0:
            return
        # ancla bajo el promedio de anclas (doctrina Mega)
        mean_ancla = sum(s.ancla for s in cands) / len(cands)
        bajos = [s for s in cands if s.ancla < mean_ancla]
        if len(bajos) < 2:
            return
        masa = _cap_masa(sum(s.masa for s in bajos))
        leader = bajos[0]
        leader.es_mega = True
        leader.masa = masa
        leader.uid = _new_uid("M")
        n_megas += 1
        kill = {s.uid for s in bajos[1:]}
        ships[:] = [s for s in ships if s.uid not in kill]

    def _spawn_capa(px: float, lado: str, centro: float) -> None:
        nonlocal n_capas
        if len(ships) >= max_ships:
            return
        sh = _Ship(uid=_new_uid("C"), centro=centro, capa=max((s.capa for s in ships), default=0) + 1)
        _arm_caza(sh, px, lado, engorde=True, masa=mordida_usd)
        ships.append(sh)
        n_capas += 1

    # Semilla inicial: un barco en espera
    for raw in precios:
        if raw <= 0:
            continue
        n += 1
        px = float(raw)
        if not ships:
            centro_manto = px
            ships.append(_Ship(uid=_new_uid("S"), centro=px, modo="espera"))
            continue

        # Semilla acechando: primer gatillo
        for sh in list(ships):
            if sh.modo != "espera":
                continue
            up = sh.centro * (1.0 + gatillo)
            dn = sh.centro * (1.0 - gatillo)
            if px >= up:
                _arm_caza(sh, px, "up", True, mordida_usd)
            elif px <= dn:
                _arm_caza(sh, px, "down", True, mordida_usd)

        # Residuales → nueva capa
        for sh in list(ships):
            if not sh.tiene_residual or sh.red_residual <= 0:
                continue
            hit = False
            if sh.lado == "up" and px >= sh.red_residual:
                hit = True
                lado = "up"
            elif sh.lado == "down" and px <= sh.red_residual:
                hit = True
                lado = "down"
            if hit:
                sh.tiene_residual = False
                _spawn_capa(px, lado, sh.centro)

        # Esperando abismo → re-gatillo
        for sh in list(ships):
            if sh.modo != "esperando_abismo":
                continue
            up = sh.centro * (1.0 + gatillo)
            dn = sh.centro * (1.0 - gatillo)
            if px >= up:
                _arm_caza(sh, px, "up", False, sh.masa)
                ciclos += 1
            elif px <= dn:
                _arm_caza(sh, px, "down", False, sh.masa)
                ciclos += 1

        # Caza: engorde solo frontera extrema
        extremo = _extreme_red_ship()
        for sh in list(ships):
            if sh.modo not in ("caza_real", "caza_fantasma"):
                continue
            engorde = sh.modo == "caza_real" and not sh.masa_congelada and sh is extremo
            if sh.lado == "up":
                if engorde and px >= sh.red:
                    sh.masa = _cap_masa(sh.masa + mordida_usd)
                    sh.red = px * (1.0 + paso_trailing)
                    sh.oz = px * (1.0 - paso_trailing)
                    masa_max = max(masa_max, sh.masa)
                elif px <= sh.oz:
                    _harvest(sh, px, "up")
                    if sh.es_mega:
                        # Mega toca oz → vuelve negociador; red mega resetea en toque red
                        _entrar_neg(sh, px, "up", sh.masa)
                    else:
                        sh.red_residual = sh.red
                        sh.tiene_residual = True
                        _entrar_neg(sh, px, "up", sh.masa)
            else:
                if engorde and px <= sh.red:
                    sh.masa = _cap_masa(sh.masa + mordida_usd)
                    sh.red = px * (1.0 - paso_trailing)
                    sh.oz = px * (1.0 + paso_trailing)
                    masa_max = max(masa_max, sh.masa)
                elif px >= sh.oz:
                    _harvest(sh, px, "down")
                    if sh.es_mega:
                        _entrar_neg(sh, px, "down", sh.masa)
                    else:
                        sh.red_residual = sh.red
                        sh.tiene_residual = True
                        _entrar_neg(sh, px, "down", sh.masa)

        # Negociador
        for sh in list(ships):
            if sh.modo != "negociador":
                continue
            toque_oz = (sh.lado == "up" and px <= sh.oz) or (sh.lado == "down" and px >= sh.oz)
            toque_red = (sh.lado == "up" and px >= sh.red) or (sh.lado == "down" and px <= sh.red)
            if toque_oz:
                _harvest(sh, px, sh.lado)
                sh.neg_toques += 1
                sh.entry = px
                if sh.neg_toques >= 6:
                    if sh.lado == "up":
                        sh.red = sh.oz_cond * (1.0 - paso_oz_neg)
                        sh.oz = sh.oz * (1.0 - paso_oz_neg)
                    else:
                        sh.red = sh.oz_cond * (1.0 + paso_oz_neg)
                        sh.oz = sh.oz * (1.0 + paso_oz_neg)
                    sh.neg_toques = 0
                else:
                    if sh.lado == "up":
                        sh.oz = px * (1.0 - paso_oz_neg)
                        sh.red = px * (1.0 + paso_red_neg)
                    else:
                        sh.oz = px * (1.0 + paso_oz_neg)
                        sh.red = px * (1.0 - paso_red_neg)
            elif toque_red:
                toques_neg += 1
                if sh.es_mega:
                    # Reset Mega: cosecha a bóveda ya contada en oz; semilla nueva masa 0
                    sh.es_mega = False
                    sh.masa = 0.0
                    sh.centro = px
                    sh.modo = "espera"
                    sh.tiene_residual = False
                else:
                    sh.modo = "esperando_abismo"

        _try_fusion()
        _try_mega()
        for sh in ships:
            masa_max = max(masa_max, sh.masa)

    neto = bruto - fees
    efi = (neto / margen_usd) if margen_usd > 0 else 0.0
    return LegionResult(
        activo=activo.upper(),
        vacio_pct=vacio * 100,
        cosechas=cosechas,
        toques_neg=toques_neg,
        ciclos_infinito=ciclos,
        botin_bruto=round(bruto, 4),
        fees=round(fees, 4),
        botin_neto=round(neto, 4),
        margen_usd=margen_usd,
        eficiencia=round(efi, 6),
        latidos=n,
        path_policy="stream",
        modo_final=ships[0].modo if ships else "",
        n_ships_max=max(len(ships), next_id - 1),
        n_capas=n_capas,
        n_fusiones=n_fusiones,
        n_megas=n_megas,
        masa_max=round(masa_max, 2),
        masa_cap_hits=masa_cap_hits,
        tier_id=tier_id.upper(),
        malla_scale=float(malla_scale),
        rango=str(g["rango"]),
    )


def simular_legion_desde_velas(
    candles: list[tuple[int, float, float, float, float]],
    *,
    path_policy: PathPolicy = "ohlc",
    step_pct: float = STEP_LATIDO,
    **kwargs,
) -> LegionResult:
    if path_policy == "ohlc":
        r = simular_beru_legion(_latidos_velas(candles, "ohlc", step_pct), **kwargs)
        r.path_policy = "ohlc"
        return r
    if path_policy == "olhc":
        r = simular_beru_legion(_latidos_velas(candles, "olhc", step_pct), **kwargs)
        r.path_policy = "olhc"
        return r
    # min = peor efi (honesto)
    a = simular_beru_legion(_latidos_velas(candles, "ohlc", step_pct), **kwargs)
    b = simular_beru_legion(_latidos_velas(candles, "olhc", step_pct), **kwargs)
    elegido = a if a.eficiencia <= b.eficiencia else b
    elegido.path_policy = "min"
    elegido.latidos = max(a.latidos, b.latidos)
    elegido.n_capas = max(a.n_capas, b.n_capas)
    elegido.n_fusiones = max(a.n_fusiones, b.n_fusiones)
    elegido.n_megas = max(a.n_megas, b.n_megas)
    elegido.masa_max = max(a.masa_max, b.masa_max)
    return elegido
