import { useState } from "react";
import { DEPLOYMENT_MARCHES, etaLoteLabel } from "./deploymentMarches.js";

/**
 * Altar de decision — ritmo de despliegue (4 marchas).
 * Personalizado: dias obligatorios + Calibrar.
 */
export default function DeploymentAltar({ onChoose, collapsing, onClose, frecuenciaManto }) {
  const [diasCustom, setDiasCustom] = useState("");
  const [errCustom, setErrCustom] = useState("");

  function choose(m) {
    if (m.requiereDuracion) {
      const d = Number(diasCustom);
      if (!(d > 0)) {
        setErrCustom("Escribe cuantos dias (~T). Sin default.");
        return;
      }
      setErrCustom("");
      onChoose(m, { duracionDias: d });
      return;
    }
    setErrCustom("");
    onChoose(m, {});
  }

  return (
    <div
      className={`fixed inset-0 z-[70] flex flex-col ${collapsing ? "asc-altar-collapse" : ""}`}
      role="dialog"
      aria-modal="true"
      aria-label="Altar de despliegue"
    >
      <div className="absolute inset-0 bg-[#050608]/75 backdrop-blur-xl" aria-hidden />
      <div className="tusk-ink-bleed pointer-events-none absolute inset-0 z-[1]" aria-hidden />

      <div className="relative z-[2] flex flex-col h-full max-w-[430px] w-full mx-auto px-4 pt-[max(1rem,env(safe-area-inset-top))] pb-[max(1.5rem,env(safe-area-inset-bottom))]">
        <header className="mb-6 relative text-center">
          <button
            type="button"
            onClick={onClose}
            className="absolute right-0 top-0 h-10 w-10 rounded-full border border-[#2a2f3a] bg-black/80 text-[#8a8490] text-lg leading-none"
            aria-label="Cerrar"
          >
            x
          </button>
          <p className="text-[10px] uppercase tracking-[0.4em] text-[#6a5a40]">Tusk · Bellion</p>
          <h2 className="text-xl text-[#e8e4d8] font-light tracking-[0.1em] mt-1">
            Ritmo del ejercito
          </h2>
          <p className="text-[12px] text-[#5a6170] mt-2 max-w-[20rem] mx-auto leading-relaxed">
            El presupuesto lo marca Tusk. Igris construye el manto. Elige con que prisa entra la
            sangre. Fill 100% · reserva 1.
          </p>
        </header>

        <div className="flex-1 overflow-y-auto flex flex-col gap-3">
          {DEPLOYMENT_MARCHES.map((m) => {
            const eta = etaLoteLabel(frecuenciaManto, m.id);
            return (
              <div
                key={m.id}
                className="asc-march-card group text-left w-full border border-[#1f222e] bg-[#0a0a0c]/90 px-4 py-4"
                style={{
                  clipPath: "polygon(0 0, 100% 0, 100% 88%, 96% 100%, 0 100%)",
                }}
              >
                <button
                  type="button"
                  onClick={() => choose(m)}
                  className="w-full text-left transition-all duration-300 active:scale-[0.99] hover:border-[#3a3428]"
                >
                  <div className="flex items-baseline justify-between gap-2">
                    <h3 className="text-[15px] text-[#d8d4c8] tracking-wide">{m.titulo}</h3>
                    <span className="text-[10px] uppercase tracking-[0.2em] text-[#6a5a40]">{m.tagline}</span>
                  </div>
                  <p className="text-[11px] text-[#5a6170] mt-1">{m.voz}</p>

                  <div className="mt-3 grid grid-cols-2 gap-2">
                    <div className="border border-[#1a1d26] bg-black/40 px-2 py-2">
                      <p className="text-[9px] uppercase tracking-[0.18em] text-[#3a3f4d]">ETA lote</p>
                      <p className="font-mono text-sm text-[#8a8490] mt-0.5">{eta}</p>
                      <p className="text-[9px] text-[#2e3440] mt-0.5">{m.tiempoNota}</p>
                    </div>
                    <div className="border border-[#2a2418] bg-[#100e0a]/80 px-2 py-2">
                      <p className="text-[9px] uppercase tracking-[0.18em] text-[#6a5a40]">{m.impacto.label}</p>
                      <p className="font-mono text-sm text-[#e8dcc0] mt-0.5">{m.impacto.valor}</p>
                      <p className="text-[9px] text-[#5a5340] mt-0.5 leading-snug">{m.impacto.detalle}</p>
                    </div>
                  </div>
                </button>

                {m.requiereDuracion ? (
                  <div className="mt-3 flex flex-col gap-2 border-t border-[#1a1d26] pt-3">
                    <label className="text-[10px] uppercase tracking-[0.18em] text-[#6a5a40]">
                      Duracion (~T dias) — obligatoria
                    </label>
                    <div className="flex gap-2">
                      <input
                        type="number"
                        min="0.1"
                        step="0.1"
                        value={diasCustom}
                        onChange={(e) => setDiasCustom(e.target.value)}
                        placeholder="ej. 7"
                        className="flex-1 bg-black/60 border border-[#2a2f3a] px-2 py-2 font-mono text-sm text-[#e8e4d8]"
                      />
                      <button
                        type="button"
                        onClick={() => choose(m)}
                        className="px-3 py-2 border border-[#3a3428] text-[11px] uppercase tracking-[0.15em] text-[#e8dcc0]"
                      >
                        Calibrar
                      </button>
                    </div>
                    {errCustom ? (
                      <p className="text-[11px] text-[#c07060]">{errCustom}</p>
                    ) : null}
                  </div>
                ) : null}
              </div>
            );
          })}
        </div>

        <p className="mt-4 text-center text-[10px] tracking-[0.2em] uppercase text-[#2a2e38]">
          costos = raiz · elige con los ojos abiertos
        </p>
      </div>
    </div>
  );
}
