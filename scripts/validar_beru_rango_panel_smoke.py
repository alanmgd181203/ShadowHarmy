#!/usr/bin/env python3
"""Smoke: foto panel Beru rango + fusión multi-Santo sin pisarse."""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core import beru_rango_panel
from core import beru_rango_paths


def _snap(activo: str, cero: float, manos: bool = False):
    vivo = {
        "uid": f"RANGO_{activo}_T",
        "estado": "ACECHANDO",
        "direccion": "",
        "cero": cero,
        "oz": 0.0,
        "red": cero * 1.008,
        "masa": 0.0,
        "sangre_lado": "",
        "cosechas": 0,
        "escalones_red": 0,
    }
    geom = {"sangre_pct": 0.012, "masa_usd": 5.0, "masa_red_usd": 5.0}
    return {"geometria": geom, "vivo": vivo, "manos": manos, "activo": activo}


def main() -> int:
    vivo = {
        "uid": "RANGO_HYPE_T",
        "estado": "ACECHANDO",
        "direccion": "",
        "cero": 100.0,
        "oz": 0.0,
        "red": 100.8,
        "masa": 0.0,
        "sangre_lado": "ABAJO",
        "cosechas": 1,
        "escalones_red": 1,
    }
    geom = {
        "sangre_pct": 0.012,
        "masa_usd": 5.0,
        "masa_red_usd": 5.0,
    }
    niv = beru_rango_panel.niveles_combate(vivo, geom)
    roles = {n["rol"] for n in niv}
    assert "wake" in roles
    assert "vacio" in roles
    assert "red" in roles
    # Sin sangre_adan: respaldo wake±1,2 (semilla / sello viejo).
    assert abs(next(n["precio"] for n in niv if n["id"] == "sangre_dn") - 98.8) < 1e-9

    # Tras Oz: sangre del peldaño, no del wake (LIT ~3% era tumor wake-fijo).
    vivo_oz = dict(vivo)
    vivo_oz["sangre"] = 100.7 * 0.988  # Oz ancla 100.7 · sangre ABAJO 1,2 %
    vivo_oz["sangre_adan"] = vivo_oz["sangre"]
    vivo_oz["oz_despliegue"] = 100.7
    niv_oz = beru_rango_panel.niveles_combate(vivo_oz, geom)
    sangre_panel = next(n["precio"] for n in niv_oz if n["id"] == "sangre_dn")
    assert abs(sangre_panel - 100.7 * 0.988) < 1e-9
    assert abs(sangre_panel - 98.8) > 0.5
    payload = beru_rango_panel.armar_payload(
        snapshot={"geometria": geom, "vivo": vivo, "manos": True, "activo": "HYPE"},
        last=99.5,
        activo="HYPE",
    )
    assert payload["activos"][0]["activo"] == "HYPE"
    assert "HYPE" in payload["details"]
    assert len(payload["details"]["HYPE"]["grafica"]["niveles"]) >= 3

    # Cazas (×) desde eventos OZ_COSECHA
    smoke_act = "_SMOKEPZ"
    p_smoke = beru_rango_paths.manos_eventos(smoke_act)
    p_smoke.parent.mkdir(parents=True, exist_ok=True)
    p_smoke.write_text(
        json.dumps(
            {
                "ts": 1700000001.0,
                "activo": smoke_act,
                "evento": "OZ_COSECHA",
                "detalle": {"oz": 12.3, "sangre": "ABAJO", "dir": "SHORT"},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    cazas_s = beru_rango_panel.cazas_desde_eventos(smoke_act)
    assert len(cazas_s) == 1 and cazas_s[0]["precio"] == 12.3
    assert cazas_s[0]["lado"] == "Sell"
    payload_c = beru_rango_panel.armar_payload(
        snapshot={
            "geometria": geom,
            "vivo": {**vivo, "uid": f"RANGO_{smoke_act}"},
            "manos": True,
            "activo": smoke_act,
        },
        last=12.5,
        activo=smoke_act,
    )
    assert payload_c["details"][smoke_act]["grafica"]["cazas"][0]["precio"] == 12.3
    assert payload_c["activos"][0]["n_cazas"] == 1
    p_smoke.unlink(missing_ok=True)
    try:
        p_smoke.parent.rmdir()
    except OSError:
        pass
    print("  cazas × desde OZ_COSECHA OK")

    # Posición real → raya en gráfica
    payload_pos = beru_rango_panel.armar_payload(
        snapshot={"geometria": geom, "vivo": vivo, "manos": True, "activo": "HYPE"},
        last=99.5,
        activo="HYPE",
        posicion=[{"lado": "SHORT", "qty": 0.2, "precio": 77.12, "masa_usd": 15.424}],
    )
    roles_pos = {n["rol"] for n in payload_pos["details"]["HYPE"]["grafica"]["niveles"]}
    assert "posicion_short" in roles_pos
    assert payload_pos["details"]["HYPE"]["posicion"][0]["lado"] == "SHORT"

    class _Tusk:
        pesos = {
            "HYPEUSDT_LINEAL": {
                "long": 0.0,
                "short": 0.34,
                "precio_medio_long": 0.0,
                "precio_medio_short": 76.5,
            }
        }

    pos = beru_rango_panel.posicion_desde_tusk(_Tusk(), "HYPE")
    assert len(pos) == 1 and pos[0]["lado"] == "SHORT"

    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "rango_vivo.json"
        beru_rango_panel.publicar(
            snapshot=_snap("HYPE", 70.0, manos=True),
            last=70.1,
            activo="HYPE",
            path=path,
            merge=True,
        )
        beru_rango_panel.publicar(
            snapshot=_snap("WLD", 0.4),
            last=0.41,
            activo="WLD",
            path=path,
            merge=True,
        )
        beru_rango_panel.publicar(
            snapshot=_snap("ONDO", 0.35),
            last=0.36,
            activo="ONDO",
            path=path,
            merge=True,
        )
        beru_rango_panel.publicar(
            snapshot=_snap("UNI", 4.0),
            last=4.01,
            activo="UNI",
            path=path,
            merge=True,
        )
        data = beru_rango_panel._leer_vivo(path)
        acts = {r["activo"] for r in data["activos"]}
        assert acts == {"HYPE", "WLD", "ONDO", "UNI"}, acts
        assert set(data["details"]) == acts
        assert data["n_santos"] == 4

        # Re-publicar HYPE no debe borrar a las otras
        beru_rango_panel.publicar(
            snapshot=_snap("HYPE", 71.0, manos=True),
            last=71.2,
            activo="HYPE",
            path=path,
            merge=True,
        )
        data2 = beru_rango_panel._leer_vivo(path)
        assert {r["activo"] for r in data2["activos"]} == acts

        beru_rango_panel.retirar_activo("ONDO", path=path)
        data3 = beru_rango_panel._leer_vivo(path)
        assert {r["activo"] for r in data3["activos"]} == {"HYPE", "WLD", "UNI"}

    print("OK beru_rango_panel smoke (merge multi-Santo)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
