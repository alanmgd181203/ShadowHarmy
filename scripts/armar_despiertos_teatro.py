#!/usr/bin/env python3
"""Escanea sellos Beru rango → despiertos.json para el teatro.

Criterio despierto: carpeta data/beru/rango/{SANTO}/ con
manos_informe · ojos_eventos · manos_eventos, o vivo en rango_vivo.json.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RANGO_DIR = ROOT / "data" / "beru" / "rango"
OUT = ROOT / "data" / "coliseo" / "rango_juicio" / "despiertos.json"
VIVO = ROOT / "data" / "beru" / "rango_vivo.json"
PIEDRA = ROOT / "data" / "beru" / "rango" / "piedra_asignacion.json"

SELLOS_INFORME = (
    "manos_informe.json",
    "manos_feria_informe.json",
    "manos_inverso_informe.json",
)
SELLOS_EVENTOS = (
    "ojos_eventos.jsonl",
    "manos_eventos.jsonl",
    "ojos_feria_eventos.jsonl",
    "manos_feria_eventos.jsonl",
    "ojos_inverso_eventos.jsonl",
    "manos_inverso_eventos.jsonl",
)


def _f(x: Any, default: float = 0.0) -> float:
    try:
        return float(x or 0)
    except (TypeError, ValueError):
        return default


def _leer_vivo_ahora() -> dict[str, dict[str, Any]]:
    """Mapa activo → fila de rango_vivo (ojos/manos corriendo ahora)."""
    if not VIVO.exists():
        return {}
    try:
        j = json.loads(VIVO.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    out: dict[str, dict[str, Any]] = {}
    for row in j.get("activos") or []:
        a = str(row.get("activo") or "").upper().strip()
        if a:
            out[a] = row if isinstance(row, dict) else {"activo": a}
    foco = str(j.get("activo_foco") or "").upper().strip()
    if foco and foco not in out:
        out[foco] = {"activo": foco}
    return out


def _ultima_linea_jsonl(path: Path) -> dict[str, Any] | None:
    try:
        raw = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    for line in reversed(raw.splitlines()):
        s = line.strip()
        if not s:
            continue
        try:
            j = json.loads(s)
        except json.JSONDecodeError:
            continue
        if isinstance(j, dict):
            return j
    return None


def _desde_manos_informe(path: Path) -> dict[str, Any] | None:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    snap = raw.get("snapshot") or {}
    vivo = snap.get("vivo") or {}
    cero = _f(vivo.get("cero"))
    estado = str(vivo.get("estado") or "").upper() or None
    return {
        "estado": estado,
        "cero": cero if cero > 0 else None,
        "manos": bool(raw.get("manos")),
        "ts_informe": _f(raw.get("ts")) or None,
        "cosechas": int(vivo.get("cosechas") or 0),
        "fuente": "manos_informe",
    }


def _desde_eventos(path: Path, *, manos: bool) -> dict[str, Any] | None:
    ev = _ultima_linea_jsonl(path)
    if not ev:
        return {"estado": None, "cero": None, "manos": manos, "ts_informe": None, "cosechas": 0, "fuente": path.name}
    detalle = ev.get("detalle") if isinstance(ev.get("detalle"), dict) else {}
    cero = _f(detalle.get("cero") if detalle else None) or _f(ev.get("cero"))
    estado = str(ev.get("estado") or detalle.get("estado") or "").upper() or None
    if not estado:
        evento = str(ev.get("evento") or detalle.get("evento") or "").upper()
        if evento:
            estado = evento
    return {
        "estado": estado,
        "cero": cero if cero > 0 else None,
        "manos": manos,
        "ts_informe": _f(ev.get("ts")) or None,
        "cosechas": int(detalle.get("cosechas") or ev.get("cosechas") or 0),
        "fuente": path.name,
    }


def _sello_carpeta(p: Path) -> dict[str, Any] | None:
    """Prioridad: informes manos (normal/feria/inverso) → eventos manos/ojos."""
    for name in SELLOS_INFORME:
        path = p / name
        if path.is_file():
            meta = _desde_manos_informe(path)
            if meta:
                meta["fuente"] = name
                # feria/inverso informes: manos True si nombre empieza manos_
                meta["manos"] = name.startswith("manos_")
                return meta
    for name in SELLOS_EVENTOS:
        path = p / name
        if path.is_file():
            manos = name.startswith("manos_")
            return _desde_eventos(path, manos=manos)
    # Cualquier otro *informe* / *eventos* en la carpeta del santo.
    if p.is_dir():
        for path in sorted(p.iterdir()):
            if not path.is_file():
                continue
            n = path.name.lower()
            if n.endswith("_informe.json") or n == "informe.json":
                meta = _desde_manos_informe(path)
                if meta:
                    meta["fuente"] = path.name
                    meta["manos"] = "manos" in n
                    return meta
            if n.endswith("_eventos.jsonl") or n.endswith("eventos.jsonl"):
                return _desde_eventos(path, manos="manos" in n)
    return None


def _leer_piedra_flota() -> dict[str, dict[str, Any]]:
    """Flota piedra volcada del teatro OKX (n≈115) — ya elegidos / a menudo ya despertados."""
    if not PIEDRA.exists():
        return {}
    try:
        j = json.loads(PIEDRA.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    out: dict[str, dict[str, Any]] = {}
    for act, row in (j.get("activos") or {}).items():
        a = str(act or "").upper().strip()
        if not a:
            continue
        meta = row if isinstance(row, dict) else {}
        out[a] = {
            "semaforo": str(meta.get("semaforo") or meta.get("color") or "").lower() or None,
            "rango_pct": meta.get("rango_pct"),
        }
    return out


def escanear() -> dict[str, Any]:
    vivos_ahora = _leer_vivo_ahora()
    piedra = _leer_piedra_flota()
    santos: dict[str, dict[str, Any]] = {}
    if not RANGO_DIR.is_dir():
        return {"santos": {}, "lista": []}

    for p in sorted(RANGO_DIR.iterdir()):
        if not p.is_dir():
            continue
        act = p.name.upper()
        meta = _sello_carpeta(p)
        if not meta:
            continue
        santos[act] = {
            "activo": act,
            "despierto": True,
            "estado": meta.get("estado"),
            "cero": meta.get("cero"),
            "manos": bool(meta.get("manos")),
            "en_vivo_ahora": act in vivos_ahora,
            "ts_informe": meta.get("ts_informe"),
            "cosechas": int(meta.get("cosechas") or 0),
            "fuente": meta.get("fuente"),
            "en_piedra": act in piedra,
            "semaforo": (piedra.get(act) or {}).get("semaforo"),
        }

    # Flota piedra del teatro OKX (≈115): marcar aunque el sello viva en otra lap.
    for act, row in piedra.items():
        if act in santos:
            santos[act]["en_piedra"] = True
            if row.get("semaforo"):
                santos[act]["semaforo"] = row["semaforo"]
            continue
        santos[act] = {
            "activo": act,
            "despierto": True,
            "estado": None,
            "cero": None,
            "manos": False,
            "en_vivo_ahora": act in vivos_ahora,
            "ts_informe": None,
            "cosechas": 0,
            "fuente": "piedra_asignacion",
            "en_piedra": True,
            "semaforo": row.get("semaforo"),
        }

    for act, row in vivos_ahora.items():
        cero = _f(row.get("cero"))
        estado = str(row.get("estado") or "").upper() or None
        if act in santos:
            santos[act]["en_vivo_ahora"] = True
            if estado:
                santos[act]["estado"] = estado
            if cero > 0:
                santos[act]["cero"] = cero
            continue
        santos[act] = {
            "activo": act,
            "despierto": True,
            "estado": estado,
            "cero": cero if cero > 0 else None,
            "manos": bool(row.get("manos")),
            "en_vivo_ahora": True,
            "ts_informe": _f(row.get("ts_santo")) or None,
            "cosechas": int(row.get("cosechas") or 0),
            "fuente": "rango_vivo",
            "en_piedra": act in piedra,
            "semaforo": (piedra.get(act) or {}).get("semaforo"),
        }

    lista = sorted(santos.keys())
    return {"santos": santos, "lista": lista}


def main() -> int:
    data = escanear()
    n_ojos = sum(1 for s in data["santos"].values() if str(s.get("fuente") or "").startswith("ojos"))
    n_manos = sum(1 for s in data["santos"].values() if s.get("manos"))
    n_piedra = sum(1 for s in data["santos"].values() if s.get("en_piedra"))
    payload = {
        "ts_utc": datetime.now(timezone.utc).isoformat(),
        "n_despiertos": len(data["lista"]),
        "n_vivos_ahora": sum(1 for s in data["santos"].values() if s.get("en_vivo_ahora")),
        "n_con_manos": n_manos,
        "n_solo_ojos": n_ojos,
        "n_piedra_flota": n_piedra,
        "santos": data["santos"],
        "lista": data["lista"],
        "nota": (
            "Despierto = sello local (manos/ojos) · flota piedra OKX (~115) · "
            "o vivo en rango_vivo. en_vivo_ahora = proceso corriendo ahora en esta lap."
        ),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        f"OK -> {OUT} · despiertos={payload['n_despiertos']} "
        f"· vivos_ahora={payload['n_vivos_ahora']} "
        f"· piedra={n_piedra} · manos={n_manos} · solo_ojos={n_ojos}"
    )
    if payload["lista"]:
        print("  " + ", ".join(payload["lista"][:20]) + ("…" if len(payload["lista"]) > 20 else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
