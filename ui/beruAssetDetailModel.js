/**
 * Modelo Sub-Santuario Beru — espejo de estado_vivo.beru_asset_details / beru_flota.
 */
import { engordePasoUsd } from "./beruMantoRegla.js";

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
    centro_manto: 0,
    centro_wake: 0,
    spot_last: null,
    composicion: { caza: 0, negociando: 0, acechando: 0, pct_caza: 0, pct_negociando: 0 },
    red_engorde: null,
    rails_vivos: [],
    rails_disponibles: [],
    barcos: [],
    grafica: { centro_0: 0, centro_manto: 0, centro_wake: 0, spot_last: null, niveles: [], cazas: [] },
    cronica: [],
    nota_pnl: "Sin barcos — legión en reposo.",
  };
}

export function desdeEstadoVivo(symbol, snap) {
  const s = String(symbol || "").toUpperCase();
  const pre = (snap?.beru_asset_details || {})[s];
  if (pre && typeof pre === "object") {
    return enriquecerSnapshot({ ...snapshotCero(s), ...pre, fuente: pre.fuente || "vivo" });
  }
  return snapshotCero(s);
}

const ARMAS_GRADO = new Set(["SOLDADO", "CAPITAN", "GENERAL", "MARISCAL"]);

function gradoCanon(g) {
  const u = String(g || "").toUpperCase();
  return ARMAS_GRADO.has(u) ? u : "";
}

function barcoVivoDe(barcos) {
  const list = Array.isArray(barcos) ? barcos : [];
  for (const b of list) {
    const modo = String(b?.modo || "");
    const est = String(b?.estado || "");
    if (modo === "ACECHANDO" || modo === "CAZA" || est === "ACECHANDO" || est === "CAZANDO") {
      return b;
    }
  }
  return list[0] || null;
}

function nCazasDe(row, det) {
  const corte = tsCorteDe(det);
  let n = 0;
  let hay = false;
  for (const r of det?.cronica || []) {
    if (!esFillCosecha(r)) continue;
    hay = true;
    if (corte > 0 && Number(r.ts) + 1e-6 < corte) continue;
    n += 1;
  }
  if (hay || corte > 0) return n;
  if (row?.n_cazas != null && Number.isFinite(Number(row.n_cazas))) {
    return Math.max(0, Math.floor(Number(row.n_cazas)));
  }
  return 0;
}

function sacoDesdeVacio(det) {
  let best = 0;
  for (const n of det?.grafica?.niveles || []) {
    if (String(n?.rol || "") !== "vacio") continue;
    const m = Number(n?.masa_usd) || 0;
    if (m > best) best = m;
  }
  if (best > 0) return best;
  const vivo = barcoVivoDe(det?.barcos);
  for (const k of ["masa_vacio_arriba_usd", "masa_vacio_abajo_usd"]) {
    const m = Number(vivo?.[k]) || 0;
    if (m > best) best = m;
  }
  return best;
}

function sacoDe(row, det, vivo, oficio) {
  if (String(oficio || "").toLowerCase() === "cerrado") return 0;
  if (oficio === "cazando") {
    return Number(vivo?.masa ?? row?.masa_total_usd) || 0;
  }
  const deVacio = sacoDesdeVacio(det);
  if (deVacio > 0) return deVacio;
  const deFila = Number(row?.saco_usd);
  if (Number.isFinite(deFila) && deFila > 0) return deFila;
  return 0;
}

function oficioDe(row, det, vivo) {
  const raw = String(row?.oficio || "").toLowerCase();
  if (raw === "cazando" || raw === "acechando" || raw === "cerrado") return raw;
  const nCaza = Number(row?.n_caza ?? det?.n_caza) || 0;
  const modo = String(vivo?.modo || "");
  const est = String(vivo?.estado || "");
  if (nCaza > 0 || modo === "CAZA" || est === "CAZANDO") return "cazando";
  return "acechando";
}

const PASO_HOZ = 0.001;
const HOZ_A_VACIO = 0.01;
const RELEVO_OFF = { SOLDADO: 0.009, CAPITAN: 0.005, GENERAL: 0.003, MARISCAL: 0 };

function masaPrometidaSilbato(gMin, grado) {
  const paso = engordePasoUsd(gMin, grado);
  if (!(paso > 0)) return 0;
  return paso * (HOZ_A_VACIO / PASO_HOZ);
}

