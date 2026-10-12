#!/usr/bin/env python3
"""Smoke — cirugías 2026-10-12: Red short sorda · memoria engorde · campos Iron."""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# Path used below for cleanup of test campo sello
sys.path.insert(0, str(ROOT))

import core.config as config
from cirugias.hiron import campo_masa as cm
from core import beru_rango as br
from core.models import BeruShip


def _perfil_piedra() -> None:
    os.environ["BERU_RANGO_SEMAFORO"] = "rojo"
    os.environ["BERU_RANGO_PIEDRA_SIN_TOPE"] = "1"
    os.environ.pop("BERU_RANGO_IRON_CAMPO_FACTOR", None)
    assert config.aplicar_perfil_beru_rango("piedra") == "piedra"


def test_campo_masa_tabla() -> None:
    assert cm.campo_de_ganancia(-0.05) == "guerra"
    assert cm.campo_de_ganancia(0.009) == "guerra"
    assert cm.campo_de_ganancia(0.01) == "sangre"
    assert cm.campo_de_ganancia(0.049) == "sangre"
    assert cm.campo_de_ganancia(0.05) == "masacre"
    assert cm.factor_de_ganancia(0.0) == 1.0
    assert cm.factor_de_ganancia(0.02) == 2.0
    assert cm.factor_de_ganancia(0.06) == 3.0
    g = cm.ganancia_fraccion(5.0, 5.0, 100.0)
    assert abs(g - 0.10) < 1e-9
    # Desengorde: misma plata sobre bolsa mitad → % sube (no se aleja el campo)
    g_llena = cm.ganancia_fraccion(2.0, 2.0, 200.0)  # 2 %
    g_mitad = cm.ganancia_fraccion(2.0, 2.0, 100.0)  # 4 %
    assert abs(g_llena - 0.02) < 1e-9
    assert abs(g_mitad - 0.04) < 1e-9
    assert cm.campo_de_ganancia(g_llena) == "sangre"
    assert cm.campo_de_ganancia(g_mitad) == "sangre"
    # Sobre posición 100: 3+2 = 5 % → masacre. Pierna hist 400 no manda.
    pub = cm.publicar(
        "TESTCAMPO", realizado=3.0, flotante=2.0, posicion_usd=100.0, pierna_hist_usd=400.0,
    )
    assert pub["campo"] == "masacre"
    assert abs(float(pub["posicion_usd"]) - 100.0) < 1e-9
    assert pub["factor"] == 3.0
    try:
        (Path(cm._DIR) / "TESTCAMPO.json").unlink(missing_ok=True)
    except Exception:
        pass
    print("  campo masa tabla OK")


def test_red_short_sorda() -> None:
    """Planta 0,8; masa como 0,7 (un peldaño menos)."""
    _perfil_piedra()
    assert br.peldaños_holgura_red_short() == 1

    b_l = BeruShip(uid="RANGO_AAA_CAZA", centro_local=100.0, masa=0.0, direccion="", estado="ACECHANDO")
    br.despertar(b_l, 100.0, activo="AAA")
    b_l.engorde_cero_oz_px = 100.0
    b_l.engorde_peldaño_offset = 0
    b_l.oz_despliegue_px = 100.0
    b_l.ultima_hoz_direccion = "LONG"
    b_l.es_relevo_cazador = True
    b_l.origen_tramo = "RED"
    b_l.red_adan = 100.0 * (1.0 - 0.007)
    m_long = br.armar_tramo_desde_red(b_l, precio=b_l.red_adan)

    b_s = BeruShip(uid="RANGO_BBB_CAZA", centro_local=100.0, masa=0.0, direccion="", estado="ACECHANDO")
    br.despertar(b_s, 100.0, activo="BBB")
    b_s.engorde_cero_oz_px = 100.0
    b_s.engorde_peldaño_offset = 0
    b_s.oz_despliegue_px = 100.0
    b_s.ultima_hoz_direccion = "SHORT"
    b_s.es_relevo_cazador = True
    b_s.origen_tramo = "RED"
    b_s.red_adan = 100.0 * (1.0 + 0.008)
    m_short = br.armar_tramo_desde_red(b_s, precio=b_s.red_adan)

    assert abs(m_long - m_short) < 1e-9, f"long={m_long} short={m_short}"
    assert m_long > 0.3
    # Oreja short sigue a 0,8
    b2 = BeruShip(uid="RANGO_CCC_CAZA", centro_local=100.0, masa=0.0, direccion="", estado="ACECHANDO")
    br.despertar(b2, 100.0, activo="CCC")
    br.toca_vacio(b2, 100.0)
    br.armar_tramo_desde_vacio(b2, "ARRIBA", precio=101.2)
    br.actualizar_trailing_oz(b2, 101.2)
    oz2 = float(b2.oz_adan)
    br.cosechar_oz_y_mover_cero(b2, oz2 * 0.999, oz_despliegue=oz2)
    assert abs(b2.red_adan - oz2 * 1.008) < 1e-9
    print("  Red short sorda OK")


