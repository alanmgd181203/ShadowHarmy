"""Teatro de sombras — 1 óptica Tank + 4 Igris de papel (una marcha cada uno).

Laboratorio pre-manos: compara fiabilidad y calidad de entrada bajo el MISMO
mercado. No toca Tusk real, no escribe marcha_despliegue.json, no es 4.0.3 live.

Óptica compartida (libros/tickers) → 4 espejos de decisión aislados.
Métricas: ¿mordió?, spread al fill, dist. al mid, espera, fees/notional, avance.
"""
from __future__ import annotations

import json
import os
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from core import igris_despliegue as ides
from core import igris_manto as im
from core import pase_director as pd

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "logs" / "teatro_sombras"

MARCHAS_TEATRO: tuple[str, ...] = ("tactico", "marcha_forzada", "asalto", "personalizado")

# personalizado de batida corta (mismo espíritu que marchas_10m)
DIAS_PERSONALIZADO_DEFAULT = 0.007


@dataclass
class ContadoresSombra:
    """Etiquetados por sombra — no se mezclan entre marchas."""

    mordidas: int = 0
    esperas: int = 0
    skips: int = 0  # semáforo ROJO / sin precio / meta llena
    sum_spread_at_fill_pct: float = 0.0
    sum_dist_mid_pct: float = 0.0
    sum_espera_s: float = 0.0
    sum_fees_usd: float = 0.0
    sum_notional_usd: float = 0.0
    avance_lote_usd: float = 0.0
    primera_mordida_s: float | None = None
    ultima_mordida_ts: float | None = None


@dataclass
class SombraIgrisPapel:
    marcha_id: str
    titulo: str
    force_market: bool
    umbral_fees_mult: float
    t0_paciencia: float
    meta_lote_usd: float
    umbrales_local: dict[str, float] = field(default_factory=dict)
    contadores: ContadoresSombra = field(default_factory=ContadoresSombra)
    ultima_decision: dict[str, Any] | None = None

    @property
    def etiqueta(self) -> str:
        return f"sombra_{self.marcha_id}"


@dataclass
class VisionCompartida:
    """Una sola cinta de mercado para las 4 sombras."""

    ts: float
    fuente: str  # orderbook | ticker | sintetico | mock
    precios: dict[str, float] = field(default_factory=dict)
    libros: dict[str, dict[str, list]] = field(default_factory=dict)
    semaforo: str = "VERDE"
    activo_foco: str = "ETH"
    activos: list[str] = field(default_factory=lambda: ["ETH"])


class TankVisionAdapter:
    """Adapta VisionCompartida a la API que espera ides.libro_tank / precio_ticker."""

    def __init__(self, vision: VisionCompartida):
        self._vision = vision
        self.libros = vision.libros
        self.precios = vision.precios
        self.nodos: list = []

    def _obtener_lider_verde(self):
        return self


def out_dir() -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    return OUT_DIR


def _escribir_json(path: Path, payload: dict[str, Any]) -> None:
    out_dir()
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    if path.exists():
        path.unlink()
    os.rename(tmp, path)


def heartbeat(msg: str, **extra: Any) -> None:
    payload = {
        "ts": time.time(),
        "iso": time.strftime("%Y-%m-%d %H:%M:%S"),
        "pid": os.getpid(),
        "msg": msg,
        **extra,
    }
    _escribir_json(out_dir() / "heartbeat.json", payload)


def vision_sintetica(
    *,
    activo: str = "ETH",
    mid: float = 3000.0,
    spread_fav_pct: float = 0.08,
    semaforo: str = "VERDE",
) -> VisionCompartida:
    """Mercado de juguete para --preparar (sin WS). spread_fav a favor del manto §E."""
    fl, fs = im.frentes_bootstrap(activo)
    half = abs(float(spread_fav_pct)) / 200.0
    # Long@Ask, Short@Bid: spread favorable ⇒ bid_short > ask_long
    # signo: positive fav edge, negative cold
    sign = 1.0 if float(spread_fav_pct) >= 0 else -1.0
    ask_l = mid * (1.0 - sign * half)
    bid_s = mid * (1.0 + sign * half)
    qty = 50_000.0
    libros = {
        fl: {"bids": [[ask_l * 0.999, qty]], "asks": [[ask_l, qty]]},
        fs: {"bids": [[bid_s, qty]], "asks": [[bid_s * 1.001, qty]]},
    }
    precios = {fl: mid, fs: mid}
    return VisionCompartida(
        ts=time.time(),
        fuente="sintetico",
        precios=precios,
        libros=libros,
        semaforo=semaforo,
        activo_foco=activo.upper(),
        activos=[activo.upper()],
    )


