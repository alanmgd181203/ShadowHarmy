/**
 * Modelo Sub-Santuario Igris — espejo de core/igris_asset_detail.py
 * Prefiere igris_asset_details precomputado por Bellion; si no, hidrata desde Bridge/Tank/pesos.
 */

export function snapshotCero(symbol = "BTC") {
  const s = String(symbol || "BTC").toUpperCase();
  return {
    symbol: s,
    fuente: "cero",
    long: {
      frente: `${s}USD_INVERSE`,
      symbol: null,
      size_base: 0,
      size_usd: 0,
      entry_price: 0,
      mark_price: 0,
      margen_usd: 0,
      leverage_actual: null,
      leverage_max: 0,
      fees_paid_usd: 0,
      impacto_1pct_usd: 0,
      entry_baseline: 0,
      unidad_apertura: "INVERSE→USD",
      unidad_coin: s,
    },
    short: {
      frente: `${s}USDT_LINEAL`,
      symbol: null,
      size_base: 0,
      size_usd: 0,
      entry_price: 0,
      mark_price: 0,
      margen_usd: 0,
      leverage_actual: null,
      leverage_max: 0,
      fees_paid_usd: 0,
      impacto_1pct_usd: 0,
      entry_baseline: 0,
      unidad_apertura: "LINEAR→COIN",
      unidad_coin: s,
    },
    global: {
      entry_avg: 0,
      margen_usd: 0,
      size_usd_long: 0,
      size_usd_short: 0,
      size_usd_total: 0,
      impacto_1pct_usd: 0,
      fees_paid_usd: 0,
    },
    desequilibrio: {
      puntos: 0,
      pct: 0,
      beneficio: "NEUTRO",
      mark_long: 0,
      mark_short: 0,
    },
    fase_manto: {
      estado: "REPOSO",
      rango_beru: "—",
      grado_beru: "BLOQUEADO",
      fase_margen: null,
      G_min: null,
    },
    optimizacion_igris: {
      mejora_pts_long: 0,
      mejora_pct_long: 0,
      mejora_pts_short: 0,
      mejora_pct_short: 0,
      mejora_pts_global: 0,
      mejora_pct_global: 0,
    },
  };
}

function impacto1pct(sizeUsd) {
  return sizeUsd > 0 ? Math.round(sizeUsd * 0.01 * 10000) / 10000 : 0;
}

function mejoraEntrada(baseline, actual, isLong) {
  if (!(baseline > 0) || !(actual > 0)) return [0, 0];
  const pts = isLong ? baseline - actual : actual - baseline;
  const pct = (pts / baseline) * 100;
  return [Math.round(pts * 1e6) / 1e6, Math.round(pct * 1e4) / 1e4];
}

function beneficioDeseq(markL, markS, entryL, entryS) {
  if (!(markL > 0) || !(markS > 0)) return "NEUTRO";
  const spreadMark = markS - markL;
  if (Math.abs(spreadMark) < 1e-12) return "NEUTRO";
  if (entryL > 0 && entryS > 0) {
    const delta = spreadMark - (entryS - entryL);
    if (Math.abs(delta) < 1e-12) return "NEUTRO";
    return delta > 0 ? "FAVOR" : "CONTRA";
  }
  return spreadMark > 0 ? "FAVOR" : "CONTRA";
}

function piernasBridge(symbol, snap) {
  const s = String(symbol || "").toUpperCase();
  const pos = snap.igris_posiciones || {};
  const por = (pos.por_activo || {})[s];
  if (por) return [por.long || {}, por.short || {}];
  const L = pos.long || {};
  const S = pos.short || {};
  const sl = String(L.symbol || "").toUpperCase();
  const ss = String(S.symbol || "").toUpperCase();
  if (sl.startsWith(s) || ss.startsWith(s)) return [L, S];
  return [{}, {}];
}

function marksDesdeSnap(symbol, snap, frenteLong, frenteShort) {
  const s = String(symbol || "").toUpperCase();
  const marks = {};
  const inv = ((snap.inverse_perp || {}).detalle) || {};
  const lin = ((snap.linear_perp || {}).detalle) || {};
  for (const [frente, det] of Object.entries({ ...inv, ...lin })) {
    if (!String(frente).toUpperCase().startsWith(s)) continue;
    const px = Number(det?.precio) || 0;
    if (px > 0) marks[frente] = px;
  }
  const [L, S] = piernasBridge(s, snap);
  if (Number(L.mark_price) > 0) {
    marks[L.frente || frenteLong] = Number(L.mark_price);
    marks.long = Number(L.mark_price);
  }
  if (Number(S.mark_price) > 0) {
    marks[S.frente || frenteShort] = Number(S.mark_price);
    marks.short = Number(S.mark_price);
  }
  return marks;
}

