"""El libro del fantasma, en seco. No toca la casa."""
from cirugias.hiron import fantasma_vivo as vivo


def _ok(cond: bool, nombre: str) -> None:
    if not cond:
        raise SystemExit("TUMOR " + nombre)
    print("OK  " + nombre)


def main() -> None:
    ruta = vivo.RAIZ / "data" / "beru" / "papel" / "_fantasma_ensayo.json"
    vivo.RUTA = ruta
    vivo.sellar_corte("JTO", 100)
    quieto = vivo.paso("JTO", 100.4, 0.012)
    _ok(quieto["estado"] == "sigue", "el estornudo sigue")
    vivo.paso("JTO", 110, 0.012)
    nacio = vivo.paso("JTO", 110 * (1 - 0.012), 0.012)
    _ok(nacio["estado"] == "nacio" and nacio["lado"] == "LONG", "el respiro nace largo")
    _ok(abs(float(nacio["cero"]) - 110 * (1 - 0.012)) < 1e-9, "el cero es el respiro")
    vivo.olvidar("JTO")
    _ok(vivo.paso("JTO", 100, 0.012)["estado"] == "libre", "olvidado, vuelve a cazar")
    vivo.sellar_corte("WIF", 100)
    vivo.paso("WIF", 110, 0.012)
    _ok(vivo.paso("WIF", 90, 0.012)["estado"] == "sigue", "el desplome no nace")
    if ruta.exists():
        ruta.unlink()
    print("FANTASMA_VIVO_EN_SECO")


if __name__ == "__main__":
    main()