def vision_desde_tank(tank, *, activos: list[str] | None = None, semaforo: str = "VERDE") -> VisionCompartida:
    """Congela óptica compartida desde un Tank vivo (un solo muestreo)."""
    bases = [a.upper() for a in (activos or ["ETH"])]
    precios: dict[str, float] = {}
    libros: dict[str, dict[str, list]] = {}
    fuente = "ticker"
    for base in bases:
        fl, fs = im.frentes_bootstrap(base)
        bids_l, asks_l = ides.libro_tank(tank, fl)
        bids_s, asks_s = ides.libro_tank(tank, fs)
        if bids_l or asks_l or bids_s or asks_s:
            libros[fl] = {"bids": list(bids_l or []), "asks": list(asks_l or [])}
            libros[fs] = {"bids": list(bids_s or []), "asks": list(asks_s or [])}
            fuente = "orderbook"
        pl = ides.precio_ticker_frente(tank, fl)
        ps = ides.precio_ticker_frente(tank, fs)
        if pl > 0:
            precios[fl] = pl
        if ps > 0:
            precios[fs] = ps
        if fl not in libros and pl > 0:
            bl, al = ides.libro_sintetico_ticker(pl, 100.0, frente=fl)
            libros[fl] = {"bids": bl, "asks": al}
        if fs not in libros and ps > 0:
            bs, as_ = ides.libro_sintetico_ticker(ps, 100.0, frente=fs)
            libros[fs] = {"bids": bs, "asks": as_}
    return VisionCompartida(
        ts=time.time(),
        fuente=fuente,
        precios=precios,
        libros=libros,
        semaforo=semaforo,
        activo_foco=bases[0] if bases else "ETH",
        activos=bases,
    )


def _calibrar_personalizado_local(
    activos: list[str],
    *,
    dias: float,
    meta_usd: float,
) -> dict[str, float]:
    """Umbrales solo en memoria — no llama calibrar_lote (no contamina global)."""
    from core import marcha_duracion as mdur

    eta_h = max(float(dias) * 24.0, 0.01)
    out: dict[str, float] = {}
    for base in activos:
        cal = mdur.calibrar_umbral_para_eta(base, float(meta_usd), eta_h)
        out[base.upper()] = float(cal.get("umbral_pct") or 0.0)
    return out


def crear_legion_papel(
    *,
    activos: list[str] | None = None,
    meta_lote_usd: float = 50.0,
    dias_personalizado: float = DIAS_PERSONALIZADO_DEFAULT,
    ahora: float | None = None,
) -> list[SombraIgrisPapel]:
    """Cuatro espejos aislados — una marcha cada uno."""
    ahora = ahora if ahora is not None else time.time()
    bases = [a.upper() for a in (activos or ["ETH"])]
    umb_pers = _calibrar_personalizado_local(bases, dias=dias_personalizado, meta_usd=meta_lote_usd)
    sombras: list[SombraIgrisPapel] = []
    for mid in MARCHAS_TEATRO:
        perfil = pd.MARCHAS[mid]
        sombras.append(
            SombraIgrisPapel(
                marcha_id=mid,
                titulo=str(perfil["titulo"]),
                force_market=bool(perfil["force_market"]),
                umbral_fees_mult=float(perfil["umbral_fees_mult"]),
                t0_paciencia=ahora,
                meta_lote_usd=float(meta_lote_usd),
                umbrales_local=dict(umb_pers) if mid == "personalizado" else {},
            )
        )
    return sombras