function baselinesFees(pesos, symbol) {
  const s = String(symbol || "").toUpperCase();
  let bl = 0;
  let bs = 0;
  let fl = 0;
  let fs = 0;
  for (const [frente, p] of Object.entries(pesos || {})) {
    if (!String(frente).toUpperCase().startsWith(s)) continue;
    if (Number(p.long) > 0 && Number(p.baseline_long) > 0) bl = Number(p.baseline_long);
    if (Number(p.short) > 0 && Number(p.baseline_short) > 0) bs = Number(p.baseline_short);
    fl += Number(p.fees_paid_long) || 0;
    fs += Number(p.fees_paid_short) || 0;
  }
  return { baselines: { long: bl, short: bs }, fees: { long: fl, short: fs } };
}

/** Hidrata desde estado_vivo (preferir igris_asset_details[symbol]). */
export function desdeEstadoVivo(symbol, snap) {
  const s = String(symbol || "BTC").toUpperCase();
  if (!snap || typeof snap !== "object") return snapshotCero(s);

  const pre = (snap.igris_asset_details || {})[s];
  if (pre && typeof pre === "object" && pre.long && pre.short) {
    return {
      ...pre,
      symbol: pre.symbol || s,
      long: {
        ...pre.long,
        unidad_apertura: pre.long.unidad_apertura || "INVERSE→USD",
        unidad_coin: pre.long.unidad_coin || s,
      },
      short: {
        ...pre.short,
        unidad_apertura: pre.short.unidad_apertura || "LINEAR→COIN",
        unidad_coin: pre.short.unidad_coin || s,
      },
    };
  }

  const out = snapshotCero(s);
  const pesos = snap.pesos_por_frente || {};
  let sizeL = 0;
  let sizeS = 0;
  let pxLNum = 0;
  let pxLDen = 0;
  let pxSNum = 0;
  let pxSDen = 0;
  let frenteLong = `${s}USD_INVERSE`;
  let frenteShort = `${s}USDT_LINEAL`;

  for (const [frente, p] of Object.entries(pesos)) {
    const fu = String(frente).toUpperCase();
    if (!fu.startsWith(s)) continue;
    const pl = Number(p.long) || 0;
    const ps = Number(p.short) || 0;
    const pml = Number(p.precio_medio_long) || 0;
    const pms = Number(p.precio_medio_short) || 0;
    if (pl > 0) {
      sizeL += pl;
      if (pml > 0) {
        pxLNum += pl * pml;
        pxLDen += pl;
      }
      if (fu.includes("INVERSE")) frenteLong = frente;
    }
    if (ps > 0) {
      sizeS += ps;
      if (pms > 0) {
        pxSNum += ps * pms;
        pxSDen += ps;
      }
      if (fu.includes("LINEAL") || fu.includes("USDT") || fu.includes("USDC")) {
        frenteShort = frente;
      }
    }
  }

  const entryL = pxLDen > 0 ? pxLNum / pxLDen : 0;
  const entryS = pxSDen > 0 ? pxSNum / pxSDen : 0;
  const marks = marksDesdeSnap(s, snap, frenteLong, frenteShort);
  let markL = Number(marks[frenteLong] || marks.long) || 0;
  let markS = Number(marks[frenteShort] || marks.short) || 0;
  if (!(markL > 0)) markL = entryL;
  if (!(markS > 0)) markS = entryS;

  const [BL, BS] = piernasBridge(s, snap);
  const margenL = Number(BL.margen_usd) || 0;
  const margenS = Number(BS.margen_usd) || 0;
  const levL = BL.leverage != null && Number(BL.leverage) > 0 ? Number(BL.leverage) : null;
  const levS = BS.leverage != null && Number(BS.leverage) > 0 ? Number(BS.leverage) : null;
  const { baselines, fees } = baselinesFees(pesos, s);

  const baseL = entryL > 0 ? sizeL / entryL : markL > 0 ? sizeL / markL : 0;
  const baseS = entryS > 0 ? sizeS / entryS : markS > 0 ? sizeS / markS : 0;

  out.fuente = sizeL > 0 || sizeS > 0 ? "pesos" : "cero";
  out.long = {
    ...out.long,
    frente: frenteLong,
    size_base: Math.round(baseL * 1e8) / 1e8,
    size_usd: Math.round(sizeL * 1e4) / 1e4,
    entry_price: Math.round(entryL * 1e6) / 1e6,
    mark_price: Math.round(markL * 1e6) / 1e6,
    margen_usd: Math.round(margenL * 1e4) / 1e4,
    leverage_actual: levL,
    fees_paid_usd: Math.round(fees.long * 1e4) / 1e4,
    impacto_1pct_usd: impacto1pct(sizeL),
    entry_baseline: Math.round((baselines.long || 0) * 1e6) / 1e6,
    unidad_apertura: "INVERSE→USD",
    unidad_coin: s,
  };
  out.short = {
    ...out.short,
    frente: frenteShort,
    size_base: Math.round(baseS * 1e8) / 1e8,
    size_usd: Math.round(sizeS * 1e4) / 1e4,
    entry_price: Math.round(entryS * 1e6) / 1e6,
    mark_price: Math.round(markS * 1e6) / 1e6,
    margen_usd: Math.round(margenS * 1e4) / 1e4,
    leverage_actual: levS,
    fees_paid_usd: Math.round(fees.short * 1e4) / 1e4,
    impacto_1pct_usd: impacto1pct(sizeS),
    entry_baseline: Math.round((baselines.short || 0) * 1e6) / 1e6,
    unidad_apertura: "LINEAR→COIN",
    unidad_coin: s,
  };

  let entryAvg = 0;
  if (sizeL > 0 && sizeS > 0 && entryL > 0 && entryS > 0) {
    entryAvg = (entryL * sizeL + entryS * sizeS) / (sizeL + sizeS);
  } else if (entryL > 0) entryAvg = entryL;
  else if (entryS > 0) entryAvg = entryS;

  out.global = {
    entry_avg: Math.round(entryAvg * 1e6) / 1e6,
    margen_usd: Math.round((margenL + margenS) * 1e4) / 1e4,
    size_usd_long: out.long.size_usd,
    size_usd_short: out.short.size_usd,
    size_usd_total: Math.round((sizeL + sizeS) * 1e4) / 1e4,
    impacto_1pct_usd: Math.round((impacto1pct(sizeL) + impacto1pct(sizeS)) * 1e4) / 1e4,
    fees_paid_usd: Math.round((fees.long + fees.short) * 1e4) / 1e4,
  };

  const pts = markL > 0 && markS > 0 ? Math.round((markS - markL) * 1e6) / 1e6 : 0;
  const mid = markL > 0 && markS > 0 ? (markL + markS) / 2 : 0;
  const pct = mid > 0 ? Math.round((pts / mid) * 10000) / 100 : 0;
  out.desequilibrio = {
    puntos: pts,
    pct,
    beneficio: beneficioDeseq(markL, markS, entryL, entryS),
    mark_long: markL,
    mark_short: markS,
  };

  const igris = snap.igris || {};
  const progresion = snap.progresion || {};
  const masa = sizeL + sizeS;
  const accion = String(igris.accion_heuristica || "");
  let estado = "REPOSO";
  if (masa > 0) {
    if (accion.includes("PODAR") || igris.fase_margen === "LEY_MARCIAL") estado = "REDUCCION";
    else estado = "CRECIMIENTO";
  }
  out.fase_manto = {
    estado,
    rango_beru: progresion.rango_ejercito || snap.rango_ejercito || "—",
    grado_beru: progresion.grado_beru || snap.grado_beru || "BLOQUEADO",
    fase_margen: igris.fase_margen || null,
    G_min: progresion.G_min ?? snap.progresion?.G_min ?? null,
  };

  const [mpl, mpcl] = mejoraEntrada(baselines.long, entryL, true);
  const [mps, mpcs] = mejoraEntrada(baselines.short, entryS, false);
  const hasBase = baselines.long > 0 || baselines.short > 0;
  out.optimizacion_igris = {
    mejora_pts_long: mpl,
    mejora_pct_long: mpcl,
    mejora_pts_short: mps,
    mejora_pct_short: mpcs,
    mejora_pts_global: hasBase ? Math.round(((mpl + mps) / 2) * 1e6) / 1e6 : 0,
    mejora_pct_global: hasBase ? Math.round(((mpcl + mpcs) / 2) * 1e4) / 1e4 : 0,
  };

  return out;
}

export function fmtUsd(n) {
  if (n == null || Number.isNaN(Number(n))) return "$0.00";
  return `$${Number(n).toFixed(2)}`;
}

export function fmtPct(n) {
  if (n == null || Number.isNaN(Number(n))) return "00%";
  const v = Number(n);
  if (v === 0) return "00%";
  return `${v.toFixed(2)}%`;
}

export function fmtNum(n, dig = 4) {
  if (n == null || Number.isNaN(Number(n)) || Number(n) === 0) return "00";
  return Number(n).toFixed(dig);
}

export function fmtLev(actual, max) {
  const a = actual == null || actual === 0 ? "00" : String(actual);
  const m = !max || max === 0 ? "00" : String(max);
  return `${a} / ${m}x`;
}
