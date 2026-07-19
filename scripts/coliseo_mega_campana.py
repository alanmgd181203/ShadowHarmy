#!/usr/bin/env python3
"""Mega Coliseo — legión máxima · 2 ejes malla · 2 vacíos · sub-Berus · checkpoints.

Orden de batalla (Monarca):
  Eje A malla ×1 → barrido vacíos (PLENO+legión) → top 2 vacíos → todos los tiers
  Eje B malla ×2 → igual
  Outliers: re-run con path min si masa_cap_hits altos o efi absurda
  Indicador: calor 3d/mes/año (20/50/30) → pase de batalla / ranking de rangos

Uso:
  python scripts/coliseo_mega_campana.py
  python scripts/coliseo_mega_campana.py --resume
  python scripts/coliseo_mega_campana.py --only BTC,ETH --eje 1
  python scripts/coliseo_mega_informe.py   # tras terminar
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import core.config as config
from core import coliseo_boveda as bov
from core.coliseo_beru_fantasma import VACIOS_BARRIDO_DEFAULT, semaforo
from core.coliseo_beru_legion import (
    TIERS_ORDEN,
    calor_pase,
    simular_legion_desde_velas,
)

MEGA_DIR = bov.COLISEO_DIR / "mega"
CKPT_PATH = MEGA_DIR / "checkpoint.json"
JOBS_DIR = MEGA_DIR / "jobs"
LOG_PATH = MEGA_DIR / "campana.log"


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _log(msg: str) -> None:
    MEGA_DIR.mkdir(parents=True, exist_ok=True)
    line = f"{_utcnow()} {msg}"
    print(line, flush=True)
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def _margen_map() -> dict[str, float]:
    path = ROOT / "config" / "diccionario_beru_flota_manto.json"
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    out: dict[str, float] = {}
    for a, row in (data.get("activos") or {}).items():
        out[str(a).upper()] = float(
            row.get("margen_volumen_base_usd") or row.get("X") or 12.5
        )
    return out


def _flota(con, only: list[str] | None) -> list[str]:
    rows = con.execute("SELECT DISTINCT base FROM candles ORDER BY base").fetchall()
    bases = [str(r[0]).upper() for r in rows]
    if only:
        want = set(only)
        return [b for b in bases if b in want]
    return bases


def _load_ckpt() -> dict[str, Any]:
    MEGA_DIR.mkdir(parents=True, exist_ok=True)
    JOBS_DIR.mkdir(parents=True, exist_ok=True)
    if not CKPT_PATH.exists():
        return {
            "version": 3,
            "status": "running",
            "created_utc": _utcnow(),
            "jobs_done": {},
            "vacios_dorados": {},
            "outliers": [],
            "eje_fase": {},
            "updated_utc": _utcnow(),
        }
    return json.loads(CKPT_PATH.read_text(encoding="utf-8"))


def _save_ckpt(ckpt: dict[str, Any]) -> None:
    ckpt["updated_utc"] = _utcnow()
    CKPT_PATH.write_text(json.dumps(ckpt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _job_key(eje: float, fase: str, vacio: float, tier: str, activo: str) -> str:
    return f"x{eje:g}|{fase}|v{vacio*100:.1f}|{tier}|{activo}"


def _job_path(key: str) -> Path:
    safe = key.replace("|", "__").replace(".", "p")
    return JOBS_DIR / f"{safe}.json"


def _partir_meses(candles: list) -> list[tuple[str, list]]:
    buckets: dict[str, list] = {}
    for row in candles:
        ts = int(row[0])
        key = datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m")
        buckets.setdefault(key, []).append(row)
    return sorted(buckets.items(), key=lambda x: x[0])


def _ventana(candles: list, now_ts: int, days: int) -> list:
    since = now_ts - days * 86_400
    return [c for c in candles if c[0] >= since]


def _result_to_dict(r) -> dict[str, Any]:
    return {
        "activo": r.activo,
        "vacio_pct": r.vacio_pct,
        "eficiencia": r.eficiencia,
        "botin_neto": r.botin_neto,
        "botin_bruto": r.botin_bruto,
        "fees": r.fees,
        "cosechas": r.cosechas,
        "margen_usd": r.margen_usd,
        "n_capas": r.n_capas,
        "n_fusiones": r.n_fusiones,
        "n_megas": r.n_megas,
        "masa_max": r.masa_max,
        "masa_cap_hits": r.masa_cap_hits,
        "n_ships_max": r.n_ships_max,
        "tier_id": r.tier_id,
        "rango": r.rango,
        "malla_scale": r.malla_scale,
        "path_policy": r.path_policy,
        "latidos": r.latidos,
    }


def run_one(
    candles: list,
    *,
    activo: str,
    vacio: float,
    margen: float,
    tier: str,
    malla: float,
    path_policy: str,
    fee_pct: float,
    slip_bps: float,
    now_ts: int,
    por_mes: bool = False,
) -> dict[str, Any]:
    kw = dict(
        activo=activo,
        vacio=vacio,
        margen_usd=margen,
        tier_id=tier,
        malla_scale=malla,
        fee_pct=fee_pct,
        slip_bps=slip_bps,
        path_policy=path_policy,  # type: ignore[arg-type]
    )
    c_anio = candles
    c_mes = _ventana(candles, now_ts, 30)
    c_3d = _ventana(candles, now_ts, 3)
    t0 = time.time()
    r_anio = simular_legion_desde_velas(c_anio, **kw)
    r_mes = simular_legion_desde_velas(c_mes, **kw) if len(c_mes) >= 100 else r_anio
    r_3d = simular_legion_desde_velas(c_3d, **kw) if len(c_3d) >= 50 else r_mes
    calor = calor_pase(r_3d.eficiencia, r_mes.eficiencia, r_anio.eficiencia)

    # Desglose mensual: solo cuando se pide (tiers dorados / outliers), no en todo el barrido
    meses = []
    if por_mes:
        for mes_key, chunk in _partir_meses(c_anio):
            if len(chunk) < 100:
                continue
            rm = simular_legion_desde_velas(chunk, **kw)
            meses.append(
                {
                    "mes": mes_key,
                    "eficiencia": rm.eficiencia,
                    "botin_neto": rm.botin_neto,
                    "cosechas": rm.cosechas,
                    "n_capas": rm.n_capas,
                    "n_fusiones": rm.n_fusiones,
                    "n_megas": rm.n_megas,
                }
            )

    out = _result_to_dict(r_anio)
    out.update(
        {
            "efi_3d": r_3d.eficiencia,
            "efi_mes": r_mes.eficiencia,
            "efi_anio": r_anio.eficiencia,
            "calor_pase": calor,
            "meses": meses,
            "secs": round(time.time() - t0, 2),
            "ts_utc": _utcnow(),
        }
    )
    return out


def _median(xs: list[float]) -> float:
    if not xs:
        return 0.0
    s = sorted(xs)
    n = len(s)
    mid = n // 2
    if n % 2:
        return s[mid]
    return 0.5 * (s[mid - 1] + s[mid])


def _pick_top2_vacios(results: list[dict[str, Any]]) -> list[float]:
    """Mediana de calor_pase por vacío → top 2."""
    by_v: dict[float, list[float]] = {}
    for r in results:
        v = round(float(r["vacio_pct"]) / 100.0, 4)
        by_v.setdefault(v, []).append(float(r["calor_pase"]))
    ranked = sorted(
        ((v, _median(vals)) for v, vals in by_v.items()),
        key=lambda x: x[1],
        reverse=True,
    )
    return [v for v, _ in ranked[:2]]


def _detect_outliers(results: list[dict[str, Any]]) -> list[str]:
    """Activos con masa_cap_hits altos o efi muy lejos de la mediana."""
    if len(results) < 5:
        return []
    efis = [float(r["efi_anio"]) for r in results]
    med = _median(efis)
    # MAD-ish
    abs_dev = sorted(abs(e - med) for e in efis)
    mad = _median(abs_dev) or 1.0
    out = []
    for r in results:
        if int(r.get("masa_cap_hits") or 0) >= 50:
            out.append(r["activo"])
            continue
        if abs(float(r["efi_anio"]) - med) > max(10 * mad, med * 3 + 100):
            out.append(r["activo"])
    return sorted(set(out))


def main() -> int:
    ap = argparse.ArgumentParser(description="Mega Coliseo legión + checkpoints")
    ap.add_argument("--resume", action="store_true", help="Reanudar desde checkpoint")
    ap.add_argument("--reset", action="store_true", help="Borrar checkpoint y empezar limpio")
    ap.add_argument("--only", type=str, default="", help="Activos CSV")
    ap.add_argument("--eje", type=float, default=0, help="Solo eje 1 o 2 (0=ambos)")
    ap.add_argument("--path-policy", choices=["ohlc", "min"], default="ohlc")
    ap.add_argument("--fee-pct", type=float, default=0.001)
    ap.add_argument("--slip-bps", type=float, default=2.0)
    ap.add_argument("--skip-tiers", action="store_true", help="Solo barrido vacíos")
    ap.add_argument("--skip-outliers", action="store_true")
    args = ap.parse_args()

    if not bov.BOVEDA_PATH.exists():
        print(f"Sin bóveda: {bov.BOVEDA_PATH}")
        return 2

    if args.reset and CKPT_PATH.exists():
        CKPT_PATH.unlink()
        _log("RESET checkpoint")

    ckpt = _load_ckpt()
    only = [x.strip().upper() for x in args.only.split(",") if x.strip()] or None
    margenes = _margen_map()
    con = bov.connect()
    flota = _flota(con, only)
    # precarga velas
    cache: dict[str, list] = {}
    for a in flota:
        cache[a] = bov.load_candles(con, a)
    con.close()
    now_ts = int(time.time())
    vacios = list(VACIOS_BARRIDO_DEFAULT)
    ejes = [1.0, 2.0] if args.eje <= 0 else [float(args.eje)]

    _log(
        f"MEGA start flota={len(flota)} ejes={ejes} path={args.path_policy} "
        f"jobs_done={len(ckpt.get('jobs_done') or {})}"
    )

    for malla in ejes:
        eje_tag = f"x{malla:g}"
        # --- Fase barrido ---
        barrido_results: list[dict[str, Any]] = []
        for vacio in vacios:
            for activo in flota:
                key = _job_key(malla, "barrido", vacio, "PLENO", activo)
                if key in (ckpt.get("jobs_done") or {}):
                    barrido_results.append(ckpt["jobs_done"][key])
                    continue
                _log(f"RUN {key}")
                try:
                    candles = cache[activo]
                    if len(candles) < 500:
                        raise RuntimeError("velas insuficientes")
                    res = run_one(
                        candles,
                        activo=activo,
                        vacio=vacio,
                        margen=margenes.get(activo, 12.5),
                        tier="PLENO",
                        malla=malla,
                        path_policy=args.path_policy,
                        fee_pct=args.fee_pct,
                        slip_bps=args.slip_bps,
                        now_ts=now_ts,
                        por_mes=False,
                    )
                    res["job_key"] = key
                    res["fase"] = "barrido"
                    _job_path(key).write_text(
                        json.dumps(res, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
                    )
                    ckpt.setdefault("jobs_done", {})[key] = res
                    _save_ckpt(ckpt)
                    barrido_results.append(res)
                    _log(
                        f"OK {key} calor={res['calor_pase']:.2f} efi={res['efi_anio']:.1f} "
                        f"capas={res['n_capas']} mega={res['n_megas']} {res['secs']}s"
                    )
                except Exception as e:
                    _log(f"FAIL {key}: {e}")
                    traceback.print_exc()
                    ckpt.setdefault("failures", {})[key] = {
                        "error": str(e),
                        "ts": _utcnow(),
                    }
                    _save_ckpt(ckpt)
                    continue

        top2 = _pick_top2_vacios(barrido_results)
        ckpt.setdefault("vacios_dorados", {})[eje_tag] = top2
        _save_ckpt(ckpt)
        _log(f"Eje {eje_tag} vacíos dorados: {[round(v*100,1) for v in top2]}")

        if args.skip_tiers:
            continue

        # --- Fase sub-Berus ---
        tier_results: list[dict[str, Any]] = []
        for vacio in top2:
            for tier in TIERS_ORDEN:
                for activo in flota:
                    key = _job_key(malla, "tier", vacio, tier, activo)
                    if key in (ckpt.get("jobs_done") or {}):
                        tier_results.append(ckpt["jobs_done"][key])
                        continue
                    _log(f"RUN {key}")
                    try:
                        res = run_one(
                            cache[activo],
                            activo=activo,
                            vacio=vacio,
                            margen=margenes.get(activo, 12.5),
                            tier=tier,
                            malla=malla,
                            path_policy=args.path_policy,
                            fee_pct=args.fee_pct,
                            slip_bps=args.slip_bps,
                            now_ts=now_ts,
                            por_mes=(tier == "PLENO"),
                        )
                        res["job_key"] = key
                        res["fase"] = "tier"
                        _job_path(key).write_text(
                            json.dumps(res, indent=2, ensure_ascii=False) + "\n",
                            encoding="utf-8",
                        )
                        ckpt.setdefault("jobs_done", {})[key] = res
                        _save_ckpt(ckpt)
                        tier_results.append(res)
                        _log(
                            f"OK {key} calor={res['calor_pase']:.2f} rango={res['rango']} "
                            f"{res['secs']}s"
                        )
                    except Exception as e:
                        _log(f"FAIL {key}: {e}")
                        ckpt.setdefault("failures", {})[key] = {
                            "error": str(e),
                            "ts": _utcnow(),
                        }
                        _save_ckpt(ckpt)

        # --- Outliers re-run path min ---
        if not args.skip_outliers:
            # usar barrido del primer vacío dorado
            sample = [
                r
                for r in barrido_results
                if top2 and abs(float(r["vacio_pct"]) / 100.0 - top2[0]) < 1e-6
            ]
            outs = _detect_outliers(sample)
            ckpt.setdefault("outliers", [])
            for activo in outs:
                key = _job_key(malla, "outlier", top2[0] if top2 else vacios[0], "PLENO", activo)
                if key in ckpt["jobs_done"]:
                    continue
                _log(f"OUTLIER re-run min {key}")
                try:
                    res = run_one(
                        cache[activo],
                        activo=activo,
                        vacio=top2[0] if top2 else vacios[3],
                        margen=margenes.get(activo, 12.5),
                        tier="PLENO",
                        malla=malla,
                        path_policy="min",
                        fee_pct=args.fee_pct,
                        slip_bps=args.slip_bps,
                        now_ts=now_ts,
                        por_mes=True,
                    )
                    res["job_key"] = key
                    res["fase"] = "outlier"
                    res["motivo_outlier"] = "masa_cap_o_efi_extrema"
                    _job_path(key).write_text(
                        json.dumps(res, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
                    )
                    ckpt["jobs_done"][key] = res
                    if activo not in ckpt["outliers"]:
                        ckpt["outliers"].append(activo)
                    _save_ckpt(ckpt)
                except Exception as e:
                    _log(f"FAIL outlier {key}: {e}")

        ckpt.setdefault("eje_fase", {})[eje_tag] = "done"
        _save_ckpt(ckpt)
        _log(f"Eje {eje_tag} COMPLETO")

    ckpt["status"] = "done"
    _save_ckpt(ckpt)
    _log("MEGA CAMPANA DONE — corre: python scripts/coliseo_mega_informe.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
