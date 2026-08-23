import { useEffect, useState } from "react";
import {
  snapshotCero,
  desdeEstadoVivo,
  fmtUsd,
  fmtPct,
  fmtNum,
  detalleCosecha,
  cargarSnapBeru,
} from "./beruAssetDetailModel.js";
import FotoCruda from "./FotoCruda.jsx";
import BeruSpotChart from "./BeruSpotChart.jsx";

/**
 * Sub-Santuario Beru — ficha por moneda (caza / rango / red / gráfica).
 */
export default function BeruAssetDetail({ symbol, onClose, onChart }) {
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
        const snap = await cargarSnapBeru();
        if (alive) setData(desdeEstadoVivo(symbol, snap));
      } catch {
        if (alive) setData(snapshotCero(symbol));
      }
    }
    load();
    const t = setInterval(load, 2000);
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

  const re = data.red_engorde;
  const graf = data.grafica || {};

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
        {onChart ? (
          <button
            type="button"
            onClick={onChart}
            className="text-[10px] uppercase tracking-widest text-emerald-400/80 w-10 text-right"
          >
            velas
          </button>
        ) : (
          <span className="text-[10px] uppercase tracking-widest text-white/35 w-10 text-right">
            {data.fuente === "cero" ? "00" : "BERU"}
          </span>
        )}
      </header>

      <div className="px-4 py-4 space-y-4 pb-10">
        <Section title="Cazador en este Santo">
          <Row label="Barcos" value={String(data.n_barcos ?? 0)} accent />
          <Row label="Cazando" value={String(data.n_caza ?? 0)} />
          <Row label="Acechando" value={String(data.n_acechando ?? 0)} />
          <p className="text-[10px] text-white/35 mt-1">
            Un oficio: CAZA. Negociador/Mega son fósiles.
          </p>
        </Section>

        <Section title="Dos ceros (no se mezclan)">
          <Row label="0 del manto (Igris)" value={fmtNum(data.centro_manto || data.grafica?.centro_manto)} accent />
          <Row label="0 de nacimiento (wake)" value={fmtNum(data.centro_wake || data.grafica?.centro_wake)} />
          <Row label="Spot ahora" value={fmtNum(data.spot_last || data.grafica?.spot_last)} />
          <p className="text-[10px] text-white/30 mt-1">
            El metro es Igris. El Vacío ±1,1 nace del wake, no del manto.
          </p>
        </Section>

        <Section title="Red que permite engordar">
          {re ? (
            <>
              <Row label="Precio red" value={fmtNum(re.precio)} accent />
              <Row label="% vs metro" value={fmtPct(re.pct_vs_centro)} />
              <Row label="Barco" value={String(re.uid || "").slice(0, 22)} />
              <Row label="Dirección" value={re.direccion || "—"} />
              <p className="text-[10px] text-amber-400/80 mt-1">{re.nota}</p>
            </>
          ) : (
            <p className="text-sm text-white/40">Sin Red activa — aún acecha o no armó tramo.</p>
          )}
        </Section>

        <Section title={String(data.oficio || "").toUpperCase() === "RANGO" ? "Velas linear + combate rango" : "Velas de spot + combate"}>
          <BeruSpotChart
            symbol={data.symbol || symbol}
            grafica={graf}
            altura={280}
            category={String(data.oficio || graf?.oficio || "").toUpperCase() === "RANGO" || data.mercado === "linear" ? "linear" : "spot"}
            leyendaRango={String(data.oficio || graf?.oficio || "").toUpperCase() === "RANGO"}
            reglaManto={String(data.oficio || "").toUpperCase() !== "RANGO"}
          />
          <p className="text-[10px] text-white/30 mt-2 leading-relaxed">
            {String(data.oficio || "").toUpperCase() === "RANGO"
              ? "Rayas: 0, Sangre, Red, Oz. Toca el lado derecho de la gráfica → % vs last."
              : "Velas spot + combate. Lado derecho → % vs last. Asa blanca → metro del manto."}
          </p>
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
                  <span className="text-white/50">{String(b.uid || "").slice(0, 20)}</span>
                  <span className="text-emerald-400/80">{b.grado || b.tier_id || "—"}</span>
                </div>
                <Row label="Estado" value={b.estado || "—"} />
                <Row label="Lado" value={b.direccion || "—"} />
                <TwoCol
                  leftTitle="Ceros"
                  rightTitle="Masa"
                  left={[
                    ["Manto", fmtNum(b.centro_manto)],
                    ["Wake", fmtNum(b.centro_wake || b.centro_local)],
                  ]}
                  right={[
                    ["Tramo", fmtUsd(b.masa_tramo_usd || b.masa)],
                    ["Carta", fmtUsd(b.masa_carta_usd)],
                  ]}
                />
                <TwoCol
                  leftTitle="Hoz"
                  rightTitle="Red / Vacío"
                  left={[
                    ["Precio", fmtNum(b.oz_precio)],
                    ["%", fmtPct(b.oz_pct)],
                  ]}
                  right={[
                    ["Red", fmtNum(b.red_precio)],
                    ["Vacío ±", fmtPct(b.vacio_pct)],
                  ]}
                />
                <Row label="Carta colgada" value={b.carta_colgada ? "sí" : "no"} />
                <Row label="Hoz modo" value={b.hoz_modo || "—"} />
                <Row label="Última Hoz tocada" value={b.ultima_hoz_precio ? fmtNum(b.ultima_hoz_precio) : "aún no"} />
                <Row label="Spot" value={fmtNum(b.spot_last)} />
                <FotoCruda titulo="Foto de este barco" data={b} />
              </div>
            ))
          )}
        </Section>

        <Section title="Crónica de ciclos">
          {(data.cronica || []).length === 0 ? (
            <p className="text-sm text-white/40">
              Sin crónica aún — se irá llenando con caza / cosecha.
            </p>
          ) : (
            (data.cronica || []).slice(-12).reverse().map((ev, i) => (
              <Row
                key={`${ev.ts}-${i}`}
                label={ev.tipo || ev.evento || "evento"}
                value={detalleCosecha(ev)}
              />
            ))
          )}
        </Section>
        <FotoCruda titulo="Foto cruda de este Santo" data={data} />
      </div>
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
