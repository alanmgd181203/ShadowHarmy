"""Smoke — ojos Beru = last spot · 0 vivo del manto (cirugía precisión 2026-08-13)."""
from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core import beru_cazador
from core import beru_ojos


def test_solo_last_spot():
    precios = {
        "ETHUSDT_SPOT": 3000.0,
        "ETHUSDT_LINEAL": 3010.0,
        "ETHUSD_INVERSE": 2990.0,
    }
    assert abs(beru_ojos.last_spot_desde_precios(precios, "ETH") - 3000.0) < 1e-9
    # Sin spot → ciego (no usa lineal/inverso)
    ciego = {"ETHUSDT_LINEAL": 3010.0, "ETHUSD_INVERSE": 2990.0}
    assert beru_ojos.last_spot_desde_precios(ciego, "ETH") == 0.0


def test_tank_solo_spot():
    class Lider:
        def precios_con_reflejo(self):
            return {
                "ADAUSDT_SPOT": 0.55,
                "ADAUSDT_LINEAL": 0.56,
            }

    class Tank:
        nodos = [Lider()]

        def _obtener_lider_verde(self):
            return self.nodos[0]

    assert abs(beru_ojos.last_spot_desde_tank(Tank(), "ADA") - 0.55) < 1e-9
    # Solo lineal en tank → ciego
    class LiderLin:
        def precios_con_reflejo(self):
            return {"ADAUSDT_LINEAL": 0.56}

    class TankLin:
        nodos = [LiderLin()]

        def _obtener_lider_verde(self):
            return self.nodos[0]

    assert beru_ojos.last_spot_desde_tank(TankLin(), "ADA") == 0.0


def test_inyectar_rest_no_lineal():
    src = (ROOT / "core" / "beru_ojos.py").read_text(encoding="utf-8")
    assert "USDT_LINEAL" not in src or "NO inyectar lineal" in src
    assert "lastPrice" in src
    assert "category=\"spot\"" in src or "category='spot'" in src


def test_cero_manto_desde_tusk():
    tusk = SimpleNamespace(
        pesos={
            "ETHUSD_INVERSE": {
                "long": 1.0,
                "short": 0.0,
                "precio_medio_long": 100.0,
                "precio_medio_short": 0.0,
            },
            "ETHUSDT_LINEAL": {
                "long": 0.0,
                "short": 1.0,
                "precio_medio_long": 0.0,
                "precio_medio_short": 110.0,
            },
        }
    )
    c = beru_cazador.centro_manto_desde_tusk(tusk, "ETH")
    assert abs(c - 105.0) < 1e-9
    # Sin medias → 0 (no inventa con spot)
    tusk2 = SimpleNamespace(pesos={"ETHUSDT_LINEAL": {"long": 0, "short": 0}})
    assert beru_cazador.centro_manto_desde_tusk(tusk2, "ETH") == 0.0


def test_aplicar_nuevo_cero_resync():
    beru = SimpleNamespace(
        centro_manto=100.0,
        centro_local=100.0,
        oz_pct=0.008,
        red_pct=0.009,
        oz_adan=100.8,
        red_adan=100.9,
        neg_oz_pct=0.0,
        modo_combate="CAZA",
    )
    assert beru_cazador.aplicar_nuevo_cero(beru, 200.0) is True
    assert abs(beru.centro_manto - 200.0) < 1e-9
    assert abs(beru.oz_adan - 201.6) < 1e-6  # 200 * 1.008
    assert abs(beru.red_adan - 201.8) < 1e-6  # 200 * 1.009
    # Sin cambio significativo → False
    assert beru_cazador.aplicar_nuevo_cero(beru, 200.0) is False


def main() -> int:
    test_solo_last_spot()
    test_tank_solo_spot()
    test_inyectar_rest_no_lineal()
    test_cero_manto_desde_tusk()
    test_aplicar_nuevo_cero_resync()
    print("validar_beru_ojos_smoke: OK (last spot · 0 manto · resync)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
