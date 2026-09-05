#!/usr/bin/env python3
"""Purga triggers Oz huerfanos: ACECHANDO sin Oz / sin caza no deben tener trigger.

  python scripts/purgar_triggers_huerfanos_okx.py --dry-run
  python scripts/purgar_triggers_huerfanos_okx.py
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from core import okx_rest


def _activo(inst: str) -> str:
    return str(inst or "").replace("-USDT-SWAP", "").upper()


def _estado_local(act: str) -> dict:
    p = ROOT / "data" / "beru" / "rango" / act / "manos_piedra_informe.json"
    if not p.exists():
        return {}
    try:
        j = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return (j.get("snapshot") or {}).get("vivo") or {}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    rows = okx_rest.get_private(
        "/api/v5/trade/orders-algo-pending",
        params={"ordType": "trigger", "limit": "100"},
    ) or []
    print(f"[PURGA] triggers vivos={len(rows)}", flush=True)

    # Multi por inst
    by: dict[str, list] = {}
    for r in rows:
        inst = str(r.get("instId") or "")
        by.setdefault(inst, []).append(r)

    cancelar: list[dict] = []
    for inst, lst in sorted(by.items()):
        act = _activo(inst)
        vivo = _estado_local(act)
        estado = str(vivo.get("estado") or "").upper()
        oz = float(vivo.get("oz") or 0)
        link = str(vivo.get("altar_link_id") or "")
        # Huérfano: acecho / sin oz / sin sello · o duplicados
        if estado != "CAZANDO" or oz <= 0:
            for r in lst:
                cancelar.append({"inst": inst, "algoId": r.get("algoId"), "motivo": f"no_caza_{estado or 'sin_vivo'}"})
            continue
        if len(lst) > 1:
            # conservar el que matchee link si se puede
            keep = None
            for r in lst:
                cl = str(r.get("algoClOrdId") or r.get("clOrdId") or "")
                if link and link in cl:
                    keep = r
                    break
            if keep is None:
                keep = lst[-1]
            for r in lst:
                if r is keep:
                    continue
                cancelar.append({"inst": inst, "algoId": r.get("algoId"), "motivo": "dupe"})

    print(f"[PURGA] a_cancelar={len(cancelar)} dry={args.dry_run}", flush=True)
    ok_n = fail_n = 0
    for i, row in enumerate(cancelar):
        print(f"  {row['motivo']} {row['inst']} {row['algoId']}", flush=True)
        if args.dry_run:
            continue
        try:
            okx_rest.post_private(
                "/api/v5/trade/cancel-algos",
                [{"instId": row["inst"], "algoId": str(row["algoId"])}],
            )
            ok_n += 1
        except Exception as exc:
            fail_n += 1
            print(f"    FAIL {exc}", flush=True)
        if i and i % 10 == 0:
            time.sleep(0.3)
    if not args.dry_run:
        left = okx_rest.get_private(
            "/api/v5/trade/orders-algo-pending",
            params={"ordType": "trigger", "limit": "100"},
        ) or []
        print(f"[PURGA] done ok={ok_n} fail={fail_n} quedan={len(left)}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
