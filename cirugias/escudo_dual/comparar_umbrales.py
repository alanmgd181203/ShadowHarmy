"""Tres modos del manto. No planta.

Calma, alerta y peligro cambian la relación, no el peldaño.
La noche real se relee con el precio de la reina.
El mechazo es una cuenta aparte: la bolsa engorda mientras el precio
va en su contra, y se mira cuánto absorbe el escudo.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))
os.environ.setdefault("IGRIS_ESCUDO_BTC_POLVO_USD", "250")

from core.igris_escudo_btc import neto_peldaño_atrasado
from cirugias.escudo_dual.comparar_histerico import (
    _cuenta,
    _grano,
    _muestras,
    _tasa,
    _velas,
)

INDICADOR = 1.6
ACTIVAR = 500.0
PELDANO = 250.0
CALMA = 6000.0
ALERTA = 12000.0
RUIDO = 2500.0


def relacion_de(neto: float, ley: str) -> float:
    """La relación que toca en ese tamaño de bolsa."""
    a = abs(float(neto or 0))
    if ley == "siempre":
        return INDICADOR
    if ley == "hueco" and a < RUIDO:
        return 0.0
    if ley == "hueco_uno" and a < RUIDO:
        return 0.0
    if a <= CALMA:
        media = INDICADOR * 0.5
        return 0.5 if ley == "hacia_uno" or ley == "hueco_uno" else media
    if a <= ALERTA:
        tres = INDICADOR * 0.75
        return 0.75 if ley == "hacia_uno" or ley == "hueco_uno" else tres
    if ley in ("literal", "hueco"):
        return 1.0
    if ley in ("hacia_uno", "hueco_uno"):
        return 1.0
    return INDICADOR


def _metal(muestras: list[dict], ley: str) -> list[tuple[float, float]]:
    armado = False
    lado = ""
    asentado = None
    out = []
    for fila in muestras:
        asiento, armado, lado = neto_peldaño_atrasado(
            fila["cruzado"],
            peldaño=PELDANO,
            activar=ACTIVAR,
            armado=armado,
            lado_armado=lado,
            asentado=asentado,
        )
        asentado = asiento if armado else None
        rel = relacion_de(fila["cruzado"], ley)
        out.append((fila["ts"], _grano(asiento * rel)))
    return out


def _noche(muestras, velas, tasa) -> None:
    cruces = [abs(f["cruzado"]) for f in muestras]
    pico = max(cruces) if cruces else 0
    n = len(cruces) or 1
    print(
        "PICO", round(pico),
        "sobre2500", round(100 * sum(1 for c in cruces if c >= RUIDO) / n),
        "sobre5000", round(100 * sum(1 for c in cruces if c > CALMA) / n),
        "sobre12000", round(100 * sum(1 for c in cruces if c > ALERTA) / n),
    )
    leyes = ("siempre", "literal", "hacia_uno", "fraccion", "hueco", "hueco_uno")
    for ley in leyes:
        hecho = _cuenta(_metal(muestras, ley), velas, tasa)
        print(
            ley,
            "peso", round(hecho["peso"]),
            "final", round(hecho["final"]),
            "precio", round(hecho["pnl_usd"], 1),
            "comision", round(hecho["fee_usd"], 1),
            "neto", round(hecho["neto_usd"], 1),
        )


def _subir(n_final: float, ley: str) -> list[float]:
    """La bolsa crece de cero al final, de a cien. Devuelve el metal de cada tramo."""
    armado = False
    lado = ""
    asentado = None
    metales = []
    n = 0.0
    while n < n_final - 1e-9:
        n = min(n_final, n + 100.0)
        asiento, armado, lado = neto_peldaño_atrasado(
            n,
            peldaño=PELDANO,
            activar=ACTIVAR,
            armado=armado,
            lado_armado=lado,
            asentado=asentado,
        )
        asentado = asiento if armado else None
        metales.append(_grano(asiento * relacion_de(n, ley)))
    return metales


def _mechazo(n_final: float, d_eth: float, ley: str) -> dict:
    """El precio de las alt se mueve 1.6 veces lo de la reina, en contra de la bolsa.

    La bolsa engorda parejo durante la vela. Lo ya sentado al final,
    si la vela cayera de golpe, va aparte.
    """
    metales = _subir(n_final, ley)
    pasos = len(metales) or 1
    d_alt = d_eth * INDICADOR
    trozo = d_alt / pasos
    trozo_reina = d_eth / pasos
    bolsa = 0.0
    vault = 0.0
    escudo = 0.0
    anterior = 0.0
    giros = 0.0
    for metal in metales:
        bolsa = min(n_final, bolsa + 100.0)
        vault += bolsa * trozo
        escudo += metal * trozo_reina
        giros += abs(metal - anterior)
        anterior = metal
    golpe_vault = n_final * d_alt
    seat = metales[-1] if metales else 0.0
    golpe_escudo = seat * d_eth
    fee = 0.0005 * giros
    return {
        "vault": vault,
        "escudo": escudo,
        "nuestro": vault - escudo,
        "fee": fee,
        "golpe_vault": golpe_vault,
        "golpe_escudo": golpe_escudo,
        "golpe_nuestro": golpe_vault - golpe_escudo,
        "final": seat,
    }


def _mechazos() -> None:
    leyes = ("siempre", "literal", "hacia_uno", "fraccion", "hueco", "hueco_uno")
    for n_final, d_eth, nombre in (
        (8000, 0.03, "ocho_mil_tres"),
        (15000, 0.05, "quince_mil_cinco"),
        (20000, 0.08, "veinte_mil_ocho"),
    ):
        print("MECHAZO", nombre)
        for ley in leyes:
            h = _mechazo(n_final, d_eth, ley)
            print(
                ley,
                "crece_bolsa", round(h["vault"]),
                "absorbe", round(h["escudo"]),
                "queda", round(h["nuestro"]),
                "comision", round(h["fee"], 1),
                "ya_gorda_bolsa", round(h["golpe_vault"]),
                "ya_gorda_absorbe", round(h["golpe_escudo"]),
                "ya_gorda_queda", round(h["golpe_nuestro"]),
                "metal", round(h["final"]),
            )


def main() -> None:
    muestras = _muestras()
    desde = int(muestras[0]["ts"] * 1000)
    hasta = int(muestras[-1]["ts"] * 1000)
    velas = sorted(_velas(desde, hasta).items())
    print("VELAS", len(velas), "TASA", _tasa())
    _noche(muestras, velas, _tasa())
    _mechazos()


if __name__ == "__main__":
    main()
