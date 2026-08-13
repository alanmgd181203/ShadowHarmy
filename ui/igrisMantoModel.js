/**
 * Modelo portal MANTO · Igris — datos reales; secciones siempre presentes.
 * Vacío = etiquetas "APAGADO" / "AÚN NO" / "—" (nunca inventar despliegue).
 */

import { desdeEstadoVivo } from "./assetDetailModel.js";

const FRESCO_S = 120;
const VIEJO_S = 1800;

const FLOTA_FALLBACK = [
  "AAVE", "ADA", "APT", "AVAX", "BCH", "BTC", "DOGE", "DOT", "ETC", "ETH",
  "FIL", "HYPE", "LINK", "LTC", "MNT", "NEAR", "OP", "SOL", "SUI", "UNI", "XLM", "XRP",
];

export function fmtUsd(n, dig = 2) {
  if (n == null || Number.isNaN(Number(n))) return "—";
  return `$${Number(n).toLocaleString("es-MX", {
    minimumFractionDigits: dig,
    maximumFractionDigits: dig,
  })}`;
}

export function fmtPct(n, dig = 1) {
  if (n == null || Number.isNaN(Number(n))) return "—";
  return `${Number(n).toFixed(dig)}%`;
}

export function fmtAge(sec) {
  if (sec == null || Number.isNaN(Number(sec)) || sec < 0) return "—";
  const s = Math.floor(Number(sec));
  if (s < 60) return `hace ${s}s`;
  if (s < 3600) return `hace ${Math.floor(s / 60)}m`;
  if (s < 86400) return `hace ${Math.floor(s / 3600)}h`;
  return `hace ${Math.floor(s / 86400)}d`;
}

function baseFromFrente(frente) {
  const fu = String(frente || "").toUpperCase();
  const m = fu.match(/^([A-Z0-9]+?)(USDT|USDC|USD)/);
  return m ? m[1] : fu.slice(0, 4);
}

function basesDesdeSnap(snap) {
  const set = new Set();
  for (const f of Object.keys(snap?.pesos_por_frente || {})) {
    set.add(baseFromFrente(f));
  }
  for (const k of Object.keys(snap?.igris_asset_details || {})) {
    set.add(String(k).toUpperCase());
  }
  const act = snap?.igris?.plan_crecimiento?.santos_grial;
  if (Array.isArray(act)) {
    for (const a of act) set.add(String(a).toUpperCase());
  }
  if (set.size === 0) {
    for (const b of FLOTA_FALLBACK) set.add(b);
  }
  return [...set].filter(Boolean).sort();
}

function pulsoDesdeTs(ts, nowSec) {
  if (ts == null || !(Number(ts) > 0)) {
    return {
      tab: "SIN_DATOS",
      estado: "SIN_SENAL",
      label: "SIN SEÑAL",
      frescura: "muerto",
      frescuraLabel: "SIN DATOS",
      ageSec: null,
      ageLabel: "—",
    };
  }
  const age = Math.max(0, nowSec - Number(ts));
  if (age > VIEJO_S) {
    return {
      tab: "DORMIDO",
      estado: "DORMIDO",
      label: "DORMIDO",
      frescura: "muerto",
      frescuraLabel: "CONGELADO",
      ageSec: age,
      ageLabel: fmtAge(age),
    };
  }
  if (age > FRESCO_S) {
    return {
      tab: "DORMIDO",
      estado: "DORMIDO",
      label: "DORMIDO",
      frescura: "viejo",
      frescuraLabel: "VIEJO",
      ageSec: age,
      ageLabel: fmtAge(age),
    };
  }
  return {
    tab: "DESPIERTO",
    estado: "DESPIERTO",
    label: "DESPIERTO",
    frescura: "fresco",
    frescuraLabel: "FRESCO",
    ageSec: age,
    ageLabel: fmtAge(age),
  };
}