function cazandoDe(vivo) {
  const modo = String(vivo?.modo || "");
  const est = String(vivo?.estado || "");
  return modo === "CAZA" || est === "CAZANDO";
}

function esRelevoDe(vivo) {
  if (vivo?.es_relevo || vivo?.es_relevo_cazador) return true;
  if ((Number(vivo?.generacion) || 1) > 1) return true;
  return /_R\d+(_|$)/.test(String(vivo?.uid || ""));
}

function idVacioCaza(vivo) {
  return String(vivo?.direccion || "").toUpperCase() === "SHORT" ? "vacio_up" : "vacio_dn";
}

function precioRedGrafica(vivo) {
  for (const k of ["red_precio", "red_relevo_precio"]) {
    const p = Number(vivo?.[k]) || 0;
    if (p > 0) return p;
  }
  const grado = gradoCanon(vivo?.grado);
  if (grado === "MARISCAL") return 0;
  if (!(vivo?.oreja_red || esRelevoDe(vivo))) return 0;
  const ancla = Number(vivo?.ultima_red_precio) || 0;
  const escala = Number(vivo?.centro_manto) || 0;
  let off = Number(vivo?.llamado_red_pct) || 0;
  if (off > 1) off /= 100;
  if (!(off > 0)) off = RELEVO_OFF[grado] || 0;
  if (!(ancla > 0) || !(escala > 0) || !(off > 0)) return 0;
  return String(vivo?.direccion || "").toUpperCase() === "LONG"
    ? ancla - escala * off
    : ancla + escala * off;
}

function tsCorteDe(snap) {
  const t = Number(snap?.ts_wake) || 0;
  if (t > 0) return t;
  const re = /BERU_SEM_[A-Z0-9]+_(\d{16,})$/;
  let best = 0;
  for (const src of [snap?.barcos || [], snap?.cronica || []]) {
    for (const x of src) {
      const m = String(x?.uid || "").match(re);
      if (!m) continue;
      const u = Number(m[1]) / 1e9;
      if (u > best) best = u;
    }
  }
  return best;
}

function esFillCosecha(r) {
  const t = String(r?.tipo || "").toUpperCase();
  if (t === "COSECHA") return true;
  return t.startsWith("COSECHA") && !t.includes("TRAMO");
}

function cazasDeCronica(cronica, tsCorte) {
  const corte = Number(tsCorte) || 0;
  const out = [];
  for (const r of cronica || []) {
    if (r?.tipo && !esFillCosecha(r)) continue;
    const px = Number(r?.precio) || 0;
    const ts = Number(r?.ts) || 0;
    if (!(px > 0) || !(ts > 0)) continue;
    if (corte > 0 && ts + 1e-6 < corte) continue;
    const d = String(r?.direccion || "").toUpperCase();
    const lado = d === "LONG" ? "Buy" : d === "SHORT" ? "Sell" : r?.lado || null;
    out.push({ ts: Math.floor(ts), precio: px, lado });
  }
  return out.slice(-40);
}

