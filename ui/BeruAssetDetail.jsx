import { useEffect, useMemo, useState } from "react";
import {
  snapshotCero,
  desdeEstadoVivo,
  fmtUsd,
  fmtPct,
  fmtNum,
} from "./beruAssetDetailModel.js";

const ESTADO_URL = "/data/estado_vivo.json";

/**
 * Sub-Santuario Beru — ficha por moneda (caza / neg / red engorde / gráfica).
 */
export default function BeruAssetDetail({ symbol, onClose }) {
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

  const C = data.composicion || {};
  const re = data.red_engorde;
  const graf = data.grafica || {};

  return (
    <div
      className={`fixed inset-0 z-[60] flex flex-col bg-[#0a0c10] text-white overflow-y-auto overflow-x-hidden transition-opacity duration-700 ease-in-out ${
        visible && !closing ? "opacity-100" : "opacity-0"
      }`}
    >
      <header className="relative flex justify-between items-center p-4 shrink-0 border-b border-white/5">
        <button
          type="button"
          onClick={handleBack}
          aria-label="Volver a flota Beru"
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
          {data.fuente === "cero" ? "00" : "BERU"}
        </span>
      </header>

      <div className="px-4 py-4 space-y-4 pb-10">
        <Section title="Legión en este activo">
          <Row label="Barcos" value={String(data.n_barcos ?? 0)} accent />
          <Row label="Cazando" value={String(data.n_caza ?? 0)} />
          <Row label="Negociando" value={String(data.n_negociando ?? 0)} />
          <Row label="Acechando" value={String(data.n_acechando ?? 0)} />
          <Row label="Mega" value={String(data.n_mega ?? 0)} />
          <div className="h-3 rounded-full overflow-hidden flex border border-white/10 mt-2">
            <div
              className="h-full bg-emerald-500/70"
              style={{ width: `${Math.min(100, C.pct_caza || 0)}%` }}
              title="Caza"
            />
            <div
              className="h-full bg-sky-500/60"
              style={{ width: `${Math.min(100, C.pct_negociando || 0)}%` }}
              title="Negociando"
            />
          </div>
          <p className="text-[10px] text-white/35 mt-1">
            Verde = caza · Azul = negociando ({C.pct_caza || 0}% / {C.pct_negociando || 0}%)
          </p>
        </Section>

        <Section title="Centro 0 y economía">
          <Row label="Centro 0" value={fmtNum(data.centro_0, 4)} accent />
          <Row label="Masa total" value={fmtUsd(data.masa_total_usd)} />
          <Row label="PnL estimado" value={fmtUsd(data.pnl_est_usd)} />
          <Row label="Fees pagados" value={data.fees_paid_usd == null ? "—" : fmtUsd(data.fees_paid_usd)} />
          <p className="text-[10px] text-white/30 mt-1">{data.nota_pnl}</p>
        </Section>

        <Section title="Red que permite engordar">
          {re ? (
            <>
              <Row label="Precio red" value={fmtNum(re.precio, 4)} accent />
              <Row label="% vs centro 0" value={fmtPct(re.pct_vs_centro)} />
              <Row label="Barco" value={String(re.uid || "").slice(0, 22)} />
              <Row label="Dirección" value={re.direccion || "—"} />
              <p className="text-[10px] text-amber-400/80 mt-1">{re.nota}</p>
            </>
          ) : (
            <p className="text-sm text-white/40">Sin red de frontera activa en este activo.</p>
          )}
        </Section>

        <Section title="Rails spot (USDT / USDC…)">
          <Row
            label="Vivos"
            value={(data.rails_vivos || []).join(", ") || "—"}
          />
          {(data.rails_disponibles || []).map((r) => (
            <Row key={r.frente || r.quote} label={r.quote || "?"} value={r.frente || "—"} />
          ))}
        </Section>

        <Section title="Mapa de niveles">
          <BeruLevelChart grafica={graf} redEngorde={re} />
        </Section>

        <Section title="Barcos">
          {(data.barcos || []).length === 0 ? (
            <p className="text-sm text-white/40">Ningún barco en este activo.</p>
          ) : (
            (data.barcos || []).map((b) => (
              <div
                key={b.uid}
                className="rounded-xl border border-white/8 bg-black/25 p-2.5 mb-2"
              >
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-white/50">{String(b.uid || "").slice(0, 18)}</span>
                  <span className={b.es_super ? "text-amber-300" : "text-white/70"}>
                    {b.modo}
                    {b.es_super ? " ★" : ""}
                  </span>
                </div>
                <TwoCol
                  leftTitle="Grid"
                  rightTitle="Masa"
                  left={[
                    ["Oz %", fmtPct(b.oz_vs_centro_pct)],
                    ["Red %", fmtPct(b.red_vs_centro_pct)],
                  ]}
                  right={[
                    ["USD", fmtUsd(b.masa)],
                    ["PnL", fmtUsd(b.pnl_est_usd)],
                  ]}
                />
                <Row label="Estado" value={b.estado || "—"} />
                <Row label="Rail" value={b.rail_quote || "—"} />
              </div>
            ))
          )}
        </Section>

        <Section title="Crónica de ciclos">
          {(data.cronica || []).length === 0 ? (
            <p className="text-sm text-white/40">
              Sin crónica aún — se irá llenando con caza / cosecha / Mega.
            </p>
          ) : (
            (data.cronica || []).slice(-12).reverse().map((ev, i) => (
              <Row
                key={`${ev.ts}-${i}`}
                label={ev.tipo || ev.evento || "evento"}
                value={ev.detalle || ev.precio || String(ev.ts || "")}
              />
            ))
          )}
        </Section>
      </div>
    </div>
  );
}

