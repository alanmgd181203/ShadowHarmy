"""Puerta por gordura en seco."""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

from cirugias.sala_por_color.gordura import (
    BAJA_AMARILLO,
    BAJA_ROJO,
    SUBE_AMARILLO,
    SUBE_ROJO,
    sala_por_neto,
    unir,
)


def _ok(nombre: str, cond: bool) -> None:
    if not cond:
        raise SystemExit("FALLO " + nombre)
    print("OK  " + nombre)


def main() -> None:
    _ok("verde quieto", sala_por_neto("verde", 100) == "verde")
    _ok("verde a amarillo", sala_por_neto("verde", SUBE_AMARILLO + 1) == "amarillo")
    _ok("verde a rojo de un salto", sala_por_neto("verde", SUBE_ROJO + 1) == "rojo")
    _ok("amarillo aguanta 400", sala_por_neto("amarillo", 400) == "amarillo")
    _ok("amarillo baja a 300", sala_por_neto("amarillo", BAJA_AMARILLO) == "verde")
    _ok("rojo aguanta 900", sala_por_neto("rojo", 900) == "rojo")
    _ok("rojo baja a 800", sala_por_neto("rojo", BAJA_ROJO) == "amarillo")
    _ok("unir reloj rojo gana", unir("rojo", "verde") == "rojo")
    _ok("unir gordura sube", unir("verde", "amarillo") == "amarillo")
    _ok("unir empate", unir("amarillo", "amarillo") == "amarillo")

    with tempfile.TemporaryDirectory() as tmp:
        ruta = Path(tmp) / "gordura.json"
        os.environ["BERU_SALA_GORDURA_PATH"] = str(ruta)
        from cirugias.sala_por_color import gordura as g

        g._MEM["mtime"] = None
        g._MEM["filas"] = None
        # Sin filtros de lote: precio 0 deja pasar.
        a = g.actualizar("NIGHT", 600, precio=0.0, frente="")
        _ok("memoria sube amarillo", a == "amarillo")
        b = g.actualizar("NIGHT", 1200, precio=0.0, frente="")
        _ok("memoria sube rojo", b == "rojo")
        c = g.actualizar("NIGHT", 850, precio=0.0, frente="")
        _ok("memoria aguanta rojo", c == "rojo")
        d = g.actualizar("NIGHT", 800, precio=0.0, frente="")
        _ok("memoria baja amarillo", d == "amarillo")
        e = g.actualizar("NIGHT", 300, precio=0.0, frente="")
        _ok("memoria baja verde", e == "verde")
        _ok("unir no quita reloj", g.unir("rojo", "verde") == "rojo")
    print("GORDURA_EN_VIGOR")


if __name__ == "__main__":
    main()
