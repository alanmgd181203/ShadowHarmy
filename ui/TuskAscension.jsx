import { useEffect, useMemo, useRef, useState } from "react";
import AspiranteStar from "./AspiranteStar.jsx";
import DeploymentAltar from "./DeploymentAltar.jsx";
import { loadMarchId, marchById, persistMarchaBackend, saveMarchId, hydrateMarchFromBackend } from "./deploymentMarches.js";
import { featureEncendida } from "./featuresApagadas.js";
import {
  DEMO_PROGRESS,
  FORMA_CLIP,
  crackFillRatio,
  equityLabelForNode,
  flattenNodeOrder,
  nextAchievedAlongPotential,
  progressFromPlan,
  ranksFromHorizon,
  resolveNodePhase,
  resolveRankPhase,
} from "./ascensionScaffold.js";

/**
 * Camino de Ascensión — Aspirante→Aprendiz→Brujo→Chamán (pase 13 Santos).
 * Altar 4 marchas: featuresApagadas → altarTresMarchas (nombre legado).
 * Fuente marcha: data/marcha_despliegue.json (hidratar Ascensión).
 */
const ALTAR_TRES_MARCHAS_ON = featureEncendida("altarTresMarchas");
const MARCHA_DEFAULT = "marcha_forzada";
const ESTADO_VIVO_URL = "/data/estado_vivo.json";
const PLAN_POLL_MS = 4000;

function NodeShell({ forma, escala, etiqueta, valor, peso, phase, revealDelay, lit, forging }) {
  const clip = FORMA_CLIP[forma] || FORMA_CLIP.rombo;
  const size =
    escala === "sm"
      ? "min-h-[3.25rem] w-[72%] max-w-[11rem]"
      : escala === "md"
        ? "min-h-[4.25rem] w-[82%] max-w-[14rem]"
        : escala === "lg"
          ? "min-h-[5.5rem] w-[92%] max-w-[18rem]"
          : "min-h-[7rem] w-[98%] max-w-none";

  const pesoClass =
    peso === "coloso"
      ? "asc-peso-coloso"
      : peso === "fortificado"
        ? "asc-peso-fortificado"
        : peso === "firme"
          ? "asc-peso-firme"
          : "asc-peso-fragil";

  const phaseClass =
    phase === "frontier"
      ? "asc-node-frontier"
      : phase === "achieved"
        ? "asc-node-achieved"
        : phase === "potential"
          ? "asc-node-potential"
          : "asc-node-locked";

  const reveal =
    lit && (phase === "frontier" || phase === "achieved") ? "asc-node-reveal" : "";
  const forgeClass = forging ? "asc-node-forge" : "";
  const nodeClass = [
    "asc-node",
    "relative",
    size,
    pesoClass,
    phaseClass,
    reveal,
    forgeClass,
    "flex",
    "flex-col",
    "items-center",
    "justify-center",
    "gap-0.5",
    "px-3",
    "py-2",
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div
      className={nodeClass}
      style={{
        clipPath: clip,
        animationDelay: revealDelay != null ? `${revealDelay}ms` : undefined,
      }}
    >
      {(peso === "fortificado" || peso === "coloso") && phase !== "locked" ? (
        <span className="asc-node-texture absolute inset-0 opacity-30 pointer-events-none" aria-hidden />
      ) : null}
      {phase === "potential" ? (
        <span className="asc-hologram-dash absolute inset-0 pointer-events-none" aria-hidden />
      ) : null}
      <span className="asc-node-label relative z-10 text-[9px] uppercase tracking-[0.22em]">{etiqueta}</span>
      <span className="asc-node-value relative z-10 font-mono text-sm">{valor}</span>
    </div>
  );
}

function ShadowPit({ progress, order, forgingId }) {
  const phase = resolveNodePhase("n0_gestacion", progress, order);
  const inPit = phase === "frontier" || phase === "achieved";
  return (
    <div className={`asc-shadow-pit relative mx-auto ${inPit ? "asc-shadow-pit-focus" : ""}`}>
      <div className="asc-shadow-pit-mouth" aria-hidden />
      <div className="asc-shadow-pit-smoke" aria-hidden />
      {forgingId === "n0_gestacion" ? <span className="asc-gestacion-pulse" aria-hidden /> : null}
    </div>
  );
}

