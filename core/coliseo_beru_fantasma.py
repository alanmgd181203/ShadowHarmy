"""Beru Fantasma — replay simplificado sobre velas 1m → latidos 0.05%.

Métrica corona: botín neto / dólar de manto (margen Soldado del diccionario).
No es el Beru vivo completo; es el Coliseo para ranking de eficiencia (5.3.3).
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable, Literal

PathPolicy = Literal["ohlc", "olhc", "min"]


def expand_to_latidos(
    open_: float,
    high: float,
    low: float,
    close: float,
    *,
    step_pct: float = 0.0005,
    order: Literal["ohlc", "olhc"] = "ohlc",
) -> list[float]:
    """Convierte OHLC en secuencia de precios a pasos ~step_pct."""
    if open_ <= 0:
        return []
    if order == "ohlc":
        waypoints = [open_, high, low, close]
    else:
        waypoints = [open_, low, high, close]
    out: list[float] = [waypoints[0]]
    for target in waypoints[1:]:
        cur = out[-1]
        if cur <= 0 or target <= 0:
            continue
        if abs(math.log(target / cur)) < 1e-12:
            out.append(target)
            continue
        direction = 1.0 if target >= cur else -1.0
        px = cur
        guard = 0
        while guard < 50_000:
            guard += 1
            nxt = px * (1.0 + direction * step_pct)
            if direction > 0 and nxt >= target:
                out.append(target)
                break
            if direction < 0 and nxt <= target:
                out.append(target)
                break
            out.append(nxt)
            px = nxt
    return out


@dataclass
class FantasmaResult:
    activo: str
    vacio_pct: float
    cosechas: int = 0
    botin_bruto: float = 0.0
    fees: float = 0.0
    botin_neto: float = 0.0
    margen_usd: float = 0.0
    eficiencia: float = 0.0  # botin_neto / margen
    latidos: int = 0
    path_policy: str = "min"


@dataclass
class _State:
    centro: float
    modo: str = "espera"  # espera | caza
    lado: str = ""  # up | down
    oz: float = 0.0
    red: float = 0.0
    masa: float = 0.0
    entry: float = 0.0


def simular_beru_fantasma(
    precios: Iterable[float],
    *,
    activo: str = "?",
    vacio: float = 0.016,
    margen_usd: float = 12.5,
    fee_pct: float = 0.001,  # 0.1% por pierna spot
    paso_latido: float = 0.0005,
    paso_trailing: float = 0.001,
    clon_red: float = 0.001,
    mordida_usd: float = 5.0,
    notional_por_pierna: float | None = None,
) -> FantasmaResult:
    """Replay cazador simplificado: gatillo vacio/2, trailing, cosecha en oz."""
    gatillo = vacio * 0.5
    # Notional tal que 0.1% ≈ $5 engorde doctrina (PLENO ~$50/1%)
    if notional_por_pierna is None:
        notional_por_pierna = mordida_usd / paso_trailing  # $5 / 0.001 = $5000
    st: _State | None = None
    cosechas = 0
    bruto = 0.0
    fees = 0.0
    n = 0

    for px in precios:
        if px <= 0:
            continue
        n += 1
        if st is None:
            st = _State(centro=px)
            continue

        if st.modo == "espera":
            up = st.centro * (1.0 + gatillo)
            dn = st.centro * (1.0 - gatillo)
            if px >= up:
                st.modo = "caza"
                st.lado = "up"
                st.entry = px
                st.masa = mordida_usd
                st.oz = px * (1.0 - paso_trailing)
                st.red = px * (1.0 + clon_red)
            elif px <= dn:
                st.modo = "caza"
                st.lado = "down"
                st.entry = px
                st.masa = mordida_usd
                st.oz = px * (1.0 + paso_trailing)
                st.red = px * (1.0 - clon_red)
            continue

        # caza
        assert st is not None
        if st.lado == "up":
            if px >= st.red:
                st.masa += mordida_usd
                st.red = px * (1.0 + paso_trailing)
                st.oz = px * (1.0 - paso_trailing)
            elif px <= st.oz:
                # Mean-reversion: gatillo arriba → cosecha al volver hacia el 0
                capas = max(1.0, st.masa / mordida_usd)
                move = abs(st.entry - px) / st.entry if st.entry else 0.0
                pnl = notional_por_pierna * move * capas
                fee = notional_por_pierna * capas * fee_pct * 2.0
                bruto += pnl
                fees += fee
                cosechas += 1
                st = _State(centro=px, modo="espera")
        else:
            if px <= st.red:
                st.masa += mordida_usd
                st.red = px * (1.0 - paso_trailing)
                st.oz = px * (1.0 + paso_trailing)
            elif px >= st.oz:
                capas = max(1.0, st.masa / mordida_usd)
                move = abs(px - st.entry) / st.entry if st.entry else 0.0
                pnl = notional_por_pierna * move * capas
                fee = notional_por_pierna * capas * fee_pct * 2.0
                bruto += pnl
                fees += fee
                cosechas += 1
                st = _State(centro=px, modo="espera")

    neto = bruto - fees
    efi = (neto / margen_usd) if margen_usd > 0 else 0.0
    return FantasmaResult(
        activo=activo.upper(),
        vacio_pct=vacio * 100,
        cosechas=cosechas,
        botin_bruto=round(bruto, 4),
        fees=round(fees, 4),
        botin_neto=round(neto, 4),
        margen_usd=margen_usd,
        eficiencia=round(efi, 6),
        latidos=n,
        path_policy="stream",
    )


def simular_desde_velas(
    candles: list[tuple[int, float, float, float, float]],
    *,
    path_policy: PathPolicy = "min",
    step_pct: float = 0.0005,
    **kwargs,
) -> FantasmaResult:
    """path_policy min = peor eficiencia entre OHL C y OLHC (honesto)."""
    if path_policy == "ohlc":
        precios = _latidos_velas(candles, "ohlc", step_pct)
        r = simular_beru_fantasma(precios, **kwargs)
        r.path_policy = "ohlc"
        return r
    if path_policy == "olhc":
        precios = _latidos_velas(candles, "olhc", step_pct)
        r = simular_beru_fantasma(precios, **kwargs)
        r.path_policy = "olhc"
        return r

    a = simular_beru_fantasma(_latidos_velas(candles, "ohlc", step_pct), **kwargs)
    b = simular_beru_fantasma(_latidos_velas(candles, "olhc", step_pct), **kwargs)
    elegido = a if a.eficiencia <= b.eficiencia else b
    elegido.path_policy = "min"
    elegido.latidos = max(a.latidos, b.latidos)
    return elegido


def _latidos_velas(
    candles: list[tuple[int, float, float, float, float]],
    order: Literal["ohlc", "olhc"],
    step_pct: float,
) -> list[float]:
    out: list[float] = []
    for _ts, o, h, l, c in candles:
        chunk = expand_to_latidos(o, h, l, c, step_pct=step_pct, order=order)
        if out and chunk and abs(chunk[0] - out[-1]) < 1e-12:
            out.extend(chunk[1:])
        else:
            out.extend(chunk)
    return out


def calor_eficiencia(
    efi_dia: float | None,
    efi_semana: float | None,
    efi_anio: float | None,
    *,
    pesos: tuple[float, float, float] = (0.20, 0.50, 0.30),
) -> float:
    """Pesos: día / semana / año — semana manda (espejo Kaiser)."""
    vals = [efi_dia, efi_semana, efi_anio]
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


def semaforo(rank: int, n: int) -> str:
    if n <= 0:
        return "GRIS"
    tercio = max(1, n // 3)
    if rank <= tercio:
        return "VERDE"
    if rank <= 2 * tercio:
        return "AMARILLO"
    return "ROJO"
