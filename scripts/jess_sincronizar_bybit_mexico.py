#!/usr/bin/env python3
"""Ritual Jess (Mexico) — sincronizar Bybit vivo y dejar evidencia en git.

Pasos:
  1) Comprueba acceso a api.bybit.com
  2) Vuelca instrumentos Tank (linear+inverse) + spot USDT/USDC (Beru)
  3) Construye data/bybit_parametros_mercado.json (lev max + minimos + piso_manto)
  4) Verifica apalancamientos vs config y aplica vivos
  5) Regenera diccionario_beru_flota_manto.json
  6) Risk-limit muestra + fees (si hay keys)

Salida principal:
  data/bybit_parametros_mercado.json   ← base para Igris/Beru/Kaiser
  data/jess_bybit_sync/RESUMEN.md
  data/jess_bybit_sync/*.json(l)

Uso:
  python scripts/jess_sincronizar_bybit_mexico.py
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT_DIR = ROOT / "data" / "jess_bybit_sync"
API = "https://api.bybit.com"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"no load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _get_json(path: str, *, timeout: float = 60) -> dict[str, Any]:
    url = f"{API}{path}"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "ShadowHarmy-JessSync/1.0", "Accept": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())


def probe() -> None:
    try:
        _get_json("/v5/market/instruments-info?category=linear&symbol=BTCUSDT", timeout=30)
    except urllib.error.HTTPError as e:
        if e.code == 403:
            print("=" * 72)
            print("  BLOQUEO HTTP 403 — esta red no llega a Bybit.")
            print("  Este ritual es para Mexico (Jess). Abortando.")
            print("=" * 72)
        raise


def dump_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def sample_risk_limits(symbols: list[str], category: str = "linear") -> dict[str, Any]:
    out: dict[str, Any] = {"category": category, "symbols": {}}
    for sym in symbols:
        try:
            data = _get_json(f"/v5/market/risk-limit?category={category}&symbol={sym}")
            lst = (data.get("result") or {}).get("list") or []
            tiers = []
            max_lev = None
            for t in lst:
                try:
                    ml = float(t.get("maxLeverage") or 0)
                except (TypeError, ValueError):
                    ml = 0.0
                if max_lev is None or ml > max_lev:
                    max_lev = ml
            for t in lst[:8]:
                tiers.append(
                    {
                        "id": t.get("id"),
                        "riskLimitValue": t.get("riskLimitValue"),
                        "maxLeverage": t.get("maxLeverage"),
                        "maintenanceMargin": t.get("maintenanceMargin"),
                        "initialMargin": t.get("initialMargin"),
                    }
                )
            out["symbols"][sym] = {
                "maxLeverage_tier1_hint": max_lev,
                "tiers_sample": tiers,
                "n_tiers": len(lst),
            }
        except Exception as e:
            out["symbols"][sym] = {"error": str(e)}
    return out


def try_fees(symbols: list[str]) -> dict[str, Any]:
    report: dict[str, Any] = {
        "nota": (
            "Maker/taker por simbolo: GET /v5/account/fee-rate (autenticado). "
            "Sin API keys solo queda deliveryFeeRate en instrumentos."
        ),
        "account_fee_rate": None,
        "tried_auth": False,
    }
    key = os.getenv("BYBIT_API_KEY") or os.getenv("API_KEY")
    secret = os.getenv("BYBIT_API_SECRET") or os.getenv("API_SECRET")
    if not key or not secret:
        try:
            from dotenv import load_dotenv

            load_dotenv(ROOT / ".env")
            key = os.getenv("BYBIT_API_KEY") or os.getenv("API_KEY")
            secret = os.getenv("BYBIT_API_SECRET") or os.getenv("API_SECRET")
        except Exception:
            pass
    if not key or not secret:
        report["skipped"] = "sin API keys en entorno"
        return report
    report["tried_auth"] = True
    try:
        from pybit.unified_trading import HTTP

        session = HTTP(testnet=False, api_key=key, api_secret=secret)
        fees = []
        for sym in symbols[:40]:
            try:
                r = session.get_fee_rate(category="linear", symbol=sym)
                fees.append({"symbol": sym, "result": r.get("result")})
            except Exception as e:
                fees.append({"symbol": sym, "error": str(e)})
        report["account_fee_rate"] = fees
    except Exception as e:
        report["error"] = str(e)
    return report


def write_resumen(
    path: Path,
    *,
    ts: str,
    n_lin: int,
    n_inv: int,
    n_spot_u: int,
    n_spot_c: int,
    n_bases: int,
    lev_focus: dict[str, Any],
    min_focus: dict[str, Any],
    dict_n: int,
    fees_note: str,
) -> None:
    lines = [
        f"# Jess Bybit sync — {ts}",
        "",
        "## Hecho",
        f"- Linear Trading: **{n_lin}** · Inverse: **{n_inv}**",
        f"- Spot USDT: **{n_spot_u}** · Spot USDC: **{n_spot_c}**",
        f"- Bases en `bybit_parametros_mercado.json`: **{n_bases}**",
        f"- Diccionario flota Beru: **{dict_n}** activos",
        f"- Config `MANTO_LEVERAGE_*` alineado al vivo (salvo --skip-apply-config)",
        "",
        "## Foco apalancamiento",
        "",
        "| Activo | Linear | Inverse |",
        "|--------|-------:|--------:|",
    ]
    for a, row in lev_focus.items():
        lines.append(f"| {a} | {row.get('linear')} | {row.get('inverse')} |")
    lines += [
        "",
        "## Foco minimos (USD est.)",
        "",
        "| Activo | Lin min | Inv min | **Piso manto** | Spot USDT |",
        "|--------|--------:|--------:|---------------:|----------:|",
    ]
    for a, row in min_focus.items():
        lines.append(
            f"| {a} | {row.get('lin')} | {row.get('inv')} | **{row.get('piso')}** | {row.get('spot')} |"
        )
    lines += [
        "",
        "## Fees",
        fees_note,
        "",
        "## Archivos",
        "- `data/bybit_parametros_mercado.json` — BD lev + minimos + piso_manto + spot",
        "- `data/jess_bybit_sync/apalancamientos_vivo.json`",
        "- `instrumentos_linear.jsonl` / `inverse` / `spot_usdt` / `spot_usdc`",
        "- `risk_limits_muestra.json` · `fees.json`",
        "- `config/diccionario_beru_flota_manto.json` · `core/config.py`",
        "",
        "## Siguiente",
        "1. Revisar este RESUMEN (LTC/SOL/BTC + pisos manto)",
        "2. Commit + push (ver migracion/JESS_SINCRONIZAR_BYBIT.md)",
        "3. Monarca: `git pull`",
        "",
        "Refresh futuro: `python scripts/kaiser_actualizar_parametros_bybit.py`",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-apply-config", action="store_true")
    ap.add_argument("--skip-dict", action="store_true")
    ap.add_argument("--no-prices", action="store_true", help="No tickers (min_usd parcial)")
    args = ap.parse_args()

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    print("=" * 72)
    print("  JESS — SINCRONIZAR BYBIT (Mexico)")
    print(f"  {ts}")
    print("=" * 72)

    try:
        probe()
    except Exception as e:
        print(f"Abort: {e}")
        return 2

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    bpm = _load("bybit_parametros_mercado", ROOT / "scripts" / "bybit_parametros_mercado.py")

    # 1) Instrumentos completos
    print("\n[1/6] Instrumentos linear + inverse + spot…")
    linear = bpm.page_instruments("linear", quote_coin="USDT")
    inverse = bpm.page_instruments("inverse")
    spot_usdt = bpm.page_instruments("spot", quote_coin="USDT")
    spot_usdc = bpm.page_instruments("spot", quote_coin="USDC")
    slim_l = [bpm.slim_instrument(x) for x in linear]
    slim_i = [bpm.slim_instrument(x) for x in inverse]
    slim_su = [bpm.slim_instrument(x) for x in spot_usdt]
    slim_sc = [bpm.slim_instrument(x) for x in spot_usdc]
    dump_jsonl(OUT_DIR / "instrumentos_linear.jsonl", slim_l)
    dump_jsonl(OUT_DIR / "instrumentos_inverse.jsonl", slim_i)
    dump_jsonl(OUT_DIR / "instrumentos_spot_usdt.jsonl", slim_su)
    dump_jsonl(OUT_DIR / "instrumentos_spot_usdc.jsonl", slim_sc)
    print(
        f"  linear={len(slim_l)} inverse={len(slim_i)} "
        f"spotUSDT={len(slim_su)} spotUSDC={len(slim_sc)}"
    )

    # 2) BD parametros (lev + minimos + piso manto)
    print("\n[2/6] Base bybit_parametros_mercado.json (con precios)…")
    db = bpm.construir_base_parametros(
        linear=linear,
        inverse=inverse,
        spot_usdt=spot_usdt,
        spot_usdc=spot_usdc,
        fetch_prices=not args.no_prices,
    )
    db_path = bpm.guardar_base(db)
    # Copia en carpeta Jess para el commit visible
    (OUT_DIR / "bybit_parametros_mercado.json").write_text(
        json.dumps(db, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"  OK → {db_path}  bases={db['meta']['n_bases']}")

    min_focus = {}
    for a in ("BTC", "ETH", "LTC", "SOL", "XRP", "ADA"):
        row = (db.get("activos") or {}).get(a) or {}
        min_focus[a] = {
            "lin": (row.get("linear") or {}).get("min_usd_est"),
            "inv": (row.get("inverse") or {}).get("min_usd_est"),
            "piso": row.get("piso_manto_usd"),
            "spot": (row.get("spot_usdt") or {}).get("min_usd_est"),
        }

    # 3) Risk limits
    print("\n[3/6] Risk-limit muestra…")
    sample_syms = [
        "BTCUSDT", "ETHUSDT", "LTCUSDT", "SOLUSDT", "XRPUSDT", "ADAUSDT",
        "DOGEUSDT", "LINKUSDT", "BNBUSDT", "SUIUSDT",
    ]
    risk = sample_risk_limits(sample_syms, "linear")
    (OUT_DIR / "risk_limits_muestra.json").write_text(
        json.dumps(risk, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    # 4) Apalancamientos vs config
    print("\n[4/6] Verificar apalancamientos vs config…")
    ver = _load("verificar_apalancamientos_bybit", ROOT / "scripts" / "verificar_apalancamientos_bybit.py")
    rows = []
    for a in ver.assets_to_check():
        try:
            rows.append(ver.check_one(a))
            print(f"  ok {a}")
        except Exception as e:
            print(f"  FAIL {a}: {e}")
    (OUT_DIR / "apalancamientos_vivo.json").write_text(
        json.dumps({"ts_utc": ts, "rows": rows}, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    if not args.skip_apply_config:
        ver.apply_config_patch(rows)
    else:
        print("  (skip apply-config)")

    lev_focus = {}
    for a in ("BTC", "ETH", "LTC", "SOL", "XRP", "ADA"):
        r = next((x for x in rows if x["activo"] == a), None)
        if r:
            lev_focus[a] = {"linear": r.get("vivo_linear"), "inverse": r.get("vivo_inverse")}

    # 5) Diccionario Beru
    dict_n = 0
    if not args.skip_dict:
        print("\n[5/6] Regenerar diccionario_beru…")
        gen = _load("generar_diccionario_beru", ROOT / "scripts" / "generar_diccionario_beru.py")
        code = int(gen.main() or 0)
        if code != 0:
            print(f"  WARN regenerar dict exit={code}")
        try:
            meta = json.loads((ROOT / "config" / "diccionario_beru_flota_manto.json").read_text(encoding="utf-8"))
            dict_n = int((meta.get("meta") or {}).get("n_flota") or 0)
        except Exception:
            dict_n = 0
    else:
        print("\n[5/6] skip dict")

    # 6) Fees
    print("\n[6/6] Fees…")
    fees = try_fees(sample_syms)
    (OUT_DIR / "fees.json").write_text(json.dumps(fees, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    fees_note = fees.get("nota", "")
    if fees.get("account_fee_rate"):
        fees_note += "\n- Se obtuvo fee-rate autenticado (muestra)."
    elif fees.get("skipped"):
        fees_note += f"\n- Omitido: {fees['skipped']}"

    write_resumen(
        OUT_DIR / "RESUMEN.md",
        ts=ts,
        n_lin=len(slim_l),
        n_inv=len(slim_i),
        n_spot_u=len(slim_su),
        n_spot_c=len(slim_sc),
        n_bases=int(db["meta"]["n_bases"]),
        lev_focus=lev_focus,
        min_focus=min_focus,
        dict_n=dict_n,
        fees_note=fees_note,
    )

    print("\n" + "=" * 72)
    print(f"  OK → {OUT_DIR}")
    print(f"  BD → {db_path}")
    print("  Siguiente: commit + push (ver migracion/JESS_SINCRONIZAR_BYBIT.md)")
    print("=" * 72)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
