"""
Kaiser — interpretación de snapshots Tank → alertas tipadas y cola de prioridad.
Sin WS ni REST; solo lee lo que Tank ya calculó.
"""
from __future__ import annotations

import time
from typing import Any

import core.config as config


def _severidad_desvio(pct: float) -> str:
    umbral = getattr(config, "DESVIO_ALERTA_PCT", 0.5)
    crit = getattr(config, "KAISER_DESVIO_CRIT_PCT", umbral * 2)
    if pct >= crit:
        return "ALERTA"
    if pct >= umbral:
        return "AVISO"
    return "INFO"


def _alerta(
    tipo: str,
    base: str,
    mensaje: str,
    severidad: str,
    destinatarios: list[str],
    datos: dict | None = None,
) -> dict:
    return {
        "tipo": tipo,
        "base": base,
        "mensaje": mensaje,
        "severidad": severidad,
        "destinatarios": destinatarios,
        "datos": datos or {},
        "id": f"{tipo}:{base}:{hash(mensaje) & 0xFFFFFF}",
    }


def interpretar_desvios_indice(snap: dict) -> list[dict]:
    out: list[dict] = []
    umbral = snap.get("umbral_alerta_pct") or getattr(config, "DESVIO_ALERTA_PCT", 0.5)
    for row in snap.get("filas") or []:
        pct = float(row.get("desvio_pct") or 0)
        if pct < umbral:
            continue
        base = row.get("base", "?")
        huerfana = row.get("huerfana", False)
        sev = _severidad_desvio(pct)
        dest = ["GREED", "BELLION"]
        if huerfana:
            dest.append("BERU")
        sign = row.get("desvio_signed_pct", 0)
        msg = (
            f"Perp {base} desviado {pct:.2f}% vs índice Bybit "
            f"({'huérfana' if huerfana else 'con spot'}) signo={sign:+.2f}%"
        )
        out.append(_alerta("DESVIO_INDICE", base, msg, sev, dest, dict(row)))
    return out


def interpretar_matriz(snap: dict) -> list[dict]:
    out: list[dict] = []
    umbral = getattr(config, "KAISER_MATRIZ_UMBRAL_PCT", 0.25)
    for row in snap.get("filas") or []:
        pct = float(row.get("spread_pct") or 0)
        if pct < umbral:
            continue
        base = row.get("base") or row.get("activo") or "?"
        tipo_sp = row.get("tipo", "spread")
        sev = "ALERTA" if pct >= umbral * 2 else "AVISO"
        luz = "ROJO" if pct >= umbral * 2 else "AMARILLO"
        msg = f"Spread {tipo_sp} {base}: {pct:.3f}%"
        # lineal_vs_inverse → Igris (manto §E); resto → Greed cazador
        if tipo_sp == "lineal_vs_inverse":
            dest = ["IGRIS", "BELLION"]
        else:
            dest = ["GREED", "BELLION"]
        payload = dict(row)
        payload["luz"] = luz
        payload["umbral_pct"] = umbral
        out.append(_alerta("MATRIZ_SPREAD", str(base), msg, sev, dest, payload))
    return out


def luces_matriz(snap: dict, *, top_n: int = 20) -> list[dict]:
    """
    Semáforos 3.7.P1 — luces V/A/R sobre filas de la matriz (solo digest).
    VERDE < umbral · AMARILLO ≥ umbral · ROJO ≥ 2× umbral.
    """
    umbral = float(getattr(config, "KAISER_MATRIZ_UMBRAL_PCT", 0.25) or 0.25)
    filas = list(snap.get("filas") or [])[: max(1, int(top_n))]
    out: list[dict] = []
    for row in filas:
        pct = float(row.get("spread_pct") or 0)
        if pct < umbral:
            luz = "VERDE"
        elif pct < umbral * 2:
            luz = "AMARILLO"
        else:
            luz = "ROJO"
        out.append({
            "base": row.get("base") or row.get("activo") or "?",
            "tipo": row.get("tipo", "spread"),
            "spread_pct": round(pct, 4),
            "luz": luz,
            "umbral_pct": umbral,
            "destinatario": "IGRIS" if row.get("tipo") == "lineal_vs_inverse" else "GREED",
        })
    return out


def _activos_flota_manto() -> list[str]:
    """Activos Inverse∩Linear del diccionario; fallback pentiverso + ETH."""
    import json
    from pathlib import Path

    path = Path(__file__).resolve().parents[1] / "config" / "diccionario_beru_flota_manto.json"
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            lista = (data.get("meta") or {}).get("activos") or []
            if lista:
                return [str(a).upper() for a in lista]
        except Exception:
            pass
    bases = list(getattr(config, "ACTIVOS_PENTIVERSO", []) or [])
    seed = str(getattr(config, "BERU_ACTIVO_SEMILLA", "ETH") or "ETH").upper()
    if seed not in bases:
        bases = [seed] + bases
    return [str(b).upper() for b in bases]