def test_memoria_engorde() -> None:
    """Dos Oz del mismo lado: el cero no se recetea; offset recuerda."""
    _perfil_piedra()
    b = BeruShip(uid="RANGO_DDD_CAZA", centro_local=100.0, masa=0.0, direccion="", estado="ACECHANDO")
    br.despertar(b, 100.0, activo="DDD")
    br.toca_vacio(b, 100.0)
    br.armar_tramo_desde_vacio(b, "ABAJO", precio=98.8)
    br.actualizar_trailing_oz(b, 98.8 * (1.0 - 0.008))
    oz1 = float(b.oz_adan)
    br.cosechar_oz_y_mover_cero(b, oz1, oz_despliegue=oz1)
    cero1 = float(b.engorde_cero_oz_px)
    assert abs(cero1 - oz1) < 1e-9
    assert str(b.engorde_campana_dir).upper() == "LONG"

    # Simula Red más lejos y segunda Oz del mismo lado
    b.origen_tramo = "RED"
    b.direccion = "LONG"
    b.ultima_hoz_direccion = "LONG"
    b.estado = "CAZANDO"
    b.engorde_bloqueado = False
    b.engorde_ancla_px = cero1
    px_red = cero1 * (1.0 - 0.007)
    br.armar_tramo_desde_red(b, precio=px_red)
    br.actualizar_trailing_oz(b, px_red * (1.0 - 0.005))
    oz2 = float(b.oz_adan)
    assert oz2 > 0
    br.cosechar_oz_y_mover_cero(b, oz2, oz_despliegue=oz2)
    assert abs(float(b.engorde_cero_oz_px) - cero1) < 1e-9, "cero de campaña debe quedarse"
    assert int(b.engorde_memoria_peldaños) >= int(b.engorde_peldaño_offset) >= 1

    assert int(b.engorde_memoria_peldaños) >= 1
    # Sangre limpia memoria de la racha
    b.sangre_lado = "ARRIBA"
    b.sangre_adan = cero1 * 1.012
    br.armar_tramo_desde_sangre(b, precio=b.sangre_adan)
    assert int(getattr(b, "engorde_memoria_peldaños", 0) or 0) == 0
    print("  memoria engorde OK")


def test_restaurar_conserva_memoria() -> None:
    """Al reenganchar acecho, la memoria del sello no se borra."""
    _perfil_piedra()
    b = BeruShip(uid="RANGO_HHH_CAZA", centro_local=100.0, masa=0.0, direccion="", estado="ACECHANDO")
    br.despertar(b, 100.0, activo="HHH")
    br.restaurar_acecho_post_oz(
        b,
        cero=100.0,
        red=99.2,
        sangre_lado="ARRIBA",
        ultima_hoz_direccion="LONG",
        oz_despliegue=100.0,
        engorde_cero_oz=100.0,
        engorde_peldaño_offset=12,
        engorde_memoria_peldaños=12,
        engorde_campana_dir="LONG",
    )
    assert abs(float(b.engorde_cero_oz_px) - 100.0) < 1e-9
    assert int(b.engorde_memoria_peldaños) == 12
    assert int(b.engorde_peldaño_offset) == 12
    assert str(b.engorde_campana_dir).upper() == "LONG"
    print("  restaurar conserva memoria OK")


def test_factor_iron() -> None:
    os.environ["BERU_RANGO_SEMAFORO"] = "rojo"
    os.environ.pop("BERU_RANGO_PIEDRA_SIN_TOPE", None)
    os.environ.pop("BERU_RANGO_IRON_CAMPO_FACTOR", None)
    assert config.aplicar_perfil_beru_rango("piedra") == "piedra"

    b = BeruShip(uid="RANGO_EEE_CAZA", centro_local=100.0, masa=0.0, direccion="", estado="ACECHANDO")
    br.despertar(b, 100.0, activo="EEE")
    br.toca_vacio(b, 100.0)
    m1 = br.armar_tramo_desde_vacio(b, "ABAJO", precio=98.8)
    assert abs(m1 - 0.40) < 1e-9, m1

    b2 = BeruShip(uid="RANGO_FFF_CAZA", centro_local=100.0, masa=0.0, direccion="", estado="ACECHANDO")
    br.despertar(b2, 100.0, activo="FFF")
    b2.iron_campo_factor = 2.0
    br.toca_vacio(b2, 100.0)
    m2 = br.armar_tramo_desde_vacio(b2, "ABAJO", precio=98.8)
    assert abs(m2 - 0.80) < 1e-9, m2
    assert abs(br.engorde_paso_usd(b2) - 0.04) < 1e-9
    assert abs(br.engorde_tope_usd(b2) - 4.0) < 1e-9  # tope guerra 2 × 2

    b3 = BeruShip(uid="RANGO_GGG_CAZA", centro_local=100.0, masa=0.0, direccion="", estado="ACECHANDO")
    br.despertar(b3, 100.0, activo="GGG")
    b3.iron_campo_factor = 3.0
    br.toca_vacio(b3, 100.0)
    m3 = br.armar_tramo_desde_vacio(b3, "ABAJO", precio=98.8)
    assert abs(m3 - 1.20) < 1e-9, m3
    assert abs(br.engorde_paso_usd(b3) - 0.06) < 1e-9
    print("  factor Iron ×1/×2/×3 OK")


def main() -> int:
    print("[SMOKE] cirugia engorde + Iron campos + Red short sorda")
    prev = str(getattr(config, "BERU_RANGO_PERFIL", "normal") or "normal")
    try:
        test_campo_masa_tabla()
        test_red_short_sorda()
        test_memoria_engorde()
        test_restaurar_conserva_memoria()
        test_factor_iron()
        print("[SMOKE] OK")
        return 0
    finally:
        config.aplicar_perfil_beru_rango(prev)
        os.environ.pop("BERU_RANGO_PIEDRA_SIN_TOPE", None)
        os.environ.pop("BERU_RANGO_IRON_CAMPO_FACTOR", None)


if __name__ == "__main__":
    raise SystemExit(main())
