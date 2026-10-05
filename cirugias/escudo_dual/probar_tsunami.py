"""Papel del tsunami. No toca el escudo vivo."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from cirugias.escudo_dual import tsunami


class Barco:
    ultima_hoz_tocada_precio = 100.0
    voz_intencion = 0.0
    bandera_tsunami = ""
    bandera_desde = 0.0
    masa_tsunami = 0.0


def hoja(color, estado, desde, ts, masa, ahora):
    return {
        "ts": ts,
        "vivo": {
            "bandera_tsunami": color,
            "estado": estado,
            "bandera_desde": desde,
            "masa_tsunami": masa,
        },
    }


def ejército(verde, roja, ahora, masa=5.0):
    hojas = []
    for _ in range(verde):
        hojas.append(hoja("verde", "ACECHANDO", ahora - 60, ahora, masa, ahora))
    for _ in range(roja):
        hojas.append(hoja("roja", "CAZANDO", ahora - 90000, ahora, masa, ahora))
    return hojas


def main() -> None:
    from core.config import aplicar_perfil_beru_rango
    from core.beru_rango import masa_al_llamado

    aplicar_perfil_beru_rango("piedra")
    quieto = Barco()
    quieto.estado = "ACECHANDO"
    quieto.direccion = ""
    quieto.pierna_bando = "paz"
    assert abs(masa_al_llamado(quieto) - 8.52) < 0.02
    tsunami.marcar_bandera(quieto, 90, 1_000_000.0)
    assert abs(quieto.masa_tsunami - 8.52) < 0.02
    quieto.estado = "CAZANDO"
    quieto.direccion = "LONG"
    tsunami.marcar_bandera(quieto, 90, 1_000_000.0)
    assert quieto.masa_tsunami == 0.0

    ahora = 1_000_000.0
    b = Barco()
    assert tsunami.marcar_bandera(b, 90, ahora) == "verde"
    assert tsunami.marcar_bandera(b, 90, ahora + 10) == "verde"
    assert b.bandera_desde == ahora
    assert tsunami.marcar_bandera(b, 110, ahora + 20) == "roja"
    assert b.bandera_desde == ahora + 20
    assert tsunami.marcar_bandera(b, 100, ahora) == ""
    mudo = Barco()
    mudo.ultima_hoz_tocada_precio = 0
    assert tsunami.marcar_bandera(mudo, 90, ahora) == ""

    fresca = hoja("verde", "ACECHANDO", ahora - 60, ahora, 5, ahora)
    vieja = hoja("verde", "ACECHANDO", ahora - tsunami.DIA - 5, ahora, 5, ahora)
    cazando = hoja("roja", "CAZANDO", ahora - tsunami.DIA - 5, ahora, 0, ahora)
    podrida = hoja("verde", "CAZANDO", ahora, ahora - 1000, 5, ahora)
    assert tsunami.vota(fresca, ahora)
    assert not tsunami.vota(vieja, ahora)
    assert tsunami.vota(cazando, ahora)
    assert not tsunami.vota(podrida, ahora)

    assert tsunami.asiento_en_extasis(1000, 230, "verde") == 770
    assert tsunami.asiento_en_extasis(200, 900, "verde") == 0
    assert tsunami.asiento_en_extasis(1000, 230, "roja") == 1230
    assert tsunami.asiento_en_extasis(-1000, 230, "verde") == -1230
    assert tsunami.asiento_en_extasis(-1000, 400, "roja") == -600

    tsunami.olvidar_memoria()
    uno = tsunami.paso(ejército(90, 20, ahora), cruzado=1000, ahora=ahora)
    assert not uno["extasis"]
    assert uno["seguidas"] == 1
    dos = tsunami.paso(ejército(90, 20, ahora), cruzado=1000, ahora=ahora + 15)
    assert dos["extasis"]
    assert dos["color"] == "verde"
    assert dos["promesa"] == 90 * 5
    assert dos["asiento"] == 1000 - 450

    tsunami.olvidar_memoria()
    tsunami.paso(ejército(90, 20, ahora), cruzado=1000, ahora=ahora)
    tsunami.paso(ejército(90, 20, ahora), cruzado=1000, ahora=ahora + 15)
    salio = tsunami.paso(ejército(20, 20, ahora), cruzado=1000, ahora=ahora + 30)
    assert not salio["extasis"]

    tsunami.olvidar_memoria()
    poco = tsunami.paso(ejército(20, 2, ahora), cruzado=1000, ahora=ahora)
    assert not poco["extasis"]
    assert poco["seguidas"] == 0
    print("papel tsunami ok")


if __name__ == "__main__":
    main()
