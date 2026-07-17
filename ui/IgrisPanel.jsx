import { useState, useEffect } from "react";
import AssetDetail from "./AssetDetail.jsx";

/**
 * IgrisPanel — Lienzo táctico "EL MANTO"
 * Estado cero + fundido + Sub-Santuario por activo.
 */
export default function IgrisPanel({ onClose }) {
  const [showOxygen, setShowOxygen] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);
  const [panelVisible, setPanelVisible] = useState(false);
  const [selectedAsset, setSelectedAsset] = useState(null);

  useEffect(() => {
    const id = requestAnimationFrame(() => setPanelVisible(true));
    return () => cancelAnimationFrame(id);
  }, []);

  const vanguardia = [
    { id: "BTC", longPct: 50 },
    { id: "ETH", longPct: 50 },
    { id: "LTC", longPct: 50 },
    { id: "XRP", longPct: 50 },
    { id: "FIL", longPct: 50 },
  ];

  const batallon = [
    { id: "SOL", longPct: 50 },
    { id: "OP", longPct: 50 },
    { id: "ARB", longPct: 50 },
    { id: "DOGE", longPct: 50 },
    { id: "LINK", longPct: 50 },
    { id: "AVAX", longPct: 50 },
  ];

  return (
    <div
      className={`fixed inset-0 z-50 flex flex-col bg-[#0a0c10] text-white overflow-y-auto overflow-x-hidden transition-opacity duration-1000 delay-500 ease-in-out ${
        panelVisible ? "opacity-100" : "opacity-0"
      }`}
    >
      <header className="relative flex justify-between items-center p-4 shrink-0 border-b border-white/5">
        <button
          type="button"
          onClick={onClose}
          aria-label="Cerrar Manto"
          className="w-10 h-10 flex items-center justify-center rounded-lg border border-white/10 active:scale-95 transition-transform cursor-pointer"
        >
          <svg
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            className="text-white/80"
          >
            <path d="M19 12H5" />
            <path d="M12 19l-7-7 7-7" />
          </svg>
        </button>

        <h1 className="absolute left-1/2 -translate-x-1/2 text-2xl italic font-bold tracking-widest text-white pointer-events-none">
          MANTO
        </h1>

        <button
          type="button"
          onClick={() => setShowOxygen((v) => !v)}
          aria-label="HUD Oxígeno"
          aria-expanded={showOxygen}
          className={`w-10 h-10 flex items-center justify-center rounded-lg border text-sm font-semibold tracking-wide transition-colors active:scale-95 cursor-pointer ${
            showOxygen
              ? "border-[#ff0055] text-[#ff0055] bg-[#ff0055]/10"
              : "border-white/10 text-white/70"
          }`}
        >
          %
        </button>

        {showOxygen && (
          <div
            className="absolute top-full right-4 mt-2 z-20 w-64 p-3 rounded-xl border border-[#ff0055]/40 bg-[#0a0c10]/90 backdrop-blur-md shadow-[0_0_24px_rgba(255,0,85,0.2)]"
            role="dialog"
            aria-label="Oxígeno del manto"
          >
            <p className="text-[10px] uppercase tracking-[0.2em] text-[#ff0055]/80 mb-2">
              HUD Oxígeno
            </p>
            <ul className="space-y-1.5 text-sm text-white/85">
              <li className="flex justify-between gap-2">
                <span className="text-white/45">Masa de Manto</span>
                <span className="font-medium tabular-nums">$0.00</span>
              </li>
              <li className="flex justify-between gap-2">
                <span className="text-white/45">Margen de Ocupación</span>
                <span className="font-medium tabular-nums">00%</span>
              </li>
              <li className="flex justify-between gap-2">
                <span className="text-white/45">Oxígeno Libre</span>
                <span className="font-medium tabular-nums text-[#ff0055]">00%</span>
              </li>
            </ul>
          </div>
        )}
      </header>

      <section className="pt-5 pb-2 shrink-0">
        <p className="text-center text-[10px] uppercase tracking-[0.25em] text-white/35 mb-2">
          Balance global · Long / Short
        </p>
        <div className="h-4 rounded-full w-[90%] mx-auto overflow-hidden flex border border-white/10">
          <div className="h-full w-1/2 bg-[#ff0055]/40" title="Long 00%" />
          <div className="h-full w-1/2 bg-[#1a1d26]" title="Short 00%" />
        </div>
        <div className="w-[90%] mx-auto mt-1.5 flex justify-between text-[10px] tracking-wider text-white/40">
          <span>LONG 00%</span>
          <span>SHORT 00%</span>
        </div>
      </section>

      <section className="px-4 pt-4 space-y-2 shrink-0">
        <p className="text-[10px] uppercase tracking-[0.25em] text-white/35 px-1 mb-1">
          Vanguardia · Top 5
        </p>
        {vanguardia.map((coin) => (
          <AssetRow key={coin.id} coin={coin} onOpen={() => setSelectedAsset(coin.id)} />
        ))}
      </section>

      <div className="flex flex-col items-center pt-3 pb-2 shrink-0">
        <button
          type="button"
          onClick={() => setIsExpanded((v) => !v)}
          aria-label={isExpanded ? "Contraer batallón" : "Expandir batallón"}
          aria-expanded={isExpanded}
          className="w-11 h-11 flex items-center justify-center rounded-full border border-white/10 text-white/50 hover:text-[#ff0055] hover:border-[#ff0055]/40 active:scale-95 transition-all cursor-pointer"
        >
          <svg
            width="18"
            height="18"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2.2"
            strokeLinecap="round"
            strokeLinejoin="round"
            className={`transition-transform duration-500 ease-in-out ${
              isExpanded ? "rotate-180" : "rotate-0"
            }`}
          >
            <polyline points="6 9 12 15 18 9" />
          </svg>
        </button>

        <div
          className={`w-full px-4 transition-all duration-500 ease-in-out overflow-hidden ${
            isExpanded ? "max-h-[1000px] opacity-100 mt-2" : "max-h-0 opacity-0 mt-0"
          }`}
        >
          <p className="text-[10px] uppercase tracking-[0.25em] text-white/30 px-1 mb-2">
            Batallón · resto de la flota
          </p>
          <div className="space-y-2 pb-2">
            {batallon.map((coin) => (
              <AssetRow key={coin.id} coin={coin} onOpen={() => setSelectedAsset(coin.id)} />
            ))}
          </div>
        </div>
      </div>

      <div className="mx-4 mb-8 mt-2 min-h-[300px] flex items-center justify-center rounded-2xl border border-dashed border-white/10 bg-[#0d0f14]/60">
        <p className="text-sm tracking-wide text-white/25 italic">
          Análisis Temporal / Gráficas
        </p>
      </div>

      {selectedAsset && (
        <AssetDetail symbol={selectedAsset} onClose={() => setSelectedAsset(null)} />
      )}
    </div>
  );
}

function AssetRow({ coin, onOpen }) {
  return (
    <button
      type="button"
      onClick={onOpen}
      className="w-full flex items-center gap-3 px-3 py-3 rounded-xl bg-[#12141a] border border-white/5 active:scale-95 transition-transform text-left cursor-pointer"
    >
      <span className="w-12 shrink-0 text-sm font-semibold tracking-wider text-white/90">
        {coin.id}
      </span>
      <div className="flex-1 h-2.5 rounded-full overflow-hidden flex border border-white/5">
        <div className="h-full w-1/2 bg-[#ff0055]/35" />
        <div className="h-full w-1/2 bg-[#2a2e3a]" />
      </div>
      <span className="w-14 shrink-0 text-right text-[10px] tabular-nums text-white/35">
        00/00
      </span>
    </button>
  );
}