function RankBlock({ rank, order, progress, lit, forgingId, isLastNearCore, gapAchieved, gapPotential }) {
  if (rank.layout === "gestacion") {
    return (
      <div className="relative" style={{ marginBottom: rank.gapBefore }}>
        <ShadowPit progress={progress} order={order} forgingId={forgingId} />
        {!isLastNearCore && (
          <div
            className={`asc-tendril pointer-events-none absolute left-1/2 -translate-x-1/2 w-[3px] ${
              gapAchieved ? "asc-tendril-lit" : gapPotential ? "asc-tendril-potential" : "asc-tendril-dim"
            }`}
            style={{ top: "100%", height: rank.gapBefore }}
            aria-hidden
          />
        )}
      </div>
    );
  }

  if (rank.layout === "estrella") {
    const rankPhase = resolveRankPhase(rank, progress, order);
    const rankClass =
      rankPhase === "frontier"
        ? "asc-rank-frontier"
        : rankPhase === "achieved"
          ? "asc-rank-achieved"
          : rankPhase === "potential"
            ? "asc-rank-potential"
            : "asc-rank-locked";

    return (
      <section className={`relative ${rankClass}`} style={{ marginBottom: rank.gapBefore }}>
        <header className="mb-3 text-center">
          <h3 className="asc-rank-title text-lg font-light tracking-[0.28em] uppercase">{rank.titulo}</h3>
        </header>
        <AspiranteStar progress={progress} order={order} lit={lit} forgingId={forgingId} />
        {!isLastNearCore && (
          <div
            className={`asc-tendril pointer-events-none absolute left-1/2 -translate-x-1/2 w-[3px] ${
              gapAchieved ? "asc-tendril-lit" : gapPotential ? "asc-tendril-potential" : "asc-tendril-dim"
            }`}
            style={{ top: "100%", height: rank.gapBefore }}
            aria-hidden
          />
        )}
      </section>
    );
  }

  const align =
    rank.zigzag === "left"
      ? "items-start pl-2"
      : rank.zigzag === "right"
        ? "items-end pr-2"
        : "items-center";

  const rankPhase = resolveRankPhase(rank, progress, order);
  const rankClass =
    rankPhase === "frontier"
      ? "asc-rank-frontier"
      : rankPhase === "achieved"
        ? "asc-rank-achieved"
        : rankPhase === "potential"
          ? "asc-rank-potential"
          : "asc-rank-locked";

  const peso = rank.peso || "fragil";
  const lockedUntilCrown =
    rank.id === "aprendiz" && resolveNodePhase("asp_corona", progress, order) === "locked";

  return (
    <section
      className={`relative flex flex-col ${align} ${rankClass} asc-rank-${peso} ${
        lockedUntilCrown ? "opacity-40" : ""
      }`}
      style={{ marginBottom: rank.gapBefore }}
    >
      <header
        className={`mb-3 max-w-[85%] ${
          rank.zigzag === "right" ? "text-right" : rank.zigzag === "center" ? "text-center" : "text-left"
        }`}
      >
        <h3 className="asc-rank-title text-lg font-light tracking-wide">{rank.titulo}</h3>
      </header>

      <div className={`flex flex-col gap-4 w-full ${align}`}>
        {rank.nodes.map((n, ni) => {
          const phase = resolveNodePhase(n.id, progress, order);
          const delay =
            phase === "frontier" || phase === "achieved" ? 80 + ni * 70 : phase === "potential" ? 40 + ni * 40 : 0;
          return (
            <NodeShell
              key={n.id}
              {...n}
              peso={n.peso || peso}
              phase={phase}
              lit={lit}
              forging={forgingId === n.id}
              revealDelay={lit ? delay : undefined}
            />
          );
        })}
      </div>

      {!isLastNearCore && (
        <div
          className={`asc-tendril pointer-events-none absolute left-1/2 -translate-x-1/2 w-[3px] ${
            gapAchieved ? "asc-tendril-lit" : gapPotential ? "asc-tendril-potential" : "asc-tendril-dim"
          }`}
          style={{ top: "100%", height: rank.gapBefore }}
          aria-hidden
        />
      )}
    </section>
  );
}

