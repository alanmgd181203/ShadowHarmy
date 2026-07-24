/**
 * Modelo Sub-Santuario Beru — espejo de estado_vivo.beru_asset_details / beru_flota.
 */
export function snapshotCero(symbol) {
  const s = String(symbol || "ETH").toUpperCase();
  return {
    symbol: s,
    fuente: "cero",
    n_barcos: 0,
    n_caza: 0,
    n_negociando: 0,
    n_acechando: 0,
    n_mega: 0,
    masa_total_usd: 0,
    pnl_est_usd: 0,
    fees_paid_usd: null,
    centro_0: 0,
    composicion: { caza: 0, negociando: 0, acechando: 0, pct_caza: 0, pct_negociando: 0 },
    red_engorde: null,
    rails_vivos: [],
    rails_disponibles: [],
    barcos: [],
    grafica: { centro_0: 0, niveles: [] },
    cronica: [],
    nota_pnl: "Sin barcos — legión en reposo.",
  };
}

export function desdeEstadoVivo(symbol, snap) {
  const s = String(symbol || "").toUpperCase();
  const pre = (snap?.beru_asset_details || {})[s];
  if (pre && typeof pre === "object") {
    return { ...snapshotCero(s), ...pre, fuente: pre.fuente || "vivo" };
  }
  return snapshotCero(s);
}

export function flotaDesdeEstado(snap) {
  const f = snap?.beru_flota || {};
  return {
    semilla: f.semilla || snap?.ticker_base || "ETH",
    n_activos: f.n_activos || 0,
    n_barcos_total: f.n_barcos_total || 0,
    activos: Array.isArray(f.activos) ? f.activos : [],
  };
}

export function fmtUsd(n) {
  if (n == null || Number.isNaN(Number(n))) return "—";
  return `$${Number(n).toFixed(2)}`;
}

export function fmtPct(n) {
  if (n == null || Number.isNaN(Number(n))) return "—";
  return `${Number(n).toFixed(2)}%`;
}

export function fmtNum(n, d = 4) {
  if (n == null || Number.isNaN(Number(n))) return "—";
  return Number(n).toFixed(d);
}
