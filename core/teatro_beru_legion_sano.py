"""FÓSIL — teatro de la legión Beru anterior; no usar para juicios nuevos.

La doctrina 2026-08-15 extirpó negociador, capas, residual, fusión y Mega.
El actor canónico es ``core.teatro_beru_sano``: un cazador continuo por Santo.
Este módulo queda únicamente para auditar resultados históricos.

Segunda arena del juicio:

- varios cazadores nacen desde las Redes residuales;
- solo la frontera extrema engorda;
- cada Hoz pasa a ping-pong de una carta;
- cartas iguales fusionan masa;
- negociadores bajo su promedio forman Mega;
- Mega cobra, purga y deja una semilla con el mismo 0 del manto.

No importa al Coliseo-legión de julio: ese actor conserva sangre por vacío,
acordeón y reset del cero. Aquí se reutilizan únicamente las leyes puras del
cazador sano y la expansión neutral de velas spot.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Literal

from core import beru_cazador as cazador
from core.teatro_beru_sano import STEP_LATIDO, expand_to_latidos

# Geometría histórica del fósil. No seguir el Vacío vivo 1.1.
SANGRE_FOSIL_PCT = 0.009
HOZ_FOSIL_PCT = 0.008

PathPolicy = Literal["ohlc", "olhc", "min"]
FUSION_EPS_PCT = 0.0001
MAX_BERUS_DEFAULT = 300


@dataclass
class LegionSanaResult:
    activo: str
    grado: str
    abismo_pct: float
    sangre_pct: float
    hoz_pct: float
    centro_manto: float
    centro_fuente: str
    cosechas_caza: int = 0
    cosechas_negociador: int = 0
    engordes: int = 0
    ciclos_pingpong: int = 0
    berus_creados: int = 0
    berus_vivos_max: int = 0
    capas: int = 0
    fusiones_carta: int = 0
    megas_creados: int = 0
    mega_fusiones: int = 0
    purgas_mega: int = 0
    tope_berus_hits: int = 0
    masa_total_max_usd: float = 0.0
    botin_bruto: float = 0.0
    fees: float = 0.0
    slippage: float = 0.0
    botin_neto: float = 0.0
    margen_manto_ls_usd: float = 0.0
    eficiencia: float = 0.0
    latidos: int = 0
    path_policy: str = "stream"
    modos_finales: dict[str, int] | None = None


@dataclass
class _Barco:
    uid: str
    modo: str = "ACECHANDO"  # ACECHANDO | CAZA | NEGOCIADOR
    direccion: str = ""
    entry: float = 0.0
    masa: float = 0.0
    oz_pct: float = 0.0
    red_pct: float = 0.0
    oro_pct: float = 0.0
    capa: int = 1
    piso_sangre_pct: float = 0.0
    es_mega: bool = False


@dataclass
class _Residual:
    red_pct: float
    direccion: str
    capa_origen: int


def _oro_opuesto(ancla_pct: float, abismo: float) -> float:
    if ancla_pct > 0:
        return ancla_pct - abismo
    if ancla_pct < 0:
        return ancla_pct + abismo
    return -abismo


def sangre_post_purga_pct(pct_purga: float) -> float:
    """Nueva sangre absoluta; conserva el 0 de Igris."""
    signo = 1 if pct_purga >= 0 else -1
    return signo * (abs(pct_purga) + SANGRE_FOSIL_PCT)


def _toca_nivel(touch_pct: float, nivel_pct: float) -> bool:
    if nivel_pct < 0:
        return touch_pct <= nivel_pct + 1e-12
    return touch_pct >= nivel_pct - 1e-12


def _cobrar(
    *,
    entry: float,
    exit_px: float,
    masa: float,
    fee_pct: float,
    slip_bps: float,
) -> tuple[float, float, float]:
    if entry <= 0 or exit_px <= 0 or masa <= 0:
        return 0.0, 0.0, 0.0
    movimiento = abs(exit_px - entry) / entry
    bruto = masa * (movimiento / max(cazador.paso_pct(), 1e-12))
    fee = masa * max(0.0, fee_pct) * 2.0
    slip = masa * max(0.0, slip_bps) / 10_000.0 * 2.0
    return bruto, fee, slip


def _target_carta(b: _Barco) -> float:
    if b.modo == "NEGOCIADOR":
        return b.oro_pct
    if b.modo == "CAZA":
        return b.oz_pct
    return 0.0


def _promedio_ponderado(barcos: list[_Barco], atributo: str) -> float:
    total = sum(max(0.0, b.masa) for b in barcos)
    if total <= 0:
        return 0.0
    return sum(float(getattr(b, atributo)) * max(0.0, b.masa) for b in barcos) / total


def _fusionar_misma_carta(barcos: list[_Barco]) -> tuple[list[_Barco], int]:
    """Une cartas iguales de la misma dirección; nunca mezcla lados."""
    activos = [b for b in barcos if b.modo in {"CAZA", "NEGOCIADOR"} and _target_carta(b) != 0]
    usados: set[str] = set()
    victimas: set[str] = set()
    fusiones = 0
    for i, primero in enumerate(activos):
        if primero.uid in usados:
            continue
        target = _target_carta(primero)
        grupo = [primero]
        for otro in activos[i + 1:]:
            if otro.uid in usados or otro.direccion != primero.direccion:
                continue
            if abs(_target_carta(otro) - target) <= FUSION_EPS_PCT + 1e-12:
                grupo.append(otro)
        if len(grupo) < 2:
            continue
        for b in grupo:
            usados.add(b.uid)
        # Si una carta ya negocia, ella conduce la fusión.
        lider = next((b for b in grupo if b.modo == "NEGOCIADOR"), max(grupo, key=lambda x: x.masa))
        masa_total = sum(b.masa for b in grupo)
        entry = _promedio_ponderado(grupo, "entry")
        carta = sum(_target_carta(b) * b.masa for b in grupo) / max(masa_total, 1e-12)
        lider.masa = masa_total
        lider.entry = entry
        lider.es_mega = any(b.es_mega for b in grupo)
        if any(b.modo == "NEGOCIADOR" for b in grupo):
            lider.modo = "NEGOCIADOR"
            lider.oro_pct = carta
            lider.oz_pct = lider.red_pct = 0.0
        else:
            lider.oz_pct = carta
            lider.red_pct = _promedio_ponderado(grupo, "red_pct")
        victimas.update(b.uid for b in grupo if b is not lider)
        fusiones += 1
    return [b for b in barcos if b.uid not in victimas], fusiones


def _bajo_promedio(ancla: float, promedio: float) -> bool:
    if promedio >= 0 and ancla >= 0:
        return ancla < promedio - 1e-12
    if promedio <= 0 and ancla <= 0:
        return ancla > promedio + 1e-12
    return ancla < promedio - 1e-12


def _crear_megas(barcos: list[_Barco]) -> tuple[list[_Barco], int]:
    """Promedio por dirección; dos o más rezagados se vuelven un Mega."""
    victimas: set[str] = set()
    creados = 0
    for direccion in ("SHORT", "LONG"):
        grupo = [
            b for b in barcos
            if b.modo == "NEGOCIADOR" and b.direccion == direccion and not b.es_mega
        ]
        if len(grupo) < 3:
            continue
        promedio = sum(b.oro_pct for b in grupo) / len(grupo)
        debajo = [b for b in grupo if _bajo_promedio(b.oro_pct, promedio)]
        if len(debajo) < 2:
            continue
        lider = max(debajo, key=lambda b: b.masa)
        entry = _promedio_ponderado(debajo, "entry")
        lider.masa = sum(b.masa for b in debajo)
        lider.entry = entry
        lider.oro_pct = promedio  # el promedio ya es el llamado Mega
        lider.es_mega = True
        victimas.update(b.uid for b in debajo if b is not lider)
        creados += 1
    return [b for b in barcos if b.uid not in victimas], creados


def _fusionar_megas(barcos: list[_Barco]) -> tuple[list[_Barco], int]:
    """Mega arriba + Mega abajo en la misma carta → una sola negociación."""
    megas = [b for b in barcos if b.modo == "NEGOCIADOR" and b.es_mega]
    if len(megas) < 2:
        return barcos, 0
    for i, a in enumerate(megas):
        for b in megas[i + 1:]:
            if abs(a.oro_pct - b.oro_pct) > FUSION_EPS_PCT + 1e-12:
                continue
            grupo = [a, b]
            lider = max(grupo, key=lambda x: x.masa)
            victima = b if lider is a else a
            entry = _promedio_ponderado(grupo, "entry")
            oro = _promedio_ponderado(grupo, "oro_pct")
            masa = a.masa + b.masa
            lider.entry = entry
            lider.oro_pct = oro
            lider.masa = masa
            lider.direccion = "SHORT" if lider.oro_pct > 0 else "LONG"
            return [x for x in barcos if x.uid != victima.uid], 1
    return barcos, 0


def simular_legion_sana(
    precios: Iterable[float],
    *,
    activo: str = "?",
    grado: str = "MARISCAL",
    abismo: float = 0.016,
    margen_manto_ls_usd: float = 12.5,
    fee_pct: float = 0.001,
    slip_bps: float = 0.0,
    centro_manto: float | None = None,
    masa_inicial_usd: float | None = None,
    engorde_paso_usd: float | None = None,
    max_berus: int = MAX_BERUS_DEFAULT,
) -> LegionSanaResult:
    act = str(activo or "?").upper()
    grado_u = str(grado or "MARISCAL").upper()
    ab = max(0.0, float(abismo or 0.0))
    centro_fijo = float(centro_manto or 0.0)
    centro_fuente = "manto_explicito" if centro_fijo > 0 else "primera_vela_proxy_manto"
    masa_inicial = (
        float(masa_inicial_usd) if masa_inicial_usd is not None
        else float(cazador.capa1_masa_usd(0.0, act, grado_u))
    )
    mordida = (
        float(engorde_paso_usd) if engorde_paso_usd is not None
        else float(cazador.engorde_paso_usd(act, grado_u))
    )
    max_b = max(2, int(max_berus))

    barcos: list[_Barco] = []
    residuales: list[_Residual] = []
    centro = centro_fijo
    siguiente_id = 1
    bruto = fees = slippage = 0.0
    caza = negociaciones = engordes = pingpong = 0
    creados = vivos_max = capas = fusiones = megas = mega_fusiones = purgas = tope_hits = 0
    masa_total_max = 0.0
    latidos = 0

    def nuevo_uid(prefijo: str = "B") -> str:
        nonlocal siguiente_id
        uid = f"{prefijo}{siguiente_id}"
        siguiente_id += 1
        return uid

    def cobrar_barco(b: _Barco, px: float) -> None:
        nonlocal bruto, fees, slippage
        ganancia, fee, slip = _cobrar(
            entry=b.entry, exit_px=px, masa=b.masa,
            fee_pct=fee_pct, slip_bps=slip_bps,
        )
        bruto += ganancia
        fees += fee
        slippage += slip

    def armar_caza(b: _Barco, px: float, touch: float) -> None:
        b.modo = "CAZA"
        b.direccion = "SHORT" if touch > 0 else "LONG"
        b.entry = px
        b.masa = max(0.0, masa_inicial)
        b.oz_pct, b.red_pct = cazador.niveles_desde_toque(touch)
        b.oro_pct = 0.0
        b.piso_sangre_pct = 0.0

    for raw in precios:
        px = float(raw or 0.0)
        if px <= 0:
            continue
        latidos += 1
        if centro <= 0:
            centro = px
            barcos.append(_Barco(uid=nuevo_uid("S")))
            creados = capas = vivos_max = 1
        touch = cazador.pct_desde_precio(centro, px)
        armados_ahora: set[str] = set()

        # Redes residuales paren nuevas capas.
        pendientes: list[_Residual] = []
        for residual in residuales:
            toca = (
                (residual.direccion == "SHORT" and touch >= residual.red_pct - 1e-12)
                or (residual.direccion == "LONG" and touch <= residual.red_pct + 1e-12)
            )
            if not toca:
                pendientes.append(residual)
                continue
            if len(barcos) >= max_b:
                tope_hits += 1
                pendientes.append(residual)
                continue
            nuevo = _Barco(
                uid=nuevo_uid("C"),
                capa=residual.capa_origen + 1,
            )
            armar_caza(nuevo, px, touch)
            barcos.append(nuevo)
            armados_ahora.add(nuevo.uid)
            creados += 1
            capas = max(capas, nuevo.capa)
        residuales = pendientes

        # Semillas normales y post-Mega.
        for b in list(barcos):
            if b.modo != "ACECHANDO":
                continue
            piso = b.piso_sangre_pct
            if piso:
                listo = abs(touch) >= abs(piso) - 1e-12 and (
                    (piso > 0 and touch > 0) or (piso < 0 and touch < 0)
                )
            else:
                listo = cazador.toca_llamado_sangre(touch)
            if listo:
                armar_caza(b, px, touch)
                armados_ahora.add(b.uid)

        # Solo el cazador con Red más extrema por lado engorda.
        cazadores = [b for b in barcos if b.modo == "CAZA"]
        frontera: dict[str, _Barco] = {}
        for direccion in ("SHORT", "LONG"):
            grupo = [b for b in cazadores if b.direccion == direccion]
            if grupo:
                frontera[direccion] = (
                    max(grupo, key=lambda b: b.red_pct)
                    if direccion == "SHORT"
                    else min(grupo, key=lambda b: b.red_pct)
                )

        for b in list(barcos):
            if b.modo == "CAZA":
                if b.uid in armados_ahora:
                    continue  # sangre/residual solo detona; cero fill o engorde
                oz_px, red_px = cazador.sincronizar_precios_grid(centro, b.oz_pct, b.red_pct)
                if cazador.toca_oz(px, b.direccion, oz_px):
                    cobrar_barco(b, px)
                    caza += 1
                    residuales.append(_Residual(b.red_pct, b.direccion, b.capa))
                    b.entry = px
                    b.oro_pct = _oro_opuesto(b.oz_pct, ab)
                    b.oz_pct = b.red_pct = 0.0
                    b.modo = "NEGOCIADOR"
                elif frontera.get(b.direccion) is b and cazador.toca_red(px, b.direccion, red_px):
                    b.masa += max(0.0, mordida)
                    b.oz_pct, b.red_pct = cazador.mover_niveles_cazador(
                        b.direccion, b.oz_pct, b.red_pct,
                    )
                    engordes += 1
                continue

            if b.modo != "NEGOCIADOR" or not _toca_nivel(touch, b.oro_pct):
                continue
            cobrar_barco(b, px)
            negociaciones += 1
            if b.es_mega:
                # Purga: masa vuelve a bóveda; nace cazador sin mover el 0.
                barcos.remove(b)
                piso = sangre_post_purga_pct(touch)
                if len(barcos) < max_b:
                    barcos.append(_Barco(
                        uid=nuevo_uid("P"),
                        direccion=b.direccion,
                        capa=b.capa + 1,
                        piso_sangre_pct=piso,
                    ))
                    creados += 1
                    capas = max(capas, b.capa + 1)
                else:
                    tope_hits += 1
                purgas += 1
            else:
                b.entry = px
                b.oro_pct = _oro_opuesto(b.oro_pct, ab)
                pingpong += 1

        barcos, n = _fusionar_misma_carta(barcos)
        fusiones += n
        barcos, n = _crear_megas(barcos)
        megas += n
        barcos, n = _fusionar_megas(barcos)
        mega_fusiones += n

        vivos_max = max(vivos_max, len(barcos))
        masa_total_max = max(masa_total_max, sum(max(0.0, b.masa) for b in barcos))

    neto = bruto - fees - slippage
    margen = max(0.0, float(margen_manto_ls_usd or 0.0))
    modos: dict[str, int] = {}
    for b in barcos:
        etiqueta = "MEGA" if b.es_mega else b.modo
        modos[etiqueta] = modos.get(etiqueta, 0) + 1
    return LegionSanaResult(
        activo=act,
        grado=grado_u,
        abismo_pct=round(ab * 100.0, 6),
        sangre_pct=round(SANGRE_FOSIL_PCT * 100.0, 6),
        hoz_pct=round(HOZ_FOSIL_PCT * 100.0, 6),
        centro_manto=round(centro, 12),
        centro_fuente=centro_fuente,
        cosechas_caza=caza,
        cosechas_negociador=negociaciones,
        engordes=engordes,
        ciclos_pingpong=pingpong,
        berus_creados=creados,
        berus_vivos_max=vivos_max,
        capas=capas,
        fusiones_carta=fusiones,
        megas_creados=megas,
        mega_fusiones=mega_fusiones,
        purgas_mega=purgas,
        tope_berus_hits=tope_hits,
        masa_total_max_usd=round(masa_total_max, 6),
        botin_bruto=round(bruto, 6),
        fees=round(fees, 6),
        slippage=round(slippage, 6),
        botin_neto=round(neto, 6),
        margen_manto_ls_usd=round(margen, 6),
        eficiencia=round(neto / margen, 6) if margen > 0 else 0.0,
        latidos=latidos,
        modos_finales=modos,
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


def simular_legion_desde_velas(
    candles: list[tuple[int, float, float, float, float]],
    *,
    path_policy: PathPolicy = "min",
    step_pct: float = STEP_LATIDO,
    **kwargs,
) -> LegionSanaResult:
    if path_policy in ("ohlc", "olhc"):
        r = simular_legion_sana(_latidos_velas(candles, path_policy, step_pct), **kwargs)
        r.path_policy = path_policy
        return r
    a = simular_legion_sana(_latidos_velas(candles, "ohlc", step_pct), **kwargs)
    b = simular_legion_sana(_latidos_velas(candles, "olhc", step_pct), **kwargs)
    elegido = a if a.eficiencia <= b.eficiencia else b
    elegido.path_policy = "min"
    elegido.latidos = max(a.latidos, b.latidos)
    return elegido
