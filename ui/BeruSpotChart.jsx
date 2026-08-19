import { useEffect, useMemo, useRef, useState } from "react";
import { createChart } from "lightweight-charts";
import { fmtUsd, fmtNum, decimalesPrecio } from "./beruAssetDetailModel.js";
import { marcaAguaManto, reglaEnPunto } from "./beruMantoRegla.js";

const KLINE_URL = "/data/beru_kline.json";

const COLOR = {
  manto: "#f8fafc",
  wake: "#9ca3af",
  vacio: "#ef4444",
  oz: "#fbbf24",
  red: "#3b82f6",
  red_engorde: "#3b82f6",
  centro: "#f8fafc",
  last: "#cbd5e1",
  buy: "#34d399",
  sell: "#f87171",
};

const LEYENDA = [
  { rol: "manto", label: "Manto" },
  { rol: "wake", label: "Wake" },
  { rol: "vacio", label: "Vacío" },
  { rol: "oz", label: "Hoz" },
  { rol: "red", label: "Red" },
  { rol: "last", label: "Last" },
];

const INTERVALOS = [
  { id: "15", label: "15m" },
  { id: "60", label: "1h" },
  { id: "240", label: "4h" },
];

const HIT = 28;
const UMBRAL_ARRASTRE = 8;
const CHIP_W = 152;
const CHIP_H = 78;

function esRolManto(rol) {
  return rol === "manto" || rol === "centro";
}

function fmtUsdSigned(n) {
  const v = Number(n);
  if (!Number.isFinite(v)) return "—";
  const abs = fmtUsd(Math.abs(v));
  if (Math.abs(v) < 1e-9) return abs;
  return v > 0 ? `+${abs}` : `−${abs}`;
}

function fmtPctSigned(n) {
  const v = Number(n);
  if (!Number.isFinite(v)) return "—";
  const body = `${Math.abs(v).toFixed(2)}%`;
  if (Math.abs(v) < 1e-9) return body;
  return v > 0 ? `+${body}` : `−${body}`;
}

function idNivel(n) {
  const id = String(n?.id || "").trim();
  if (id) return id;
  return `${n.rol}:${Number(n.precio).toFixed(6)}`;
}

function optsNivel(n) {
  const esManto = esRolManto(n.rol);
  const esVacio = n.rol === "vacio";
  const esWake = n.rol === "wake";
  return {
    price: n.precio,
    color: COLOR[n.rol] || COLOR.manto,
    lineWidth: esManto || n.rol === "red_engorde" ? 2 : 1,
    lineStyle: esWake ? 1 : esManto || esVacio ? 2 : 0,
    axisLabelVisible: !esWake,
    title: "",
  };
}

function datosVelas(rows) {
  return (rows || []).map((v) => ({
    time: Number(v.time),
    open: Number(v.open),
    high: Number(v.high),
    low: Number(v.low),
    close: Number(v.close),
  }));
}

function colocarFicha(x, y, boxW, boxH, { parked }) {
  let left;
  let top;
  if (parked) {
    left = 10;
    top = y - CHIP_H / 2;
  } else {
    left = x > boxW * 0.55 ? x - 16 - CHIP_W : x + 16;
    top = y - CHIP_H - 14;
    if (top < 8) top = y + 18;
  }
  left = Math.max(8, Math.min(left, boxW - CHIP_W - 8));
  top = Math.max(8, Math.min(top, boxH - CHIP_H - 8));
  return { left, top };
}

/**
 * Velas spot + rayas del combate Beru.
 * reglaManto: metro nativo (asa + simulación + ficha al lado del dedo).
 */
