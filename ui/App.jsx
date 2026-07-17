import { useState } from "react";
import IgrisPanel from "./IgrisPanel.jsx";

import imgTusk from "../assets/portales/tusk.png";
import imgBeru from "../assets/portales/beru.png";
import imgKamish from "../assets/portales/kamish.png";
import imgBellion from "../assets/portales/bellion.png";
import imgGreed from "../assets/portales/greed.png";
import imgIgris from "../assets/portales/igris.png";

/**
 * Cascada + umbral cinematográfico hacia Igris / MANTO.
 * Layout absoluto de portales intacto; solo clases dinámicas.
 */
const PORTALS = [
  { id: "tusk", src: imgTusk, label: "Tusk", style: { top: "-1%", left: "-14%", width: "70%", zIndex: 8 } },
  { id: "beru", src: imgBeru, label: "Beru", style: { top: "13%", right: "-18%", width: "68%", zIndex: 7 } },
  { id: "kamish", src: imgKamish, label: "Kamish", style: { top: "28%", left: "-22%", width: "72%", zIndex: 6 } },
  { id: "bellion", src: imgBellion, label: "Bellion", style: { top: "44%", right: "8%", width: "60%", zIndex: 5 } },
  { id: "greed", src: imgGreed, label: "Greed", style: { top: "58%", left: "-24%", width: "72%", zIndex: 4 } },
  { id: "igris", src: imgIgris, label: "Igris", style: { top: "74%", right: "-16%", width: "68%", zIndex: 3 } },
];

export default function App() {
  const [activeGeneral, setActiveGeneral] = useState(null);
  const [isTransitioning, setIsTransitioning] = useState(false);

  const umbralIgris = isTransitioning && activeGeneral === "igris";

  function openIgris() {
    setIsTransitioning(true);
    setActiveGeneral("igris");
  }

  function closeIgris() {
    setIsTransitioning(false);
    setActiveGeneral(null);
  }

  return (
    <div className="relative min-h-screen w-full max-w-[430px] mx-auto bg-[#0a0c10] overflow-hidden">
      <div className="relative w-full h-[100dvh] min-h-[720px]">
        {PORTALS.map((p) => {
          const isIgris = p.id === "igris";
          const wrapStyle = {
            ...p.style,
            zIndex: isIgris && umbralIgris ? 40 : p.style.zIndex,
          };

          const imgClass = [
            "w-full h-auto max-w-none select-none",
            "transition-all duration-1000 ease-in-out",
            "origin-center",
            isIgris
              ? umbralIgris
                ? "scale-150 opacity-100 brightness-125"
                : "scale-100 opacity-100 brightness-100"
              : umbralIgris
                ? "opacity-0 scale-75 blur-md"
                : "opacity-90 scale-100 blur-0",
          ].join(" ");

          return (
            <div
              key={p.id}
              className={`absolute pointer-events-none transition-all duration-1000 ease-in-out ${
                isIgris && umbralIgris ? "opacity-100" : ""
              }`}
              style={wrapStyle}
            >
              {isIgris ? (
                <button
                  type="button"
                  onClick={openIgris}
                  aria-label="Abrir Manto · Igris"
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
      </div>

      {activeGeneral === "igris" && (
        <IgrisPanel onClose={closeIgris} />
      )}
    </div>
  );
}
