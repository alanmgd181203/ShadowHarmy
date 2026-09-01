#!/usr/bin/env python3
"""Smoke — piedra: peldaños sumados · semáforo · pierna · sangre desde Oz · Red continua."""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import core.config as config
from core import beru_rango as br
from core import beru_rango_semaforo as sem
from core.models import BeruShip


def _assert_serie_numeros() -> None:
    assert abs(br.masa_peldaños_sumados_usd(10) - 2.45) < 1e-9
    assert abs(br.masa_peldaños_sumados_usd(11) - 2.75) < 1e-9
    assert abs(br.masa_peldaños_sumados_usd(12) - 3.06) < 1e-9
    assert abs(br.masa_peldaños_sumados_usd(15, offset=10) - 1.60) < 1e-9
    print("  serie 2.45 / 2.75 / 3.06 / 1.60 OK")


def _assert_semaforo_pierna() -> None:
    assert sem.semaforo_normalizado("verde") == "verde"
    assert sem.semaforo_normalizado("ancho") == "verde"
    assert sem.semaforo_normalizado("cenido") == "rojo"
    assert sem.masa_nacimiento_por_bando("amarillo", "paz") == 0.30
    assert sem.masa_nacimiento_por_bando("amarillo", "medio") == 0.25
    assert sem.masa_nacimiento_por_bando("verde", "paz") == 0.50
    assert sem.masa_nacimiento_por_bando("verde", "pesado") == 0.20
    assert sem.tope_serie_por_color("rojo") == 0.50
    assert sem.tope_serie_por_color("verde") == 1.00

    b = BeruShip(uid="RANGO_ETH_CAZA", centro_local=100.0, masa=0.0, direccion="", estado="ACECHANDO")
    br.despertar(b, 100.0, activo="ETH")
    assert sem.actualizar_bando_pierna(b, 50.0, 100.0) == "paz"
    assert sem.actualizar_bando_pierna(b, 100.0, 100.0) == "medio"
    assert abs(float(b.pierna_umbral_involucion) - 100.0) < 1e-9
    assert sem.actualizar_bando_pierna(b, 80.0, 99.0) == "paz"
    b.pierna_bando = "medio"
    assert sem.actualizar_bando_pierna(b, 301.0, 101.0) == "pesado"
    assert sem.actualizar_bando_pierna(b, 240.0, 100.5) == "medio"
    b.saco_long_usd = 150.0
    assert sem.pierna_usd(b) == 150.0
    b.estado = "CAZANDO"
    b.direccion = "LONG"
    b.masa = 2.0
    assert sem.pierna_usd(b) == 152.0
    print("  semaforo + pierna bandos OK")