function libroFrente(frentes, keyHints) {
  const entries = Object.entries(frentes || {});
  for (const hint of keyHints) {
    const hit = entries.find(([k]) => String(k).toUpperCase().includes(hint));
    if (hit) {
      const v = hit[1] || {};
      const bids = v.bids ?? v.n_bids ?? null;
      const asks = v.asks ?? v.n_asks ?? null;
      const edad = v.edad_s ?? v.age_s ?? null;
      const stale = v.stale === true;
      const vacio =
        stale ||
        bids == null ||
        asks == null ||
        Number(bids) <= 0 ||
        Number(asks) <= 0;
      return {
        frente: hit[0],
        bids: bids == null ? null : Number(bids),
        asks: asks == null ? null : Number(asks),
        edad_s: edad == null ? null : Number(edad),
        stale,
        vacio,
        estado: vacio ? "VACÍO" : stale ? "VIEJO" : "VIVO",
      };
    }
  }
  return {
    frente: "—",
    bids: null,
    asks: null,
    edad_s: null,
    stale: true,
    vacio: true,
    estado: "VACÍO",
  };
}

function librosDesde(snap, hb, activoFoco = null) {
  const act =
    String(
      activoFoco ||
        snap?.igris?.meta_engorde?.activo ||
        snap?.igris?.libros_foco?.activo ||
        "ETH",
    ).toUpperCase() || "ETH";

  const fromFoco = snap?.igris?.libros_foco || null;
  const fromSnap = snap?.igris?.libros_eth || snap?.libros_eth || null;
  const hbFrentes = hb?.libros_eth || null;

  let frentes = {};
  let fromOk = null;
  let fromStale = null;

  if (fromFoco && String(fromFoco.activo || "").toUpperCase() === act && fromFoco.frentes) {
    frentes = fromFoco.frentes;
    fromOk = fromFoco.ok;
    fromStale = fromFoco.stale;
  } else if (act === "ETH" && fromSnap?.frentes) {
    frentes = fromSnap.frentes;
    fromOk = fromSnap.ok;
    fromStale = fromSnap.stale;
  } else if (fromFoco?.frentes) {
    frentes = fromFoco.frentes;
    fromOk = fromFoco.ok;
    fromStale = fromFoco.stale;
  } else if (act === "ETH" && hbFrentes && typeof hbFrentes === "object") {
    frentes = hbFrentes.frentes || hbFrentes;
    fromOk = hb?.books_eth;
    fromStale = hb?.books_stale;
  }

  const lineal = libroFrente(frentes, [
    `${act}USDT_LINEAL`,
    "LINEAL",
    `${act}USDT`,
  ]);
  const inverso = libroFrente(frentes, [
    `${act}USD_INVERSE`,
    "INVERSE",
    `${act}USD`,
  ]);
  // Si no hubo snapshot, etiqueta frentes esperados
  if (lineal.frente === "—" ) lineal.frente = `${act}USDT_LINEAL`;
  if (inverso.frente === "—") inverso.frente = `${act}USD_INVERSE`;

  const ok =
    fromOk === true ||
    hb?.books_eth === true ||
    (!lineal.vacio && !inverso.vacio);
  const stale =
    fromStale === true ||
    hb?.books_stale === true ||
    lineal.stale ||
    inverso.stale ||
    lineal.vacio ||
    inverso.vacio;
  let estado = "VIVO";
  if (lineal.vacio && inverso.vacio) estado = "VACÍO";
  else if (stale || !ok) estado = "VIEJO";
  return {
    estado,
    ok: !!ok,
    stale: !!stale,
    activo: act,
    lineal,
    inverso,
  };
}

function motivoLeyLegible(motivo) {
  const m = String(motivo || "").toLowerCase();
  if (!m) return "Aún no";
  if (m.includes("sin_puerta")) return "Aún no hay disparo";
  if (m.includes("asim")) return "Bloqueo por asimetría";
  if (m.includes("fail") || m.includes("fall")) return "Ley de masa fallida";
  return String(motivo).replace(/_/g, " ");
}

function manosDesdeOido(snap) {
  const rec = (snap?.bellion_oido?.recientes || []).slice().reverse();
  const hit = rec.find((r) => {
    const blob = `${r?.accion || ""} ${r?.detalle || ""} ${r?.general || ""}`.toUpperCase();
    return (
      blob.includes("UNMATCHED IP") ||
      blob.includes("10010") ||
      blob.includes("LEVERAGE") ||
      blob.includes("NAV_EXCEPCI") ||
      (blob.includes("IP") && blob.includes("BOUND"))
    );
  });
  if (!hit) {
    return {
      hay: false,
      titulo: "SIN ALERTA",
      detalle: "Sin alerta reciente de manos / IP",
      ts: null,
      nivel: "salud",
    };
  }
  const det = String(hit.detalle || hit.accion || "");
  let titulo = "ALERTA MANOS";
  if (/unmatched ip|10010/i.test(det)) titulo = "IP NO COINCIDE (BYBIT)";
  else if (/leverage/i.test(det)) titulo = "PALANCA FALLIDA";
  else if (/nav/i.test(det)) titulo = "NAV / CUENTA BLOQUEADA";
  return {
    hay: true,
    titulo,
    detalle: det.split("\n")[0].slice(0, 160),
    ts: hit.ts ?? null,
    nivel: hit.nivel || "critico",
  };
}

