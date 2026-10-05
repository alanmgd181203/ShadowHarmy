"""Papel del fantasma con velas reales. Sin manos. No despierta a nadie."""
from __future__ import annotations

import time

from cirugias.hiron.fantasma import Fantasma
from cirugias.hiron.probar_fantasma import pasos_de_vela
from cirugias.sala_por_color.contar_cuota import velas


def caminar(nombre: str, puerta: float, filas: list, desde: int) -> None:
    if len(filas) < desde + 5:
        print(nombre, "SIN_CAMINO", flush=True)
        return
    corte = float(filas[desde][4])
    fant = Fantasma(corte, puerta)
    pasos = 0
    for vela in filas[desde + 1 :]:
        for px in pasos_de_vela(vela[1], vela[2], vela[3], vela[4]):
            pasos += 1
            if fant.ver(px):
                dist = (fant.cero - corte) / corte * 100.0
                print(
                    f"{nombre} puerta {puerta*100:.1f} DESPIERTA {fant.lado} "
                    f"a {dist:+.2f}% del corte en {pasos} pasos",
                    flush=True,
                )
                return
    arriba = (fant.punta_alta - corte) / corte * 100.0
    abajo = (corte - fant.punta_baja) / corte * 100.0
    print(
        f"{nombre} puerta {puerta*100:.1f} SIGUE FANTASMA "
        f"arriba {arriba:.2f}% abajo {abajo:.2f}% pasos {pasos}",
        flush=True,
    )


def main() -> None:
    ahora = int(time.time() * 1000)
    desde_ms = ahora - 2 * 86400 * 1000
    casos = (("SUI", 0.012), ("JTO", 0.017), ("WIF", 0.012))
    for nombre, puerta in casos:
        filas = velas(nombre, desde_ms)
        if len(filas) < 30:
            print(nombre, "SIN_VELAS", len(filas), flush=True)
            continue
        mitad = len(filas) // 2
        print(f"--- {nombre} corte a la mitad del camino ---", flush=True)
        caminar(nombre, puerta, filas, mitad)
        pico = max(range(10, len(filas) - 5), key=lambda i: filas[i][2])
        print(f"--- {nombre} corte justo antes de la punta ---", flush=True)
        caminar(nombre, puerta, filas, pico - 1)


if __name__ == "__main__":
    main()