def umbral_sombra(
    sombra: SombraIgrisPapel,
    fees_be_pct: float,
    *,
    base: str,
    ahora: float | None = None,
) -> dict[str, Any]:
    """
    Umbral por marcha sin contaminar ritmo_lote / marcha_despliegue globales.
    Táctico/forzada → piso fees×mult (ritmo fino queda para GO con store propio).
    Asalto → 0 + force_market.
    Personalizado → umbral local calibrado en el teatro.
    """
    mid = sombra.marcha_id
    fees = max(0.0, float(fees_be_pct))
    ahora = ahora if ahora is not None else time.time()
    bu = (base or "").upper()

    if mid == "asalto" or sombra.force_market:
        return {
            "umbral_pct": 0.0,
            "fees_be_pct": round(fees, 6),
            "modo_paciencia": "teatro_asalto",
            "marcha_id": mid,
            "force_market": True,
            "piso_fees_mult": sombra.umbral_fees_mult,
        }

    if mid == "personalizado":
        u = float(sombra.umbrales_local.get(bu) or 0.0)
        return {
            "umbral_pct": round(u, 6),
            "fees_be_pct": round(fees, 6),
            "modo_paciencia": "teatro_personalizado",
            "marcha_id": mid,
            "force_market": False,
            "piso_fees_mult": sombra.umbral_fees_mult,
        }

    try:
        urg = pd.umbral_por_marcha(
            fees,
            marcha_id=mid,
            t0_paciencia=sombra.t0_paciencia,
            ahora=ahora,
            base=bu,
        )
        return {
            **urg,
            "modo_paciencia": str(urg.get("modo_paciencia") or f"teatro_{mid}"),
        }
    except Exception:
        piso = fees * float(sombra.umbral_fees_mult)
        return {
            "umbral_pct": round(piso, 6),
            "fees_be_pct": round(fees, 6),
            "modo_paciencia": f"teatro_piso_{mid}",
            "marcha_id": mid,
            "force_market": False,
            "piso_fees_mult": sombra.umbral_fees_mult,
        }


def _dist_mid_pct(ask_l: float, bid_s: float, mid: float) -> float:
    if mid <= 0:
        return 0.0
    d_ask = abs(ask_l - mid) / mid * 100.0
    d_bid = abs(bid_s - mid) / mid * 100.0
    return (d_ask + d_bid) / 2.0


