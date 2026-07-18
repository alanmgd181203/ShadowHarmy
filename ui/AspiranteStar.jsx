import { useEffect, useState } from "react";
import {
  ESTRELLA_LAYOUT,
  FORMA_CLIP,
  VANGUARDIA_SOLDADOS,
  resolveNodePhase,
} from "./ascensionScaffold.js";

function polarToPercent(angleDeg, rPct) {
  const rad = (angleDeg * Math.PI) / 180;
  const x = 50 + rPct * Math.sin(rad);
  const y = 50 - rPct * Math.cos(rad);
  return { left: `${x}%`, top: `${y}%` };
}

function isActive(phase) {
  return phase === "achieved" || phase === "frontier";
}

/**
 * Constelación dormida → ignición.
 * LOCKED = silueta muda · ACTIVE = cian + precio.
 * Centro = sello 0/5…5/5 (no total $104).
 */
export default function AspiranteStar({ progress, order, lit, forgingId }) {
  const [tipId, setTipId] = useState(null);

  const points = ESTRELLA_LAYOUT.map((p) => {
    const ship = VANGUARDIA_SOLDADOS.find((v) => v.id === p.id);
    const phase = resolveNodePhase(p.id, progress, order);
    const active = isActive(phase);
    const pos = polarToPercent(p.angle, p.r);
    return { ...p, ship, phase, active, pos };
  });

  const coronaPhase = resolveNodePhase("asp_corona", progress, order);
  const crowned = isActive(coronaPhase);
  const litCount = points.filter((p) => p.active).length;
  const fillPct = (litCount / 5) * 100;
  const clip = FORMA_CLIP.garra;

  useEffect(() => {
    if (!tipId) return undefined;
    const t = window.setTimeout(() => setTipId(null), 2200);
    return () => clearTimeout(t);
  }, [tipId]);

  function onClawTap(p) {
    if (p.active) {
      setTipId(null);
      return;
    }
    setTipId((cur) => (cur === p.id ? null : p.id));
  }

  const tip = points.find((p) => p.id === tipId);

  return (
    <div className="asp-star relative mx-auto w-full max-w-[20rem] aspect-square">
      <svg className="asp-star-web absolute inset-0 w-full h-full pointer-events-none" viewBox="0 0 100 100" aria-hidden>
        {points.map((p, i) => {
          const q = points[(i + 1) % points.length];
          const both = p.active && q.active;
          const px = 50 + p.r * Math.sin((p.angle * Math.PI) / 180);
          const py = 50 - p.r * Math.cos((p.angle * Math.PI) / 180);
          const qx = 50 + q.r * Math.sin((q.angle * Math.PI) / 180);
          const qy = 50 - q.r * Math.cos((q.angle * Math.PI) / 180);
          return (
            <line
              key={`edge-${p.id}`}
              x1={px}
              y1={py}
              x2={qx}
              y2={qy}
              className={both ? "asp-star-edge-lit" : "asp-star-edge-ghost"}
            />
          );
        })}
        {points.map((p) => {
          if (!p.active) return null;
          const px = 50 + p.r * Math.sin((p.angle * Math.PI) / 180);
          const py = 50 - p.r * Math.cos((p.angle * Math.PI) / 180);
          return (
            <line
              key={`spoke-${p.id}`}
              x1={50}
              y1={50}
              x2={px}
              y2={py}
              className={crowned ? "asp-star-spoke-crown" : "asp-star-spoke-lit"}
            />
          );
        })}
      </svg>

      <div
        className={`asp-corona absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 z-[2] ${
          crowned ? "asp-corona-on" : litCount > 0 ? "asp-corona-wait" : "asp-corona-off"
        } ${forgingId === "asp_corona" ? "asc-node-forge" : ""}`}
        aria-label={crowned ? "Vanguardia coronada" : `${litCount} de 5 soldados`}
      >
        <span className="asp-corona-fill" style={{ height: `${crowned ? 100 : fillPct}%` }} aria-hidden />
        <span className="asp-corona-label relative z-[1]">
          {crowned ? "corona" : `${litCount}/5`}
        </span>
      </div>

      {points.map((p) => {
        const forge = forgingId === p.id;
        return (
          <button
            key={p.id}
            type="button"
            className={`asp-claw absolute z-[3] -translate-x-1/2 -translate-y-1/2 ${
              p.active ? "asp-claw-on" : "asp-claw-locked"
            } ${forge ? "asc-node-forge" : ""} ${lit && p.active ? "asc-node-reveal" : ""}`}
            style={{
              left: p.pos.left,
              top: p.pos.top,
              clipPath: clip,
            }}
            onClick={() => onClawTap(p)}
            aria-label={
              p.active
                ? `${p.ship?.activo} activo · $${p.ship?.costoX}`
                : `${p.ship?.activo} dormido`
            }
          >
            {p.active ? (
              <>
                <span className="asp-claw-label">{p.ship?.activo}</span>
                <span className="asp-claw-val">${p.ship?.costoX}</span>
              </>
            ) : (
              <span className="asp-claw-ghost" aria-hidden />
            )}
          </button>
        );
      })}

      {tip?.ship ? (
        <p className="asp-tip absolute left-1/2 z-[4] -translate-x-1/2 bottom-1 px-3 py-1.5 text-center">
          Necesitas ${tip.ship.costoX} para invocar a {tip.ship.activo}
        </p>
      ) : null}
    </div>
  );
}
