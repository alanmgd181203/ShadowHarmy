/**
 * Tres marchas de despliegue — ritmo del manto Igris + lote del pase.
 * Espejo backend: core/pase_director.py · data/marcha_despliegue.json
 *
 * Táctico  = umbral ≥ fees · reserva 3 pasos
 * Forzada  = umbral ≥ ½ fees · reserva 2
 * Asalto   = umbral 0 / market · reserva 0
 */

export const DEPLOYMENT_MARCHES = [
  {
    id: "tactico",
    titulo: "Despliegue Tactico",
    tagline: "Espera total",
    voz: "Igris solo entra si el spread cubre fees",
    tiempoEstimado: "—",
    tiempoNota: "luego: ~1–2 dias",
    impacto: {
      label: "Rentabilidad sacrificada",
      valor: "~0 – 0.3%",
      detalle: "umbral = fees · reserva 3 pasos",
    },
    ritmoMs: 1400,
    reservaPasos: 3,
    umbralFeesMult: 1.0,
    forceMarket: false,
  },
  {
    id: "marcha_forzada",
    titulo: "Marcha Forzada",
    tagline: "Medio espero",
    voz: "Umbral a mitad de fees · lote con colchon",
    tiempoEstimado: "—",
    tiempoNota: "luego: horas",
    impacto: {
      label: "Rentabilidad sacrificada",
      valor: "~0.3 – 0.8%",
      detalle: "umbral = ½ fees · reserva 2 pasos",
    },
    ritmoMs: 700,
    reservaPasos: 2,
    umbralFeesMult: 0.5,
    forceMarket: false,
  },
  {
    id: "asalto",
    titulo: "Asalto Inmediato",
    tagline: "Cero espera",
    voz: "El ejercito entra ya (market)",
    tiempoEstimado: "—",
    tiempoNota: "luego: minutos",
    impacto: {
      label: "Rentabilidad sacrificada",
      valor: "~0.8 – 2%+",
      detalle: "umbral 0 · sin reserva de lote",
    },
    ritmoMs: 280,
    reservaPasos: 0,
    umbralFeesMult: 0.0,
    forceMarket: true,
  },
];

export const MARCH_STORAGE_KEY = "shadow_marcha_despliegue";
export const MARCHA_API_URL = "/data/marcha_despliegue.json";

export function loadMarchId() {
  try {
    const v = localStorage.getItem(MARCH_STORAGE_KEY);
    return v && v.length > 0 ? v : null;
  } catch {
    return null;
  }
}

export function saveMarchId(id) {
  try {
    if (!id) {
      localStorage.removeItem(MARCH_STORAGE_KEY);
      return;
    }
    localStorage.setItem(MARCH_STORAGE_KEY, id);
  } catch {
    /* ignore */
  }
}

/** Persiste marcha para el ejército (Vite POST → data/marcha_despliegue.json). */
export async function persistMarchaBackend(marchaId) {
  const m = marchById(marchaId);
  if (!m) return false;
  const body = {
    marcha_id: m.id,
    titulo: m.titulo,
    reserva_pasos: m.reservaPasos,
    umbral_fees_mult: m.umbralFeesMult,
    force_market: m.forceMarket,
    ts: Date.now() / 1000,
  };
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

export function marchById(id) {
  return DEPLOYMENT_MARCHES.find((m) => m.id === id) || null;
}
