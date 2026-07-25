import { useEffect, useState } from "react";
import { oidoCero, oidoDesdeEstado, fmtTs } from "./bellionOidoModel.js";

const ESTADO_URL = "/data/estado_vivo.json";

const NIVEL_STYLE = {
  critico: {
    border: "border-rose-500/40",
    title: "text-rose-400",
    label: "Crítico",
  },
  ejecucion: {
    border: "border-sky-500/35",
    title: "text-sky-400",
    label: "Ejecución",
  },
  salud: {
    border: "border-emerald-500/35",
    title: "text-emerald-400",
    label: "Salud",
  },
};

/**
 * BellionPanel — Susurro del oído (4.1.2). Sin LLM.
 */
export default function BellionPanel({ onClose }) {
  const [visible, setVisible] = useState(false);
  const [oido, setOido] = useState(() => oidoCero());

  useEffect(() => {
    const id = requestAnimationFrame(() => setVisible(true));
    return () => cancelAnimationFrame(id);
  }, []);

  useEffect(() => {
    let alive = true;
    async function load() {
      try {
        const res = await fetch(`${ESTADO_URL}?t=${Date.now()}`, { cache: "no-store" });
        if (!res.ok) return;
        const snap = await res.json();
        if (alive) setOido(oidoDesdeEstado(snap));
      } catch {
        /* silencio */
      }
    }
    load();
    const t = setInterval(load, 2500);
    return () => {
      alive = false;
      clearInterval(t);
    };
  }, []);

  const c = oido.counts || {};

  return (
    <div
      className={`fixed inset-0 z-50 flex flex-col bg-[#0a0c10] text-white overflow-y-auto overflow-x-hidden transition-opacity duration-1000 ease-in-out ${
        visible ? "opacity-100" : "opacity-0"
      }`}
    >
      <header className="relative flex justify-between items-center p-4 shrink-0 border-b border-white/5">
        <button
          type="button"
          onClick={onClose}
          aria-label="Cerrar oído Bellion"
          className="w-10 h-10 flex items-center justify-center rounded-lg border border-white/10 active:scale-95 cursor-pointer"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-white/80">
            <path d="M19 12H5" />
            <path d="M12 19l-7-7 7-7" />
          </svg>
        </button>
        <h1 className="absolute left-1/2 -translate-x-1/2 text-2xl italic font-bold tracking-widest pointer-events-none">
          BELLION
        </h1>
        <span className="text-[10px] text-white/35 w-10 text-right">oído</span>
      </header>

      <section className="px-4 pt-4 pb-2">
        <p className="text-center text-[10px] uppercase tracking-[0.25em] text-white/35 mb-1">
          Susurro de las sombras
        </p>
        <p className="text-center text-xs text-white/50 mb-3">
          Solo lo que importa — ruido queda en la crónica cruda
        </p>
        <div className="grid grid-cols-3 gap-2 mb-2">
          <Stat label="Crítico" value={c.critico || 0} tone="text-rose-400" />
          <Stat label="Ejecución" value={c.ejecucion || 0} tone="text-sky-400" />
          <Stat label="Salud" value={c.salud || 0} tone="text-emerald-400" />
        </div>
      </section>

      <div className="px-4 pb-10 space-y-4">
        {["critico", "ejecucion", "salud"].map((nivel) => {
          const st = NIVEL_STYLE[nivel];
          const rows = oido.por_nivel?.[nivel] || [];
          return (
            <section
              key={nivel}
              className={`rounded-2xl border ${st.border} bg-[#12141a]/85 p-3.5`}
            >
              <h2 className={`text-[10px] uppercase tracking-[0.22em] ${st.title} mb-2.5`}>
                {st.label}
              </h2>
              {rows.length === 0 ? (
                <p className="text-sm text-white/35">Sin avisos en este nivel.</p>
              ) : (
                <ul className="space-y-2">
                  {rows.map((ev, i) => (
                    <li
                      key={`${ev.ts}-${ev.accion}-${i}`}
                      className="rounded-xl border border-white/5 bg-black/25 px-3 py-2"
                    >
                      <div className="flex justify-between gap-2 text-[10px] text-white/40 mb-0.5">
                        <span>{ev.general || "—"}</span>
                        <span className="tabular-nums">{fmtTs(ev.ts)}</span>
                      </div>
                      <p className="text-sm text-white/90 font-medium tracking-wide">
                        {ev.accion}
                      </p>
                      {ev.detalle ? (
                        <p className="text-[11px] text-white/45 mt-0.5 leading-snug">
                          {ev.detalle}
                        </p>
                      ) : null}
                    </li>
                  ))}
                </ul>
              )}
            </section>
          );
        })}
        {oido.nota ? (
          <p className="text-[10px] text-white/30 text-center px-2">{oido.nota}</p>
        ) : null}
      </div>
    </div>
  );
}

function Stat({ label, value, tone }) {
  return (
    <div className="rounded-xl border border-white/8 bg-black/30 px-2 py-2 text-center">
      <p className="text-[9px] uppercase tracking-widest text-white/35">{label}</p>
      <p className={`text-lg tabular-nums font-semibold ${tone}`}>{value}</p>
    </div>
  );
}
