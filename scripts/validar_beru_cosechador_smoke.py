"""Smoke — cosechador = alias ping-pong negociador."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core import beru_cosechador
from core import beru_negociador


def test_alias_oro():
    assert abs(beru_cosechador.llamado_tiempo_pct(0.008) - beru_negociador.oro_orilla_opuesta(0.008)) < 1e-9


def test_activar_trailing():
    oz, red = beru_cosechador.activar_primera_vez(-0.008, 0.001)
    assert red == 0.0
    assert abs(oz + 0.008) < 1e-9


def main() -> int:
    test_alias_oro()
    test_activar_trailing()
    print("validar_beru_cosechador_smoke: OK (alias ping-pong)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
