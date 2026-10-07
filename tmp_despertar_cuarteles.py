"""Despierta la flota en los cuarteles parejos. No toca a Igris ni a BTC.

Corre en la viejita.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from collections import defaultdict
from pathlib import Path

ROOT = Path(r"C:\Users\lenovo\ShadowHarmy")
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))
os.environ.setdefault("BERU_MAR", "okx")
os.environ.setdefault("PYTHONUTF8", "1")

PY = r"C:\Users\lenovo\AppData\Local\Python\pythoncore-3.14-64\python.exe"
VF = ROOT / "data" / "beru" / "rango" / "vigilante_flota"
MANIFEST = VF / "campamentos.json"


def ps(script: str) -> str:
    r = subprocess.run(
        ["powershell", "-NoProfile", "-Command", script],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return (r.stdout or "") + (r.stderr or "")


def procesos(filtro: str) -> list[tuple[int, str]]:
    raw = ps(
        "Get-CimInstance Win32_Process -EA SilentlyContinue | "
        "Where-Object { $_.CommandLine -and $_.CommandLine -match '" + filtro + "' } | "
        "ForEach-Object { $_.ProcessId.ToString() + '|' + $_.CommandLine }"
    )
    out = []
    for line in raw.splitlines():
        if "|" not in line:
            continue
        pid_s, cmd = line.split("|", 1)
        try:
            out.append((int(pid_s.strip()), cmd))
        except ValueError:
            continue
    return out


def wmi_bat(bat: Path) -> int:
    cmd = "cmd.exe /c \"" + str(bat) + "\""
    safe = cmd.replace("'", "''")
    raw = ps(
        "$r = ([wmiclass]'Win32_Process').Create('" + safe + "'); "
        "Write-Output ($r.ReturnValue.ToString() + '|' + $r.ProcessId.ToString())"
    )
    for line in reversed(raw.splitlines()):
        if "|" in line:
            ret, pid = line.strip().split("|", 1)
            return int(pid) if ret.strip() == "0" else -1
    return -1


def cargar() -> list[dict]:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    camps = list(data.get("campamentos") or [])
    vistos = []
    for c in camps:
        for a in c.get("santos") or []:
            vistos.append(str(a).upper())
    if "BTC" in vistos:
        raise SystemExit("BTC_EN_CUARTEL")
    if len(vistos) != len(set(vistos)):
        raise SystemExit("MANIFEST_CON_DUPLICADOS")
    print(f"MANIFEST camps={len(camps)} santos={len(vistos)}", flush=True)
    rojos = []
    for c in camps:
        nrojo = len((c.get("por_color") or {}).get("rojo") or [])
        rojos.append(nrojo)
    print(f"ROJOS_POR_CUARTEL min={min(rojos)} max={max(rojos)}", flush=True)
    return camps


def matar_sueltos() -> None:
    antes_igris = len(procesos("arise_igris_escudo_btc"))
    print(f"IGRIS_ANTES={antes_igris}", flush=True)
    matados = 0
    for pid, cmd in procesos("arise_beru_rango_manos|arise_beru_rango_campamento|vigilar_flota_piedra"):
        if "arise_igris" in cmd:
            continue
        subprocess.run(["taskkill", "/PID", str(pid), "/F"], capture_output=True)
        matados += 1
    print(f"MATADOS={matados}", flush=True)
    time.sleep(4)
    print(f"MANOS_TRAS_MUERTE={len(procesos('arise_beru_rango_manos'))}", flush=True)
    print(f"CAMP_TRAS_MUERTE={len(procesos('arise_beru_rango_campamento'))}", flush=True)
    print(f"IGRIS_TRAS_MUERTE={len(procesos('arise_igris_escudo_btc'))}", flush=True)


def escribir_bats(camps: list[dict]) -> None:
    for camp in camps:
        cid = str(camp["id"])
        santos = ",".join(str(a).upper() for a in camp["santos"])
        folder = VF / "campamentos" / cid
        folder.mkdir(parents=True, exist_ok=True)
        bat = VF / f"run_{cid}.bat"
        bat.write_text(
            "@echo off\r\n"
            "set BERU_MAR=okx\r\n"
            "set BERU_RANGO_PERFIL=piedra\r\n"
            "set BERU_RANGO_MANOS=true\r\n"
            "set BERU_RANGO_RED_EXPANSIVA=1\r\n"
            "set BERU_RANGO_RED_EXPANSIVA_MAX_ESCALONES=15\r\n"
            "set BERU_RANGO_FLACO=false\r\n"
            "set BRIDGE_WS_SUBSCRIBE_BOOKS=false\r\n"
            "set BERU_FLOTA_CUPO_VIVOS=0\r\n"
            "set MODO_SIMULACION=false\r\n"
            "set PYTHONUTF8=1\r\n"
            "cd /d C:\\Users\\lenovo\\ShadowHarmy\r\n"
            f"{PY} -u scripts\\arise_beru_rango_campamento.py --santos {santos} "
            f"--camp-id {cid} --desde-cero --perfil piedra --manos-go "
            f">> data\\beru\\rango\\vigilante_flota\\campamentos\\{cid}\\stdout.log "
            f"2>> data\\beru\\rango\\vigilante_flota\\campamentos\\{cid}\\stderr.log\r\n",
            encoding="ascii",
        )


def ordenes() -> None:
    from core import okx_rest

    if not okx_rest.credenciales_ok():
        print("SIN_CREDENCIALES")
        return
    rows = []
    after = ""
    for _ in range(12):
        params = {"instType": "SWAP", "limit": "100"}
        if after:
            params["after"] = after
        batch = okx_rest.get_private("/api/v5/trade/orders-pending", params=params) or []
        if not batch:
            break
        rows.extend(batch)
        after = str(batch[-1].get("ordId") or "")
        if len(batch) < 100:
            break
        time.sleep(0.2)
    by = defaultdict(list)
    for o in rows:
        inst = str(o.get("instId") or "")
        if inst == "BTC-USD-SWAP":
            continue
        by[inst].append(o)
    dups = {k: v for k, v in by.items() if len(v) > 1}
    print(f"ORDENES_BERU={sum(len(v) for v in by.values())} INSTRUMENTOS={len(by)} DUPLICADAS={len(dups)}", flush=True)
    canceladas = 0
    for inst, ords in dups.items():
        ords.sort(key=lambda o: int(o.get("cTime") or 0))
        for vieja in ords[:-1]:
            try:
                okx_rest.post_private(
                    "/api/v5/trade/cancel-order",
                    {"instId": inst, "ordId": str(vieja.get("ordId") or "")},
                )
                canceladas += 1
            except Exception as exc:
                print(f"CANCEL_FALLO {inst} {exc}", flush=True)
            time.sleep(0.15)
    print(f"ORDENES_VIEJAS_CANCELADAS={canceladas}", flush=True)


def limpiar_cache() -> None:
    for carpeta in (
        ROOT / "core" / "__pycache__",
        ROOT / "cirugias" / "__pycache__",
        ROOT / "cirugias" / "sala_por_color" / "__pycache__",
    ):
        if not carpeta.exists():
            continue
        for p in carpeta.glob("*.pyc"):
            if "beru_rango" in p.name or "sala" in p.name:
                p.unlink(missing_ok=True)


def main() -> int:
    limpiar_cache()
    camps = cargar()
    matar_sueltos()
    escribir_bats(camps)
    pids = []
    for i, camp in enumerate(camps, start=1):
        bat = VF / f"run_{camp['id']}.bat"
        pid = wmi_bat(bat)
        pids.append(pid)
        print(f"LANZA {i}/{len(camps)} {camp['id']} pid={pid} n={camp['n']}", flush=True)
        time.sleep(1.4)
    print("ESPERA_ARRANQUE", flush=True)
    time.sleep(35)
    vivos = procesos("arise_beru_rango_campamento")
    manos = procesos("arise_beru_rango_manos")
    santos = []
    for _pid, cmd in vivos:
        if "--santos " in cmd:
            trozo = cmd.split("--santos ", 1)[1].split(" ", 1)[0]
            santos.extend(a.strip().upper() for a in trozo.split(",") if a.strip())
    print(f"CUARTELES={len(vivos)} MANOS_SUELTAS={len(manos)} SANTOS_EN_CUARTEL={len(santos)} UNICOS={len(set(santos))}", flush=True)
    dups = [a for a, n in __import__('collections').Counter(santos).items() if n > 1]
    print(f"SANTOS_REPETIDOS={len(dups)}", flush=True)
    if dups:
        print("REPETIDOS", ",".join(dups[:20]), flush=True)
    print(f"IGRIS={len(procesos('arise_igris_escudo_btc'))}", flush=True)
    print(f"PIDS_OK={sum(1 for p in pids if p > 0)}", flush=True)
    ordenes()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
