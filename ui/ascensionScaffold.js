/**
 * Scaffold Camino de Ascensión (Tusk).
 *
 * Rangos de cuenta — firma Monarca 2026-07-19 (pase Coliseo):
 * - Aspirante = estrella 5 Soldados (ETH HYPE XRP MNT LTC) · techo ~$123
 * - Aprendiz  = resto Santos + AVAX Caballero · techo ~$411
 * - Brujo     = hasta LTC Mariscal · techo ~$1451
 * - Chamán    = hasta 13 Mariscales · techo ~$3161
 * Pergamino: migracion/PASE_BATALLA_13_SANTOS.md
 */

/** Estrella Aspirante — pasos 1–5 del pase (costo X Igris). */
export const VANGUARDIA_SOLDADOS = [
  { id: "v_eth", activo: "ETH", costoX: 14, margenLS: 12.5, lev: 100 },
  { id: "v_hype", activo: "HYPE", costoX: 28, margenLS: 26.32, lev: 47.5 },
  { id: "v_xrp", activo: "XRP", costoX: 18, margenLS: 16.67, lev: 75 },
  { id: "v_mnt", activo: "MNT", costoX: 36, margenLS: 33.33, lev: 37.5 },
  { id: "v_ltc", activo: "LTC", costoX: 27, margenLS: 25.0, lev: 50 },
];

export const VANGUARDIA_SUMA_X = VANGUARDIA_SOLDADOS.reduce((s, v) => s + v.costoX, 0);

/** Techos del pase (acumulado Igris). */
export const ASPIRANTE_TECHO_X = 123;
export const APRENDIZ_TECHO_FLOTA_SOLDADO_X = 411;
export const BRUJO_TECHO_X = 1451;
export const CHAMAN_TECHO_X = 3161;

/** Piso gestación: bajo el Soldado más barato de la estrella. */
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
    subtitulo: `Estrella · ETH HYPE XRP MNT LTC · ~$${ASPIRANTE_TECHO_X}`,
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
        valor: `$${ASPIRANTE_TECHO_X}`,
        peso: "fortificado",
      },
    ],
  },
  {
    id: "aprendiz",
    nivel: "2",
    titulo: "Aprendiz",
    subtitulo: `13 Santos despertados · hasta ~$${APRENDIZ_TECHO_FLOTA_SOLDADO_X}`,
    zigzag: "left",
    gapBefore: "3.25rem",
    peso: "firme",
    nodes: [
      {
        id: "apr_santos",
        forma: "cuña",
        escala: "md",
        etiqueta: "Grial Soldado",
        valor: `~$${APRENDIZ_TECHO_FLOTA_SOLDADO_X}`,
        peso: "firme",
      },
    ],
  },
  {
    id: "brujo",
    nivel: "3",
    titulo: "Brujo",
    subtitulo: `Hasta LTC Mariscal · ~$${BRUJO_TECHO_X}`,
    zigzag: "right",
    gapBefore: "4rem",
    peso: "fortificado",
    nodes: [
      {
        id: "bru_ltc_mariscal",
        forma: "agresivo",
        escala: "lg",
        etiqueta: "LTC Mariscal",
        valor: `~$${BRUJO_TECHO_X}`,
        peso: "fortificado",
      },
    ],
  },
  {
    id: "chaman",
    nivel: "4",
    titulo: "Chamán",
    subtitulo: `13 Mariscales · ~$${CHAMAN_TECHO_X}`,
    zigzag: "left",
    gapBefore: "4.5rem",
    peso: "fortificado",
    nodes: [
      {
        id: "cha_grial",
        forma: "rasgado",
        escala: "lg",
        etiqueta: "Grial pleno",
        valor: `~$${CHAMAN_TECHO_X}`,
        peso: "fortificado",
      },
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
  { id: "v_eth", angle: -90, r: 40 },
  { id: "v_hype", angle: -18, r: 46 },
  { id: "v_xrp", angle: 54, r: 42 },
  { id: "v_mnt", angle: 126, r: 48 },
  { id: "v_ltc", angle: 198, r: 44 },
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
  if (nodeId === "asp_corona") return `~$${ASPIRANTE_TECHO_X}`;
  if (nodeId === "apr_santos") return `~$${APRENDIZ_TECHO_FLOTA_SOLDADO_X}`;
  if (nodeId === "bru_ltc_mariscal") return `~$${BRUJO_TECHO_X}`;
  if (nodeId === "cha_grial") return `~$${CHAMAN_TECHO_X}`;
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
 * Progreso vivo desde plan_crecimiento (estado_vivo.igris.plan_crecimiento).
 * Si falta plan, el altar sigue en demo.
 */
export function progressFromPlan(plan) {
  if (!plan || typeof plan !== "object") return null;
  const eq = Math.max(0, Number(plan.equity_usd) || 0);
  const nivel = String(plan.nivel || "ASPIRANTE").toUpperCase();
  const director = plan.pase_director || {};
  const potentialByNivel = {
    ASPIRANTE: "asp_corona",
    APRENDIZ: "apr_santos",
    BRUJO: "bru_ltc_mariscal",
    CHAMAN: "cha_grial",
    CAPITAN: "senor",
    GENERAL: "senor",
    SENOR_SOMBRAS: "senor",
  };
  const potentialNodeId = potentialByNivel[nivel] || "asp_corona";

  let achievedNodeId = "n0_gestacion";
  if (eq >= FASE_CERO_TECHO_X) {
    let sum = 0;
    for (const v of VANGUARDIA_SOLDADOS) {
      sum += v.costoX;
      if (eq >= sum) achievedNodeId = v.id;
      else break;
    }
    if (eq >= ASPIRANTE_TECHO_X) achievedNodeId = "asp_corona";
    if (eq >= APRENDIZ_TECHO_FLOTA_SOLDADO_X) achievedNodeId = "apr_santos";
    if (eq >= BRUJO_TECHO_X) achievedNodeId = "bru_ltc_mariscal";
    if (eq >= CHAMAN_TECHO_X) achievedNodeId = "cha_grial";
  }

  const nLog = Number(director.n_logrados) || 0;
  if (nLog >= 1 && nLog <= 5) {
    const v = VANGUARDIA_SOLDADOS[nLog - 1];
    if (v) achievedNodeId = v.id;
  } else if (nLog >= 5 && eq < APRENDIZ_TECHO_FLOTA_SOLDADO_X) {
    achievedNodeId = "asp_corona";
  }

  const label =
    eq > 0 ? `~$${Math.round(eq)}` : equityLabelForNode(achievedNodeId);
  const foco = director.foco;
  const focoLabel = foco
    ? `${foco.activo || ""} ${foco.grado || ""}`.trim()
    : plan.activo_manto_preferido || plan.activo_semilla || null;

  return {
    potentialNodeId,
    achievedNodeId,
    equityLabel: label,
    live: true,
    nivel,
    activoPreferido: focoLabel,
    rankGate: Boolean(plan.rank_gate),
    marchaId: director.marcha_id || null,
    potenciaN: director.potencia_n ?? null,
    nLogrados: nLog,
  };
}

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
