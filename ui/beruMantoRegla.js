/**
 * Regla del manto (solo velas): el 0, la masa L+S y el grado que ese manto
 * da de comer. Al arrastrar: % vs el 0, jugo = promedio de piernas × %.
 * No mueve a Igris — es metro, no orden.
 */

const FRICCION = {
  SOLDADO: 0.008,
  CAPITAN: 0.004,
  GENERAL: 0.002,
  MARISCAL: 0.001,
};

const GRADOS = ["SOLDADO", "CAPITAN", "GENERAL", "MARISCAL"];

const NOMBRE_GRADO = {
  SOLDADO: "Soldado",
  CAPITAN: "Capitán",
  GENERAL: "General",
  MARISCAL: "Mariscal",
};

export function nombreGrado(grado) {
  const g = String(grado || "").toUpperCase();
  return NOMBRE_GRADO[g] || "00";
}

/** Peldaño de Hoz por cada 0,1: G_min × (0,001 / fricción del rango). */
export function engordePasoUsd(gMin, grado) {
  const fr = FRICCION[String(grado || "").toUpperCase()];
  const g = Number(gMin) || 0;
  if (!(fr > 0) || !(g > 0)) return 0;
  return g * (0.001 / fr);
}

export function precioCeroManto(beruSnap) {
  const g = beruSnap?.grafica || {};
  const c = Number(beruSnap?.centro_manto || g.centro_manto || 0);
  if (c > 0) return c;
  const niveles = Array.isArray(g.niveles) ? g.niveles : [];
  for (const n of niveles) {
    const rol = String(n?.rol || "");
    const p = Number(n?.precio);
    if ((rol === "manto" || rol === "centro") && p > 0) return p;
  }
  return 0;
}

export function mantoDesdeFuentes(symbol, beruSnap, igrisDet) {
  const s = String(symbol || beruSnap?.symbol || igrisDet?.symbol || "").toUpperCase();
  const cero = precioCeroManto(beruSnap) || Number(igrisDet?.global?.entry_avg || 0);
  const usdL = Number(igrisDet?.global?.size_usd_long || igrisDet?.long?.size_usd || 0);
  const usdS = Number(igrisDet?.global?.size_usd_short || igrisDet?.short?.size_usd || 0);
  const usdTotal = (usdL > 0 ? usdL : 0) + (usdS > 0 ? usdS : 0);
  const usdPromedio = usdTotal / 2;
  const gMin = Number(igrisDet?.fase_manto?.G_min || 0);
  const vivo = usdTotal > 1e-9;
  const grado = gradoQueAguanta(usdTotal, gMin);
  return {
    symbol: s,
    cero,
    usdL,
    usdS,
    usdTotal,
    usdPromedio,
    gMin,
    vivo,
    grado,
    gradoNombre: nombreGrado(grado),
  };
}

/**
 * Mayor grado cuyo manto (L+S = 2 × G_min / fricción) cabe en el nocional real.
 * Sin masa o sin peaje → 00 (Igris dormido / aún no da de comer).
 */
export function gradoQueAguanta(usdTotal, gMin) {
  const have = Number(usdTotal) || 0;
  const g = Number(gMin) || 0;
  if (!(have > 0) || !(g > 0)) return "00";
  let out = "00";
  for (const cand of GRADOS) {
    const need = (2 * g) / FRICCION[cand];
    if (have + 1e-9 >= need * 0.995) out = cand;
    else break;
  }
  return out;
}

/**
 * Metro en un precio: fracción vs el 0, dólares del promedio de piernas, moneda.
 */
export function reglaEnPunto(manto, precio) {
  const cero = Number(manto?.cero) || 0;
  const px = Number(precio) || 0;
  if (!(cero > 0) || !(px > 0)) return null;
  const frac = (px - cero) / cero;
  const usd = (Number(manto?.usdPromedio) || 0) * frac;
  const coin = px > 0 ? usd / px : 0;
  return {
    precio: px,
    frac,
    pct: frac * 100,
    usd,
    coin,
  };
}

export function fraseGrado(manto) {
  if (!manto?.vivo) return "Igris dormido · 00";
  if (!(Number(manto.gMin) > 0)) return "Hay manto · peaje de este Santo no llegó";
  if (manto.grado === "00") return "Aún no da de comer a un Soldado";
  return `Da de comer a un ${manto.gradoNombre}`;
}

export function marcaAguaManto(manto, fmtUsd) {
  if (!manto?.vivo) return "Manto · 00";
  const usd = typeof fmtUsd === "function" ? fmtUsd(manto.usdTotal) : String(manto.usdTotal);
  if (manto.grado === "00") return `${usd} · aún no Soldado`;
  return `${usd} · ${manto.gradoNombre}`;
}
