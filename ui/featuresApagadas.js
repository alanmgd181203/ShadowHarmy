/**
 * Cosas apagadas del Pergamino — cableado listo, efecto/pantalla en pausa.
 *
 * Cómo encender: poner `encendido: true` en la entrada (y el flag local si existe).
 * No borrar el código; solo despertar cuando el Monarca lo pida.
 *
 * Panel clásico (dashboard_sombras.html) y Pergamino React (ui/) comparten esta lista
 * como memoria. Algunos flags viven también en su archivo (ej. SMOKE_ABYSS_ENABLED).
 */

export const FEATURES_APAGADAS = {
  humoAbismo: {
    encendido: false,
    nombre: "Humo abisal (video de sombras)",
    donde:
      "dashboard_sombras.html → SMOKE_ABYSS_ENABLED · assets/fx/humo_abismo.mp4",
    porQue:
      "Pausado en WiFi (latencia). Encender cuando el Pergamino sea app y el MP4 vaya empaquetado en local.",
  },

  /** Altar de marcha al despertar — solo Asalto (cirugía Igris 2026-08-12). */
  altarTresMarchas: {
    encendido: true,
    nombre: "Altar Asalto (solo marcha operativa)",
    donde: "ui/DeploymentAltar.jsx · core/pase_director.py · data/marcha_despliegue.json",
    porQue:
      "Solo Asalto. Personalizado/legado → asalto. Fill 100% · reserva 1. Paciencia = Greed.",
  },
};

/** true solo si la entrada existe y está encendida. */
export function featureEncendida(id) {
  return FEATURES_APAGADAS[id]?.encendido === true;
}

/** Lista legible para logs / Bellion / checklist. */
export function listarApagadas() {
  return Object.entries(FEATURES_APAGADAS)
    .filter(([, f]) => !f.encendido)
    .map(([id, f]) => ({ id, ...f }));
}
