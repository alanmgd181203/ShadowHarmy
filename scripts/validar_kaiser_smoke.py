#!/usr/bin/env python3
"""Smoke test Kaiser — interpreta Tank sin WS (datos sintéticos)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core import kaiser_indicators as ki


class _TankFake:
    tsunami_activado = False
    capitan_activo = type("CapitanCazador", (), {"__name__": "CapitanCazador"})()
    ref_binance = {}

    def _obtener_lider_verde(self):
        n = type("N", (), {"estado_foco": "VERDE", "latencia_ms": 120.0})()
        return n

    def snapshot_matriz_spreads(self):
        return {
            "filas": [{"base": "FOO", "tipo": "spot_vs_perp", "spread_pct": 0.42}],
            "ts_calc": 1.0,
        }

    def snapshot_desvios_indice(self):
        return {
            "filas": [{"base": "BAR", "desvio_pct": 0.8, "desvio_signed_pct": 0.8, "huerfana": True}],
            "umbral_alerta_pct": 0.5,
            "ts_calc": 1.0,
        }

    def snapshot_panorama_global(self):
        return {
            "filas": [{"base": "BAR", "estado": "DESALINEADO", "desvio_global_pct": 0.6}],
            "refs_binance": 0,
            "bases_huerfanas": 1,
        }

    def snapshot_funding(self):
        return {"top": [{"base": "BTC", "funding_rate": 0.001, "funding_pct": 0.1}]}

    def snapshot_sentidos_extra(self):
        return {"errores": {}}


def main():
    d = ki.interpretar_tank(_TankFake())
    assert d["indicadores"]["alertas_criticas"] >= 1
    assert d["cola_prioridad"]
    assert any(a["tipo"] == "DESVIO_INDICE" for a in d["alertas"])
    print("OK kaiser smoke:", d["resumen"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
