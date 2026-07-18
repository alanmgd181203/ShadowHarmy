/**
 * Scaffold Camino de Ascensión (Tusk).
 *
 * Rangos de cuenta (provisional Monarca — sujeto a cambio):
 * - Aspirante = solo la estrella (5 Soldados mayor lev) · techo ~$104
 * - Aprendiz  = despertar el resto de Soldados de la flota · hasta ~$766 acum.
 * Snapshot X desde beru_capital; recalcular si Bybit mueve mínimos.
 */

/** 5 barcos mayor apalancamiento promedio · Soldado = capital X con colchón ~5%. */
export const VANGUARDIA_SOLDADOS = [
  { id: "v_btc", activo: "BTC", costoX: 14, margenLS: 12.5, lev: 100 },
  { id: "v_eth", activo: "ETH", costoX: 14, margenLS: 12.5, lev: 100 },
  { id: "v_xrp", activo: "XRP", costoX: 22, margenLS: 20.0, lev: 75 },
  { id: "v_sol", activo: "SOL", costoX: 27, margenLS: 25.0, lev: 75 },
  { id: "v_ada", activo: "ADA", costoX: 27, margenLS: 25.0, lev: 62.5 },
];

export const VANGUARDIA_SUMA_X = VANGUARDIA_SOLDADOS.reduce((s, v) => s + v.costoX, 0);

/** Techo Aspirante = corona de la estrella (5 Soldados). */
export const ASPIRANTE_TECHO_X = VANGUARDIA_SUMA_X;

/**
 * Suma X Soldado flota completa (22).
 * Aprendiz = despertar los Soldados que faltan tras la vanguardia → este techo.
 */
export const APRENDIZ_TECHO_FLOTA_SOLDADO_X = 766;

/** Piso gestación: bajo el Soldado más barato de la vanguardia. */
export const FASE_CERO_TECHO_X = Math.min(...VANGUARDIA_SOLDADOS.map((v) => v.costoX));

export const ASCENSION_RANKS = [
  {
    id: "nivel_0",
    nivel: "0",
    titulo: "Sin rango",
    subtitulo: `Gestacion del manto · $0 – ~$${FASE_CERO_TECHO_X - 1}`,
    zigzag: "center",
    gapBefore: "1.5rem",
    peso: "fragil",
    layout: "gestacion",
    nodes: [
      {
        id: "n0_gestacion",
        forma: "trazo_roto",
        escala: "sm",
        etiqueta: "Fase Cero",
        valor: `< $${FASE_CERO_TECHO_X}`,
        peso: "fragil",
      },
    ],
  },
  {
    id: "aspirante",
    nivel: "1",
    titulo: "Aspirante",
    subtitulo: `Estrella · 5 Soldados · ~$${ASPIRANTE_TECHO_X}`,
    zigzag: "center",
    gapBefore: "2rem",
    peso: "firme",
    layout: "estrella",
    nodes: [
      ...VANGUARDIA_SOLDADOS.map((v) => ({
        id: v.id,
        forma: "garra",
        escala: "sm",
        etiqueta: v.activo,
        valor: `$${v.costoX}`,
        peso: "fragil",
        activo: v.activo,
        costoX: v.costoX,
        margenLS: v.margenLS,
        lev: v.lev,
      })),
      {
        id: "asp_corona",
        forma: "poligono",
        escala: "md",
        etiqueta: "Corona",
        valor: `$${VANGUARDIA_SUMA_X}`,
        peso: "fortificado",
      },
    ],
  },
  {
    id: "aprendiz",
    nivel: "2",
    titulo: "Aprendiz de Mago",
    subtitulo: `Resto Soldados flota · hasta ~$${APRENDIZ_TECHO_FLOTA_SOLDADO_X}`,
    zigzag: "left",
    gapBefore: "3.25rem",
    peso: "firme",
    nodes: [
      {
        id: "apr_caballeros",
        forma: "cuña",
        escala: "md",
        etiqueta: "Caballeros",
        valor: "—",
        peso: "firme",
      },
    ],
  },
  {
    id: "brujo",
    nivel: "3",
    titulo: "Brujo",
    subtitulo: "Flota despierta · horizonte",
    zigzag: "right",
    gapBefore: "4rem",
    peso: "fortificado",
    nodes: [
      { id: "bru_flota", forma: "agresivo", escala: "lg", etiqueta: "Flota", valor: "—", peso: "fortificado" },
    ],
  },
  {
    id: "mariscal_sombra",
    nivel: "∞",
    titulo: "Senor de las Sombras",
    subtitulo: "Horizonte · aun sin tallar",
    zigzag: "center",
    gapBefore: "5rem",
    peso: "coloso",
    nodes: [
      { id: "senor", forma: "coloso", escala: "xl", etiqueta: "Trono vacio", valor: "—", peso: "coloso" },
    ],
  },
];

/**
 * Geometrías únicas — ley de asimetría (arte).
 */
