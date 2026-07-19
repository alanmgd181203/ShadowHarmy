"""
Validación global del checklist — genera data/validacion_checklist.json

Uso:
  python scripts/validar_checklist.py           # fases 0,2,3,4
  python scripts/validar_checklist.py --fase 3  # solo Fase 3
  python scripts/validar_checklist.py --all     # incluye probar m2 si stale
"""
import argparse
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from core.validacion import CHECKS_FASE, ejecutar_checks, guardar_informe  # noqa: E402

# ASCII para consolas Windows (cp1252); el JSON del informe sigue siendo la fuente.
ICONOS = {"pass": "[OK]", "fail": "[X]", "pending": "[..]", "stub": "[~]", "skip": "[-]"}

# Evitar UnicodeEncodeError en stdout heredado
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass



def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fase", action="append", help="Fase(s) a validar: 0,2,3,4")
    parser.add_argument("--all", action="store_true", help="Correr validar_m2 si pentiverso stale")
    args = parser.parse_args()

    fases = args.fase or ["0", "2", "3", "4"]

    if args.all and "3" in fases:
        import subprocess
        m2 = os.path.join(ROOT, "data", "validacion_m2.json")
        stale = True
        if os.path.exists(m2):
            import json
            import time
            with open(m2, encoding="utf-8") as f:
                d = json.load(f)
            stale = (time.time() - d.get("ts", 0)) > 3600
        if stale or not os.path.exists(m2):
            print("[…] Pentiverso stale — ejecutando validar_m2.py (25s WS)…")
            subprocess.run(
                [sys.executable, os.path.join(ROOT, "scripts", "validar_m2.py"), "--segundos", "20"],
                cwd=ROOT,
            )

    informe = ejecutar_checks(fases)
    ruta = guardar_informe(informe)

    print(f"\n=== CHECKLIST SHADOWHARMY | {len(informe.checks)} checks ===\n")
    for c in informe.checks:
        icon = ICONOS.get(c.status, "?")
        print(f"  {icon} [{c.fase}] {c.id} {c.titulo}")
        if c.detalle:
            print(f"      → {c.detalle}")

    print(f"\nResumen: {informe.resumen}")
    print(f"Reporte: {ruta}\n")

    fails = informe.resumen.get("fail", 0)
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
