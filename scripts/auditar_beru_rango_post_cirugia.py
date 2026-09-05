#!/usr/bin/env python3
"""Auditoria post-cirugia: cobertura, Oz, markets vs cosechas, piernas gordas."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core import beru_flota_vigilante as vf
from core import okx_rest


def main() -> int:
    esp = vf.flota_esperada()
    reg = vf._leer_pids_registro()
    vivos = [a for a in esp if a in reg and vf._pid_vivo(int(reg[a]))]
    print(f"cobertura {len(vivos)}/{len(esp)}", flush=True)

    tr = (
        okx_rest.get_private(
            "/api/v5/trade/orders-algo-pending",
            params={"ordType": "trigger", "limit": "100"},
        )
        or []
    )
    print(f"triggers_okx {len(tr)}", flush=True)

    pos = okx_rest.get_private("/api/v5/account/positions", params={"instType": "SWAP"}) or []
    pos = [p for p in pos if abs(float(p.get("pos") or 0)) > 0]
    print(f"piernas_okx {len(pos)}", flush=True)

    corte = datetime.now(timezone.utc) - timedelta(minutes=90)
    corte_s = corte.strftime("%Y-%m-%dT%H:%M")
    mkt = cose = reparar = 0
    mkt_by: dict[str, int] = {}
    estados: dict[str, int] = {}
    saco_vs: list[tuple] = []
    base = ROOT / "data" / "beru" / "rango"

    for act in esp:
        ev = base / act / "eventos.jsonl"
        if ev.exists():
            try:
                lines = ev.read_text(encoding="utf-8", errors="replace").splitlines()[-400:]
            except Exception as exc:
                print(f"ev_fail {act} {exc}", flush=True)
                lines = []
            for line in lines:
                if not line.strip():
                    continue
                try:
                    j = json.loads(line)
                except Exception:
                    continue
                ts = str(j.get("ts") or j.get("ts_utc") or "")
                if ts and ts < corte_s:
                    continue
                blob = json.dumps(j, ensure_ascii=False).upper()
                if (
                    "BRGMKT" in blob
                    or "DISPARAR_ENTRADA_MARKET" in blob
                    or "MARKET_ENVIADO" in blob
                    or "ENTRADA_MARKET" in blob
                ):
                    mkt += 1
                    mkt_by[act] = mkt_by.get(act, 0) + 1
                if "COSECH" in blob or "HARVEST" in blob:
                    cose += 1
                if "REPARAR_SELLO" in blob:
                    reparar += 1

        inf = base / act / "manos_piedra_informe.json"
        if not inf.exists():
            continue
        try:
            j = json.loads(inf.read_text(encoding="utf-8"))
            vivo = (j.get("snapshot") or {}).get("vivo") or {}
            est = str(vivo.get("estado") or "?")
            estados[est] = estados.get(est, 0) + 1
            if est == "CAZANDO":
                saco_vs.append(
                    (
                        act,
                        float(vivo.get("saco_long") or 0),
                        float(vivo.get("saco_short") or 0),
                        float(
                            vivo.get("pierna_long_usd")
                            or vivo.get("masa_long_usd")
                            or 0
                        ),
                        float(
                            vivo.get("pierna_short_usd")
                            or vivo.get("masa_short_usd")
                            or 0
                        ),
                        float(vivo.get("oz") or 0),
                    )
                )
        except Exception:
            pass

    print(
        f"eventos_90m markets~{mkt} cosechas~{cose} reparar_sello~{reparar}",
        flush=True,
    )
    top_m = sorted(mkt_by.items(), key=lambda x: -x[1])[:8]
    print(f"top_market {top_m}", flush=True)
    print(f"estados {dict(sorted(estados.items()))}", flush=True)
    print(f"cazando {len(saco_vs)}", flush=True)
    for row in saco_vs[:12]:
        print(f"caza {row}", flush=True)

    pos_map: dict[str, dict[str, float]] = {}
    for p in pos:
        inst = p.get("instId") or ""
        act = inst.replace("-USDT-SWAP", "").upper()
        side = "long" if float(p.get("pos") or 0) > 0 else "short"
        try:
            notional = abs(float(p.get("notionalUsd") or 0))
            if notional <= 0:
                notional = abs(
                    float(p.get("pos") or 0)
                    * float(p.get("markPx") or 0)
                    * float(p.get("ctVal") or 1)
                )
        except Exception:
            notional = 0.0
        pos_map.setdefault(act, {"long": 0.0, "short": 0.0})
        pos_map[act][side] = notional

    for act, sl, ss, pl, ps, oz in saco_vs:
        ok = pos_map.get(act, {"long": 0.0, "short": 0.0})
        if max(ok["long"], ok["short"], pl, ps) >= 80:
            print(
                f"gorda {act} okx_L={ok['long']:.1f} okx_S={ok['short']:.1f} "
                f"brain_L={pl:.1f} brain_S={ps:.1f} saco_L={sl:.1f} saco_S={ss:.1f} oz={oz}",
                flush=True,
            )

    # ratio sanity: spam if markets >> harvests on same activo
    spammy = [(a, n, ) for a, n in mkt_by.items() if n >= 8]
    print(f"spam_suspects>={8} {spammy[:15]}", flush=True)
    print("AUDIT_DONE", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
