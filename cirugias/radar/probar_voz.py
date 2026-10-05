"""La voz y el salto de mil. En seco. El que caza no lee el asiento."""
from __future__ import annotations

from cirugias.radar.voz import Escudo, firmar, suma


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


def main() -> None:
    la_voz_es_el_lado()
    quinientos_no_recortan()
    al_voltear_se_calla()
    print("VOZ_REVISADA")


if __name__ == "__main__":
    main()