function SoulThermometer({ pFill, aFill }) {
  return (
    <aside className="asc-soul-thermo pointer-events-none absolute left-1 top-24 bottom-8 w-3 z-[3]" aria-hidden>
      <div className="asc-soul-well absolute inset-0" />
      <div
        className="asc-soul-smoke absolute bottom-0 left-0 right-0"
        style={{ height: `${Math.max(8, pFill * 100)}%` }}
      />
      <div
        className="asc-soul-fire absolute bottom-0 left-0 right-0"
        style={{ height: `${Math.max(4, aFill * 100)}%` }}
      />
      <span className="asc-soul-label">almas</span>
    </aside>
  );
}

function GravityOrb({ onClick, burst }) {
  const orbClass = [
    "tusk-gravity-orb relative h-11 w-11 rounded-full border border-[#2a2f3a] bg-black pointer-events-auto",
    "active:scale-95 transition-transform duration-300",
    burst ? "animate-pulse" : "",
  ].join(" ");

  return (
    <button
      type="button"
      onClick={onClick}
      aria-label="Abrir Camino de Ascension · Tusk"
      className={orbClass}
    >
      <span className="tusk-orb-core absolute inset-[3px] rounded-full border border-[#1a1d26]" />
      <span className="tusk-orb-cracks absolute inset-0 opacity-60" aria-hidden />
      <span className="absolute inset-0 flex items-center justify-center text-[10px] tracking-widest text-[#5c5340]">
        *
      </span>
    </button>
  );
}

export function TuskOrbButton({ onOpen }) {
  return (
    <div className="pointer-events-auto absolute z-[12]" style={{ top: "9%", left: "52%" }}>
      <GravityOrb onClick={onOpen} />
    </div>
  );
}

