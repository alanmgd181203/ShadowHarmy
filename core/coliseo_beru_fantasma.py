"""Beru Fantasma v2 — Coliseo: cazador + negociador + ciclo infinito.

Métrica corona: botín_neto / margen_usd (dólar de manto).
Un Beru por activo (sin fusiones/Mega). Path OHLC → latidos 0.05%.

Engorde: +$5 / 0.1% en red de frontera **sin techo artificial** (doctrina Monarca
2026-07-18). Único límite en vivo = oxígeno Tusk; en teatro = el propio movimiento.

Contabilidad (Monarca 2026-07-18 — corrección):
  Beru transmuta dólares secos de la **masa** spot del manto (una pierna tapa a la otra).
  Fee = fee_pct × masa × 2 (ida/vuelta sobre esa plata), **no** sobre nocional $5k de Igris.
  Botín = masa × (movimiento / 0.1%) — doctrina +$5/0.1% por capa, sin pasar por $5000.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Literal

PathPolicy = Literal["ohlc", "olhc", "min"]

# Defaults doctrina / Coliseo
STEP_LATIDO = 0.0005          # 0.05%
PASO_TRAILING = 0.001         # 0.1%
PASO_OZ_NEG = 0.001           # 0.1%
PASO_RED_NEG = 0.0005         # 0.05% (toques 2–5)
CLON_RED = 0.001              # 0.1% inicial
MORDIDA_USD = 5.0             # +$5 por escalón; engorde libre (sin tope $50)
FEE_PCT = 0.001               # 0.1% por pierna — sobre masa spot, no nocional Igris
PESOS_CALOR = (0.20, 0.50, 0.30)  # día / semana / año


def expand_to_latidos(
    open_: float,
    high: float,
    low: float,
    close: float,
    *,
    step_pct: float = STEP_LATIDO,
    order: Literal["ohlc", "olhc"] = "ohlc",
) -> list[float]:
    if open_ <= 0:
        return []
    waypoints = [open_, high, low, close] if order == "ohlc" else [open_, low, high, close]
    out: list[float] = [float(waypoints[0])]
    for target in waypoints[1:]:
        cur = out[-1]
        target = float(target)
        if cur <= 0 or target <= 0:
            continue
        if abs(target - cur) / cur < step_pct * 0.5:
            out.append(target)
            continue
        direction = 1.0 if target >= cur else -1.0
        px = cur
        guard = 0
        while guard < 100_000:
            guard += 1
            nxt = px * (1.0 + direction * step_pct)
            if (direction > 0 and nxt >= target) or (direction < 0 and nxt <= target):
                out.append(target)
                break
            out.append(nxt)
            px = nxt
    return out


def apply_slip(px: float, lado: str, slip_bps: float) -> float:
    """Empeora el fill: compra más caro / venta más barata."""
    if slip_bps <= 0 or px <= 0:
        return px
    s = slip_bps / 10_000.0
    # lado up (mean-reversion short-ish harvest): fill peor
    if lado == "up":
        return px * (1.0 - s)  # cosecha bajista: vendemos peor (más bajo)
    return px * (1.0 + s)


@dataclass
class FantasmaResult:
    activo: str
    vacio_pct: float
    cosechas: int = 0
    toques_neg: int = 0
    ciclos_infinito: int = 0
    botin_bruto: float = 0.0
    fees: float = 0.0
    botin_neto: float = 0.0
    margen_usd: float = 0.0
    eficiencia: float = 0.0
    latidos: int = 0
    path_policy: str = "min"
    modo_final: str = ""


@dataclass
class _St:
    centro: float
    modo: str = "espera"
    # espera | caza_real | negociador | esperando_abismo | caza_fantasma
    lado: str = ""  # up | down — lado del breakout / caza
    oz: float = 0.0
    red: float = 0.0
    masa: float = 0.0
    entry: float = 0.0
    ancla: float = 0.0  # precio oz de primera cosecha
    oz_cond: float = 0.0
    neg_toques: int = 0
    masa_congelada: bool = False


def _cobrar(
    *,
    entry: float,
    exit_px: float,
    masa: float,
    fee_pct: float,
    paso_trailing: float = PASO_TRAILING,
) -> tuple[float, float]:
    """Botín y fee sobre dólares secos de la masa Beru (no nocional Igris).

    - Botín: masa × (Δprecio / paso_trailing) → $5 por cada 0.1% si masa=$5.
    - Fee: fee_pct × masa × 2 (entrada+salida spot sobre esa masa).
    """
    if entry <= 0 or masa <= 0 or paso_trailing <= 0:
        return 0.0, 0.0
    move = abs(exit_px - entry) / entry
    pnl = masa * (move / paso_trailing)
    fee = masa * fee_pct * 2.0
    return pnl, fee


def simular_beru_fantasma(
    precios: Iterable[float],
    *,
    activo: str = "?",
    vacio: float = 0.016,
    margen_usd: float = 12.5,
    fee_pct: float = FEE_PCT,
    paso_trailing: float = PASO_TRAILING,
    clon_red: float = CLON_RED,
    mordida_usd: float = MORDIDA_USD,
    notional_por_pierna: float | None = None,  # legacy ignorado (era el bug Igris)
    slip_bps: float = 0.0,
    abismo: float | None = None,
) -> FantasmaResult:
    """Beru al 100% (un barco): caza real → negociador → ciclo infinito.

    abismo: distancia del negociador; default = vacio (misma perilla Adán).
    Gatillo primera caza: ± vacío/2 desde el centro del manto.
    """
    _ = notional_por_pierna  # no usar: fee/botín van por masa spot
    gatillo = vacio * 0.5
    ab = float(abismo) if abismo is not None else float(vacio)

    st: _St | None = None
    cosechas = 0
    toques_neg = 0
    ciclos = 0
    bruto = 0.0
    fees = 0.0
    n = 0

    def _arm_caza(px: float, lado: str, engorde: bool) -> _St:
        assert st is not None
        masa = mordida_usd if engorde else (st.masa if st.masa > 0 else mordida_usd)
        if lado == "up":
            return _St(
                centro=st.centro,
                modo="caza_real" if engorde else "caza_fantasma",
                lado="up",
                entry=px,
                masa=masa,
                oz=px * (1.0 - paso_trailing),
                red=px * (1.0 + clon_red),
                masa_congelada=not engorde,
                ancla=st.ancla,
                oz_cond=st.oz_cond,
                neg_toques=0,
            )
        return _St(
            centro=st.centro,
            modo="caza_real" if engorde else "caza_fantasma",
            lado="down",
            entry=px,
            masa=masa,
            oz=px * (1.0 + paso_trailing),
            red=px * (1.0 - clon_red),
            masa_congelada=not engorde,
            ancla=st.ancla,
            oz_cond=st.oz_cond,
            neg_toques=0,
        )

    def _entrar_negociador(px: float, ancla_px: float, lado: str, masa: float) -> _St:
        # oz condicional = ancla ± abismo hacia el 0 (centro)
        if lado == "up":
            # caza arriba: ancla bajo el pico; condicional más abajo (abismo)
            oz_cond = ancla_px * (1.0 - ab)
            oz_n = oz_cond * (1.0 - PASO_OZ_NEG)
            red_n = oz_cond * (1.0 + PASO_OZ_NEG)  # red más cerca del 0
        else:
            oz_cond = ancla_px * (1.0 + ab)
            oz_n = oz_cond * (1.0 + PASO_OZ_NEG)
            red_n = oz_cond * (1.0 - PASO_OZ_NEG)
        return _St(
            centro=st.centro if st else px,
            modo="negociador",
            lado=lado,
            oz=oz_n,
            red=red_n,
            masa=masa,
            entry=ancla_px,
            ancla=ancla_px,
            oz_cond=oz_cond,
            neg_toques=1,
            masa_congelada=True,
        )

    for raw in precios:
        if raw <= 0:
            continue
        n += 1
        if st is None:
            st = _St(centro=raw)
            continue

        px = raw

        # --- ESPERA: primer gatillo o re-gatillo tras abismo ---
        if st.modo == "espera":
            up = st.centro * (1.0 + gatillo)
            dn = st.centro * (1.0 - gatillo)
            if px >= up:
                st = _arm_caza(px, "up", engorde=True)
            elif px <= dn:
                st = _arm_caza(px, "down", engorde=True)
            continue

        if st.modo == "esperando_abismo":
            up = st.centro * (1.0 + gatillo)
            dn = st.centro * (1.0 - gatillo)
            # Tras red negociador: buscar gatillo del lado opuesto al último neg
            if st.lado == "up" and px >= up:
                st = _arm_caza(px, "up", engorde=False)
                ciclos += 1
            elif st.lado == "down" and px <= dn:
                st = _arm_caza(px, "down", engorde=False)
                ciclos += 1
            elif st.lado == "up" and px <= dn:
                st = _arm_caza(px, "down", engorde=False)
                ciclos += 1
            elif st.lado == "down" and px >= up:
                st = _arm_caza(px, "up", engorde=False)
                ciclos += 1
            continue

        # --- CAZA REAL / FANTASMA ---
        if st.modo in ("caza_real", "caza_fantasma"):
            engorde = st.modo == "caza_real" and not st.masa_congelada
            if st.lado == "up":
                if engorde and px >= st.red:
                    st.masa += mordida_usd
                    st.red = px * (1.0 + paso_trailing)
                    st.oz = px * (1.0 - paso_trailing)
                elif px <= st.oz:
                    fill = apply_slip(px, "up", slip_bps)
                    pnl, fee = _cobrar(
                        entry=st.entry,
                        exit_px=fill,
                        masa=st.masa,
                        fee_pct=fee_pct,
                        paso_trailing=paso_trailing,
                    )
                    bruto += pnl
                    fees += fee
                    cosechas += 1
                    if st.modo == "caza_real":
                        st = _entrar_negociador(fill, fill, "up", st.masa)
                    else:
                        # fantasma → otra vez negociador, masa congelada
                        st = _entrar_negociador(fill, fill, "up", st.masa)
            else:
                if engorde and px <= st.red:
                    st.masa += mordida_usd
                    st.red = px * (1.0 - paso_trailing)
                    st.oz = px * (1.0 + paso_trailing)
                elif px >= st.oz:
                    fill = apply_slip(px, "down", slip_bps)
                    pnl, fee = _cobrar(
                        entry=st.entry,
                        exit_px=fill,
                        masa=st.masa,
                        fee_pct=fee_pct,
                        paso_trailing=paso_trailing,
                    )
                    bruto += pnl
                    fees += fee
                    cosechas += 1
                    if st.modo == "caza_real":
                        st = _entrar_negociador(fill, fill, "down", st.masa)
                    else:
                        st = _entrar_negociador(fill, fill, "down", st.masa)
            continue

        # --- NEGOCIADOR ---
        if st.modo == "negociador":
            # toque oz = cosecha negociador (sin engorde)
            toque_oz = (st.lado == "up" and px <= st.oz) or (st.lado == "down" and px >= st.oz)
            toque_red = (st.lado == "up" and px >= st.red) or (st.lado == "down" and px <= st.red)

            if toque_oz:
                fill = apply_slip(px, st.lado, slip_bps)
                pnl, fee = _cobrar(
                    entry=st.entry,
                    exit_px=fill,
                    masa=st.masa,
                    fee_pct=fee_pct,
                    paso_trailing=paso_trailing,
                )
                bruto += pnl
                fees += fee
                cosechas += 1
                toques_neg += 1
                st.neg_toques += 1
                st.entry = fill
                # avanzar grid
                if st.neg_toques >= 6:
                    # resorte: red cerca de oz_cond, oz extra
                    if st.lado == "up":
                        st.red = st.oz_cond * (1.0 - PASO_OZ_NEG)
                        st.oz = st.oz * (1.0 - PASO_OZ_NEG)
                    else:
                        st.red = st.oz_cond * (1.0 + PASO_OZ_NEG)
                        st.oz = st.oz * (1.0 + PASO_OZ_NEG)
                    st.neg_toques = 0
                elif st.neg_toques == 1:
                    pass  # ya armado en entrada
                else:
                    # toques 2–5: oz 0.1%, red 0.05%
                    if st.lado == "up":
                        st.oz = fill * (1.0 - PASO_OZ_NEG)
                        st.red = fill * (1.0 + PASO_RED_NEG)
                    else:
                        st.oz = fill * (1.0 + PASO_OZ_NEG)
                        st.red = fill * (1.0 - PASO_RED_NEG)
            elif toque_red:
                # red negociador → esperando abismo / re-gatillo (ciclo infinito)
                toques_neg += 1
                st.modo = "esperando_abismo"
                # centro se mantiene (manto); lado indica de dónde venimos
            continue

    neto = bruto - fees
    efi = (neto / margen_usd) if margen_usd > 0 else 0.0
    return FantasmaResult(
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
        modo_final=(st.modo if st else ""),
    )


def _latidos_velas(
    candles: list[tuple[int, float, float, float, float]],
    order: Literal["ohlc", "olhc"],
    step_pct: float,
) -> list[float]:
    out: list[float] = []
    for _ts, o, h, l, c in candles:
        chunk = expand_to_latidos(o, h, l, c, step_pct=step_pct, order=order)
        if out and chunk and abs(chunk[0] - out[-1]) < 1e-12 * max(1.0, abs(out[-1])):
            out.extend(chunk[1:])
        else:
            out.extend(chunk)
    return out


def simular_desde_velas(
    candles: list[tuple[int, float, float, float, float]],
    *,
    path_policy: PathPolicy = "min",
    step_pct: float = STEP_LATIDO,
    **kwargs,
) -> FantasmaResult:
    if path_policy == "ohlc":
        r = simular_beru_fantasma(_latidos_velas(candles, "ohlc", step_pct), **kwargs)
        r.path_policy = "ohlc"
        return r
    if path_policy == "olhc":
        r = simular_beru_fantasma(_latidos_velas(candles, "olhc", step_pct), **kwargs)
        r.path_policy = "olhc"
        return r
    a = simular_beru_fantasma(_latidos_velas(candles, "ohlc", step_pct), **kwargs)
    b = simular_beru_fantasma(_latidos_velas(candles, "olhc", step_pct), **kwargs)
    elegido = a if a.eficiencia <= b.eficiencia else b
    elegido.path_policy = "min"
    elegido.latidos = max(a.latidos, b.latidos)
    return elegido


def calor_eficiencia(
    efi_dia: float | None,
    efi_semana: float | None,
    efi_anio: float | None,
    *,
    pesos: tuple[float, float, float] = PESOS_CALOR,
) -> float:
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


VACIOS_BARRIDO_DEFAULT = (0.008, 0.010, 0.012, 0.014, 0.016, 0.018, 0.020)  # 0.8%…2.0% — sin 0.6%
