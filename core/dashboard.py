import os
import time
from collections import Counter
import core.config as config

class PanelDeControl:
    def __init__(self, tusk, beru_gen, igris, tank=None):
        self.tusk = tusk
        self.beru = beru_gen
        self.igris = igris
        self.tank = tank or beru_gen.tank
        self.inicio_sesion = time.time()

    def refrescar(self):
        vuelo = time.strftime("%H:%M:%S", time.gmtime(time.time() - self.inicio_sesion))
        print(f"--- 💎 {config.SISTEMA_NOMBRE} | SESIÓN: {vuelo} ---")
        self._mostrar_pentiverso()
        self._mostrar_diagnostico_hidra()
        self._mostrar_manto_riesgo()
        self._mostrar_distribucion_espejos()
        self._mostrar_estado_legion_deep()
        print("\n" + "═" * 45)

    def _mostrar_pentiverso(self):
        snap = self.tank.snapshot_pentiverso()
        print(f"\n[ PENTIVERSO DUAL LTC+BTC | ref: {config.TICKER_BASE} ]")
        if not snap:
            print("  (Sin datos de Tank)")
            return
        for asset in config.ACTIVOS_PENTIVERSO:
            print(f"  --- {asset} ---")
            for frente, datos in snap.items():
                if datos.get("activo") != asset and not frente.startswith(asset):
                    continue
                p = datos.get("precio", 0)
                ref = " (reflejo)" if datos.get("reflejo_spot") else ""
                marca = "✓" if p > 0 else "—"
                print(f"  {marca} {frente:20} P:{p:>12.4f}{ref}")

    def _mostrar_diagnostico_hidra(self):
        print(f"\n[ TELEMETRÍA DE TANK ]")
        lider = self.tank._obtener_lider_verde()
        id_lider = lider.node_id if lider else "NINGUNO"
        for nodo in self.tank.nodos:
            marca = ">>" if lider and nodo.node_id == id_lider else "  "
            print(f" {marca} NODO {nodo.node_id:02}: {nodo.estado_foco:10} | {nodo.latencia_ms:>5.2f}ms")

    def _mostrar_manto_riesgo(self):
        peso_l = sum(f["long"] for f in self.tusk.pesos.values())
        peso_s = sum(f["short"] for f in self.tusk.pesos.values())
        masa_bruta = peso_l + peso_s
        oxigeno_libre = 100.0 - self.tusk.margen_ocupado
        status_margen = "NORMAL"
        if oxigeno_libre < 10.0:
            status_margen = "CRÍTICO"
        elif oxigeno_libre > 80.0:
            status_margen = "SEGURO"

        print(f"\n[ MANTO PIEZOELÉCTRICO ]")
        print(f"  CAPITAL REAL: {self.tusk.masa_bruta:.2f} USD")
        print(f"  MASA BRUTA: {masa_bruta:.4f} | DELTA: {(peso_l - peso_s):.4f}")
        print(f"  OXÍGENO: {oxigeno_libre:.2f}% | ESTADO: {status_margen}")

    def _mostrar_distribucion_espejos(self):
        print(f"\n[ DISTRIBUCIÓN DE ESPEJOS ]")
        activos = False
        for muelle, pesos in self.tusk.pesos.items():
            if pesos["long"] > 0 or pesos["short"] > 0:
                print(f"  {muelle:15}: L {pesos['long']:.4f} | S {pesos['short']:.4f}")
                activos = True
        if not activos:
            print("  (Esperando materialización...)")

    def _mostrar_estado_legion_deep(self):
        print(f"\n[ LEGIÓN DE BERU ]")
        n_barcos = len(self.beru.legion)
        masa_caza = sum(b.masa for b in self.beru.legion)
        capitan = self.beru.tank.capitan_activo.nombre
        conteo_estados = Counter([b.estado for b in self.beru.legion if b.estado != "COSECHADO"])
        estados_str = ", ".join([f"{k}: {v}" for k, v in conteo_estados.items()])
        print(f"  BARCOS: {n_barcos} | MASA EN CAZA: {masa_caza:.4f}")
        print(f"  CLIMA TÁCTICO: {capitan}")
        if n_barcos > 0:
            print(f"  ESTADOS: {estados_str}")
        if self.tusk.total_ciclos_consumados > 0:
            print(f"  ⚡ TOTAL CICLOS CONSUMADOS: {self.tusk.total_ciclos_consumados}")
