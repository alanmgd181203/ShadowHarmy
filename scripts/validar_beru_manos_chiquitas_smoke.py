"""Smoke frío — Beru manos chiquitas (nivel 3)."""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import core.config as config
from core import beru_ensayo
from core import beru_wake
from generales.beru import BeruCazador


def test_flags_nivel3_default_off():
    assert config.BERU_ENSAYO_NIVEL3 is False
    assert beru_ensayo.activo() is False


def test_activos_default_mnt():
    prev = getattr(config, "BERU_ENSAYO_ACTIVOS", None)
    try:
        config.BERU_ENSAYO_ACTIVOS = "MNT"
        assert beru_ensayo.activos_ensayo() == ["MNT"]
    finally:
        if prev is not None:
            config.BERU_ENSAYO_ACTIVOS = prev


def test_siembra_nivel3_sin_candado_pase():
    prev_n = bool(getattr(config, "BERU_ENSAYO_NIVEL3", False))
    prev_flota = list(getattr(config, "ACTIVOS_BERU_FLOTA", None) or [])
    try:
        config.BERU_ENSAYO_NIVEL3 = True
        config.ACTIVOS_BERU_FLOTA = ["MNT"]
        ok = beru_wake.activos_siembra_permitidos(2000.0, pasos_logrados=[])
        assert ok == ["MNT"]
        assert beru_wake.siembra_sin_candado_pase() is True

        from core.bellion import BellionAuditor
        from generales.tusk import TuskBoveda
        from generales.capitanes import CapitanNormal

        bel = BellionAuditor()
        tusk = TuskBoveda(bel)
        tusk.masa_bruta_real = 2200.0
        tusk.pesos = {
            "MNTUSD_INVERSE": {
                "long": 1, "short": 0,
                "precio_medio_long": 0.45, "precio_medio_short": 0,
            }
        }
        tank = MagicMock()
        tank.capitan_activo = CapitanNormal
        tank.nodos = []
        tank._obtener_lider_verde = MagicMock(return_value=None)
        beru = BeruCazador(tusk, bel, tank, bridge=MagicMock())
        n = beru.despertar_flota_reset_0({"MNT": 0.45})
        assert n == 1
        assert len(beru.legion) == 1
        assert beru._activo_de_barco(beru.legion[0]) == "MNT"
    finally:
        config.BERU_ENSAYO_NIVEL3 = prev_n
        config.ACTIVOS_BERU_FLOTA = prev_flota


def test_techo_cazas_no_apaga_manos():
    prev_n = bool(getattr(config, "BERU_ENSAYO_NIVEL3", False))
    prev_max = getattr(config, "BERU_ENSAYO_MAX_ORDENES", 1)
    prev_manos = bool(getattr(config, "BERU_MANOS", False))
    try:
        config.BERU_ENSAYO_NIVEL3 = True
        config.BERU_ENSAYO_MAX_ORDENES = 1
        config.BERU_MANOS = True
        beru_ensayo.reset_contadores()
        beru_ensayo.anotar_orden_ok(symbol="MNTUSDT", lado="LONG")
        assert beru_ensayo.techo_alcanzado() is True
        assert config.BERU_MANOS is True  # cosecha sigue posible
        beru_ensayo.anotar_cosecha_ok(symbol="MNTUSDT")
        assert beru_ensayo.ordenes_ok() == 1
    finally:
        config.BERU_ENSAYO_NIVEL3 = prev_n
        config.BERU_ENSAYO_MAX_ORDENES = prev_max
        config.BERU_MANOS = prev_manos
        beru_ensayo.reset_contadores()


def test_registrar_consola_y_log():
    beru_ensayo.registrar("SMOKE_N3", detalle="ok", qty=5.0)
    assert beru_ensayo.LOG_PATH.exists()
    text = beru_ensayo.LOG_PATH.read_text(encoding="utf-8")
    assert "SMOKE_N3" in text


def test_ritual_script_candados():
    src = (ROOT / "scripts" / "arise_beru_manos_chiquitas.py").read_text(encoding="utf-8")
    assert 'MODO_SIMULACION"] = "false"' in src or "MODO_SIMULACION\"] = \"false\"" in src
    assert 'BERU_MANOS"] = "true"' in src
    assert 'BERU_MANOS_FANTASMA"] = "false"' in src
    assert "BERU_ENSAYO_NIVEL3" in src
    assert "estrechar_ojos_bridge" in src
    assert "_muleta_ojos_rest" in src


def test_wake_conoce_nivel3():
    prev = bool(getattr(config, "BERU_ENSAYO_NIVEL3", False))
    try:
        config.BERU_ENSAYO_NIVEL3 = True
        assert beru_wake.ensayo_nivel3_activo() is True
        r = beru_wake.resumen_cableado()
        assert r.get("ensayo_nivel3") is True
    finally:
        config.BERU_ENSAYO_NIVEL3 = prev


if __name__ == "__main__":
    test_flags_nivel3_default_off()
    test_activos_default_mnt()
    test_siembra_nivel3_sin_candado_pase()
    test_techo_cazas_no_apaga_manos()
    test_registrar_consola_y_log()
    test_ritual_script_candados()
    test_wake_conoce_nivel3()
    print("OK beru manos chiquitas smoke")