def main() -> int:
    print("[SMOKE] beru rango perfil piedra peldaños sumados")
    prev = str(getattr(config, "BERU_RANGO_PERFIL", "normal") or "normal")
    prev_tier = os.environ.get("BERU_RANGO_PIEDRA_TIER")
    prev_sem = os.environ.get("BERU_RANGO_SEMAFORO")
    prev_sin_tope = os.environ.get("BERU_RANGO_PIEDRA_SIN_TOPE")
    prev_asig = os.environ.get("BERU_RANGO_PIEDRA_ASIGNACION_PATH")
    try:
        os.environ["BERU_RANGO_PIEDRA_TIER"] = "medio"
        os.environ["BERU_RANGO_SEMAFORO"] = "rojo"
        os.environ["BERU_RANGO_PIEDRA_SIN_TOPE"] = "1"
        assert config.aplicar_perfil_beru_rango("piedra") == "piedra"
        g = br.resumen_geometria()
        assert g["perfil"] == "piedra"
        assert g["engorde_modo"] == "peldaños_sumados"
        assert g["saco_techo"] == "peldaños_sumados"
        assert g.get("semaforo_default") == "rojo"
        _assert_serie_numeros()
        _assert_semaforo_pierna()

        # Vacío rojo: nace $0.20; ~1 % -> $2.45 en la Oz
        b = BeruShip(uid="RANGO_OP_CAZA", centro_local=100.0, masa=0.0, direccion="", estado="ACECHANDO")
        br.despertar(b, 100.0, activo="OP")
        br.toca_vacio(b, 100.0)
        m = br.armar_tramo_desde_vacio(b, "ABAJO", precio=98.8)
        assert abs(m - 0.20) < 1e-9, f"rojo nace $0.20, got {m}"
        br.actualizar_trailing_oz(b, 98.8 * (1.0 - 0.010))
        assert abs(float(b.masa) - 2.45) < 1e-9, f"1pct engorde sumado -> 2.45, got {b.masa}"
        print("  vacio 1pct -> Oz 2.45 OK")

        # Amarillo default: nace $0.30
        os.environ["BERU_RANGO_SEMAFORO"] = "amarillo"
        b7 = BeruShip(uid="RANGO_SOL_CAZA", centro_local=100.0, masa=0.0, direccion="", estado="ACECHANDO")
        br.despertar(b7, 100.0, activo="SOL")
        br.toca_vacio(b7, 100.0)
        m7 = br.armar_tramo_desde_vacio(b7, "ABAJO", precio=98.8)
        assert abs(m7 - 0.30) < 1e-9, f"amarillo nace $0.30, got {m7}"
        print("  amarillo nace 0.30 OK")

        # Tope rojo congela engorde en $0.50
        os.environ.pop("BERU_RANGO_PIEDRA_SIN_TOPE", None)
        os.environ["BERU_RANGO_SEMAFORO"] = "rojo"
        b8 = BeruShip(uid="RANGO_DOT_CAZA", centro_local=100.0, masa=0.0, direccion="", estado="ACECHANDO")
        br.despertar(b8, 100.0, activo="DOT")
        br.toca_vacio(b8, 100.0)
        br.armar_tramo_desde_vacio(b8, "ABAJO", precio=98.8)
        br.actualizar_trailing_oz(b8, 98.8 * (1.0 - 0.010))
        assert abs(float(b8.masa) - 0.50) < 1e-9, f"rojo tope 0.50, got {b8.masa}"
        print("  rojo tope 0.50 OK")
        os.environ["BERU_RANGO_PIEDRA_SIN_TOPE"] = "1"

        # Oz cosecha -> sangre +/-1.2 % desde Oz; al armar sangre ya trae ~2.45+ (12 peldaños)
        os.environ["BERU_RANGO_SEMAFORO"] = "rojo"
        oz = float(b.oz_adan)
        br.cosechar_oz_y_mover_cero(b, oz, oz_despliegue=oz)
        assert float(b.engorde_cero_oz_px) > 0
        sangre_px = float(b.sangre_adan)
        assert sangre_px > 0
        n_sangre = br.peldaños_entre(float(b.engorde_cero_oz_px), sangre_px)
        assert n_sangre >= 11, n_sangre
        m_s = br.armar_tramo_desde_sangre(b, precio=sangre_px)
        assert m_s >= 2.45 - 1e-9, f"sangre desde Oz >=2.45, got {m_s}"
        print("  sangre desde ultima Oz OK")

        # Red SHORT 0,8 %
        b2 = BeruShip(uid="P2", centro_local=100.0, masa=0.0, direccion="", estado="ACECHANDO")
        br.despertar(b2, 100.0, activo="ETH")
        br.toca_vacio(b2, 100.0)
        br.armar_tramo_desde_vacio(b2, "ARRIBA", precio=101.2)
        br.actualizar_trailing_oz(b2, 101.2)
        oz2 = float(b2.oz_adan)
        br.cosechar_oz_y_mover_cero(b2, oz2 * 0.999, oz_despliegue=oz2)
        assert abs(b2.red_adan - oz2 * 1.008) < 1e-9
        print("  Red SHORT 0,8 % OK")

        # Beru 2: offset 10 -> red en peldaño 15 ~ $1.60
        b3 = BeruShip(uid="R3", centro_local=100.0, masa=0.0, direccion="", estado="ACECHANDO")
        br.despertar(b3, 100.0, activo="ETH")
        b3.engorde_cero_oz_px = 100.0
        b3.engorde_peldaño_offset = 10
        b3.oz_despliegue_px = 100.0
        b3.ultima_hoz_direccion = "SHORT"
        b3.es_relevo_cazador = True
        b3.red_adan = 101.5
        b3.oreja_red_activa = True
        px_red = 101.5
        m_red = br.armar_tramo_desde_red(b3, precio=px_red)
        assert abs(m_red - 1.60) < 1e-9, f"Red delta f(15)-f(10)=1.60, got {m_red}"
        br.actualizar_trailing_oz(b3, px_red * 1.001)
        assert abs(float(b3.masa) - 1.95) < 1e-9, f"+0.1pct -> ~1.95, got {b3.masa}"
        print("  Red Beru2 1.60 -> 1.95 OK")

        # Floor + deuda (WLD paso fino vs doctrina 2.45)
        from core import lote_beru as lb
        b5 = BeruShip(uid="R5", centro_local=100.0, masa=2.45, direccion="LONG", estado="CAZANDO")
        b5.masa_pendiente_usd = 0.0
        px_wld = 0.365
        frente = "WLDUSDT_LINEAL"
        pack1 = lb.masa_a_qty_con_deuda(2.45, px_wld, frente, usar_floor=True)
        assert pack1.get("ok"), pack1
        not1 = float(pack1["notional_usd"])
        deuda1 = float(pack1["deuda_usd"])
        assert deuda1 > 0.01, deuda1
        assert abs(2.45 - not1 - deuda1) < 0.02
        pack2b = lb.masa_a_qty_con_deuda(2.75 + deuda1, px_wld, frente, usar_floor=True)
        assert pack2b.get("ok")
        assert float(pack2b["notional_usd"]) >= not1 + 0.01
        assert float(pack2b["deuda_usd"]) < deuda1 + 0.01
        br.limpiar_masa_pendiente(b5)
        assert float(b5.masa_pendiente_usd) == 0.0
        print("  floor deuda WLD OK")

        # Sangre inverso borra deuda
        b6 = BeruShip(uid="R6", centro_local=100.0, masa=0.0, direccion="", estado="ACECHANDO")
        br.despertar(b6, 100.0, activo="ETH")
        b6.masa_pendiente_usd = 0.45
        b6.engorde_cero_oz_px = 100.0
        b6.oz_despliegue_px = 100.0
        b6.sangre_lado = "ABAJO"
        b6.sangre_adan = 98.8
        br.armar_tramo_desde_sangre(b6, precio=98.8)
        assert float(b6.masa_pendiente_usd) == 0.0
        print("  sangre inverso borra deuda OK")

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as tf:
            json.dump({"activos": {"WLD": {"semaforo": "verde"}}}, tf)
            tmp_path = tf.name
        os.environ["BERU_RANGO_PIEDRA_ASIGNACION_PATH"] = tmp_path
        os.environ.pop("BERU_RANGO_PIEDRA_SIN_TOPE", None)
        br.invalidar_piedra_asignacion()
        assert sem.semaforo_resuelto("WLD") == "verde"
        assert br.engorde_tope_usd(activo="WLD") == 1.00
        os.unlink(tmp_path)
    finally:
        if prev_tier is None:
            os.environ.pop("BERU_RANGO_PIEDRA_TIER", None)
        else:
            os.environ["BERU_RANGO_PIEDRA_TIER"] = prev_tier
        if prev_sem is None:
            os.environ.pop("BERU_RANGO_SEMAFORO", None)
        else:
            os.environ["BERU_RANGO_SEMAFORO"] = prev_sem
        if prev_sin_tope is None:
            os.environ.pop("BERU_RANGO_PIEDRA_SIN_TOPE", None)
        else:
            os.environ["BERU_RANGO_PIEDRA_SIN_TOPE"] = prev_sin_tope
        if prev_asig is None:
            os.environ.pop("BERU_RANGO_PIEDRA_ASIGNACION_PATH", None)
        else:
            os.environ["BERU_RANGO_PIEDRA_ASIGNACION_PATH"] = prev_asig
        br.invalidar_piedra_asignacion()
        valid = tuple(getattr(config, "BERU_RANGO_PERFILES", {}) or {})
        config.aplicar_perfil_beru_rango(prev if prev in valid else "normal")
        print("  restaurado perfil", config.BERU_RANGO_PERFIL)

    print("OK validar_beru_rango_piedra_smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
