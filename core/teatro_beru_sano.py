"""FÓSIL BLOQUEADO — teatro del mismo Beru + Vacío 1.6 tras cada Hoz.

Actor aislado, sin Bridge ni manos:

- 0 absoluto = manto Igris (explícito o primera vela como proxy).
- Primera vida: sangre ±0.9% y Hoz ±0.8%.
- Después de cada Hoz: 0 local = fill; llamado a ±vacío Adán y Hoz 0.1% atrás.
- Masa = recorrido hasta Hoz × engorde del grado; Red suma otro peldaño.
- Hoz transmuta toda la masa y reinicia el tramo.

Fue útil para la cirugía continua del 2026-08-15, pero ya no representa el
relevo puro desde la última Red tocada. No puede coronar Santos.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Literal

from core import beru_cazador as cazador

PathPolicy = Literal["ohlc", "olhc", "min"]

STEP_LATIDO = 0.0005
FEE_PCT = 0.001
FOSIL_BLOQUEADO = True


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
    out = [float(waypoints[0])]
    for target_raw in waypoints[1:]:
        target = float(target_raw)
        cur = out[-1]
        if cur <= 0 or target <= 0:
            continue
        if abs(target - cur) / cur < step_pct * 0.5:
            out.append(target)
            continue
        direccion = 1.0 if target >= cur else -1.0
        px = cur
        for _ in range(100_000):
            nxt = px * (1.0 + direccion * step_pct)
            if (direccion > 0 and nxt >= target) or (direccion < 0 and nxt <= target):
                out.append(target)
                break
            out.append(nxt)
            px = nxt
    return out


@dataclass
class TeatroBeruResult:
    activo: str
    grado: str
    abismo_pct: float
    sangre_pct: float
    hoz_pct: float
    centro_manto: float
    centro_fuente: str
    cosechas_caza: int = 0
    cosechas_continuas: int = 0
    cosechas_negociador: int = 0
    engordes: int = 0
    ciclos_pingpong: int = 0
    tramos_primera_sangre: int = 0
    tramos_vacio_adan: int = 0
    masa_total_transmutada_usd: float = 0.0
    botin_bruto: float = 0.0
    fees: float = 0.0
    slippage: float = 0.0
    botin_neto: float = 0.0
    margen_manto_ls_usd: float = 0.0
    eficiencia: float = 0.0
    masa_max_usd: float = 0.0
    latidos: int = 0
    path_policy: str = "stream"
    modo_final: str = ""
    ancla_tramo_final: float = 0.0


@dataclass
class _Actor:
    centro_manto: float
    ancla_tramo: float
    modo: str = "ACECHANDO"
    direccion: str = ""
    masa: float = 0.0
    oz_pct: float = 0.0
    red_pct: float = 0.0
    cosechas: int = 0


def _distancias(st: _Actor, abismo: float) -> tuple[float, float]:
    llamado = cazador.llamado_sangre_pct() if st.cosechas == 0 else abismo
    hoz = max(cazador.paso_pct(), llamado - cazador.paso_pct())
    return llamado, hoz


def _cobrar_masa(
    masa: float,
    *,
    fee_pct: float,
    slip_bps: float,
) -> tuple[float, float, float]:
    """El botín es el recorrido del manto que Beru acaba de transmutar."""
    m = max(0.0, float(masa or 0))
    fee = m * max(0.0, float(fee_pct)) * 2.0
    slip = m * max(0.0, float(slip_bps)) / 10_000.0 * 2.0
    return m, fee, slip


def simular_beru_sano(
    precios: Iterable[float],
    *,
    activo: str = "?",
    grado: str = "MARISCAL",
    abismo: float = 0.016,
    margen_manto_ls_usd: float = 12.5,
    fee_pct: float = FEE_PCT,
    slip_bps: float = 0.0,
    centro_manto: float | None = None,
    masa_inicial_usd: float | None = None,
    engorde_paso_usd: float | None = None,
) -> TeatroBeruResult:
    """Bloqueado: validaba el tumor mismo-Beru + Vacío desde fill."""
    raise RuntimeError(
        "FOSIL_BLOQUEADO: usa el altar/relevo cazador; "
        "este teatro reiniciaba al mismo Beru desde la Hoz"
    )
    act = str(activo or "?").upper()
    grado_u = str(grado or "MARISCAL").upper()
    ab = max(cazador.paso_pct(), float(abismo or 0.0))
    centro_fijo = float(centro_manto or 0.0)
    fuente_centro = "manto_explicito" if centro_fijo > 0 else "primera_vela_proxy_manto"
    mordida = (
        float(engorde_paso_usd)
        if engorde_paso_usd is not None
        else float(cazador.engorde_paso_usd(act, grado_u))
    )

    st: _Actor | None = None
    cosechas = engordes = tramos_sangre = tramos_vacio = latidos = 0
    bruto = fees = slippage = masa_max = masa_total = 0.0

    for raw in precios:
        px = float(raw or 0.0)
        if px <= 0:
            continue
        latidos += 1
        if st is None:
            centro = centro_fijo if centro_fijo > 0 else px
            st = _Actor(centro_manto=centro, ancla_tramo=centro)

        touch = cazador.pct_desde_precio(st.ancla_tramo, px)
        llamado, hoz = _distancias(st, ab)

        if st.modo == "ACECHANDO":
            if abs(touch) + 1e-12 < llamado:
                continue
            signo = 1 if touch > 0 else -1
            st.direccion = "SHORT" if signo > 0 else "LONG"
            st.oz_pct = signo * hoz
            # El llamado ya fue tocado: la primera Red queda 0.1% más afuera.
            st.red_pct = signo * (llamado + cazador.paso_pct())
            if st.cosechas == 0 and masa_inicial_usd is not None:
                st.masa = max(0.0, float(masa_inicial_usd))
            else:
                st.masa = max(0.0, mordida * (hoz / max(cazador.paso_pct(), 1e-12)))
            masa_max = max(masa_max, st.masa)
            st.modo = "CAZA"
            if st.cosechas == 0:
                tramos_sangre += 1
            else:
                tramos_vacio += 1
            continue

        oz_px, red_px = cazador.sincronizar_precios_grid(
            st.ancla_tramo, st.oz_pct, st.red_pct,
        )
        if cazador.toca_oz(px, st.direccion, oz_px):
            b, f, slip = _cobrar_masa(
                st.masa, fee_pct=fee_pct, slip_bps=slip_bps,
            )
            bruto += b
            fees += f
            slippage += slip
            masa_total += st.masa
            cosechas += 1
            st.cosechas += 1
            st.ancla_tramo = px
            st.modo = "ACECHANDO"
            st.direccion = ""
            st.masa = 0.0
            st.oz_pct = st.red_pct = 0.0
            continue

        if cazador.toca_red(px, st.direccion, red_px):
            st.masa += max(0.0, mordida)
            masa_max = max(masa_max, st.masa)
            engordes += 1
            st.oz_pct, st.red_pct = cazador.mover_niveles_cazador(
                st.direccion, st.oz_pct, st.red_pct,
            )

    neto = bruto - fees - slippage
    margen = max(0.0, float(margen_manto_ls_usd or 0.0))
    eficiencia = neto / margen if margen > 0 else 0.0
    centro_out = st.centro_manto if st is not None else centro_fijo
    return TeatroBeruResult(
        activo=act,
        grado=grado_u,
        abismo_pct=round(ab * 100.0, 6),
        sangre_pct=round(cazador.llamado_sangre_pct() * 100.0, 6),
        hoz_pct=round(cazador.hoz_productiva_pct() * 100.0, 6),
        centro_manto=round(centro_out, 12),
        centro_fuente=fuente_centro,
        cosechas_caza=cosechas,
        cosechas_continuas=cosechas,
        cosechas_negociador=0,
        engordes=engordes,
        ciclos_pingpong=0,
        tramos_primera_sangre=tramos_sangre,
        tramos_vacio_adan=tramos_vacio,
        masa_total_transmutada_usd=round(masa_total, 6),
        botin_bruto=round(bruto, 6),
        fees=round(fees, 6),
        slippage=round(slippage, 6),
        botin_neto=round(neto, 6),
        margen_manto_ls_usd=round(margen, 6),
        eficiencia=round(eficiencia, 6),
        masa_max_usd=round(masa_max, 6),
        latidos=latidos,
        modo_final=st.modo if st is not None else "",
        ancla_tramo_final=round(st.ancla_tramo, 12) if st is not None else 0.0,
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
) -> TeatroBeruResult:
    if path_policy in ("ohlc", "olhc"):
        r = simular_beru_sano(
            _latidos_velas(candles, path_policy, step_pct), **kwargs,
        )
        r.path_policy = path_policy
        return r
    a = simular_beru_sano(_latidos_velas(candles, "ohlc", step_pct), **kwargs)
    b = simular_beru_sano(_latidos_velas(candles, "olhc", step_pct), **kwargs)
    elegido = a if a.eficiencia <= b.eficiencia else b
    elegido.path_policy = "min"
    elegido.latidos = max(a.latidos, b.latidos)
    return elegido
