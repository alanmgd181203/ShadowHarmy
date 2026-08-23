#!/usr/bin/env python3
"""Prepara lote Beru rango (perfil normal) — SIN despertar.

Valida Santos, apalancamiento máximo del juicio, paths y doctrina.
Escribe manifiesto + comandos listos para cuando el Monarca diga GO.

Uso:
  python scripts/preparar_beru_rango_lote_despertar.py
  python scripts/preparar_beru_rango_lote_despertar.py --santos VVV,HYPE,LIT
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["BERU_RANGO_MANOS"] = "false"
os.environ.setdefault("MODO_SIMULACION", "true")
os.environ["BERU_RANGO_PERFIL"] = "normal"

import core.config as config  # noqa: E402
from core import beru_rango  # noqa: E402
from core import beru_rango_paths  # noqa: E402

LOTE_DEFAULT = (
    "VVV,AKT,XLM,CC,HYPE,NEAR,ZEREBRO,LIT,MORPHO,MON,KORU,AXTI,NBIS,SAMSUNG"
)
OUT_JSON = beru_rango_paths.RANGO_DIR / "lote_despertar_ejercito.json"
OUT_MD = beru_rango_paths.RANGO_DIR / "LOTE_DESPERTAR_EJERCITO.md"
FICHAS = ROOT / "data" / "coliseo" / "rango_juicio" / "santos_ficha.json"
FILTROS = ROOT / "data" / "coliseo" / "rango_juicio" / "filtros_absolutos.json"
VIVO = ROOT / "data" / "beru" / "rango_vivo.json"


def _parse_santos(raw: str) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for part in str(raw or "").replace(";", ",").split(","):
        a = part.strip().upper()
        if a and a not in seen:
            seen.add(a)
            out.append(a)
    return out


def _ficha(act: str, fichas: dict[str, Any]) -> dict[str, Any]:
    return fichas.get(act) or {}


def _lev(act: str, filtros: dict[str, Any], ficha: dict[str, Any]) -> float | None:
    fx = filtros.get(act) or {}
    for src in (fx.get("max_leverage"), ficha.get("max_leverage")):
        try:
            v = float(src)
            if v > 0:
                return v
        except (TypeError, ValueError):
            pass
    return None


def _vivo_activos() -> dict[str, Any]:
    if not VIVO.is_file():
        return {}
    try:
        data = json.loads(VIVO.read_text(encoding="utf-8"))
    except Exception:
        return {}
    out: dict[str, Any] = {}
    for row in data.get("activos") or []:
        a = str(row.get("activo") or "").upper()
        if a:
            out[a] = row
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Preparar lote despertar Beru rango normal")
    ap.add_argument("--santos", default=LOTE_DEFAULT, help="Lista comma-separated")
    ap.add_argument("--perfil", default="normal", choices=["normal", "feria"])
    args = ap.parse_args()

    config.aplicar_perfil_beru_rango(args.perfil)
    santos = _parse_santos(args.santos)
    if not santos:
        print("FALLO: lista vacía", flush=True)
        return 2

    fichas = (json.loads(FICHAS.read_text(encoding="utf-8")).get("por_base") or {}) if FICHAS.is_file() else {}
    filtros = (json.loads(FILTROS.read_text(encoding="utf-8")).get("activos") or {}) if FILTROS.is_file() else {}
    vivo = _vivo_activos()
    geo = beru_rango.resumen_geometria()

    filas: list[dict[str, Any]] = []
    fallos = 0
    for act in santos:
        f = _ficha(act, fichas)
        sym = str(f.get("symbol") or f"{act}USDT")
        lev = _lev(act, filtros, f)
        v = vivo.get(act) or {}
        en_vivo = bool(v)
        ok = bool(f.get("symbol") or f.get("base"))
        if not ok:
            fallos += 1
        filas.append(
            {
                "activo": act,
                "symbol": sym,
                "ok_ficha": ok,
                "max_leverage": lev,
                "tradefi": bool(f.get("tradefi")),
                "symbol_type": f.get("symbol_type"),
                "en_vivo_ahora": en_vivo,
                "estado_vivo": v.get("estado"),
                "pid_vivo": v.get("pid"),
                "path_ojos": str(beru_rango_paths.ojos_eventos(act)),
                "path_manos": str(beru_rango_paths.manos_informe(act)),
            }
        )

    lista_csv = ",".join(santos)
    cmd_ojos = f"python scripts/arise_beru_rango_ojos.py --santos {lista_csv}"
    cmds_manos = [
        f"python scripts/arise_beru_rango_manos.py --activo {a} --manos-go --continuar"
        for a in santos
    ]

    payload = {
        "ts": time.time(),
        "ts_utc": datetime.now(timezone.utc).isoformat(),
        "estado": "PREPARADO_SIN_WAKE",
        "perfil_beru": args.perfil,
        "apalancamiento": "maximo_por_contrato_al_despertar",
        "n_santos": len(santos),
        "n_fallos_ficha": fallos,
        "santos": filas,
        "geometria": geo,
        "env_despertar": {
            "BERU_RANGO_PERFIL": args.perfil,
            "IGRIS_FORCE_MAX_LEVERAGE": "true",
            "BERU_RANGO_MANOS": "false_para_ojos_true_para_manos",
        },
        "comandos": {
            "ojos_una_flota": cmd_ojos,
            "manos_un_proceso_por_santo": cmds_manos,
        },
        "nota_lit": (
            "LIT puede estar vivo en esta lap (manos ON). "
            "Al cambiar de máquina: Ctrl+C manos LIT o cerrar PID antes de relanzar el lote."
        ),
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    md_lines = [
        "# Lote despertar — Beru rango original (sin wake aún)",
        "",
        f"Generado: {payload['ts_utc']}",
        f"Perfil: **{args.perfil}** · apalancamiento: **máximo** al `--manos-go`",
        f"Santos: **{len(santos)}**",
        "",
        "## Antes de despertar (otra lap / nueva máquina)",
        "",
        "1. **Pausar LIT** si sigue vivo aquí (Ctrl+C en terminal manos, o cerrar PID del panel).",
        "2. `git pull` si el código viene del repo.",
        "3. API Bybit cargada · `MODO_SIMULACION=false` solo en manos con `--manos-go`.",
        "",
        "## Ojos (una flota · sin manos)",
        "",
        "```powershell",
        f"$env:BERU_RANGO_PERFIL = \"{args.perfil}\"",
        cmd_ojos,
        "```",
        "",
        "## Manos (un proceso por Santo · GO explícito)",
        "",
        "```powershell",
        f"$env:BERU_RANGO_PERFIL = \"{args.perfil}\"",
        f"$env:IGRIS_FORCE_MAX_LEVERAGE = \"true\"",
        "# Repetir en terminal aparte por Santo:",
    ]
    for c in cmds_manos:
        md_lines.append(c)
    md_lines.extend(
        [
            "```",
            "",
            "## Santos",
            "",
            "| Santo | Symbol | Lev máx | TradeFi | Vivo ahora |",
            "|-------|--------|---------|---------|------------|",
        ]
    )
    for row in filas:
        md_lines.append(
            f"| {row['activo']} | {row['symbol']} | {row['max_leverage'] or '—'} | "
            f"{'✓' if row['tradefi'] else ''} | "
            f"{row['estado_vivo'] or '—'}{' (pid '+str(row['pid_vivo'])+')' if row['pid_vivo'] else ''} |"
        )
    md_lines.extend(["", f"JSON: `{OUT_JSON}`", ""])
    OUT_MD.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    print("═" * 56)
    print("  PREPARAR LOTE DESPERTAR — Beru rango (sin wake)")
    print("═" * 56)
    print(f"  Perfil: {args.perfil} · apalanc: máximo al manos-go")
    print(f"  Santos: {len(santos)} · fallos ficha: {fallos}")
    for row in filas:
        mark = "OK" if row["ok_ficha"] else "??"
        live = f" VIVO={row['estado_vivo']}" if row["en_vivo_ahora"] else ""
        print(
            f"  [{mark}] {row['activo']:8} {row['symbol']:14} "
            f"lev={row['max_leverage'] or '?'}{live}"
        )
    print("─" * 56)
    print(f"  Manifiesto: {OUT_JSON}")
    print(f"  Runbook:    {OUT_MD}")
    print("  NO se despertó nada. Cuando digas GO → ojos primero, luego manos por Santo.")
    print()
    return 0 if fallos == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