function geometriaNiveles(snap, vivo) {
  const g = snap?.grafica && typeof snap.grafica === "object" ? snap.grafica : {};
  // Oficio rango: niveles ya vienen armados (0 / sangre / Red / Oz).
  if (
    String(g.oficio || snap?.oficio || "").toUpperCase() === "RANGO" &&
    Array.isArray(g.niveles) &&
    g.niveles.length
  ) {
    const cero = Number(vivo?.ancla_tramo || vivo?.centro_local || g.centro_0) || 0;
    const tsCorte = tsCorteDe(snap);
    const cazasRaw = Array.isArray(g.cazas) ? g.cazas : [];
    const cazas = (cazasRaw.length ? cazasRaw : cazasDeCronica(snap?.cronica, tsCorte)).filter(
      (c) => !(tsCorte > 0 && Number(c.ts) + 1e-6 < tsCorte),
    );
    const out = { ...g, niveles: g.niveles.slice(), cazas };
    if (cero > 0) {
      out.centro_0 = cero;
      out.centro_wake = cero;
      out.centro_manto = Number(g.centro_manto) || cero;
    }
    return out;
  }
  const niveles = [];
  for (const n of Array.isArray(g.niveles) ? g.niveles : []) {
    const rol = String(n?.rol || "");
    if (rol === "oz" && !vivo?.carta_colgada) continue;
    niveles.push(n);
  }
  const cero = Number(vivo?.ancla_tramo || vivo?.centro_local || vivo?.centro_wake) || 0;
  if (cero > 0) {
    let hayWake = false;
    for (const n of niveles) {
      if (String(n?.rol || "") !== "wake") continue;
      n.precio = cero;
      n.id = n.id || "wake";
      hayWake = true;
    }
    if (!hayWake) niveles.push({ id: "wake", precio: cero, pct: 0, rol: "wake" });
  }
  const vacioPct = Number(vivo?.vacio_pct) || 1.1;
  const relevo = esRelevoDe(vivo);
  const cazando = cazandoDe(vivo);
  const dual = !relevo && !cazando && !(Number(vivo?.oz_precio || vivo?.oz_adan) > 0);
  const dir = String(vivo?.direccion || "").toUpperCase();
  let keepUp = Number(vivo?.vacio_arriba) > 0;
  let keepDn = Number(vivo?.vacio_abajo) > 0;
  if (!dual) {
    if (dir === "SHORT") keepUp = false;
    if (dir === "LONG") keepDn = false;
  }
  if (!keepUp) {
    for (let i = niveles.length - 1; i >= 0; i -= 1) {
      if (String(niveles[i]?.id || "") === "vacio_up") niveles.splice(i, 1);
    }
  }
  if (!keepDn) {
    for (let i = niveles.length - 1; i >= 0; i -= 1) {
      if (String(niveles[i]?.id || "") === "vacio_dn") niveles.splice(i, 1);
    }
  }
  if (keepUp) {
    let hayUp = false;
    for (const n of niveles) {
      if (String(n?.id || "") !== "vacio_up") continue;
      n.precio = Number(vivo.vacio_arriba);
      n.pct = vacioPct;
      hayUp = true;
    }
    if (!hayUp) {
      niveles.push({
        id: "vacio_up",
        precio: Number(vivo.vacio_arriba),
        pct: vacioPct,
        rol: "vacio",
        masa_usd: vivo?.masa_vacio_arriba_usd || null,
      });
    }
  }
  if (keepDn) {
    let hayDn = false;
    for (const n of niveles) {
      if (String(n?.id || "") !== "vacio_dn") continue;
      n.precio = Number(vivo.vacio_abajo);
      n.pct = -vacioPct;
      hayDn = true;
    }
    if (!hayDn) {
      niveles.push({
        id: "vacio_dn",
        precio: Number(vivo.vacio_abajo),
        pct: -vacioPct,
        rol: "vacio",
        masa_usd: vivo?.masa_vacio_abajo_usd || null,
      });
    }
  }
  const manto = Number(vivo?.centro_manto) || 0;
  if (manto > 0 && !niveles.some((n) => String(n?.rol || "") === "manto")) {
    niveles.push({ id: "manto", precio: manto, pct: 0, rol: "manto" });
  }
  const redPx = precioRedGrafica(vivo);
  if (redPx > 0 && !niveles.some((n) => ["red", "red_engorde"].includes(String(n?.rol)))) {
    niveles.push({
      id: "red_relevo",
      precio: redPx,
      pct: null,
      rol: "red",
      uid: vivo?.uid,
      masa_usd: vivo?.masa_red_usd || null,
    });
  }
  const tsCorte = tsCorteDe(snap);
  const cazasRaw = Array.isArray(g.cazas) ? g.cazas : [];
  const cazas = (cazasRaw.length ? cazasRaw : cazasDeCronica(snap?.cronica, tsCorte)).filter(
    (c) => !(tsCorte > 0 && Number(c.ts) + 1e-6 < tsCorte),
  );
  const out = { ...g, niveles, cazas };
  if (cero > 0) {
    out.centro_0 = cero;
    out.centro_wake = cero;
  }
  if (manto > 0) out.centro_manto = manto;
  return out;
}

