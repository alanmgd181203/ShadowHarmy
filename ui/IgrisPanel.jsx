import { useState, useEffect } from "react";
import AssetDetail from "./AssetDetail.jsx";
import { mantoDesdeFuentes, fmtUsd, fmtPct, fmtAge } from "./igrisMantoModel.js";

const ESTADO_URL = "/data/estado_vivo.json";
const ARISE_HB_URL = "/data/logs/arise_igris/heartbeat.json";

const TABS = ["ESTADO", "DORMIDO", "DESPIERTO", "SIN DATOS"];

/** Tabs = pulso del soldado (lectura), no filtros de la lista. */

function chipTone(v) {
  const s = String(v || "").toUpperCase();
  if (["OK", "ACTIVA", "LLENA", "VIVO", "ASALTO", "ASALTO INMEDIATO"].some((x) => s.includes(x) && !s.includes("AÚN"))) {
    if (s.includes("AÚN") || s.includes("APAGADO") || s.includes("VAC") || s.includes("MUERT") || s.includes("PUERTA")) {
      /* fall through */
    } else if (s === "OK" || s === "ACTIVA" || s === "LLENA" || s === "VIVO" || s.includes("ASALTO")) {
      return "text-emerald-400";
    }
  }
  if (s.includes("ASALTO") && !s.includes("AÚN")) return "text-emerald-400";
  if (s === "OK" || s === "ACTIVA" || s === "LLENA" || s === "VIVO") return "text-emerald-400";
  if (
    s.includes("VAC") ||
    s.includes("VIEJO") ||
    s.includes("PUERTA") ||
    s.includes("MUERT") ||
    s.includes("APAGADO") ||
    s.includes("AÚN") ||
    s.includes("CONGEL")
  ) {
    return "text-amber-400";
  }
  return "text-white/75";
}

function badgeCls(estado) {
  const v = String(estado || "").toUpperCase();
  if (v.includes("CRECIMIENTO") || v === "OK" || v === "VIVO") {
    return "border-emerald-500/45 text-emerald-400 bg-emerald-500/10";
  }
  if (v.includes("ACTIVA") || (v.includes("ASALTO") && !v.includes("AÚN"))) {
    return "border-[#ff0055]/50 text-[#ff0055] bg-[#ff0055]/10";
  }
  if (
    v.includes("VAC") ||
    v.includes("VIEJO") ||
    v.includes("PUERTA") ||
    v.includes("CONGEL") ||
    v.includes("DORMIDO") ||
    v.includes("MUERT") ||
    v.includes("APAGADO") ||
    v.includes("AÚN") ||
    v.includes("BLOQUE") ||
    v.includes("REPOSO")
  ) {
    return "border-amber-500/40 text-amber-400 bg-amber-500/10";
  }
  return "border-white/15 text-white/45 bg-white/5";
}

function tabActiva(pulso, tab) {
  const t = pulso?.tab || "SIN_DATOS";
  if (tab === "ESTADO") return false;
  if (tab === "DORMIDO") return t === "DORMIDO";
  if (tab === "DESPIERTO") return t === "DESPIERTO";
  if (tab === "SIN DATOS") return t === "SIN_DATOS";
  return false;
}

/**
 * Pantalla completa tipo Figma · scroll · todas las zonas siempre visibles.
 */
