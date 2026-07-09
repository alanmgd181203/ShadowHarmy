"""
Panel visual del Shadow Army — Streamlit
Corre aparte: streamlit run panel.py
Lee data/estado_vivo.json que arise.py actualiza cada segundo.
"""
import json
import time
import os
import streamlit as st

st.set_page_config(
    page_title="Shadow Army — Panel de Control",
    page_icon="🌑",
    layout="wide",
)

RUTA_ESTADO = "data/estado_vivo.json"
RUTA_HISTORIAL = "data/historial_hierro.jsonl"


def cargar_estado():
    if not os.path.exists(RUTA_ESTADO):
        return None
    try:
        with open(RUTA_ESTADO, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return None


def cargar_ultimos_logs(n=20):
    if not os.path.exists(RUTA_HISTORIAL):
        return []
    try:
        with open(RUTA_HISTORIAL, "r", encoding="utf-8") as f:
            lineas = f.readlines()
        return lineas[-n:]
    except IOError:
        return []


def main():
    st.title("🌑 Shadow Army — Lilit de Hierro")

    estado = cargar_estado()

    if estado is None:
        st.warning("Esperando a que el ejército despierte... (`python arise.py`)")
        st.info("El panel se actualiza automáticamente cuando `data/estado_vivo.json` aparezca.")
        time.sleep(2)
        st.rerun()
        return

    # --- HEADER ---
    ts = estado.get("ts", 0)
    edad = time.time() - ts
    sistema = estado.get("sistema", "?")

    if edad > 10:
        st.error(f"⚠️ Datos desactualizados ({edad:.0f}s sin actualizar). ¿El ejército sigue corriendo?")
    else:
        st.success(f"✅ {sistema} — datos de hace {edad:.1f}s")

    # --- MÉTRICAS PRINCIPALES ---
    col1, col2, col3, col4 = st.columns(4)

    margen = estado.get("margen_ocupado", 0)
    col1.metric("Margen usado", f"{margen:.1f}%")

    masa_aut = estado.get("masa_autorizada", 0)
    col2.metric("Masa autorizada", f"{masa_aut:.4f} LTC")

    masa_bruta = estado.get("masa_bruta", 0)
    col3.metric("Masa bruta", f"{masa_bruta:.4f} LTC")

    ciclos = estado.get("ciclos_consumados", 0)
    col4.metric("Ciclos completados", ciclos)

    bc = estado.get("beru_capital", {})
    if bc:
        st.subheader("⚔️ Beru — ProtoBeru / capital manto")
        sem = bc.get("semilla", {})
        tier_act = bc.get("tier_activo", "?")
        modo = bc.get("modo_combate_default", "NEGOCIADOR")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Semilla", bc.get("activo_semilla", "?"))
        c2.metric("Tier activo", tier_act)
        c3.metric("Margen manto (tier)", f"${sem.get('margen_manto_tier_usd', 0):.0f}")
        c4.metric("Equity mín", f"${sem.get('equity_min_usd', 0):.0f}")
        caps = bc.get("capitanes", {})
        st.caption(
            f"Modo default {modo} | Objetivo ${bc.get('pnl_objetivo_1pct_usd', 50)}/1% por pierna | "
            f"Vacío Ansiedad {caps.get('ansiedad_vacio_pct', 1.2)}% / Normal {caps.get('normal_vacio_pct', 1.6)}%"
        )
        tiers = bc.get("tiers") or []
        if tiers:
            st.caption("Pasos oz/red por tier (% del centro)")
            st.dataframe(
                [
                    {
                        "Tier": t.get("id"),
                        "Nombre": t.get("nombre"),
                        "Caza oz": t.get("caza_oz_pct"),
                        "Caza red": t.get("caza_red_pct"),
                        "Neg oz": t.get("negociador_oz_pct"),
                        "Neg red": t.get("negociador_red_pct"),
                        "Manto ÷": t.get("escala_manto"),
                    }
                    for t in tiers
                ],
                use_container_width=True,
                hide_index=True,
            )
        flota = bc.get("flota_por_tier") or []
        if flota:
            st.dataframe(
                [
                    {
                        "Tier": r.get("tier"),
                        "Activo": r.get("activo"),
                        "Lev prom": r.get("lev_promedio"),
                        "Manto $": r.get("margen_manto_tier_usd"),
                        "Pleno $": r.get("margen_manto_pleno_usd"),
                        "Equity min $": r.get("equity_min_usd"),
                    }
                    for r in flota
                ],
                use_container_width=True,
                hide_index=True,
            )

    # --- DELTA Y BANDA ---
    st.subheader("⚖️ Delta L/S y Banda Adaptativa")

    delta_ratio = estado.get("delta_ratio", 0.5)
    banda_min = estado.get("banda_min", 0.45)
    banda_max = estado.get("banda_max", 0.55)
    peso_l = estado.get("peso_long", 0)
    peso_s = estado.get("peso_short", 0)

    col_d1, col_d2, col_d3 = st.columns(3)
    col_d1.metric("LONG", f"{peso_l:.4f} LTC")
    col_d2.metric("SHORT", f"{peso_s:.4f} LTC")
    col_d3.metric("Ratio LONG", f"{delta_ratio*100:.1f}%")

    # Barra visual del delta
    progreso_normalizado = max(0.0, min(1.0, (delta_ratio - banda_min) / max(banda_max - banda_min, 0.001)))
    st.progress(progreso_normalizado)
    st.caption(f"Banda: {banda_min*100:.1f}% — {banda_max*100:.1f}% | Posición: {delta_ratio*100:.1f}%")

    # --- IGRIS — MANTO ---
    igris = estado.get("igris", {})
    if igris:
        st.subheader("🛡️ Igris — escudo del manto")
        fase = igris.get("fase_margen", "?")
        accion = igris.get("accion_heuristica", "VIGILAR")
        umb = igris.get("umbrales", {})
        i1, i2, i3, i4 = st.columns(4)
        i1.metric("Fase margen", fase)
        i2.metric("Acción heurística", accion)
        i3.metric("Delta en banda", "✅" if igris.get("delta_en_banda") else "⚠️")
        i4.metric("Frentes manto", len(igris.get("frentes_manto", [])))
        st.caption(
            f"Umbrales: expansion <{umb.get('expansion_max', 80)}% | "
            f"piso {umb.get('piso_ideal', 85)}% | objetivo {umb.get('objetivo_margen', 90)}% | "
            f"espejos >{umb.get('limpieza_desde', 93)}% | ley marcial >={umb.get('ley_marcial_desde', 95)}%"
        )
        extremos = igris.get("funding_extremo") or []
        if extremos:
            st.caption("Funding extremo (vigilancia pasiva — sin maniobra auto): " + "; ".join(
                f"{e.get('base')}: {e.get('mensaje', '')}" for e in extremos[:5]
            ))
        toques = igris.get("toques_greed_manto") or {}
        activos = toques.get("activos") or []
        if activos:
            st.caption(
                "Toques Greed en manto (pausa rebalanceo Igris): "
                + "; ".join(f"{t.get('frente')} ({t.get('edad_s')}s)" for t in activos[:5])
            )
        basis_holds = estado.get("greed_basis_abiertos") or []
        if basis_holds:
            st.caption(
                "Greed basis holds (manto temporal): "
                + "; ".join(
                    f"{h.get('base')} {h.get('tipo')} ${h.get('notional_usd', 0):.0f} "
                    f"spread_ent {h.get('spread_entrada_pct', 0):.2f}% ({h.get('edad_s', 0)}s)"
                    for h in basis_holds[:5]
                )
            )
        promedios = igris.get("promedios_pierna") or []
        if promedios:
            st.caption(
                "Promedios Igris §E: "
                + "; ".join(
                    f"{p.get('frente')} "
                    + (f"L@{p.get('precio_medio_long')}" if p.get("precio_medio_long") else "")
                    + (f" S@{p.get('precio_medio_short')}" if p.get("precio_medio_short") else "")
                    for p in promedios[:4]
                )
            )
        plan = igris.get("plan_crecimiento") or {}
        if plan.get("nivel"):
            st.caption(
                f"Plan crecimiento: {plan.get('nivel')} · "
                f"peces máx {plan.get('peces_max')} · tier {plan.get('tier_default')} · "
                f"Greed {plan.get('greed_modo')} · reserva ${plan.get('reserva_usd', 0):.0f}"
            )

    # --- TRINIDAD (multiflota sentidos) ---
    tri = estado.get("trinidad", {})
    if tri:
        st.subheader("👁️ Trinidad — multiflota (manto + spot USDT)")
        c1, c2, c3 = st.columns(3)
        c1.metric("Activos", tri.get("activos", 0))
        c2.metric("Precios vivos", f"{tri.get('frentes_vivos', 0)}/{tri.get('frentes_esperados', '?')}")
        c3.metric("Muros vivos", f"{tri.get('muros_vivos', 0)}/{tri.get('frentes_esperados', '?')}")
        st.caption("Inverse + USDT lineal + spot USDT por activo (mainnet).")

    usdc = estado.get("usdc_spot", {})
    if usdc:
        st.subheader("💵 Spot USDC — permitidos Bybit")
        u1, u2, u3 = st.columns(3)
        u1.metric("Pares USDC", usdc.get("activos", 0))
        u2.metric("Precios vivos", f"{usdc.get('frentes_vivos', 0)}/{usdc.get('frentes_esperados', '?')}")
        u3.metric("Muros vivos", f"{usdc.get('muros_vivos', 0)}/{usdc.get('frentes_esperados', '?')}")

    usde = estado.get("usde", {})
    if usde:
        st.subheader("🪙 USDE — 7 pares (spot + linear)")
        e1, e2, e3 = st.columns(3)
        e1.metric("Pares USDE", usde.get("pares", 0))
        e2.metric("Precios vivos", f"{usde.get('frentes_vivos', 0)}/{usde.get('frentes_esperados', 7)}")
        e3.metric("Muros vivos", f"{usde.get('muros_vivos', 0)}/{usde.get('frentes_esperados', 7)}")
        st.caption("Solo sentidos Tank — arbitraje estable pendiente.")

    usd1 = estado.get("usd1", {})
    if usd1:
        st.subheader("🪙 USD1 — 6 pares (spot + linear)")
        d1, d2, d3 = st.columns(3)
        d1.metric("Pares USD1", usd1.get("pares", 0))
        d2.metric("Precios vivos", f"{usd1.get('frentes_vivos', 0)}/{usd1.get('frentes_esperados', 6)}")
        d3.metric("Muros vivos", f"{usd1.get('muros_vivos', 0)}/{usd1.get('frentes_esperados', 6)}")
        st.caption("WLFI/BitGo stable — solo sentidos; estrategia después.")

    mnt_spot = estado.get("mnt_spot", {})
    if mnt_spot:
        st.subheader("🔶 MNT spot — ventanilla + token")
        m1, m2, m3 = st.columns(3)
        m1.metric("Pares MNT", mnt_spot.get("pares", 0))
        m2.metric("Precios vivos", f"{mnt_spot.get('frentes_vivos', 0)}/{mnt_spot.get('frentes_esperados', '?')}")
        m3.metric("Muros vivos", f"{mnt_spot.get('muros_vivos', 0)}/{mnt_spot.get('frentes_esperados', '?')}")
        st.caption("Alt/MNT + MNT/* — solo sentidos; cruce guerrillero después.")

    spot_all = estado.get("spot_all", {})
    if spot_all:
        st.subheader("🌐 Spot Bybit — mapa completo")
        s1, s2, s3 = st.columns(3)
        s1.metric("Pares spot", spot_all.get("pares", 0))
        s2.metric("Precios vivos", f"{spot_all.get('frentes_vivos', 0)}/{spot_all.get('frentes_esperados', '?')}")
        s3.metric("Muros vivos", f"{spot_all.get('muros_vivos', 0)}/{spot_all.get('frentes_esperados', '?')}")
        st.caption("EUR, BRL, MNT, USDT, USDC… — solo sentidos; jerarquía Greed después.")

    linear_perp = estado.get("linear_perp", {})
    if linear_perp:
        st.subheader("📈 Perpetuos lineales — mapa completo")
        l1, l2, l3 = st.columns(3)
        l1.metric("Perps USDT/USDC", linear_perp.get("pares", 0))
        l2.metric("Precios vivos", f"{linear_perp.get('frentes_vivos', 0)}/{linear_perp.get('frentes_esperados', '?')}")
        l3.metric("Muros vivos", f"{linear_perp.get('muros_vivos', 0)}/{linear_perp.get('frentes_esperados', '?')}")

    inverse_perp = estado.get("inverse_perp", {})
    if inverse_perp:
        st.subheader("📉 Perpetuos inverse — manto")
        i1, i2, i3 = st.columns(3)
        i1.metric("Perps inverse", inverse_perp.get("pares", 0))
        i2.metric("Precios vivos", f"{inverse_perp.get('frentes_vivos', 0)}/{inverse_perp.get('frentes_esperados', '?')}")
        i3.metric("Muros vivos", f"{inverse_perp.get('muros_vivos', 0)}/{inverse_perp.get('frentes_esperados', '?')}")

    linear_futures = estado.get("linear_futures", {})
    if linear_futures:
        st.subheader("📅 Futuros lineales — dated / trimestrales")
        f1, f2, f3 = st.columns(3)
        f1.metric("Contratos", linear_futures.get("pares", 0))
        f2.metric("Precios vivos", f"{linear_futures.get('frentes_vivos', 0)}/{linear_futures.get('frentes_esperados', '?')}")
        f3.metric("Muros vivos", f"{linear_futures.get('muros_vivos', 0)}/{linear_futures.get('frentes_esperados', '?')}")
        st.caption("Capa Líderes Igris — basis vs perp; estrategia después.")

    matriz = estado.get("matriz_spreads", {})
    kaiser = estado.get("kaiser", {})
    if kaiser.get("alertas") is not None:
        st.subheader("🐉 Kaiser — vocero interno (interpretación Tank)")
        ind = kaiser.get("indicadores", {})
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Alertas críticas", ind.get("alertas_criticas", 0))
        k2.metric("Avisos", ind.get("avisos", 0))
        k3.metric("Tank semáforo", ind.get("tank_semaforo", "?"))
        k4.metric("Capitán clima", ind.get("capitan_clima", "?"))
        if kaiser.get("resumen"):
            st.caption(kaiser["resumen"])
        if ind.get("pipeline_ms") is not None:
            st.caption(
                f"Pipeline ~{ind.get('pipeline_ms'):.0f} ms | "
                f"Ancla: {ind.get('ancla_oportunidades', 0)} vivas, "
                f"{ind.get('ancla_abortadas', 0)} abortadas"
            )
        cola = kaiser.get("cola_prioridad", [])
        if cola:
            import pandas as pd
            st.markdown("**Cola prioridad (para generales)**")
            st.dataframe(pd.DataFrame(cola), use_container_width=True, hide_index=True)
        alertas = kaiser.get("alertas", [])[:25]
        if alertas:
            import pandas as pd
            st.markdown("**Alertas interpretadas (muestra)**")
            st.dataframe(
                pd.DataFrame([{
                    "severidad": a.get("severidad"),
                    "tipo": a.get("tipo"),
                    "base": a.get("base"),
                    "mensaje": a.get("mensaje"),
                    "para": ",".join(a.get("destinatarios") or []),
                } for a in alertas]),
                use_container_width=True,
                hide_index=True,
            )
        st.caption("Kaiser traduce Tank — Beru/Greed/Igris consumirán digest; aún no disparan.")

        perfiles = kaiser.get("perfiles") or {}
        if perfiles:
            import pandas as pd
            st.markdown("**Perfiles multietiqueta (3d / 1m / 1a)**")
            filas_p = []
            for base, edges in list(perfiles.items())[:12]:
                p = edges.get("perp_vs_index") or {}
                pl = p.get("plazos") or {}
                filas_p.append({
                    "base": base,
                    "corto": ", ".join(pl.get("corto", {}).get("etiquetas", [])),
                    "mediano": ", ".join(pl.get("mediano", {}).get("etiquetas", [])),
                    "largo": ", ".join(pl.get("largo", {}).get("etiquetas", [])),
                    "resumen": ", ".join(p.get("etiquetas_resumen", [])),
                })
            if filas_p:
                st.dataframe(pd.DataFrame(filas_p), use_container_width=True, hide_index=True)

        mv = kaiser.get("metaverso") or {}
        ancla_d = kaiser.get("ancla") or {}
        if ancla_d.get("oportunidades"):
            import pandas as pd
            st.markdown("**⚓ Ancla — liquidez real (orderbook, sin perfiles)**")
            st.caption(
                f"Libros vivos: {ancla_d.get('libros_vivos', 0)} | "
                "max = muro | neto ≥ fees | Greed decide tamaño"
            )
            filas_a = []
            for op in ancla_d.get("oportunidades", [])[:12]:
                filas_a.append({
                    "base": op.get("base"),
                    "tipo": op.get("tipo_spread"),
                    "spread%": op.get("spread_bruto_pct"),
                    "max USD": op.get("entrada_maxima_usd"),
                    "neto%": op.get("regalo_neto_pct_est"),
                    "fees%": op.get("fees_total_pct"),
                    "pipe ms": op.get("pipeline_ms"),
                })
            if filas_a:
                st.dataframe(pd.DataFrame(filas_a), use_container_width=True, hide_index=True)
            aborts = ancla_d.get("abortadas") or []
            if aborts:
                st.caption(f"Abortadas Greed: {len(aborts)}")

        if mv:
            import pandas as pd
            st.markdown("**Metaverso — rutas (slippage Ancla si hay libro, si no estimado)**")
            filas_r = []
            for base, data in list(mv.items())[:8]:
                ruta = data.get("ruta_idonea") or {}
                if ruta.get("ruta_id"):
                    filas_r.append({
                        "base": base,
                        "ruta": ruta.get("nombre", ruta.get("ruta_id")),
                        "neto_pct": ruta.get("regalo_neto_pct"),
                        "score": ruta.get("score_total"),
                        "etiquetas": ", ".join(ruta.get("etiquetas_ruta") or [])[:80],
                    })
                elif ruta.get("arista_directa"):
                    ad = ruta["arista_directa"]
                    filas_r.append({
                        "base": base,
                        "ruta": ad.get("tipo", "arista"),
                        "neto_pct": ad.get("regalo_neto_pct"),
                        "score": ad.get("score_total"),
                        "etiquetas": ", ".join(ad.get("etiquetas_arista") or [])[:80],
                    })
            if filas_r:
                st.dataframe(pd.DataFrame(filas_r), use_container_width=True, hide_index=True)

    if matriz:
        st.subheader("⚡ Matriz spreads — raw Tank")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Filas top", matriz.get("top_n", 0))
        m2.metric("Funding vivos", matriz.get("funding_vivos", 0))
        m3.metric("Índice vivos", matriz.get("index_vivos", 0))
        filas = matriz.get("filas", [])
        if filas:
            import pandas as pd
            st.dataframe(pd.DataFrame(filas), use_container_width=True, hide_index=True)
        st.caption("Calculado desde precios WS — lineal↔inverso, spot↔perp, basis, USDT↔USDC.")

    desvios = estado.get("desvios_indice", {})
    if desvios.get("filas"):
        st.subheader("📐 Desvío perp vs índice (Bybit local)")
        d1, d2, d3 = st.columns(3)
        d1.metric("Filas top", desvios.get("top_n", 0))
        d2.metric("Perps con índice", desvios.get("perps_con_indice", 0))
        d3.metric("Umbral alerta %", desvios.get("umbral_alerta_pct", 0))
        import pandas as pd
        st.dataframe(pd.DataFrame(desvios["filas"]), use_container_width=True, hide_index=True)
        st.caption("Fase 1 — desvío mark/last vs indexPrice en el mismo exchange.")

    panorama = estado.get("panorama_global", {})
    if panorama.get("filas"):
        st.subheader("🌐 Panorama global — Bybit vs Binance (perps huérfanos)")
        p1, p2, p3 = st.columns(3)
        p1.metric("Filas", len(panorama.get("filas", [])))
        p2.metric("Bases huérfanas", panorama.get("bases_huerfanas", 0))
        p3.metric("Refs Binance", panorama.get("refs_binance", 0))
        import pandas as pd
        st.dataframe(pd.DataFrame(panorama["filas"]), use_container_width=True, hide_index=True)
        st.caption("Fase 2 — perp sin spot Bybit; referencia spot Binance si el WS está vivo.")

    funding = estado.get("funding", {})
    if funding.get("vivos", 0) > 0:
        st.subheader("💸 Funding rate — presente (perps WS)")
        f1, _ = st.columns(2)
        f1.metric("Símbolos con funding", funding.get("vivos", 0))
        top_f = funding.get("top", [])
        if top_f:
            import pandas as pd
            st.dataframe(pd.DataFrame(top_f), use_container_width=True, hide_index=True)

    sentidos = estado.get("sentidos_extra", {})
    if sentidos:
        st.subheader("🔭 Sentidos extra — Spread / Alpha / Convert")
        sp = sentidos.get("spread_producto", {})
        al = sentidos.get("alpha", {})
        cv = sentidos.get("convert", {})
        e1, e2, e3 = st.columns(3)
        e1.metric("Spread producto", f"{sp.get('vivos', 0)}/{sp.get('instrumentos', 0)}")
        e2.metric("Alpha tokens", al.get("tokens", 0))
        e3.metric("Convert pares", cv.get("pares", 0))
        cq = sentidos.get("convert_quotes", {})
        if cq.get("filas", 0) > 0:
            st.metric("Convert quotes (muestra)", cq.get("filas", 0))
            if cq.get("muestra"):
                import pandas as pd
                st.dataframe(pd.DataFrame(cq["muestra"]), use_container_width=True, hide_index=True)
        errs = sentidos.get("errores", {})
        if errs:
            st.warning(f"Errores REST: {errs}")
        if sp.get("top"):
            import pandas as pd
            st.markdown("**Spread Trading Bybit (muestra)**")
            st.dataframe(pd.DataFrame(sp["top"]), use_container_width=True, hide_index=True)
        if al.get("muestra"):
            import pandas as pd
            st.markdown("**Alpha (muestra)**")
            st.dataframe(pd.DataFrame(al["muestra"]), use_container_width=True, hide_index=True)
        st.caption("Solo ojos — estrategia Greed/Igris después.")

    inverse_futures = estado.get("inverse_futures", {})
    if inverse_futures:
        st.subheader("📅 Futuros inverse — dated")
        g1, g2, g3 = st.columns(3)
        g1.metric("Contratos", inverse_futures.get("pares", 0))
        g2.metric("Precios vivos", f"{inverse_futures.get('frentes_vivos', 0)}/{inverse_futures.get('frentes_esperados', '?')}")
        g3.metric("Muros vivos", f"{inverse_futures.get('muros_vivos', 0)}/{inverse_futures.get('frentes_esperados', '?')}")

    # --- PENTIVERSO (5 MARES × LTC + BTC) ---
    st.subheader("🌊 Pentiverso — LTC + BTC")

    pentiverso = estado.get("pentiverso", {})
    activos = estado.get("activos_pentiverso", ["LTC", "BTC"])
    ticker_ref = estado.get("ticker_base", "?")
    st.caption(f"Referencia operativa Beru/manos: **{ticker_ref}** | Ojos: mainnet | Sim: {estado.get('sistema', '')}")

    if pentiverso:
        import pandas as pd
        for asset in activos:
            st.markdown(f"**{asset}**")
            filas_p = []
            for frente, d in pentiverso.items():
                if d.get("activo") != asset and not frente.startswith(asset):
                    continue
                precio = d.get("precio", 0)
                filas_p.append({
                    "Frente": frente,
                    "Precio": f"{precio:.4f}" if precio > 0 else "—",
                    "Muro BID": f"{d.get('muro_bid', 0):.2f}",
                    "Muro ASK": f"{d.get('muro_ask', 0):.2f}",
                    "Activo": "✅" if precio > 0 else "⏳",
                    "Nota": "reflejo spot" if d.get("reflejo_spot") else "",
                })
            if filas_p:
                st.dataframe(pd.DataFrame(filas_p), use_container_width=True, hide_index=True)
        activos_vivos = sum(1 for d in pentiverso.values() if d.get("precio", 0) > 0)
        st.caption(f"Mares con precio vivo: {activos_vivos}/{len(pentiverso)}")
    else:
        st.info("Esperando datos del Tank...")

    # --- PESOS POR FRENTE ---
    st.subheader("🌊 Distribución por Frente")

    pesos = estado.get("pesos_por_frente", {})
    if pesos:
        import pandas as pd
        filas = []
        for frente, p in pesos.items():
            total_f = p["long"] + p["short"]
            ratio_f = (p["long"] / total_f * 100) if total_f > 0 else 50.0
            filas.append({
                "Frente": frente,
                "LONG": f"{p['long']:.4f}",
                "SHORT": f"{p['short']:.4f}",
                "Ratio L%": f"{ratio_f:.1f}%",
            })
        st.dataframe(pd.DataFrame(filas), use_container_width=True, hide_index=True)
    else:
        st.info("Sin posiciones abiertas todavía.")

    # --- LEGIÓN DE BERU ---
    st.subheader("⚔️ Legión de Beru")

    legion = estado.get("legion", [])
    if legion:
        import pandas as pd
        filas_l = []
        for b in legion:
            filas_l.append({
                "UID": b["uid"][:16],
                "Estado": b["estado"],
                "Dir": b["direccion"],
                "Centro": f"{b['centro']:.2f}",
                "Masa": f"{b['masa']:.4f}",
                "Ganancia máx": f"{b['max_favor']*100:.2f}%",
                "Gen": b["generacion"],
                "Super": "⭐" if b["es_super"] else "",
            })
        st.dataframe(pd.DataFrame(filas_l), use_container_width=True, hide_index=True)
    else:
        st.info("Legión vacía — esperando primera semilla.")

    # --- LOG RECIENTE ---
    st.subheader("📜 Crónica de Bellion (últimas acciones)")

    logs = cargar_ultimos_logs(15)
    if logs:
        log_text = "".join(logs)
        st.code(log_text, language="text")
    else:
        st.info("Sin registros todavía.")

    # --- AUTO-REFRESH ---
    time.sleep(1.5)
    st.rerun()


if __name__ == "__main__":
    main()