function masaDeNivel(n, snap, vivo) {
  const ya = Number(n?.masa_usd);
  if (Number.isFinite(ya) && ya > 0) return ya;
  const grado = gradoCanon(vivo?.grado);
  const gMin = Number(snap?.G_min) || 0;
  let teo = masaPrometidaSilbato(gMin, grado);
  if (esRelevoDe(vivo) && !cazandoDe(vivo) && gMin > 0) teo = gMin;
  if (!(teo > 0)) return 0;
  const masaNow = Number(vivo?.masa) || 0;
  const paso = engordePasoUsd(gMin, grado);
  const rol = String(n?.rol || "");
  const id = String(n?.id || "").toLowerCase();
  if (rol === "vacio") {
    if (cazandoDe(vivo) && masaNow > 0) {
      const dir = String(vivo?.direccion || "").toUpperCase();
      const ladoCaza = dir === "SHORT" ? "up" : "dn";
      if (id.includes(ladoCaza)) return masaNow;
    }
    return teo;
  }
  if (rol === "oz") return masaNow > 0 ? masaNow : teo;
  if (rol === "red" || rol === "red_engorde") {
    if (cazandoDe(vivo) && masaNow > 0) return masaNow + paso;
    return teo;
  }
  return 0;
}

function enriquecerSnapshot(snap) {
  const vivo = barcoVivoDe(snap?.barcos);
  const g = geometriaNiveles(snap, vivo);
  const niveles = Array.isArray(g.niveles) ? g.niveles : [];
  return {
    ...snap,
    grafica: {
      ...g,
      niveles: niveles.map((n) => {
        const masa = masaDeNivel(n, snap, vivo);
        return masa > 0 ? { ...n, masa_usd: masa } : { ...n };
      }),
    },
  };
}

function distSilbato(det, vivo, oficio) {
  const spot = Number(det?.spot_last ?? vivo?.spot_last) || 0;
  const escala = Number(det?.centro_manto ?? vivo?.centro_manto) || 0;
  if (!(spot > 0) || !(escala > 0)) return 1e9;
  const roles = oficio === "cazando"
    ? ["oz", "red", "red_engorde", "vacio"]
    : ["vacio", "red", "red_engorde"];
  let best = null;
  const niveles = det?.grafica?.niveles || [];
  for (const n of niveles) {
    if (!roles.includes(String(n?.rol || ""))) continue;
    const px = Number(n?.precio) || 0;
    if (!(px > 0)) continue;
    const d = Math.abs(spot - px) / escala;
    if (best == null || d < best) best = d;
  }
  if (best == null) {
    for (const px of [vivo?.vacio_arriba, vivo?.vacio_abajo]) {
      const p = Number(px) || 0;
      if (!(p > 0)) continue;
      const d = Math.abs(spot - p) / escala;
      if (best == null || d < best) best = d;
    }
  }
  return best == null ? 1e9 : best;
}

function calorBanda(oficio, vivo, dist) {
  if (oficio === "cazando") return 0;
  if (oficio === "cerrado") return 4;
  if (vivo?.es_relevo || esRelevoDe(vivo)) return 1;
  if (dist < 1e8) return 2;
  return 3;
}

function ultimaLecturasDe(det) {
  const cron = det?.cronica || [];
  for (let i = cron.length - 1; i >= 0; i -= 1) {
    if (esFillCosecha(cron[i])) return detalleCosecha(cron[i]);
  }
  return null;
}

/**
 * Flota para el Pergamino.
 * Si hay Beru rango vivo → solo esos Santos activos (hoy HYPE).
 * Si no → flota cazador legacy (con manto).
 */