def decidir_entrada(
    vision: VisionCompartida,
    sombra: SombraIgrisPapel,
    *,
    activo: str | None = None,
    restante_usd: float | None = None,
    inyectar_papel: bool = True,
) -> dict[str, Any]:
    """
    Decisión de teatro (comparación justa):
    - misma óptica para todas las sombras
    - umbral por marcha SIN el bypass ticker→umbral0 del sim de fills
    - force_market (asalto) muerde aunque el spread esté frío
    """
    activo_u = (activo or vision.activo_foco or "ETH").upper()
    fl, fs = im.frentes_bootstrap(activo_u)
    tank = TankVisionAdapter(vision)
    resto = float(
        restante_usd
        if restante_usd is not None
        else max(0.0, sombra.meta_lote_usd - sombra.contadores.avance_lote_usd)
    )

    if vision.semaforo == "ROJO":
        sombra.contadores.skips += 1
        dec = {
            "ok": False,
            "motivo": "semaforo_rojo",
            "accion": "skip",
            "etiqueta": sombra.etiqueta,
        }
        sombra.ultima_decision = dec
        return dec

    if resto <= 1e-9:
        sombra.contadores.skips += 1
        dec = {
            "ok": False,
            "motivo": "meta_papel_llena",
            "accion": "skip",
            "etiqueta": sombra.etiqueta,
        }
        sombra.ultima_decision = dec
        return dec

    bids_l, asks_l = ides.libro_tank(tank, fl)
    bids_s, asks_s = ides.libro_tank(tank, fs)
    ask_l = ides.best_ask(asks_l)
    bid_s = ides.best_bid(bids_s)
    if ask_l <= 0 or bid_s <= 0:
        px_l = float(vision.precios.get(fl) or 0)
        px_s = float(vision.precios.get(fs) or 0)
        if px_l <= 0:
            px_l = px_s
        if px_s <= 0:
            px_s = px_l
        if px_l > 0 and px_s > 0:
            bids_l, asks_l = ides.libro_sintetico_ticker(px_l, resto, frente=fl)
            bids_s, asks_s = ides.libro_sintetico_ticker(px_s, resto, frente=fs)
            ask_l = ides.best_ask(asks_l)
            bid_s = ides.best_bid(bids_s)

    if ask_l <= 0 or bid_s <= 0:
        sombra.contadores.skips += 1
        dec = {
            "ok": False,
            "motivo": "sin_ask_bid",
            "accion": "skip",
            "etiqueta": sombra.etiqueta,
        }
        sombra.ultima_decision = dec
        return dec

    spread = ides.spread_ejecutable_pct(ask_l, bid_s)
    fees_be = ides.fees_break_even_pct(fl, fs)
    urg = umbral_sombra(sombra, fees_be, base=activo_u, ahora=vision.ts)
    umbral = float(urg.get("umbral_pct") or 0.0)
    force = bool(urg.get("force_market") or sombra.force_market)
    mid = (ask_l + bid_s) / 2.0
    dist_mid = _dist_mid_pct(ask_l, bid_s, mid)
    espera_s = max(0.0, float(vision.ts) - float(sombra.t0_paciencia))

    muerde = force or (spread + 1e-12 >= umbral)
    if not muerde:
        sombra.contadores.esperas += 1
        dec = {
            "ok": False,
            "accion": "esperar",
            "motivo": "spread_bajo_umbral",
            "etiqueta": sombra.etiqueta,
            "marcha_id": sombra.marcha_id,
            "activo": activo_u,
            "ask_long": ask_l,
            "bid_short": bid_s,
            "mid": mid,
            "spread_pct": round(spread, 6),
            "umbral_pct": round(umbral, 6),
            "dist_mid_pct": round(dist_mid, 6),
            "espera_s": round(espera_s, 3),
            "force_market": force,
            "fees_be_pct": round(fees_be, 6),
            "fuente_vision": vision.fuente,
            **{k: urg[k] for k in ("modo_paciencia", "piso_fees_mult") if k in urg},
        }
        sombra.ultima_decision = dec
        return dec

    micro = min(resto, max(5.0, resto * 0.25))
    fees_usd = micro * (fees_be / 100.0)
    c = sombra.contadores
    c.mordidas += 1
    c.sum_spread_at_fill_pct += float(spread)
    c.sum_dist_mid_pct += float(dist_mid)
    c.sum_espera_s += float(espera_s)
    c.sum_fees_usd += float(fees_usd)
    c.sum_notional_usd += float(micro)
    if inyectar_papel:
        c.avance_lote_usd = min(sombra.meta_lote_usd, c.avance_lote_usd + micro)
    if c.primera_mordida_s is None:
        c.primera_mordida_s = espera_s
    c.ultima_mordida_ts = vision.ts
    sombra.t0_paciencia = vision.ts

    dec = {
        "ok": True,
        "accion": "morder_papel" if inyectar_papel else "senal_entrada",
        "motivo": "force_market" if force else "spread_ok",
        "etiqueta": sombra.etiqueta,
        "marcha_id": sombra.marcha_id,
        "activo": activo_u,
        "ask_long": ask_l,
        "bid_short": bid_s,
        "mid": mid,
        "spread_pct": round(spread, 6),
        "umbral_pct": round(umbral, 6),
        "dist_mid_pct": round(dist_mid, 6),
        "espera_s": round(espera_s, 3),
        "force_market": force,
        "fees_be_pct": round(fees_be, 6),
        "fees_usd_est": round(fees_usd, 6),
        "notional_usd": round(micro, 4),
        "avance_lote_usd": round(c.avance_lote_usd, 4),
        "fuente_vision": vision.fuente,
        "modo_paciencia": urg.get("modo_paciencia"),
    }
    sombra.ultima_decision = dec
    return dec


