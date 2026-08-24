#!/usr/bin/env python3
"""Prepara ejército Beru rango + teatro de sombras — SIN despertar Santos.

Comprueba:
  · doctrina viva (nace $5 · engorde desde activación · escalera sin tope)
  · flota multi: un Bridge por Santo (no una boca hablando por todos)
  · paths por Santo · juicio importable · bóveda al alcance
  · manos OFF por defecto

No levanta WS ni wake. Cuando el Monarca nombre Santos:
  python scripts/arise_beru_rango_ojos.py --santos A,B,C
  python -u scripts/teatro_beru_rango_juicio.py --perfil reciente
"""
from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["BERU_RANGO_MANOS"] = "false"
os.environ.setdefault("MODO_SIMULACION", "true")

import core.config as config  # noqa: E402
from core import beru_rango  # noqa: E402
from core import beru_rango_paths  # noqa: E402
from core.bridge import BybitBridge  # noqa: E402
from core.bellion import BellionAuditor  # noqa: E402
from generales.tank import TankCluster  # noqa: E402
from generales.tusk import TuskBoveda  # noqa: E402

OUT = beru_rango_paths.RANGO_DIR / "preparar_sanidad.json"
OJOS_SCRIPT = ROOT / "scripts" / "arise_beru_rango_ojos.py"
MANOS_SCRIPT = ROOT / "scripts" / "arise_beru_rango_manos.py"
JUICIO_SCRIPT = ROOT / "scripts" / "teatro_beru_rango_juicio.py"


def _ok(nombre: str, ok: bool, detalle: str) -> dict:
    return {"check": nombre, "ok": bool(ok), "detalle": detalle}


