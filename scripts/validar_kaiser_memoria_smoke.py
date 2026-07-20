#!/usr/bin/env python3
"""Smoke memoria barcos Kaiser — Tank fake → append diario."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import core.config as config
from core import kaiser_memoria_barcos as mem


class _TankFake:
    tsunami_activado = False
    capitan_activo = type("CapitanCazador", (), {"__name__": "CapitanCazador"})()
    desvios_indice = []
    matriz_spreads = []

    def _obtener_lider_verde(self):
        return type("N", (), {"estado_foco": "VERDE", "latencia_ms": 50.0})()

    def snapshot_matriz_spreads(self):
        return {
            "filas": [
                {"base": "ETH", "tipo": "lineal_vs_inverse", "spread_pct": 0.12},
                {"base": "DOGE", "tipo": "spot_vs_perp", "spread_pct": 0.55},
            ],
            "ts_calc": 1.0,
        }

    def snapshot_desvios_indice(self):
        return {
            "filas": [
                {"base": "ETH", "desvio_pct": 0.2, "desvio_signed_pct": 0.2, "huerfana": False},
                {"base": "DOGE", "desvio_pct": 0.9, "desvio_signed_pct": 0.9, "huerfana": False},
            ],
            "ts_calc": 1.0,
        }

    def snapshot_funding(self):
        return {"top": [{"base": "ETH", "funding_pct": 0.01}]}

    def snapshot_panorama_global(self):
        return {"filas": [], "refs_binance": 0, "bases_huerfanas": 0}

    def snapshot_sentidos_extra(self):
        return {"errores": {}}


def main():
    with tempfile.TemporaryDirectory() as tmp:
        with mock.patch.object(mem, "MEMORIA_DIR", Path(tmp)):
            with mock.patch.object(config, "KAISER_MEMORIA_INTERVAL_S", 0.0):
                n1, ts1, al1, r1 = mem.append_memoria_si_toca(_TankFake(), 0.0)
                assert n1 >= 2, n1
                assert r1.get("escrito") is True
                eth = mem.leer_ultimas("ETH", 5)
                assert len(eth) == 1
                assert eth[0]["base"] == "ETH"
                assert "spread_pct" in eth[0]

                # segunda hora con salto grande → aviso
                tank2 = _TankFake()
                tank2.snapshot_matriz_spreads = lambda: {
                    "filas": [
                        {"base": "ETH", "tipo": "lineal_vs_inverse", "spread_pct": 0.90},
                        {"base": "DOGE", "tipo": "spot_vs_perp", "spread_pct": 0.55},
                    ],
                    "ts_calc": 2.0,
                }
                n2, ts2, al2, r2 = mem.append_memoria_si_toca(tank2, 0.0)
                assert n2 >= 2
                assert any(a.get("tipo") in ("GRIAL_PULSO", "CANDIDATO_PULSO") for a in al2), al2
                assert len(mem.leer_ultimas("ETH", 5)) == 2

    # smoke digest Kaiser sigue OK
    from core import kaiser_indicators as ki
    d = ki.interpretar_tank(_TankFake())
    assert "indicadores" in d
    print("OK kaiser memoria barcos + digest")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
