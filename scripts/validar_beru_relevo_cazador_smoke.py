#!/usr/bin/env python3
"""Smoke frío — orejas post-Hoz: sangre 1.1 · Red apaga sangre · Hoz condicional."""
from __future__ import annotations

import sys
import asyncio
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.models import BeruShip
from core import beru_altar_cazador as altar
from core import beru_continuo as bc
from generales.capitanes import CapitanNormal


PASO = {
    "SOLDADO": 0.625,
    "CAPITAN": 1.25,
    "GENERAL": 2.50,
    "MARISCAL": 5.00,
}
CASOS = (
    ("BERUBBY", "SOLDADO", 0.009, 6.25),
    ("PROTO2", "CAPITAN", 0.005, 12.50),
    ("PROTO1", "GENERAL", 0.003, 25.0),
)


def barco(tier: str, uid: str = "BERU_SEM_ETH_PADRE") -> BeruShip:
    return BeruShip(
        uid=uid,
        centro_local=100.0,
        centro_manto=100.0,
        ancla_tramo=100.0,
        masa=0.0,
        direccion="LONG",
        estado="ACECHANDO",
        adn_capitan=CapitanNormal,
        tier_id=tier,
        modo_combate="CAZA",
    )


def pulso(b: BeruShip, precio: float):
    return altar.pulsar_cazador_sim(b, precio, activo="ETH")


def test_relevo_por_grado() -> None:
    for tier, grado, offset, masa_primera in CASOS:
        b = barco(tier, f"BERU_SEM_ETH_{grado}")
        pulso(b, 100.0)
        r = pulso(b, 101.10)
        assert r.eventos[0].tipo == "ARMAR_CONDICIONAL"
        assert abs(b.masa - masa_primera) < 1e-9

        r = pulso(b, 101.20)
        assert r.eventos[0].tipo == "MOVER_CONDICIONAL"
        assert abs(b.ultima_red_tocada_precio - 101.20) < 1e-9

        r = pulso(b, 101.10)
        hijo = r.relevo
        assert hijo is not None
        assert b.estado == "COSECHADO"
        assert hijo.estado == "ACECHANDO"
        assert hijo.oreja_sangre_activa
        assert hijo.oreja_red_activa
        assert abs(hijo.ancla_tramo - 101.10) < 1e-9
        assert abs(hijo.llamado_red_pct - offset) < 1e-9

        # Red gana: sangre apagada, arma desde última Red tocada.
        llamado_red = 101.20 + 100.0 * offset
        r_hijo = pulso(hijo, llamado_red)
        assert r_hijo.eventos[0].tipo == "ARMAR_CONDICIONAL"
        assert not hijo.oreja_sangre_activa
        assert abs(hijo.ancla_tramo - 101.20) < 1e-9
        assert abs(hijo.masa - 5.0) < 1e-9

        assert altar.crear_relevo_desde_hoz(
            b, 101.10, activo="ETH", fill_confirmado=True,
        ) is None


def test_sangre_desde_ultima_hoz() -> None:
    """Si vuelve a la sangre antes que la Red, arma desde la Hoz cobrada."""
    b = barco("BERUBBY", "BERU_SEM_ETH_SANGRE")
    pulso(b, 100.0)
    pulso(b, 101.10)
    pulso(b, 101.20)
    r = pulso(b, 101.10)
    hijo = r.relevo
    assert hijo is not None
    assert hijo.oreja_sangre_activa
    # Sangre ±1.1 desde Hoz 101.10 por abajo → 99.99 (Red arriba en 102.11 gana antes).
    r2 = pulso(hijo, 99.99)
    assert r2.eventos[0].tipo == "ARMAR_CONDICIONAL"
    assert not hijo.oreja_sangre_activa
    assert abs(hijo.ancla_tramo - 101.10) < 1e-9
    assert hijo.direccion == "LONG"


def test_red_apaga_sangre_sin_revivir() -> None:
    """Red gana → sangre muerta; no revive hasta nueva Hoz."""
    b = barco("BERUBBY", "BERU_SEM_ETH_APAGAR")
    pulso(b, 100.0)
    pulso(b, 101.10)
    pulso(b, 101.20)
    r = pulso(b, 101.10)
    hijo = r.relevo
    assert hijo is not None
    llamado_red = 101.20 + 100.0 * 0.009
    pulso(hijo, llamado_red)
    assert not hijo.oreja_sangre_activa
    assert hijo.estado == "CAZANDO"
    # Sangre vieja no revive: latido neutro sin re-armar orejas.
    r3 = pulso(hijo, 102.15)
    assert not r3.eventos
    assert not hijo.oreja_sangre_activa


