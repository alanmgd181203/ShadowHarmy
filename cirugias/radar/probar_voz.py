"""La voz y el salto de mil. En seco. El que caza no lee el asiento."""
from __future__ import annotations

from cirugias.radar.voz import Escudo, firmar, suma, voz_de_hoja
from core import beru_rango
from core.beru_rango_balanza import cruzar_libreta


def _cerca(a: float, b: float, nombre: str) -> None:
    if abs(float(a) - b) > 1e-6:
        raise SystemExit(f"TUMOR {nombre}: salio {a}, debia {b}")
    print(f"OK  {nombre} = {a}")


def la_voz_es_el_lado() -> None:
    _cerca(firmar("SHORT", 3), 3.0, "tres de corto")
    _cerca(firmar("LONG", 2), -2.0, "dos de largo")
    _cerca(firmar("SHORT", 0), 0.0, "sin masa calla")
    voces = [firmar("SHORT", 800), firmar("SHORT", 700), firmar("LONG", 200)]
    _cerca(suma(voces), 1300.0, "la colmena suma 1300")


def quinientos_no_recortan() -> None:
    """Asentado en dos mil. Bajar quinientos se ve y el asiento no se mueve."""
    escudo = Escudo()
    _cerca(escudo.ver(2500), 2000.0, "dos mil quinientos sientan dos mil")
    _cerca(escudo.ver(2000), 2000.0, "quinientos de menos no recortan")
    _cerca(escudo.ver(1000), 1000.0, "al tocar el salto de abajo, recorta")
    print("OK  el salto sigue en mil")


def al_voltear_se_calla() -> None:
    escudo = Escudo()
    escudo.ver(2500)
    _cerca(escudo.ver(-2500), 0.0, "si la intencion voltea, el asiento cae")
    _cerca(escudo.ver(-2500), -2000.0, "el lado nuevo se sienta en el siguiente latido")


class _Beru:
    direccion = "LONG"
    estado = "CAZANDO"
    masa = 10.0
    voz_intencion = 0.0


def boca_fina_y_libreta() -> None:
    b = _Beru()
    beru_rango.publicar_voz(b, 1.0)
    # sin fill: firme 0, quiero long negativo
    _cerca(float(b.voz_quiero), float(b.voz_intencion), "quiero=intencion")
    beru_rango.registrar_voz_firme(b, 10.0)
    _cerca(float(b.voz_firme), -10.0, "firme long -10")
    _cerca(float(b.voz_delta), -10.0, "delta al firmar")
    hoja = {
        "voz_quiero": -12.0,
        "voz_firme": -10.0,
        "voz_delta": -10.0,
        "voz_intencion": -12.0,
    }
    _cerca(voz_de_hoja(hoja), -10.0, "hoja prioriza firme")
    cruz, fuente = cruzar_libreta(-10.0, -10.0, calibrar=False)
    _cerca(cruz, -10.0, "libreta sin calibrar")
    _cerca(1.0 if fuente == "libreta" else 0.0, 1.0, "fuente libreta")
    cruz2, fuente2 = cruzar_libreta(-10.0, -5000.0, calibrar=True)
    _cerca(cruz2, -5000.0, "casa gana si desalineada")
    _cerca(1.0 if fuente2 == "casa_desalineada" else 0.0, 1.0, "fuente casa")
    beru_rango.cerrar_voz_firme(b)
    _cerca(float(b.voz_firme), 0.0, "cerrar firme")
    print("OK  boca fina + libreta")


def main() -> None:
    la_voz_es_el_lado()
    quinientos_no_recortan()
    al_voltear_se_calla()
    boca_fina_y_libreta()
    print("VOZ_REVISADA")


if __name__ == "__main__":
    main()