function filasManto(snap) {
  const bases = basesDesdeSnap(snap);
  const rows = bases.map((id) => {
    const det = desdeEstadoVivo(id, snap);
    const usdL = Number(det?.global?.size_usd_long || det?.long?.size_usd || 0);
    const usdS = Number(det?.global?.size_usd_short || det?.short?.size_usd || 0);
    const total = usdL + usdS;
    const pctL = total > 0 ? (usdL / total) * 100 : null;
    const pctS = total > 0 ? (usdS / total) * 100 : null;
    const fase = String(det?.fase_manto?.estado || "").toUpperCase();
    const badge = total > 0 ? fase || "CRECIMIENTO" : "REPOSO";
    return {
      id,
      usdLong: usdL,
      usdShort: usdS,
      usdTotal: total,
      pctLong: pctL,
      pctShort: pctS,
      badge,
      tieneMasa: total > 1e-9,
    };
  });
  rows.sort((a, b) => b.usdTotal - a.usdTotal || a.id.localeCompare(b.id));
  return rows;
}

function padRank(ranking) {
  const out = ranking.slice(0, 3);
  while (out.length < 3) {
    out.push({
      n: out.length + 1,
      base: "—",
      modo: "aún no",
      score: null,
      vacio: true,
    });
  }
  return out.map((r, i) => ({ ...r, n: i + 1, vacio: r.vacio || r.base === "—" }));
}

/**
 * @param {object|null} snap
 * @param {object|null} hb
 * @param {number} [nowSec]
 */