function AscensionTrack({ progress, march, lit, forgingId, onResetMarch, onClose }) {
  const order = useMemo(() => flattenNodeOrder(), []);
  const visualRanks = useMemo(() => ranksFromHorizon(), []);
  const potentialFill = crackFillRatio(progress.potentialNodeId, order);
  const achievedFill = crackFillRatio(progress.achievedNodeId, order);
  const [pFill, setPFill] = useState(0);
  const [aFill, setAFill] = useState(0);

  useEffect(() => {
    setPFill(0);
    setAFill(0);
    const id = requestAnimationFrame(() => {
      setPFill(potentialFill);
      setAFill(achievedFill);
    });
    return () => cancelAnimationFrame(id);
  }, [potentialFill, achievedFill]);

  const aIdx = order.indexOf(progress.achievedNodeId);
  const pIdx = order.indexOf(progress.potentialNodeId);

  return (
    <div className="fixed inset-0 z-[60] flex flex-col" role="dialog" aria-modal="true" aria-label="Camino de Ascension">
      <div className="absolute inset-0 bg-[#050608]/60 backdrop-blur-xl" aria-hidden />
      <div className="tusk-ink-bleed pointer-events-none absolute inset-0 z-[1]" aria-hidden />

      <div className="relative z-[2] flex flex-col h-full max-w-[430px] w-full mx-auto pointer-events-none">
        <header className="pointer-events-auto flex items-start justify-between px-4 pt-[max(0.75rem,env(safe-area-inset-top))] pb-2 gap-2">
          <div>
            <p className="text-[10px] uppercase tracking-[0.4em] text-[#6a5a40]">Tusk</p>
            <h2 className="text-xl text-[#e8e4d8] font-light tracking-[0.12em]">Camino de Ascension</h2>
            {march ? (
              <p className="text-[10px] text-[#6a5a40] mt-1 tracking-wide">{march.titulo}</p>
            ) : null}
            {progress?.live ? (
              <p className="text-[10px] text-[#8a7a55] mt-1 tracking-wide">
                {progress.nivel || "—"} · {progress.equityLabel}
                {progress.activoPreferido ? ` · foco ${progress.activoPreferido}` : ""}
                {progress.potenciaN != null ? ` · potencia ${progress.nLogrados || 0}/${progress.potenciaN}` : ""}
              </p>
            ) : null}
          </div>
          <div className="flex flex-col items-end gap-2 shrink-0">
            <button
              type="button"
              onClick={onClose}
              className="h-10 w-10 rounded-full border border-[#2a2f3a] bg-black/80 text-[#8a8490] text-lg leading-none"
              aria-label="Cerrar"
            >
              x
            </button>
            <button
              type="button"
              onClick={onResetMarch}
              className="text-[9px] uppercase tracking-[0.15em] text-[#4a5160] border border-[#1f222e] px-2 py-1"
            >
              cambiar marcha
            </button>
          </div>
        </header>

        <div className="relative flex-1 min-h-0 flex flex-col">
          <SoulThermometer pFill={pFill} aFill={aFill} />

          <div className="pointer-events-auto flex-1 overflow-y-auto overscroll-contain pl-6 pr-4 pb-[max(2rem,env(safe-area-inset-bottom))]">
            <div className="relative min-h-full pt-2 pb-4">
              <div className="tusk-smoke-crack tusk-smoke-crack-dim pointer-events-none absolute left-[48%] top-2 bottom-2 w-[3px] -translate-x-1/2" aria-hidden />
              <div
                className="tusk-smoke-crack tusk-smoke-crack-potential pointer-events-none absolute left-[48%] bottom-2 w-[3px] -translate-x-1/2"
                style={{
                  height: `calc((100% - 1rem) * ${pFill})`,
                  transition: "height 0.9s cubic-bezier(0.22, 1, 0.36, 1)",
                }}
                aria-hidden
              />
              <div
                className="tusk-smoke-crack tusk-smoke-crack-lit pointer-events-none absolute left-[48%] bottom-2 w-[3px] -translate-x-1/2"
                style={{
                  height: `calc((100% - 1rem) * ${aFill})`,
                  transition: "height 0.75s cubic-bezier(0.22, 1, 0.36, 1)",
                }}
                aria-hidden
              />

              <div className="relative flex flex-col">
                {visualRanks.map((rank, i) => {
                  const anchor =
                    rank.layout === "estrella"
                      ? rank.nodes[rank.nodes.length - 1]
                      : rank.nodes[0];
                  const anchorIdx = order.indexOf(anchor.id);
                  const gapAchieved = anchorIdx >= 0 && anchorIdx <= aIdx;
                  const gapPotential = anchorIdx >= 0 && anchorIdx <= pIdx && !gapAchieved;
                  return (
                    <RankBlock
                      key={rank.id}
                      rank={rank}
                      order={order}
                      progress={progress}
                      lit={lit}
                      forgingId={forgingId}
                      isLastNearCore={i === visualRanks.length - 1}
                      gapAchieved={gapAchieved}
                      gapPotential={gapPotential}
                    />
                  );
                })}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function TuskAscension({ onClose }) {
  const order = useMemo(() => flattenNodeOrder(), []);
  const [marchId, setMarchId] = useState(() => {
    const saved = loadMarchId();
    if (saved) return saved;
    return ALTAR_TRES_MARCHAS_ON ? null : MARCHA_DEFAULT;
  });
  const [duracionDias, setDuracionDias] = useState(null);
  const [collapsing, setCollapsing] = useState(false);
  const [showTrack, setShowTrack] = useState(() => {
    if (!ALTAR_TRES_MARCHAS_ON) return true;
    return Boolean(loadMarchId());
  });
  const [lit, setLit] = useState(false);
  const [progress, setProgress] = useState(() => ({ ...DEMO_PROGRESS }));
  const [liveMode, setLiveMode] = useState(false);
  const [forgingId, setForgingId] = useState(null);
  const [freqManto, setFreqManto] = useState(null);
  const forgeTimer = useRef(null);

  const march = marchById(marchId) || (!ALTAR_TRES_MARCHAS_ON ? marchById(MARCHA_DEFAULT) : null);

  function sparkForge(nodeId) {
    if (forgeTimer.current) clearTimeout(forgeTimer.current);
    setForgingId(nodeId);
    forgeTimer.current = window.setTimeout(() => setForgingId(null), 1100);
  }

  function handleChoose(m, opts = {}) {
    if (m.requiereDuracion) {
      const d = Number(opts.duracionDias);
      if (!(d > 0)) return;
      setDuracionDias(d);
    } else {
      setDuracionDias(null);
    }
    setCollapsing(true);
    saveMarchId(m.id);
    persistMarchaBackend(m.id, {
      duracionDias: opts.duracionDias,
    });
    setMarchId(m.id);
    window.setTimeout(() => {
      setCollapsing(false);
      setShowTrack(true);
      setProgress({
        ...DEMO_PROGRESS,
        achievedNodeId: "n0_gestacion",
        equityLabel: equityLabelForNode("n0_gestacion"),
      });
      setLit(false);
      requestAnimationFrame(() => setLit(true));
      sparkForge("n0_gestacion");
    }, 480);
  }

  function resetMarch() {
    if (!ALTAR_TRES_MARCHAS_ON) return;
    saveMarchId(null);
    setMarchId(null);
    setDuracionDias(null);
    setShowTrack(false);
    setLit(false);
    setForgingId(null);
    setLiveMode(false);
    setProgress({ ...DEMO_PROGRESS });
  }

  // Hidratar desde JSON de marcha (altar solo si no hay marcha en disco)
  useEffect(() => {
    let cancelled = false;
    (async () => {
      const h = await hydrateMarchFromBackend();
      if (cancelled || !h) return;
      saveMarchId(h.id);
      setMarchId(h.id);
      if (h.duracionDias != null) setDuracionDias(h.duracionDias);
      setShowTrack(true);
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  // Pulso vivo: equity Tusk → nodos del pase (si hay plan en estado_vivo)
  useEffect(() => {
    if (!showTrack) return undefined;
    let cancelled = false;
    let lastAchieved = null;

    async function tick() {
      try {
        const res = await fetch(ESTADO_VIVO_URL, { cache: "no-store" });
        if (!res.ok || cancelled) return;
        const data = await res.json();
        const plan = data?.igris?.plan_crecimiento || data?.plan_crecimiento;
        if (data?.igris?.frecuencia_manto) setFreqManto(data.igris.frecuencia_manto);
        const next = progressFromPlan(plan);
        if (!next || cancelled) return;
        setLiveMode(true);
        setProgress(next);
        setLit(true);
        if (next.achievedNodeId && next.achievedNodeId !== lastAchieved) {
          lastAchieved = next.achievedNodeId;
          sparkForge(next.achievedNodeId);
        }
      } catch {
        /* sin panel → demo */
      }
    }

    tick();
    const id = window.setInterval(tick, PLAN_POLL_MS);
    return () => {
      cancelled = true;
      window.clearInterval(id);
    };
  }, [showTrack]);

  useEffect(() => {
    if (!showTrack || !march || liveMode) return undefined;
    const pot = DEMO_PROGRESS.potentialNodeId;
    let achieved = "n0_gestacion";
    setProgress({
      ...DEMO_PROGRESS,
      achievedNodeId: achieved,
      equityLabel: equityLabelForNode(achieved),
    });
    setLit(true);
    sparkForge(achieved);

    const timers = [];
    const schedule = () => {
      const next = nextAchievedAlongPotential(achieved, pot, order);
      if (next === achieved) return;
      achieved = next;
      setProgress({
        potentialNodeId: pot,
        achievedNodeId: next,
        equityLabel: equityLabelForNode(next),
      });
      sparkForge(next);
      const a = order.indexOf(achieved);
      const p = order.indexOf(pot);
      if (a < p) timers.push(window.setTimeout(schedule, march.ritmoMs));
    };
    timers.push(window.setTimeout(schedule, march.ritmoMs + 250));
    return () => {
      timers.forEach(clearTimeout);
      if (forgeTimer.current) clearTimeout(forgeTimer.current);
    };
  }, [showTrack, marchId, march, order, liveMode]);

  return (
    <>
      {ALTAR_TRES_MARCHAS_ON && !showTrack && (
        <DeploymentAltar
          onChoose={handleChoose}
          collapsing={collapsing}
          onClose={onClose}
          frecuenciaManto={freqManto}
        />
      )}
      {showTrack && (
        <AscensionTrack
          progress={{
            potentialNodeId: progress.potentialNodeId || DEMO_PROGRESS.potentialNodeId,
            achievedNodeId: progress.achievedNodeId || "n0_gestacion",
            equityLabel: progress.equityLabel || DEMO_PROGRESS.equityLabel,
            live: Boolean(progress.live),
            nivel: progress.nivel,
            activoPreferido: progress.activoPreferido,
            potenciaN: progress.potenciaN,
            nLogrados: progress.nLogrados,
          }}
          march={march}
          lit={lit}
          forgingId={forgingId}
          onClose={onClose}
          onResetMarch={resetMarch}
        />
      )}
    </>
  );
}
