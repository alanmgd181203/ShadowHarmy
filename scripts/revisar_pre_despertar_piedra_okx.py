#!/usr/bin/env python3
"""Auditoría pre-despertar — Beru rango piedra OKX (doctrina 22b + 23).

No despierta nada. Compara código, teatro y JSON de asignación contra doctrina.
Un smoke verde no basta: aquí se marcan huecos (calor Bybit, sin live OKX, etc.).

Salida: data/beru/rango/pre_despertar_piedra_okx.json

Uso:
  python scripts/revisar_pre_despertar_piedra_okx.py
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ.setdefault("BERU_MAR", "okx")
os.environ.setdefault("BERU_RANGO_MANOS", "false")
os.environ.setdefault("MODO_SIMULACION", "true")
os.environ.setdefault("BERU_RANGO_PERFIL", "piedra")

OUT = ROOT / "data" / "beru" / "rango" / "pre_despertar_piedra_okx.json"
ASIG = ROOT / "data" / "beru" / "rango" / "piedra_asignacion.json"
RANGO_FILTRO = ROOT / "data" / "coliseo" / "rango_juicio" / "filtros_rango_okx_teatro.json"
LIQ_FILTRO = ROOT / "data" / "coliseo" / "rango_juicio" / "filtros_liquidez_okx.json"
CATALOGO = ROOT / "data" / "coliseo" / "rango_juicio" / "teatro_okx_catalogo.json"
MIN_TOPE_USD = 1.50


def _chk(nombre: str, ok: bool, detalle: str, *, severidad: str = "bloqueo") -> dict[str, Any]:
    return {
        "check": nombre,
        "ok": bool(ok),
        "severidad": severidad,
        "detalle": detalle,
    }


def _load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _flota_esperada(rango_data: dict[str, Any]) -> set[str]:
    bases: set[str] = set()
    for base, row in (rango_data.get("activos") or {}).items():
        if not isinstance(row, dict):
            continue
        banda = str(row.get("rango_banda") or "").lower()
        if banda in ("verde", "amarillo", "rojo") and not row.get("rango_fuera"):
            bases.add(str(base).upper())
    return bases


def _run_smoke(script: str) -> tuple[bool, str]:
    path = ROOT / "scripts" / script
    if not path.is_file():
        return False, f"falta {script}"
    try:
        r = subprocess.run(
            [sys.executable, str(path)],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=120,
            env={**os.environ},
        )
        tail = (r.stdout or "")[-400:] + (r.stderr or "")[-200:]
        if r.returncode == 0:
            return True, f"exit 0 · {tail.strip()[-120:]}"
        return False, f"exit {r.returncode} · {tail.strip()[-200:]}"
    except subprocess.TimeoutExpired:
        return False, "timeout 120s"
    except Exception as exc:
        return False, str(exc)


def main() -> int:
    import core.config as config
    from core import beru_bridge
    from core import beru_mar
    from core import beru_rango
    from core import beru_rango_semaforo as sem
    from core import lote_beru as lb
    from core import lote_okx

    config.aplicar_perfil_beru_rango("piedra")
    beru_rango.invalidar_piedra_asignacion()

    checks: list[dict[str, Any]] = []
    avisos: list[str] = []
    bloqueos = 0

    # —— Mar y perfil ——
    mar_ok = beru_mar.es_okx() and str(getattr(config, "BERU_MAR", "")).lower() == "okx"
    checks.append(_chk("mar_okx", mar_ok, f"BERU_MAR={getattr(config, 'BERU_MAR', '?')}"))
    if not mar_ok:
        bloqueos += 1

    perfil_ok = str(getattr(config, "BERU_RANGO_PERFIL", "")) == "piedra"
    checks.append(_chk("perfil_piedra", perfil_ok, f"BERU_RANGO_PERFIL={config.BERU_RANGO_PERFIL}"))
    if not perfil_ok:
        bloqueos += 1

    # —— Doctrina geometría (22b) ——
    geo = beru_rango.resumen_geometria()
    doctrina_ok = (
        geo.get("nacimiento") == "piedra_usd"
        and geo.get("engorde_modo") == "peldaños_sumados"
        and geo.get("saco_techo") == "peldaños_sumados"
        and geo.get("engorde") == "desde_activacion"
        and geo.get("cero") == "wake"
        and abs(float(geo.get("masa_usd") or 0) - 0.20) < 1e-9
        and abs(float(geo.get("red_activacion_short_pct") or geo.get("red_activacion_pct") or 0) - 0.008) < 1e-6
    )
    checks.append(
        _chk(
            "doctrina_piedra",
            doctrina_ok,
            f"nacimiento={geo.get('nacimiento')} engorde={geo.get('engorde_modo')} "
            f"masa={geo.get('masa_usd')} red_short={geo.get('red_activacion_short_pct')}",
        )
    )
    if not doctrina_ok:
        bloqueos += 1

    # —— Manos OFF ——
    manos = bool(getattr(config, "BERU_RANGO_MANOS", False))
    checks.append(_chk("manos_off", not manos, f"BERU_RANGO_MANOS={manos}"))
    if manos:
        bloqueos += 1

    # —— Puente OKX ——
    try:
        from core.okx_bridge import OkxBridge
        from core.bellion import BellionAuditor
        from generales.tank import TankCluster
        from generales.tusk import TuskBoveda

        bellion = BellionAuditor()
        tusk = TuskBoveda(bellion)
        tank = TankCluster(tusk, bellion)
        br = beru_bridge.crear_beru_bridge(tank, tusk, bellion, ws_bases=["ETH"])
        bridge_ok = isinstance(br, OkxBridge) and beru_bridge.nombre_mar() == "OKX"
        checks.append(_chk("puente_okx", bridge_ok, f"tipo={type(br).__name__} mar={beru_bridge.nombre_mar()}"))
        if not bridge_ok:
            bloqueos += 1
    except Exception as exc:
        checks.append(_chk("puente_okx", False, str(exc)))
        bloqueos += 1

    # —— Asignación piedra ——
    asig = _load_json(ASIG)
    activos_asig = asig.get("activos") or {}
    rango_data = _load_json(RANGO_FILTRO)
    flota_esperada = _flota_esperada(rango_data)
    asig_keys = {str(k).upper() for k in activos_asig}
    faltan = sorted(flota_esperada - asig_keys)
    sobran = sorted(asig_keys - flota_esperada)
    asig_ok = len(activos_asig) > 0 and not faltan
    checks.append(
        _chk(
            "piedra_asignacion_flota",
            asig_ok,
            f"n={len(activos_asig)} esperados={len(flota_esperada)} "
            f"faltan={len(faltan)} sobran={len(sobran)}",
        )
    )
    if not asig_ok:
        bloqueos += 1
        if faltan[:5]:
            avisos.append(f"Asignación incompleta — faltan ej: {', '.join(faltan[:5])}")

    # —— Semáforo coherente con rango banda ——
    incoherentes: list[str] = []
    for base in flota_esperada & asig_keys:
        row_r = (rango_data.get("activos") or {}).get(base) or {}
        row_a = activos_asig.get(base) or activos_asig.get(base.lower()) or {}
        banda = str(row_r.get("rango_banda") or "").lower()
        sem_asig = str((row_a if isinstance(row_a, dict) else {}).get("semaforo") or "").lower()
        esperado = banda  # verde/amarillo/rojo 1:1
        if sem_asig and esperado and sem_asig != esperado:
            incoherentes.append(f"{base}:{banda}→{sem_asig}")
    sem_ok = not incoherentes
    checks.append(
        _chk(
            "semaforo_coherente_rango",
            sem_ok,
            f"incoherentes={len(incoherentes)} ej={incoherentes[:3]}",
        )
    )
    if not sem_ok:
        bloqueos += 1

    # —— Muestra: semáforo resuelve masa nacimiento ——
    muestra_ok = True
    muestra_det = []
    for color, masa_esperada in (("rojo", 0.20), ("amarillo", 0.30), ("verde", 0.50)):
        m = sem.masa_nacimiento_por_bando(color, "paz")
        if abs(m - masa_esperada) > 1e-9:
            muestra_ok = False
        muestra_det.append(f"{color}=${m:g}")
    checks.append(_chk("mapa_semaforo_masa", muestra_ok, " · ".join(muestra_det)))
    if not muestra_ok:
        bloqueos += 1

    # —— Catálogo OKX cubre flota ——
    cat = _load_json(CATALOGO)
    cat_set = {str(r.get("activo") or "").upper() for r in (cat.get("activos") or []) if r}
    sin_cat = sorted(flota_esperada - cat_set)
    cat_ok = not sin_cat
    checks.append(
        _chk("catalogo_okx_flota", cat_ok, f"sin_catalogo={len(sin_cat)} ej={sin_cat[:5]}")
    )
    if not cat_ok:
        bloqueos += 1

    # —— Min orden ≤ $1.50 en flota ——
    cat_map = {str(r.get("activo") or "").upper(): r for r in (cat.get("activos") or [])}
    min_altos: list[str] = []
    for base in sorted(flota_esperada):
        row = cat_map.get(base) or {}
        min_u = float(row.get("min_usd") or 0)
        if min_u > MIN_TOPE_USD + 1e-6:
            min_altos.append(f"{base}:${min_u:.2f}")
    min_ok = not min_altos
    checks.append(
        _chk(
            "min_orden_flota",
            min_ok,
            f"tope=${MIN_TOPE_USD} altos={len(min_altos)} ej={min_altos[:5]}",
        )
    )
    if not min_ok:
        bloqueos += 1

    # —— Lote OKX floor (WLD muestra) ——
    lote_ok = False
    lote_det = ""
    try:
        pack = lb.masa_a_qty_con_deuda(0.50, 0.365, "WLDUSDT_LINEAL", usar_floor=True)
        lote_ok = bool(pack.get("ok"))
        lote_det = f"WLD notional={pack.get('notional_usd')} deuda={pack.get('deuda_usd')}"
    except Exception as exc:
        lote_det = str(exc)
    checks.append(_chk("lote_okx_floor", lote_ok, lote_det))
    if not lote_ok:
        bloqueos += 1

    # —— Smokes ——
    ok_piedra, det_p = _run_smoke("validar_beru_rango_piedra_smoke.py")
    checks.append(_chk("smoke_piedra", ok_piedra, det_p))
    if not ok_piedra:
        bloqueos += 1

    ok_ojos, det_o = _run_smoke("validar_beru_rango_ojos_smoke.py")
    checks.append(_chk("smoke_ojos_logica", ok_ojos, det_o))
    if not ok_ojos:
        bloqueos += 1

    # —— Avisos doctrinales (no bloquean volcado pero sí wake prudente) ——
    rango_meta = rango_data.get("meta") or {}
    if "bybit" in str(rango_meta.get("fuente_rango") or rango_meta.get("nota") or "").lower():
        avisos.append("Rango anual 1a viene de bóveda Bybit — no es histórico OKX nativo.")
    liq_meta = (_load_json(LIQ_FILTRO)).get("meta") or {}
    liq_ts = liq_meta.get("ts_utc") or ""
    if liq_ts:
        avisos.append(f"Scan liquidez OKX: {liq_ts} — re-escanear si el mercado movió mucho.")
    avisos.append("Sin prueba live OKX (ojos WS + manos paper) — bloqueo blando para primer wake.")
    avisos.append("Calor > BTC usa juicio Bybit (matriz normal/feria) — no ranking OKX propio.")
    if len([b for b in flota_esperada if str((activos_asig.get(b) or {}).get("semaforo")) == "verde"]) <= 8:
        verdes = [b for b in flota_esperada if (activos_asig.get(b) or {}).get("semaforo") == "verde"]
        avisos.append(f"Solo {len(verdes)} verdes en flota — revisar si son Santos reales: {verdes[:6]}")

    # —— Veredicto ——
    go_wake = bloqueos == 0
    veredicto = "LISTO_REVISION" if go_wake else "NO_DESPERTAR"
    nota_wake = (
        "Geometría y asignación pasan. Siguiente: ojos paper en 2–3 Santos nombrados, "
        "luego manos con --manos-go en uno solo."
        if go_wake
        else f"{bloqueos} bloqueo(s) — corregir antes de nombrar Santos."
    )

    sello = {
        "ts": time.time(),
        "ts_utc": datetime.now(timezone.utc).isoformat(),
        "veredicto": veredicto,
        "go_wake": go_wake,
        "bloqueos": bloqueos,
        "checks": checks,
        "avisos": avisos,
        "geometria": geo,
        "flota": {
            "n_esperada": len(flota_esperada),
            "n_asignacion": len(activos_asig),
            "conteo_semaforo": (asig.get("meta") or {}).get("conteo_semaforo"),
        },
        "nota_wake": nota_wake,
        "ritual_siguiente": [
            "python scripts/arise_beru_rango_ojos.py --santos WLD,UNI (paper)",
            "python scripts/arise_beru_rango_manos.py --activo WLD --manos-go (solo con GO Monarca)",
        ],
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(sello, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print("=" * 58)
    print("  REVISION PRE-DESPERTAR — Beru piedra OKX")
    print("=" * 58)
    for c in checks:
        tag = "OK" if c["ok"] else "FAIL"
        print(f"  [{tag}] {c['check']}: {c['detalle'][:100]}")
    print("-" * 58)
    for a in avisos:
        print(f"  ! {a}")
    print("-" * 58)
    print(f"  Veredicto: {veredicto} ({bloqueos} bloqueos)")
    print(f"  Sello: {OUT}")
    print(f"  {nota_wake}")
    print()
    return 0 if go_wake else 1


if __name__ == "__main__":
    raise SystemExit(main())
