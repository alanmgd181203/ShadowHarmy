import { useState } from "react";
import BeruPanel from "./BeruPanel.jsx";
import BellionPanel from "./BellionPanel.jsx";
import TuskAscension, { TuskOrbButton } from "./TuskAscension.jsx";

import imgTusk from "../assets/portales/tusk.png";
import imgBeru from "../assets/portales/beru.png";
import imgKamish from "../assets/portales/kamish.png";
import imgBellion from "../assets/portales/bellion.png";
import imgGreed from "../assets/portales/greed.png";
import imgIgris from "../assets/portales/igris.png";

/**
 * Cascada + umbral Beru/Bellion + Orbe de Ascensión (Tusk).
 * Igris de baja: sello visible, sin umbral (panel retirado).
 * Cosas apagadas: ui/featuresApagadas.js
 */
const PORTALS = [
  { id: "tusk", src: imgTusk, label: "Tusk", aura: "#00ff66", style: { top: "-1%", left: "-14%", width: "70%", zIndex: 8 } },
  { id: "beru", src: imgBeru, label: "Beru", aura: "#00f0ff", style: { top: "13%", right: "-18%", width: "68%", zIndex: 7 } },
  { id: "kamish", src: imgKamish, label: "Kamish", aura: "#4a72ff", style: { top: "28%", left: "-22%", width: "72%", zIndex: 6 } },
  { id: "bellion", src: imgBellion, label: "Bellion", aura: "#a100ff", style: { top: "44%", right: "8%", width: "60%", zIndex: 5 } },
  { id: "greed", src: imgGreed, label: "Greed", aura: "#e0115f", style: { top: "58%", left: "-24%", width: "72%", zIndex: 4 } },
  { id: "igris", src: imgIgris, label: "Igris", aura: "#ff0055", style: { top: "74%", right: "-16%", width: "68%", zIndex: 3 } },
];

const UMBRAL_IDS = new Set(["beru", "bellion"]);

const ARIA = {
  beru: "Abrir flota · Beru",
  bellion: "Abrir oído · Bellion",
};

export default function App() {
  const [activeGeneral, setActiveGeneral] = useState(null);
  const [isTransitioning, setIsTransitioning] = useState(false);
  const [ascensionOpen, setAscensionOpen] = useState(false);

  const umbralActivo =
    isTransitioning &&
    (activeGeneral === "beru" || activeGeneral === "bellion");
  const vanguardiaOculta = umbralActivo || ascensionOpen;

  function openGeneral(id) {
    setAscensionOpen(false);
    setIsTransitioning(true);
    setActiveGeneral(id);
  }

  function closeGeneral() {
    setIsTransitioning(false);
    setActiveGeneral(null);
  }

  return (
    <div className="relative min-h-screen w-full max-w-[430px] mx-auto bg-[#0a0c10] overflow-hidden">
      <div className="relative w-full h-[100dvh] min-h-[720px]">
        {/* Aura de color detrás de cada sello · humo/video sigue apagado */}
        <div
          className={`absolute inset-0 z-0 pointer-events-none overflow-hidden transition-opacity duration-1000 ${
            vanguardiaOculta ? "opacity-0" : "opacity-100"
          }`}
          aria-hidden
        >
          {PORTALS.map((p) => (
            <div key={`aura-${p.id}`} className="absolute" style={{ ...p.style, zIndex: 0 }}>
              <div
                className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-64 h-64 rounded-full blur-[64px] opacity-45"
                style={{ background: p.aura }}
              />
            </div>
          ))}
        </div>

        {PORTALS.map((p) => {
          const esUmbral = UMBRAL_IDS.has(p.id);
          const enFoco = umbralActivo && activeGeneral === p.id;
          const wrapStyle = {
            ...p.style,
            zIndex: enFoco ? 40 : p.style.zIndex,
          };

          const imgClass = [
            "w-full h-auto max-w-none select-none",
            "transition-all duration-1000 ease-in-out",
            "origin-center",
            esUmbral && enFoco
              ? "scale-150 opacity-100 brightness-125"
              : esUmbral && !vanguardiaOculta
                ? "scale-100 opacity-100 brightness-100"
                : vanguardiaOculta
                  ? "opacity-0 scale-75 blur-md"
                  : "opacity-90 scale-100 blur-0",
          ].join(" ");

          return (
            <div
              key={p.id}
              className={`absolute pointer-events-none transition-all duration-1000 ease-in-out ${
                enFoco ? "opacity-100" : ""
              }`}
              style={wrapStyle}
            >
              {esUmbral ? (
                <button
                  type="button"
                  onClick={() => openGeneral(p.id)}
                  aria-label={ARIA[p.id] || `Abrir ${p.label}`}
                  className="block w-full p-0 m-0 bg-transparent border-0 cursor-pointer pointer-events-auto active:scale-[0.98]"
                >
                  <img
                    src={p.src}
                    alt={p.label}
                    draggable={false}
                    className={imgClass}
                  />
                </button>
              ) : (
                <img
                  src={p.src}
                  alt={p.label}
                  draggable={false}
                  className={`${imgClass} pointer-events-none`}
                />
              )}
            </div>
          );
        })}

        {!vanguardiaOculta && (
          <TuskOrbButton onOpen={() => setAscensionOpen(true)} />
        )}
      </div>

      {activeGeneral === "beru" && (
        <BeruPanel onClose={closeGeneral} />
      )}

      {activeGeneral === "bellion" && (
        <BellionPanel onClose={closeGeneral} />
      )}

      {ascensionOpen && (
        <TuskAscension onClose={() => setAscensionOpen(false)} />
      )}
    </div>
  );
}
