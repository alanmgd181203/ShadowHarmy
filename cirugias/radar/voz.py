"""La voz de la cabeza. El escudo vivo no lee esto.

Cada Beru dice, en todo momento, los dólares que ya tiene en la
cabeza. No espera a firmar la orden ni a que la Oz se toque.
Igris suma. El escudo solo se mueve de mil en mil. Quinientos de
menos se ven, y no recortan todavía.
"""
from __future__ import annotations

import math

SALTO = 1000.0
POLVO = 250.0


def firmar(lado: str, dolares: float) -> float:
    """Una voz. Positiva es corto. Negativa es largo."""
    masa = max(0.0, float(dolares or 0))
    cual = "SHORT" if str(lado or "").upper() == "SHORT" else "LONG"
    if masa <= 0:
        return 0.0
    if str(lado or "").upper() not in ("LONG", "SHORT"):
        return 0.0
    return masa if cual == "SHORT" else -masa


def suma(voces: list[float]) -> float:
    """La colmena. El que calla aporta cero."""
    return float(sum(float(v or 0) for v in voces))


def oir_boca(saltar: set[str] | None = None) -> float | None:
    """Suma firmada de las bocas vivas. None si no hay ninguna hoja.

    Positiva es más corto. Negativa es más largo. El que calla aporta cero.
    ``saltar`` son casas de otro manto: no se oyen aquí.
    """
    import json
    from core.beru_rango_paths import RANGO_DIR

    if not RANGO_DIR.is_dir():
        return None
    fuera = {str(x or "").strip().upper() for x in (saltar or set()) if str(x or "").strip()}
    vistos = 0
    total = 0.0
    for inf in RANGO_DIR.glob("*/manos_piedra_informe.json"):
        nombre = inf.parent.name.upper()
        if nombre == "BTC" or nombre in fuera:
            continue
        try:
            data = json.loads(inf.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            continue
        vivo = data.get("vivo")
        if not isinstance(vivo, dict):
            vivo = (data.get("snapshot") or {}).get("vivo")
        if not isinstance(vivo, dict) or "voz_intencion" not in vivo:
            continue
        vistos += 1
        total += float(vivo.get("voz_intencion") or 0)
    if vistos == 0:
        return None
    return float(total)


class Escudo:
    """El asiento del escudo, leído de la intención. No manda orden."""

    def __init__(self) -> None:
        self.asentado = 0.0
        self.armado = False
        self.lado = ""

    def ver(self, intencion: float) -> float:
        """El asiento después de oír la suma. Dentro del salto, no se mueve."""
        firmado, armado, lado = _peldaño(
            intencion,
            armado=self.armado,
            lado_armado=self.lado,
            asentado=self.asentado if self.armado else None,
        )
        self.asentado = firmado
        self.armado = armado
        self.lado = lado
        return firmado


def _peldaño(
    neto: float,
    *,
    armado: bool,
    lado_armado: str,
    asentado: float | None,
) -> tuple[float, bool, str]:
    """Igual que el salto vivo de mil. Aquí el número es la intención."""
    p = SALTO
    n = float(neto or 0)
    if abs(n) <= POLVO + 1e-9 or abs(n) < 1e-12:
        return 0.0, False, ""
    lado = "SHORT" if n > 0 else "LONG"
    if armado and lado_armado and lado != lado_armado:
        return 0.0, False, ""
    stepped = math.floor(abs(n) / p + 1e-15) * p

    def _firmado(abs_step: float) -> tuple[float, bool, str]:
        if abs_step + 1e-12 < SALTO:
            return 0.0, False, ""
        signed = abs_step if n > 0 else -abs_step
        return float(signed), True, lado

    if not armado or asentado is None:
        return _firmado(stepped)
    S = abs(float(asentado))
    if S >= 1e-12:
        S = math.floor(S / p + 1e-15) * p
    if S < 1e-12:
        return _firmado(stepped)
    lo = S - p
    hi = S + p
    if (lo + 1e-6) < abs(n) < (hi - 1e-6):
        return _firmado(S)
    return _firmado(stepped)
