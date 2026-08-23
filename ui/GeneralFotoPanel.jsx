import { useEffect, useState } from "react";
import FotoCruda from "./FotoCruda.jsx";
import { useEstadoVivo } from "./useEstadoVivo.js";

/**
 * Pergamino de un General — HUD corto + foto cruda de lo que procesa.
 */
export default function GeneralFotoPanel({ titulo, ariaCerrar, slices, onClose, nota }) {
  const [visible, setVisible] = useState(false);
  const snap = useEstadoVivo(3000);

  useEffect(() => {
    const id = requestAnimationFrame(() => setVisible(true));
    return () => cancelAnimationFrame(id);
  }, []);

  const bloques = typeof slices === "function" ? slices(snap || {}) : slices || [];

  return (
    <div
      className={`absolute inset-0 z-50 flex flex-col bg-[#0a0c10] text-white overflow-y-auto overflow-x-hidden transition-opacity duration-700 ${
        visible ? "opacity-100" : "opacity-0"
      }`}
    >
      <header className="relative flex justify-between items-center p-4 shrink-0 border-b border-white/5">
        <button
          type="button"
          onClick={onClose}
          aria-label={ariaCerrar || `Cerrar ${titulo}`}
          className="w-10 h-10 flex items-center justify-center rounded-lg border border-white/10 active:scale-95"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M19 12H5" />
            <path d="M12 19l-7-7 7-7" />
          </svg>
        </button>
        <h1 className="absolute left-1/2 -translate-x-1/2 text-xl italic font-bold tracking-[0.2em] pointer-events-none">
          {titulo}
        </h1>
        <span className="text-[10px] text-white/35 w-10 text-right">
          {snap?.ts ? "vivo" : "00"}
        </span>
      </header>

      <div className="px-4 py-4 space-y-3 pb-10">
        {nota ? <p className="text-[12px] text-white/45 leading-relaxed">{nota}</p> : null}
        {!snap ? (
          <p className="text-sm text-white/40 py-6 text-center">Esperando foto viva…</p>
        ) : null}
        {bloques.map((b) => (
          <FotoCruda key={b.id || b.titulo} titulo={b.titulo} data={b.data} defaultOpen={b.abierto} />
        ))}
      </div>
    </div>
  );
}
