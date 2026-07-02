import os
import time
from collections import Counter
import core.config as config

class PanelDeControl:
    def __init__(self, tusk, beru_gen, igris):
        self.tusk = tusk
        self.beru = beru_gen
        self.igris = igris
        self.inicio_sesion = time.time()

    def refrescar(self):
        vuelo = time.strftime("%H:%M:%S", time.gmtime(time.time() - self.inicio_sesion))
        print(f"--- 💎 {config.SISTEMA_NOMBRE} | SESIÓN: {vuelo} ---")
        self._mostrar_diagnostico_hidra()
        self._mostrar_altar_greed()
        self._mostrar_manto_riesgo()
        self._mostrar_distribucion_espejos()
        self._mostrar_estado_legion_deep()
        print("\n" + "═"*45)

    def _mostrar_diagnostico_hidra(self):
        tank = self.beru.tank
        print(f"\n[ TELEMETRÍA DE TANK ]")
        lider = tank._obtener_lider_verde()
        id_lider = lider.node_id if lider else "NINGUNO"
        for nodo in tank.nodos:
            marca = ">>" if nodo.node_id == id_lider else "  "
            print(f" {marca} NODO {nodo.node_id:02}: {nodo.estado_foco:10} | {nodo.latencia_ms:>5.2f}ms | P: {nodo.p_usdt_lineal:.2f}")

    def _mostrar_altar_greed(self):
        greed = self.beru.greed
        print(f"\n[ ALTAR DE GREED ]")
        print(f"  ÓRDENES EN COLA: {greed.altar.qsize()} | FILTRO DEDUPE: {len(greed.dedupe_set)}")

    # === [SUBTEMA CORREGIDO: MANTO RIESGO Y OXÍGENO] ===
    def _mostrar_manto_riesgo(self):
        # Calculamos la masa total que Greed ha expandido en el Manto
        peso_l = sum(f["long"] for f in self.tusk.pesos.values())
        peso_s = sum(f["short"] for f in self.tusk.pesos.values())
        masa_bruta = peso_l + peso_s
        
        # 🛡️ COBRE: Definición real de Oxígeno (Capital libre que NO está en uso)
        oxigeno_libre = 100.0 - self.tusk.margen_ocupado
        
        status_margen = "NORMAL"
        if oxigeno_libre < 10.0: status_margen = "CRÍTICO"
        elif oxigeno_libre > 80.0: status_margen = "SEGURO"

        print(f"\n[ MANTO PIEZOELÉCTRICO ]")
        print(f"  CAPITAL REAL: {self.tusk.masa_bruta:.2f} USD")
        print(f"  MASA BRUTA: {masa_bruta:.4f} LTC | DELTA: {(peso_l - peso_s):.4f} LTC")
        print(f"  OXÍGENO: {oxigeno_libre:.2f}% | ESTADO: {status_margen}")

    def _mostrar_distribucion_espejos(self):
        print(f"\n[ DISTRIBUCIÓN DE ESPEJOS ]")
        activos = False
        for muelle, pesos in self.tusk.pesos.items():
            if pesos['long'] > 0 or pesos['short'] > 0:
                print(f"  {muelle:15}: L {pesos['long']:.4f} | S {pesos['short']:.4f}")
                activos = True
        if not activos: print("  (Esperando materialización...)")

    def _mostrar_estado_legion_deep(self):
        print(f"\n[ LEGIÓN DE BERU ]")
        n_barcos = len(self.beru.legion)
        masa_caza = sum(b.masa for b in self.beru.legion)
        capitan = self.beru.tank.capitan_activo.nombre
        conteo_estados = Counter([b.estado for b in self.beru.legion if b.estado != "COSECHADO"])
        estados_str = ", ".join([f"{k}: {v}" for k, v in conteo_estados.items()])
        
        print(f"  BARCOS: {n_barcos} | MASA EN CAZA: {masa_caza:.4f} LTC")
        print(f"  CLIMA TÁCTICO: {capitan}")
        if n_barcos > 0:
            print(f"  ESTADOS: {estados_str}")
        if self.tusk.total_ciclos_consumados > 0:
            print(f"  ⚡ TOTAL CICLOS CONSUMADOS: {self.tusk.total_ciclos_consumados}")