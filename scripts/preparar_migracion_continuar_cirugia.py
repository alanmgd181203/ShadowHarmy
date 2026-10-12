#!/usr/bin/env python3
"""Prepara el ejército para despertar con --continuar (cirugías engorde/Iron).

NO despierta. NO abre manos. NO aplana. Solo mira sellos y deja un informe.

Qué deja listo:
- Confirma que el código de memoria/campo/Red sorda está en el disco
- Audita cada manos_piedra_informe: ¿puede CONTINUAR con memoria?
- Crea carpeta de campos Iron
- Escribe informe en data/beru/preparar_continuar_cirugia.json
"""
from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

RANGO = ROOT / "data" / "beru" / "rango"
CAMPOS = ROOT / "data" / "hiron" / "campos"
OUT = ROOT / "data" / "beru" / "preparar_continuar_cirugia.json"
CAMP_MANIFEST = ROOT / "data" / "beru" / "rango" / "vigilante_flota" / "campamentos.json"


def _vivo(inf: dict) -> dict:
    snap = inf.get("snapshot") if isinstance(inf.get("snapshot"), dict) else {}
    vivo = snap.get("vivo") if isinstance(snap.get("vivo"), dict) else {}
    return vivo if isinstance(vivo, dict) else {}


def _leer_informe(path: Path) -> dict | None:
    try:
        dato = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        return None
    return dato if isinstance(dato, dict) else None


def _codigo_ok() -> dict:
    br = (ROOT / "core" / "beru_rango.py").read_text(encoding="utf-8", errors="replace")
    cm = (ROOT / "cirugias" / "hiron" / "campo_masa.py").read_text(
        encoding="utf-8", errors="replace"
    )
    gen = (ROOT / "generales" / "beru_rango.py").read_text(encoding="utf-8", errors="replace")
    return {
        "memoria_engorde": "engorde_memoria_peldaños" in br and "limpiar_engorde_campana" in br,
        "red_short_sorda": "peldaños_holgura_red_short" in br,
        "campo_posicion": "posicion_usd" in cm and "SANGRE_PCT" in cm,
        "sello_guarda_memoria": "engorde_memoria_peldaños" in gen,
    }


def main() -> int:
    print("[PREP] migracion continuar · no despierta", flush=True)
    codigo = _codigo_ok()
    CAMPOS.mkdir(parents=True, exist_ok=True)

    santos = []
    if RANGO.is_dir():
        for d in sorted(RANGO.iterdir()):
            if not d.is_dir():
                continue
            act = d.name.upper()
            if act.startswith("_") or act in ("VIGILANTE_FLOTA",):
                continue
            inf_path = d / "manos_piedra_informe.json"
            if not inf_path.is_file():
                continue
            inf = _leer_informe(inf_path)
            if not inf:
                santos.append({"activo": act, "clase": "sello_roto", "continuar": False})
                continue
            vivo = _vivo(inf)
            estado = str(vivo.get("estado") or "").upper()
            cero = float(vivo.get("cero") or 0)
            oz = float(vivo.get("oz") or 0)
            red = float(vivo.get("red") or 0)
            mem = int(vivo.get("engorde_memoria_peldaños") or 0)
            cero_e = float(vivo.get("engorde_cero_oz") or 0)
            edad_h = None
            try:
                edad_h = round((time.time() - inf_path.stat().st_mtime) / 3600.0, 2)
            except OSError:
                pass

            if estado == "CAZANDO" and oz > 0 and cero > 0:
                clase = "continuar_caza"
                ok = True
            elif estado in ("ACECHANDO",) and cero > 0 and (red > 0 or oz > 0):
                clase = "continuar_acecho"
                ok = True
            elif cero > 0:
                clase = "continuar_flojo"
                ok = True
            else:
                clase = "semilla"
                ok = False

            memoria_lista = bool(cero_e > 0 or mem > 0)
            santos.append(
                {
                    "activo": act,
                    "clase": clase,
                    "continuar": ok,
                    "estado": estado or "—",
                    "memoria_engorde_en_sello": memoria_lista,
                    "engorde_cero_oz": cero_e,
                    "engorde_memoria_peldaños": mem,
                    "sello_edad_h": edad_h,
                }
            )

    n = len(santos)
    n_cont = sum(1 for s in santos if s.get("continuar"))
    n_mem = sum(1 for s in santos if s.get("memoria_engorde_en_sello"))
    n_sem = sum(1 for s in santos if s.get("clase") == "semilla")
    camp_ok = CAMP_MANIFEST.is_file()

    informe = {
        "hora_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "no_despierta": True,
        "codigo": codigo,
        "campos_iron_dir": str(CAMPOS),
        "campamentos_manifest": camp_ok,
        "resumen": {
            "sellos": n,
            "pueden_continuar": n_cont,
            "con_memoria_engorde": n_mem,
            "solo_semilla": n_sem,
        },
        "cuando_monarca_diga_go": (
            "arise_beru_rango_campamento.py --manos-go --continuar "
            "(NO --desde-cero). Así retoman sello + memoria."
        ),
        "nota_memoria": (
            "Sellos escritos ANTES de este código no traen engorde_memoria_*; "
            "pueden CONTINUAR mapa/saco, pero la racha de engorde arranca limpia "
            "hasta el primer Oz con código nuevo. Tras un latido con código nuevo, "
            "el sello ya guarda memoria."
        ),
        "santos": santos,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(informe, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"  codigo memoria={codigo['memoria_engorde']} red_sorda={codigo['red_short_sorda']} "
          f"campo={codigo['campo_posicion']} sello={codigo['sello_guarda_memoria']}", flush=True)
    print(f"  sellos={n} continuar={n_cont} memoria_en_sello={n_mem} semilla={n_sem}", flush=True)
    print(f"  campamentos.json={'OK' if camp_ok else 'FALTA'}", flush=True)
    print(f"  informe → {OUT}", flush=True)
    print("  GO futuro: campamento --continuar (prohibido --desde-cero en este pase)", flush=True)
    if not all(codigo.values()):
        print("[PREP] FALTA codigo de cirugia — haz pull regalo primero", flush=True)
        return 2
    print("[PREP] OK · ejercito preparado en papel · nada despertado", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
