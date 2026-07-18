/**
 * Tres marchas de despliegue (onboarding).
 * Tiempo estimado = placeholder "—" hasta calibrar con ranking/Igris.
 */

export const DEPLOYMENT_MARCHES = [
  {
    id: "tactico",
    titulo: "Despliegue Tactico",
    tagline: "Espera total",
    voz: "Igris caza el mejor Ask/Bid",
    tiempoEstimado: "—",
    tiempoNota: "luego: ~1–2 dias",
    impacto: {
      label: "Rentabilidad sacrificada",
      valor: "~0 – 0.3%",
      detalle: "minima friccion · preferencia maker",
    },
    ritmoMs: 1400,
  },
  {
    id: "marcha_forzada",
    titulo: "Marcha Forzada",
    tagline: "Medio espero",
    voz: "Equilibrio entre prisa y precio",
    tiempoEstimado: "—",
    tiempoNota: "luego: horas",
    impacto: {
      label: "Rentabilidad sacrificada",
      valor: "~0.3 – 0.8%",
      detalle: "evita peores momentos · mix limit/market",
    },
    ritmoMs: 700,
  },
  {
    id: "asalto",
    titulo: "Asalto Inmediato",
    tagline: "Cero espera",
    voz: "El ejercito entra ya",
    tiempoEstimado: "—",
    tiempoNota: "luego: minutos",
    impacto: {
      label: "Rentabilidad sacrificada",
      valor: "~0.8 – 2%+",
      detalle: "slippage + fees market · listo al instante",
    },
    ritmoMs: 280,
  },
];

export const MARCH_STORAGE_KEY = "shadow_marcha_despliegue";

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

export function marchById(id) {
  return DEPLOYMENT_MARCHES.find((m) => m.id === id) || null;
}