export function mantoDesdeFuentes(snap, hb = null, nowSec = Date.now() / 1000) {
  const vacioTotal = {
    ok: false,
    pulso: pulsoDesdeTs(null, nowSec),
    chips: {
      marcha: "—",
      ventana: "—",
      meta: "AÚN NO",
      libros: "VACÍO",
      ley: "S/PUERTA",
      pulso: "MUERTO",
    },
    oxygen: {
      equity: null,
      oxigeno: null,
      margen: null,
      o2Pct: null,
      marchaTitulo: null,
      metaActivo: null,
      metaRestante: null,
    },
    ventana: {
      pctLong: null,
      pctShort: null,
      estado: null,
      ok: false,
      usdLong: 0,
      usdShort: 0,
      apagado: true,
      label: "APAGADO",
    },
    meta: {
      ok: false,
      activo: null,
      grado: null,
      paso: null,
      need: null,
      have: null,
      resta: null,
      fillPct: null,
      marchaId: null,
      metaLlena: false,
      activa: false,
      aunNo: true,
      labelBadge: "AÚN NO",
    },
    ley: {
      estado: "SIN PUERTA AÚN",
      ok: null,
      bloqueado: null,
      asimPct: null,
      activo: null,
      motivo: null,
      motivoLegible: "Aún no",
    },
    libros: { ...librosDesde({}, null, "ETH"), activo: "ETH" },
    frecuencia: {
      ranking: padRank([]),
      etaLabel: "sin ETA · sin frecuencia aún",
      aunNo: true,
      motivoVacio: "Sin ranking: hace falta Kaiser / historia manto o Igris despierto",
    },
    manos: {
      hay: false,
      titulo: "SIN ALERTA",
      detalle: "Sin ejército / sin oído aún",
      ts: null,
      nivel: "salud",
    },
    vanguardia: FLOTA_FALLBACK.slice(0, 5).map((id) => ({
      id,
      usdLong: 0,
      usdShort: 0,
      usdTotal: 0,
      pctLong: null,
      pctShort: null,
      badge: "REPOSO",
      tieneMasa: false,
    })),
    batallon: FLOTA_FALLBACK.slice(5).map((id) => ({
      id,
      usdLong: 0,
      usdShort: 0,
      usdTotal: 0,
      pctLong: null,
      pctShort: null,
      badge: "REPOSO",
      tieneMasa: false,
    })),
    nBatallon: Math.max(0, FLOTA_FALLBACK.length - 5),
  };

  if (!snap || typeof snap !== "object") return vacioTotal;

  const igris = snap.igris || {};
  const tes = snap.tusk_tesoreria || {};
  const march = igris.marcha || {};
  const vent = igris.ventana_manto || {};
  const meta = igris.meta_engorde || {};
  const ley = igris.ley_masa || {};
  const freq = igris.frecuencia_manto || {};

  // DESPIERTO = misión activa o arise vivo. Preferir telemetría sueño (cirugía 2026-08-12).
  const mis = igris.mision || {};
  const tsHb = hb?.ts ?? null;
  const tsIgrisSolo = igris.ts ?? igris.pulso_ts ?? igris.ultimo_latido_ts ?? null;
  const tsPulso =
    tsHb != null && Number(tsHb) > 0
      ? Number(tsHb)
      : tsIgrisSolo != null && Number(tsIgrisSolo) > 0
        ? Number(tsIgrisSolo)
        : null;
  let pulso = pulsoDesdeTs(tsPulso, nowSec);
  if (mis.sueno_mision === true || mis.dormido === true || mis.dormido === false) {
    const age =
      tsPulso != null && Number(tsPulso) > 0
        ? Math.max(0, nowSec - Number(tsPulso))
        : null;
    if (mis.dormido === true && !mis.mision_activa) {
      pulso = {
        tab: "DORMIDO",
        estado: "DORMIDO",
        label: "DORMIDO",
        frescura: age != null && age <= FRESCO_S ? "fresco" : "viejo",
        frescuraLabel: mis.sueno_mision ? "SUEÑO·MISIÓN" : "DORMIDO",
        ageSec: age,
        ageLabel: age != null ? fmtAge(age) : "—",
      };
    } else if (mis.dormido === false || mis.mision_activa) {
      const tipo = mis.mision_activa?.tipo || "misión";
      pulso = {
        tab: "DESPIERTO",
        estado: "DESPIERTO",
        label: "DESPIERTO",
        frescura: "fresco",
        frescuraLabel: String(tipo).toUpperCase(),
        ageSec: age,
        ageLabel: age != null ? fmtAge(age) : "—",
      };
    }
  }

  const usdL = Number(vent.usd_long ?? 0);
  const usdS = Number(vent.usd_short ?? 0);
  const mantoApagado = usdL + usdS <= 1e-9;
  const pctL = !mantoApagado && vent.pct_long != null ? Number(vent.pct_long) : null;
  const pctS =
    !mantoApagado && vent.pct_short != null
      ? Number(vent.pct_short)
      : pctL != null
        ? 100 - pctL
        : null;

  const need = meta.need_fill_usd ?? meta.need_usd ?? null;
  const have = meta.have_usd ?? null;
  const resta = meta.restante_usd ?? null;
  let fillPct = null;
  if (need != null && Number(need) > 0 && have != null) {
    fillPct = Math.max(0, Math.min(100, (Number(have) / Number(need)) * 100));
  } else if (meta.meta_llena === true) {
    fillPct = 100;
  } else if (have === 0 && need != null) {
    fillPct = 0;
  }

  const metaAunNo = !(meta.activo || meta.ok === true);
  const metaActiva = meta.ok === true && meta.meta_llena !== true && !!meta.activo;
  const activoFoco = String(meta.activo || "ETH").toUpperCase();

  let leyEstado = "SIN PUERTA AÚN";
  if (ley.ok === true) leyEstado = "OK";
  else if (ley.bloqueado === true || ley.ok === false) leyEstado = "BLOQUEADA";
  else if (String(ley.motivo || "").includes("sin_puerta") || ley.ok == null) {
    leyEstado = "SIN PUERTA AÚN";
  }

  const libros = librosDesde(snap, hb, activoFoco);
  const rankingRaw = (freq.ranking || []).slice(0, 3).map((r, i) => ({
    n: i + 1,
    base: r.base || r.activo || "—",
    modo: r.modo_sugerido || r.marcha || "—",
    score:
      r.score_paciencia != null
        ? Math.round(Number(r.score_paciencia) * 100)
        : r.score != null
          ? Number(r.score)
          : null,
    vacio: false,
  }));
  const ranking = padRank(rankingRaw);
  const freqAunNo = !(freq.ranking || []).length;
  const freqError = freq.error ? String(freq.error).slice(0, 80) : null;
  const motivoVacio = freqAunNo
    ? freqError
      ? `Sin ranking · ${freqError}`
      : "Sin ranking · Kaiser/frecuencia no alimenta (Igris dormido o sin historia)"
    : null;

  const mid = march.id || meta.marcha_id || null;
  const etaLote =
    mid && (freq.eta_lote_por_marcha?.[mid] || freq.eta_por_marcha?.[mid]);
  let etaLabel = "sin ETA · aún no";
  if (etaLote != null) {
    if (typeof etaLote === "object") {
      const h = etaLote.horas ?? etaLote.eta_h ?? etaLote.eta_horas;
      etaLabel = h != null ? `ETA ~${Number(h).toFixed(1)}h` : "sin ETA · lote sin horas";
    } else if (Number(etaLote) > 0) {
      etaLabel = `ETA ~${Number(etaLote).toFixed(1)}h`;
    }
  } else if (freqAunNo) {
    etaLabel = "sin ETA · sin frecuencia aún";
  }

  const filas = filasManto(snap);
  const vanguardia = filas.slice(0, 5);
  while (vanguardia.length < 5) {
    vanguardia.push({
      id: "—",
      usdLong: 0,
      usdShort: 0,
      usdTotal: 0,
      pctLong: null,
      pctShort: null,
      badge: "AÚN NO",
      tieneMasa: false,
    });
  }
  const batallon = filas.slice(5);

  const margen = snap.margen_ocupado ?? null;
  const o2 = tes.oxigeno_guerra_usd ?? snap.masa_autorizada ?? null;
  const equity = tes.equity_usd ?? snap.masa_bruta_real ?? null;
  const o2Pct =
    margen != null && Number(margen) >= 0 ? Math.max(0, 100 - Number(margen)) : null;

  const chips = {
    marcha: march.titulo || mid || "—",
    ventana: mantoApagado
      ? "APAGADO"
      : vent.estado || (vent.ok === true ? "OK" : "—"),
    meta: meta.meta_llena ? "LLENA" : metaActiva ? "ACTIVA" : "AÚN NO",
    libros: libros.estado,
    ley: leyEstado === "SIN PUERTA AÚN" ? "S/PUERTA" : leyEstado,
    pulso:
      pulso.frescura === "fresco"
        ? "VIVO"
        : pulso.frescura === "viejo"
          ? "VIEJO"
          : "MUERTO",
  };

  return {
    ok: true,
    pulso,
    chips,
    oxygen: {
      equity,
      oxigeno: o2,
      margen,
      o2Pct,
      marchaTitulo: march.titulo || mid || null,
      metaActivo: meta.activo || null,
      metaRestante: resta,
    },
    ventana: {
      pctLong: pctL,
      pctShort: pctS,
      estado: vent.estado || null,
      ok: vent.ok === true && !mantoApagado,
      usdLong: usdL,
      usdShort: usdS,
      apagado: mantoApagado,
      label: mantoApagado ? "APAGADO" : vent.estado || "OK",
    },
    meta: {
      ok: meta.ok === true,
      activo: meta.activo || null,
      grado: meta.grado || null,
      paso: meta.paso_n ?? null,
      need,
      have,
      resta,
      fillPct,
      marchaId: meta.marcha_id || mid,
      metaLlena: meta.meta_llena === true,
      activa: metaActiva,
      aunNo: metaAunNo,
      labelBadge: meta.meta_llena
        ? "LLENA"
        : metaActiva
          ? "ACTIVA"
          : "AÚN NO",
    },
    ley: {
      estado: leyEstado,
      ok: ley.ok,
      bloqueado: ley.bloqueado,
      asimPct: ley.asim_pct != null ? Number(ley.asim_pct) : null,
      activo: ley.activo || null,
      motivo: ley.motivo || null,
      motivoLegible: motivoLeyLegible(ley.motivo),
    },
    libros,
    frecuencia: { ranking, etaLabel, aunNo: freqAunNo, motivoVacio },
    manos: manosDesdeOido(snap),
    vanguardia,
    batallon,
    nBatallon: batallon.length,
  };
}
