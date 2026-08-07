/**
 * Dos marchas de despliegue — ritmo del manto Igris + lote del pase.
 * Espejo backend: core/pase_director.py · data/marcha_despliegue.json
 * Sello 2 marchas: asalto (rápido) · personalizado (~T). Legado → asalto.
 */

/** Legado no operativo: se mapea a asalto al hidratar / elegir. */
export const MARCHA_LEGACY_MAP = {
  tactico: "asalto",
  marcha_forzada: "asalto",
  forzada: "asalto",
  inmediato: "asalto",
  custom: "personalizado",
  duracion: "personalizado",
};

export const DEPLOYMENT_MARCHES = [
  {
    id: "asalto",
    titulo: "Asalto Inmediato",
    tagline: "Cero espera",
    voz: "El ejercito entra ya (market). Peaje aceptado.",
    tiempoEstimado: "—",
    tiempoNota: "minutos",
    impacto: {
      label: "Rentabilidad sacrificada",
      valor: "~0.8 – 2%+",
      detalle: "umbral 0 · reserva 1 · fill 100%",
    },
    ritmoMs: 280,
    reservaPasos: 1,
    umbralFeesMult: 0.0,
    forceMarket: true,
    fillRatio: 1.0,
  },
  {
    id: "personalizado",
    titulo: "Marcha Personalizada",
    tagline: "Por duracion",
    voz: "El Monarca escribe ~T dias; cada par calibra umbral",
    tiempoEstimado: "—",
    tiempoNota: "obligatorio: dias",
    impacto: {
      label: "Calibracion viva",
      valor: "T dias",
      detalle: "reserva 1 · fill 100% · reajuste vivo",
    },
    ritmoMs: 900,
    reservaPasos: 1,
    umbralFeesMult: -1,
    forceMarket: false,
    fillRatio: 1.0,
    requiereDuracion: true,
  },
];

export const MARCH_STORAGE_KEY = "shadow_marcha_despliegue";
export const MARCHA_API_URL = "/data/marcha_despliegue.json";
export const MARCHA_DEFAULT = "asalto";

export function normalizeMarchId(id) {
  const raw = String(id || "").toLowerCase().trim();
  if (!raw) return null;
  const mapped = MARCHA_LEGACY_MAP[raw] || raw;
  return DEPLOYMENT_MARCHES.some((m) => m.id === mapped) ? mapped : null;
}

export function loadMarchId() {
  try {
    const v = localStorage.getItem(MARCH_STORAGE_KEY);
    return normalizeMarchId(v);
  } catch {
    return null;
  }
}

export function saveMarchId(id) {
  try {
    const mid = normalizeMarchId(id);
    if (!mid) {
      localStorage.removeItem(MARCH_STORAGE_KEY);
      return;
    }
    localStorage.setItem(MARCH_STORAGE_KEY, mid);
  } catch {
    /* ignore */
  }
}

export function marchById(id) {
  const mid = normalizeMarchId(id);
  return DEPLOYMENT_MARCHES.find((m) => m.id === mid) || null;
}

/** Hydrata Ascensión desde data/marcha_despliegue.json (fuente de verdad). */
export async function hydrateMarchFromBackend() {
  try {
    const res = await fetch(MARCHA_API_URL, { cache: "no-store" });
    if (!res.ok) return null;
    const data = await res.json();
    const id = normalizeMarchId(data?.marcha_id || data?.id);
    if (!id) return null;
    return {
      id,
      duracionDias: data.duracion_dias != null ? Number(data.duracion_dias) : null,
      equityUsd: data.equity_usd != null ? Number(data.equity_usd) : null,
      fillRatio: data.fill_ratio != null ? Number(data.fill_ratio) : 1,
      reservaPasos: data.reserva_pasos != null ? Number(data.reserva_pasos) : 1,
      raw: data,
    };
  } catch {
    return null;
  }
}

/**
 * Persiste marcha vía POST (panel/Vite → set_marcha_cli / guardar_marcha).
 * opts: { duracionDias, equity }
 */
export async function persistMarchaBackend(marchaId, opts = {}) {
  const m = marchById(marchaId);
  if (!m) return false;
  if (m.requiereDuracion) {
    const d = Number(opts.duracionDias);
    if (!(d > 0)) return false;
  }
  const body = {
    marcha_id: m.id,
    titulo: m.titulo,
    reserva_pasos: m.reservaPasos,
    umbral_fees_mult: m.umbralFeesMult,
    force_market: m.forceMarket,
    fill_ratio: m.fillRatio ?? 1.0,
    ts: Date.now() / 1000,
  };
  if (opts.duracionDias != null && Number(opts.duracionDias) > 0) {
    body.duracion_dias = Number(opts.duracionDias);
  }
  if (opts.equity != null && Number(opts.equity) > 0) {
    body.equity_usd = Number(opts.equity);
  }
  try {
    const res = await fetch(MARCHA_API_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    return res.ok;
  } catch {
    return false;
  }
}

/** ETA lote desde estado_vivo.igris.frecuencia_manto */
export function etaLoteLabel(freq, marchaId) {
  const mid = normalizeMarchId(marchaId) || marchaId;
  const lote = freq?.eta_lote_por_marcha?.[mid];
  if (!lote || lote.eta_h == null) return "—";
  const h = Number(lote.eta_h);
  if (h < 1) return `~${Math.round(h * 60)} min`;
  if (h < 48) return `~${h.toFixed(1)} h`;
  return `~${(h / 24).toFixed(1)} d`;
}
