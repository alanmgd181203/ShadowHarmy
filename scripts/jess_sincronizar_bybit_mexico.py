#!/usr/bin/env python3
"""Ritual Jess (Mexico) — sincronizar Bybit vivo y dejar evidencia en git.

Pasos (este script hace casi todo solo):
  1) Comprueba acceso a api.bybit.com
  2) Verifica apalancamientos (flota Beru + contraste config)
  3) Regenera diccionario_beru_flota_manto.json
  4) Aplica maxLeverage vivos a core/config.py
  5) Vuelca instrumentos Tank (linear+inverse Trading) + risk-limit muestra
  6) Intenta fees (publico limitado; con API keys si hay .env)

Salida:
  data/jess_bybit_sync/
    RESUMEN.md
    apalancamientos_vivo.json
    instrumentos_linear.jsonl
    instrumentos_inverse.jsonl
    risk_limits_muestra.json
    fees.json  (si aplica)

Uso:
  python scripts/jess_sincronizar_bybit_mexico.py
  python scripts/jess_sincronizar_bybit_mexico.py --skip-apply-config
"""
from __future__ import annotations

import argparse
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


def _get_json(path: str, *, timeout: float = 60) -> dict[str, Any]:
    url = f"{API}{path}"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "ShadowHarmy-JessSync/1.0", "Accept": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())


def _page_instruments(category: str, *, quote_coin: str | None = None) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    cursor = ""
    while True:
        q = f"/v5/market/instruments-info?category={category}&limit=1000"
        if cursor:
            q += f"&cursor={cursor}"
        payload = _get_json(q)
        if int(payload.get("retCode") or -1) != 0:
            raise RuntimeError(f"instruments {category}: {payload.get('retMsg')}")
        result = payload.get("result") or {}
        for x in result.get("list") or []:
            if x.get("status") != "Trading":
                continue
            if quote_coin and x.get("quoteCoin") != quote_coin:
                continue
            out.append(x)
        cursor = result.get("nextPageCursor") or ""
        if not cursor:
            break
    return out


def _slim_instrument(x: dict[str, Any]) -> dict[str, Any]:
    lf = x.get("leverageFilter") or {}
    lot = x.get("lotSizeFilter") or {}
    price = x.get("priceFilter") or {}
    return {
        "symbol": x.get("symbol"),
        "baseCoin": x.get("baseCoin"),
        "quoteCoin": x.get("quoteCoin"),
        "contractType": x.get("contractType"),
        "status": x.get("status"),
        "maxLeverage": lf.get("maxLeverage"),
        "minLeverage": lf.get("minLeverage"),
        "leverageStep": lf.get("leverageStep"),
        "minOrderQty": lot.get("minOrderQty"),
        "qtyStep": lot.get("qtyStep"),
        "maxOrderQty": lot.get("maxOrderQty"),
        "minNotionalValue": lot.get("minNotionalValue"),
        "tickSize": price.get("tickSize"),
        "deliveryFeeRate": x.get("deliveryFeeRate"),
        "fundingInterval": x.get("fundingInterval"),
        "unifiedMarginTrade": x.get("unifiedMarginTrade"),
    }


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
            # tier mas permisivo suele ser el de menor riskLimitValue / mayor maxLeverage
            tiers = []
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
            max_lev = None
            for t in lst:
                try:
                    ml = float(t.get("maxLeverage") or 0)
                except (TypeError, ValueError):
                    ml = 0.0
                if max_lev is None or ml > max_lev:
                    max_lev = ml
            out["symbols"][sym] = {"maxLeverage_tier1_hint": max_lev, "tiers_sample": tiers, "n_tiers": len(lst)}
        except Exception as e:
            out["symbols"][sym] = {"error": str(e)}
    return out


