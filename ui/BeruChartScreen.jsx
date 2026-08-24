import { useEffect, useMemo, useState } from "react";
import BeruSpotChart from "./BeruSpotChart.jsx";
import { snapshotCero, desdeEstadoVivo as beruDesdeEstado, cargarSnapBeru } from "./beruAssetDetailModel.js";
import { desdeEstadoVivo as igrisDesdeEstado } from "./assetDetailModel.js";
import { mantoDesdeFuentes } from "./beruMantoRegla.js";

/**
 * Lienzo grande: velas + combate Beru (rango linear o cazador spot).
 */
export default function BeruChartScreen({ symbol, onClose, onFicha }) {
  const [visible, setVisible] = useState(false);
  const [data, setData] = useState(() => snapshotCero(symbol));
  const [igris, setIgris] = useState(() => igrisDesdeEstado(symbol, null));

  useEffect(() => {
    const id = requestAnimationFrame(() => setVisible(true));
    return () => cancelAnimationFrame(id);
  }, []);

  useEffect(() => {
    setData(snapshotCero(symbol));
    setIgris(igrisDesdeEstado(symbol, null));
  }, [symbol]);

  useEffect(() => {
    let alive = true;
    let lastKey = "";
    async function load() {
      try {
        const snap = await cargarSnapBeru();
        if (!alive) return;
        const next = beruDesdeEstado(symbol, snap);
        const niv = next?.grafica?.niveles || [];
        const key = [
          next?.oficio,
          next?.mercado,
          next?.spot_last ?? next?.last_lineal,
          ...niv.map((n) => `${n.id || n.rol}:${Number(n.precio || 0).toFixed(6)}`),
        ].join("|");
        if (key === lastKey) return;
        lastKey = key;
        setData(next);
        setIgris(igrisDesdeEstado(symbol, snap));
      } catch {
        /* silencio — no borrar data viva (evita rayas duales → semilla) */
      }
    }
    load();
    const t = setInterval(load, 2000);
    return () => {
      alive = false;
      clearInterval(t);
    };
  }, [symbol]);

  const manto = useMemo(() => mantoDesdeFuentes(symbol, data, igris), [symbol, data, igris]);
  const esRango = String(data?.oficio || data?.grafica?.oficio || "").toUpperCase() === "RANGO";
  const category = esRango || data?.mercado === "linear" ? "linear" : "spot";

  return (
    <div
      className={`absolute inset-0 z-[60] flex flex-col bg-[#0a0c10] text-white overflow-hidden transition-opacity duration-500 ${
        visible ? "opacity-100" : "opacity-0"
      }`}
    >
      <header className="relative flex justify-between items-center p-4 shrink-0 border-b border-white/5">
        <button
          type="button"
          onClick={onClose}
          aria-label="Volver a flota Beru"
          className="w-10 h-10 flex items-center justify-center rounded-lg border border-white/10 active:scale-95"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M19 12H5" />
            <path d="M12 19l-7-7 7-7" />
          </svg>
        </button>
        <h1 className="absolute left-1/2 -translate-x-1/2 text-xl italic font-bold tracking-widest pointer-events-none">
          {data.symbol || symbol}
          {esRango ? <span className="ml-2 text-[10px] not-italic font-normal text-cyan-400/80">LINEAR</span> : null}
        </h1>
        <button
          type="button"
          onClick={onFicha}
          className="text-[10px] uppercase tracking-widest text-emerald-400/80 px-2"
        >
          ficha
        </button>
      </header>
      <div className="flex-1 min-h-0 px-3 pt-3 pb-4 flex flex-col">
        <div className="flex-1 min-h-0">
          <BeruSpotChart
            symbol={symbol}
            grafica={data.grafica}
            manto={manto}
            llenar
            reglaManto={!esRango}
            category={category}
            leyendaRango={esRango}
          />
        </div>
      </div>
    </div>
  );
}