export function flotaDesdeEstado(snap) {
  const rango = snap?.beru_rango;
  if (rango && Array.isArray(rango.activos) && rango.activos.length) {
    return flotaDesdeRango(snap, rango);
  }
  const f = snap?.beru_flota || {};
  const details = snap?.beru_asset_details || {};
  const legion = Array.isArray(snap?.legion) ? snap.legion : [];
  const crudos = Array.isArray(f.activos) ? f.activos : [];
  const activos = [];
  for (const row of crudos) {
    const act = String(row?.activo || "").toUpperCase();
    if (!act) continue;
    const detRaw = details[act] && typeof details[act] === "object" ? details[act] : {};
    const det = enriquecerSnapshot({ ...snapshotCero(act), ...detRaw, symbol: act });
    const nBarcos = Number(row.n_barcos ?? det.n_barcos) || 0;
    const manto = Number(row.centro_manto ?? det.centro_manto) || 0;
    const oficioPre = String(row?.oficio || "").toLowerCase();
    const cerrado = oficioPre === "cerrado";
    if (!cerrado && (nBarcos <= 0 || !(manto > 0))) continue;
    const vivoDet = barcoVivoDe(det.barcos);
    const vivoLeg = barcoVivoDe(legion.filter((b) => String(b?.activo || "").toUpperCase() === act));
    const vivo = vivoDet || vivoLeg;
    const grado = gradoCanon(row.grado) || gradoCanon(vivo?.grado) || (cerrado ? "MARISCAL" : "");
    if (!grado) continue;
    const oficio = oficioDe(row, det, vivo);
    const dist = cerrado ? null : distSilbato(det, vivo, oficio);
    const calor = calorBanda(oficio, vivo, dist);
    const pasoRow = Number(row.engorde_paso_usd);
    const paso =
      Number.isFinite(pasoRow) && pasoRow > 0
        ? pasoRow
        : engordePasoUsd(row.G_min ?? det.G_min, grado);
    activos.push({
      ...row,
      activo: act,
      n_barcos: nBarcos,
      centro_manto: manto,
      grado,
      oficio,
      engorde_paso_usd: paso,
      n_cazas: nCazasDe(row, det),
      saco_usd: sacoDe(row, det, vivo, oficio),
      dist_silbato: dist,
      calor_banda: calor,
      es_relevo: Boolean(vivo?.es_relevo),
      ultima_lecturas: row.ultima_lecturas || ultimaLecturasDe(det),
    });
  }
  return cerrarFlota(activos, f.semilla || snap?.ticker_base || "ETH");
}

function flotaDesdeRango(snap, rango) {
  const details = {
    ...(snap?.beru_asset_details || {}),
    ...(rango.details || {}),
  };
  const activos = [];
  for (const row of rango.activos || []) {
    const act = String(row?.activo || "").toUpperCase();
    if (!act) continue;
    const detRaw = details[act] && typeof details[act] === "object" ? details[act] : {};
    const det = enriquecerSnapshot({
      ...snapshotCero(act),
      ...detRaw,
      symbol: act,
      oficio: "RANGO",
    });
    const vivo = barcoVivoDe(det.barcos) || {};
    const oficio = String(row.oficio || oficioDe(row, det, vivo) || "acechando").toLowerCase();
    const last = Number(row.last ?? det.spot_last ?? det.last_lineal) || 0;
    const cero = Number(row.cero ?? vivo.centro_local) || 0;
    let dist = 1e9;
    if (last > 0 && cero > 0) {
      for (const n of det.grafica?.niveles || []) {
        const rol = String(n?.rol || "");
        if (!["vacio", "red", "oz"].includes(rol)) continue;
        const px = Number(n?.precio) || 0;
        if (!(px > 0)) continue;
        const d = Math.abs(last - px) / cero;
        if (d < dist) dist = d;
      }
      // Respaldo: sangre del vivo (post-Oz) si la foto aún no trae niveles frescos.
      const sangrePx =
        Number(row.sangre ?? row.sangre_adan ?? vivo.sangre ?? vivo.sangre_adan) || 0;
      if (sangrePx > 0) {
        const d = Math.abs(last - sangrePx) / cero;
        if (d < dist) dist = d;
      }
    }
    activos.push({
      ...row,
      activo: act,
      n_barcos: 1,
      centro_manto: cero,
      grado: "GENERAL",
      oficio,
      engorde_paso_usd: 0,
      n_cazas: Number(row.n_cazas ?? row.cosechas) || 0,
      saco_usd: Number(vivo.masa) || Number(det.G_min) || 10,
      dist_silbato: dist < 1e8 ? dist : null,
      calor_banda: calorBanda(oficio, vivo, dist),
      es_relevo: false,
      mercado: "linear",
      oficio_beru: "RANGO",
      last,
      cero,
      red: Number(row.red) || 0,
      oz: Number(row.oz) || 0,
      sangre_lado: row.sangre_lado || "",
      manos: Boolean(row.manos ?? det.manos),
      ultima_lecturas: null,
    });
  }
  return cerrarFlota(activos, rango.activo_foco || "HYPE", {
    modo: "RANGO",
    latido_vivo: Boolean(rango.latido_vivo),
    ts: rango.ts,
  });
}

