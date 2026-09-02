import { useEffect, useState } from "react";
import BeruAssetDetail from "./BeruAssetDetail.jsx";
import BeruChartScreen from "./BeruChartScreen.jsx";
import {
  cargarSnapBeru,
  fmtDistSilbato,
  fmtUsd,
} from "./beruAssetDetailModel.js";
import {
  cargarCatalogoOkx,
  fmtPrecioLista,
  listaPerpetuosDesdeCatalogo,
} from "./beruCatalogoModel.js";

function etiquetaOficio(oficio) {
  const o = String(oficio || "").toLowerCase();
  if (o === "cazando") return "cazando";
  if (o === "cerrado") return "cerrado";
  return "acechando";
}

/**
 * BeruPanel — catálogo completo USDT-SWAP (perp + TradeFi) → Sub-Santuario.
 * Sin filtros de color/rango todavía; solo lista viva del mar OKX.
 */
export default function BeruPanel({ onClose }) {
  const [panelVisible, setPanelVisible] = useState(false);
  const [selected, setSelected] = useState(null);
  const [lista, setLista] = useState(() =>
    listaPerpetuosDesdeCatalogo({ activos: {} }),
  );
  const [cargando, setCargando] = useState(true);

  useEffect(() => {
    const id = requestAnimationFrame(() => setPanelVisible(true));
    return () => cancelAnimationFrame(id);
  }, []);

  useEffect(() => {
    let alive = true;
    async function load() {
      let catalogo = { activos: {} };
      try {
        catalogo = await cargarCatalogoOkx();
      } catch {
        /* silencio */
      }
      if (alive) {
        setLista(listaPerpetuosDesdeCatalogo(catalogo, null));
        setCargando(false);
      }
      try {
        const snap = await cargarSnapBeru();
        if (alive) setLista(listaPerpetuosDesdeCatalogo(catalogo, snap));
      } catch {
        /* silencio — catálogo ya visible */
      }
    }
    load();
    const t = setInterval(load, 15000);
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

  const activos = lista.activos || [];

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
        <div className="absolute left-1/2 -translate-x-1/2 text-center pointer-events-none">
          <h1 className="text-2xl italic font-bold tracking-widest">BERU</h1>
          <p className="text-[9px] uppercase tracking-[0.22em] text-cyan-400/75 mt-0.5">
            OKX · USDT perpetuo
          </p>
        </div>
        <div className="flex flex-col items-end justify-center min-w-[4.5rem] px-2.5 py-1.5 rounded-xl border border-cyan-400/45 bg-cyan-400/10">
          <span className="text-lg font-bold tabular-nums leading-none text-cyan-300">
            {lista.n_total || activos.length}
          </span>
          <span className="text-[9px] uppercase tracking-[0.18em] text-cyan-400/90">pares</span>
        </div>
      </header>

      <div className="px-4 py-2 border-b border-white/5 text-[10px] uppercase tracking-[0.16em] text-white/40 flex flex-wrap gap-x-3 gap-y-1">
        <span>{lista.n_perp ?? 0} crypto</span>
        <span>{lista.n_tradefi ?? 0} tradefi</span>
        {lista.n_vivos > 0 ? (
          <span className="text-cyan-300/80">{lista.n_vivos} vivos</span>
        ) : null}
        <span className="ml-auto normal-case tracking-normal text-white/30">
          sin filtro · colores después
        </span>
      </div>

      <div className="px-4 pt-3 pb-10 space-y-1.5">
        {cargando && activos.length === 0 ? (
          <p className="text-center text-white/40 text-sm py-8">Cargando catálogo OKX…</p>
        ) : activos.length === 0 ? (
          <p className="text-center text-white/40 text-sm py-8">
            Catálogo vacío — corre sync OKX (`okx_parametros_mercado.json`).
          </p>
        ) : (
          activos.map((a) => {
            const vivo = a.vivo;
            const enRango = String(a.oficio_beru || "").toUpperCase() === "RANGO";
            const oficio = vivo ? etiquetaOficio(a.oficio) : "";
            const distTxt = vivo ? fmtDistSilbato(vivo.dist_silbato, a.oficio) : "";
            return (
              <div
                key={a.activo}
                className={`w-full rounded-xl border bg-[#12141a]/90 px-3 py-2.5 ${
                  vivo ? "border-cyan-400/25" : "border-white/8"
                }`}
              >
                <div className="flex justify-between items-baseline gap-2">
                  <button
                    type="button"
                    onClick={() => setSelected({ symbol: a.activo, vista: "chart" })}
                    className="text-left active:scale-[0.98] min-w-0"
                    aria-label={`Velas ${a.activo}`}
                  >
                    <span className="text-[15px] font-semibold tracking-wide">{a.activo}</span>
                    <span
                      className={`ml-2 text-[9px] uppercase tracking-wider ${
                        a.tradefi ? "text-amber-400/90" : "text-white/35"
                      }`}
                    >
                      {a.tradefi ? "tradefi" : "perp"}
                    </span>
                    {enRango ? (
                      <span className="ml-1.5 text-[9px] uppercase text-cyan-400/85">rango</span>
                    ) : null}
                  </button>
                  <button
                    type="button"
                    onClick={() => setSelected({ symbol: a.activo, vista: "ficha" })}
                    className="text-xs tabular-nums text-white/75 shrink-0 active:scale-[0.98]"
                    aria-label={`Ficha ${a.activo}`}
                  >
                    {fmtPrecioLista(a.precio)}
                  </button>
                </div>
                <button
                  type="button"
                  onClick={() => setSelected({ symbol: a.activo, vista: "ficha" })}
                  className="w-full text-left active:scale-[0.99] mt-0.5"
                  aria-label={`Detalle ${a.activo}`}
                >
                  <div className="flex justify-between text-[10px] text-white/45">
                    <span className="tabular-nums">
                      min {a.minUsd > 0 ? fmtUsd(a.minUsd) : "—"}
                    </span>
                    {vivo ? (
                      <span className="text-cyan-300/75">
                        {oficio}
                        {vivo.manos ? " · manos" : ""}
                        {distTxt ? ` · ${distTxt}` : ""}
                      </span>
                    ) : (
                      <span className="text-white/25">—</span>
                    )}
                  </div>
                  {enRango && vivo ? (
                    <p className="text-[10px] text-white/40 mt-0.5 tabular-nums">
                      0={vivo.cero > 0 ? Number(vivo.cero).toFixed(2) : "—"}
                      {vivo.red > 0 ? ` · Red=${Number(vivo.red).toFixed(2)}` : ""}
                      {vivo.sangre_lado ? ` · sangre ${vivo.sangre_lado}` : ""}
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