def interpretar_oportunidades_manto(tank, activos: list[str] | None = None) -> list[dict]:
    """Igris de baja — ya no hay semáforo morado de espejo L+S."""
    _ = tank, activos
    return []


def interpretar_panorama(snap: dict) -> list[dict]:
    out: list[dict] = []
    for row in snap.get("filas") or []:
        estado = row.get("estado", "")
        if estado not in ("DESALINEADO", "BINANCE_STALE"):
            continue
        base = row.get("base", "?")
        dg = row.get("desvio_global_pct")
        sev = "ALERTA" if estado == "DESALINEADO" else "AVISO"
        msg = f"Panorama {base}: {estado}"
        if dg is not None:
            msg += f" (desvío global {dg:+.3f}%)"
        out.append(_alerta("PANORAMA_GLOBAL", base, msg, sev, ["GREED", "BELLION"], dict(row)))
    return out


def interpretar_funding(snap: dict) -> list[dict]:
    out: list[dict] = []
    umbral = getattr(config, "KAISER_FUNDING_UMBRAL", 0.0005)
    for row in snap.get("top") or []:
        rate = abs(float(row.get("funding_rate") or 0))
        if rate < umbral:
            continue
        base = row.get("base", "?")
        pct = row.get("funding_pct", rate * 100)
        sev = "ALERTA" if rate >= umbral * 3 else "AVISO"
        msg = f"Funding {base}: {pct:.4f}%"
        out.append(_alerta("FUNDING", base, msg, sev, ["GREED", "BERU", "BELLION"], dict(row)))
    return out


def interpretar_sentidos_rest(snap: dict) -> list[dict]:
    out: list[dict] = []
    for canal, err in (snap.get("errores") or {}).items():
        if not err:
            continue
        msg = f"REST {canal} falló — sentido Tank incompleto"
        out.append(_alerta("SENTIDOS_REST", canal, msg, "INFO", ["BELLION"], {"error": str(err)[:200]}))
    return out


def interpretar_ancla_liquidez(
    tank,
    matriz_snap: dict,
    *,
    pipeline: dict | None = None,
    rastreador=None,
    cola_greed=None,
) -> tuple[list[dict], list[dict], list[dict]]:
    """
    Capa Ancla — oportunidades Greed (max USD, neto ≥ fees).
    Retorna (oportunidades, alertas, abortadas).
    """
    from core import ancla

    filas = matriz_snap.get("filas") or []
    libros = ancla.libros_desde_lider(tank)
    if not libros:
        return [], [], []

    lider = tank._obtener_lider_verde()
    semaforo = lider.estado_foco if lider else "ROJO"
    latencia = lider.latencia_ms if lider else 999.0
    pipeline = pipeline or {}
    pipeline_ms = float(pipeline.get("total_ms") or 500)

    abortadas: list[dict] = []
    if cola_greed is not None:
        abortadas.extend(cola_greed.limpiar_expiradas())

    oportunidades = ancla.escanear_oportunidades_ancla(
        filas,
        libros,
        tank_semaforo=semaforo,
        latencia_ms=latencia,
        pipeline_ms=pipeline_ms,
        rastreador=rastreador,
    )

    # Revalidar cola previa y abortar muertas
    if cola_greed is not None:
        for oid, entry in cola_greed.entries_vivas():
            base = entry.get("base")
            tipo = entry.get("tipo_spread")
            row = next(
                (r for r in filas if str(r.get("base", "")).upper() == base and r.get("tipo") == tipo),
                None,
            )
            op_now = None
            if row:
                op_now = ancla.evaluar_fila_matriz(
                    row, libros,
                    tank_semaforo=semaforo,
                    latencia_ms=latencia,
                    pipeline_ms=pipeline_ms,
                )
            ab = cola_greed.revalidar(
                op_now, oid=oid, pipeline_ms=pipeline_ms, tank_semaforo=semaforo,
            )
            if ab:
                abortadas.append(ab)

    alertas: list[dict] = []
    for op in oportunidades:
        if cola_greed is not None:
            cola_greed.registrar_o_actualizar(op, pipeline_ms)

        max_u = op.get("entrada_maxima_usd", 0)
        spread = op.get("spread_bruto_pct", 0)
        tipo = op.get("tipo_spread", "")
        base = op.get("base", "?")
        neto = op.get("regalo_neto_pct_est")
        fees = op.get("fees_total_pct")
        pip = op.get("pipeline_ms", pipeline_ms)
        msg = (
            f"Ancla {tipo} {base}: spread {spread:.2f}% | "
            f"max ${max_u:.0f} neto {neto:.2f}% (fees {fees:.2f}%) | "
            f"pipe {pip:.0f}ms"
        )
        sev = "ALERTA" if float(neto or 0) >= float(fees or 0) * 1.5 else "AVISO"
        alertas.append(_alerta(
            "OPORTUNIDAD_LIQUIDEZ",
            base,
            msg,
            sev,
            ["GREED", "BELLION"],
            dict(op),
        ))
    return oportunidades, alertas, abortadas


