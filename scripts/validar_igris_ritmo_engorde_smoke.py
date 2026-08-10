#!/usr/bin/env python3
"""Smoke frío — ritmo 15s entre duales + candado fills L+S antes del siguiente Market."""
from __future__ import annotations

import sys
import time
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import core.config as config
from generales.igris import IgrisEscudo


def _igris_frio() -> IgrisEscudo:
    bel = SimpleNamespace(anotar=lambda *a, **k: None)
    return IgrisEscudo(
        tusk=SimpleNamespace(pesos={}),
        tank=SimpleNamespace(),
        bellion=bel,
    )


def main() -> int:
    print("[SMOKE] igris ritmo engorde + fills dual")
    ritmo = float(getattr(config, "IGRIS_ENGORDE_RITMO_S", 0))
    assert ritmo >= 3.0, f"piso engorde ≥3s; got {ritmo}"
    assert abs(ritmo - 15.0) < 1e-9, f"default debe ser 15.0; got {ritmo}"

    ig = _igris_frio()
    t0 = 1_700_000_000.0
    assert not ig._engorde_en_espera("ETH", t0)

    ig._override_activo = "ETH"
    ig._marcar_ritmo_engorde("ETH")
    until = float(ig._engorde_ritmo_until_por["ETH"])
    assert until > time.time()
    assert ig._engorde_en_espera("ETH", time.time())
    assert not ig._engorde_en_espera("BTC", time.time())

    ig._engorde_ritmo_until_por["ETH"] = time.time() - 0.1
    assert not ig._engorde_en_espera("ETH", time.time())

    # Candado fills: dual incompleto bloquea nuevo par
    ig._marcar_dual_fills("ETH", False)
    assert not ig._dual_previo_confirmado("ETH")
    assert ig._engorde_en_espera("ETH", time.time())
    ig._marcar_dual_fills("ETH", True)
    assert ig._dual_previo_confirmado("ETH")
    assert not ig._engorde_en_espera("ETH", time.time())

    ig._marcar_fail_cooldown("ETH")
    assert ig._engorde_en_espera("ETH", time.time())
    ig._engorde_fail_until_por["ETH"] = time.time() - 0.1
    assert not ig._engorde_en_espera("ETH", time.time())

    prev = config.IGRIS_ENGORDE_RITMO_S
    try:
        config.IGRIS_ENGORDE_RITMO_S = 0.0
        ig2 = _igris_frio()
        ig2._marcar_ritmo_engorde("SOL")
        assert "SOL" not in ig2._engorde_ritmo_until_por
    finally:
        config.IGRIS_ENGORDE_RITMO_S = prev

    print("[OK] igris ritmo engorde · default=15s · fills L+S · por Santo")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