def try_fees(symbols: list[str]) -> dict[str, Any]:
    """Fees de cuenta requieren firma. Sin keys: solo nota + deliveryFeeRate ya en instrumentos."""
    report: dict[str, Any] = {
        "nota": (
            "Maker/taker por simbolo suele ir en GET /v5/account/fee-rate (autenticado). "
            "Sin API keys solo dejamos deliveryFeeRate en instrumentos y esta nota."
        ),
        "account_fee_rate": None,
        "tried_auth": False,
    }
    key = os.getenv("BYBIT_API_KEY") or os.getenv("API_KEY")
    secret = os.getenv("BYBIT_API_SECRET") or os.getenv("API_SECRET")
    if not key or not secret:
        # intentar .env via config si existe
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
        # Usar cliente del ejercito si existe
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
    lev_focus: dict[str, Any],
    dict_n: int,
    fees_note: str,
) -> None:
    lines = [
        f"# Jess Bybit sync — {ts}",
        "",
        "## Hecho",
        f"- Instrumentos linear Trading: **{n_lin}**",
        f"- Instrumentos inverse Trading: **{n_inv}**",
        f"- Diccionario flota Beru regenerado: **{dict_n}** activos",
        f"- Config apalancamientos: actualizado desde vivo (salvo --skip-apply-config)",
        "",
        "## Foco apalancamiento (instruments-info)",
        "",
        "| Activo | Linear | Inverse |",
        "|--------|-------:|--------:|",
    ]
    for a, row in lev_focus.items():
        lines.append(f"| {a} | {row.get('linear')} | {row.get('inverse')} |")
    lines += [
        "",
        "## Fees",
        fees_note,
        "",
        "## Archivos",
        "- `apalancamientos_vivo.json`",
        "- `instrumentos_linear.jsonl` / `instrumentos_inverse.jsonl`",
        "- `risk_limits_muestra.json`",
        "- `fees.json`",
        "- `config/diccionario_beru_flota_manto.json` (repo)",
        "- `core/config.py` (MANTO_LEVERAGE_* si apply)",
        "",
        "## Siguiente (Jess / Cursor)",
        "1. Revisar RESUMEN y foco LTC/SOL/BTC/ETH/XRP",
        "2. `git add` de data/jess_bybit_sync/ + diccionario + config.py",
        "3. `git commit` + `git push` a origin",
        "4. Avisar al Monarca para `git pull`",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-apply-config", action="store_true")
    ap.add_argument("--skip-dict", action="store_true")
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

    # 1) Snapshot Tank / sentidos: todos los perps Trading
    print("\n[1/5] Instrumentos linear + inverse…")
    linear = _page_instruments("linear", quote_coin="USDT")
    inverse = _page_instruments("inverse")
    slim_l = [_slim_instrument(x) for x in linear]
    slim_i = [_slim_instrument(x) for x in inverse]
    dump_jsonl(OUT_DIR / "instrumentos_linear.jsonl", slim_l)
    dump_jsonl(OUT_DIR / "instrumentos_inverse.jsonl", slim_i)
    print(f"  linear={len(slim_l)}  inverse={len(slim_i)}")

    # 2) Risk limits muestra (vanguardia + extras)
    print("\n[2/5] Risk-limit muestra…")
    sample_syms = [
        "BTCUSDT", "ETHUSDT", "LTCUSDT", "SOLUSDT", "XRPUSDT", "ADAUSDT",
        "DOGEUSDT", "LINKUSDT", "BNBUSDT", "SUIUSDT",
    ]
    risk = sample_risk_limits(sample_syms, "linear")
    (OUT_DIR / "risk_limits_muestra.json").write_text(
        json.dumps(risk, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    # 3) Verificar apalancamientos (reusa script)
    print("\n[3/5] Verificar apalancamientos vs config…")
    import importlib.util

    def _load(name: str, path: Path):
        spec = importlib.util.spec_from_file_location(name, path)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"no load {path}")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    ver = _load("verificar_apalancamientos_bybit", ROOT / "scripts" / "verificar_apalancamientos_bybit.py")

    rows = []
    for a in ver.assets_to_check():
        try:
            rows.append(ver.check_one(a))
            print(f"  ok {a}")
        except Exception as e:
            print(f"  FAIL {a}: {e}")
    lev_path = OUT_DIR / "apalancamientos_vivo.json"
    lev_path.write_text(
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

    # 4) Regenerar diccionario Beru
    dict_n = 0
    if not args.skip_dict:
        print("\n[4/5] Regenerar diccionario_beru…")
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
        print("\n[4/5] skip dict")

    # 5) Fees
    print("\n[5/5] Fees…")
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
        lev_focus=lev_focus,
        dict_n=dict_n,
        fees_note=fees_note,
    )

    print("\n" + "=" * 72)
    print(f"  OK → {OUT_DIR}")
    print("  Siguiente: commit + push de data/jess_bybit_sync/ + diccionario + config")
    print("=" * 72)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
