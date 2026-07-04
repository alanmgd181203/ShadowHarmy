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