def ciclo_teatro(
    vision: VisionCompartida,
    sombras: list[SombraIgrisPapel],
    *,
    inyectar_papel: bool = True,
) -> dict[str, Any]:
    """Un pulso de mercado → 4 decisiones."""
    filas = []
    for sombra in sombras:
        for activo in vision.activos or [vision.activo_foco]:
            filas.append(
                decidir_entrada(
                    vision,
                    sombra,
                    activo=activo,
                    inyectar_papel=inyectar_papel,
                )
            )
    return {
        "ts": vision.ts,
        "fuente": vision.fuente,
        "semaforo": vision.semaforo,
        "activos": list(vision.activos),
        "decisiones": filas,
    }


def resumen_sombra(sombra: SombraIgrisPapel) -> dict[str, Any]:
    c = sombra.contadores
    n = max(c.mordidas, 1)
    return {
        "etiqueta": sombra.etiqueta,
        "marcha_id": sombra.marcha_id,
        "titulo": sombra.titulo,
        "force_market": sombra.force_market,
        "umbral_fees_mult": sombra.umbral_fees_mult,
        "umbrales_local": dict(sombra.umbrales_local),
        "mordidas": c.mordidas,
        "esperas": c.esperas,
        "skips": c.skips,
        "avg_spread_at_fill_pct": round(c.sum_spread_at_fill_pct / n, 6) if c.mordidas else None,
        "avg_dist_mid_pct": round(c.sum_dist_mid_pct / n, 6) if c.mordidas else None,
        "avg_espera_s": round(c.sum_espera_s / n, 3) if c.mordidas else None,
        "fees_usd_est": round(c.sum_fees_usd, 6),
        "notional_usd": round(c.sum_notional_usd, 4),
        "avance_lote_usd": round(c.avance_lote_usd, 4),
        "meta_lote_usd": sombra.meta_lote_usd,
        "avance_frac": round(c.avance_lote_usd / max(sombra.meta_lote_usd, 1e-9), 4),
        "primera_mordida_s": c.primera_mordida_s,
        "ultima_decision": sombra.ultima_decision,
    }


def resumen_teatro(
    sombras: list[SombraIgrisPapel],
    *,
    meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "ts": time.time(),
        "iso": time.strftime("%Y-%m-%d %H:%M:%S"),
        "teatro": "sombras_igris",
        "nota": "Laboratorio — no es 4.0.3 live · no manos reales · no 4×arise",
        "meta": meta or {},
        "sombras": [resumen_sombra(s) for s in sombras],
    }


def preparar(
    *,
    activo: str = "ETH",
    spread_fav_pct: float = 0.08,
    meta_lote_usd: float = 50.0,
    dias_personalizado: float = DIAS_PERSONALIZADO_DEFAULT,
) -> dict[str, Any]:
    """Sanidad dry-run: un ciclo sintético, sin WS ni caffeinate."""
    out_dir()
    (out_dir() / "README.txt").write_text(
        "Teatro de sombras Igris — logs ruidosos (gitignored vía data/logs/).\n"
        "Ver migracion/TEATRO_SOMBRAS_IGRIS.md para soltar con GO del Monarca.\n",
        encoding="utf-8",
    )
    # 3 climas: abundante (todos pueden morder) · medio · frío (solo asalto)
    climas = (
        ("abundante", max(float(spread_fav_pct), 0.15)),
        ("medio", 0.08),
        ("frio", -0.02),
    )
    sombras = crear_legion_papel(
        activos=[activo],
        meta_lote_usd=meta_lote_usd,
        dias_personalizado=dias_personalizado,
    )
    ciclos_out = []
    for nombre, edge in climas:
        vision = vision_sintetica(activo=activo, spread_fav_pct=edge)
        snap = ciclo_teatro(vision, sombras)
        snap["clima"] = nombre
        snap["spread_fav_pct"] = edge
        ciclos_out.append(snap)
    res = resumen_teatro(
        sombras,
        meta={
            "modo": "preparar",
            "activo": activo.upper(),
            "climas": [{"nombre": n, "spread_fav_pct": e} for n, e in climas],
            "ciclos": len(ciclos_out),
        },
    )
    res["ciclos"] = ciclos_out
    _escribir_json(out_dir() / "preparar_sanidad.json", res)
    heartbeat("preparar_ok", n_sombras=len(sombras))
    return res


