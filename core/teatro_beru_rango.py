"""Teatro visual Beru rango — velas de bóveda + crónica narrada.

Sin Bridge ni manos. Recorre OHLC (o→h→l→c), latea BeruRango y arma
una película HTML: gráfica que avanza + texto de qué hizo y por qué.
"""
from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core import beru_rango
from core import coliseo_boveda as bov
from generales.beru_rango import BeruRango

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "coliseo" / "rango_teatro"


@dataclass
class EventoTeatro:
    i: int
    t: int
    tipo: str
    titulo: str
    detalle: str
    precio: float
    niveles: dict[str, Any] = field(default_factory=dict)
    marca: dict[str, Any] | None = None


class _BelMudo:
    async def anotar(self, *_a, **_k):
        return None


class _Tank:
    def __init__(self) -> None:
        self.precios: dict[str, float] = {}


def _fmt_px(px: float) -> str:
    p = abs(float(px or 0))
    if p >= 1000:
        return f"{px:.2f}"
    if p >= 10:
        return f"{px:.4f}"
    if p >= 1:
        return f"{px:.5f}"
    return f"{px:.6f}"


def _utc(ts: int) -> str:
    return datetime.fromtimestamp(int(ts), tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def _niveles_de(
    beru,
    *,
    oz_fantasma: float | None = None,
    red_fantasma: float | None = None,
    dir_fantasma: str = "",
) -> dict[str, Any]:
    """Niveles según fase: dual solo al nacer; luego un lado + Oz/Red."""
    if beru is None:
        return {}
    cero = float(getattr(beru, "centro_local", 0) or 0)
    if cero <= 0:
        return {}
    vac = beru_rango.vacio_adan_pct()
    sang = beru_rango.sangre_contraria_pct()
    estado = str(getattr(beru, "estado", "") or "")
    d = str(getattr(beru, "direccion", "") or "").upper()
    sangre_lado = str(getattr(beru, "sangre_lado", "") or "").upper()
    oz = float(getattr(beru, "oz_adan", 0) or 0) or None
    red = float(getattr(beru, "red_adan", 0) or 0) or None
    masa = float(getattr(beru, "masa", 0) or 0) or beru_rango.masa_tramo_usd()

    out: dict[str, Any] = {
        "fase": "dual",
        "cero": cero,
        "oz": None,
        "red": None,
        "vacio_arriba": None,
        "vacio_abajo": None,
        "sangre": None,
        "contrario_1_2": None,
        "dir": d or None,
        "masa": None,
        "labels": {},
    }

    if estado == "CAZANDO" and oz:
        # Un tramo vivo: Oz + Red + 0. El otro flanco se pega a ±1,2 % de la Oz.
        out["fase"] = "caza"
        out["oz"] = oz
        out["red"] = red
        out["masa"] = masa
        out["dir"] = d
        if d == "SHORT":
            out["vacio_arriba"] = cero * (1 + vac)  # silbato que disparó
            out["contrario_1_2"] = oz * (1 - vac)  # otro lado pegado a la Oz
            out["labels"] = {
                "cero": "0",
                "oz": f"Oz trailing {d} ${masa:.0f}",
                "red": "Red",
                "vacio_arriba": "Vacío↑ (armo trail)",
                "contrario_1_2": "otro flanco",
            }
        else:
            out["vacio_abajo"] = cero * (1 - vac)
            out["contrario_1_2"] = oz * (1 + vac) if oz else None
            out["labels"] = {
                "cero": "0",
                "oz": f"Oz trailing {d} ${masa:.0f}",
                "red": "Red",
                "vacio_abajo": "Vacío↓ (armo trail)",
                "contrario_1_2": "otro flanco",
            }
        return out

    if estado == "ACECHANDO" and (
        bool(getattr(beru, "es_relevo_cazador", False)) or sangre_lado
    ):
        # Tras Oz: sangre 1,2 contraria + Red 0,7 mismo sentido (→ Beru $5).
        out["fase"] = "bifurca"
        masa_marca = float(getattr(beru, "ultima_masa_cosechada", 0) or 0) or beru_rango.masa_tramo_usd()
        out["oz"] = oz_fantasma
        out["red"] = float(getattr(beru, "red_adan", 0) or 0) or red_fantasma
        out["masa"] = beru_rango.masa_red_usd()
        out["dir"] = dir_fantasma or None
        if sangre_lado == "ABAJO":
            out["sangre"] = cero * (1 - sang)
        elif sangre_lado == "ARRIBA":
            out["sangre"] = cero * (1 + sang)
        out["labels"] = {
            "cero": "0 = Oz",
            "sangre": f"Sangre {sang*100:.1f}% → $10",
            "red": f"Red +{beru_rango.red_desde_oz_pct()*100:.1f}% → Beru $5",
            "oz": f"marca {dir_fantasma or 'OZ'} ${masa_marca:.0f}" if oz_fantasma else "",
        }
        return out

    # Nacimiento / acecho dual
    out["fase"] = "dual"
    out["vacio_arriba"] = cero * (1 + vac)
    out["vacio_abajo"] = cero * (1 - vac)
    out["labels"] = {
        "cero": "0",
        "vacio_arriba": f"Vacío +{vac*100:.1f}%",
        "vacio_abajo": f"Vacío -{vac*100:.1f}%",
    }
    return out


def _narrar_armar(beru, origen: str, precio: float, precio_antes: float) -> tuple[str, str]:
    d = str(beru.direccion or "")
    vac = beru_rango.vacio_adan_pct()
    trail = beru_rango.trailing_dist_pct()
    lado = "arriba" if "ARRIBA" in origen or d == "SHORT" else "abajo"
    oz = float(beru.oz_adan or 0)
    extremo = float(getattr(beru, "trail_extremo", 0) or precio)
    if origen == "RED":
        esc = int(getattr(beru, "rango_escalones_red", 0) or 0)
        titulo = f"Toco la Red — nace Beru {d} ${beru.masa:.0f} (escalon {esc})"
        detalle = (
            f"Precio {_fmt_px(precio_antes)} → {_fmt_px(precio)}. "
            f"Red de continuacion armo trailing {d} ${beru.masa:.2f}: "
            f"extremo {_fmt_px(extremo)}, Oz a {trail*100:.1f}% detras → {_fmt_px(oz)}. "
            f"Cuando el precio retroceda/rebote a la Oz, detona la entrada."
        )
        return titulo, detalle
    if origen.startswith("VACIO"):
        titulo = f"Toco el Vacio de Adan {lado} — arma trailing"
        detalle = (
            f"El precio vino de {_fmt_px(precio_antes)} a {_fmt_px(precio)}. "
            f"Vacío ±{vac*100:.1f}% arma trailing {d} ${beru.masa:.2f}: "
            f"extremo {_fmt_px(extremo)}, Oz = trailing {trail*100:.1f}% → {_fmt_px(oz)}. "
            f"Si sigue subiendo/bajando, la Oz persigue; al tocar la Oz entra el {d}."
        )
    else:
        titulo = f"Toco la sangre contraria ({getattr(beru, 'sangre_lado', lado)})"
        detalle = (
            f"Precio {_fmt_px(precio_antes)} → {_fmt_px(precio)}. "
            f"Sangre a {beru_rango.sangre_contraria_pct()*100:.1f}% arma trailing {d} "
            f"${beru.masa:.2f}: Oz {_fmt_px(oz)} ({trail*100:.1f}% del extremo {_fmt_px(extremo)})."
        )
    return titulo, detalle


def _narrar_oz(
    beru,
    fill: float,
    precio_antes: float,
    *,
    direccion: str,
    masa: float,
    red_tramo: float,
) -> tuple[str, str]:
    lado = str(getattr(beru, "sangre_lado", "") or "")
    sang = beru_rango.sangre_contraria_pct()
    sangre_px = fill * (1 - sang) if lado == "ABAJO" else fill * (1 + sang)
    red_cont = float(getattr(beru, "red_adan", 0) or 0)
    titulo = f"Trailing Oz detono — {direccion} ${masa:.0f}"
    detalle = (
        f"El trailing 0,2% se disparo ({_fmt_px(precio_antes)} → Oz {_fmt_px(fill)}). "
        f"Entra {direccion} ${masa:.0f}. El 0 se mueve a {_fmt_px(fill)}. "
        f"Bifurcacion: sangre {lado} a {sang*100:.1f}% → {_fmt_px(sangre_px)} ($10), "
        f"o Red a {_fmt_px(red_cont)} (0,7%) → Beru $5 con otro trailing. "
        f"(Red del tramo previo {_fmt_px(red_tramo)})."
    )
    return titulo, detalle


def expandir_ohlc(
    candles: list[tuple[int, float, float, float, float]],
) -> list[tuple[int, float]]:
    """Cada vela → open, high, low, close (latidos de teatro, sin micro-pasos)."""
    out: list[tuple[int, float]] = []
    for ts, o, h, l, c in candles:
        t = int(ts)
        for px in (float(o), float(h), float(l), float(c)):
            if px > 0:
                out.append((t, px))
    return out


def cargar_velas(
    activo: str,
    *,
    dias: int = 3,
    market: str = "auto",
) -> tuple[list[tuple[int, float, float, float, float]], str]:
    """Bóveda linear si hay; si no spot. Mercado real de la casa de datos."""
    act = str(activo or "ETH").upper()
    mercados = []
    if market == "auto":
        mercados = ["linear", "spot"]
    else:
        mercados = [str(market).lower()]

    fin = None
    for m in mercados:
        path = bov.boveda_path(m)
        if not path.exists():
            continue
        con = bov.connect_market(m)
        try:
            n = bov.count_candles(con, act)
            if n < 30:
                continue
            fin_ts = bov.max_ts(con, act)
            if fin_ts is None:
                continue
            since = int(fin_ts) - max(1, int(dias)) * 86400
            rows = bov.load_candles(con, act, since_ts=since, until_ts=fin_ts)
            if len(rows) >= 30:
                return rows, m
        finally:
            con.close()
    raise FileNotFoundError(
        f"Sin velas suficientes de {act} en bóveda linear/spot "
        f"(pide dias={dias}). Corre la noche de historial o baja dias."
    )


async def simular_rango(
    candles: list[tuple[int, float, float, float, float]],
    *,
    activo: str = "ETH",
) -> dict[str, Any]:
    """Recorre latidos, construye precios + eventos narrados."""
    latidos = expandir_ohlc(candles)
    if not latidos:
        raise ValueError("sin latidos")

    tank = _Tank()
    g = BeruRango(object(), _BelMudo(), tank, bridge=None)
    import core.config as config
    prev = getattr(config, "BERU_RANGO_BITACORA", True)
    config.BERU_RANGO_BITACORA = False

    precios: list[dict[str, float | int]] = []
    eventos: list[EventoTeatro] = []
    marcas: list[dict[str, Any]] = []
    oz_fantasma: float | None = None
    red_fantasma: float | None = None
    dir_fantasma = ""

    px0 = float(latidos[0][1])
    t0 = int(latidos[0][0])
    await g.despertar(px0, activo=activo)
    beru = g.vivo
    assert beru is not None
    vac = beru_rango.vacio_adan_pct()
    eventos.append(EventoTeatro(
        i=0, t=t0, tipo="WAKE",
        titulo="Nace el Beru rango",
        detalle=(
            f"0 local = {_fmt_px(px0)} ({_utc(t0)}). "
            f"Vacío de Adán dual ±{vac*100:.1f}% "
            f"(arriba {_fmt_px(px0*(1+vac))}, abajo {_fmt_px(px0*(1-vac))}). "
            f"Masa por tramo ${beru_rango.masa_tramo_usd():.2f}. "
            f"Al tocar un lado, el otro se pega a ±1,2% de la Oz. "
            f"Un vivo, sin engorde."
        ),
        precio=px0,
        niveles=_niveles_de(beru),
    ))
    precios.append({"t": t0, "px": px0})
    px_prev = px0
    cosechas = 0

    try:
        for i, (ts, px) in enumerate(latidos):
            if i == 0:
                continue
            tank.precios[f"{activo.upper()}USDT_LINEAL"] = px
            tank.precios[f"{activo.upper()}USDT_SPOT"] = px
            # Snapshot Oz/Red antes de cosechar (el vivo los limpia)
            beru_pre = g.vivo
            oz_pre = float(getattr(beru_pre, "oz_adan", 0) or 0) if beru_pre else 0.0
            red_pre = float(getattr(beru_pre, "red_adan", 0) or 0) if beru_pre else 0.0
            dir_pre = str(getattr(beru_pre, "direccion", "") or "") if beru_pre else ""
            masa_pre = float(getattr(beru_pre, "masa", 0) or 0) if beru_pre else 0.0

            r = await g.pulso(px)
            precios.append({"t": int(ts), "px": float(px)})
            ev = str(r.get("evento") or "")
            beru = g.vivo
            if ev in ("ACECHO", "CAZA") or not beru:
                px_prev = px
                continue
            if ev.startswith("ARMAR_"):
                if ev == "ARMAR_SANGRE":
                    titulo, detalle = _narrar_armar(beru, "SANGRE", px, px_prev)
                elif ev == "ARMAR_RED":
                    titulo, detalle = _narrar_armar(beru, "RED", px, px_prev)
                elif ev == "ARMAR_ARRIBA":
                    titulo, detalle = _narrar_armar(beru, "VACIO_ARRIBA", px, px_prev)
                elif ev == "ARMAR_ABAJO":
                    titulo, detalle = _narrar_armar(beru, "VACIO_ABAJO", px, px_prev)
                else:
                    titulo, detalle = _narrar_armar(beru, ev, px, px_prev)
                marca_red = None
                if ev == "ARMAR_RED":
                    marca_red = {
                        "i": i,
                        "t": int(ts),
                        "px": float(beru.oz_adan or px),
                        "dir": str(beru.direccion or ""),
                        "masa": float(beru.masa or 5),
                        "red": float(beru.red_adan or 0),
                        "label": f"{beru.direccion} ${float(beru.masa or 5):.0f} (Red)",
                    }
                    marcas.append(marca_red)
                eventos.append(EventoTeatro(
                    i=i, t=int(ts), tipo=ev, titulo=titulo, detalle=detalle,
                    precio=float(px),
                    niveles=_niveles_de(
                        beru,
                        oz_fantasma=oz_fantasma,
                        red_fantasma=red_fantasma,
                        dir_fantasma=dir_fantasma,
                    ),
                    marca=marca_red,
                ))
            elif ev == "OZ_COSECHA":
                cosechas += 1
                fill = float(r.get("cero") or beru.centro_local or px)
                d_mark = dir_pre or str(getattr(beru, "ultima_hoz_direccion", "") or "")
                red_mark = red_pre or float(getattr(beru, "red_adan", 0) or fill)
                masa_mark = float(r.get("masa_hecha") or masa_pre or beru_rango.masa_tramo_usd())
                oz_fantasma = fill
                red_fantasma = float(getattr(beru, "red_adan", 0) or red_mark)
                dir_fantasma = d_mark
                titulo, detalle = _narrar_oz(
                    beru, fill, px_prev,
                    direccion=d_mark or "OZ",
                    masa=masa_mark,
                    red_tramo=red_mark,
                )
                marca = {
                    "i": i,
                    "t": int(ts),
                    "px": fill,
                    "dir": d_mark,
                    "masa": masa_mark,
                    "red": red_fantasma,
                    "label": f"{d_mark or 'OZ'} ${masa_mark:.0f}",
                }
                marcas.append(marca)
                eventos.append(EventoTeatro(
                    i=i, t=int(ts), tipo=ev, titulo=titulo, detalle=detalle,
                    precio=fill,
                    niveles=_niveles_de(
                        beru,
                        oz_fantasma=oz_fantasma,
                        red_fantasma=red_fantasma,
                        dir_fantasma=dir_fantasma,
                    ),
                    marca=marca,
                ))
            px_prev = px
    finally:
        config.BERU_RANGO_BITACORA = prev

    return {
        "activo": str(activo).upper(),
        "n_velas": len(candles),
        "n_latidos": len(latidos),
        "n_eventos": len(eventos),
        "cosechas": cosechas,
        "geometria": beru_rango.resumen_geometria(),
        "precios": precios,
        "marcas": marcas,
        "eventos": [
            {
                "i": e.i,
                "t": e.t,
                "tipo": e.tipo,
                "titulo": e.titulo,
                "detalle": e.detalle,
                "precio": e.precio,
                "utc": _utc(e.t),
                "niveles": e.niveles,
                "marca": e.marca,
            }
            for e in eventos
        ],
    }


def escribir_cronica_md(sim: dict[str, Any], path: Path) -> None:
    lines = [
        f"# Teatro Beru rango — {sim['activo']}",
        "",
        f"- Velas: **{sim['n_velas']}** · Latidos OHLC: **{sim['n_latidos']}**",
        f"- Eventos: **{sim['n_eventos']}** · Cosechas Oz: **{sim['cosechas']}**",
        f"- Geometría: Vacío {sim['geometria']['vacio_pct']*100:.1f}% · "
        f"Oz gap {sim['geometria']['oz_gap_pct']*100:.1f}% · "
        f"Red +{sim['geometria']['red_desde_oz_pct']*100:.1f}% · "
        f"masa ${sim['geometria']['masa_usd']:.0f}",
        "",
        "## Cronica",
        "",
    ]
    for e in sim["eventos"]:
        lines.append(f"### {e['utc']} — {e['titulo']}")
        lines.append("")
        lines.append(e["detalle"])
        lines.append("")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def escribir_html(sim: dict[str, Any], path: Path) -> None:
    """Película autocontenida: play / velocidad / gráfica + narración."""
    payload = json.dumps(sim, ensure_ascii=False)
    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8"/>
<title>Teatro Beru rango — {sim['activo']}</title>
<style>
  :root {{ --bg:#0f1419; --fg:#e7ecf1; --muted:#8b9aab; --oz:#e8c547; --red:#4ea1ff; --cero:#c4d0dc; --ok:#6bcf7f; --sangre:#f07178; --otro:#c3a6ff; }}
  * {{ box-sizing: border-box; }}
  body {{ margin:0; font-family: "Segoe UI", system-ui, sans-serif; background:var(--bg); color:var(--fg); }}
  header {{ padding:12px 18px; border-bottom:1px solid #243040; }}
  header h1 {{ margin:0 0 4px; font-size:1.15rem; font-weight:600; }}
  header p {{ margin:0; color:var(--muted); font-size:0.85rem; }}
  .layout {{ display:grid; grid-template-columns: 1.45fr 1fr; gap:0; height: calc(100vh - 120px); }}
  @media (max-width: 900px) {{ .layout {{ grid-template-columns:1fr; height:auto; }} }}
  .pane {{ padding:12px 16px; overflow:hidden; display:flex; flex-direction:column; }}
  #chart {{ width:100%; flex:1; min-height:320px; background:#121a22; border-radius:8px; border:1px solid #243040; }}
  .controls {{ display:flex; flex-wrap:wrap; gap:8px; align-items:center; margin-top:10px; }}
  button, select {{ background:#1c2834; color:var(--fg); border:1px solid #344556; border-radius:6px; padding:6px 12px; cursor:pointer; }}
  button:hover {{ border-color:#5a7a9a; }}
  input[type=range] {{ flex:1; min-width:120px; }}
  #narracion {{ flex:1; overflow:auto; font-size:0.9rem; line-height:1.45; padding-right:6px; }}
  .card {{ background:#151d27; border:1px solid #2a3a4c; border-radius:8px; padding:10px 12px; margin-bottom:8px; }}
  .card.active {{ border-color:var(--oz); box-shadow:0 0 0 1px var(--oz); }}
  .card .meta {{ color:var(--muted); font-size:0.75rem; margin-bottom:4px; }}
  .card .titulo {{ font-weight:600; margin-bottom:4px; }}
  .leyenda {{ font-size:0.72rem; color:var(--muted); margin-top:6px; line-height:1.6; }}
  .leyenda span {{ margin-right:10px; white-space:nowrap; }}
  .dot {{ display:inline-block; width:8px; height:8px; border-radius:50%; margin-right:4px; }}
</style>
</head>
<body>
<header>
  <h1>Teatro Beru rango — {sim['activo']}</h1>
  <p>Vacío ±1,2 arma trailing Oz 0,2 · SHORT al bajar / LONG al subir · Red 0,7 → Beru $5 · sangre 1,2.
     Cosechas: {sim['cosechas']} · Eventos: {sim['n_eventos']} · Latidos: {sim['n_latidos']}</p>
</header>
<div class="layout">
  <div class="pane">
    <canvas id="chart"></canvas>
    <div class="leyenda">
      <span><i class="dot" style="background:var(--cero)"></i>0</span>
      <span><i class="dot" style="background:var(--oz)"></i>Oz / marca</span>
      <span><i class="dot" style="background:var(--red)"></i>Red</span>
      <span><i class="dot" style="background:#a78bfa"></i>Vacío</span>
      <span><i class="dot" style="background:var(--sangre)"></i>Sangre</span>
      <span><i class="dot" style="background:var(--otro)"></i>otro ±1,2 Oz</span>
      <span><i class="dot" style="background:var(--ok)"></i>precio</span>
    </div>
    <div class="controls">
      <button id="btnPlay" type="button">Play</button>
      <button id="btnReset" type="button">Inicio</button>
      <label>Velocidad
        <select id="speed">
          <option value="40">lenta</option>
          <option value="16" selected>media</option>
          <option value="4">rapida</option>
          <option value="1">muy rapida</option>
        </select>
      </label>
      <input id="scrub" type="range" min="0" max="100" value="0"/>
      <span id="clock" style="color:var(--muted); font-size:0.8rem;"></span>
    </div>
  </div>
  <div class="pane">
    <div id="narracion"></div>
  </div>
</div>
<script>
const DATA = {payload};
const precios = DATA.precios;
const eventos = DATA.eventos;
const marcas = DATA.marcas || [];
const byIndex = {{}};
eventos.forEach(e => {{ byIndex[e.i] = e; }});

const canvas = document.getElementById('chart');
const ctx = canvas.getContext('2d');
const narr = document.getElementById('narracion');
const scrub = document.getElementById('scrub');
const clock = document.getElementById('clock');
const btnPlay = document.getElementById('btnPlay');
const btnReset = document.getElementById('btnReset');
const speedSel = document.getElementById('speed');

let idx = 0;
let playing = false;
let timer = null;

function resize() {{
  const r = canvas.getBoundingClientRect();
  canvas.width = Math.floor(r.width * devicePixelRatio);
  canvas.height = Math.floor(r.height * devicePixelRatio);
  ctx.setTransform(devicePixelRatio, 0, 0, devicePixelRatio, 0, 0);
  draw();
}}
window.addEventListener('resize', resize);

function nivelesActuales() {{
  let niv = null;
  for (let k = eventos.length - 1; k >= 0; k--) {{
    if (eventos[k].i <= idx) {{ niv = eventos[k].niveles; break; }}
  }}
  return niv || {{}};
}}

function draw() {{
  const w = canvas.clientWidth, h = canvas.clientHeight;
  ctx.clearRect(0, 0, w, h);
  if (!precios.length) return;
  const slice = precios.slice(0, idx + 1);
  const n = Math.max(40, Math.min(slice.length, 800));
  const view = slice.slice(-n);
  const viewStart = slice.length - view.length;
  let mn = Infinity, mx = -Infinity;
  view.forEach(p => {{ mn = Math.min(mn, p.px); mx = Math.max(mx, p.px); }});
  const niv = nivelesActuales();
  const keys = ['cero','oz','red','vacio_arriba','vacio_abajo','sangre','contrario_1_2'];
  keys.forEach(k => {{
    const v = niv[k];
    if (v != null && v > 0) {{ mn = Math.min(mn, v); mx = Math.max(mx, v); }}
  }});
  marcas.forEach(m => {{
    if (m.i <= idx && m.px > 0) {{ mn = Math.min(mn, m.px); mx = Math.max(mx, m.px); if (m.red) {{ mn = Math.min(mn, m.red); mx = Math.max(mx, m.red); }} }}
  }});
  const pad = (mx - mn) * 0.1 || 1;
  mn -= pad; mx += pad;
  const y = (px) => h - 28 - ((px - mn) / (mx - mn)) * (h - 48);
  const x = (i) => 10 + (i / Math.max(1, view.length - 1)) * (w - 20);

  function hline(px, color, dash, label, width) {{
    if (px == null || !(px > 0)) return;
    ctx.beginPath();
    ctx.strokeStyle = color;
    ctx.lineWidth = width || 1.4;
    ctx.setLineDash(dash || []);
    const yy = y(px);
    ctx.moveTo(10, yy); ctx.lineTo(w - 10, yy); ctx.stroke();
    ctx.setLineDash([]);
    if (label) {{
      ctx.fillStyle = color;
      ctx.font = '600 11px Segoe UI, sans-serif';
      ctx.fillText(label, 14, Math.max(12, yy - 4));
    }}
  }}

  const labels = niv.labels || {{}};
  hline(niv.vacio_arriba, '#a78bfa', [5,4], labels.vacio_arriba);
  hline(niv.vacio_abajo, '#a78bfa', [5,4], labels.vacio_abajo);
  hline(niv.contrario_1_2, '#c3a6ff', [2,4], labels.contrario_1_2, 1.2);
  hline(niv.sangre, '#f07178', [6,3], labels.sangre, 1.6);
  hline(niv.cero, '#c4d0dc', [], labels.cero || '0', 1.5);
  hline(niv.red, '#4ea1ff', [], labels.red || 'Red', 1.6);
  hline(niv.oz, '#e8c547', [], labels.oz || 'Oz', 2);

  // Marcas de cosecha (SHORT/LONG $10) — persistentes
  marcas.forEach(m => {{
    if (m.i > idx) return;
    const localI = m.i - viewStart;
    const yy = y(m.px);
    const xx = (localI >= 0 && localI < view.length) ? x(localI) : (w - 24);
    // Red fantasma del tramo cosechado
    if (m.red) {{
      ctx.beginPath();
      ctx.strokeStyle = 'rgba(78,161,255,0.35)';
      ctx.lineWidth = 1;
      ctx.setLineDash([3,3]);
      ctx.moveTo(10, y(m.red)); ctx.lineTo(w - 10, y(m.red)); ctx.stroke();
      ctx.setLineDash([]);
    }}
    ctx.fillStyle = '#e8c547';
    ctx.beginPath();
    ctx.moveTo(xx, yy - 7);
    ctx.lineTo(xx + 6, yy);
    ctx.lineTo(xx, yy + 7);
    ctx.lineTo(xx - 6, yy);
    ctx.closePath();
    ctx.fill();
    ctx.fillStyle = '#e8c547';
    ctx.font = '700 11px Segoe UI, sans-serif';
    const lab = m.label || ((m.dir || 'OZ') + ' $' + (m.masa || 10));
    ctx.fillText(lab, Math.min(xx + 8, w - 90), yy - 8);
  }});

  ctx.beginPath();
  ctx.strokeStyle = '#6bcf7f';
  ctx.lineWidth = 1.6;
  view.forEach((p, i) => {{
    const xx = x(i), yy = y(p.px);
    if (i === 0) ctx.moveTo(xx, yy); else ctx.lineTo(xx, yy);
  }});
  ctx.stroke();
  const last = view[view.length - 1];
  if (last) {{
    ctx.fillStyle = '#6bcf7f';
    ctx.beginPath();
    ctx.arc(x(view.length - 1), y(last.px), 4, 0, Math.PI * 2);
    ctx.fill();
  }}
}}

function utc(ts) {{
  try {{ return new Date(ts * 1000).toISOString().replace('T',' ').slice(0,16) + ' UTC'; }}
  catch {{ return String(ts); }}
}}

function renderNarr() {{
  const shown = eventos.filter(e => e.i <= idx);
  narr.innerHTML = shown.map((e, j) => {{
    const active = (j === shown.length - 1);
    return `<div class="card ${{active ? 'active' : ''}}" data-i="${{e.i}}">
      <div class="meta">${{e.utc || utc(e.t)}} · ${{e.tipo}} · px ${{Number(e.precio).toFixed(5)}}</div>
      <div class="titulo">${{e.titulo}}</div>
      <div>${{e.detalle}}</div>
    </div>`;
  }}).join('');
  if (shown.length) {{
    const last = narr.querySelector('.card:last-child');
    if (last) last.scrollIntoView({{ behavior: 'smooth', block: 'nearest' }});
  }}
}}

function setIdx(v) {{
  idx = Math.max(0, Math.min(precios.length - 1, v|0));
  scrub.value = String(idx);
  const p = precios[idx];
  clock.textContent = p ? (utc(p.t) + ' · ' + Number(p.px).toFixed(5)) : '';
  draw();
  if (byIndex[idx] || idx === 0) renderNarr();
  else if (idx % 20 === 0) renderNarr();
}}

function tick() {{
  if (!playing) return;
  const step = Math.max(1, Math.floor(8 / Math.max(1, Number(speedSel.value) / 8)));
  if (idx >= precios.length - 1) {{ playing = false; btnPlay.textContent = 'Play'; return; }}
  setIdx(idx + step);
  for (let j = idx; j < Math.min(precios.length, idx + 50); j++) {{
    if (byIndex[j]) {{ setIdx(j); break; }}
  }}
  timer = setTimeout(tick, Number(speedSel.value));
}}

btnPlay.onclick = () => {{
  playing = !playing;
  btnPlay.textContent = playing ? 'Pausa' : 'Play';
  if (playing) tick();
}};
btnReset.onclick = () => {{ playing = false; btnPlay.textContent = 'Play'; setIdx(0); renderNarr(); }};
scrub.max = String(Math.max(0, precios.length - 1));
scrub.oninput = () => {{ playing = false; btnPlay.textContent = 'Play'; setIdx(Number(scrub.value)); renderNarr(); }};

resize();
setIdx(0);
renderNarr();
</script>
</body>
</html>
"""
    path.write_text(html, encoding="utf-8")


async def correr_teatro(
    *,
    activo: str = "HYPE",
    dias: int = 3,
    market: str = "auto",
    out_dir: Path | None = None,
) -> dict[str, Any]:
    out = Path(out_dir or OUT_DIR)
    out.mkdir(parents=True, exist_ok=True)
    candles, fuente = cargar_velas(activo, dias=dias, market=market)
    sim = await simular_rango(candles, activo=activo)
    sim["fuente_velas"] = fuente
    sim["dias"] = dias
    stem = f"{activo.upper()}_{dias}d"
    json_path = out / f"teatro_{stem}.json"
    md_path = out / f"cronica_{stem}.md"
    html_path = out / f"teatro_{stem}.html"
    json_path.write_text(json.dumps(sim, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    escribir_cronica_md(sim, md_path)
    escribir_html(sim, html_path)
    sim["paths"] = {
        "json": str(json_path),
        "cronica": str(md_path),
        "html": str(html_path),
    }
    return sim
