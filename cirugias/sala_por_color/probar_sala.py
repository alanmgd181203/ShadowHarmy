"""Comprueba la sala sellada. No toca config ni al Beru que caza."""
from cirugias.sala_por_color.sala import (
    estiron_extra_pct,
    estiron_paso_pct,
    oz_pct,
    red_pct,
    sangre_pct,
    vacio_pct,
)


def _ok(nombre: str, cond: bool) -> None:
    if not cond:
        raise SystemExit("FALLO " + nombre)
    print("OK  " + nombre)


def main() -> None:
    _ok("verde vacio 1.2", abs(vacio_pct("verde") - 0.012) < 1e-12)
    _ok("verde sangre 1.2", abs(sangre_pct("verde") - 0.012) < 1e-12)
    _ok("verde red L 0.7", abs(red_pct("verde", "LONG") - 0.007) < 1e-12)
    _ok("verde red S 0.8", abs(red_pct("verde", "SHORT") - 0.008) < 1e-12)

    _ok("amarillo vacio 1.7", abs(vacio_pct("amarillo") - 0.017) < 1e-12)
    _ok("amarillo sangre 1.7", abs(sangre_pct("amarillo") - 0.017) < 1e-12)
    _ok("amarillo red L 1.0", abs(red_pct("amarillo", "LONG") - 0.010) < 1e-12)
    _ok("amarillo red S 1.1", abs(red_pct("amarillo", "SHORT") - 0.011) < 1e-12)

    _ok("rojo vacio 2.2", abs(vacio_pct("rojo") - 0.022) < 1e-12)
    _ok("rojo sangre 2.2", abs(sangre_pct("feria") - 0.022) < 1e-12)
    _ok("rojo red L 1.4", abs(red_pct("rojo", "LONG") - 0.014) < 1e-12)
    _ok("rojo red S 1.6", abs(red_pct("rojo", "SHORT") - 0.016) < 1e-12)

    for color in ("verde", "amarillo", "rojo"):
        _ok(color + " oz 0.2", abs(oz_pct(color) - 0.002) < 1e-12)

    _ok("desconocido es amarillo", abs(vacio_pct("morado") - 0.017) < 1e-12)

    _ok("verde metro 0.5", abs(estiron_paso_pct("verde") - 0.005) < 1e-12)
    _ok("amarillo metro 0.7", abs(estiron_paso_pct("amarillo") - 0.007) < 1e-12)
    _ok("rojo metro 1", abs(estiron_paso_pct("rojo") - 0.010) < 1e-12)
    # 2 % de camino: verde 4 saltos, amarillo 2, rojo 2. Salto 0,1. No es engorde.
    _ok("verde extra 0.4", abs(estiron_extra_pct("verde", 0.02) - 0.004) < 1e-12)
    _ok("amarillo extra 0.2", abs(estiron_extra_pct("amarillo", 0.02) - 0.002) < 1e-12)
    _ok("rojo extra 0.2", abs(estiron_extra_pct("rojo", 0.02) - 0.002) < 1e-12)
    _ok("rojo aun no a 1", abs(estiron_extra_pct("rojo", 0.009) - 0.0) < 1e-12)
    print("SALA_EN_VIGOR")


if __name__ == "__main__":
    main()