def _arrancar_batida(
    *,
    durar_s: float,
    activos: list[str] | None,
    meta_lote_usd: float,
    dias_personalizado: float,
    campo_limpio: bool,
) -> tuple[float, float, list[str], list[SombraIgrisPapel], Path]:
    """Prepara sombras + campo limpio. El reloj de batida arranca DESPUÉS de calibrar."""
    bases = [a.upper() for a in (activos or ["ETH"])]
    sombras = crear_legion_papel(
        activos=bases,
        meta_lote_usd=meta_lote_usd,
        dias_personalizado=dias_personalizado,
    )
    t0 = time.time()
    deadline = t0 + max(1.0, float(durar_s))
    if campo_limpio:
        for s in sombras:
            s.contadores = ContadoresSombra()
            s.t0_paciencia = t0
    decisiones_path = out_dir() / "decisiones.jsonl"
    if campo_limpio and decisiones_path.exists():
        decisiones_path.unlink()
    return t0, deadline, bases, sombras, decisiones_path


def _pulso_batida(
    *,
    vision_fn,
    bases: list[str],
    sombras: list[SombraIgrisPapel],
    ciclos: int,
    t0: float,
    deadline: float,
    decisiones_path: Path,
) -> int:
    """Un ciclo de visión → decisión → sello parcial. Devuelve ciclos+1."""
    ahora = time.time()
    if vision_fn is not None:
        vision = vision_fn()
    else:
        edge = 0.08 if (ciclos % 4) else -0.01
        vision = vision_sintetica(activo=bases[0], spread_fav_pct=edge)
    snap = ciclo_teatro(vision, sombras)
    ciclos += 1
    with open(decisiones_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(snap, ensure_ascii=False) + "\n")
    parcial = resumen_teatro(
        sombras,
        meta={
            "modo": "correr",
            "ciclos": ciclos,
            "elapsed_s": round(ahora - t0, 1),
            "restante_s": round(deadline - ahora, 1),
            "activos": bases,
            "fuente_vision": getattr(vision, "fuente", "?"),
        },
    )
    _escribir_json(out_dir() / "resumen_parcial.json", parcial)
    heartbeat("teatro_tick", ciclos=ciclos, elapsed_s=round(ahora - t0, 1))
    return ciclos


def _sellar_batida(
    *,
    sombras: list[SombraIgrisPapel],
    bases: list[str],
    ciclos: int,
    t0: float,
    meta_extra: dict[str, Any] | None = None,
    sellado: bool = True,
    motivo_fin: str = "deadline",
) -> dict[str, Any]:
    """
    Escribe resumen. sellado=True solo si la batida llegó al plazo (guadían termina).
    Interrupción / crash limpio → sellado=False para que el guardián relance.
    """
    meta = {
        "modo": "correr",
        "ciclos": ciclos,
        "elapsed_s": round(time.time() - t0, 1),
        "activos": bases,
        "sellado": bool(sellado),
        "motivo_fin": motivo_fin,
    }
    if meta_extra:
        meta.update(meta_extra)
    final = resumen_teatro(sombras, meta=meta)
    _escribir_json(out_dir() / "resumen_parcial.json", final)
    if sellado:
        _escribir_json(out_dir() / "resumen_monarca.json", final)
        heartbeat("teatro_done", ciclos=ciclos, motivo_fin=motivo_fin)
    else:
        # No sellar monarca: si quedó un sello viejo, quitarlo para no engañar al guardián
        monarca = out_dir() / "resumen_monarca.json"
        if monarca.exists():
            try:
                monarca.unlink()
            except OSError:
                pass
        heartbeat("teatro_interrupted", ciclos=ciclos, motivo_fin=motivo_fin)
    return final