function BeruLevelChart({ grafica, redEngorde }) {
  const niveles = useMemo(() => {
    const raw = Array.isArray(grafica?.niveles) ? [...grafica.niveles] : [];
    return raw.filter((n) => Number(n.precio) > 0);
  }, [grafica]);

  if (!niveles.length) {
    return <p className="text-sm text-white/40">Sin niveles para graficar.</p>;
  }

  const precios = niveles.map((n) => Number(n.precio));
  const min = Math.min(...precios);
  const max = Math.max(...precios);
  const span = Math.max(max - min, 1e-9);
  const w = 320;
  const h = 140;
  const pad = 12;

  function yOf(p) {
    return pad + ((max - p) / span) * (h - pad * 2);
  }

  const color = {
    centro: "#ff0055",
    oz: "#34d399",
    red: "#38bdf8",
    red_engorde: "#fbbf24",
  };

  return (
    <div className="overflow-x-auto">
      <svg viewBox={`0 0 ${w} ${h}`} className="w-full max-w-full" role="img" aria-label="Niveles Beru">
        <rect x="0" y="0" width={w} height={h} fill="#0a0c10" />
        {niveles.map((n, i) => {
          const y = yOf(Number(n.precio));
          const c = color[n.rol] || "#ffffff88";
          const thick = n.rol === "red_engorde" || n.rol === "centro" ? 2.2 : 1.2;
          return (
            <g key={`${n.id}-${i}`}>
              <line x1={pad} x2={w - pad} y1={y} y2={y} stroke={c} strokeWidth={thick} opacity={0.85} />
              <text x={pad + 2} y={y - 3} fill={c} fontSize="8" opacity={0.9}>
                {n.rol}
                {n.pct != null ? ` ${Number(n.pct).toFixed(2)}%` : ""}
              </text>
            </g>
          );
        })}
      </svg>
      {redEngorde?.precio ? (
        <p className="text-[10px] text-amber-400/80 mt-1">
          Ámbar = red engorde @ {fmtNum(redEngorde.precio, 4)}
        </p>
      ) : null}
    </div>
  );
}

function Section({ title, children }) {
  return (
    <section className="rounded-2xl border border-white/8 bg-[#12141a]/80 p-3.5">
      <h2 className="text-[10px] uppercase tracking-[0.22em] text-emerald-400/80 mb-2.5">
        {title}
      </h2>
      <div className="space-y-1.5">{children}</div>
    </section>
  );
}

function Row({ label, value, accent }) {
  return (
    <div className="flex justify-between gap-3 text-sm">
      <span className="text-white/40 tracking-wide">{label}</span>
      <span className={`tabular-nums font-medium text-right ${accent ? "text-emerald-400" : "text-white/90"}`}>
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
