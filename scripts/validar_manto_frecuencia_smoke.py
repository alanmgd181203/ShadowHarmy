#!/usr/bin/env python3
"""Smoke frecuencia manto — 4 umbrales × plazos (anual 10%) + ETA + tau."""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import core.config as config
from core import manto_frecuencia as mf
from core import igris_despliegue as ides
from core.kaiser_samples import SAMPLES_DIR, append_sample


def _sembrar(base: str, n: int = 60, abs_pct: float = 0.12) -> None:
    ahora = time.time()
    for i in range(n):
        append_sample(
            base,
            mf.EDGE_MANTO,
            signed_pct=abs_pct if i % 2 == 0 else -abs_pct,
            abs_pct=abs_pct,
            ts=ahora - i * 3600,
            ref_tipo="smoke",
        )


def test_pesos():
    p = mf._pesos()
    assert abs(p["largo"] - 0.10) < 1e-9, p
    assert abs(p["corto"] + p["mediano"] + p["largo"] - 1.0) < 1e-6, p
    print("  pesos 50/40/10 OK", p)


def test_cuatro_umbrales():
    base = "SMKFREQ"
    # Limpiar semilla previa
    path = SAMPLES_DIR / f"{base}_{mf.EDGE_MANTO}.jsonl"
    if path.exists():
        path.unlink()
    # Spreads ~0.12% — por encima de tablas y probablemente medio_fees si fees~0.11
    _sembrar(base, n=80, abs_pct=0.12)
    freq = mf.frecuencia_activo(base)
    assert freq["ok"] is True, freq
    c = freq["contadores"]
    for k in ("fees", "medio_fees", "tablas", "morado"):
        assert k in c, c
        assert "pct_blend" in c[k], c[k]
    assert freq["score_paciencia"] is not None
    print(
        "  4 umbrales OK",
        {k: c[k].get("pct_blend") for k in ("fees", "medio_fees", "tablas", "morado")},
        "modo=", freq.get("modo_sugerido"),
    )
    if path.exists():
        path.unlink()


def test_tau_invertido():
    # Sin muestras → fallback estático o kaiser
    info = ides.tau_paciencia_horas(
        {"plazos": {"mediano": {"metricas": {"n_muestras": 100, "pct_tiempo_sobre_umbral": 0.9}, "etiquetas": []}}},
        base="NOSAMPLEXYZ",
    )
    assert info["tau_h"] > 1.0, info
    print("  tau fallback/perfil OK", info.get("modo"), info["tau_h"])


def test_eta():
    base = "SMKETA"
    path = SAMPLES_DIR / f"{base}_{mf.EDGE_MANTO}.jsonl"
    if path.exists():
        path.unlink()
    _sembrar(base, n=100, abs_pct=0.2)
    eta = mf.eta_despliegue_horas(base, 100.0, marcha_id="marcha_forzada", mordida_usd=5.0)
    assert eta["ok"] is True, eta
    assert eta["eta_h"] is not None and eta["eta_h"] > 0, eta
    assert eta["eta_h_opt"] <= eta["eta_h"] <= eta["eta_h_pes"], eta
    print("  ETA forzada OK", eta["eta_h"], "h · bocados", eta["bocados_est"])
    if path.exists():
        path.unlink()


def test_cero_estructural_filtra_gap_eterno():
    """Si el spread vive pegado al cero, NO cuenta como oportunidad (anti-Asalto falso)."""
    base = "SMKCERO"
    ahora = time.time()
    for edge in ("perp_vs_index", "inverse_vs_index", mf.EDGE_MANTO):
        p = SAMPLES_DIR / f"{base}_{edge}.jsonl"
        if p.exists():
            p.unlink()
    # Cero manto = lineal(+0.05) − inverso(−0.05) = +0.10
    for i in range(40):
        ts = ahora - i * 3600
        append_sample(base, "perp_vs_index", signed_pct=0.05, ts=ts)
        append_sample(base, "inverse_vs_index", signed_pct=-0.05, ts=ts)
        # Spread eterno ~0.10 — igual al cero → exceso ~0
        append_sample(base, mf.EDGE_MANTO, signed_pct=0.10, abs_pct=0.10, ts=ts)

    from core import kaiser_sesgo_index as ksi

    cm = ksi.cero_estructural_manto(base)
    assert cm.get("ok") and abs(float(cm["cero_pct"]) - 0.10) < 0.02, cm
    samples = __import__("core.kaiser_samples", fromlist=["load_samples"]).load_samples(
        base, mf.EDGE_MANTO, since_ts=ahora - 3 * 86400
    )
    met_legacy_style = sum(1 for s in samples if float(s.get("abs_pct") or 0) >= 0.05)
    met = mf._pct_sobre(samples, 0.05, cero_pct=cm["cero_pct"])
    assert met_legacy_style == len(samples), "legado vería casi todo como opp"
    assert met["n_sobre"] < len(samples) * 0.2, met
    print(
        "  cero filtra gap eterno OK",
        f"legado_sobre={met_legacy_style}/{len(samples)}",
        f"con_cero={met['n_sobre']}/{met['n']}",
        f"cero={cm['cero_pct']}",
    )
    for edge in ("perp_vs_index", "inverse_vs_index", mf.EDGE_MANTO):
        p = SAMPLES_DIR / f"{base}_{edge}.jsonl"
        if p.exists():
            p.unlink()


def test_snapshot():
    snap = mf.snapshot_ranking(bases=["BTC", "ETH"], equity_usd=200.0)
    assert "ranking" in snap
    assert snap["pesos_plazos"]["largo"] == 0.10 or abs(snap["pesos_plazos"]["largo"] - 0.10) < 1e-9
    print("  snapshot ranking OK n=", snap.get("n_activos"))


def main() -> int:
    print("[SMOKE] manto_frecuencia")
    assert getattr(config, "MANTO_FREQ_ACTIVA", True)
    test_pesos()
    test_cuatro_umbrales()
    test_tau_invertido()
    test_eta()
    test_cero_estructural_filtra_gap_eterno()
    test_snapshot()
    print("[OK] manto_frecuencia smoke completo")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