def interpretar_clima_tank(tank) -> list[dict]:
    out: list[dict] = []
    capitan = getattr(tank.capitan_activo, "__name__", "Capitan")
    if tank.tsunami_activado:
        out.append(_alerta(
            "TANK_CLIMA", "GLOBAL",
            f"Tsunami activo — capitán {capitan}",
            "ALERTA", ["BERU", "IGRIS", "GREED", "BELLION"],
            {"capitan": capitan, "tsunami": True},
        ))
    lider = tank._obtener_lider_verde()
    if not lider:
        out.append(_alerta(
            "TANK_CLIMA", "GLOBAL",
            "Sin nodo Tank VERDE/AMARILLO — ojos degradados",
            "AVISO", ["BELLION"],
            {"semaforo": "ROJO"},
        ))
    elif lider.estado_foco == "AMARILLO":
        out.append(_alerta(
            "TANK_CLIMA", "GLOBAL",
            f"Latencia Tank AMARILLO ({lider.latencia_ms:.0f} ms)",
            "INFO", ["BELLION"],
            {"latencia_ms": lider.latencia_ms},
        ))
    return out


def _prioridad(alerta: dict) -> float:
    sev_w = {"ALERTA": 3.0, "AVISO": 2.0, "INFO": 1.0}.get(alerta.get("severidad", ""), 0)
    datos = alerta.get("datos") or {}
    if alerta.get("tipo") == "OPORTUNIDAD_LIQUIDEZ":
        mag = float(datos.get("entrada_maxima_usd") or 0) * float(datos.get("regalo_neto_pct_est") or 0)
        return sev_w * 10000 + mag
    # Morado debe sobrevivir el tope KAISER_MAX_ALERTAS (misma vía que Igris event-driven)
    if False and alerta.get("tipo") == "OPORTUNIDAD_MANTO":
        mag = float(datos.get("spread_pct") or 0)
        return sev_w * 8000 + mag * 100
    mag = abs(float(
        datos.get("desvio_pct")
        or datos.get("spread_pct")
        or datos.get("desvio_global_pct")
        or datos.get("funding_rate", 0) * 10000
        or 0
    ))
    return sev_w * 1000 + mag


def _enriquecer_con_perfil(alerta: dict, perfiles: dict | None) -> None:
    if not perfiles:
        return
    base = str(alerta.get("base", "")).upper()
    perf = (perfiles.get(base) or {}).get("perp_vs_index")
    if not perf:
        return
    plazos = perf.get("plazos", {})
    alerta["perfil"] = {
        "corto": plazos.get("corto", {}).get("etiquetas", []),
        "mediano": plazos.get("mediano", {}).get("etiquetas", []),
        "largo": plazos.get("largo", {}).get("etiquetas", []),
        "resumen": perf.get("etiquetas_resumen", []),
    }
    tags = perf.get("etiquetas_resumen") or []
    if tags:
        alerta["mensaje"] = f"{alerta['mensaje']} | perfil [{', '.join(tags[:5])}]"


