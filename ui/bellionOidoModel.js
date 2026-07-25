/**
 * Modelo oído Bellion — estado_vivo.bellion_oido
 */
export function oidoCero() {
  return {
    ts: 0,
    fuente: "cero",
    n_anillo: 0,
    counts: { critico: 0, ejecucion: 0, salud: 0, ruido: 0 },
    recientes: [],
    por_nivel: { critico: [], ejecucion: [], salud: [] },
    nota: "Sin susurro aún — despertando al ejército.",
  };
}

export function oidoDesdeEstado(snap) {
  const o = snap?.bellion_oido;
  if (!o || typeof o !== "object" || o.error) {
    return oidoCero();
  }
  return {
    ...oidoCero(),
    ...o,
    counts: { ...oidoCero().counts, ...(o.counts || {}) },
    por_nivel: {
      critico: Array.isArray(o.por_nivel?.critico) ? o.por_nivel.critico : [],
      ejecucion: Array.isArray(o.por_nivel?.ejecucion) ? o.por_nivel.ejecucion : [],
      salud: Array.isArray(o.por_nivel?.salud) ? o.por_nivel.salud : [],
    },
    recientes: Array.isArray(o.recientes) ? o.recientes : [],
  };
}

export function fmtTs(ts) {
  if (!ts) return "—";
  try {
    return new Date(Number(ts) * 1000).toLocaleTimeString("es-MX", {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
  } catch {
    return "—";
  }
}