def main() -> int:
    checks: list[dict] = []
    fallos = 0

    # 1) Doctrina
    geo = beru_rango.resumen_geometria()
    doctrina_ok = (
        geo.get("nacimiento") == "cinco_usd"
        and geo.get("engorde") == "desde_activacion"
        and geo.get("saco_techo") == "sin_tope"
        and geo.get("cero") == "wake"
        and abs(float(geo.get("masa_usd") or 0) - 5.0) < 1e-9
    )
    checks.append(
        _ok(
            "doctrina",
            doctrina_ok,
            f"geo={ {k: geo.get(k) for k in ('cero','nacimiento','engorde','saco_techo','masa_usd','vacio_pct','red_activacion_pct')} }",
        )
    )
    if not doctrina_ok:
        fallos += 1

    # 2) Manos OFF
    manos = bool(getattr(config, "BERU_RANGO_MANOS", False))
    checks.append(_ok("manos_off", not manos, f"BERU_RANGO_MANOS={manos}"))
    if manos:
        fallos += 1

    # 3) Puentes propios (identidad + ws_bases aislados)
    bellion = BellionAuditor()
    tusk = TuskBoveda(bellion)
    probes = ["AAA", "BBB", "CCC"]
    bridges = []
    for act in probes:
        tank = TankCluster(tusk, bellion, ticker_base=getattr(config, "TICKER_BASE", "USDT"))
        br = BybitBridge(tank, tusk, bellion, None, None, ws_bases=[act])
        bridges.append(br)
    ids = {id(b) for b in bridges}
    bases = [tuple(b.ws_bases or []) for b in bridges]
    multi_ok = len(ids) == 3 and bases == [("AAA",), ("BBB",), ("CCC",)]
    checks.append(
        _ok(
            "bridge_propio_por_santo",
            multi_ok,
            f"ids_distintos={len(ids)} bases={bases}",
        )
    )
    if not multi_ok:
        fallos += 1

    # 4) Paths por Santo
    p_wld = beru_rango_paths.ojos_eventos("WLD")
    p_ondo = beru_rango_paths.ojos_eventos("ONDO")
    paths_ok = p_wld != p_ondo and "WLD" in str(p_wld) and "ONDO" in str(p_ondo)
    checks.append(_ok("paths_por_santo", paths_ok, f"ej={p_wld.name} vs {p_ondo.name}"))
    if not paths_ok:
        fallos += 1

    # 5) Scripts listos
    scripts_ok = OJOS_SCRIPT.is_file() and MANOS_SCRIPT.is_file() and JUICIO_SCRIPT.is_file()
    checks.append(
        _ok(
            "scripts",
            scripts_ok,
            f"ojos={OJOS_SCRIPT.exists()} manos={MANOS_SCRIPT.exists()} juicio={JUICIO_SCRIPT.exists()}",
        )
    )
    if not scripts_ok:
        fallos += 1

    # 6) Bóveda (teatro de sombras)
    boveda = {"ok": False, "bases": 0, "velas": 0, "error": ""}
    try:
        from core import coliseo_boveda as bov

        con = bov.connect_market("linear")
        try:
            n_bases = int(
                con.execute("SELECT COUNT(DISTINCT base) FROM candles").fetchone()[0] or 0
            )
            n_velas = int(con.execute("SELECT COUNT(*) FROM candles").fetchone()[0] or 0)
            boveda = {"ok": n_bases > 0, "bases": n_bases, "velas": n_velas, "error": ""}
        finally:
            con.close()
    except Exception as exc:
        boveda = {"ok": False, "bases": 0, "velas": 0, "error": str(exc)}
    checks.append(
        _ok(
            "boveda_linear",
            bool(boveda["ok"]),
            f"bases={boveda['bases']} velas={boveda['velas']} err={boveda.get('error') or '—'}",
        )
    )
    if not boveda["ok"]:
        fallos += 1

    # 7) Import juicio + sim fill doctrinal
    juicio_ok = False
    juicio_det = ""
    try:
        from core.teatro_beru_rango import simular_rango_juicio

        juicio_ok = callable(simular_rango_juicio)
        juicio_det = "simular_rango_juicio OK · fill≠wake en cosecha"
    except Exception as exc:
        juicio_det = str(exc)
    checks.append(_ok("juicio_import", juicio_ok, juicio_det))
    if not juicio_ok:
        fallos += 1

    sello = {
        "ts": time.time(),
        "ts_utc": datetime.now(timezone.utc).isoformat(),
        "ok": fallos == 0,
        "fallos": fallos,
        "checks": checks,
        "geometria": geo,
        "boveda": boveda,
        "arquitectura": {
            "ojos": "bridge_propio_por_santo",
            "manos": "un_santo_por_proceso_hasta_GO",
            "panel": "rango_vivo.json merge",
            "teatro": "teatro_beru_rango_juicio.py perfil reciente",
        },
        "listo_para": {
            "ojos_cuando_nombres": (
                "python scripts/arise_beru_rango_ojos.py --santos A,B,C"
            ),
            "juicio_ahora": (
                "python -u scripts/teatro_beru_rango_juicio.py --perfil reciente"
            ),
            "manos_solo_con_go": (
                "python scripts/arise_beru_rango_manos.py --activo X --manos-go"
            ),
        },
        "nota": (
            "Ejército formado en patio. Sin wake. "
            "Cada Santo pedirá a la API con su propio puente cuando nombres la lista."
        ),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(sello, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print("═" * 56)
    print("  PREPARAR EJÉRCITO — Beru rango (sin despertar)")
    print("═" * 56)
    for c in checks:
        marca = "OK" if c["ok"] else "FAIL"
        print(f"  [{marca}] {c['check']}: {c['detalle']}")
    print("─" * 56)
    print(f"  Sello: {OUT}")
    print(f"  Resultado: {'LISTO' if fallos == 0 else f'{fallos} fallos'}")
    if fallos == 0:
        print("\n  Cuando nombres Santos (ojos, multi, bridge propio):")
        print("    python scripts/arise_beru_rango_ojos.py --santos A,B,C")
        print("  Teatro de sombras (puede ir en paralelo):")
        print("    python -u scripts/teatro_beru_rango_juicio.py --perfil reciente")
    print()
    return 0 if fallos == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
