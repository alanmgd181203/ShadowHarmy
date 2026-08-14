"""Smoke — ley Beru: neutro margen · sin engorde · aborto solo ceguera."""
from __future__ import annotations

import sys
import time
from pathlib import Path
from unittest.mock import MagicMock

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import core.config as config
from core import beru_ley


def test_defaults_ley():
    assert config.BERU_NEUTRO_MARGEN is True
    assert config.BERU_ENGORDE_PERMITIDO is True  # engorde Hoz en caza
    assert config.BERU_ABORTAR_SOLO_CEGUERA is True
    assert config.BERU_MANOS is False
    assert config.BERU_HILO_ENABLED is False
    assert config.BERU_SPOT_MARGEN_ENABLED is True
    assert abs(config.BERU_ABISMO_SALIDA_PCT - 0.016) < 1e-9
    assert abs(config.BERU_LLAMADO_SANGRE_PCT - 0.009) < 1e-9
    assert beru_ley.consumir_auth_en_reserva() is False
    assert beru_ley.nunca_descansa() is True
    assert beru_ley.spot_margen_activo() is True
    assert beru_ley.llamados_solo_detonan() is True
    assert beru_ley.engorde_escudo_prohibido() is True


def test_rojo_no_aborta_si_hay_precio():
    aborta, motivo = beru_ley.debe_abortar_por_vision(
        "ROJO", {"ETHUSDT_SPOT": {}}, precio_casa=3000.0, tank=None,
    )
    assert aborta is False
    assert motivo == "ok"


def test_sin_precio_aborta():
    aborta, motivo = beru_ley.debe_abortar_por_vision(
        "VERDE", {"x": 1}, precio_casa=0.0, tank=None,
    )
    assert aborta is True
    assert motivo == "sin_precio_casa"


def test_coma_aborta():
    n = MagicMock()
    n.ultima_actualizacion = time.time() - 60
    n.estado_foco = "CONGELADO"
    tank = MagicMock()
    tank.nodos = [n, n, n, n]
    aborta, motivo = beru_ley.debe_abortar_por_vision(
        "ROJO", {"x": 1}, precio_casa=100.0, tank=tank,
    )
    assert aborta is True
    assert motivo == "tank_coma"


def test_engorde_caza_on():
    assert beru_ley.engorde_permitido() is True


def main() -> int:
    test_defaults_ley()
    test_rojo_no_aborta_si_hay_precio()
    test_sin_precio_aborta()
    test_coma_aborta()
    test_engorde_caza_on()
    print("validar_beru_ley_neutro_smoke: OK (molino · engorde caza · manos OFF)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
