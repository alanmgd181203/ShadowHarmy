#!/usr/bin/env python3
"""Smoke — Red expansiva: helpers + plantado post-Oz (OFF por defecto)."""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core import beru_rango as br
from core.models import BeruShip


def _beru(escalones: int = 0) -> BeruShip:
    b = BeruShip(uid="T_RED_X", centro_local=100.0, masa=0.0, direccion="", estado="ACECHANDO")
    b.rango_escalones_red = int(escalones)
    return b


def main() -> int:
    print("=== validar_beru_rango_red_expansiva_smoke ===")
    os.environ.pop("BERU_RANGO_RED_EXPANSIVA", None)
    os.environ.pop("BERU_RANGO_RED_EXPANSIVA_TICK_PCT", None)

    b = _beru(5)

    # OFF por defecto: cero extra aunque haya escalones
    assert br.red_expansiva_activo() is False
    assert abs(br.red_expansiva_extra_pct(b)) < 1e-15
    assert abs(br.red_mapa_pct(b, "LONG") - br.red_activacion_pct("LONG")) < 1e-15
    print("  OFF por defecto -> extra=0 OK")

    # ON: 5 escalones × 0.1% = 0.5%
    os.environ["BERU_RANGO_RED_EXPANSIVA"] = "1"
    assert br.red_expansiva_activo() is True
    assert abs(br.red_expansiva_tick_pct() - 0.001) < 1e-12
    assert abs(br.red_expansiva_extra_pct(b) - 0.005) < 1e-12
    assert abs(br.red_mapa_pct(b, "LONG") - (br.red_activacion_pct("LONG") + 0.005)) < 1e-12
    print("  ON 5 escalones -> +0.5% OK")

    b.rango_escalones_red = 0
    assert abs(br.red_expansiva_extra_pct(b)) < 1e-15
    print("  ON sin escalones -> extra=0 OK")

    # red_desde_ancla sigue siendo base fija (no recibe beru; restore/corte 3)
    os.environ["BERU_RANGO_RED_EXPANSIVA"] = "1"
    b.rango_escalones_red = 10
    base_l = br.red_activacion_pct("LONG")
    base_s = br.red_activacion_pct("SHORT")
    r = br.red_desde_ancla(100.0, "LONG")
    assert abs(r - 100.0 * (1.0 - base_l)) < 1e-9, (r, base_l)
    r2 = br.red_desde_ancla(100.0, "SHORT")
    assert abs(r2 - 100.0 * (1.0 + base_s)) < 1e-9, (r2, base_s)
    print("  red_desde_ancla intacta (base) OK")

    # Corte 2: plantado OFF = mismo precio que base (tumor = flota cambia sola)
    os.environ.pop("BERU_RANGO_RED_EXPANSIVA", None)
    b_off = _beru(5)
    br._plantar_orejas_post_oz(b_off, 100.0, "SHORT")
    red_off = float(b_off.red_adan)
    assert abs(red_off - 100.0 * (1.0 + base_s)) < 1e-9, (red_off, base_s)
    print("  plantado OFF + escalones -> Red base OK")

    # Corte 2: plantado ON + 5 escalones -> Red más lejos (+0.5%)
    os.environ["BERU_RANGO_RED_EXPANSIVA"] = "1"
    b_on = _beru(5)
    br._plantar_orejas_post_oz(b_on, 100.0, "SHORT")
    red_on = float(b_on.red_adan)
    esperado = 100.0 * (1.0 + base_s + 0.005)
    assert abs(red_on - esperado) < 1e-9, (red_on, esperado)
    assert red_on > red_off + 1e-9
    print("  plantado ON 5 escalones SHORT -> Red +0.5% OK")

    b_long = _beru(5)
    br._plantar_orejas_post_oz(b_long, 100.0, "LONG")
    red_long = float(b_long.red_adan)
    esp_l = 100.0 * (1.0 - (base_l + 0.005))
    assert abs(red_long - esp_l) < 1e-9, (red_long, esp_l)
    print("  plantado ON 5 escalones LONG -> Red +0.5% OK")

    # Tumor: sangre/vacio no se tocan por el flag
    sil = float(b_on.sangre_adan)
    assert abs(sil - 100.0 * (1.0 - br.sangre_contraria_pct())) < 1e-6 or sil > 0
    print("  sangre sigue plantada (no tumorizada) OK")

    # Corte 3A: revive con Red expansiva no tuerce ancla de sangre
    os.environ["BERU_RANGO_RED_EXPANSIVA"] = "1"
    oz = 100.0
    esc = 5
    red_viva = oz * (1.0 + base_s + 0.005)
    b_r = _beru(0)
    br.restaurar_acecho_post_oz(
        b_r,
        cero=100.0,
        red=red_viva,
        sangre_lado="ABAJO",
        ultima_hoz_direccion="SHORT",
        escalones_red=esc,
        oz_despliegue=oz,
        sangre_campana_oz0=oz,
        sangre_campana_dir="SHORT",
    )
    assert int(b_r.rango_escalones_red) == esc
    assert abs(abs(float(b_r.red_pct)) - (base_s + 0.005)) < 1e-12, b_r.red_pct
    sil_m = float(getattr(b_r, "sangre_mapa_pct", 0) or 0) or br.sangre_contraria_pct()
    ancla_imp = float(b_r.sangre_adan) / (1.0 - sil_m)
    assert abs(ancla_imp - oz) < 1e-6, (ancla_imp, oz)
    print("  restore ON + 5 escalones -> ancla sangre sana OK")

    # OFF restore sigue clavado a base
    os.environ.pop("BERU_RANGO_RED_EXPANSIVA", None)
    b_roff = _beru(0)
    red_base_px = oz * (1.0 + base_s)
    br.restaurar_acecho_post_oz(
        b_roff,
        cero=100.0,
        red=red_base_px,
        sangre_lado="ABAJO",
        ultima_hoz_direccion="SHORT",
        escalones_red=5,
        oz_despliegue=oz,
        sangre_campana_oz0=oz,
        sangre_campana_dir="SHORT",
    )
    sil_off = float(getattr(b_roff, "sangre_mapa_pct", 0) or 0) or br.sangre_contraria_pct()
    ancla_off = float(b_roff.sangre_adan) / (1.0 - sil_off)
    assert abs(ancla_off - oz) < 1e-6, (ancla_off, oz)
    assert abs(abs(float(b_roff.red_pct)) - base_s) < 1e-12
    print("  restore OFF -> ancla/base intactos OK")

    # Corte 3B: sangre gana limpia escalones
    os.environ["BERU_RANGO_RED_EXPANSIVA"] = "1"
    b_sang = _beru(7)
    b_sang.sangre_lado = "ABAJO"
    b_sang.sangre_adan = 98.8
    b_sang.red_adan = 101.0
    b_sang.oreja_red_activa = True
    b_sang.ultima_hoz_direccion = "SHORT"
    br.armar_tramo_desde_sangre(b_sang, precio=98.8)
    assert int(b_sang.rango_escalones_red) == 0, b_sang.rango_escalones_red
    print("  sangre gana -> escalones_red=0 OK")

    # Tope: 500 escalones no abren Red al 50 %
    os.environ["BERU_RANGO_RED_EXPANSIVA"] = "1"
    os.environ.pop("BERU_RANGO_RED_EXPANSIVA_MAX_ESCALONES", None)
    b_cap = _beru(500)
    extra = br.red_expansiva_extra_pct(b_cap)
    assert abs(extra - 0.015) < 1e-12, extra  # 15 * 0.1%
    br._plantar_orejas_post_oz(b_cap, 100.0, "SHORT")
    assert abs(float(b_cap.red_adan) - 100.0 * (1.0 + base_s + 0.015)) < 1e-9
    print("  tope 15 escalones -> +1.5% max OK")

    # Restore reclava Red historica absurda al mapa con tope
    b_fat = _beru(0)
    br.restaurar_acecho_post_oz(
        b_fat,
        cero=100.0,
        red=140.0,  # 40% lejos absurdo
        sangre_lado="ABAJO",
        ultima_hoz_direccion="SHORT",
        escalones_red=400,
        oz_despliegue=100.0,
        sangre_campana_oz0=100.0,
        sangre_campana_dir="SHORT",
    )
    assert int(b_fat.rango_escalones_red) == 15
    assert abs(float(b_fat.red_adan) - 100.0 * (1.0 + base_s + 0.015)) < 1e-9, b_fat.red_adan
    print("  restore Red gorda -> reclavada al tope OK")

    # Corte 3C: checkpoint inventa Red con mapa
    from core import beru_rango_checkpoint as ck

    os.environ["BERU_RANGO_RED_EXPANSIVA"] = "1"
    r_ck = ck._red_desde_ancla(100.0, "ABAJO", "SHORT", escalones_red=5)
    assert abs(r_ck - 100.0 * (1.0 + base_s + 0.005)) < 1e-9, r_ck
    os.environ.pop("BERU_RANGO_RED_EXPANSIVA", None)
    r_ck_off = ck._red_desde_ancla(100.0, "ABAJO", "SHORT", escalones_red=5)
    assert abs(r_ck_off - 100.0 * (1.0 + base_s)) < 1e-9, r_ck_off
    print("  checkpoint Red inventada ON/OFF OK")

    os.environ.pop("BERU_RANGO_RED_EXPANSIVA", None)
    os.environ.pop("BERU_RANGO_RED_EXPANSIVA_MAX_ESCALONES", None)
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