def interpretar_tank(
    tank,
    *,
    perfiles: dict | None = None,
    metaverso: dict | None = None,
    pipeline: dict | None = None,
    rastreador=None,
    cola_greed=None,
) -> dict[str, Any]:
    """Digest Kaiser desde Tank en memoria."""
    from core import ancla as ancla_mod

    matriz = tank.snapshot_matriz_spreads()
    desvios = tank.snapshot_desvios_indice()
    panorama = tank.snapshot_panorama_global()
    funding = tank.snapshot_funding()
    sentidos = tank.snapshot_sentidos_extra()

    alertas: list[dict] = []
    alertas.extend(interpretar_desvios_indice(desvios))
    alertas.extend(interpretar_matriz(matriz))
    alertas.extend(interpretar_panorama(panorama))
    alertas.extend(interpretar_funding(funding))
    alertas.extend(interpretar_sentidos_rest(sentidos))
    alertas.extend(interpretar_clima_tank(tank))

    if perfiles:
        for a in alertas:
            if a.get("tipo") in (
                "DESVIO_INDICE", "PANORAMA_GLOBAL", "MATRIZ_SPREAD",
            ):
                _enriquecer_con_perfil(a, perfiles)

    oportunidades_ancla, alertas_ancla, abortadas = interpretar_ancla_liquidez(
        tank, matriz,
        pipeline=pipeline,
        rastreador=rastreador,
        cola_greed=cola_greed,
    )
    alertas.extend(alertas_ancla)

    for ab in abortadas:
        alertas.append(_alerta(
            "OPORTUNIDAD_ABORTADA",
            ab.get("base", "?"),
            f"Abort Greed {ab.get('tipo_spread','?')} {ab.get('base','?')}: {ab.get('abort_motivo','')}",
            "AVISO",
            ["GREED", "BELLION"],
            dict(ab),
        ))

    alertas.sort(key=_prioridad, reverse=True)
    max_a = getattr(config, "KAISER_MAX_ALERTAS", 50)
    alertas = alertas[:max_a]

    cola = [
        {
            "id": a["id"],
            "tipo": a["tipo"],
            "base": a["base"],
            "severidad": a["severidad"],
            "mensaje": a["mensaje"],
            "destinatarios": a["destinatarios"],
        }
        for a in alertas
        if a["severidad"] in ("ALERTA", "AVISO")
    ][: getattr(config, "KAISER_COLA_TOP_N", 20)]

    n_alerta = sum(1 for a in alertas if a["severidad"] == "ALERTA")
    n_aviso = sum(1 for a in alertas if a["severidad"] == "AVISO")

    top_spread = 0.0
    if matriz.get("filas"):
        top_spread = float(matriz["filas"][0].get("spread_pct") or 0)
    top_desvio = 0.0
    if desvios.get("filas"):
        top_desvio = float(desvios["filas"][0].get("desvio_pct") or 0)

    matriz_luces = luces_matriz(matriz)
    n_verde = sum(1 for x in matriz_luces if x.get("luz") == "VERDE")
    n_amarillo = sum(1 for x in matriz_luces if x.get("luz") == "AMARILLO")
    n_rojo = sum(1 for x in matriz_luces if x.get("luz") == "ROJO")

    capitan = getattr(tank.capitan_activo, "__name__", "?")
    lider = tank._obtener_lider_verde()
    semaforo = lider.estado_foco if lider else "ROJO"

    return {
        "ts": time.time(),
        "ts_tank_calc": matriz.get("ts_calc") or desvios.get("ts_calc") or 0,
        "alertas": alertas,
        "cola_prioridad": cola,
        "indicadores": {
            "tank_semaforo": semaforo,
            "capitan_clima": capitan,
            "tsunami": tank.tsunami_activado,
            "alertas_total": len(alertas),
            "alertas_criticas": n_alerta,
            "avisos": n_aviso,
            "top_spread_pct": round(top_spread, 4),
            "top_desvio_pct": round(top_desvio, 4),
            "matriz_luces": matriz_luces,
            "matriz_verde": n_verde,
            "matriz_amarillo": n_amarillo,
            "matriz_rojo": n_rojo,
            "refs_binance": panorama.get("refs_binance", 0),
            "huerfanas_catalogo": panorama.get("bases_huerfanas", 0),
            "ancla_oportunidades": len(oportunidades_ancla),
            "ancla_abortadas": len(abortadas),
            "pipeline_ms": (pipeline or {}).get("total_ms"),
        },
        "resumen": (
            f"{n_alerta} alertas, {n_aviso} avisos | "
            f"Tank {semaforo} | top desvío {top_desvio:.2f}% | top spread {top_spread:.3f}% | "
            f"matriz V{n_verde}/A{n_amarillo}/R{n_rojo}"
        ),
        "perfiles": perfiles or {},
        "metaverso": metaverso or {},
        "ancla": {
            "oportunidades": oportunidades_ancla,
            "count": len(oportunidades_ancla),
            "libros_vivos": len(ancla_mod.libros_desde_lider(tank)),
            "abortadas": abortadas,
            "cola_greed_viva": cola_greed.cola_vivas() if cola_greed else [],
        },
        "pipeline": pipeline or {},
    }


def filtrar_por_destinatario(digest: dict, destinatario: str) -> list[dict]:
    """Slice para un general — uso futuro."""
    return [
        a for a in digest.get("alertas", [])
        if destinatario in (a.get("destinatarios") or [])
    ]
