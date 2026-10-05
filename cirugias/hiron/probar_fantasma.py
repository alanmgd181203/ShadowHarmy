"""Fantasma en seco. Si el estornudo lo despierta, o el cero no es el respiro, es tumor."""
from cirugias.hiron.fantasma import Fantasma

PUERTA = 0.012


def _ok(cond: bool, nombre: str) -> None:
    if not cond:
        raise SystemExit("TUMOR " + nombre)
    print("OK  " + nombre)


def estornudo_no_despierta() -> None:
    """Medio por ciento arriba y abajo del corte no es explosión."""
    f = Fantasma(100, PUERTA)
    for px in (100.4, 99.7, 100.2, 100.5, 99.6):
        f.ver(px)
    _ok(not f.despierto(), "estornudo sigue fantasma")
    _ok(f.cero == 0.0, "estornudo sin cero")


def explosion_arriba_espera_el_respiro() -> None:
    """De 100 a 110. Todavía no hay retroceso: no compra."""
    f = Fantasma(100, PUERTA)
    f.ver(105)
    f.ver(110)
    _ok(not f.despierto(), "cohete sin respiro")
    nacio = f.ver(110 * (1.0 - PUERTA))
    _ok(nacio and f.lado == "LONG", "respiro compra largo")
    _ok(abs(f.cero - 110 * (1.0 - PUERTA)) < 1e-9, "el cero es el respiro")
    _ok(f.ver(100) is False and abs(f.cero - 110 * (1.0 - PUERTA)) < 1e-9, "el cero no se mueve")


def colapso_espera_el_rebote() -> None:
    """De 100 a 90. El rebote de una puerta vende corto, y ese precio es el cero."""
    f = Fantasma(100, PUERTA)
    f.ver(95)
    f.ver(90)
    _ok(not f.despierto(), "caida sin rebote")
    cero = 90 * (1.0 + PUERTA)
    _ok(f.ver(cero) and f.lado == "SHORT", "rebote vende corto")
    _ok(abs(f.cero - cero) < 1e-9, "el cero es el rebote")


def un_salto_no_lleva_el_cero_al_fondo() -> None:
    """Si el retroceso salta de 110 a 100, el cero queda en la puerta, no en el fondo."""
    f = Fantasma(100, PUERTA)
    f.ver(110)
    f.ver(100)
    puerta = 110 * (1.0 - PUERTA)
    _ok(f.lado == "LONG" and abs(f.cero - puerta) < 1e-9, "el salto deja el cero en la puerta")


def desplome_de_un_golpe_no_compra() -> None:
    """De 110 salta a 90. Eso es el desplome, no un largo. El rebote vende corto."""
    f = Fantasma(100, PUERTA)
    f.ver(110)
    _ok(f.ver(90) is False and not f.despierto(), "el desplome no compra largo")
    cero = 90 * (1.0 + PUERTA)
    _ok(f.ver(cero) and f.lado == "SHORT" and abs(f.cero - cero) < 1e-9, "el rebote del desplome vende corto")


def puerta_mas_lejos_pide_mas() -> None:
    """La sala del medio pide 1,7. Un 1,5 no es explosión todavía."""
    f = Fantasma(100, 0.017)
    f.ver(101.5)
    f.ver(101.5 * (1.0 - 0.012))
    _ok(not f.despierto(), "1,5 no despierta la puerta del medio")
    f.ver(101.7)
    _ok(f.ver(101.7 * (1.0 - 0.017)) and f.lado == "LONG", "1,7 si despierta largo")


def una_sola_punta_no_basta() -> None:
    """La punta exacta de una puerta aún no es el despertar. Falta el respiro."""
    f = Fantasma(100, PUERTA)
    _ok(f.ver(100 * (1.0 + PUERTA)) is False, "la punta no es el cero")
    _ok(not f.despierto(), "en la punta sigue fantasma")


def pasos_de_vela(o: float, h: float, l: float, c: float) -> list[float]:
    """El mismo orden con el que el cazador oye un vaso, sin manos."""
    crudo = [o, l, h, c] if c >= o else [o, h, l, c]
    out: list[float] = []
    for px in crudo:
        if px > 0 and (not out or abs(out[-1] - px) > 1e-12):
            out.append(px)
    return out


def vaso_no_despierte_estornudo() -> None:
    f = Fantasma(100, PUERTA)
    for px in pasos_de_vela(100, 100.5, 99.6, 100.1):
        f.ver(px)
    _ok(not f.despierto(), "el vaso del estornudo no despierta")


def main() -> None:
    estornudo_no_despierta()
    explosion_arriba_espera_el_respiro()
    colapso_espera_el_rebote()
    un_salto_no_lleva_el_cero_al_fondo()
    desplome_de_un_golpe_no_compra()
    puerta_mas_lejos_pide_mas()
    vaso_no_despierte_estornudo()
    una_sola_punta_no_basta()
    print("FANTASMA_EN_SECO")


if __name__ == "__main__":
    main()