function cerrarFlota(activos, semilla, extra = {}) {
  activos.sort((a, b) => {
    const rank = (of) => {
      const o = String(of || "").toLowerCase();
      if (o === "cazando") return 0;
      if (o === "cerrado") return 2;
      return 1;
    };
    const ra = rank(a.oficio);
    const rb = rank(b.oficio);
    if (ra !== rb) return ra - rb;
    const da = a.dist_silbato == null ? 1e9 : Number(a.dist_silbato);
    const db = b.dist_silbato == null ? 1e9 : Number(b.dist_silbato);
    if (da !== db) return da - db;
    return String(a.activo).localeCompare(String(b.activo));
  });
  const conteo = { MARISCAL: 0, GENERAL: 0, CAPITAN: 0, SOLDADO: 0 };
  for (const a of activos) {
    if (conteo[a.grado] != null) conteo[a.grado] += 1;
  }
  return {
    semilla,
    n_activos: activos.length,
    n_barcos_total: activos.reduce((s, a) => s + (Number(a.n_barcos) || 0), 0),
    n_santos: activos.length,
    conteo_grados: conteo,
    activos,
    ...extra,
  };
}

/** Une estado_vivo + foto rango (solo activos del oficio nuevo). */
export async function cargarSnapBeru() {
  const out = {};
  try {
    const res = await fetch(`/data/estado_vivo.json?t=${Date.now()}`, { cache: "no-store" });
    if (res.ok) Object.assign(out, await res.json());
  } catch {
    /* silencio */
  }
  try {
    const res = await fetch(`/data/beru/rango_vivo.json?t=${Date.now()}`, { cache: "no-store" });
    if (res.ok) {
      const r = await res.json();
      out.beru_rango = r;
      if (Array.isArray(r?.activos) && r.activos.length) {
        out.beru_flota = {
          activos: r.activos,
          semilla: r.activo_foco || "HYPE",
        };
        out.beru_asset_details = {
          ...(out.beru_asset_details || {}),
          ...(r.details || {}),
        };
      }
    }
  } catch {
    /* silencio */
  }
  return out;
}

export function detalleCosecha(ev) {
  if (!ev || typeof ev !== "object") return "";
  const metro = ev.beneficio_metro_pct != null ? Number(ev.beneficio_metro_pct) : null;
  const hoz = ev.beneficio_hoz_pct != null ? Number(ev.beneficio_hoz_pct) : null;
  const legacy = ev.beneficio_pct != null ? Number(ev.beneficio_pct) : null;
  const m = metro != null && Number.isFinite(metro) ? metro : (legacy != null && Number.isFinite(legacy) ? legacy : null);
  const sello = (x) => `${x >= 0 ? "Botín" : "Merma"} ${Number(x).toFixed(2)}%`;
  if (m != null && hoz != null && Number.isFinite(hoz)) {
    return `metro ${sello(m)} · Hoz ${sello(hoz)}`;
  }
  if (ev.detalle_lecturas) return String(ev.detalle_lecturas);
  if (m != null) return `metro ${sello(m)}`;
  return String(ev.detalle || ev.precio || ev.ts || "");
}

export function fmtDistSilbato(dist, oficio) {
  const of = String(oficio || "").toLowerCase();
  if (of === "cazando" || of === "cerrado") return "";
  const d = Number(dist);
  if (!Number.isFinite(d) || d >= 1e8) return "—";
  const pct = d * 100;
  if (pct < 0.1) return `${pct.toFixed(2)}%`;
  return `${pct.toFixed(1)}%`;
}

export function fmtUsd(n) {
  if (n == null || Number.isNaN(Number(n))) return "—";
  return `$${Number(n).toFixed(2)}`;
}

export function fmtPct(n) {
  if (n == null || Number.isNaN(Number(n))) return "—";
  return `${Number(n).toFixed(2)}%`;
}

export function decimalesPrecio(n) {
  const p = Math.abs(Number(n));
  if (!(p > 0) || Number.isNaN(p)) return 2;
  if (p >= 1000) return 2;
  if (p >= 100) return 3;
  if (p >= 1) return 4;
  if (p >= 0.1) return 5;
  if (p >= 0.01) return 6;
  if (p >= 0.001) return 7;
  return 8;
}

export function fmtNum(n, d) {
  if (n == null || Number.isNaN(Number(n))) return "—";
  const dig = d == null ? decimalesPrecio(n) : d;
  return Number(n).toFixed(dig);
}
