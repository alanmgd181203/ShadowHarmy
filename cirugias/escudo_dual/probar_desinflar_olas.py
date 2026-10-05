"""Engorde y desengorde del umbral, en seco."""
from cirugias.escudo_dual.desinflar import paso


def _ok(nombre: str, cond: bool) -> None:
    if not cond:
        raise SystemExit("FALLO " + nombre)
    print("OK  " + nombre)


def main() -> None:
    e: dict = {}
    e, _ = paso(e, 1000, 1, 1)
    e, _ = paso(e, 1100, 1, 1)
    e, f = paso(e, 990, 1, 1)  # -10% desde 1100
    _ok("primer desengorde", e["desengordes"] == 1 and e["cortado"] and f == 0.0)
    e, _ = paso(e, 990 * 1.10, 1.1, 1.1)  # +10% desde valle
    _ok("engorde tras corte", e["engordes"] == 1 and e["alza"] > 0)
    cresta = float(e["cresta"])
    e, _ = paso(e, cresta * 0.90, 1.0, 1.0)  # -10% desde cresta
    _ok("segundo desengorde", e["desengordes"] == 2 and e["engordes"] == 1)
    e, _ = paso(e, 1200, 1.2, 1.2)  # recupera el pico
    _ok("lleno otra vez", (not e["cortado"]) and e["desengordes"] == 2)
    print("OLAS_EN_VIGOR")


if __name__ == "__main__":
    main()
