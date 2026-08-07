#!/usr/bin/env python3
"""Smoke frío — ritmo entre duales OK de engorde Igris (Asalto / piso general)."""
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
        tusk=SimpleNamespace(),
        tank=SimpleNamespace(),
        bellion=bel,
    )


def main() -> int:
    print("[SMOKE] igris ritmo engorde")
    ritmo = float(getattr(config, "IGRIS_ENGORDE_RITMO_S", 0))
    assert ritmo >= 3.0, f"piso Asalto ~3–5s; got {ritmo}"
    assert abs(ritmo - 5.0) < 1e-9, f"default debe ser 5.0; got {ritmo}"

    ig = _igris_frio()
    t0 = 1_700_000_000.0
    # Sin marca: libre
    assert not ig._engorde_en_espera("ETH", t0)

    # Dual OK → aire
    ig._override_activo = "ETH"
    # Marcar con reloj real; luego forzamos until relativo
    ig._marcar_ritmo_engorde("ETH")
    until = float(ig._engorde_ritmo_until_por["ETH"])
    assert until > time.time()
    assert ig._engorde_en_espera("ETH", time.time())
    # Otro Santo del lote no queda amarrado
    assert not ig._engorde_en_espera("BTC", time.time())

    # Tras cumplir ritmo: libre
    ig._engorde_ritmo_until_por["ETH"] = time.time() - 0.1
    assert not ig._engorde_en_espera("ETH", time.time())

    # Fail cooldown sigue bloqueando (mismo espíritu ~5s)
    ig._marcar_fail_cooldown("ETH")
    assert ig._engorde_en_espera("ETH", time.time())
    ig._engorde_fail_until_por["ETH"] = time.time() - 0.1
    assert not ig._engorde_en_espera("ETH", time.time())

    # Ritmo 0 desactiva marca (Personalizado / laboratorio)
    prev = config.IGRIS_ENGORDE_RITMO_S
    try:
        config.IGRIS_ENGORDE_RITMO_S = 0.0
        ig2 = _igris_frio()
        ig2._marcar_ritmo_engorde("SOL")
        assert "SOL" not in ig2._engorde_ritmo_until_por
    finally:
        config.IGRIS_ENGORDE_RITMO_S = prev

    print("[OK] igris ritmo engorde · default=5s · por Santo · fail+ritmo")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