def test_hijo_marcado_relevo() -> None:
    b = barco("BERUBBY", "BERU_SEM_ETH_FLAG")
    pulso(b, 100.0)
    pulso(b, 101.10)
    pulso(b, 101.20)
    hijo = pulso(b, 101.10).relevo
    assert hijo is not None
    assert hijo.es_relevo_cazador


def test_fallo_armado_restaura_orejas() -> None:
    """Reserva fallida: hijo no vuelve a ser semilla; orejas reviven."""
    b = barco("BERUBBY", "BERU_SEM_ETH_FALLO")
    pulso(b, 100.0)
    pulso(b, 101.10)
    pulso(b, 101.20)
    hijo = pulso(b, 101.10).relevo
    assert hijo is not None
    llamado_red = 101.20 + 100.0 * 0.009
    oreja = bc.decidir_oreja_acecho(hijo, llamado_red)
    assert oreja == "RED"
    bc.armar_tramo(hijo, llamado_red, activo="ETH", grado="SOLDADO", oreja=oreja)
    bc.restaurar_acecho_tras_fallo_armado(hijo)
    assert hijo.estado == "ACECHANDO"
    assert hijo.oreja_sangre_activa
    assert hijo.oreja_red_activa
    assert abs(hijo.ancla_tramo - 101.10) < 1e-9
    assert bc.decidir_oreja_acecho(hijo, 101.05) == ""


def test_lado_negativo() -> None:
    b = barco("BERUBBY", "BERU_SEM_ETH_NEG")
    pulso(b, 100.0)
    pulso(b, 98.90)
    pulso(b, 98.80)
    assert b.direccion == "LONG"
    r = pulso(b, 98.90)
    hijo = r.relevo
    assert hijo is not None
    llamado_red = 98.80 - 100.0 * 0.009
    pulso(hijo, llamado_red)
    assert abs(hijo.oz_adan - (llamado_red + 0.10)) < 1e-9
    assert abs(hijo.masa - 5.0) < 1e-9


def test_fill_y_mariscal() -> None:
    b = barco("BERUBBY", "BERU_SEM_ETH_NOFILL")
    pulso(b, 100.0)
    pulso(b, 101.10)
    pulso(b, 101.20)
    assert altar.crear_relevo_desde_hoz(
        b, 101.10, activo="ETH", fill_confirmado=False,
    ) is None
    assert b.estado == "CAZANDO"

    m = barco("PLENO", "BERU_SEM_ETH_MARISCAL")
    pulso(m, 100.0)
    pulso(m, 101.10)
    pulso(m, 101.20)
    r = pulso(m, 101.10)
    assert r.relevo is None
    assert m.estado == "COSECHADO"
    assert m.relevo_creado


def test_integracion_general_y_cuarentena() -> None:
    from generales.beru import BeruCazador

    class Bel:
        def __init__(self):
            self.eventos = []

        async def anotar(self, *args):
            self.eventos.append(args)

    class Tank:
        capitan_activo = CapitanNormal

    class Tusk:
        pesos = {}
        masa_autorizada = 0.0
        masa_bruta_real = 0.0
        masa_bruta = 0.0

    bel = Bel()
    general = BeruCazador(Tusk(), bel, Tank())
    padre = barco("BERUBBY", "BERU_SEM_ETH_INTEGRACION")
    pulso(padre, 100.0)
    pulso(padre, 101.10)
    pulso(padre, 101.20)

    async def cosecha_confirmada(b, _uid, forzar=False):
        _ = forzar
        b.precio_salida_real = 101.10
        b.estado = "COSECHADO"

    general._ejecutar_cosecha = cosecha_confirmada
    general.legion = [padre]
    asyncio.run(general._cosecha_capa_cazador(padre, 101.10))
    hijos = [b for b in general.legion if b.padre_cazador_uid == padre.uid]
    assert len(hijos) == 1
    assert hijos[0].estado == "ACECHANDO"
    assert hijos[0].oreja_sangre_activa


def main() -> int:
    with patch(
        "core.beru_cazador.engorde_paso_usd",
        side_effect=lambda _a, g: PASO[str(g).upper()],
    ):
        test_relevo_por_grado()
        test_sangre_desde_ultima_hoz()
        test_red_apaga_sangre_sin_revivir()
        test_hijo_marcado_relevo()
        test_fallo_armado_restaura_orejas()
        test_lado_negativo()
        test_fill_y_mariscal()
        test_integracion_general_y_cuarentena()
    print(
        "OK validar_beru_relevo_cazador_smoke "
        "(sangre 1.1 desde Hoz · Red apaga sangre · Hoz condicional)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
