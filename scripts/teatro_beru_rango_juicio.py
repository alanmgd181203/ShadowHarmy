#!/usr/bin/env python3
"""Juicio Beru rango — flota sobre bóveda linear 1m (teatro de sombras).

Sin manos. Rankea por calor = efi_corta×w1 + efi_media×w2 + efi_larga×w3.

Perfiles de tiempo:
  reciente (default): 7d / 30d / 90d · pesos 20/50/30
  anual:              3d / 30d / 365d · pesos 20/50/30

Perfiles Beru (--beru-perfil):
  normal · feria

Matriz preparada (no arrancar sola):
  python scripts/preparar_teatro_beru_matriz.py
  python scripts/servir_teatro_live.py   # página ranking vivo

Ejemplo:
  python -u scripts/teatro_beru_rango_juicio.py --beru-perfil feria --perfil reciente --out data/coliseo/rango_juicio/matriz/feria_reciente
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from statistics import median
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core import beru_rango
from core import coliseo_boveda as bov
from core.teatro_beru_rango import simular_rango_juicio

OUT_DEFAULT = ROOT / "data" / "coliseo" / "rango_juicio"

PERFILES = {
    "reciente": {
        "corta_d": 7,
        "media_d": 30,
        "larga_d": 90,
        "pesos": (0.20, 0.50, 0.30),
        "stem": "juicio_rango_7_30_90",
    },
    "anual": {
        "corta_d": 3,
        "media_d": 30,
        "larga_d": 365,
        "pesos": (0.20, 0.50, 0.30),
        "stem": "juicio_rango_365d",
    },
}


def _duracion(segundos: float) -> str:
    total = max(0, int(segundos))
    horas, resto = divmod(total, 3600)
    minutos, segundos = divmod(resto, 60)
    if horas:
        return f"{horas}h{minutos:02d}m"
    if minutos:
        return f"{minutos}m{segundos:02d}s"
    return f"{segundos}s"


def _csv(texto: str) -> list[str]:
    return [x.strip().upper() for x in str(texto or "").split(",") if x.strip()]


def _ventana(candles: list[tuple], fin_ts: int, dias: int) -> list[tuple]:
    desde = fin_ts - max(1, int(dias)) * 86_400
    return [row for row in candles if int(row[0]) >= desde]


def _semaforo(rank: int, n: int) -> str:
    tercio = max(1, n // 3)
    if rank <= tercio:
        return "VERDE"
    if rank <= 2 * tercio:
        return "AMARILLO"
    return "ROJO"


def _calor(efi_c: float, efi_m: float, efi_l: float, pesos: tuple[float, float, float]) -> float:
    w1, w2, w3 = pesos
    return round(efi_c * w1 + efi_m * w2 + efi_l * w3, 6)


async def _juicio_async(
    *,
    corta_d: int,
    media_d: int,
    larga_d: int,
    pesos: tuple[float, float, float],
    fee_pct: float,
    only: list[str] | None,
    out: Path,
    beru_perfil: str = "normal",
    tiempo_perfil: str = "reciente",
) -> dict[str, Any]:
    con = bov.connect_market("linear")
    try:
        row = con.execute("SELECT MAX(ts) FROM candles").fetchone()
        fin_ts = int(row[0]) if row and row[0] is not None else 0
        bases_rows = con.execute(
            "SELECT DISTINCT base FROM candles ORDER BY base"
        ).fetchall()
        flota = [str(r[0]).upper() for r in bases_rows]
        if only:
            want = set(only)
            flota = [b for b in flota if b in want]

        total = len(flota) * 3
        hecho = 0
        t0 = time.monotonic()
        ranking: list[dict[str, Any]] = []
        print(
            f"\n[TEATRO RANGO] flota={len(flota)} · tramos={total} · "
            f"ventanas={corta_d}/{media_d}/{larga_d}d · "
            f"pesos={pesos[0]*100:.0f}/{pesos[1]*100:.0f}/{pesos[2]*100:.0f} · "
            f"fee={fee_pct*100:.3f}%",
            flush=True,
        )

        for activo in flota:
            candles = bov.load_candles(
                con,
                activo,
                since_ts=fin_ts - larga_d * 86_400,
                until_ts=fin_ts,
            )
            if len(candles) < 30:
                ranking.append({
                    "activo": activo,
                    "datos": "INSUFICIENTES",
                    "velas": len(candles),
                })
                hecho = min(total, hecho + 3)
                print(f"  {activo}: sin datos ({len(candles)} velas)", flush=True)
                continue

            ventanas = {
                "corta": _ventana(candles, fin_ts, min(corta_d, larga_d)),
                "media": _ventana(candles, fin_ts, min(media_d, larga_d)),
                "larga": candles,
            }
            etiquetas = {
                "corta": f"{corta_d}d",
                "media": f"{media_d}d",
                "larga": f"{larga_d}d",
            }
            resultados: dict[str, Any] = {}
            for key in ("corta", "media", "larga"):
                v = ventanas[key]
                print(
                    f"  [{hecho + 1}/{total}] {activo} · {etiquetas[key]} · {len(v):,} velas",
                    flush=True,
                )
                resultados[key] = await simular_rango_juicio(
                    v, activo=activo, fee_pct=fee_pct,
                )
                hecho = min(total, hecho + 1)
                trans = time.monotonic() - t0
                ritmo = hecho / trans if trans > 0 else 0.0
                eta = (total - hecho) / ritmo if ritmo > 0 else 0.0
                print(
                    f"    → cosechas={resultados[key]['cosechas']} · "
                    f"neto=${resultados[key]['botin_neto_usd']:.2f} · "
                    f"efi={resultados[key]['eficiencia']:.3f} · "
                    f"ETA ~{_duracion(eta)}",
                    flush=True,
                )

            calor = _calor(
                float(resultados["corta"]["eficiencia"]),
                float(resultados["media"]["eficiencia"]),
                float(resultados["larga"]["eficiencia"]),
                pesos,
            )
            ranking.append({
                "activo": activo,
                "datos": "OK",
                "calor": calor,
                "margen_usd": resultados["larga"]["margen_usd"],
                # aliases compat con informe anual
                "d3": resultados["corta"],
                "m30": resultados["media"],
                "horizonte": resultados["larga"],
                "corta": resultados["corta"],
                "media": resultados["media"],
                "larga": resultados["larga"],
            })
            _escribir_parcial(
                out,
                ranking,
                corta_d,
                media_d,
                larga_d,
                pesos,
                fee_pct,
                fin_ts,
                beru_perfil=beru_perfil,
                tiempo_perfil=tiempo_perfil,
            )
    finally:
        con.close()

    validos = sorted(
        (r for r in ranking if r.get("datos") == "OK"),
        key=lambda r: float(r["calor"]),
        reverse=True,
    )
    for pos, row in enumerate(validos, 1):
        row["rank_calor"] = pos
        row["semaforo"] = _semaforo(pos, len(validos))
    grises = [r for r in ranking if r.get("datos") != "OK"]
    geo = beru_rango.resumen_geometria()
    return {
        "meta": {
            "version": "teatro_beru_rango_juicio_v2",
            "ts_utc": datetime.now(timezone.utc).isoformat(),
            "actor": "Beru rango (trailing activacion + Oz callback)",
            "beru_perfil": beru_perfil,
            "tiempo_perfil": tiempo_perfil,
            "mercado": "linear_1m_boveda",
            "geometria": geo,
            "ventanas_dias": {
                "corta": corta_d,
                "media": media_d,
                "larga": larga_d,
            },
            "calor": {
                f"{corta_d}d": pesos[0],
                f"{media_d}d": pesos[1],
                f"{larga_d}d": pesos[2],
            },
            "metrica": "botin_neto_trail_Oz / (masa_vacio + masa_red)",
            "fee_pct": fee_pct,
            "fin_ts": fin_ts,
            "pase": "NO modifica manos ni pase",
        },
        "ranking": validos + grises,
        "candidatos_top20": [r["activo"] for r in validos[:20]],
        "candidatos_top50": [r["activo"] for r in validos[:50]],
    }


def _escribir_parcial(
    out: Path,
    ranking: list[dict[str, Any]],
    corta_d: int,
    media_d: int,
    larga_d: int,
    pesos: tuple[float, float, float],
    fee_pct: float,
    fin_ts: int,
    *,
    beru_perfil: str = "normal",
    tiempo_perfil: str = "reciente",
) -> None:
    """Ranking vivo para la página teatro_live (se reescribe tras cada Santo)."""
    out.mkdir(parents=True, exist_ok=True)
    validos = sorted(
        (r for r in ranking if r.get("datos") == "OK"),
        key=lambda r: float(r.get("calor") or 0),
        reverse=True,
    )
    live: list[dict[str, Any]] = []
    for pos, row in enumerate(validos, 1):
        live.append({
            "activo": row["activo"],
            "datos": "OK",
            "calor": float(row["calor"]),
            "rank_calor": pos,
            "semaforo": _semaforo(pos, max(len(validos), 1)),
            "efi_corta": float((row.get("corta") or row.get("d3") or {}).get("eficiencia") or 0),
            "efi_media": float((row.get("media") or row.get("m30") or {}).get("eficiencia") or 0),
            "efi_larga": float((row.get("larga") or row.get("horizonte") or {}).get("eficiencia") or 0),
            "cosechas_larga": int((row.get("larga") or row.get("horizonte") or {}).get("cosechas") or 0),
            "neto_larga": float((row.get("larga") or row.get("horizonte") or {}).get("botin_neto_usd") or 0),
        })
    grises = [
        {"activo": r["activo"], "datos": r.get("datos") or "INSUFICIENTES"}
        for r in ranking
        if r.get("datos") != "OK"
    ]
    path = out / "checkpoint_parcial.json"
    path.write_text(
        json.dumps(
            {
                "ts_utc": datetime.now(timezone.utc).isoformat(),
                "estado": "corriendo",
                "beru_perfil": beru_perfil,
                "tiempo_perfil": tiempo_perfil,
                "n": len(ranking),
                "n_ok": len(validos),
                "ventanas_dias": [corta_d, media_d, larga_d],
                "pesos": list(pesos),
                "fee_pct": fee_pct,
                "fin_ts": fin_ts,
                "geometria": beru_rango.resumen_geometria(),
                "ranking": live,
                "grises": grises,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def _write_md(report: dict[str, Any], path: Path) -> None:
    meta = report["meta"]
    geo = meta.get("geometria") or {}
    v = meta.get("ventanas_dias") or {}
    c_d, m_d, l_d = int(v.get("corta") or 7), int(v.get("media") or 30), int(v.get("larga") or 90)
    pesos = meta.get("calor") or {}
    lines = [
        "# Teatro Beru rango — juicio de sombras (reciente)",
        "",
        f"- Actor: **{meta['actor']}**",
        f"- Mercado: **linear 1m** · ventanas **{c_d}d / {m_d}d / {l_d}d**",
        f"- Calor: "
        + " · ".join(f"**{k}** {float(w)*100:.0f}%" for k, w in pesos.items()),
        f"- Geometría: Vacío {float(geo.get('vacio_pct') or 0)*100:.1f}% · "
        f"Oz {float(geo.get('oz_gap_pct') or 0)*100:.1f}% · "
        f"Red L {float(geo.get('red_activacion_long_pct') or geo.get('red_activacion_pct') or 0)*100:.1f}% / "
        f"S {float(geo.get('red_activacion_short_pct') or geo.get('red_activacion_pct') or 0)*100:.1f}% · "
        f"masa ${float(geo.get('masa_usd') or 0):.0f}/${float(geo.get('masa_red_usd') or 0):.0f} · "
        f"nace {geo.get('nacimiento') or '?'} · engorde {geo.get('engorde') or '?'}",
        "- Corona: **botín neto del trail Oz / margen (Vacío+Red)**",
        "- No toca manos ni el pase.",
        f"- Sello: `{meta.get('ts_utc') or ''}` · `{meta.get('version') or ''}`",
        "",
        f"| # | Santo | Calor | Luz | Efi {c_d}d | Efi {m_d}d | Efi {l_d}d | Cosechas {l_d}d | Neto {l_d}d |",
        "|--:|-------|------:|-----|-------:|--------:|------:|-----------:|-------:|",
    ]
    for row in report["ranking"]:
        if row.get("datos") != "OK":
            lines.append(f"| — | {row['activo']} | — | GRIS | — | — | — | — | — |")
            continue
        h = row.get("larga") or row["horizonte"]
        corta = row.get("corta") or row["d3"]
        media = row.get("media") or row["m30"]
        lines.append(
            f"| {row['rank_calor']} | {row['activo']} | {row['calor']:.3f} | "
            f"{row['semaforo']} | {corta['eficiencia']:.3f} | "
            f"{media['eficiencia']:.3f} | {h['eficiencia']:.3f} | "
            f"{h['cosechas']} | {h['botin_neto_usd']:.2f} |"
        )
    lines.extend([
        "",
        "## Candidatos top 20",
        "",
        ", ".join(report.get("candidatos_top20") or []) or "—",
        "",
    ])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="Juicio Beru rango sobre bóveda linear")
    ap.add_argument(
        "--perfil",
        default="reciente",
        choices=sorted(PERFILES.keys()),
        help="Ventanas: reciente=7/30/90 · anual=3/30/365",
    )
    ap.add_argument(
        "--beru-perfil",
        default="",
        choices=["", "normal", "feria"],
        help="Geometría Beru: normal | feria (default = BERU_RANGO_PERFIL / normal)",
    )
    ap.add_argument(
        "--horizonte",
        type=int,
        default=0,
        help="Compat: si >0 y sin override, fuerza perfil anual con esa larga",
    )
    ap.add_argument("--fee-pct", type=float, default=0.0006)
    ap.add_argument("--only", default="", help="Lista CSV de bases (opcional)")
    ap.add_argument("--out", default="", help="Carpeta de salida")
    args = ap.parse_args()

    import core.config as config

    beru_perfil = str(args.beru_perfil or "").strip().lower()
    if not beru_perfil:
        beru_perfil = str(getattr(config, "BERU_RANGO_PERFIL", "normal") or "normal")
    if beru_perfil not in ("normal", "feria"):
        beru_perfil = "normal"
    config.aplicar_perfil_beru_rango(beru_perfil)

    perfil_nombre = str(args.perfil or "reciente")
    if int(args.horizonte or 0) > 0 and perfil_nombre == "reciente":
        # Compat invocaciones viejas: --horizonte 365
        if int(args.horizonte) >= 180:
            perfil_nombre = "anual"
    perfil = dict(PERFILES[perfil_nombre])
    if int(args.horizonte or 0) > 0 and perfil_nombre == "anual":
        perfil["larga_d"] = int(args.horizonte)
        perfil["stem"] = f"juicio_rango_{int(args.horizonte)}d"

    corta_d = int(perfil["corta_d"])
    media_d = int(perfil["media_d"])
    larga_d = int(perfil["larga_d"])
    pesos = tuple(perfil["pesos"])  # type: ignore[arg-type]
    stem = str(perfil["stem"])
    if beru_perfil != "normal":
        stem = f"{stem}_{beru_perfil}"

    out = Path(args.out) if args.out else OUT_DEFAULT
    out.mkdir(parents=True, exist_ok=True)
    only = _csv(args.only) or None

    print("═" * 56, flush=True)
    print("  TEATRO DE SOMBRAS — Beru rango · bóveda linear", flush=True)
    print(
        f"  beru={beru_perfil} · tiempo={perfil_nombre} · "
        f"{corta_d}/{media_d}/{larga_d}d",
        flush=True,
    )
    print(f"  out={out}", flush=True)
    print("═" * 56, flush=True)

    t0 = time.monotonic()
    report = asyncio.run(
        _juicio_async(
            corta_d=corta_d,
            media_d=media_d,
            larga_d=larga_d,
            pesos=pesos,  # type: ignore[arg-type]
            fee_pct=float(args.fee_pct),
            only=only,
            out=out,
            beru_perfil=beru_perfil,
            tiempo_perfil=perfil_nombre,
        )
    )
    json_path = out / f"{stem}.json"
    md_path = out / f"{stem}.md"
    json_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8",
    )
    _write_md(report, md_path)

    # Marcar parcial como terminado (la web deja de decir "corriendo")
    parcial = out / "checkpoint_parcial.json"
    if parcial.exists():
        try:
            data = json.loads(parcial.read_text(encoding="utf-8"))
            data["estado"] = "hecho"
            data["informe_json"] = str(json_path.name)
            data["ts_fin_utc"] = datetime.now(timezone.utc).isoformat()
            parcial.write_text(
                json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8",
            )
        except Exception:
            pass

    ok = [r for r in report["ranking"] if r.get("datos") == "OK"]
    calores = [float(r["calor"]) for r in ok]
    comp = {
        "version": "teatro_beru_rango_juicio_v2",
        "beru_perfil": beru_perfil,
        "perfil": perfil_nombre,
        "ventanas_dias": [corta_d, media_d, larga_d],
        "pesos": list(pesos),
        "n_ok": len(ok),
        "mediana_calor": median(calores) if calores else 0.0,
        "top": (report.get("candidatos_top20") or [None])[0],
        "informe_md": str(md_path),
        "informe_json": str(json_path),
        "duracion_s": round(time.monotonic() - t0, 1),
    }
    (out / "comparativa.json").write_text(
        json.dumps(comp, ensure_ascii=False, indent=2) + "\n", encoding="utf-8",
    )
    print(
        f"\nOK · beru={beru_perfil} · {len(ok)} Santos · "
        f"mediana calor={comp['mediana_calor']:.3f} · "
        f"top={comp['top']} · {_duracion(comp['duracion_s'])}",
        flush=True,
    )
    print(f"  {md_path}", flush=True)
    print(f"  {json_path}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
