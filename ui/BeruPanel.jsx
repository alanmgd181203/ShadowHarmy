import { useEffect, useState } from "react";
import BeruAssetDetail from "./BeruAssetDetail.jsx";
import BeruChartScreen from "./BeruChartScreen.jsx";
import { flotaDesdeEstado, fmtUsd, fmtDistSilbato, cargarSnapBeru } from "./beruAssetDetailModel.js";
import { nombreGrado } from "./beruMantoRegla.js";

const COLOR_GRADO = {
  SOLDADO: "#1e3a5f",
  CAPITAN: "#3b82f6",
  GENERAL: "#22d3ee",
  MARISCAL: "#67e8f9",
};

const RANGOS_SANTOS = [
  { id: "MARISCAL", plural: "Mariscales" },
  { id: "GENERAL", plural: "Generales" },
  { id: "CAPITAN", plural: "Capitanes" },
  { id: "SOLDADO", plural: "Soldados" },
];

function colorGrado(grado) {
  const g = String(grado || "").toUpperCase();
  return COLOR_GRADO[g] || "#64748b";
}

function etiquetaOficio(oficio) {
  const o = String(oficio || "").toLowerCase();
  if (o === "cazando") return "cazando";
  if (o === "cerrado") return "cerrado";
  return "acechando";
}

/**
 * BeruPanel — flota por moneda → Sub-Santuario.
 */
