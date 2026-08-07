import { useEffect, useState } from "react";
import {
  snapshotCero,
  desdeEstadoVivo,
  fmtUsd,
  fmtPct,
  fmtNum,
  fmtLev,
} from "./assetDetailModel.js";

const ESTADO_URL = "/data/estado_vivo.json";

/**
 * Sub-Santuario de activo — pantalla completa sobre el Manto.
 * Sin gráfica. Apalancamiento solo lectura (no modificar).
 */
export default function AssetDetail({ symbol, onClose }) {
  const [visible, setVisible] = useState(false);
  const [closing, setClosing] = useState(false);
  const [data, setData] = useState(() => snapshotCero(symbol));

  useEffect(() => {
    const id = requestAnimationFrame(() => setVisible(true));
    return () => cancelAnimationFrame(id);
  }, []);

  useEffect(() => {
    let alive = true;
    async function load() {
      try {
        const res = await fetch(`${ESTADO_URL}?t=${Date.now()}`, { cache: "no-store" });
        if (!res.ok) {
          if (alive) setData(snapshotCero(symbol));
          return;
        }
        const snap = await res.json();
        if (alive) setData(desdeEstadoVivo(symbol, snap));
      } catch {
        if (alive) setData(snapshotCero(symbol));
      }
    }
    load();
    const t = setInterval(load, 3000);
    return () => {
      alive = false;
      clearInterval(t);
    };
  }, [symbol]);

  function handleBack() {
    setClosing(true);
    setVisible(false);
    window.setTimeout(() => onClose?.(), 700);
  }

  const L = data.long || {};
  const S = data.short || {};
  const G = data.global || {};
  const D = data.desequilibrio || {};
  const F = data.fase_manto || {};
  const O = data.optimizacion_igris || {};

  return (
    <div
      className={`absolute inset-0 z-[60] flex flex-col bg-[#0a0c10] text-white overflow-y-auto overflow-x-hidden transition-opacity duration-700 ease-in-out ${
        visible && !closing ? "opacity-100" : "opacity-0"
      }`}
    >
      <header className="relative flex justify-between items-center p-4 shrink-0 border-b border-white/5">
        <button
          type="button"
          onClick={handleBack}
          aria-label="Volver al Manto"
          className="w-10 h-10 flex items-center justify-center rounded-lg border border-white/10 active:scale-95 cursor-pointer"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-white/80">
            <path d="M19 12H5" />
            <path d="M12 19l-7-7 7-7" />
          </svg>
        </button>
        <h1 className="absolute left-1/2 -translate-x-1/2 text-xl italic font-bold tracking-widest text-white pointer-events-none">
          {data.symbol || symbol}
        </h1>
        <span className="text-[10px] uppercase tracking-widest text-white/35 w-10 text-right">
          {data.fuente === "cero" ? "00" : data.fuente}
        </span>
      </header>

      <div className="px-4 py-4 space-y-4 pb-10">
        {/* Sellos de unidad de apertura · doctrina 21 */}
        <div className="grid grid-cols-2 gap-2">
          <Sello
            lado="LONG"
            sello={L.unidad_apertura || "INVERSE→USD"}
            frente={L.frente}
            tone="long"
          />
          <Sello
            lado="SHORT"
            sello={S.unidad_apertura || "LINEAR→COIN"}
            frente={S.frente}
            tone="short"
          />
        </div>

        {/* Identidad / frentes */}
        <Section title="Frentes del manto">
          <Row label="Long (frente)" value={L.frente || "—"} />
          <Row label="Short (frente)" value={S.frente || "—"} />
        </Section>

        {/* Tamaños · USD + moneda en ambas piernas */}
        <Section title="Tamaño de posiciones">
          <TwoCol
            leftTitle={`Long · ${L.unidad_apertura || "INVERSE→USD"}`}
            rightTitle={`Short · ${S.unidad_apertura || "LINEAR→COIN"}`}
            left={[
              ["USD", fmtUsd(L.size_usd)],
              [L.unidad_coin || data.symbol || "COIN", fmtNum(L.size_base, 6)],
            ]}
            right={[
              ["USD", fmtUsd(S.size_usd)],
              [S.unidad_coin || data.symbol || "COIN", fmtNum(S.size_base, 6)],
            ]}
          />
          <Row label="Global (L+S USD)" value={fmtUsd(G.size_usd_total)} accent />
          <p className="text-[10px] text-white/30 mt-1.5 leading-relaxed">
            Inverso abre en dólares; lineal abre en moneda. Ambas piernas muestran USD + coin.
          </p>
        </Section>

        {/* Margen y apalancamiento (solo lectura) */}
        <Section title="Margen y apalancamiento">
          <TwoCol
            leftTitle="Long"
            rightTitle="Short"
            left={[
              ["Margen", fmtUsd(L.margen_usd)],
              ["Lev actual / máx", fmtLev(L.leverage_actual, L.leverage_max)],
            ]}
            right={[
              ["Margen", fmtUsd(S.margen_usd)],
              ["Lev actual / máx", fmtLev(S.leverage_actual, S.leverage_max)],
            ]}
          />
          <Row label="Margen conjunto" value={fmtUsd(G.margen_usd)} accent />
          <p className="text-[10px] text-white/30 mt-1 tracking-wide">
            Apalancamiento solo lectura — sin mando de cambio en esta forja.
          </p>
        </Section>

        {/* Entradas */}
        <Section title="Puntos de entrada">
          <TwoCol
            leftTitle="Long"
            rightTitle="Short"
            left={[["Entrada", fmtNum(L.entry_price, 4)]]}
            right={[["Entrada", fmtNum(S.entry_price, 4)]]}
          />
          <Row label="Ancla global (Beru)" value={fmtNum(G.entry_avg, 4)} accent />
        </Section>

        {/* Desequilibrio */}
        <Section title="Medidor de desequilibrio">
          <Row label="Mark Long" value={fmtNum(D.mark_long, 4)} />
          <Row label="Mark Short" value={fmtNum(D.mark_short, 4)} />
          <Row label="Delta (puntos)" value={fmtNum(D.puntos, 4)} />
          <Row label="Delta (%)" value={fmtPct(D.pct)} />
          <Row
            label="Lectura"
            value={D.beneficio || "NEUTRO"}
            accent={D.beneficio === "FAVOR"}
            warn={D.beneficio === "CONTRA"}
          />
        </Section>

        {/* Sensibilidad 1% */}
        <Section title="Sensibilidad ±1%">
          <TwoCol
            leftTitle="Long"
            rightTitle="Short"
            left={[["≈ USD", fmtUsd(L.impacto_1pct_usd)]]}
            right={[["≈ USD", fmtUsd(S.impacto_1pct_usd)]]}
          />
          <Row label="Global (suma)" value={fmtUsd(G.impacto_1pct_usd)} accent />
        </Section>

        {/* Fase manto / Beru */}
        <Section title="Fase del manto">
          <Row label="Estado" value={F.estado || "REPOSO"} accent />
          <Row label="Fase margen §A" value={F.fase_margen || "—"} />
          <Row label="Grado Beru" value={F.grado_beru || "BLOQUEADO"} />
          <Row label="Rango ejército" value={F.rango_beru || "—"} />
        </Section>

        {/* Fees */}
        <Section title="Auditoría de desgaste (fees)">
          <TwoCol
            leftTitle="Long"
            rightTitle="Short"
            left={[["Pagado", fmtUsd(L.fees_paid_usd)]]}
            right={[["Pagado", fmtUsd(S.fees_paid_usd)]]}
          />
          <Row label="Suma total" value={fmtUsd(G.fees_paid_usd)} accent />
        </Section>

        {/* Optimización Igris */}
        <Section title="Optimización de entrada (Igris)">
          <TwoCol
            leftTitle="Long"
            rightTitle="Short"
            left={[
              ["Mejora pts", fmtNum(O.mejora_pts_long, 4)],
              ["Mejora %", fmtPct(O.mejora_pct_long)],
            ]}
            right={[
              ["Mejora pts", fmtNum(O.mejora_pts_short, 4)],
              ["Mejora %", fmtPct(O.mejora_pct_short)],
            ]}
          />
          <Row label="Global pts" value={fmtNum(O.mejora_pts_global, 4)} />
          <Row label="Global %" value={fmtPct(O.mejora_pct_global)} accent />
        </Section>
      </div>
    </div>
  );
}