export default function IgrisPanel({ onClose }) {
  const [showOxygen, setShowOxygen] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);
  const [panelVisible, setPanelVisible] = useState(false);
  const [selectedAsset, setSelectedAsset] = useState(null);
  const [manto, setManto] = useState(() => mantoDesdeFuentes(null, null));

  useEffect(() => {
    const id = requestAnimationFrame(() => setPanelVisible(true));
    return () => cancelAnimationFrame(id);
  }, []);

  useEffect(() => {
    let alive = true;
    async function tick() {
      try {
        const [resEstado, resHb] = await Promise.all([
          fetch(`${ESTADO_URL}?t=${Date.now()}`, { cache: "no-store" }),
          fetch(`${ARISE_HB_URL}?t=${Date.now()}`, { cache: "no-store" }).catch(() => null),
        ]);
        if (!alive) return;
        const snap = resEstado.ok ? await resEstado.json() : null;
        let hb = null;
        if (resHb?.ok) {
          try {
            hb = await resHb.json();
          } catch {
            hb = null;
          }
        }
        if (alive) setManto(mantoDesdeFuentes(snap, hb));
      } catch {
        /* mantener último */
      }
    }
    tick();
    const t = setInterval(tick, 3000);
    return () => {
      alive = false;
      clearInterval(t);
    };
  }, []);

  const ox = manto.oxygen || {};
  const vent = manto.ventana || {};
  const meta = manto.meta || {};
  const ley = manto.ley || {};
  const libros = manto.libros || {};
  const pulso = manto.pulso || {};
  const chips = manto.chips || {};
  const manos = manto.manos || {};
  const pctL = vent.pctLong;
  const pctS = vent.pctShort;
  const barOff = vent.apagado;
  const wL = barOff ? 0 : pctL != null ? Math.max(0, Math.min(100, pctL)) : 0;
  const wS = barOff ? 0 : pctS != null ? Math.max(0, Math.min(100, pctS)) : 0;

  return (
    <div
      className={`absolute inset-0 z-50 flex flex-col bg-[#0a0c10] text-white overflow-y-auto overflow-x-hidden transition-opacity duration-500 ${
        panelVisible ? "opacity-100" : "opacity-0"
      }`}
    >
      {/* Pulso del soldado · solo lectura (no filtra bloques) */}
      <div className="sticky top-0 z-40 bg-[#0a0c10] border-b border-white/10">
        <p className="px-3 pt-1.5 text-[8px] uppercase tracking-[0.2em] text-white/30">
          Estado del soldado · solo lectura
        </p>
        <div className="flex items-stretch gap-0 px-1 pb-0" role="status" aria-label="Pulso Igris">
          {TABS.map((tab) => {
            const on = tabActiva(pulso, tab);
            const isEstado = tab === "ESTADO";
            return (
              <div
                key={tab}
                className={`flex-1 text-center py-2 text-[9px] font-semibold tracking-[0.12em] border-b-2 ${
                  isEstado
                    ? "text-white/35 border-transparent"
                    : on
                      ? "text-[#ff0055] border-[#ff0055]"
                      : "text-white/30 border-transparent"
                }`}
              >
                {tab}
              </div>
            );
          })}
        </div>

        <div className="relative flex justify-between items-center px-4 py-3">
          <button
            type="button"
            onClick={onClose}
            aria-label="Cerrar Manto"
            className="w-9 h-9 flex items-center justify-center rounded-lg border border-white/10 active:scale-95"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M19 12H5" />
              <path d="M12 19l-7-7 7-7" />
            </svg>
          </button>
          <div className="absolute left-1/2 -translate-x-1/2 text-center pointer-events-none">
            <h1 className="text-[22px] font-bold tracking-[0.22em] leading-none">MANTO</h1>
            <p className="text-[10px] tracking-[0.4em] text-white/40 mt-0.5">IGRIS</p>
          </div>
          <button
            type="button"
            onClick={() => setShowOxygen((v) => !v)}
            aria-expanded={showOxygen}
            className={`w-9 h-9 flex items-center justify-center rounded-lg border text-sm font-bold active:scale-95 ${
              showOxygen
                ? "border-[#ff0055] text-[#ff0055] bg-[#ff0055]/10"
                : "border-white/10 text-white/60"
            }`}
          >
            %
          </button>
        </div>

        {showOxygen && (
          <div className="px-4 pb-3">
            <div className="rounded-xl border border-[#ff0055]/40 bg-[#0d0f14] p-3">
              <p className="text-[10px] uppercase tracking-[0.2em] text-[#ff0055]/80 mb-2">HUD Oxígeno</p>
              <ul className="space-y-1.5 text-[13px]">
                <HudRow k="Equity Tusk" v={ox.equity != null ? fmtUsd(ox.equity, 0) : "—"} />
                <HudRow k="Oxígeno guerra" v={ox.oxigeno != null ? fmtUsd(ox.oxigeno, 0) : "—"} />
                <HudRow k="Margen ocupado" v={ox.margen != null ? fmtPct(ox.margen) : "—"} />
                <HudRow k="Oxígeno libre" v={ox.o2Pct != null ? fmtPct(ox.o2Pct) : "—"} accent />
                <HudRow k="Marcha" v={ox.marchaTitulo || "—"} />
                <HudRow
                  k="Resta engorde"
                  v={
                    ox.metaActivo
                      ? `${ox.metaActivo}${ox.metaRestante != null ? ` · ${fmtUsd(ox.metaRestante)}` : ""}`
                      : "aún no"
                  }
                />
              </ul>
            </div>
          </div>
        )}
      </div>

      <div className="px-4 pt-3 pb-8 space-y-3">
        {/* Línea pulso */}
        <div className="flex flex-wrap items-center gap-2 text-[11px]">
          <span
            className={`inline-flex items-center gap-1.5 font-semibold tracking-wide ${
              pulso.estado === "DESPIERTO" ? "text-emerald-400" : "text-white/55"
            }`}
          >
            <span className="w-1.5 h-1.5 rounded-full bg-current" />
            {pulso.label || "—"}
          </span>
          <span className={`text-[11px] font-medium ${chipTone(pulso.frescuraLabel)}`}>
            {pulso.frescuraLabel || "—"}
          </span>
          <span className="text-white/35">{pulso.ageLabel || "—"}</span>
        </div>

        {/* Chips 3×2 */}
        <div className="grid grid-cols-3 gap-1.5">
          {[
            ["MARCHA", chips.marcha],
            ["VENTANA", chips.ventana],
            ["META", chips.meta],
            ["LIBROS", chips.libros],
            ["LEY MASA", chips.ley],
            ["PULSO", chips.pulso],
          ].map(([k, v]) => (
            <div key={k} className="rounded-lg border border-white/10 bg-[#12141a] px-2 py-2">
              <p className="text-[8px] uppercase tracking-[0.14em] text-white/35">{k}</p>
              <p className={`text-[12px] font-semibold truncate mt-0.5 ${chipTone(v)}`}>{v || "—"}</p>
            </div>
          ))}
        </div>

        {/* Manos */}
        <Card>
          <CardHead
            title="MANOS · BYBIT"
            right={
              <span className={manos.hay ? "text-rose-400 text-[10px] font-semibold tracking-wide" : "text-white/35 text-[10px]"}>
                {manos.titulo || "—"}
              </span>
            }
          />
          <p className="text-[12px] text-white/65 leading-snug">{manos.detalle || "aún no"}</p>
          {manos.ts ? (
            <p className="text-[10px] text-white/30 mt-1.5">{fmtAge(Date.now() / 1000 - Number(manos.ts))}</p>
          ) : null}
        </Card>

        {/* Balance */}
        <Card>
          <CardHead
            title="BALANCE GLOBAL"
            right={
              <span
                className={`text-[10px] font-medium tracking-wide ${
                  vent.apagado ? "text-amber-400" : "text-emerald-400"
                }`}
              >
                {vent.apagado
                  ? "MANTO APAGADO"
                  : `VENTANA 48-52 · ${vent.estado || "OK"}`}
              </span>
            }
          />
          {vent.apagado ? (
            <p className="text-[12px] text-white/40 mb-2">Sin posición dual aún · cuando Igris despliegue verás L/S reales</p>
          ) : null}
          <div className="h-3.5 rounded-full w-full overflow-hidden flex border border-white/10 bg-[#0d0f14]">
            {barOff ? (
              <div className="h-full w-full bg-white/[0.04]" />
            ) : (
              <>
                <div className="h-full bg-[#ff0055]/70" style={{ width: `${wL}%` }} />
                <div className="h-full bg-[#2a2e3a]" style={{ width: `${wS}%` }} />
              </>
            )}
          </div>
          <div className="mt-2 flex justify-between text-[11px] tracking-wide">
            <span className={barOff ? "text-white/30" : "text-[#ff0055]/90"}>
              ● LONG {pctL != null ? fmtPct(pctL) : "—"}
              <span className="block text-[10px] tabular-nums text-white/55 mt-0.5">
                {barOff ? "$0" : fmtUsd(vent.usdLong)}
              </span>
            </span>
            <span className="text-white/40 text-right">
              ● SHORT {pctS != null ? fmtPct(pctS) : "—"}
              <span className="block text-[10px] tabular-nums text-white/55 mt-0.5">
                {barOff ? "$0" : fmtUsd(vent.usdShort)}
              </span>
            </span>
          </div>
        </Card>

        {/* Meta */}
        <Card>
          <CardHead
            title="META ENGORDE"
            right={
              <span className={`px-2 py-0.5 rounded border text-[10px] ${badgeCls(meta.marchaId || "—")}`}>
                {meta.marchaId ? String(meta.marchaId).toUpperCase() : "AÚN NO"}
              </span>
            }
          />
          <div className="flex items-start justify-between gap-2 mb-3">
            <div>
              <p className="text-[28px] font-bold tracking-wide leading-none">
                {meta.activo || "—"}
              </p>
              <p className="text-[11px] text-white/40 tracking-wide mt-1">
                {meta.aunNo
                  ? "aún no hay meta de paso"
                  : `${meta.grado || "—"}${meta.paso != null ? ` · PASO ${meta.paso}` : ""}`}
              </p>
            </div>
            <span className={`px-2 py-0.5 rounded border text-[10px] ${badgeCls(meta.labelBadge)}`}>
              {meta.labelBadge || "AÚN NO"}
            </span>
          </div>
          <div className="grid grid-cols-3 gap-2 mb-3">
            <Mini k="NEED" v={meta.need != null ? fmtUsd(meta.need) : "—"} />
            <Mini k="HAVE" v={meta.have != null ? fmtUsd(meta.have) : "—"} />
            <Mini k="RESTA" v={meta.resta != null ? fmtUsd(meta.resta) : "—"} />
          </div>
          <div className="flex items-center justify-between mb-1">
            <p className="text-[10px] text-white/35 tracking-wide">FILL PASO</p>
            <p className="text-[10px] text-white/45 tabular-nums">
              {meta.fillPct != null ? `${Math.round(meta.fillPct)}%` : "—"}
            </p>
          </div>
          <div className="h-2 rounded-full overflow-hidden bg-white/5 border border-white/10">
            <div
              className="h-full bg-[#ff0055]/75"
              style={{ width: `${meta.fillPct != null ? meta.fillPct : 0}%` }}
            />
          </div>
        </Card>

        {/* Libros del Santo en foco */}
        <Card>
          <CardHead
            title={`LIBROS · ${libros.activo || meta.activo || "ETH"}`}
            right={<span className={`text-[10px] font-semibold ${chipTone(libros.estado)}`}>{libros.estado || "VACÍO"}</span>}
          />
          <p className="text-[10px] text-white/30 mb-2">
            Santo en meta engorde · lineal e inverso
          </p>
          <LibroBlock name={`LINEAL ${(libros.activo || "ETH")}USDT`} row={libros.lineal} />
          <div className="h-px bg-white/5 my-2.5" />
          <LibroBlock name={`INVERSO ${(libros.activo || "ETH")}USD`} row={libros.inverso} />
        </Card>

        {/* Ley masa */}
        <Card>
          <CardHead
            title="LEY DE LA MASA"
            right={
              <span className={`px-2 py-0.5 rounded border text-[10px] ${badgeCls(ley.estado)}`}>
                {ley.estado || "SIN PUERTA AÚN"}
              </span>
            }
          />
          <p className="text-[14px] text-white/80 text-center py-1">{ley.motivoLegible || "Aún no"}</p>
          <div className="mt-2 flex justify-center gap-4 text-[11px] text-white/40">
            <span>
              Asimetría{" "}
              <span className="text-white/75 tabular-nums">
                {ley.asimPct != null ? fmtPct(ley.asimPct, 2) : "—"}
              </span>
            </span>
            <span>
              Activo <span className="text-white/75">{ley.activo || "—"}</span>
            </span>
          </div>
        </Card>

        {/* Frecuencia */}
        <Card>
          <CardHead
            title="FRECUENCIA · RANKING"
            right={<span className="text-[10px] text-white/30">lectura · no dispara</span>}
          />
          {manto.frecuencia?.aunNo ? (
            <p className="text-[12px] text-white/40 mb-2">
              {manto.frecuencia?.motivoVacio ||
                "Sin ranking · frecuencia aún no alimenta este bloque"}
            </p>
          ) : null}
          <div className="space-y-2.5">
            {(manto.frecuencia?.ranking || []).map((r) => (
              <div key={`r-${r.n}`} className="flex items-center gap-2">
                <span className="w-4 text-[11px] text-white/30">{r.n}</span>
                <span className={`w-14 text-[13px] font-semibold ${r.vacio ? "text-white/30" : ""}`}>
                  {r.base}
                </span>
                <span className="px-1.5 py-0.5 rounded border border-white/10 text-[9px] text-white/40 uppercase">
                  {r.modo}
                </span>
                <div className="flex-1 h-1.5 rounded-full overflow-hidden bg-white/5">
                  <div
                    className="h-full bg-[#ff0055]/65"
                    style={{ width: `${r.score != null ? Math.min(100, r.score) : 0}%` }}
                  />
                </div>
                <span className="w-8 text-right text-[11px] tabular-nums text-white/45">
                  {r.score != null ? r.score : "—"}
                </span>
              </div>
            ))}
          </div>
          <p className="text-[10px] text-white/30 mt-2.5">{manto.frecuencia?.etaLabel || "sin ETA"}</p>
        </Card>

        {/* Vanguardia */}
        <section>
          <div className="flex items-center justify-between mb-2 px-0.5">
            <p className="text-[10px] uppercase tracking-[0.22em] text-white/35">Vanguardia · Top 5</p>
            <span className="text-[10px] text-white/30">toca para detalle</span>
          </div>
          <div className="space-y-2">
            {(manto.vanguardia || []).map((coin, i) => (
              <AssetRow
                key={`${coin.id}-${i}`}
                coin={coin}
                onOpen={() => coin.id && coin.id !== "—" && setSelectedAsset(coin.id)}
              />
            ))}
          </div>
        </section>

        {/* Batallón */}
        <button
          type="button"
          onClick={() => setIsExpanded((v) => !v)}
          className="w-full flex items-center justify-between px-3 py-3 rounded-xl border border-white/10 bg-[#12141a] active:scale-[0.99]"
        >
          <span className="text-[10px] uppercase tracking-[0.22em] text-white/45">
            Batallón · {manto.nBatallon || 0} activos
          </span>
          <svg
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2.2"
            className={`text-white/35 transition-transform ${isExpanded ? "rotate-180" : ""}`}
          >
            <polyline points="6 9 12 15 18 9" />
          </svg>
        </button>
        <div
          className={`transition-all duration-500 overflow-hidden ${
            isExpanded ? "max-h-[2400px] opacity-100" : "max-h-0 opacity-0"
          }`}
        >
          <div className="space-y-2 pt-1">
            {(manto.batallon || []).length === 0 ? (
              <p className="text-[12px] text-white/35 px-1">Aún no hay más activos en batallón</p>
            ) : (
              manto.batallon.map((coin) => (
                <AssetRow key={coin.id} coin={coin} onOpen={() => setSelectedAsset(coin.id)} />
              ))
            )}
          </div>
        </div>

        <div className="min-h-[140px] flex flex-col items-center justify-center rounded-2xl border border-dashed border-white/15 bg-[#0d0f14]/50 mt-2">
          <p className="text-[13px] tracking-[0.25em] text-white/25 uppercase">Análisis temporal</p>
          <p className="text-[11px] text-white/20 mt-1">gráficas · próximamente</p>
        </div>
      </div>

      {selectedAsset && (
        <AssetDetail symbol={selectedAsset} onClose={() => setSelectedAsset(null)} />
      )}
    </div>
  );
}

