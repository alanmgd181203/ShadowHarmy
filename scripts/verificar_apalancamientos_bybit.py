#!/usr/bin/env python3
"""Verifica apalancamientos máximos REALES en Bybit (instruments-info).

Por qué existe: la IP del Monarca / forja a veces recibe HTTP 403 de api.bybit.com.
Correr en la Mac de Jess (México) o cualquier red que sí llegue a Bybit.

Qué hace:
  1) Baja maxLeverage linear (USDT) + inverse por cada activo de la flota.
  2) Compara contra core.config (hardcode) y, si existe, el diccionario JSON.
  3) Imprime tabla + discrepancias. Opcional: --apply-config (parchea config.py).

Uso (desde raíz del repo):
  python scripts/verificar_apalancamientos_bybit.py
  python scripts/verificar_apalancamientos_bybit.py --json data/apalancamientos_bybit_vivo.json
  python scripts/verificar_apalancamientos_bybit.py --regen-dict   # llama generar_diccionario_beru

Fuente de verdad Bybit:
  GET /v5/market/instruments-info → leverageFilter.maxLeverage
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import core.config as config

API = "https://api.bybit.com"
DICT_PATH = ROOT / "config" / "diccionario_beru_flota_manto.json"

# Activos a chequear: unión flota config + diccionario si existe
CORE_ASSETS = [
    "BTC", "ETH", "LTC", "SOL", "XRP", "DOGE", "ADA", "LINK", "AVAX", "MATIC",
    "DOT", "UNI", "ATOM", "FIL", "APT", "ARB", "OP", "SUI", "WIF", "PEPE",
    "AAVE", "HYPE", "MNT", "NEAR", "BCH", "ETC", "XLM",
]


def _get_json(path: str) -> dict[str, Any]:
    url = f"{API}{path}"
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "ShadowHarmy-LevCheck/1.0",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=45) as resp:
        return json.loads(resp.read().decode())


def _max_lev(instr: dict[str, Any] | None) -> float | None:
    if not instr:
        return None
    lf = instr.get("leverageFilter") or {}
    try:
        lev = float(lf.get("maxLeverage") or 0)
    except (TypeError, ValueError):
        return None
    return lev if lev > 0 else None


def fetch_instrument(category: str, symbol: str) -> dict[str, Any] | None:
    data = _get_json(f"/v5/market/instruments-info?category={category}&symbol={symbol}")
    if int(data.get("retCode") or -1) != 0:
        raise RuntimeError(f"{symbol} {category}: {data.get('retMsg')}")
    lst = (data.get("result") or {}).get("list") or []
    return lst[0] if lst else None


def probe_api() -> None:
    """Falla rápido si la IP está bloqueada (403)."""
    try:
        fetch_instrument("linear", "BTCUSDT")
    except urllib.error.HTTPError as e:
        if e.code == 403:
            print("=" * 72)
            print("  BLOQUEO: Bybit devolvio HTTP 403 (IP/region).")
            print("  Corre este script en la Mac de Jess (Mexico) u otra red.")
            print("=" * 72)
        raise


def load_dict_leverage() -> dict[str, dict[str, float]]:
    if not DICT_PATH.is_file():
        return {}
    raw = json.loads(DICT_PATH.read_text(encoding="utf-8"))
    out: dict[str, dict[str, float]] = {}
    for a, row in (raw.get("activos") or {}).items():
        out[a.upper()] = {
            "linear": float(row.get("max_leverage_linear") or 0),
            "inverse": float(row.get("max_leverage_inverse") or 0),
            "avg": float(row.get("lev_promedio") or 0),
        }
    return out


def assets_to_check() -> list[str]:
    s = set(CORE_ASSETS)
    s |= set(getattr(config, "ACTIVOS_BERU_FLOTA", []) or [])
    s |= set(getattr(config, "MANTO_LEVERAGE_LINEAR_MAX_BY_ASSET", {}) or {})
    d = load_dict_leverage()
    s |= set(d.keys())
    return sorted(s)


def check_one(asset: str) -> dict[str, Any]:
    lin_sym = f"{asset}USDT"
    inv_sym = f"{asset}USD"
    lin = fetch_instrument("linear", lin_sym)
    try:
        inv = fetch_instrument("inverse", inv_sym)
    except RuntimeError:
        inv = None

    lev_l = _max_lev(lin)
    lev_i = _max_lev(inv)
    avg = None
    if lev_l and lev_i:
        avg = (lev_l + lev_i) / 2.0
    elif lev_l:
        avg = lev_l
    elif lev_i:
        avg = lev_i

    cfg_l = float((getattr(config, "MANTO_LEVERAGE_LINEAR_MAX_BY_ASSET", {}) or {}).get(asset, 0) or 0)
    cfg_i = float((getattr(config, "MANTO_LEVERAGE_INVERSE_MAX_BY_ASSET", {}) or {}).get(asset, 0) or 0)
    dict_row = load_dict_leverage().get(asset, {})

    return {
        "activo": asset,
        "symbol_linear": lin_sym if lin else None,
        "symbol_inverse": inv_sym if inv else None,
        "status_linear": (lin or {}).get("status"),
        "status_inverse": (inv or {}).get("status"),
        "vivo_linear": lev_l,
        "vivo_inverse": lev_i,
        "vivo_avg": avg,
        "config_linear": cfg_l or None,
        "config_inverse": cfg_i or None,
        "dict_linear": dict_row.get("linear") or None,
        "dict_inverse": dict_row.get("inverse") or None,
        "dict_avg": dict_row.get("avg") or None,
        "diff_config_linear": (None if lev_l is None or not cfg_l else lev_l - cfg_l),
        "diff_config_inverse": (None if lev_i is None or not cfg_i else lev_i - cfg_i),
    }


def print_report(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    print()
    print(
        f"{'Act':<6} {'VivoL':>6} {'VivoI':>6} {'Avg':>6} "
        f"{'CfgL':>6} {'CfgI':>6} {'DictL':>6} {'DictI':>6}  nota"
    )
    print("-" * 78)
    diffs: list[dict[str, Any]] = []
    for r in sorted(rows, key=lambda x: (-(x.get("vivo_avg") or 0), x["activo"])):
        nota = []
        if r["vivo_linear"] is None and r["vivo_inverse"] is None:
            nota.append("SIN_CONTRATO")
        if r.get("diff_config_linear") not in (None, 0.0):
            nota.append(f"CfgL d{r['diff_config_linear']:+.0f}")
            diffs.append(r)
        if r.get("diff_config_inverse") not in (None, 0.0):
            nota.append(f"CfgI d{r['diff_config_inverse']:+.0f}")
            if r not in diffs:
                diffs.append(r)
        def fmt(v: Any) -> str:
            if v is None:
                return "—"
            return f"{float(v):.0f}"

        print(
            f"{r['activo']:<6} {fmt(r['vivo_linear']):>6} {fmt(r['vivo_inverse']):>6} {fmt(r['vivo_avg']):>6} "
            f"{fmt(r['config_linear']):>6} {fmt(r['config_inverse']):>6} "
            f"{fmt(r['dict_linear']):>6} {fmt(r['dict_inverse']):>6}  "
            f"{','.join(nota) or 'ok'}"
        )
    print()
    if diffs:
        print(f"  DISCREPANCIAS config vs Bybit vivo: {len(diffs)}")
        for r in diffs:
            print(
                f"    {r['activo']}: vivo L/I={r['vivo_linear']}/{r['vivo_inverse']}  "
                f"config L/I={r['config_linear']}/{r['config_inverse']}"
            )
    else:
        print("  Config alineada con Bybit vivo (para los que respondieron).")
    print()
    print("  Nota: maxLeverage = techo del contrato en instruments-info (tier 1).")
    print("  Posiciones grandes bajan el techo por risk limit dinámico.")
    return diffs


def apply_config_patch(rows: list[dict[str, Any]]) -> None:
    """Actualiza los dicts hardcodeados en core/config.py con valores vivos."""
    path = ROOT / "core" / "config.py"
    text = path.read_text(encoding="utf-8")
    lin: dict[str, float] = {}
    inv: dict[str, float] = {}
    for r in rows:
        a = r["activo"]
        if r["vivo_linear"]:
            lin[a] = float(r["vivo_linear"])
        if r["vivo_inverse"]:
            inv[a] = float(r["vivo_inverse"])
    if not lin and not inv:
        print("  --apply-config: nada que escribir.")
        return

    def _fmt_dict(d: dict[str, float]) -> str:
        # agrupar visualmente en líneas
        items = [f'"{k}": {int(v) if v == int(v) else v}' for k, v in sorted(d.items())]
        lines = []
        chunk: list[str] = []
        for it in items:
            chunk.append(it)
            if len(chunk) >= 5:
                lines.append("    " + ", ".join(chunk) + ",")
                chunk = []
        if chunk:
            lines.append("    " + ", ".join(chunk) + ",")
        return "{\n" + "\n".join(lines) + "\n}"

    lin_block = "MANTO_LEVERAGE_LINEAR_MAX_BY_ASSET: dict[str, float] = " + _fmt_dict(lin)
    inv_block = "MANTO_LEVERAGE_INVERSE_MAX_BY_ASSET: dict[str, float] = " + _fmt_dict(inv)

    text2, n1 = re.subn(
        r"MANTO_LEVERAGE_LINEAR_MAX_BY_ASSET: dict\[str, float\] = \{[\s\S]*?\n\}",
        lin_block,
        text,
        count=1,
    )
    text3, n2 = re.subn(
        r"MANTO_LEVERAGE_INVERSE_MAX_BY_ASSET: dict\[str, float\] = \{[\s\S]*?\n\}",
        inv_block,
        text2,
        count=1,
    )
    if n1 != 1 or n2 != 1:
        raise RuntimeError(f"No se pudo parchear config.py (n1={n1}, n2={n2})")
    path.write_text(text3, encoding="utf-8")
    print(f"  Parcheado {path} ({len(lin)} linear, {len(inv)} inverse).")


def main() -> int:
    ap = argparse.ArgumentParser(description="Verificar maxLeverage Bybit vs config")
    ap.add_argument("--json", type=Path, help="Guardar reporte JSON")
    ap.add_argument("--apply-config", action="store_true", help="Escribir vivos en config.py")
    ap.add_argument("--regen-dict", action="store_true", help="Regenerar diccionario_beru tras verificar")
    ap.add_argument("--only", nargs="*", help="Solo estos activos (ej. LTC SOL ETH)")
    args = ap.parse_args()

    print("=" * 72)
    print("  VERIFICACIÓN APALANCAMIENTOS BYBIT (instruments-info)")
    print(f"  {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC")
    print("=" * 72)

    try:
        probe_api()
    except Exception as e:
        print(f"\n  No se pudo contactar Bybit: {e}")
        print("  -> Pedi a Jess que corra este mismo script en Mexico.")
        return 2

    assets = args.only or assets_to_check()
    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    for a in assets:
        a = a.upper()
        try:
            rows.append(check_one(a))
            print(f"  ok {a}")
        except Exception as e:
            errors.append(f"{a}: {e}")
            print(f"  FAIL {a}: {e}")

    diffs = print_report(rows)

    # Foco Monarca: LTC / SOL
    print("  FOCO:")
    for a in ("LTC", "SOL", "BTC", "ETH", "XRP"):
        r = next((x for x in rows if x["activo"] == a), None)
        if not r:
            continue
        print(
            f"    {a}: Bybit L/I = {r['vivo_linear']}/{r['vivo_inverse']}  "
            f"| config = {r['config_linear']}/{r['config_inverse']}  "
            f"| dict JSON = {r['dict_linear']}/{r['dict_inverse']}"
        )
    print()

    payload = {
        "ts_utc": datetime.now(timezone.utc).isoformat(),
        "api": API,
        "rows": rows,
        "errors": errors,
        "n_diff_config": len(diffs),
    }
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"  Guardado {args.json}")

    if args.apply_config:
        apply_config_patch(rows)

    if args.regen_dict:
        from scripts.generar_diccionario_beru import main as regen

        print("\n  Regenerando diccionario_beru…")
        return int(regen() or 0)

    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
