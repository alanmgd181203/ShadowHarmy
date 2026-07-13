#!/usr/bin/env python3
"""
Arena aislada Igris — Kaiser despierta al escudo; fills virtuales al Ask/Bid mainnet.

Sin arise.py, Beru ni Greed. Ojos mainnet (Bridge WS); Tusk mock con equity fijo.
Salida: data/arena_igris_report.json + eventos en data/historial_hierro.jsonl

Env (defaults orientados a ráfagas, no horas de espera):
  ARENA_IGRIS_ACTIVA=true
  ARENA_IGRIS_EQUITY_USD=500
  ARENA_IGRIS_UMBRAL_PCT=0.01
  ARENA_IGRIS_MORDIDA_USD=5
  ARENA_IGRIS_FILLS_VIRTUALES=true
  ARENA_IGRIS_SIN_RANGOS=true
  ARENA_IGRIS_SIN_PACIENCIA=true
  ARENA_IGRIS_ACTIVOS=flota   # o ETH,BTC,SOL
  ARENA_IGRIS_SEGUNDOS_OJOS=25
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Forzar modo arena antes de importar config-dependent modules
os.environ.setdefault("ARENA_IGRIS_ACTIVA", "true")
os.environ.setdefault("ARENA_IGRIS_FILLS_VIRTUALES", "true")
os.environ.setdefault("ARENA_IGRIS_SIN_RANGOS", "true")
os.environ.setdefault("ARENA_IGRIS_SIN_PACIENCIA", "true")
os.environ.setdefault("MODO_SIMULACION", "true")

import core.config as config
from core.bellion import BellionAuditor
from core.bridge import BybitBridge
from core import igris_manto as im
from core import igris_despliegue as ides
from core.trinidad import aplicar_a_config, refrescar_config
from generales.igris import IgrisEscudo
from generales.kaiser import KaiserVocero
from generales.tank import TankCluster


class TuskArenaMock:
    """Bóveda mínima — sin Bridge testnet; equity fijo para la arena."""

    def __init__(self, bellion, equity_usd: float):
        self.bel = bellion
        self.pesos: dict = {}
        self.masa_bruta = float(equity_usd)
        self.masa_bruta_real = float(equity_usd)
        self.masa_autorizada = max(float(equity_usd) * 0.5, 50.0)
        self.margen_ocupado = 0.0
        self.total_ciclos_consumados = 0
        self.toques_greed_manto = {}
        self.cola_ordenes_manto = []
        self.manto_cedido_a_greed = False
        self.greed_basis_abiertos = []
        self.reservas_activas: dict = {}
        self.masa_reservada_ltc = 0.0

    async def solicitar_reserva(self, uid: str, masa: float, general: str, direccion: str = "LONG") -> bool:
        if masa <= 0 or self.masa_autorizada < masa:
            return False
        self.reservas_activas[uid] = type("Sombra", (), {
            "uid": uid, "masa": masa, "direccion": direccion,
        })()
        self.masa_autorizada -= masa
        self.masa_reservada_ltc += masa
        return True

    async def confirmar_reserva(
        self, uid: str, frente: str, direccion: str,
        fill_confirmado=True, precio_fill: float | None = None,
    ):
        if uid not in self.reservas_activas:
            return False
        sombra = self.reservas_activas.pop(uid)
        im.asegurar_peso(self.pesos, frente)
        dir_key = "long" if direccion == "LONG" else "short"
        px = float(precio_fill or 0)
        if px > 0:
            im.actualizar_promedio(self.pesos, frente, direccion, sombra.masa, px)
        self.pesos[frente][dir_key] += sombra.masa
        self.masa_reservada_ltc = max(0.0, self.masa_reservada_ltc - sombra.masa)
        await self.bel.anotar(
            "TUSK", "ANCLAJE_ARENA",
            f"{sombra.masa:.6f} virtual {direccion} en {frente} @{px:.4f}",
        )
        return True

    async def liberar_reserva(self, uid: str):
        if uid in self.reservas_activas:
            sombra = self.reservas_activas.pop(uid)
            self.masa_autorizada += sombra.masa
            self.masa_reservada_ltc = max(0.0, self.masa_reservada_ltc - sombra.masa)

    async def actualizar_precios(self, *args, **kwargs):
        pass

    def snapshot_telemetria_posiciones(self):
        return {}

def _cargar_activos_flota() -> list[str]:
    raw = (getattr(config, "ARENA_IGRIS_ACTIVOS", "flota") or "flota").strip()
    if raw.lower() in ("flota", "all", "*"):
        path = ROOT / "config" / "diccionario_beru_flota_manto.json"
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            meta = data.get("meta") or {}
            lista = meta.get("activos") or []
            if lista:
                return sorted(str(a).upper() for a in lista)
            activos_map = data.get("activos") or {}
            if isinstance(activos_map, dict) and activos_map:
                return sorted(activos_map.keys())
        return ["ETH", "BTC", "LTC", "SOL"]
    return [a.strip().upper() for a in raw.split(",") if a.strip()]


def _alertas_manto_igris(kaiser: KaiserVocero, activo: str) -> list[dict]:
    todas = kaiser.consumir("IGRIS")
    tipos = {"OPORTUNIDAD_MANTO", "MATRIZ_SPREAD"}
    out = []
    for a in todas:
        if str(a.get("base", "")).upper() != activo.upper():
            continue
        if a.get("tipo") not in tipos:
            datos = a.get("datos") or {}
            if str(datos.get("tipo") or "") != "lineal_vs_inverse":
                continue
        out.append(a)
    return out


async def _warmup_ojos(tank: TankCluster, bellion: BellionAuditor, segundos: float) -> None:
    bridge = BybitBridge(tank, TuskArenaMock(bellion, 1), bellion, None, None)
    tasks = [
        asyncio.create_task(bridge.conectar()),
        asyncio.create_task(tank.vigilar_aguas()),
    ]
    await asyncio.sleep(segundos)
    for t in tasks:
        t.cancel()
    for t in tasks:
        try:
            await t
        except asyncio.CancelledError:
            pass


async def run_arena(segundos: float | None = None) -> dict:
    aplicar_a_config(config)
    try:
        refrescar_config()
        aplicar_a_config(config)
    except Exception:
        print("[arena] trinidad cache local")

    config.ARENA_IGRIS_ACTIVA = True
    config.MODO_SIMULACION = True

    equity = float(getattr(config, "ARENA_IGRIS_EQUITY_USD", 500))
    seg = float(segundos if segundos is not None else getattr(config, "ARENA_IGRIS_SEGUNDOS_OJOS", 25))
    activos_cfg = _cargar_activos_flota()

    bellion = BellionAuditor()
    tusk = TuskArenaMock(bellion, equity)
    tank = TankCluster(tusk, bellion, ticker_base=config.TICKER_BASE)
    kaiser = KaiserVocero(tank, bellion)
    igris = IgrisEscudo(tusk, tank, bellion, bridge=None, kaiser=kaiser)

    print(f"[arena] Ojos mainnet {seg:.0f}s — equity mock ${equity:.0f} — activos: {len(activos_cfg)}")
    await _warmup_ojos(tank, bellion, seg)

    digest = kaiser.refrescar()
    matriz = tank.snapshot_matriz_spreads()
    filas_li = [
        r for r in (matriz.get("filas") or [])
        if str(r.get("tipo") or "") == "lineal_vs_inverse"
    ]

    await bellion.anotar(
        "ARENA", "INICIO",
        f"Matriz L/S: {len(filas_li)} filas · umbral {config.ARENA_IGRIS_UMBRAL_PCT}% · "
        f"mordida ${config.ARENA_IGRIS_MORDIDA_USD}",
    )

    resultados: list[dict] = []
    disparos = 0
    esperas = 0

    for activo in activos_cfg:
        alertas = _alertas_manto_igris(kaiser, activo)
        fl, fs = im.frentes_bootstrap(activo)
        bids_l, asks_l = ides.libro_tank(tank, fl)
        bids_s, asks_s = ides.libro_tank(tank, fs)
        tiene_libro = bool(bids_l or asks_l) and bool(bids_s or asks_s)

        puerta_previa = ides.evaluar_puerta_se(
            tank, fl, fs,
            t0_paciencia=time.time(),
            restante_usd=max(float(config.ARENA_IGRIS_MORDIDA_USD) * 4, 50.0),
            activo=activo,
            perfiles=getattr(kaiser, "perfiles", None),
            tank_semaforo=igris._tank_semaforo(),
            pipeline_ms=(digest.get("pipeline") or {}).get("total_ms"),
            margen_ocupado_pct=0.0,
        )

        fila = {
            "activo": activo,
            "alertas_kaiser": len(alertas),
            "tiene_libro": tiene_libro,
            "puerta_previa_ok": puerta_previa.get("ok"),
            "puerta_motivo": puerta_previa.get("motivo"),
            "spread_pct": puerta_previa.get("spread_pct"),
            "umbral_pct": puerta_previa.get("umbral_pct"),
        }

        if alertas or puerta_previa.get("ok"):
            res = await igris.arena_inyectar_activo(activo, origen="ARENA")
            fila["disparo_ok"] = res.get("ok")
            if res.get("ok"):
                disparos += 1
                await bellion.anotar("ARENA", "DISPARO_OK", f"{activo} dual §E virtual")
            else:
                esperas += 1
                fila["disparo_motivo"] = puerta_previa.get("motivo", "inyectar_fallido")
        else:
            esperas += 1
            fila["disparo_ok"] = False
            fila["disparo_motivo"] = "sin_alerta_ni_puerta"

        resultados.append(fila)

    reporte = {
        "ts": time.time(),
        "segundos_ojos": seg,
        "equity_mock_usd": equity,
        "config": {
            "umbral_pct": config.ARENA_IGRIS_UMBRAL_PCT,
            "mordida_usd": config.ARENA_IGRIS_MORDIDA_USD,
            "fills_virtuales": config.ARENA_IGRIS_FILLS_VIRTUALES,
            "sin_rangos": config.ARENA_IGRIS_SIN_RANGOS,
            "activos_pedidos": activos_cfg,
        },
        "matriz_lineal_inverse_top": filas_li[:15],
        "kaiser_alertas_igris": len(kaiser.consumir("IGRIS")),
        "disparos_ok": disparos,
        "esperas_o_fallos": esperas,
        "pesos_finales": {f: dict(p) for f, p in tusk.pesos.items()},
        "resultados": resultados,
    }

    out_path = ROOT / "data" / "arena_igris_report.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(reporte, indent=2, ensure_ascii=False), encoding="utf-8")

    await bellion.anotar(
        "ARENA", "FIN",
        f"Disparos OK: {disparos}/{len(resultados)} · reporte {out_path.name}",
    )

    print(json.dumps({
        "disparos_ok": disparos,
        "total": len(resultados),
        "reporte": str(out_path),
    }, indent=2))
    return reporte


def main() -> int:
    parser = argparse.ArgumentParser(description="Arena aislada Igris (Kaiser→escudo, fills virtuales)")
    parser.add_argument("--segundos", type=float, default=None, help="Segundos de WS mainnet")
    args = parser.parse_args()
    asyncio.run(run_arena(args.segundos))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
