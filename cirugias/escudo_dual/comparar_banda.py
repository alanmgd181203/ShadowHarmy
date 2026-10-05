"""La banda del hueco contra el manto de ahora. No planta."""
from __future__ import annotations

import os
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))
os.environ.setdefault("IGRIS_ESCUDO_BTC_POLVO_USD", "250")

from core.igris_escudo_btc import neto_peldaño_atrasado
from cirugias.escudo_dual.comparar_histerico import _cuenta, _grano, _muestras, _tasa, _velas

ABRE = 5000.0
CIERRA = 2500.0
MEDIA = 0.8
LLENA = 1.6


def _lleno(muestras: list[dict]) -> list[tuple[float, float]]:
    armado = False
    lado = ""
    asentado = None
    out = []
    for fila in muestras:
        asiento, armado, lado = neto_peldaño_atrasado(
            fila["cruzado"],
            peldaño=250.0,
            activar=500.0,
            armado=armado,
            lado_armado=lado,
            asentado=asentado,
        )
        asentado = asiento if armado else None
        out.append((fila["ts"], _grano(asiento * LLENA)))
    return out


def _banda(muestras: list[dict]) -> list[tuple[float, float]]:
    prendido = False
    armado = False
    lado = ""
    asentado = None
    out = []
    for fila in muestras:
        n = float(fila["cruzado"])
        if not prendido:
            if abs(n) >= ABRE:
                prendido = True
                armado = False
                lado = ""
                asentado = None
            else:
                out.append((fila["ts"], 0.0))
                continue
        asiento, armado, lado = neto_peldaño_atrasado(
            n,
            peldaño=250.0,
            activar=500.0,
            armado=armado,
            lado_armado=lado,
            asentado=asentado,
        )
        if (not armado) or abs(n) <= CIERRA:
            prendido = False
            armado = False
            lado = ""
            asentado = None
            out.append((fila["ts"], 0.0))
            continue
        asentado = asiento
        out.append((fila["ts"], _grano(asiento * MEDIA)))
    return out


def _linea(nombre: str, hecho: dict) -> None:
    print(
        nombre,
        "peso", round(hecho["peso"]),
        "veces", round(hecho["veces"]),
        "precio", round(hecho["pnl_usd"], 1),
        "comision", round(hecho["fee_usd"], 1),
        "neto", round(hecho["neto_usd"], 1),
    )


def main() -> None:
    muestras = _muestras()
    velas = sorted(_velas(int(muestras[0]["ts"] * 1000), int(muestras[-1]["ts"] * 1000)).items())
    tasa = _tasa()
    print("VENTANA", muestras[0]["hora"], "->", muestras[-1]["hora"], "TASA", tasa)
    _linea("ahora", _cuenta(_lleno(muestras), velas, tasa))
    _linea("banda", _cuenta(_banda(muestras), velas, tasa))
    vivo = [(f["ts"], _grano(f["reina"])) for f in muestras if f["reina"] is not None]
    _linea("reina", _cuenta(vivo, velas, tasa))


if __name__ == "__main__":
    main()