def correr_hasta(
    *,
    durar_s: float,
    intervalo_s: float = 5.0,
    activos: list[str] | None = None,
    meta_lote_usd: float = 50.0,
    dias_personalizado: float = DIAS_PERSONALIZADO_DEFAULT,
    vision_fn=None,
    campo_limpio: bool = True,
) -> dict[str, Any]:
    """
    Loop de batida sync — SOLO tras orden GO del Monarca.
    vision_fn: callable() -> VisionCompartida; default sintético (demo segura).
    """
    t0, deadline, bases, sombras, decisiones_path = _arrancar_batida(
        durar_s=durar_s,
        activos=activos,
        meta_lote_usd=meta_lote_usd,
        dias_personalizado=dias_personalizado,
        campo_limpio=campo_limpio,
    )
    ciclos = 0
    interrupted = False
    heartbeat("teatro_start", durar_s=durar_s, activos=bases)
    try:
        while time.time() < deadline:
            ciclos = _pulso_batida(
                vision_fn=vision_fn,
                bases=bases,
                sombras=sombras,
                ciclos=ciclos,
                t0=t0,
                deadline=deadline,
                decisiones_path=decisiones_path,
            )
            sleep_for = min(float(intervalo_s), max(0.2, deadline - time.time()))
            if sleep_for <= 0:
                break
            time.sleep(sleep_for)
    except KeyboardInterrupt:
        interrupted = True
        heartbeat("teatro_interrupted", ciclos=ciclos)

    return _sellar_batida(
        sombras=sombras,
        bases=bases,
        ciclos=ciclos,
        t0=t0,
        sellado=not interrupted and time.time() >= deadline - 1.0,
        motivo_fin="interrupted" if interrupted else "deadline",
    )


async def correr_hasta_async(
    *,
    durar_s: float,
    intervalo_s: float = 5.0,
    activos: list[str] | None = None,
    meta_lote_usd: float = 50.0,
    dias_personalizado: float = DIAS_PERSONALIZADO_DEFAULT,
    vision_fn=None,
    campo_limpio: bool = True,
    stop_event=None,
    meta_extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Misma batida que correr_hasta, async — convive con Bridge/Tank WS.
    stop_event: asyncio.Event opcional para apagado limpio (Ctrl+C / timeout externo).
    """
    import asyncio

    t0, deadline, bases, sombras, decisiones_path = _arrancar_batida(
        durar_s=durar_s,
        activos=activos,
        meta_lote_usd=meta_lote_usd,
        dias_personalizado=dias_personalizado,
        campo_limpio=campo_limpio,
    )
    ciclos = 0
    interrupted = False
    motivo = "deadline"
    heartbeat("teatro_start", durar_s=durar_s, activos=bases)
    try:
        while time.time() < deadline:
            if stop_event is not None and stop_event.is_set():
                interrupted = True
                motivo = "stop_event"
                heartbeat("teatro_interrupted", ciclos=ciclos, motivo=motivo)
                break
            ciclos = _pulso_batida(
                vision_fn=vision_fn,
                bases=bases,
                sombras=sombras,
                ciclos=ciclos,
                t0=t0,
                deadline=deadline,
                decisiones_path=decisiones_path,
            )
            sleep_for = min(float(intervalo_s), max(0.2, deadline - time.time()))
            if sleep_for <= 0:
                break
            if stop_event is not None:
                try:
                    await asyncio.wait_for(stop_event.wait(), timeout=sleep_for)
                    interrupted = True
                    motivo = "stop_event"
                    heartbeat("teatro_interrupted", ciclos=ciclos, motivo=motivo)
                    break
                except asyncio.TimeoutError:
                    pass
            else:
                await asyncio.sleep(sleep_for)
    except asyncio.CancelledError:
        heartbeat("teatro_interrupted", ciclos=ciclos, motivo="cancelled")
        raise

    ok_plazo = (not interrupted) and time.time() >= deadline - 1.0
    return _sellar_batida(
        sombras=sombras,
        bases=bases,
        ciclos=ciclos,
        t0=t0,
        meta_extra=meta_extra,
        sellado=ok_plazo,
        motivo_fin=motivo if interrupted else "deadline",
    )


def sombras_a_dict(sombras: list[SombraIgrisPapel]) -> list[dict[str, Any]]:
    return [asdict(s) for s in sombras]