export const FORMA_CLIP = {
  trazo_roto: "polygon(4% 18%, 38% 0%, 72% 14%, 100% 8%, 92% 48%, 100% 88%, 58% 100%, 22% 92%, 0% 62%, 12% 38%)",
  garra: "polygon(50% 0%, 72% 28%, 100% 32%, 78% 55%, 88% 100%, 50% 78%, 12% 100%, 22% 55%, 0% 32%, 28% 28%)",
  rombo: "polygon(50% 0%, 100% 50%, 50% 100%, 0% 50%)",
  cuña: "polygon(0% 12%, 100% 0%, 88% 100%, 8% 92%)",
  poligono: "polygon(8% 0%, 100% 12%, 92% 100%, 0% 88%)",
  rasgado: "polygon(0% 6%, 94% 0%, 100% 42%, 88% 100%, 4% 94%, 12% 48%)",
  agresivo: "polygon(0% 20%, 18% 0%, 55% 8%, 100% 0%, 92% 55%, 100% 100%, 40% 92%, 0% 100%, 12% 58%)",
  coloso: "polygon(2% 0%, 98% 4%, 100% 55%, 90% 100%, 8% 96%, 0% 40%)",
};

/** Vértices de la estrella irregular (ángulo deg, radio %). */
export const ESTRELLA_LAYOUT = [
  { id: "v_btc", angle: -90, r: 40 },
  { id: "v_eth", angle: -18, r: 46 },
  { id: "v_xrp", angle: 54, r: 42 },
  { id: "v_sol", angle: 126, r: 48 },
  { id: "v_ada", angle: 198, r: 44 },
];

export function flattenNodeOrder(ranks = ASCENSION_RANKS) {
  const out = [];
  for (const r of ranks) {
    for (const n of r.nodes) out.push(n.id);
  }
  return out;
}

export function ranksFromHorizon(ranks = ASCENSION_RANKS) {
  return [...ranks].reverse();
}

export function vanguardiaIds() {
  return VANGUARDIA_SOLDADOS.map((v) => v.id);
}

/** Cuántos Soldados de vanguardia ya están encendidos (achieved/frontier). */
export function countLitVanguardia(progress, order = flattenNodeOrder()) {
  let n = 0;
  for (const id of vanguardiaIds()) {
    const ph = resolveNodePhase(id, progress, order);
    if (ph === "achieved" || ph === "frontier") n += 1;
  }
  return n;
}

export function aspiranteCoronado(progress, order = flattenNodeOrder()) {
  const ph = resolveNodePhase("asp_corona", progress, order);
  return ph === "achieved" || ph === "frontier";
}

/** Equity acumulada demo al llegar a un nodo de vanguardia. */
export function equityLabelForNode(nodeId) {
  if (nodeId === "n0_gestacion") return `< $${FASE_CERO_TECHO_X}`;
  let sum = 0;
  for (const v of VANGUARDIA_SOLDADOS) {
    sum += v.costoX;
    if (v.id === nodeId) return `~$${sum}`;
  }
  if (nodeId === "asp_corona") return `~$${VANGUARDIA_SUMA_X}`;
  return "—";
}

/**
 * Demo: potencial hasta corona Aspirante (5 Soldados + corona).
 * Logrado arranca en gestación.
 */
export const DEMO_PROGRESS = {
  potentialNodeId: "asp_corona",
  achievedNodeId: "n0_gestacion",
  equityLabel: `< $${FASE_CERO_TECHO_X}`,
};

/**
 * locked | potential | achieved | frontier
 */
export function resolveNodePhase(nodeId, { potentialNodeId, achievedNodeId }, order = flattenNodeOrder()) {
  const i = order.indexOf(nodeId);
  const p = order.indexOf(potentialNodeId);
  const a = order.indexOf(achievedNodeId);
  if (i < 0) return "locked";
  if (a >= 0 && i < a) return "achieved";
  if (a >= 0 && i === a) return "frontier";
  if (p >= 0 && i <= p) return "potential";
  return "locked";
}

export function resolveRankPhase(rank, progress, order = flattenNodeOrder()) {
  if (rank.id === "aspirante") {
    if (aspiranteCoronado(progress, order)) return "frontier";
    const lit = countLitVanguardia(progress, order);
    if (lit > 0) return lit >= 5 ? "achieved" : "frontier";
    const g = resolveNodePhase("n0_gestacion", progress, order);
    if (g === "frontier" || g === "achieved") return "potential";
    return "potential";
  }
  const phases = rank.nodes.map((n) => resolveNodePhase(n.id, progress, order));
  if (phases.every((s) => s === "achieved" || s === "frontier")) {
    return phases.includes("frontier") ? "frontier" : "achieved";
  }
  if (phases.some((s) => s === "frontier")) return "frontier";
  if (phases.some((s) => s === "achieved" || s === "potential")) return "potential";
  return "locked";
}

export function crackFillRatio(nodeId, order = flattenNodeOrder()) {
  const cur = order.indexOf(nodeId);
  if (cur < 0 || order.length <= 1) return 0;
  return (cur + 1) / order.length;
}

export function nextAchievedAlongPotential(achievedId, potentialId, order = flattenNodeOrder()) {
  const a = order.indexOf(achievedId);
  const p = order.indexOf(potentialId);
  if (a < 0) return order[0] || achievedId;
  if (a >= p) return achievedId;
  return order[a + 1] || achievedId;
}
