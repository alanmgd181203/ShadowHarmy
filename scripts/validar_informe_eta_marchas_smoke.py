#!/usr/bin/env python3
"""Smoke — informe ETA 2 marchas operativas + map legado (semillas locales)."""
from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core import manto_frecuencia as mf
from core import pase_director as pd
from core.kaiser_samples import SAMPLES_DIR, append_sample


def main() -> int:
    base = "SMKETA3"
    ahora = time.time()
    for edge in (mf.EDGE_MANTO, "perp_vs_index", "inverse_vs_index"):
        p = SAMPLES_DIR / f"{base}_{edge}.jsonl"
        if p.exists():
            p.unlink()
    for i in range(80):
        ts = ahora - i * 3600
        gap = 0.25 if i % 4 == 0 else 0.10
        append_sample(base, "perp_vs_index", signed_pct=0.05, ts=ts)
        append_sample(base, "inverse_vs_index", signed_pct=-0.05, ts=ts)
        append_sample(base, mf.EDGE_MANTO, signed_pct=gap, abs_pct=abs(gap), ts=ts)

    assert pd.normalizar_marcha("tactico") == "asalto"
    assert pd.normalizar_marcha("marcha_forzada") == "asalto"

    eta_leg = mf.eta_despliegue_horas(base, 100.0, marcha_id="marcha_forzada", mordida_usd=5.0)
    eta_a = mf.eta_despliegue_horas(base, 100.0, marcha_id="asalto", mordida_usd=5.0)
    assert eta_a.get("ok"), eta_a
    assert eta_leg.get("marcha_id") == "asalto"
    assert eta_a.get("marcha_id") == "asalto"
    print(
        "PASS eta 2 marchas",
        "legado->asalto", eta_leg.get("eta_h"),
        "asalto", eta_a.get("eta_h"),
    )
    for edge in (mf.EDGE_MANTO, "perp_vs_index", "inverse_vs_index"):
        p = SAMPLES_DIR / f"{base}_{edge}.jsonl"
        if p.exists():
            p.unlink()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
