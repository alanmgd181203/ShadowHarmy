#!/usr/bin/env python3
"""
4.0.3 — Igris live: manos sueltas, ojos con libros, lote del pase.

Despierta: Tusk (oxígeno) · Tank (orderbook real) · Kaiser · Igris (manto).
NO despierta: Greed · Beru (hibernados hasta orden Monarca).
Manos reales: ON (MODO_SIMULACION=False).
Convert ritual Tusk: OFF. MNT = Santo (long inverso + short lineal). Short inverso = sucio legado, no plantar.
Canal: lote completo de potencia (vacío exclusivos). Un Santo: IGRIS_FORZAR_EXCLUSIVOS=MNT|ADA|BCH.
No reconstruir hedge de saco. Sueño+misión + solo Asalto (cirugía 2026-08-12).

  python scripts/arise_igris.py --solo-ojos --segundos 90
  python scripts/arise_igris.py --durar-hasta 2026-08-09T12:00:00 --permitir-mainnet-manos

ABORTA mainnet manos sin --permitir-mainnet-manos / ARISE_IGRIS_PERMITIR_MAINNET.
Respeta marcha Asalto (IGRIS_SOLO_ASALTO).
Logs: data/logs/arise_igris/<CANAL>/ · reporte: data/arise_igris_report_<CANAL>.json
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import signal
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# --- Sesión 4.0.3 (antes de importar config) — no reescribe .env ---
os.environ["ARISE_IGRIS_LIVE"] = "true"
os.environ["MODO_SIMULACION"] = "False"
# Ojos estrechos (sello 2026-08-13): last price Santos · sin orderbook.
# Override: ARISE_IGRIS_BOOKS=true
_books_on = os.getenv("ARISE_IGRIS_BOOKS", "").lower() in ("1", "true", "yes")
os.environ["BRIDGE_WS_SUBSCRIBE_BOOKS"] = "true" if _books_on else "false"
os.environ.setdefault("BRIDGE_WS_PROXY", "direct")
os.environ.setdefault("TUSK_BOVEDA_MANOS", "false")
os.environ.setdefault("ARENA_IGRIS_ACTIVA", "false")
os.environ.setdefault("ARENA_IGRIS_FILLS_VIRTUALES", "false")
os.environ.setdefault("GREED_KAISER_ENABLED", "false")
os.environ.setdefault("GREED_VIP_ENABLED", "false")
os.environ.setdefault("GREED_BASIS_HOLD_ENABLED", "false")
os.environ.setdefault("GREED_MULTICRUCE_ENABLED", "false")
os.environ.setdefault("SAFE_MODE", "true")
# Asalto: plantar ya (no esperar señal Kaiser / no event-driven frío)
os.environ["IGRIS_EVENT_DRIVEN"] = "false"
os.environ["IGRIS_BOOTSTRAP_ON_START"] = "true"
os.environ["ARISE_BERU_ARMADO"] = "false"
# Lote completo del pase. Canal 1 Santo: export IGRIS_FORZAR_EXCLUSIVOS=ADA
_forzar_excl = (os.environ.get("IGRIS_FORZAR_EXCLUSIVOS") or "").strip().upper()
os.environ["IGRIS_ACTIVOS_EXCLUSIVOS"] = _forzar_excl  # vacío = lote potencia
os.environ.setdefault("TICKER_BASE", "ETH")
# Bóveda limpia (Jess campo): no pausar base MNT; proteger solo símbolos bóveda USDC
os.environ.setdefault("IGRIS_BOVEDA_BASES", "")
os.environ.setdefault("IGRIS_PROTEGER_BASES", "")
os.environ.setdefault("IGRIS_PROTEGER_SYMBOLS", "MNTPERP,MNTUSDC")
os.environ.setdefault("IGRIS_MNT_HEDGE_OBLIGATORIO", "false")
os.environ.setdefault("IGRIS_BOVEDA_EN_LOTE", "true")
os.environ.setdefault("IGRIS_BOVEDA_SHORT_QUOTE", "USDC")
os.environ.setdefault("IGRIS_SUENO_MISION", "true")
os.environ.setdefault("IGRIS_SARGENTO_AUTO", "true")
os.environ.setdefault("IGRIS_SOLO_ASALTO", "true")
os.environ.setdefault("IGRIS_DUAL_SALVAVIDAS_EMPATE", "false")
os.environ.setdefault("IGRIS_DUAL_SALVAVIDAS_EMERGENCIA", "true")
os.environ.setdefault("IGRIS_BOCADO_ASIMETRICO", "true")
os.environ.setdefault("IGRIS_OXIGENO_PILOTO", "false")
os.environ.setdefault("IGRIS_VISION_MODO", "last_price")
# Ojos Asalto: no castrar por ruido mid↔ticker 0.4–0.7%
os.environ.setdefault("IGRIS_LIBRO_DIVERGENCIA_PCT", "1.0")
os.environ.setdefault("IGRIS_LIBRO_DIVERGENCIA_ASALTO_PCT", "2.5")
os.environ.setdefault("IGRIS_MASA_ASIMETRIA_ASALTO_PCT", "0.12")
os.environ.setdefault("IGRIS_ASALTO_OVERSHOOT_META", "true")
os.environ.setdefault("IGRIS_FORCE_MAX_LEVERAGE", "true")
os.environ.setdefault("IGRIS_ESPERA_COOLDOWN_S", "3")
# Sin libros: puerta §E usa ticker (Asalto Market)
os.environ.setdefault(
    "IGRIS_TICKER_PUERTA_SI_SIN_LIBRO",
    "true" if not _books_on else "false",
)
os.environ.setdefault("BYBIT_RECV_WINDOW_MS", "60000")
os.environ.setdefault("BRIDGE_WS_FORCE_IPV4", "true")
os.environ.setdefault("IGRIS_LIBRO_REST_FALLBACK", "true" if _books_on else "false")
# Muleta REST más a menudo cuando WS tiembla (Asalto)
os.environ.setdefault("IGRIS_LIBRO_REST_COOLDOWN_S", "8")
os.environ.setdefault("BRIDGE_WS_OPEN_TIMEOUT_S", "60")
os.environ.setdefault("BRIDGE_WS_INVALIDAR_ON_DROP", "true")
# Asalto: aire ~2s (Market + dens máx — Monarca 2026-08-09)
os.environ.setdefault("IGRIS_ENGORDE_RITMO_S", "2")
os.environ.setdefault("IGRIS_ESPERA_LOG_S", "20")
os.environ.setdefault("IGRIS_VENTANA_NO_BLOQUEA_ENGORDE", "true")
os.environ.setdefault("IGRIS_ASALTO_SIN_TANK_ROJO", "true")
os.environ.setdefault("IGRIS_ASALTO_PUERTA_SIN_OJOS", "true")
os.environ.setdefault("IGRIS_RESERVA_AJUSTAR_A_AUTH", "true")
os.environ.setdefault("IGRIS_PODA_AUTO", "false")
# Arise live: no DEMO Bybit (sim/arena son otro ritual)
os.environ.setdefault("MODO_TESTNET", "False")

import core.config as config  # noqa: E402
from core import ojos_estrechos  # noqa: E402

config.MODO_SIMULACION = False
config.ARISE_IGRIS_LIVE = True
config.BRIDGE_WS_SUBSCRIBE_BOOKS = bool(_books_on)
if hasattr(config, "BRIDGE_WS_PROXY"):
    config.BRIDGE_WS_PROXY = (os.environ.get("BRIDGE_WS_PROXY") or "direct").strip()
if hasattr(config, "TUSK_BOVEDA_MANOS"):
    config.TUSK_BOVEDA_MANOS = False
config.ARENA_IGRIS_ACTIVA = False
if hasattr(config, "ARENA_IGRIS_FILLS_VIRTUALES"):
    config.ARENA_IGRIS_FILLS_VIRTUALES = False
config.GREED_KAISER_ENABLED = False
config.GREED_VIP_ENABLED = False
config.GREED_BASIS_HOLD_ENABLED = False
config.GREED_MULTICRUCE_ENABLED = False
config.SAFE_MODE = True
config.IGRIS_EVENT_DRIVEN = False
if hasattr(config, "IGRIS_BOOTSTRAP_ON_START"):
    config.IGRIS_BOOTSTRAP_ON_START = True
config.IGRIS_ENGORDE_RITMO_S = float(os.getenv("IGRIS_ENGORDE_RITMO_S", "2") or 2)
config.IGRIS_TICKER_PUERTA_SI_SIN_LIBRO = "true" if not _books_on else "false"
config.BYBIT_RECV_WINDOW_MS = int(float(os.getenv("BYBIT_RECV_WINDOW_MS", "60000") or 60000))
if hasattr(config, "BRIDGE_WS_FORCE_IPV4"):
    config.BRIDGE_WS_FORCE_IPV4 = True
if hasattr(config, "IGRIS_LIBRO_REST_FALLBACK"):
    config.IGRIS_LIBRO_REST_FALLBACK = bool(_books_on)
if not _books_on and hasattr(config, "BINANCE_REF_ENABLED"):
    config.BINANCE_REF_ENABLED = False
if hasattr(config, "IGRIS_LIBRO_REST_COOLDOWN_S"):
    config.IGRIS_LIBRO_REST_COOLDOWN_S = float(
        os.environ.get("IGRIS_LIBRO_REST_COOLDOWN_S", "8") or 8
    )
if hasattr(config, "BRIDGE_WS_OPEN_TIMEOUT_S"):
    config.BRIDGE_WS_OPEN_TIMEOUT_S = float(
        os.environ.get("BRIDGE_WS_OPEN_TIMEOUT_S", "60") or 60
    )
if hasattr(config, "BRIDGE_WS_INVALIDAR_ON_DROP"):
    config.BRIDGE_WS_INVALIDAR_ON_DROP = (
        os.environ.get("BRIDGE_WS_INVALIDAR_ON_DROP", "true").lower() == "true"
    )
if hasattr(config, "IGRIS_ESPERA_LOG_S"):
    config.IGRIS_ESPERA_LOG_S = float(os.environ.get("IGRIS_ESPERA_LOG_S", "20") or 20)
# Ticker de arranque ETH; exclusivos vacíos = Igris sigue el lote del pase
config.TICKER_BASE = "ETH"
config.SIMBOLO_LINEAR = "ETHUSDT"
config.FRENTE_PRINCIPAL = "ETHUSDT_LINEAL"
_excl_raw = (os.environ.get("IGRIS_ACTIVOS_EXCLUSIVOS") or "").strip()
config.IGRIS_ACTIVOS_EXCLUSIVOS = (
    [a.strip().upper() for a in _excl_raw.split(",") if a.strip()] if _excl_raw else []
)
_bb = (os.environ.get("IGRIS_BOVEDA_BASES") or "").strip()
config.IGRIS_BOVEDA_BASES = (
    [a.strip().upper() for a in _bb.split(",") if a.strip()] if _bb else []
)
_pb = (os.environ.get("IGRIS_PROTEGER_BASES") or "").strip()
config.IGRIS_PROTEGER_BASES = (
    [a.strip().upper() for a in _pb.split(",") if a.strip()]
    if _pb
    else list(config.IGRIS_BOVEDA_BASES)
)
_ps = (os.environ.get("IGRIS_PROTEGER_SYMBOLS") or "MNTPERP,MNTUSDC").strip()
config.IGRIS_PROTEGER_SYMBOLS = [
    a.strip().upper() for a in _ps.split(",") if a.strip()
]
config.IGRIS_MNT_HEDGE_OBLIGATORIO = (
    os.environ.get("IGRIS_MNT_HEDGE_OBLIGATORIO", "false").lower() == "true"
)
config.IGRIS_BOVEDA_EN_LOTE = (
    os.environ.get("IGRIS_BOVEDA_EN_LOTE", "true").lower() == "true"
)
config.IGRIS_SUENO_MISION = os.environ.get("IGRIS_SUENO_MISION", "true").lower() == "true"
config.IGRIS_SARGENTO_AUTO = os.environ.get("IGRIS_SARGENTO_AUTO", "true").lower() == "true"
config.IGRIS_SOLO_ASALTO = os.environ.get("IGRIS_SOLO_ASALTO", "true").lower() == "true"
config.IGRIS_DUAL_SALVAVIDAS_EMPATE = (
    os.environ.get("IGRIS_DUAL_SALVAVIDAS_EMPATE", "false").lower() == "true"
)
config.IGRIS_BOCADO_ASIMETRICO = (
    os.environ.get("IGRIS_BOCADO_ASIMETRICO", "true").lower() == "true"
)
config.IGRIS_OXIGENO_PILOTO = False
config.MARCHA_DESPLIEGUE = "asalto"
config.IGRIS_LIBRO_DIVERGENCIA_PCT = float(
    os.environ.get("IGRIS_LIBRO_DIVERGENCIA_PCT", "1.0") or 1.0
)
config.IGRIS_LIBRO_DIVERGENCIA_ASALTO_PCT = float(
    os.environ.get("IGRIS_LIBRO_DIVERGENCIA_ASALTO_PCT", "2.5") or 2.5
)
config.IGRIS_MASA_ASIMETRIA_ASALTO_PCT = float(
    os.environ.get("IGRIS_MASA_ASIMETRIA_ASALTO_PCT", "0.12") or 0.12
)
config.IGRIS_ASALTO_OVERSHOOT_META = (
    os.environ.get("IGRIS_ASALTO_OVERSHOOT_META", "true").lower() == "true"
)
config.IGRIS_FORCE_MAX_LEVERAGE = (
    os.environ.get("IGRIS_FORCE_MAX_LEVERAGE", "true").lower() == "true"
)
if hasattr(config, "IGRIS_ESPERA_COOLDOWN_S"):
    config.IGRIS_ESPERA_COOLDOWN_S = float(
        os.environ.get("IGRIS_ESPERA_COOLDOWN_S", "3") or 3
    )
config.IGRIS_EXCLUIR_BASES = [
    a.strip().upper()
    for a in (os.environ.get("IGRIS_EXCLUIR_BASES") or "").split(",")
    if a.strip()
]

from core.bellion import BellionAuditor  # noqa: E402
from core.bridge import BybitBridge  # noqa: E402
from core.dashboard import PanelDeControl  # noqa: E402
from generales.igris import IgrisEscudo  # noqa: E402
from generales.kaiser import KaiserVocero  # noqa: E402
from generales.tank import TankCluster  # noqa: E402
from generales.tusk import TuskBoveda  # noqa: E402

_canal_log = (
    (os.environ.get("IGRIS_FORZAR_EXCLUSIVOS") or os.environ.get("ARISE_CANAL") or "")
    .strip()
    .upper()
    .replace(",", "_")
    or "lote"
)
LOG_DIR = ROOT / "data" / "logs" / "arise_igris" / _canal_log
REPORT_PATH = ROOT / "data" / f"arise_igris_report_{_canal_log}.json"
HEARTBEAT_PATH = LOG_DIR / "heartbeat.json"


def _truthy(val: str | None) -> bool:
    return (val or "").strip().lower() in ("1", "true", "yes", "on")


def _parse_deadline(raw: str) -> float | None:
    s = (raw or "").strip()
    if not s:
        return None
    try:
        return float(s)
    except ValueError:
        pass
    for fmt in (
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M",
        "%Y-%m-%d %H:%M",
    ):
        try:
            return datetime.strptime(s, fmt).timestamp()
        except ValueError:
            continue
    return None


def _segundos_desde_flags(
    *,
    segundos: float,
    horas: float,
    durar_hasta: str,
) -> float:
    """Devuelve segundos de corte (>0) o 0 = sin corte por tiempo."""
    dl = _parse_deadline(durar_hasta)
    if dl is not None:
        remaining = dl - time.time()
        if remaining <= 0:
            raise SystemExit(f"ABORT: --durar-hasta ya pasó ({durar_hasta})")
        return remaining
    if horas and horas > 0:
        return float(horas) * 3600.0
    return float(segundos or 0)


def _bases_lote_ojos(equity_usd: float | None = None) -> list[str]:
    """Bases del pase en potencia (+ ETH si ya tiene manto) para WS/REST."""
    from core import pase_director as pd

    eq = float(equity_usd or 0)
    if eq <= 0:
        try:
            eq = float((pd.cargar_marcha_payload() or {}).get("equity_usd") or 0)
        except Exception:
            eq = 0.0
    if eq <= 0:
        eq = float(getattr(config, "EQUITY_FALLBACK_USD", 1500) or 1500)
    plan = pd.plan_lote(eq)
    bases: list[str] = []
    seen: set[str] = set()
    for p in list(plan.get("lote") or []) + list(plan.get("cola_fina") or []):
        act = str(p.get("activo") or "").upper()
        if act and act not in seen:
            seen.add(act)
            bases.append(act)
    # ETH siempre en ojos si hay paso 1 (manto vivo / calentamiento)
    if "ETH" not in seen:
        bases.insert(0, "ETH")
    excl = list(getattr(config, "IGRIS_ACTIVOS_EXCLUSIVOS", None) or [])
    if excl:
        bases = [b for b in bases if b in {str(x).upper() for x in excl}] or list(excl)
    # Pausa bóveda / CSV excluido: ojos alineados al canal de engorde
    from core import igris_proteccion as iprot

    return iprot.filtrar_activos_trabajo(bases)


def _books_requeridos() -> bool:
    return bool(getattr(config, "BRIDGE_WS_SUBSCRIBE_BOOKS", False))


def _aplicar_ojos_abiertos(tusk) -> list[str]:
    """Ojos del canal Igris.

    Default (2026-08-13): Santos last price · books OFF (Asalto Market).
    ARISE_IGRIS_BOOKS=true → books ON (legado calentamiento con muros).
    """
    eq = float(getattr(tusk, "masa_bruta_real", 0) or getattr(tusk, "masa_bruta", 0) or 0)
    out = _bases_lote_ojos(eq if eq > 0 else None)
    excl = list(getattr(config, "IGRIS_ACTIVOS_EXCLUSIVOS", None) or [])
    config.TICKER_BASE = str((excl[0] if excl else (out[0] if out else "ETH"))).upper()
    # Unión: lote del pase + Santos canónicos (MNT foco no se queda ciego)
    bases = ojos_estrechos.bases_santos(extra=out)
    if excl:
        bases = [b for b in bases if b in {str(x).upper() for x in excl}] or list(excl)

    books_on = _books_requeridos()
    if books_on:
        books = list(bases)
        if "ETH" not in {b.upper() for b in books}:
            books = ["ETH"] + books
        config.BRIDGE_WS_BASES = list(books)
        config.BRIDGE_WS_SUBSCRIBE_BOOKS = True
        if hasattr(config, "BRIDGE_WS_BOOKS_BASES"):
            config.BRIDGE_WS_BOOKS_BASES = list(books)
        modo_ojos = "books=ON"
    else:
        ojos_estrechos.aplicar_ojos_last_price_santos(
            bases, apagar_binance_ref=True,
        )
        books = []
        modo_ojos = "books=OFF · last_price"

    modo = f"exclusivos={excl}" if excl else "lote_completo_pase"
    boveda = "ON" if getattr(config, "IGRIS_BOVEDA_EN_LOTE", True) else "OFF(pausa MNT)"
    print(
        f"[OJOS] Canal Igris · {modo} · {modo_ojos} · Beru hibernado · "
        f"bóveda_en_lote={boveda}"
    )
    print(
        f"[OJOS] Bases ({len(bases)}): {', '.join(bases)}"
        + (f" · books={', '.join(books)}" if books else "")
    )
    return bases


def _libros_eth(tank) -> dict:
    """Evidencia de libros en frentes ETH (bids/asks + edad)."""
    from core import igris_despliegue as ides
    from core import igris_ojos as ojos

    frentes = ("ETHUSDT_LINEAL", "ETHUSD_INVERSE")
    detalle = {}
    ok_alguno = False
    stale_alguno = False
    for f in frentes:
        bids, asks = ides.libro_tank(tank, f)
        n_b, n_a = len(bids or []), len(asks or [])
        meta = ojos.meta_libro(tank, f)
        detalle[f] = {
            "bids": n_b,
            "asks": n_a,
            "edad_s": meta.get("edad_s"),
            "stale": meta.get("stale"),
        }
        if n_b > 0 and n_a > 0:
            ok_alguno = True
        if meta.get("stale"):
            stale_alguno = True
    return {"ok": ok_alguno and not stale_alguno, "frentes": detalle, "stale": stale_alguno}


def _escribir_heartbeat(msg: str, extra: dict | None = None) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "ts": time.time(),
        "iso": datetime.now().isoformat(timespec="seconds"),
        "msg": msg,
        "pid": os.getpid(),
    }
    if extra:
        payload.update(extra)
    try:
        HEARTBEAT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    except OSError:
        pass


def _snapshot_cierre(tusk, igris, *, solo_ojos: bool, libros: dict | None) -> dict:
    from core import pase_director as pd
    from core import manto_ventana as mv

    eq = float(getattr(tusk, "masa_bruta_real", 0) or getattr(tusk, "masa_bruta", 0) or 0)
    mid = pd.cargar_marcha()
    payload = pd.cargar_marcha_payload() or {}
    plan = pd.plan_lote(eq, marcha_id=mid) if eq > 0 else {}
    meta = pd.meta_engorde_usd(eq, tusk=tusk, marcha_id=mid) if eq > 0 else {}
    usd_l, usd_s = mv.usd_piernas_desde_pesos(getattr(tusk, "pesos", {}) or {})
    ventana = mv.resumen_barco(usd_l, usd_s)
    return {
        "ts": time.time(),
        "checklist": "4.0.3",
        "sim": False,
        "manos_reales": not solo_ojos,
        "solo_ojos": solo_ojos,
        "books_on": bool(getattr(config, "BRIDGE_WS_SUBSCRIBE_BOOKS", False)),
        "libros_eth": libros,
        "testnet": bool(getattr(config, "TESTNET", True)),
        "marcha_id": mid,
        "marcha_payload": {
            "fill_ratio": payload.get("fill_ratio"),
            "reserva_pasos": payload.get("reserva_pasos"),
            "titulo": payload.get("titulo"),
        },
        "equity_usd": round(eq, 4),
        "masa_autorizada": float(getattr(tusk, "masa_autorizada", 0) or 0),
        "plan": {
            "potencia_n": plan.get("potencia_n"),
            "foco": plan.get("foco"),
            "activos_trabajo": plan.get("activos_trabajo"),
            "fill_ratio": plan.get("fill_ratio"),
            "reserva_pasos": plan.get("reserva_pasos"),
        },
        "meta_engorde": meta,
        "ventana_manto": ventana,
        "n_frentes_peso": len(getattr(tusk, "pesos", {}) or {}),
        "greed_hibernado": True,
        "beru_hibernado": True,
        "boveda_manos": False,
    }


async def _publicar_estado(bellion, tusk, igris, tank, kaiser):
    await asyncio.sleep(2)
    while True:
        await bellion.publicar_estado_vivo(tusk, None, igris, tank, kaiser=kaiser)
        await asyncio.sleep(1)


async def _refrescar_panel(panel):
    while True:
        panel.refrescar()
        await asyncio.sleep(1)


async def _cronica(tusk, tank, intervalo_s: float = 30.0):
    await asyncio.sleep(10)
    from core import pase_director as pd

    while True:
        mid = pd.cargar_marcha()
        eq = float(getattr(tusk, "masa_bruta_real", 0) or getattr(tusk, "masa_bruta", 0) or 0)
        tes = getattr(tusk, "tesoreria", None) or {}
        lib = _libros_eth(tank)
        n_pesos = sum(
            float(p.get("long") or 0) + float(p.get("short") or 0)
            for p in (getattr(tusk, "pesos", {}) or {}).values()
        )
        print(
            f"[LIVE] marcha={mid} | equity={eq:.2f} | O2={tes.get('oxigeno_guerra_usd')} | "
            f"masa_auth={getattr(tusk, 'masa_autorizada', None)} | pesos≈{n_pesos:.4f} | "
            f"books_eth={lib.get('ok')} stale={lib.get('stale')} | "
            f"SIM={config.MODO_SIMULACION} | TN={config.TESTNET}"
        )
        _escribir_heartbeat(
            "cronica",
            {
                "marcha": mid,
                "equity": eq,
                "books_eth": lib.get("ok"),
                "books_stale": lib.get("stale"),
                "libros_eth": lib.get("frentes"),
                "ciclos": int(time.time()),
            },
        )
        await asyncio.sleep(intervalo_s)


async def _esperar_ojos_y_libros(
    tank,
    bridge=None,
    *,
    timeout_s: float = 120.0,
    shutdown_event: asyncio.Event | None = None,
) -> tuple[bool, bool, dict]:
    """Calentamiento: Tank VERDE + last price (o libros ETH si books ON)."""
    from core import igris_ojos as ojos

    books_on = _books_requeridos()
    base = str(getattr(config, "TICKER_BASE", "ETH") or "ETH").upper()
    keys = (
        f"{base}USDT_LINEAL",
        f"{base}USD_INVERSE",
        f"{base}USDT_SPOT",
        "ETHUSDT_LINEAL",
        "ETHUSD_INVERSE",
        "MNTUSDT_LINEAL",
        "MNTUSD_INVERSE",
    )
    frentes_rest = [f"{base}USDT_LINEAL", f"{base}USD_INVERSE"]
    t0 = time.time()
    if books_on:
        print(f"[OJOS] Calentamiento VERDE + libros (hasta {timeout_s:.0f}s)…")
    else:
        print(f"[OJOS] Calentamiento VERDE + last price (hasta {timeout_s:.0f}s) · sin muros…")
    verde_ok = False
    libros: dict = {"ok": False, "frentes": {}, "stale": True}
    ultimo_rest = 0.0
    while time.time() - t0 < timeout_s:
        if shutdown_event is not None and shutdown_event.is_set():
            print("[OJOS] Calentamiento abortado (apagado).")
            return False, False, libros
        try:
            tank._auditar_semaforos()
        except Exception:
            pass
        lider = None
        try:
            lider = tank._obtener_lider_verde()
        except Exception:
            lider = None
        px = {}
        if lider and getattr(lider, "estado_foco", "") == "VERDE":
            px = lider.precios_con_reflejo() or {}
            if any(float(px.get(k) or 0) > 0 for k in keys):
                verde_ok = True
        if books_on:
            libros = _libros_eth(tank)
            if verde_ok and libros.get("ok"):
                print(
                    f"[OJOS] VERDE+libros OK lat={getattr(lider, 'latencia_ms', 0):.0f}ms · "
                    f"{libros.get('frentes')}"
                )
                return True, True, libros
            ahora = time.time()
            if bridge is not None and ahora - ultimo_rest >= 8.0 and not libros.get("ok"):
                ultimo_rest = ahora
                try:
                    diag = await ojos.asegurar_libros_frescos(tank, bridge, frentes_rest)
                    if any(r.get("ok") for r in (diag.get("rest") or [])):
                        print(
                            f"[OJOS] REST muleta · "
                            f"{[r.get('frente') for r in diag.get('rest') or [] if r.get('ok')]}"
                        )
                    libros = _libros_eth(tank)
                    if verde_ok and libros.get("ok"):
                        print(f"[OJOS] VERDE+libros OK tras REST · {libros.get('frentes')}")
                        return True, True, libros
                except Exception as e:
                    print(f"[OJOS] REST muleta falló: {e}")
        else:
            # Sin books: VERDE + ticker basta (Asalto Market)
            vivos = {k: float(px.get(k) or 0) for k in keys if float(px.get(k) or 0) > 0}
            libros = {
                "ok": bool(vivos),
                "frentes": {k: {"last": v, "modo": "ticker"} for k, v in vivos.items()},
                "stale": not bool(vivos),
                "modo": "last_price",
            }
            if verde_ok and vivos:
                print(
                    f"[OJOS] VERDE+last OK lat={getattr(lider, 'latencia_ms', 0):.0f}ms · "
                    f"tickers={list(vivos.keys())[:6]}"
                )
                return True, True, libros
        await asyncio.sleep(1.0)
    print(
        f"[OJOS] Timeout calentamiento — verde={verde_ok} ojos={libros.get('ok')} "
        f"detalle={libros.get('frentes')}"
    )
    return verde_ok, bool(libros.get("ok")), libros


async def _apagado(
    shutdown_event,
    bellion,
    tusk,
    igris,
    started: float,
    tasks: list,
    *,
    solo_ojos: bool,
    libros_ref: dict,
):
    await shutdown_event.wait()
    snap = _snapshot_cierre(tusk, igris, solo_ojos=solo_ojos, libros=libros_ref.get("libros"))
    snap["duracion_s"] = round(time.time() - started, 1)
    snap["veredicto_calentamiento"] = libros_ref.get("veredicto")
    try:
        REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        REPORT_PATH.write_text(json.dumps(snap, indent=2, ensure_ascii=False), encoding="utf-8")
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        (LOG_DIR / "ultimo_reporte.json").write_text(
            json.dumps(snap, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        print(f"\n[LIVE] Reporte → {REPORT_PATH}")
        print(
            f"[LIVE] marcha={snap.get('marcha_id')} | meta_restante="
            f"{(snap.get('meta_engorde') or {}).get('restante_usd')} | "
            f"ventana={(snap.get('ventana_manto') or {}).get('estado')} | "
            f"books={(snap.get('libros_eth') or {}).get('ok')}"
        )
    except OSError as e:
        print(f"[LIVE] No se pudo escribir reporte: {e}")
    _escribir_heartbeat("sellado", {"sellado": True})
    try:
        await bellion.ley_de_sucesion(tusk.export_for_bellion(), [])
        await bellion.anotar(
            "BELLION",
            "SUCESION",
            "Ritual Igris LIVE 4.0.3 sellado — Greed/Beru hibernados.",
        )
    except Exception as e:
        print(f"[LIVE] Aviso sucesión: {e}")
    for t in tasks:
        if not t.done():
            t.cancel()
    # WS Bridge a veces no suelta el handshake — no dejar zombie tras sello
    async def _salida_dura():
        await asyncio.sleep(6)
        print("[LIVE] Salida dura tras sello (WS no cede).")
        os._exit(0)

    asyncio.create_task(_salida_dura())


async def _corte_tiempo(shutdown_event, segundos: float):
    if segundos <= 0:
        return
    await asyncio.sleep(segundos)
    print(f"\n[LIVE] Corte por tiempo ({segundos:.0f}s) — sellando…")
    shutdown_event.set()


def _senales(loop, shutdown_event):
    def _handler(sig, frame):
        loop.call_soon_threadsafe(shutdown_event.set)

    signal.signal(signal.SIGINT, _handler)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, _handler)


def _gate_seguridad(*, solo_ojos: bool, permitir_mainnet: bool) -> None:
    if not config.API_KEY or not config.API_SECRET:
        raise SystemExit("ABORT: faltan BYBIT_API_KEY / BYBIT_API_SECRET en .env")
    if config.MODO_SIMULACION:
        raise SystemExit("ABORT: MODO_SIMULACION debe ser False en 4.0.3")
    # Arise live = mainnet real; manos exigen flag explícito
    if not solo_ojos:
        if not permitir_mainnet:
            raise SystemExit(
                "ABORT: manos mainnet sin flag de seguridad.\n"
                "  Usa --permitir-mainnet-manos o ARISE_IGRIS_PERMITIR_MAINNET=true"
            )
        print("[SEGURIDAD] Mainnet manos AUTORIZADAS por flag explícito.")
    else:
        print("[SEGURIDAD] Solo ojos — sin manos Igris.")


async def ritual_igris_live(
    *,
    segundos: float = 0.0,
    solo_ojos: bool = False,
    permitir_mainnet: bool = False,
):
    from core import pase_director as pd

    _gate_seguridad(solo_ojos=solo_ojos, permitir_mainnet=permitir_mainnet)

    mid = pd.cargar_marcha()
    perfil = pd.perfil_marcha(mid)
    modo = "SOLO OJOS (sin Igris manos)" if solo_ojos else "MANOS SUELTAS (Igris manto)"
    print("\n" + "═" * 52)
    print("    4.0.3  RITUAL IGRIS LIVE (parcial)")
    print("    Kaiser · Tank · Tusk · Igris")
    print(f"    {modo}")
    print(
        f"    Canal log: {LOG_DIR.name} · exclusivos="
        f"{config.IGRIS_ACTIVOS_EXCLUSIVOS or 'lote'}"
    )
    print(
        "    MNT bóveda: "
        + ("en lote" if config.IGRIS_BOVEDA_EN_LOTE else "PAUSA engorde")
        + f" · proteger={config.IGRIS_PROTEGER_SYMBOLS}"
    )
    print("    Greed/Beru hibernados · Convert OFF · sueño+misión ON")
    print(
        f"    Books={'ON' if _books_requeridos() else 'OFF(last_price)'} · "
        f"SIM={config.MODO_SIMULACION} · proxy={getattr(config, 'BRIDGE_WS_PROXY', 'direct')}"
    )
    print(f"    Marcha: {mid} · fill={perfil.get('fill_ratio')} · reserva={perfil.get('reserva_pasos')}")
    print("═" * 52)

    shutdown_event = asyncio.Event()
    _senales(asyncio.get_running_loop(), shutdown_event)
    started = time.time()
    running: list[asyncio.Task] = []
    libros_ref: dict = {"libros": None, "veredicto": None}
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    _escribir_heartbeat("arranque", {"solo_ojos": solo_ojos, "marcha": mid})

    try:
        api_key = getattr(config, "API_KEY", None)
        api_secret = getattr(config, "API_SECRET", None)

        bellion = BellionAuditor()
        tusk = TuskBoveda(bellion)
        tank = TankCluster(tusk, bellion, ticker_base=config.TICKER_BASE)
        bridge = BybitBridge(tank, tusk, bellion, api_key, api_secret)
        binance_ref = None
        if getattr(config, "BINANCE_REF_ENABLED", True):
            try:
                from core.binance_ref import BinanceRefBridge

                binance_ref = BinanceRefBridge(tank, bellion)
            except Exception as e:
                print(f"[OJOS] Binance ref omitido: {e}")

        estado_prev = bellion.cargar_estado()
        if estado_prev:
            tusk.restaurar_desde_bellion(estado_prev.get("boveda", {}))
            print("[BELLION] Recovery: bóveda restaurada.")

        _aplicar_ojos_abiertos(tusk)

        # Hidratar acumulado real ANTES de que Igris mire meta/engorde
        print("[TUSK] Reconciliación inmediata con exchange (L+S visible)…")
        recon_ok = False
        try:
            recon_ok = bool(await tusk.reconciliar_con_exchange(bridge))
            await tusk.actualizar_telemetria_posiciones(bridge)
        except Exception as e:
            print(f"[TUSK] Reconciliación arranque falló: {e}")
            recon_ok = False
        if not solo_ojos and not recon_ok:
            print(
                "[SEGURIDAD] ABORT: Tusk ciego (sin reconciliación). "
                "No se sueltan manos — evita duplicar manto / confundir bóveda."
            )
            print(
                "  Si ves ErrCode 10010: actualiza la IP whitelist de la API en Bybit "
                "y vuelve a lanzar el guardián."
            )
            await bellion.anotar(
                "IGRIS", "ABORT_RECON",
                "Manos OFF: reconciliación fallida al arranque",
            )
            raise SystemExit(2)

        # Hedge MNT solo si la bóveda entra al lote de engorde
        if (
            not solo_ojos
            and getattr(config, "IGRIS_BOVEDA_EN_LOTE", True)
            and getattr(config, "IGRIS_MNT_HEDGE_OBLIGATORIO", False)
        ):
            from core import mnt_manto_hedge as mmh

            hedge = await mmh.asegurar_hedge_bases_boveda(bridge)
            pares_ok = [
                f"{p['symbol']}/{p['category']}"
                for p in (hedge.get("pares") or [])
                if p.get("ok")
            ]
            pares_bad = [
                f"{p['symbol']}/{p['category']}:{p.get('mensaje')}"
                for p in (hedge.get("pares") or [])
                if not p.get("ok")
            ]
            if pares_ok:
                print(f"[OJOS] Hedge bidireccional ON · {', '.join(pares_ok)}")
            if pares_bad:
                print(f"[!] Hedge FALLIDO (MNT): {'; '.join(pares_bad)}")
                await bellion.anotar(
                    "IGRIS", "HEDGE_REQUERIDO",
                    f"Bóveda sin Both Sides: {pares_bad} — "
                    f"abrir long comería el short de colateral.",
                )
                raise SystemExit(2)
            await bellion.anotar(
                "IGRIS", "HEDGE_BOVEDA_OK",
                f"Bidireccional activo · {pares_ok}",
            )
        elif not solo_ojos and not getattr(config, "IGRIS_BOVEDA_EN_LOTE", True):
            print("[OJOS] MNT fuera del lote — short bóveda intacto (sin engorde MNT)")
            await bellion.anotar(
                "IGRIS", "BOVEDA_PAUSA_LOTE",
                "IGRIS_BOVEDA_EN_LOTE=false · MNT no se engorda",
            )

        eq0 = float(getattr(tusk, "masa_bruta_real", 0) or getattr(tusk, "masa_bruta", 0) or 0)
        if eq0 <= 0:
            # Oxígeno aún no late — equity de marcha / fallback
            try:
                eq0 = float((pd.cargar_marcha_payload() or {}).get("equity_usd") or 0)
            except Exception:
                eq0 = 0.0
        if eq0 <= 0:
            eq0 = float(getattr(config, "EQUITY_FALLBACK_USD", 1500) or 1500)
        try:
            pd.sincronizar_logrados_desde_tusk(tusk, eq0)
        except Exception as e:
            print(f"[PASE] sync logrados arranque: {e}")
        meta0 = pd.meta_engorde_usd(eq0, tusk=tusk, marcha_id=pd.cargar_marcha())
        have0 = float(meta0.get("have_usd") or 0)
        need0 = float(meta0.get("need_usd") or 0)
        rest0 = float(meta0.get("restante_usd") or 0)
        pierna0 = float(meta0.get("need_notional_pierna_usd") or 0)
        act0 = str(meta0.get("activo") or "?")
        print(
            f"[PASE] Foco {act0} · paso={meta0.get('paso_n')} {meta0.get('grado')} · "
            f"have=${have0:.2f} need=${need0:.2f} restante=${rest0:.2f} "
            f"pierna≈${pierna0:.2f} capΔ={meta0.get('delta_paso_usd')}"
        )
        plan0 = pd.plan_lote(eq0, marcha_id=pd.cargar_marcha())
        trab = plan0.get("trabajo") or []
        if trab:
            print(
                "[PASE] Trabajo: "
                + ", ".join(
                    f"{p.get('n')}:{p.get('activo')} {p.get('grado')}" for p in trab
                )
            )

        kaiser = KaiserVocero(tank, bellion)
        igris = IgrisEscudo(tusk, tank, bellion, bridge=bridge, kaiser=kaiser)

        # Densidad máxima desde el arranque (antes de engorde)
        if not solo_ojos and getattr(config, "IGRIS_FORCE_MAX_LEVERAGE", True):
            print("[IGRIS] Forzando apalancamiento MÁXIMO en lote (avisos si Bybit baja)…")
            try:
                lev_lote = await igris.forzar_densidad_maxima_lote()
                print(
                    f"[IGRIS] LEVERAGE_MAX_LOTE · ok={lev_lote.get('n_ok')} "
                    f"avisos={lev_lote.get('n_aviso')} Santos={len(lev_lote.get('activos') or [])}"
                )
            except Exception as e:
                print(f"[IGRIS] LEVERAGE_MAX_LOTE aviso: {e}")
                await bellion.anotar("IGRIS", "LEVERAGE_MAX_AVISO", f"lote arranque: {e}")

        from core.validacion import advertir_gates

        advertir_gates()

        panel = PanelDeControl(tusk, igris, tank)

        print("\n[TUSK] Oxígeno real → masa_autorizada (Convert ritual OFF).")
        print("[TANK] Ojos abiertos con orderbook.")
        print("[GREED/BERU] Hibernados.")
        if solo_ojos:
            print("[IGRIS] Hibernado (--solo-ojos).")
        print("Ctrl+C para sellar.\n")

        await bellion.anotar(
            "IGRIS",
            "LIVE_START",
            f"4.0.3 arranque · marcha={mid} · solo_ojos={solo_ojos} · "
            f"testnet={config.TESTNET} · books={'ON' if _books_requeridos() else 'OFF'} · sin Greed/Beru",
        )

        def _spawn(coro):
            t = asyncio.create_task(coro)
            running.append(t)
            return t

        _spawn(tusk.latido_persistencia([]))
        _spawn(tusk.hilo_reconciliacion(bridge))
        _spawn(tank.vigilar_aguas())
        _spawn(bridge.conectar())
        _spawn(bridge.hilo_sincronizacion_nav())
        _spawn(_refrescar_panel(panel))
        _spawn(_publicar_estado(bellion, tusk, igris, tank, kaiser))
        _spawn(_cronica(tusk, tank))
        _spawn(
            _apagado(
                shutdown_event,
                bellion,
                tusk,
                igris,
                started,
                running,
                solo_ojos=solo_ojos,
                libros_ref=libros_ref,
            )
        )

        verde_ok, libros_ok, libros = await _esperar_ojos_y_libros(
            tank,
            bridge,
            timeout_s=float(os.getenv("ARISE_IGRIS_CALENTAMIENTO_S", "300") or 300),
            shutdown_event=shutdown_event,
        )
        libros_ref["libros"] = libros
        if verde_ok and libros_ok:
            libros_ref["veredicto"] = "OJOS_Y_LIBROS_OK"
        elif verde_ok:
            libros_ref["veredicto"] = "VERDE_SIN_LIBROS"
        else:
            libros_ref["veredicto"] = "OJOS_DEBILES"

        _escribir_heartbeat(
            "post_calentamiento",
            {"veredicto": libros_ref["veredicto"], "libros": libros},
        )

        if shutdown_event.is_set():
            for t in running:
                t.cancel()
            await asyncio.gather(*running, return_exceptions=True)
            return

        if not libros_ok:
            if _books_requeridos():
                await bellion.anotar(
                    "TANK",
                    "LIBROS_AUSENTES",
                    f"4.0.3 sin evidencia books ETH: {libros}",
                )
                print("[!] BLOQUEO: sin libros ETH (bids/asks). No se suelta Igris.")
                print("[!] Documentando y sellando — no zombie.")
                snap = _snapshot_cierre(tusk, igris, solo_ojos=True, libros=libros)
                snap["duracion_s"] = round(time.time() - started, 1)
                snap["veredicto_calentamiento"] = libros_ref["veredicto"]
                snap["bloqueo"] = "sin_libros_eth"
                REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
                REPORT_PATH.write_text(json.dumps(snap, indent=2, ensure_ascii=False), encoding="utf-8")
                _escribir_heartbeat("bloqueo_sin_libros", {"sellado": True, "bloqueo": True})
                shutdown_event.set()
                for t in running:
                    if not t.done():
                        t.cancel()
                await asyncio.gather(*running, return_exceptions=True)
                raise SystemExit(2)
            # Modo last_price: sin muros no es bloqueo duro si hay VERDE flojo
            await bellion.anotar(
                "TANK",
                "OJOS_LAST_DEBIL",
                f"calentamiento sin ticker fuerte · verde={verde_ok} · {libros}",
            )
            print("[!] Aviso: last price flojo — continuo en solo observación / Asalto holgado.")

        # Tras ojos: Kaiser / sentidos (Binance OFF en ojos estrechos)
        _spawn(kaiser.vigilar_indicadores())
        _spawn(bridge.hilo_sentidos_extra())
        if binance_ref and getattr(config, "BINANCE_REF_ENABLED", True):
            _spawn(binance_ref.conectar())

        if segundos > 0:
            _spawn(_corte_tiempo(shutdown_event, segundos))

        if solo_ojos:
            print("[OJOS] Smoke solo-ojos — Igris no arranca. Observando plan/restante…")
            await bellion.anotar("IGRIS", "SOLO_OJOS", "calentamiento OK · sin manos Igris")
            # Parte claro al Monarca: qué mordiría si soltara manos
            try:
                eqv = float(
                    getattr(tusk, "masa_bruta_real", 0)
                    or getattr(tusk, "masa_bruta", 0)
                    or 0
                )
                mid = pd.cargar_marcha()
                meta = pd.meta_engorde_usd(eqv, tusk=tusk, marcha_id=mid)
                print(
                    f"[PLAN] Si manos ON → {meta.get('activo')} paso {meta.get('paso_n')} "
                    f"{meta.get('grado')} · restante≈${float(meta.get('restante_usd') or 0):.2f} "
                    f"(have ${float(meta.get('have_usd') or 0):.2f} / need ${float(meta.get('need_usd') or 0):.2f})"
                )
            except Exception as e:
                print(f"[PLAN] no disponible: {e}")
        else:
            print("[IGRIS] vigilar_manto_operativo — manos reales ON.")
            if not verde_ok:
                await bellion.anotar("TANK", "OJOS_DEBILES", "Igris arranca con verde flojo.")
            _spawn(igris.vigilar_manto_operativo())

        await asyncio.gather(*running, return_exceptions=True)

    except SystemExit:
        raise
    except Exception:
        print("\n[!] ERROR EN RITUAL IGRIS LIVE:")
        traceback.print_exc()
        for t in running:
            t.cancel()
        raise


def main():
    ap = argparse.ArgumentParser(
        description="4.0.3 Igris — ojos Santos last price (books OFF) · manos con flag"
    )
    ap.add_argument("--segundos", type=float, default=0.0, help="Corte tras N s (post-arranque total)")
    ap.add_argument("--horas", type=float, default=0.0, help="Duración en horas")
    ap.add_argument(
        "--durar-hasta",
        type=str,
        default="",
        help="Deadline local YYYY-MM-DDTHH:MM:SS",
    )
    ap.add_argument(
        "--solo-ojos",
        action="store_true",
        help="Calentamiento + plan restante sin Igris manos",
    )
    ap.add_argument(
        "--permitir-mainnet-manos",
        action="store_true",
        help="Obligatorio si MODO_TESTNET=False y se sueltan manos Igris",
    )
    args = ap.parse_args()

    permitir = args.permitir_mainnet_manos or _truthy(os.getenv("ARISE_IGRIS_PERMITIR_MAINNET"))
    try:
        seg = _segundos_desde_flags(
            segundos=args.segundos,
            horas=args.horas,
            durar_hasta=args.durar_hasta,
        )
    except SystemExit as e:
        print(e)
        raise SystemExit(2) from e

    # Default smoke-friendly si no hay duración (guardián suele pasar deadline)
    if seg <= 0 and not args.durar_hasta and args.horas <= 0 and args.segundos <= 0:
        print("[LIVE] Sin duración: corre hasta Ctrl+C (guardián debe pasar --durar-hasta).")

    asyncio.run(
        ritual_igris_live(
            segundos=seg,
            solo_ojos=args.solo_ojos,
            permitir_mainnet=permitir,
        )
    )


if __name__ == "__main__":
    try:
        main()
    except SystemExit as e:
        code = int(e.code) if isinstance(e.code, int) else (1 if e.code else 0)
        raise SystemExit(code)