function Sello({ lado, sello, frente, tone }) {
  const longTone = tone === "long";
  return (
    <div
      className={`rounded-xl border px-2.5 py-2 ${
        longTone
          ? "border-[#ff0055]/35 bg-[#ff0055]/8"
          : "border-cyan-500/30 bg-cyan-500/8"
      }`}
    >
      <p
        className={`text-[9px] uppercase tracking-[0.18em] ${
          longTone ? "text-[#ff0055]/80" : "text-cyan-400/80"
        }`}
      >
        {lado}
      </p>
      <p className="text-[13px] font-bold tracking-wide mt-0.5">{sello}</p>
      <p className="text-[9px] text-white/35 truncate mt-0.5">{frente || "—"}</p>
    </div>
  );
}

function Section({ title, children }) {
  return (
    <section className="rounded-2xl border border-white/8 bg-[#12141a]/80 p-3.5">
      <h2 className="text-[10px] uppercase tracking-[0.22em] text-[#ff0055]/75 mb-2.5">
        {title}
      </h2>
      <div className="space-y-1.5">{children}</div>
    </section>
  );
}

function Row({ label, value, accent, warn }) {
  return (
    <div className="flex justify-between gap-3 text-sm">
      <span className="text-white/40 tracking-wide">{label}</span>
      <span
        className={`tabular-nums font-medium text-right ${
          warn ? "text-amber-400" : accent ? "text-[#ff0055]" : "text-white/90"
        }`}
      >
        {value}
      </span>
    </div>
  );
}

function TwoCol({ leftTitle, rightTitle, left, right }) {
  return (
    <div className="grid grid-cols-2 gap-3 mb-1">
      <div className="rounded-xl bg-black/25 border border-white/5 p-2.5">
        <p className="text-[10px] uppercase tracking-widest text-white/35 mb-1.5">{leftTitle}</p>
        {left.map(([k, v]) => (
          <div key={k} className="flex justify-between text-xs mb-0.5">
            <span className="text-white/35">{k}</span>
            <span className="tabular-nums text-white/85">{v}</span>
          </div>
        ))}
      </div>
      <div className="rounded-xl bg-black/25 border border-white/5 p-2.5">
        <p className="text-[10px] uppercase tracking-widest text-white/35 mb-1.5">{rightTitle}</p>
        {right.map(([k, v]) => (
          <div key={k} className="flex justify-between text-xs mb-0.5">
            <span className="text-white/35">{k}</span>
            <span className="tabular-nums text-white/85">{v}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
