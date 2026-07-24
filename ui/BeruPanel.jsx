import { useEffect, useState } from "react";
import BeruAssetDetail from "./BeruAssetDetail.jsx";
import { flotaDesdeEstado, fmtUsd, fmtPct } from "./beruAssetDetailModel.js";

const ESTADO_URL = "/data/estado_vivo.json";

/**
 * BeruPanel — flota por moneda → Sub-Santuario.
 */
export default function BeruPanel({ onClose }) {
  const [panelVisible, setPanelVisible] = useState(false);
  const [selected, setSelected] = useState(null);
  const [flota, setFlota] = useState(() => flotaDesdeEstado({}));

  useEffect(() => {
    const id = requestAnimationFrame(() => setPanelVisible(true));
    return () => cancelAnimationFrame(id);
  }, []);

  useEffect(() => {
    let alive = true;
    async function load() {
      try {
        const res = await fetch(`${ESTADO_URL}?t=${Date.now()}`, { cache: "no-store" });
        if (!res.ok) return;
        const snap = await res.json();
        if (alive) setFlota(flotaDesdeEstado(snap));
      } catch {
        /* silencio */
      }
    }
    load();
    const t = setInterval(load, 3000);
    return () => {
      alive = false;
      clearInterval(t);
    };
  }, []);

  if (selected) {
    return <BeruAssetDetail symbol={selected} onClose={() => setSelected(null)} />;
  }

  const activos = flota.activos || [];

  return (
    <div
      className={`fixed inset-0 z-50 flex flex-col bg-[#0a0c10] text-white overflow-y-auto overflow-x-hidden transition-opacity duration-1000 ease-in-out ${
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
        <span className="text-[10px] text-white/35 w-10 text-right">{flota.n_barcos_total || 0}</span>
      </header>

      <section className="px-4 pt-4 pb-2">
        <p className="text-center text-[10px] uppercase tracking-[0.25em] text-white/35 mb-1">
          Flota · semilla {flota.semilla || "—"}
        </p>
        <p className="text-center text-xs text-white/50 mb-3">
          {flota.n_activos || 0} monedas · toca una para el Sub-Santuario
        </p>
      </section>

      <div className="px-4 pb-10 space-y-2">
        {activos.length === 0 ? (
          <p className="text-center text-white/40 text-sm py-8">
            Legión vacía — esperando semilla.
          </p>
        ) : (
          activos.map((a) => {
            const comp = a.composicion || {};
            const pctC = Math.min(100, Number(comp.pct_caza) || 0);
            const pctN = Math.min(100, Number(comp.pct_negociando) || 0);
            return (
              <button
                key={a.activo}
                type="button"
                onClick={() => setSelected(a.activo)}
                className="w-full text-left rounded-2xl border border-white/10 bg-[#12141a]/90 p-3.5 active:scale-[0.99] transition-transform"
              >
                <div className="flex justify-between items-baseline mb-1.5">
                  <span className="text-lg font-semibold tracking-wide">
                    {a.activo}
                    {a.es_semilla ? (
                      <span className="ml-2 text-[10px] uppercase text-emerald-400/80">semilla</span>
                    ) : null}
                  </span>
                  <span className="text-xs text-white/45 tabular-nums">{fmtUsd(a.masa_total_usd)}</span>
                </div>
                <div className="flex gap-3 text-[11px] text-white/55 mb-2">
                  <span>{a.n_caza || 0} caza</span>
                  <span>{a.n_negociando || 0} neg</span>
                  <span>{a.n_acechando || 0} acech</span>
                  {a.n_mega ? <span className="text-amber-300">{a.n_mega} mega</span> : null}
                </div>
                <div className="h-2.5 rounded-full overflow-hidden flex border border-white/10 mb-1.5">
                  <div className="h-full bg-emerald-500/70" style={{ width: `${pctC}%` }} />
                  <div className="h-full bg-sky-500/60" style={{ width: `${pctN}%` }} />
                </div>
                <div className="flex justify-between text-[10px] text-white/40">
                  <span>
                    Red engorde {a.red_engorde_pct != null ? fmtPct(a.red_engorde_pct) : "—"}
                  </span>
                  <span>PnL {fmtUsd(a.pnl_est_usd)}</span>
                </div>
              </button>
            );
          })
        )}
      </div>
    </div>
  );
}