export default function BeruSpotChart({
  symbol,
  grafica,
  manto = null,
  altura = 300,
  llenar = false,
  reglaManto = false,
}) {
  const wrapRef = useRef(null);
  const paneRef = useRef(null);
  const apiRef = useRef(null);
  const liveRef = useRef({});
  const nivelesRef = useRef([]);
  const dragRef = useRef(false);
  const simRef = useRef(null);
  const armadoRef = useRef(false);
  const originYRef = useRef(0);
  const startLineYRef = useRef(0);
  const sesionSoloArmarRef = useRef(false);
  const [iv, setIv] = useState("15");
  const [velas, setVelas] = useState([]);
  const [meta, setMeta] = useState(null);
  const [error, setError] = useState("");
  const [asaY, setAsaY] = useState(null);
  const [simPrecio, setSimPrecio] = useState(null);
  const [ficha, setFicha] = useState(null);
  const [etiquetas, setEtiquetas] = useState([]);
  const [marcasCaza, setMarcasCaza] = useState([]);
  const [armado, setArmado] = useState(false);

  const niveles = useMemo(() => {
    const raw = Array.isArray(grafica?.niveles) ? grafica.niveles : [];
    const seen = new Set();
    const out = [];
    for (const n of raw) {
      const precio = Number(n?.precio);
      const rol = String(n?.rol || "");
      if (!(precio > 0) || rol === "spot") continue;
      if (rol === "oz" && !n.carta_colgada) continue;
      const key = `${rol}:${precio.toFixed(6)}`;
      if (seen.has(key)) continue;
      seen.add(key);
      out.push({ ...n, precio, rol });
      if (out.length >= 12) break;
    }
    return out;
  }, [grafica]);

  const cazas = useMemo(() => {
    const raw = Array.isArray(grafica?.cazas) ? grafica.cazas : [];
    return raw.filter((c) => Number(c?.precio) > 0 && Number(c?.ts) > 0);
  }, [grafica]);
  const cazasRef = useRef([]);
  cazasRef.current = cazas;
  const velasRef = useRef([]);
  velasRef.current = velas;

  const hayVelas = velas.length > 0;
  const mantoReal = useMemo(() => {
    const n = niveles.find((x) => esRolManto(x.rol));
    const c = n?.precio > 0 ? n.precio : Number(grafica?.centro_manto || manto?.cero || 0);
    return c > 0 ? c : 0;
  }, [niveles, grafica?.centro_manto, manto?.cero]);

  nivelesRef.current = niveles;
  liveRef.current = { reglaManto, mantoReal, simPrecio, manto, armado };

  const encajarRef = useRef(true);

  useEffect(() => {
    let alive = true;
    const s = String(symbol || "ETH").toUpperCase();
    encajarRef.current = true;
    setVelas([]);
    async function load() {
      setError("");
      try {
        const res = await fetch(
          `${KLINE_URL}?symbol=${encodeURIComponent(s)}&interval=${iv}&limit=240&t=${Date.now()}`,
          { cache: "no-store" },
        );
        const data = res.ok ? await res.json() : null;
        if (!alive) return;
        const rows = Array.isArray(data?.velas) ? data.velas : [];
        setVelas((prev) => {
          if (
            prev.length === rows.length &&
            prev.length > 0 &&
            Number(prev[0]?.time) === Number(rows[0]?.time) &&
            Number(prev[prev.length - 1]?.time) === Number(rows[rows.length - 1]?.time) &&
            Number(prev[prev.length - 1]?.close) === Number(rows[rows.length - 1]?.close) &&
            Number(prev[prev.length - 1]?.high) === Number(rows[rows.length - 1]?.high)
          ) {
            return prev;
          }
          return rows;
        });
        setMeta(data);
        if (!rows.length) setError(data?.error || "Sin velas aún");
      } catch (e) {
        if (!alive) return;
        setVelas([]);
        setError(String(e?.message || e));
      }
    }
    load();
    const t = setInterval(load, 30000);
    return () => {
      alive = false;
      clearInterval(t);
    };
  }, [symbol, iv]);

  useEffect(() => {
    const el = wrapRef.current;
    if (!el || !hayVelas) return undefined;

    const h = llenar ? Math.max(180, el.clientHeight || altura) : altura;
    const chart = createChart(el, {
      width: el.clientWidth,
      height: h,
      layout: {
        background: { color: "#0a0c10" },
        textColor: "#94a3b8",
      },
      grid: {
        vertLines: { color: "#ffffff10" },
        horzLines: { color: "#ffffff10" },
      },
      rightPriceScale: { borderColor: "#ffffff18" },
      timeScale: {
        borderColor: "#ffffff18",
        timeVisible: true,
        secondsVisible: false,
        lockVisibleTimeRangeOnResize: true,
      },
      crosshair: { mode: 0 },
    });
    const prec = Number.isInteger(Number(meta?.precision)) ? Number(meta.precision) : 4;
    const move = Number(meta?.min_move) > 0 ? Number(meta.min_move) : Number((10 ** -prec).toFixed(prec));
    const series = chart.addCandlestickSeries({
      upColor: "#34d399",
      downColor: "#fb7185",
      borderVisible: false,
      wickUpColor: "#34d399",
      wickDownColor: "#fb7185",
      lastValueVisible: true,
      priceLineVisible: true,
      priceLineColor: COLOR.last,
      priceLineWidth: 1,
      priceLineStyle: 2,
      priceFormat: {
        type: "price",
        precision: Math.max(0, Math.min(10, prec)),
        minMove: move,
      },
      autoscaleInfoProvider: (original) => {
        const def = original();
        if (!def?.priceRange) return def;
        if (encajarRef.current === false) return def;
        let min = def.priceRange.minValue;
        let max = def.priceRange.maxValue;
        for (const n of nivelesRef.current) {
          if (n.precio > 0) {
            min = Math.min(min, n.precio);
            max = Math.max(max, n.precio);
          }
        }
        const pad = (max - min) * 0.05 || Math.abs(max) * 0.002;
        return { ...def, priceRange: { minValue: min - pad, maxValue: max + pad } };
      },
    });

    const lines = new Map();
    let mantoLines = [];
    let ghostLine = null;

    function setMantoIlumina(on) {
      for (const line of mantoLines) {
        line.applyOptions({
          color: on ? "#ffffff" : COLOR.manto,
          lineWidth: on ? 3 : 2,
          lineStyle: on ? 0 : 2,
        });
      }
    }

    function setGhost(price) {
      if (!(price > 0)) {
        if (ghostLine) {
          try {
            series.removePriceLine(ghostLine);
          } catch {
            /* ignore */
          }
          ghostLine = null;
        }
        return;
      }
      if (!ghostLine) {
        ghostLine = series.createPriceLine({
          price,
          color: "#ffffff",
          lineWidth: 2,
          lineStyle: 0,
          axisLabelVisible: true,
          title: "",
        });
      } else {
        ghostLine.applyOptions({ price });
      }
    }

    function syncRayas() {
      const next = nivelesRef.current || [];
      const seen = new Set();
      const mantos = [];
      for (const n of next) {
        const id = idNivel(n);
        seen.add(id);
        const opts = optsNivel(n);
        const prev = lines.get(id);
        if (prev) prev.applyOptions(opts);
        else lines.set(id, series.createPriceLine(opts));
        if (esRolManto(n.rol)) mantos.push(lines.get(id));
      }
      for (const [id, line] of Array.from(lines.entries())) {
        if (seen.has(id)) continue;
        try {
          series.removePriceLine(line);
        } catch {
          /* ignore */
        }
        lines.delete(id);
      }
      mantoLines = mantos;
      if (liveRef.current.armado) setMantoIlumina(true);
    }

    function syncAsa() {
      const live = liveRef.current;
      if (!live.reglaManto) {
        setAsaY(null);
      } else {
        const px = Number(live.simPrecio) > 0 ? Number(live.simPrecio) : live.mantoReal;
        if (!(px > 0)) {
          setAsaY(null);
        } else {
          const y = series.priceToCoordinate(px);
          setAsaY(typeof y === "number" && Number.isFinite(y) ? y : null);
        }
      }
      const tags = [];
      const seenY = new Set();
      for (const n of nivelesRef.current) {
        const masa = Number(n.masa_usd);
        if (!(masa > 0) || (n.rol !== "vacio" && n.rol !== "oz" && n.rol !== "red" && n.rol !== "red_engorde")) {
          continue;
        }
        const y = series.priceToCoordinate(n.precio);
        if (typeof y !== "number" || !Number.isFinite(y)) continue;
        const yk = y.toFixed(1);
        if (seenY.has(yk)) continue;
        seenY.add(yk);
        tags.push({
          key: `${n.rol}:${n.id || n.precio}`,
          y,
          masa,
          color: COLOR[n.rol] || COLOR.vacio,
        });
      }
      setEtiquetas(tags);
      const xs = [];
      const rows = velasRef.current || [];
      for (const c of cazasRef.current) {
        const ts = Number(c.ts);
        const px = Number(c.precio);
        if (!(ts > 0) || !(px > 0)) continue;
        let vela = null;
        for (const v of rows) {
          if (Number(v.time) <= ts) vela = v;
          else break;
        }
        if (!vela) continue;
        const x = chart.timeScale().timeToCoordinate(Number(vela.time));
        const y = series.priceToCoordinate(px);
        if (typeof x !== "number" || typeof y !== "number") continue;
        if (!Number.isFinite(x) || !Number.isFinite(y)) continue;
        const lado = String(c.lado || "").toLowerCase();
        xs.push({
          key: `${c.ts}:${px}`,
          x,
          y,
          color: lado === "buy" ? COLOR.buy : lado === "sell" ? COLOR.sell : COLOR.last,
        });
      }
      setMarcasCaza(xs);
    }

    function pintarVelas(rows, { encajar }) {
      const data = datosVelas(rows);
      if (!data.length) return;
      const ts = chart.timeScale();
      const ps = chart.priceScale("right");
      const rangoT = encajar ? null : ts.getVisibleLogicalRange();
      let rangoP = null;
      if (!encajar) {
        try {
          rangoP = ps.getVisibleRange();
        } catch {
          rangoP = null;
        }
      }
      series.setData(data);
      if (encajar || !rangoT) {
        ts.fitContent();
        encajarRef.current = false;
      } else {
        try {
          ts.setVisibleLogicalRange(rangoT);
        } catch {
          /* ignore */
        }
        if (rangoP && Number.isFinite(rangoP.from) && Number.isFinite(rangoP.to)) {
          try {
            ps.setVisibleRange(rangoP);
            ps.applyOptions({ autoScale: false });
          } catch {
            /* ignore */
          }
        }
      }
      syncRayas();
      syncAsa();
    }

    chart.timeScale().subscribeVisibleLogicalRangeChange(syncAsa);

    const ro = new ResizeObserver(() => {
      if (!wrapRef.current) return;
      chart.applyOptions({
        width: wrapRef.current.clientWidth,
        height: llenar ? Math.max(180, wrapRef.current.clientHeight) : altura,
      });
      syncAsa();
    });
    ro.observe(el);

    apiRef.current = { chart, series, setGhost, syncAsa, syncRayas, pintarVelas, setMantoIlumina };
    pintarVelas(velasRef.current, { encajar: true });
    const already = Number(liveRef.current.simPrecio);
    if (already > 0) setGhost(already);
    requestAnimationFrame(() => {
      syncAsa();
      if (liveRef.current.armado) setMantoIlumina(true);
    });

    return () => {
      ro.disconnect();
      apiRef.current = null;
      setAsaY(null);
      setEtiquetas([]);
      setMarcasCaza([]);
      chart.remove();
    };
  }, [hayVelas, altura, llenar, meta?.precision, meta?.min_move]);

  useEffect(() => {
    const api = apiRef.current;
    if (!api?.pintarVelas || !velas.length) return;
    api.pintarVelas(velas, { encajar: encajarRef.current });
  }, [velas]);

  useEffect(() => {
    apiRef.current?.syncRayas?.();
    apiRef.current?.syncAsa?.();
  }, [niveles, cazas]);

  useEffect(() => {
    apiRef.current?.setMantoIlumina?.(armado);
  }, [armado]);

  useEffect(() => {
    const moved =
      armado &&
      simPrecio > 0 &&
      mantoReal > 0 &&
      Math.abs(simPrecio - mantoReal) / mantoReal > 0.00008;
    apiRef.current?.setGhost?.(moved ? simPrecio : null);
    apiRef.current?.syncAsa?.();
  }, [simPrecio, mantoReal, armado]);

  useEffect(() => {
    armadoRef.current = false;
    dragRef.current = false;
    sesionSoloArmarRef.current = false;
    simRef.current = null;
    setArmado(false);
    setSimPrecio(null);
    setFicha(null);
  }, [symbol]);

  function precioDesdeYPane(yPane) {
    const series = apiRef.current?.series;
    if (!series) return null;
    const p = series.coordinateToPrice(yPane);
    return p != null && Number(p) > 0 ? Number(p) : null;
  }

  function estacionarFichaEnLinea(yLine) {
    const box = paneRef.current;
    if (!box || typeof yLine !== "number") return;
    const rect = box.getBoundingClientRect();
    setFicha(colocarFicha(16, yLine, rect.width, rect.height, { parked: true }));
  }

  function actualizarFicha(clientX, clientY, parked) {
    const box = paneRef.current;
    if (!box) return;
    const rect = box.getBoundingClientRect();
    setFicha(colocarFicha(clientX - rect.left, clientY - rect.top, rect.width, rect.height, { parked }));
  }

  function onAsaDown(ev) {
    if (!reglaManto || !(mantoReal > 0)) return;
    const yaArmado = armadoRef.current;
    const yLine =
      typeof asaY === "number"
        ? asaY
        : ev.currentTarget.getBoundingClientRect().top +
          HIT / 2 -
          (paneRef.current?.getBoundingClientRect().top || 0);

    if (!yaArmado) {
      sesionSoloArmarRef.current = true;
      armadoRef.current = true;
      setArmado(true);
      dragRef.current = false;
      simRef.current = mantoReal;
      setSimPrecio(mantoReal);
      estacionarFichaEnLinea(yLine);
      try {
        ev.currentTarget.setPointerCapture(ev.pointerId);
      } catch {
        /* ignore */
      }
      ev.preventDefault();
      ev.stopPropagation();
      return;
    }

    sesionSoloArmarRef.current = false;
    dragRef.current = false;
    originYRef.current = ev.clientY;
    startLineYRef.current = yLine;
    try {
      ev.currentTarget.setPointerCapture(ev.pointerId);
    } catch {
      /* ignore */
    }
    ev.preventDefault();
    ev.stopPropagation();
  }

  function onAsaMove(ev) {
    if (sesionSoloArmarRef.current) return;
    if (!armadoRef.current) return;
    const dy = ev.clientY - originYRef.current;
    if (!dragRef.current) {
      if (Math.abs(dy) < UMBRAL_ARRASTRE) return;
      dragRef.current = true;
    }
    const p = precioDesdeYPane(startLineYRef.current + dy);
    if (p) {
      simRef.current = p;
      setSimPrecio(p);
    }
    actualizarFicha(ev.clientX, ev.clientY, false);
    ev.preventDefault();
  }

  function onAsaUp(ev) {
    if (sesionSoloArmarRef.current) {
      sesionSoloArmarRef.current = false;
      return;
    }
    if (!armadoRef.current) return;
    dragRef.current = false;
    const px = simRef.current;
    const series = apiRef.current?.series;
    const y = series && px > 0 ? series.priceToCoordinate(px) : asaY;
    if (typeof y === "number") estacionarFichaEnLinea(y);
    else if (ev) actualizarFicha(ev.clientX, ev.clientY, true);
  }

  function cerrarSim(ev) {
    ev?.stopPropagation?.();
    dragRef.current = false;
    armadoRef.current = false;
    sesionSoloArmarRef.current = false;
    simRef.current = null;
    setArmado(false);
    setSimPrecio(null);
    setFicha(null);
    apiRef.current?.setGhost?.(null);
    apiRef.current?.setMantoIlumina?.(false);
    apiRef.current?.syncAsa?.();
  }

  const regla = armado ? reglaEnPunto(manto || { cero: mantoReal }, simPrecio || mantoReal) : null;
  const agua = reglaManto ? marcaAguaManto(manto, fmtUsd) : "";

  return (
    <div className={llenar ? "h-full flex flex-col min-h-0" : ""}>
      <div className="flex gap-1.5 mb-2 shrink-0">
        {INTERVALOS.map((x) => (
          <button
            key={x.id}
            type="button"
            onClick={() => setIv(x.id)}
            className={`px-2 py-1 rounded-lg text-[10px] uppercase tracking-widest border ${
              iv === x.id
                ? "border-emerald-400/50 text-emerald-300 bg-emerald-500/10"
                : "border-white/10 text-white/45"
            }`}
          >
            {x.label}
          </button>
        ))}
        <span className="ml-auto text-[10px] text-white/30 self-center tabular-nums">
          {meta?.symbol || ""} · {velas.length || 0}
        </span>
      </div>
      {velas.length ? (
        <div
          ref={paneRef}
          className={`relative w-full rounded-xl overflow-hidden border border-white/8 ${llenar ? "flex-1 min-h-[180px]" : ""}`}
          style={llenar ? undefined : { height: altura }}
        >
          <div ref={wrapRef} className="absolute inset-0" />
          {etiquetas.map((t) => (
            <div
              key={t.key}
              className="absolute z-[8] pointer-events-none left-2 -translate-y-1/2 tabular-nums text-[10px] font-semibold tracking-wide drop-shadow-[0_1px_2px_rgba(0,0,0,0.85)]"
              style={{ top: t.y, color: t.color }}
            >
              {fmtUsd(t.masa)}
            </div>
          ))}
          {marcasCaza.map((m) => (
            <div
              key={m.key}
              className="absolute z-[8] pointer-events-none -translate-x-1/2 -translate-y-1/2 text-[11px] font-semibold leading-none drop-shadow-[0_1px_2px_rgba(0,0,0,0.9)]"
              style={{ left: m.x, top: m.y, color: m.color }}
              aria-hidden
            >
              ×
            </div>
          ))}
          {reglaManto && agua ? (
            <div className="absolute top-2 left-2 z-[8] pointer-events-none text-[10px] tracking-wide text-white/40">
              {agua}
            </div>
          ) : null}
          {reglaManto && armado && asaY != null ? (
            <div
              className="absolute left-0 right-0 z-[9] pointer-events-none h-[3px] bg-white/85 shadow-[0_0_14px_rgba(248,250,252,0.7)]"
              style={{ top: Math.max(0, asaY - 1) }}
            />
          ) : null}
          {reglaManto && asaY != null ? (
            <div
              role="slider"
              aria-label="Metro del manto"
              className="absolute left-0 right-0 z-10 cursor-ns-resize"
              style={{ top: Math.max(0, asaY - HIT / 2), height: HIT, touchAction: "none" }}
              onPointerDown={onAsaDown}
              onPointerMove={onAsaMove}
              onPointerUp={onAsaUp}
              onPointerCancel={onAsaUp}
            >
              <div
                className={`absolute right-8 top-1/2 -translate-y-1/2 rounded-full border bg-[#0a0c10]/90 shadow-md flex items-center justify-center ${
                  armado
                    ? "w-7 h-7 border-white text-white"
                    : "w-6 h-6 border-white/45 text-white/70"
                }`}
              >
                <span className="text-[10px] leading-none">⇅</span>
              </div>
            </div>
          ) : null}
          {reglaManto && armado && regla && ficha ? (
            <div
              className="absolute z-20 rounded-lg border border-white/25 bg-[#0a0c10]/95 px-2.5 py-2 shadow-lg pointer-events-auto"
              style={{ left: ficha.left, top: ficha.top, width: CHIP_W }}
            >
              <div className="flex items-start justify-between gap-1">
                <p className="text-sm font-semibold tabular-nums text-white leading-tight">
                  {fmtPctSigned(regla.pct)}
                </p>
                <button
                  type="button"
                  onPointerDown={(e) => e.stopPropagation()}
                  onClick={cerrarSim}
                  aria-label="Cerrar simulación"
                  className="w-6 h-6 -mt-0.5 -mr-0.5 flex items-center justify-center rounded text-white/70 text-base leading-none"
                >
                  ×
                </button>
              </div>
              <p className="text-[11px] tabular-nums text-white/85 leading-tight mt-0.5">
                {fmtUsdSigned(regla.usd)}
              </p>
              <p className="text-[11px] tabular-nums text-white/60 leading-tight">
                {(regla.usd || 0) >= 0 ? "+" : "−"}
                {fmtNum(Math.abs(regla.coin || 0), decimalesPrecio(Math.abs(regla.coin || 0) || 1))}{" "}
                {manto?.symbol || ""}
              </p>
            </div>
          ) : null}
        </div>
      ) : (
        <p className="text-sm text-white/40 py-8 text-center">
          {error || "Esperando velas de spot…"}
        </p>
      )}
      <div className="flex flex-wrap gap-x-3 gap-y-1 mt-2 text-[10px] text-white/45 shrink-0">
        {LEYENDA.filter((x) => {
          if (x.rol === "last") return true;
          if (x.rol === "oz" || x.rol === "red") {
            return niveles.some((n) => n.rol === x.rol || (x.rol === "red" && n.rol === "red_engorde"));
          }
          return true;
        }).map((x) => (
          <span key={x.rol} style={{ color: COLOR[x.rol] }}>{x.label}</span>
        ))}
      </div>
    </div>
  );
}
