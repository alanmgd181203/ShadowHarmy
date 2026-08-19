#!/usr/bin/env python3
"""
Smoke Sub-Santuario Beru — core/beru_asset_detail.py

Verifica:
  A) Estado cero
  B) Flota por activo + composición caza/neg
  C) Red engorde (frontera)
  D) Crónica append / load
  E) mapa_asset_details + enriquecer_legion
  I) masa prometida + chip saco = Vacío ahora (acecho) / Hoz viva (caza)
  K) calor flota + tarjeta (chip acecho ≠ 0)

Uso: python scripts/validar_beru_asset_detail_smoke.py
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from core import beru_asset_detail as bad  # noqa: E402


def _assert(cond: bool, msg: str) -> None:
    if not cond:
        raise AssertionError(msg)


def _barco(**kw):
    base = dict(
        uid="BERU_SEM_ETH_1",
        estado="CAZANDO",
        direccion="LONG",
        masa=25.0,
        masa_congelada=25.0,
        centro_manto=3000.0,
        centro_local=3000.0,
        oz_adan=3015.0,
        red_adan=2970.0,
        oz_pct=0.005,
        red_pct=-0.01,
        frente_asignado="ETHUSDT_SPOT",
        precio_entrada_real=3000.0,
        precio_salida_real=0.0,
        tier_id="PROTO1",
        modo_combate="CAZA",
        capa=1,
        generacion=1,
        es_super_beru=False,
        ciclo_infinito=False,
        neg_post_cazador=False,
        neg_toques_ciclo=0,
        ancla_cosecha_pct=0.0,
        max_favor=0.0,
    )
    base.update(kw)
    return SimpleNamespace(**base)


def test_cero() -> None:
    s = bad.snapshot_cero("ETH")
    _assert(s["symbol"] == "ETH", "symbol")
    _assert(s["fuente"] == "cero", "fuente")
    _assert(s["n_barcos"] == 0, "barcos 0")
    _assert(s["composicion"]["pct_caza"] == 0, "pct caza")
    print("  A) estado cero OK")


def test_flota_composicion() -> None:
    leg = [
        _barco(uid="BERU_SEM_ETH_CAZA", modo_combate="CAZA", estado="CAZANDO"),
        _barco(
            uid="BERU_SEM_BTC_1",
            frente_asignado="BTCUSDT_SPOT",
            centro_manto=100000.0,
            oz_adan=100100.0,
            red_adan=99000.0,
            precio_entrada_real=100000.0,
        ),
    ]
    flota = bad.flota_resumen(leg, semilla="ETH")
    acts = {a["activo"]: a for a in flota["activos"]}
    _assert("ETH" in acts and "BTC" in acts, "activos ETH+BTC")
    _assert(acts["ETH"]["n_caza"] >= 1, "eth caza")
    _assert(acts["ETH"]["n_negociando"] == 0, "sin negociador")
    _assert(acts["ETH"]["es_semilla"] is True, "semilla ETH")
    snap = bad.snapshot_activo("ETH", leg, precio_mark=3010.0, semilla="ETH")
    _assert(snap["n_barcos"] == 1, f"eth barcos {snap['n_barcos']}")
    _assert(snap["masa_total_usd"] > 0, "masa")
    _assert(snap["pnl_est_usd"] is not None, "pnl")
    _assert(len(snap["grafica"]["niveles"]) >= 1, "grafica")
    print("  B) flota composición OK")


def test_red_engorde() -> None:
    # Un cazador continuo por Santo: su propia Red es la frontera.
    b = _barco(uid="BERU_B", red_adan=2950.0, red_pct=-0.0167, estado="CAZANDO", modo_combate="CAZA")
    re = bad.red_engorde_de_legion([b], "ETH")
    _assert(re is not None, "red existe")
    _assert(re["uid"] == "BERU_B", f"frontera {re['uid']}")
    _assert(re["precio"] == 2950.0, "precio frontera")
    print("  C) red engorde OK")


def test_cronica() -> None:
    prev = bad.CRONICA_DIR
    with tempfile.TemporaryDirectory() as td:
        bad.CRONICA_DIR = Path(td)
        try:
            bad.append_cronica("ETH", {"tipo": "COSECHA", "detalle": "botín test", "precio": 3010})
            bad.append_cronica("ETH", {"tipo": "COSECHA_TRAMO", "detalle": "nuevo 0 local"})
            rows = bad._cargar_cronica("ETH", limit=10)
            _assert(len(rows) == 2, f"rows {len(rows)}")
            _assert(rows[-1]["tipo"] == "COSECHA_TRAMO", "ultimo tramo")
            snap = bad.snapshot_activo("ETH", [], semilla="ETH")
            _assert(len(snap["cronica"]) == 2, "cronica en snapshot")
        finally:
            bad.CRONICA_DIR = prev
    print("  D) crónica OK")


def test_dos_ceros_grafica_carta() -> None:
    b = _barco(
        centro_manto=3000.0,
        centro_local=3100.0,
        centro_wake=3100.0,
        altar_link_id="LINK-ETH-1",
        oz_adan=3015.0,
        red_adan=2970.0,
    )
    snap = bad.snapshot_activo("ETH", [b], precio_mark=3010.0, semilla="ETH")
    fila = snap["barcos"][0]
    _assert(fila["centro_manto"] == 3000.0, "manto no mezclado")
    _assert(fila["centro_wake"] == 3100.0, "wake no mezclado")
    _assert(fila["carta_colgada"] is True, "carta colgada")
    # Caza LONG: Hoz abajo; una sola sangre arriba, 1.1 de esa Hoz.
    # Hoz 3015 · manto 3000 → sangre 3048.
    _assert(fila.get("vacio_abajo") in (None, 0, 0.0), f"sin Vacío del lado Hoz {fila.get('vacio_abajo')}")
    _assert(abs(float(fila["vacio_arriba"]) - 3048.0) < 1e-6, f"vacio up {fila['vacio_arriba']}")
    _assert(snap["centro_manto"] == 3000.0, "snap manto")
    _assert(snap["centro_wake"] == 3100.0, "snap wake")
    roles = {n.get("rol") for n in (snap.get("grafica") or {}).get("niveles") or []}
    for r in ("manto", "wake", "vacio", "spot", "oz", "red"):
        _assert(r in roles, f"rol gráfica {r} en {roles}")
    cero = bad.snapshot_cero("ETH")
    _assert(cero["centro_manto"] == 0.0 and cero["centro_wake"] == 0.0, "cero 00")
    print("  F) dos ceros + gráfica + carta OK")


def test_vacio_metro_doctrina() -> None:
    """Manto 100, wake 130 → campanas 131,1 / 128,9. Nunca 130×1,011."""
    b = _barco(
        estado="ACECHANDO",
        modo_combate="ACECHANDO",
        centro_manto=100.0,
        centro_local=130.0,
        centro_wake=130.0,
        ancla_tramo=130.0,
        oz_adan=0.0,
        red_adan=0.0,
        precio_entrada_real=0.0,
        altar_link_id="",
    )
    fila = bad._barco_fila(b, "ETH", precio_mark=130.0)
    _assert(abs(float(fila["vacio_arriba"]) - 131.1) < 1e-9, f"up {fila['vacio_arriba']}")
    _assert(abs(float(fila["vacio_abajo"]) - 128.9) < 1e-9, f"dn {fila['vacio_abajo']}")
    src = Path(ROOT, "core", "beru_asset_detail.py").read_text(encoding="utf-8")
    _assert("wake * 1.011" not in src, "sin atajo % del wake")
    _assert("precio_desde_ancla" in src, "misma cuenta que el cazador")
    print("  G) Vacío metro doctrina OK")


def test_hoz_solo_si_carta_colgada() -> None:
    """Pensar oz_adan no pinta Hoz. Solo carta colgada."""
    pensada = _barco(oz_adan=3015.0, altar_link_id="", red_adan=2970.0)
    snap_p = bad.snapshot_activo("ETH", [pensada], precio_mark=3010.0, semilla="ETH")
    roles_p = {n.get("rol") for n in (snap_p.get("grafica") or {}).get("niveles") or []}
    _assert("oz" not in roles_p, f"sin carta no hay Hoz {roles_p}")
    colgada = _barco(oz_adan=3015.0, altar_link_id="BERU-HOZ-1", red_adan=2970.0)
    snap_c = bad.snapshot_activo("ETH", [colgada], precio_mark=3010.0, semilla="ETH")
    roles_c = {n.get("rol") for n in (snap_c.get("grafica") or {}).get("niveles") or []}
    _assert("oz" in roles_c, f"con carta sí hay Hoz {roles_c}")
    oz = next(n for n in (snap_c.get("grafica") or {}).get("niveles") or [] if n.get("rol") == "oz")
    _assert(float(oz.get("masa_usd") or 0) + 1e-9 >= 24.95, f"saco Hoz {oz.get('masa_usd')}")
    print("  H) Hoz solo carta colgada OK")


def test_masa_prometida_grafica() -> None:
    """Vacío al nacer y Red en caza/relevo llevan masa ya pasada por el lote."""
    nace = _barco(
        estado="ACECHANDO",
        oz_adan=0.0,
        red_adan=0.0,
        masa=0.0,
        masa_congelada=0.0,
        altar_link_id="",
        centro_manto=100.0,
        centro_local=130.0,
        centro_wake=130.0,
        ancla_tramo=130.0,
        precio_entrada_real=0.0,
    )
    snap_n = bad.snapshot_activo("ETH", [nace], precio_mark=130.0, semilla="ETH")
    vacios = [
        n for n in (snap_n.get("grafica") or {}).get("niveles") or []
        if n.get("rol") == "vacio"
    ]
    _assert(len(vacios) == 2, f"dos campanas {vacios}")
    masas_v = [float(n.get("masa_usd") or 0) for n in vacios]
    _assert(all(m >= 5.0 for m in masas_v), f"Vacío ≥ lote casa {masas_v}")
    _assert(abs(masas_v[0] - masas_v[1]) < 0.5, f"mismas dos campanas {masas_v}")

    caza = _barco(
        estado="CAZANDO",
        masa=25.0,
        altar_link_id="BERU-HOZ-1",
        centro_manto=100.0,
        centro_local=130.0,
        centro_wake=130.0,
        ancla_tramo=130.0,
        oz_adan=131.0,
        red_adan=131.2,
        oz_pct=0.01,
        red_pct=0.012,
        direccion="SHORT",
    )
    snap_c = bad.snapshot_activo("ETH", [caza], precio_mark=130.5, semilla="ETH")
    reds = [
        n for n in (snap_c.get("grafica") or {}).get("niveles") or []
        if n.get("rol") in ("red", "red_engorde") and float(n.get("masa_usd") or 0) > 0
    ]
    _assert(reds, "Red de caza con masa")
    _assert(float(reds[0]["masa_usd"]) + 1e-9 >= 25.0 - 0.05, f"acumulado {reds[0]['masa_usd']}")

    hijo = _barco(
        uid="BERU_SEM_ETH_R2",
        estado="ACECHANDO",
        es_relevo_cazador=True,
        oreja_sangre_activa=True,
        oreja_red_activa=True,
        direccion="SHORT",
        masa=0.0,
        masa_congelada=0.0,
        oz_adan=0.0,
        red_adan=0.0,
        altar_link_id="",
        centro_manto=100.0,
        centro_local=101.1,
        ancla_tramo=101.1,
        ultima_red_tocada_precio=101.2,
        llamado_red_pct=0.003,
        precio_entrada_real=0.0,
    )
    snap_h = bad.snapshot_activo("ETH", [hijo], precio_mark=101.15, semilla="ETH")
    red_h = [
        n for n in (snap_h.get("grafica") or {}).get("niveles") or []
        if n.get("rol") == "red"
    ]
    _assert(len(red_h) == 1, f"Red relevo {red_h}")
    _assert(abs(float(red_h[0]["precio"]) - 101.5) < 1e-6, f"precio relevo {red_h[0]['precio']}")
    _assert(float(red_h[0].get("masa_usd") or 0) >= 4.5, f"nacimiento {red_h[0].get('masa_usd')}")
    _assert(float(red_h[0].get("masa_usd") or 0) < 8.0, f"hijo no es saco de semilla {red_h[0].get('masa_usd')}")
    vac_h = [
        n for n in (snap_h.get("grafica") or {}).get("niveles") or []
        if n.get("rol") == "vacio"
    ]
    _assert(len(vac_h) == 1, f"hijo una sangre {vac_h}")
    _assert(vac_h[0].get("id") == "vacio_dn", vac_h)
    _assert(abs(float(vac_h[0]["precio"]) - 100.0) < 1e-6, vac_h[0])
    roles_h = {n.get("rol") for n in (snap_h.get("grafica") or {}).get("niveles") or []}
    _assert("wake" in roles_h, f"hijo 0 local {roles_h}")
    _assert("oz" not in roles_h, f"hijo acecho sin Hoz {roles_h}")
    _assert("manto" in roles_h, roles_h)
    flota_n = bad.flota_resumen([nace], semilla="ETH", precios={"ETH": 130.0})
    eth_n = next(a for a in flota_n["activos"] if a["activo"] == "ETH")
    masa_n = max(masas_v)
    _assert(
        abs(float(eth_n["saco_usd"]) - masa_n) < 0.05,
        f"chip nace {eth_n['saco_usd']} ≠ Vacío {masa_n}",
    )
    flota_h = bad.flota_resumen([hijo], semilla="ETH", precios={"ETH": 101.15})
    eth_h = next(a for a in flota_h["activos"] if a["activo"] == "ETH")
    masa_h = max(float(n.get("masa_usd") or 0) for n in vac_h)
    _assert(
        abs(float(eth_h["saco_usd"]) - masa_h) < 0.05,
        f"chip hijo {eth_h['saco_usd']} ≠ Vacío {masa_h}",
    )
    _assert(float(eth_h["saco_usd"]) < 8.0, f"hijo chip no es saco padre {eth_h['saco_usd']}")
    print("  I) masa prometida Vacío/Red OK")


def test_sangre_persigue_y_x() -> None:
    """En caza, una sola sangre: 1,1 al otro lado de la Hoz. × de fill."""
    caza = _barco(
        estado="CAZANDO",
        direccion="SHORT",
        masa=25.0,
        altar_link_id="BERU-HOZ-1",
        centro_manto=100.0,
        centro_local=130.0,
        centro_wake=130.0,
        ancla_tramo=130.0,
        oz_adan=131.0,
        red_adan=131.2,
        oz_pct=0.01,
        red_pct=0.012,
    )
    fila = bad._barco_fila(caza, "ETH", precio_mark=130.5)
    _assert(not fila.get("vacio_arriba"), f"sin Vacío del lado de la Hoz {fila.get('vacio_arriba')}")
    _assert(abs(float(fila["vacio_abajo"]) - 129.9) < 1e-9, f"contrario {fila['vacio_abajo']}")
    marks = bad._cazas_de_cronica([
        {"tipo": "COSECHA", "ts": 1700000000, "precio": 131.0, "direccion": "SHORT"},
        {"tipo": "COSECHA", "ts": 1700000900, "precio": 128.4, "direccion": "LONG"},
        {"tipo": "ACECHO", "ts": 1700001000, "precio": 130.0, "direccion": "SHORT"},
    ])
    _assert(len(marks) == 2, f"solo cosechas {marks}")
    _assert(marks[0]["lado"] == "Sell", marks[0])
    _assert(marks[1]["lado"] == "Buy", marks[1])
    print("  J) sangre persigue + × de caza OK")


def test_calor_y_tarjeta() -> None:
    """Cazando arriba de acecho. Tarjeta: oficio, saco, grado, paso 0,1."""
    caza = _barco(estado="CAZANDO", masa=25.0, altar_link_id="BERU-HOZ-1")
    acecho = _barco(
        uid="BERU_SEM_ADA_1",
        frente_asignado="ADAUSDT_SPOT",
        estado="ACECHANDO",
        oz_adan=0.0,
        red_adan=0.0,
        masa=0.0,
        masa_congelada=0.0,
        centro_manto=100.0,
        centro_local=130.0,
        centro_wake=130.0,
        ancla_tramo=130.0,
        precio_entrada_real=0.0,
        altar_link_id="",
    )
    flota = bad.flota_resumen(
        [caza, acecho],
        semilla="ETH",
        precios={"ETH": 3010.0, "ADA": 130.95},
    )
    orden = [a["activo"] for a in flota["activos"]]
    _assert(orden[0] == "ETH", f"caza arriba {orden}")
    eth = next(a for a in flota["activos"] if a["activo"] == "ETH")
    ada = next(a for a in flota["activos"] if a["activo"] == "ADA")
    _assert(eth["oficio"] == "cazando", eth["oficio"])
    _assert(ada["oficio"] == "acechando", ada["oficio"])
    _assert(float(eth["saco_usd"]) + 1e-9 >= 24.95, f"saco {eth['saco_usd']}")
    snap_ada = bad.snapshot_activo("ADA", [acecho], precio_mark=130.95, semilla="ETH")
    vac_ada = [
        n for n in (snap_ada.get("grafica") or {}).get("niveles") or []
        if n.get("rol") == "vacio"
    ]
    masa_ada = max((float(n.get("masa_usd") or 0) for n in vac_ada), default=0.0)
    _assert(masa_ada >= 5.0, f"ADA Vacío {masa_ada}")
    _assert(
        abs(float(ada["saco_usd"]) - masa_ada) < 0.05,
        f"chip ADA {ada['saco_usd']} ≠ Vacío {masa_ada}",
    )
    _assert(eth["grado"] == "GENERAL", eth.get("grado"))
    _assert(float(eth["engorde_paso_usd"]) > 0, "paso 0,1")
    _assert(eth["calor_banda"] == 0, f"banda eth {eth['calor_banda']}")
    _assert(int(ada["calor_banda"]) >= 1, f"banda ada {ada['calor_banda']}")
    print("  K) calor flota + tarjeta OK")


def test_oculta_huecos() -> None:
    """Sin Beru o sin manto, el Santo no entra a la flota. Semilla vacía tampoco."""
    prev = bad.CRONICA_DIR
    with tempfile.TemporaryDirectory() as td:
        bad.CRONICA_DIR = Path(td)
        try:
            flota = bad.flota_resumen([_barco()], semilla="ETH")
            acts = {a["activo"] for a in flota["activos"]}
            _assert("ETH" in acts, "ETH con Beru y manto")
            _assert("BTC" not in acts, "semilla vacía no lista")
            hueco = _barco(
                uid="BERU_SEM_BTC_1",
                frente_asignado="BTCUSDT_SPOT",
                centro_manto=0.0,
                centro_local=0.0,
                masa=0.0,
                masa_congelada=0.0,
                estado="ACECHANDO",
                modo_combate="ACECHANDO",
            )
            flota2 = bad.flota_resumen([hueco], semilla="BTC")
            _assert(all(float(a.get("centro_manto") or 0) > 0 for a in flota2["activos"]), "sin manto no lista")
            _assert(all(int(a.get("n_barcos") or 0) > 0 for a in flota2["activos"]), "sin Beru no lista")
            eth = next(a for a in flota["activos"] if a["activo"] == "ETH")
            _assert(eth["grado"] in ("SOLDADO", "CAPITAN", "GENERAL", "MARISCAL"), f"grado {eth.get('grado')}")
            _assert("ultima_lecturas" in eth, "chip lecturas")
        finally:
            bad.CRONICA_DIR = prev
    print("  L) huecos fuera de flota OK")


def test_mapa_cerrados_y_dist() -> None:
    """Mariscal cerrado aparece abajo; acecho muestra distancia; caza va primero."""
    prev = bad.CRONICA_DIR
    with tempfile.TemporaryDirectory() as td:
        bad.CRONICA_DIR = Path(td)
        try:
            bad.append_cronica(
                "MNT",
                {"tipo": "COSECHA", "detalle": "mariscal", "precio": 0.43, "beneficio_pct": -1.38},
            )
            caza = _barco(
                uid="BERU_SEM_ETH_CAZA",
                estado="CAZANDO",
                modo_combate="CAZA",
                spot_last=3010.0,
            )
            acecho = _barco(
                uid="BERU_SEM_ADA_1",
                frente_asignado="ADAUSDT_SPOT",
                estado="ACECHANDO",
                modo_combate="ACECHANDO",
                masa=0.0,
                masa_congelada=0.0,
                oz_adan=0.0,
                red_adan=0.0,
                altar_link_id="",
                centro_manto=0.18,
                centro_local=0.175,
                vacio_arriba=0.177,
                vacio_abajo=0.173,
                spot_last=0.1755,
                grado="MARISCAL",
            )
            with __import__("unittest.mock", fromlist=["patch"]).patch(
                "core.beru_wake.leer_wake_ritual", return_value=1.0,
            ):
                flota = bad.flota_resumen(
                    [caza, acecho],
                    semilla="ETH",
                    precios={"ETH": 3010.0, "ADA": 0.1755},
                )
            acts = [a["activo"] for a in flota["activos"]]
            _assert(acts[0] == "ETH", f"caza primero {acts}")
            _assert("ADA" in acts, "acecho vivo")
            _assert(acts[-1] == "MNT", f"cerrado al fondo {acts}")
            mnt = next(a for a in flota["activos"] if a["activo"] == "MNT")
            _assert(mnt["oficio"] == "cerrado", mnt)
            _assert(mnt["dist_silbato"] is None, "cerrado sin %")
            ada = next(a for a in flota["activos"] if a["activo"] == "ADA")
            _assert(ada["oficio"] == "acechando", ada)
            _assert(ada.get("dist_silbato") is not None, "dist acecho")
        finally:
            bad.CRONICA_DIR = prev
    print("  N) cerrados + distancia OK")


def _hijo(activo: str, *, direccion: str, tier: str, ancla: float, ultima_red: float, llamado: float):
    return _barco(
        uid=f"BERU_SEM_{activo}_R2_TEST",
        frente_asignado=f"{activo}USDT_SPOT",
        estado="ACECHANDO",
        modo_combate="ACECHANDO",
        es_relevo_cazador=True,
        generacion=2,
        oreja_sangre_activa=True,
        oreja_red_activa=True,
        direccion=direccion,
        masa=0.0,
        masa_congelada=0.0,
        oz_adan=0.0,
        red_adan=0.0,
        altar_link_id="",
        centro_manto=100.0,
        centro_local=ancla,
        centro_wake=ancla,
        ancla_tramo=ancla,
        ultima_red_tocada_precio=ultima_red,
        llamado_red_pct=llamado,
        precio_entrada_real=0.0,
        tier_id=tier,
    )


def test_geometria_toda_la_flota() -> None:
    """Semilla / caza / relevo para varios Santos, ambos lados y tres rangos con hijo."""
    sem = _barco(
        uid="BERU_SEM_DOT_1",
        frente_asignado="DOTUSDT_SPOT",
        estado="ACECHANDO",
        modo_combate="ACECHANDO",
        oz_adan=0.0,
        red_adan=0.0,
        masa=0.0,
        masa_congelada=0.0,
        altar_link_id="",
        centro_manto=100.0,
        centro_local=130.0,
        centro_wake=130.0,
        ancla_tramo=130.0,
        precio_entrada_real=0.0,
    )
    snap_s = bad.snapshot_activo("DOT", [sem], precio_mark=130.0, semilla="ETH")
    vac_s = [n for n in snap_s["grafica"]["niveles"] if n.get("rol") == "vacio"]
    roles_s = {n.get("rol") for n in snap_s["grafica"]["niveles"]}
    _assert(len(vac_s) == 2, f"semilla dos Vacío {vac_s}")
    _assert("wake" in roles_s, roles_s)
    _assert("red" not in roles_s and "oz" not in roles_s, roles_s)

    caza_l = _barco(
        uid="BERU_SEM_FIL_1",
        frente_asignado="FILUSDT_SPOT",
        estado="CAZANDO",
        direccion="LONG",
        masa=25.0,
        altar_link_id="BERU-HOZ-FIL",
        centro_manto=100.0,
        centro_local=130.0,
        centro_wake=130.0,
        ancla_tramo=130.0,
        oz_adan=129.0,
        red_adan=128.8,
    )
    snap_cl = bad.snapshot_activo("FIL", [caza_l], precio_mark=129.5, semilla="ETH")
    roles_cl = {n.get("rol") for n in snap_cl["grafica"]["niveles"]}
    ids_cl = {n.get("id") for n in snap_cl["grafica"]["niveles"] if n.get("rol") == "vacio"}
    _assert(ids_cl == {"vacio_up"}, ids_cl)
    _assert("oz" in roles_cl and "red" in roles_cl, roles_cl)

    casos = [
        ("ADA", "SHORT", "PROTO1", 101.1, 101.2, 0.003, 101.5, "vacio_dn"),
        ("XRP", "LONG", "BERUBBY", 100.0, 99.0, 0.009, 98.1, "vacio_up"),
        ("SUI", "SHORT", "PROTO2", 101.0, 101.0, 0.005, 101.5, "vacio_dn"),
        ("OP", "LONG", "PROTO1", 100.0, 100.2, 0.003, 99.9, "vacio_up"),
    ]
    for act, direccion, tier, ancla, ultima, llamado, red_esp, keep in casos:
        hijo = _hijo(
            act, direccion=direccion, tier=tier,
            ancla=ancla, ultima_red=ultima, llamado=llamado,
        )
        snap = bad.snapshot_activo(act, [hijo], precio_mark=ancla, semilla="ETH")
        niveles = snap["grafica"]["niveles"]
        vac = [n for n in niveles if n.get("rol") == "vacio"]
        reds = [n for n in niveles if n.get("rol") == "red"]
        roles = {n.get("rol") for n in niveles}
        _assert(len(vac) == 1, f"{act} una sangre {vac}")
        ids = {n.get("id") for n in vac}
        _assert(ids == {keep}, f"{act} sangre {ids} ≠ {keep}")
        _assert(len(reds) == 1, f"{act} Red relevo {reds}")
        _assert(abs(float(reds[0]["precio"]) - red_esp) < 1e-6, f"{act} red {reds[0]['precio']} ≠ {red_esp}")
        _assert("wake" in roles, f"{act} 0 local {roles}")
        _assert("oz" not in roles, f"{act} oz {roles}")
        _assert("manto" in roles, roles)

    # Foto vieja de cualquier Santo: dos campanas + wake + Hoz pensada → se repara.
    for act, direccion, keep, red_px in (
        ("LINK", "SHORT", "vacio_dn", 12.4),
        ("AVAX", "LONG", "vacio_up", 18.1),
    ):
        vivo = {
            "uid": f"BERU_SEM_{act}_R3_OLD",
            "es_relevo": True,
            "generacion": 3,
            "estado": "ACECHANDO",
            "modo": "ACECHANDO",
            "direccion": direccion,
            "grado": "GENERAL",
            "vacio_arriba": 12.5,
            "vacio_abajo": 12.1,
            "vacio_pct": 1.1,
            "red_relevo_precio": red_px,
            "carta_colgada": False,
            "oreja_red": True,
            "centro_manto": 10.0,
            "ancla_tramo": 12.0,
            "centro_local": 12.0,
        }
        sucia = {
            "niveles": [
                {"id": "wake", "rol": "wake", "precio": 12.3},
                {"id": "vacio_up", "rol": "vacio", "precio": 12.5},
                {"id": "vacio_dn", "rol": "vacio", "precio": 12.1},
                {"id": "oz_old", "rol": "oz", "precio": 12.35},
            ],
            "cazas": [],
        }
        cron = [{"tipo": "COSECHA", "ts": 1700000000, "precio": 12.3, "direccion": direccion}]
        limpia = bad._reparar_grafica(sucia, vivo, cron)
        ids = [n.get("id") for n in limpia["niveles"] if n.get("rol") == "vacio"]
        roles = {n.get("rol") for n in limpia["niveles"]}
        _assert(ids == [keep], f"{act} foto vieja {ids} ≠ {keep}")
        _assert("wake" in roles, roles)
        wake = next(n for n in limpia["niveles"] if n.get("rol") == "wake")
        _assert(abs(float(wake["precio"]) - 12.0) < 1e-9, f"{act} 0 local {wake['precio']}")
        _assert(abs(float(limpia.get("centro_wake") or 0) - 12.0) < 1e-9, f"{act} centro_wake")
        _assert("oz" not in roles, roles)
        _assert("red" in roles, roles)
        _assert(len(limpia["cazas"]) == 1, limpia["cazas"])
        _assert(limpia["cazas"][0]["precio"] == 12.3, limpia["cazas"])
    print("  M) geometría toda la flota OK")


def test_mapa_y_enriquecer() -> None:
    leg = [_barco()]
    m = bad.mapa_asset_details(leg, precios={"ETH": 3010.0}, semilla="ETH")
    _assert("ETH" in m, "mapa ETH")
    _assert(m["ETH"]["fuente"] == "legion", "fuente legion")
    enr = bad.enriquecer_legion_resumen(leg, semilla="ETH")
    _assert(len(enr) == 1 and enr[0]["activo"] == "ETH", "enriquecer")
    _assert(bad.activo_de_legionario(leg[0], "ETH") == "ETH", "activo_de_legionario")
    print("  E) mapa + enriquecer OK")


def main() -> None:
    print("Smoke Sub-Santuario Beru")
    test_cero()
    test_flota_composicion()
    test_red_engorde()
    test_cronica()
    test_mapa_y_enriquecer()
    test_dos_ceros_grafica_carta()
    test_vacio_metro_doctrina()
    test_hoz_solo_si_carta_colgada()
    test_masa_prometida_grafica()
    test_sangre_persigue_y_x()
    test_calor_y_tarjeta()
    test_oculta_huecos()
    test_geometria_toda_la_flota()
    test_mapa_cerrados_y_dist()
    print("PASS 14/14")


if __name__ == "__main__":
    main()
