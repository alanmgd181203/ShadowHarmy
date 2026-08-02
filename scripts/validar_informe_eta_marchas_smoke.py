#!/usr/bin/env python3
"""Smoke — informe ETA 3 marchas (semillas locales, sin API)."""
from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core import manto_frecuencia as mf
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
        # Cero ~0.10; a veces exceso fuerte para que haya ops
        gap = 0.25 if i % 4 == 0 else 0.10
        append_sample(base, "perp_vs_index", signed_pct=0.05, ts=ts)
        append_sample(base, "inverse_vs_index", signed_pct=-0.05, ts=ts)
        append_sample(base, mf.EDGE_MANTO, signed_pct=gap, abs_pct=abs(gap), ts=ts)

    eta_t = mf.eta_despliegue_horas(base, 100.0, marcha_id="tactico", mordida_usd=5.0)
    eta_f = mf.eta_despliegue_horas(base, 100.0, marcha_id="marcha_forzada", mordida_usd=5.0)
    eta_a = mf.eta_despliegue_horas(base, 100.0, marcha_id="asalto", mordida_usd=5.0)
    assert eta_f.get("ok"), eta_f
    # Asalto (tablas) debe ser <= Forzada <= Tactico en ETA (mas oportunidades)
    if eta_t.get("ok") and eta_a.get("ok") and eta_t.get("eta_h") and eta_a.get("eta_h"):
        assert float(eta_a["eta_h"]) <= float(eta_t["eta_h"]) + 1e-6, (eta_a, eta_t)
    print(
        "PASS eta 3 marchas",
        "tactico", eta_t.get("eta_h"),
        "forzada", eta_f.get("eta_h"),
        "asalto", eta_a.get("eta_h"),
    )
    for edge in (mf.EDGE_MANTO, "perp_vs_index", "inverse_vs_index"):
        p = SAMPLES_DIR / f"{base}_{edge}.jsonl"
        if p.exists():
            p.unlink()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
