"""Memoria de barcos — diario horario desde Tank (Kaiser).

Cada hora (configurable) se agrega un snapshot por activo a
`data/kaiser/memoria/{BASE}.jsonl` con los mismos datos que Tank
ya calcula (matriz, desvío, funding). No re-corre el Coliseo Mega.

Kaiser compara con el grial firmado (13 Santos) para susurrar
candidatos / sillas en riesgo al Pergamino vía digest.
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import core.config as config

ROOT = Path(__file__).resolve().parents[1]
MEMORIA_DIR = ROOT / "data" / "kaiser" / "memoria"


def _santos_grial() -> set[str]:
    try:
        from core.plan_crecimiento import SANTOS_GRIAL
        return {s.upper() for s in SANTOS_GRIAL}
    except Exception:
        return set()


def _ruta(base: str) -> Path:
    MEMORIA_DIR.mkdir(parents=True, exist_ok=True)
    safe = "".join(c for c in base.upper() if c.isalnum() or c in "_-")
    return MEMORIA_DIR / f"{safe}.jsonl"


def _trim(path: Path) -> None:
    max_lines = int(getattr(config, "KAISER_MEMORIA_MAX_LINES", 2160))
    max_days = int(getattr(config, "KAISER_MEMORIA_MAX_DAYS", 120))
    cutoff = time.time() - max_days * 86400
    if not path.exists():
        return
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return
    kept: list[str] = []
    for ln in lines:
        try:
            row = json.loads(ln)
            if float(row.get("ts", 0)) >= cutoff:
                kept.append(ln)
        except json.JSONDecodeError:
            continue
    if len(kept) > max_lines:
        kept = kept[-max_lines:]
    path.write_text("\n".join(kept) + ("\n" if kept else ""), encoding="utf-8")


def leer_ultimas(base: str, n: int = 24) -> list[dict]:
    path = _ruta(base)
    if not path.exists():
        return []
    out: list[dict] = []
    try:
        for ln in path.read_text(encoding="utf-8").splitlines():
            if not ln.strip():
                continue
            out.append(json.loads(ln))
    except (OSError, json.JSONDecodeError):
        return []
    return out[-max(1, n) :]


def _indice_filas(filas: list[dict], key: str = "base") -> dict[str, dict]:
    out: dict[str, dict] = {}
    for r in filas or []:
        b = str(r.get(key) or "").upper()
        if not b:
            continue
        # conservar la fila de mayor |spread| / |desvio| si hay varias
        prev = out.get(b)
        if prev is None:
            out[b] = r
            continue
        cur_m = abs(float(r.get("spread_pct") or r.get("desvio_pct") or r.get("desvio_signed_pct") or 0))
        prev_m = abs(float(prev.get("spread_pct") or prev.get("desvio_pct") or prev.get("desvio_signed_pct") or 0))
        if cur_m >= prev_m:
            out[b] = r
    return out


def _bases_desde_tank(tank) -> list[str]:
    """Unión: grial + pentiverso + top matriz/desvío."""
    santos = list(_santos_grial()) or list(getattr(config, "ACTIVOS_PENTIVERSO", []) or [])
    penta = list(getattr(config, "ACTIVOS_PENTIVERSO", []) or [])
    matriz = tank.snapshot_matriz_spreads() if hasattr(tank, "snapshot_matriz_spreads") else {}
    desvios = tank.snapshot_desvios_indice() if hasattr(tank, "snapshot_desvios_indice") else {}
    top_m = [str(r.get("base") or "").upper() for r in (matriz.get("filas") or [])[:30]]
    top_d = [str(r.get("base") or "").upper() for r in (desvios.get("filas") or [])[:30]]
    out: list[str] = []
    seen: set[str] = set()
    for b in santos + penta + top_m + top_d:
        if not b or b in seen:
            continue
        seen.add(b)
        out.append(b)
    cap = int(getattr(config, "KAISER_MEMORIA_MAX_BASES", 40))
    return out[:cap]


def construir_filas_hora(tank) -> list[dict[str, Any]]:
    """Una fila por barco a partir de snapshots Tank actuales."""
    matriz = tank.snapshot_matriz_spreads() if hasattr(tank, "snapshot_matriz_spreads") else {}
    desvios = tank.snapshot_desvios_indice() if hasattr(tank, "snapshot_desvios_indice") else {}
    funding = tank.snapshot_funding() if hasattr(tank, "snapshot_funding") else {}
    lider = tank._obtener_lider_verde() if hasattr(tank, "_obtener_lider_verde") else None
    semaforo = getattr(lider, "estado_foco", "ROJO") if lider else "ROJO"

    by_spread = _indice_filas(list(matriz.get("filas") or []))
    by_desvio = _indice_filas(list(desvios.get("filas") or []))
    by_fund: dict[str, dict] = {}
    for r in funding.get("top") or []:
        b = str(r.get("base") or "").upper()
        if b:
            by_fund[b] = r

    santos = _santos_grial()
    ts = time.time()
    filas: list[dict[str, Any]] = []
    for base in _bases_desde_tank(tank):
        sp = by_spread.get(base) or {}
        dv = by_desvio.get(base) or {}
        fd = by_fund.get(base) or {}
        filas.append({
            "ts": ts,
            "base": base,
            "en_grial": base in santos,
            "tank_semaforo": semaforo,
            "spread_pct": round(float(sp.get("spread_pct") or 0), 6),
            "spread_tipo": sp.get("tipo") or None,
            "desvio_pct": round(float(dv.get("desvio_pct") or dv.get("desvio_signed_pct") or 0), 6),
            "desvio_signed_pct": round(float(dv.get("desvio_signed_pct") or 0), 6),
            "huerfana": bool(dv.get("huerfana")),
            "funding_pct": round(float(fd.get("funding_pct") or 0), 6) if fd else None,
        })
    return filas


def _alertas_desde_delta(nuevas: list[dict], prev_por_base: dict[str, dict]) -> list[dict]:
    """Susurros ligeros si el barco cambia mucho vs la hora anterior."""
    umbral = float(getattr(config, "KAISER_MEMORIA_DELTA_UMBRAL_PCT", 0.35))
    alertas: list[dict] = []
    santos = _santos_grial()
    for row in nuevas:
        base = row["base"]
        prev = prev_por_base.get(base)
        if not prev:
            continue
        d_sp = abs(float(row.get("spread_pct") or 0) - float(prev.get("spread_pct") or 0))
        d_dv = abs(float(row.get("desvio_pct") or 0) - float(prev.get("desvio_pct") or 0))
        salto = max(d_sp, d_dv)
        if salto < umbral:
            continue
        en_grial = base in santos
        tipo = "GRIAL_PULSO" if en_grial else "CANDIDATO_PULSO"
        msg = (
            f"{base}: pulso memoria Δ{salto:.2f}% "
            f"(spread {prev.get('spread_pct')}→{row.get('spread_pct')}, "
            f"desvío {prev.get('desvio_pct')}→{row.get('desvio_pct')})"
        )
        if not en_grial and abs(float(row.get("desvio_pct") or 0)) >= umbral:
            msg += " · fuera del grial — posible candidato a Santo"
        alertas.append({
            "id": f"MEMORIA|{tipo}|{base}|{int(row['ts'])}",
            "tipo": tipo,
            "base": base,
            "severidad": "AVISO",
            "mensaje": msg,
            "destinatarios": ["BELLION", "KAISER", "MONARCA"],
            "payload": {"salto_pct": round(salto, 4), "en_grial": en_grial, "row": row},
        })
    return alertas


def persistir_filas(filas: list[dict]) -> int:
    n = 0
    for row in filas:
        path = _ruta(row["base"])
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=True) + "\n")
        _trim(path)
        n += 1
    return n


def append_memoria_si_toca(tank, ultimo_ts: float) -> tuple[int, float, list[dict], dict]:
    """
    Si pasó el intervalo, escribe memoria y devuelve alertas de pulso.
    Returns: (n_escritos, nuevo_ultimo_ts, alertas, resumen)
    """
    intervalo = float(getattr(config, "KAISER_MEMORIA_INTERVAL_S", 3600.0))
    ahora = time.time()
    if ultimo_ts > 0 and (ahora - ultimo_ts) < intervalo:
        return 0, ultimo_ts, [], resumen_memoria([])

    filas = construir_filas_hora(tank)
    prev: dict[str, dict] = {}
    for row in filas:
        hist = leer_ultimas(row["base"], 1)
        if hist:
            prev[row["base"]] = hist[-1]
    alertas = _alertas_desde_delta(filas, prev)
    n = persistir_filas(filas)
    resumen = resumen_memoria(filas)
    resumen["escrito"] = True
    resumen["n_filas"] = n
    resumen["ts"] = ahora
    return n, ahora, alertas, resumen


def resumen_memoria(filas_hora: list[dict] | None = None) -> dict[str, Any]:
    """Resumen ligero para digest / estado_vivo."""
    santos = sorted(_santos_grial())
    n_archivos = 0
    if MEMORIA_DIR.exists():
        n_archivos = sum(1 for _ in MEMORIA_DIR.glob("*.jsonl"))
    grial_vivo = []
    for s in santos[:13]:
        ult = leer_ultimas(s, 1)
        if ult:
            grial_vivo.append({
                "base": s,
                "spread_pct": ult[-1].get("spread_pct"),
                "desvio_pct": ult[-1].get("desvio_pct"),
                "ts": ult[-1].get("ts"),
            })
    return {
        "archivos_barcos": n_archivos,
        "santos_grial": santos,
        "grial_ultimo_pulso": grial_vivo,
        "hora_n_bases": len(filas_hora or []),
        "escrito": False,
    }


def snapshot_para_digest(ultimo_resumen: dict | None = None) -> dict[str, Any]:
    base = ultimo_resumen or resumen_memoria()
    return {
        "memoria_barcos": base,
        "nota": "Diario horario Tank→Kaiser; Coliseo Mega sigue siendo el juicio del grial.",
    }