function Card({ children }) {
  return (
    <section className="rounded-xl border border-white/10 bg-[#12141a] p-3">{children}</section>
  );
}

function CardHead({ title, right }) {
  return (
    <div className="flex items-center justify-between gap-2 mb-2.5">
      <p className="text-[10px] uppercase tracking-[0.2em] text-white/40">{title}</p>
      {right}
    </div>
  );
}

function HudRow({ k, v, accent }) {
  return (
    <li className="flex justify-between gap-2">
      <span className="text-white/40">{k}</span>
      <span className={`tabular-nums ${accent ? "text-[#ff0055]" : "text-white/85"}`}>{v}</span>
    </li>
  );
}

function Mini({ k, v }) {
  return (
    <div className="rounded-lg bg-black/30 border border-white/5 py-2 px-1 text-center">
      <p className="text-[8px] uppercase tracking-[0.12em] text-white/35">{k}</p>
      <p className="text-[13px] font-semibold tabular-nums mt-0.5">{v}</p>
    </div>
  );
}

function LibroBlock({ name, row }) {
  const r = row || {};
  return (
    <div>
      <div className="flex items-center justify-between mb-1.5">
        <p className="text-[11px] font-medium tracking-wide text-white/80">
          {name}{" "}
          <span className={r.vacio ? "text-amber-400" : "text-emerald-400"}>{r.estado || "VACÍO"}</span>
        </p>
      </div>
      <div className="grid grid-cols-3 gap-2 text-[10px] text-white/35">
        <span>
          BID <span className="text-white/75 tabular-nums">{r.bids != null ? r.bids : "—"}</span>
        </span>
        <span>
          ASK <span className="text-white/75 tabular-nums">{r.asks != null ? r.asks : "—"}</span>
        </span>
        <span>
          EDAD{" "}
          <span className="text-white/75 tabular-nums">
            {r.edad_s != null ? `${Number(r.edad_s).toFixed(1)}s` : "—"}
          </span>
        </span>
      </div>
    </div>
  );
}