export default function BeruPanel({ onClose }) {
  const [panelVisible, setPanelVisible] = useState(false);
  const [selected, setSelected] = useState(null);
  const [flota, setFlota] = useState(() => flotaDesdeEstado({}));
  const [menuSantos, setMenuSantos] = useState(false);
  const [filtroGrado, setFiltroGrado] = useState(null);

  useEffect(() => {
    const id = requestAnimationFrame(() => setPanelVisible(true));
    return () => cancelAnimationFrame(id);
  }, []);

  useEffect(() => {
    let alive = true;
    async function load() {
      try {
        const snap = await cargarSnapBeru();
        if (alive) setFlota(flotaDesdeEstado(snap));
      } catch {
        /* silencio */
      }
    }
    load();
    const t = setInterval(load, 2000);
    return () => {
      alive = false;
      clearInterval(t);
    };
  }, []);

  if (selected?.vista === "chart") {
    return (
      <BeruChartScreen
        symbol={selected.symbol}
        onClose={() => setSelected(null)}
        onFicha={() => setSelected({ symbol: selected.symbol, vista: "ficha" })}
      />
    );
  }
  if (selected?.vista === "ficha" || typeof selected === "string") {
    const sym = typeof selected === "string" ? selected : selected.symbol;
    return (
      <BeruAssetDetail
        symbol={sym}
        onClose={() => setSelected(null)}
        onChart={() => setSelected({ symbol: sym, vista: "chart" })}
      />
    );
  }

  const todos = flota.activos || [];
  const activos = filtroGrado ? todos.filter((a) => a.grado === filtroGrado) : todos;
  const nSantos = flota.n_santos || todos.length;
  const conteo = flota.conteo_grados || {};
  const filtroLabel = RANGOS_SANTOS.find((r) => r.id === filtroGrado)?.plural;

  return (
    <div
      className={`absolute inset-0 z-50 flex flex-col bg-[#0a0c10] text-white overflow-y-auto overflow-x-hidden transition-opacity duration-1000 ease-in-out ${
        panelVisible ? "opacity-100" : "opacity-0"
      }`}
    >
      <header className="relative flex justify-between items-center p-4 shrink-0 border-b border-white/5">
        <button
          type="button"
          onClick={onClose}
          aria-label="Cerrar flota Beru"
          className="w-10 h-10 flex items-center justify-center rounded-lg border border-white/10 active:scale-95 cursor-pointer"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-white/80">
            <path d="M19 12H5" />
            <path d="M12 19l-7-7 7-7" />
          </svg>
        </button>
        <h1 className="absolute left-1/2 -translate-x-1/2 text-2xl italic font-bold tracking-widest pointer-events-none">
          BERU
        </h1>
        <button
          type="button"
          onClick={() => setMenuSantos((v) => !v)}
          aria-expanded={menuSantos}
          aria-label={`${nSantos} Santos de la flota`}
          className={`flex flex-col items-end justify-center min-w-[4.5rem] px-2.5 py-1.5 rounded-xl border active:scale-95 ${
            menuSantos || filtroGrado
              ? "border-cyan-300/70 bg-cyan-400/20"
              : "border-cyan-400/45 bg-cyan-400/10"
          }`}
        >
          <span className="text-lg font-bold tabular-nums leading-none text-cyan-300">{nSantos}</span>
          <span className="text-[9px] uppercase tracking-[0.18em] text-cyan-400/90">Santos</span>
        </button>
      </header>

      {menuSantos ? (
        <div className="mx-4 mt-3 rounded-2xl border border-cyan-400/25 bg-[#12141a] p-3 space-y-1 shadow-[0_0_24px_rgba(103,232,249,0.08)]">
          {RANGOS_SANTOS.map((r) => {
            const n = Number(conteo[r.id]) || 0;
            const activo = filtroGrado === r.id;
            return (
              <button
                key={r.id}
                type="button"
                disabled={n <= 0}
                onClick={() => {
                  setFiltroGrado(r.id);
                  setMenuSantos(false);
                }}
                className={`w-full flex justify-between items-center px-3 py-2 rounded-xl text-sm ${
                  n <= 0
                    ? "text-white/25 cursor-not-allowed"
                    : activo
                      ? "bg-cyan-400/15 text-cyan-200"
                      : "text-white/85 active:scale-[0.99]"
                }`}
              >
                <span style={{ color: n > 0 ? colorGrado(r.id) : undefined }}>{r.plural}</span>
                <span className="tabular-nums font-semibold">{n}</span>
              </button>
            );
          })}
          <button
            type="button"
            onClick={() => {
              setFiltroGrado(null);
              setMenuSantos(false);
            }}
            className="w-full mt-1 px-3 py-2 rounded-xl text-xs uppercase tracking-[0.2em] text-white/50 active:scale-[0.99]"
          >
            Todos
          </button>
        </div>
      ) : null}

      {filtroLabel && !menuSantos ? (
        <div className="px-4 pt-3">
          <button
            type="button"
            onClick={() => setFiltroGrado(null)}
            className="text-[11px] uppercase tracking-[0.18em] text-cyan-300/80"
          >
            {filtroLabel} · todos
          </button>
        </div>
      ) : null}

      <div className="px-4 pt-4 pb-10 space-y-2">
        {activos.length === 0 ? (
          <p className="text-center text-white/40 text-sm py-8">
            {filtroGrado ? "Ningún Santo de este rango." : "Nadie activo — Beru rango en silencio."}
          </p>
        ) : (
          activos.map((a) => {
            const cerrado = String(a.oficio || "").toLowerCase() === "cerrado";
            const distTxt = fmtDistSilbato(a.dist_silbato, a.oficio);
            const tono = colorGrado(a.grado);
            const mariscal = String(a.grado || "").toUpperCase() === "MARISCAL";
            const saco = a.saco_usd != null ? a.saco_usd : a.masa_total_usd;
            const cazas = Number(a.n_cazas) || 0;
            const paso = Number(a.engorde_paso_usd);
            const rango = nombreGrado(a.grado);
            return (
              <div
                key={a.activo}
                className="w-full text-left rounded-2xl border bg-[#12141a]/90 p-3.5"
                style={{
                  borderColor: cerrado
                    ? "rgba(255,255,255,0.08)"
                    : mariscal
                      ? "rgba(103,232,249,0.45)"
                      : "rgba(255,255,255,0.10)",
                  boxShadow: mariscal && !cerrado ? "0 0 18px rgba(103,232,249,0.12)" : "none",
                  opacity: cerrado ? 0.72 : 1,
                }}
              >
                <div className="flex justify-between items-baseline mb-1">
                  <button
                    type="button"
                    onClick={() => setSelected({ symbol: a.activo, vista: "chart" })}
                    className="text-lg font-semibold tracking-wide text-left active:scale-[0.98]"
                    aria-label={`Velas ${a.activo}`}
                  >
                    {a.activo}
                    {a.oficio_beru === "RANGO" ? (
                      <span className="ml-2 text-[10px] uppercase text-cyan-400/80">rango</span>
                    ) : a.es_semilla ? (
                      <span className="ml-2 text-[10px] uppercase text-emerald-400/80">semilla</span>
                    ) : null}
                  </button>
                  <button
                    type="button"
                    onClick={() => setSelected({ symbol: a.activo, vista: "ficha" })}
                    className="text-xs text-white/70 tabular-nums active:scale-[0.98]"
                    aria-label={`Precio ${a.activo}`}
                  >
                    {a.oficio_beru === "RANGO"
                      ? (a.last > 0 ? Number(a.last).toFixed(2) : "—")
                      : fmtUsd(cerrado ? null : saco)}
                  </button>
                </div>
                <button
                  type="button"
                  onClick={() => setSelected({ symbol: a.activo, vista: "ficha" })}
                  className="w-full text-left active:scale-[0.99]"
                  aria-label={`Ficha ${a.activo}`}
                >
                  <p
                    className="text-[12px] font-semibold tracking-wide mb-1"
                    style={{
                      color: tono,
                      textShadow: mariscal ? "0 0 10px rgba(103,232,249,0.55)" : "none",
                    }}
                  >
                    {a.oficio_beru === "RANGO"
                      ? `0=${a.cero > 0 ? Number(a.cero).toFixed(2) : "—"} · Red=${a.red > 0 ? Number(a.red).toFixed(2) : "—"}`
                      : rango === "00"
                        ? ""
                        : rango}
                    {a.oficio_beru === "RANGO" && a.sangre_lado ? (
                      <span className="ml-2 text-[11px] font-normal opacity-90">
                        sangre {a.sangre_lado}
                      </span>
                    ) : !cerrado && Number.isFinite(paso) && paso > 0 ? (
                      <span className="ml-2 text-[11px] font-normal tabular-nums opacity-90">
                        +{fmtUsd(paso)} / 0,1
                      </span>
                    ) : null}
                  </p>
                  <div className="flex justify-between text-[11px] text-white/55">
                    <span>
                      {etiquetaOficio(a.oficio)}
                      {a.manos ? " · manos ON" : ""}
                    </span>
                    <span className="tabular-nums">
                      {a.oficio_beru === "RANGO"
                        ? (cazas > 0 ? `${cazas} oz` : distTxt || "")
                        : cerrado
                          ? (cazas > 0 ? `${cazas} ${cazas === 1 ? "caza" : "cazas"}` : "")
                          : distTxt
                            ? distTxt
                            : `${cazas} ${cazas === 1 ? "caza" : "cazas"}`}
                    </span>
                  </div>
                  {a.ultima_lecturas ? (
                    <p className="text-[10px] text-white/40 mt-1 tabular-nums leading-snug">
                      {a.ultima_lecturas}
                    </p>
                  ) : null}
                </button>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
