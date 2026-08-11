#!/usr/bin/env python3
"""Smoke frío — peaje IM pierna a pierna vs ranking/oxígeno (sin red, sin manos).

Fórmula doctrinal (muro 95% / colchón Tusk):
  - Cada paso del pase tiene delta_usd = capital peaje (IM / (1 - colchón)).
  - acum_usd(N) = suma de delta 1…N = equity mínima de corona al sellar N.
  - IM_ofensivo(N) = suma, por Santo activo en 1…N, del IM del grado más alto
    alcanzado (margen_piernas_para_friccion = notional/lev_inv + notional/lev_lin).
  - Invariante: IM_ofensivo(N) ≤ acum_usd(N) × (1 - colchón)  (+ holgura de redondeo).
    Equivale a: con equity E = acum(N), el muro 95% cubre el margen ofensivo del ranking;
    la bóveda MNT NO suma al presupuesto ofensivo.

Asserts vivos: Brujo acum 1673 · Chamán 3735 alineados plan_crecimiento.
Peaje LINK/AVAX/OP: IM = notional/lev_i + notional/lev_l (sin promedio).

Uso:
  python scripts/validar_pase_im_ranking_smoke.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core import beru_capital as bc
from core import plan_crecimiento as pc
from core.pase_director import PASE_PASOS, potencia_n


_ORDER = {"SOLDADO": 1, "CAPITAN": 2, "GENERAL": 3, "MARISCAL": 4}


def _grados_hasta(n: int) -> dict[str, str]:
    out: dict[str, str] = {}
    for p in PASE_PASOS:
        if int(p["n"]) > n:
            break
        act = str(p["activo"]).upper()
        g = str(p["grado"]).upper()
        if act not in out or _ORDER.get(g, 0) > _ORDER.get(out[act], 0):
            out[act] = g
    return out


def im_ofensivo_hasta(n: int) -> float:
    """Suma IM (inv+lin) del grado máximo por Santo en pasos 1…n. MNT bóveda se excluye del assert ofensivo?"""
    # Doctrina: bóveda MNT short cubre colchón — su peaje en pase SÍ está en acum (pasos MNT),
    # pero el smoke de muro mide todos los peajes del ranking ofensivo incluyendo MNT manto
    # del pase (no la bóveda spot). Aquí usamos el IM del grado del pase.
    total = 0.0
    for act, grado in _grados_hasta(n).items():
        fric = bc.friccion_grado_pct(grado)
        total += float(bc.margen_piernas_para_friccion(act, fric)["im_total_usd"])
    return total


def test_techos_brujo_chaman():
    brujo = next(p for p in PASE_PASOS if int(p["n"]) == 27)
    chaman = next(p for p in PASE_PASOS if int(p["n"]) == 52)
    assert abs(float(brujo["acum_usd"]) - 1673.0) < 1e-9, brujo["acum_usd"]
    assert abs(float(chaman["acum_usd"]) - 3735.0) < 1e-9, chaman["acum_usd"]
    assert abs(float(pc.BRUJO_TECHO_USD) - 1673.0) < 1e-9
    assert abs(float(pc.CHAMAN_TECHO_USD) - 3735.0) < 1e-9
    assert abs(float(pc.ASPIRANTE_TECHO_USD) - 143.0) < 1e-9
    assert abs(float(pc.APRENDIZ_TECHO_USD) - 478.0) < 1e-9
    print("  techos Brujo1673 / Chamán3735 / plan_crecimiento OK")


def test_potencia_corona():
    assert potencia_n(1673.0) == 27
    assert potencia_n(1672.0) == 26
    assert potencia_n(3735.0) == 52
    assert potencia_n(1500.0) == 24
    print("  potencia_n(1673)=27 · (1500)=24 OK")


def test_muro_oxigeno_ranking():
    """IM ofensivo 1…N ≤ acum(N) × (1 - colchón) (+ holgura redondeo capital)."""
    colchon = bc.colchon_tusk_pct()
    assert abs(colchon - 0.05) < 1e-9
    holgura = 25.0  # redondeos ceil/round por paso + G_min vivo
    for n in (5, 13, 27, 52):
        acum = float(next(p for p in PASE_PASOS if int(p["n"]) == n)["acum_usd"])
        im = im_ofensivo_hasta(n)
        techo_im = acum * (1.0 - colchon) + holgura
        assert im <= techo_im + 1e-6, (
            f"paso {n}: IM_ofensivo={im:.2f} > acum*{1-colchon}+h={techo_im:.2f} (acum={acum})"
        )
        # Equidad: potencia con E=acum alcanza exactamente n
        assert potencia_n(acum) == n
        print(f"  muro N={n}: IM={im:.1f} <= acum*0.95+h ({techo_im:.1f}) acum={acum:.0f} OK")


def test_peaje_piernas_link_avax_op():
    """Assert IM = notional/lev_i + notional/lev_l (tabla config)."""
    for asset in ("LINK", "AVAX", "OP"):
        fric = bc.friccion_grado_pct("MARISCAL")
        det = bc.margen_piernas_para_friccion(asset, fric)
        pierna = float(det["notional_pierna_usd"])
        lev_i = float(det["lev_inverse"])
        lev_l = float(det["lev_linear"])
        expect = pierna / lev_i + pierna / lev_l
        assert abs(float(det["im_total_usd"]) - expect) < 1e-6
        # No promedio: 2*pierna/avg ≠ IM (salvo lev_i == lev_l)
        avg = (lev_i + lev_l) / 2.0
        mentira = (2.0 * pierna) / avg
        if abs(lev_i - lev_l) > 1e-9:
            assert abs(mentira - expect) > 1.0, (asset, mentira, expect)
        print(
            f"  {asset} Mariscal IM={expect:.1f} "
            f"(={pierna:.0f}/{lev_i:.0f}+{pierna:.0f}/{lev_l:.0f}) OK"
        )


def test_overshoot_candado_frio():
    """have > need → restante 0 + OVERSHOOT_RANKING (sin órdenes)."""
    from core import pase_director as pd

    class FakeTusk:
        def __init__(self, have: float):
            self._have = have

        def exposición_por_base(self, base: str):  # noqa: N802 — si existe
            return {}

    # Monkey vía notional_manto_usd: stub tusk that pd knows
    # Usamos patch local de notional_manto_usd
    act = "ETH"
    eq = 2000.0  # potencia abre trabajo
    need = pd.need_notional_grado_usd(act, "SOLDADO")

    class T:
        pass

    t = T()

    real = pd.notional_manto_usd
    try:
        pd.notional_manto_usd = lambda _tusk, a, **kw: need * 1.5 if a == act else 0.0  # type: ignore
        meta = pd.meta_engorde_usd(eq, act, tusk=t, marcha_id="asalto", pasos_logrados=[])
        assert meta.get("ok") is True
        assert float(meta["restante_usd"]) == 0.0  # 0.0 is falsy — never use `or`
        assert meta.get("overshoot_ranking") is True
        assert meta.get("telemetria") == "OVERSHOOT_RANKING"
        assert meta.get("motivo") == "OVERSHOOT_RANKING"
        print("  candado OVERSHOOT_RANKING restante=0 OK")
    finally:
        pd.notional_manto_usd = real  # type: ignore


def main() -> int:
    print("[SMOKE] pase IM ranking / oxígeno (frío)")
    test_techos_brujo_chaman()
    test_potencia_corona()
    test_muro_oxigeno_ranking()
    test_peaje_piernas_link_avax_op()
    test_overshoot_candado_frio()
    print("OK validar_pase_im_ranking_smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