function AssetRow({ coin, onOpen }) {
  const disabled = !coin?.id || coin.id === "—";
  const has = coin.tieneMasa;
  const pctL = has && coin.pctLong != null ? coin.pctLong : 50;
  const pctS = has && coin.pctShort != null ? coin.pctShort : 50;
  return (
    <button
      type="button"
      disabled={disabled}
      onClick={onOpen}
      className="w-full flex items-center gap-2 px-3 py-3 rounded-xl bg-[#12141a] border border-white/5 text-left disabled:opacity-60 active:scale-[0.99]"
    >
      <span className="w-12 shrink-0 text-[13px] font-semibold tracking-wider">{coin.id}</span>
      <div className="flex-1 h-2 rounded-full overflow-hidden flex border border-white/5 bg-[#0d0f14]">
        {has ? (
          <>
            <div className="h-full bg-[#ff0055]/60" style={{ width: `${pctL}%` }} />
            <div className="h-full bg-[#2a2e3a]" style={{ width: `${pctS}%` }} />
          </>
        ) : (
          <div className="h-full w-full bg-white/[0.06]" />
        )}
      </div>
      <span className="w-[64px] shrink-0 text-right text-[11px] tabular-nums text-white/70">
        {has ? fmtUsd(coin.usdTotal) : coin.usdTotal === 0 ? "$0" : "—"}
      </span>
      <span className={`shrink-0 px-1.5 py-0.5 rounded border text-[8px] tracking-wider ${badgeCls(coin.badge)}`}>
        {coin.badge || "REPOSO"}
      </span>
      <span className="text-white/25 text-sm">›</span>
    </button>
  );
}
