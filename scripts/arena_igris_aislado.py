#!/usr/bin/env python3
"""
Arena aislada Igris — Kaiser (Ask/Bid) despierta al escudo; fills virtuales.

Sin arise/Beru/Greed. Bridge vivo durante el barrido (rápido).
Default ojos: 120 s.

  python scripts/arena_igris_aislado.py --segundos 120
  ARENA_IGRIS_ACTIVOS=ETH python scripts/arena_igris_aislado.py --segundos 45
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

# Consola Windows (cp1252) no traga Unicode del ejército
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

os.environ.setdefault("ARENA_IGRIS_ACTIVA", "true")
os.environ.setdefault("ARENA_IGRIS_FILLS_VIRTUALES", "true")
os.environ.setdefault("ARENA_IGRIS_SIN_RANGOS", "true")
os.environ.setdefault("ARENA_IGRIS_SIN_PACIENCIA", "true")
os.environ.setdefault("ARENA_IGRIS_SIN_BANDA_DELTA", "true")
os.environ.setdefault("ARENA_IGRIS_TUSK_LIMPIO_POR_ACTIVO", "true")
os.environ.setdefault("ARENA_IGRIS_SEGUNDOS_OJOS", "120")
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
    def __init__(self, bellion, equity_usd: float):
        self.bel = bellion
        self._equity = float(equity_usd)
        self.reset_manto(equity_usd)

    def reset_manto(self, equity_usd: float | None = None):
        eq = float(equity_usd if equity_usd is not None else self._equity)
        self._equity = eq
        self.pesos: dict = {}
        self.masa_bruta = eq
        self.masa_bruta_real = eq
        self.masa_autorizada = max(eq * 0.5, 50.0)
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
            lista = (data.get("meta") or {}).get("activos") or []
            if lista:
                return sorted(str(a).upper() for a in lista)
        return ["ETH", "BTC", "LTC", "SOL"]
    return [a.strip().upper() for a in raw.split(",") if a.strip()]


def _alertas_por_activo(alertas: list[dict], activo: str) -> list[dict]:
    tipos = {"OPORTUNIDAD_MANTO", "MATRIZ_SPREAD"}
    out = []
    for a in alertas:
        if str(a.get("base", "")).upper() != activo.upper():
            continue
        if a.get("tipo") not in tipos:
            datos = a.get("datos") or {}
            if str(datos.get("tipo") or "") != "lineal_vs_inverse":
                continue
        out.append(a)
    return out


async def run_arena(segundos: float | None = None) -> dict:
    aplicar_a_config(config)
    try:
        refrescar_config()
        aplicar_a_config(config)
    except Exception:
        print("[arena] trinidad cache local")

    config.ARENA_IGRIS_ACTIVA = True
    config.ARENA_IGRIS_SIN_BANDA_DELTA = True
    config.MODO_SIMULACION = True

    equity = float(getattr(config, "ARENA_IGRIS_EQUITY_USD", 500))
    seg = float(segundos if segundos is not None else getattr(config, "ARENA_IGRIS_SEGUNDOS_OJOS", 120))
    activos_cfg = _cargar_activos_flota()
    tusk_limpio = getattr(config, "ARENA_IGRIS_TUSK_LIMPIO_POR_ACTIVO", True)
    require_kaiser = getattr(config, "ARENA_IGRIS_REQUIRE_KAISER", False)

    bellion = BellionAuditor()
    tusk = TuskArenaMock(bellion, equity)
    tank = TankCluster(tusk, bellion, ticker_base=config.TICKER_BASE)
    kaiser = KaiserVocero(tank, bellion)
    igris = IgrisEscudo(tusk, tank, bellion, bridge=None, kaiser=kaiser)

    bridge = BybitBridge(tank, TuskArenaMock(bellion, 1), bellion, None, None)
    tasks = [
        asyncio.create_task(bridge.conectar()),
        asyncio.create_task(tank.vigilar_aguas()),
    ]

    print(
        f"[arena] Ojos mainnet {seg:.0f}s (~{seg/60:.1f} min) — equity ${equity:.0f} — "
        f"activos {len(activos_cfg)} — tusk_limpio={tusk_limpio}"
    )

    try:
        t0 = time.time()
        while time.time() - t0 < seg:
            await asyncio.sleep(min(10.0, max(0.5, seg - (time.time() - t0))))
            # Preview Ask/Bid morado (rápido) sin cancelar WS
            from core import kaiser_indicators as ki
            preview = ki.interpretar_oportunidades_manto(tank, activos_cfg)
            print(
                f"[arena] ojos {time.time()-t0:.0f}/{seg:.0f}s | "
                f"OPORTUNIDAD_MANTO Ask/Bid={len(preview)}"
            )

        # Un solo digest Kaiser con Bridge aún vivo
        digest = kaiser.refrescar()
        alertas_totales = list(kaiser.consumir("IGRIS"))
        n_oportunidad = sum(1 for a in alertas_totales if a.get("tipo") == "OPORTUNIDAD_MANTO")
        # Recalcular Ask/Bid fresco sobre flota (fuente de verdad del morado)
        from core import kaiser_indicators as ki
        morado_fresco = ki.interpretar_oportunidades_manto(tank, activos_cfg)
        # Fusionar morados frescos en el índice por activo
        alertas_idx: dict[str, list] = {}
        for a in alertas_totales + morado_fresco:
            if a.get("tipo") != "OPORTUNIDAD_MANTO":
                continue
            b = str(a.get("base", "")).upper()
            alertas_idx.setdefault(b, []).append(a)

        await bellion.anotar(
            "ARENA", "INICIO",
            f"OPORTUNIDAD_MANTO Ask/Bid: {len(morado_fresco)} | "
            f"umbral {config.ARENA_IGRIS_UMBRAL_PCT}% | mordida ${config.ARENA_IGRIS_MORDIDA_USD}",
        )
        print(
            f"[arena] Barrido rapido | OPORTUNIDAD_MANTO={len(morado_fresco)} | "
            f"alertas Igris digest={len(alertas_totales)}"
        )

        resultados: list[dict] = []
        disparos = disparos_kaiser = disparos_puerta = esperas = 0
        pesos_acumulados: dict = {}
        t_barrido = time.time()

        for activo in activos_cfg:
            print(f"[arena] -> {activo} ...", flush=True)
            if tusk_limpio:
                tusk.reset_manto(equity)
                igris._bloque_objetivo_usd = 0.0
                igris._bloque_inyectado_usd = 0.0
                igris._engorde_fail_until = 0.0

            alertas = alertas_idx.get(activo, []) or _alertas_por_activo(alertas_totales, activo)
            fl, fs = im.frentes_bootstrap(activo)
            bids_l, asks_l = ides.libro_tank(tank, fl)
            bids_s, asks_s = ides.libro_tank(tank, fs)
            tiene_libro = bool(bids_l or asks_l) and bool(bids_s or asks_s)

            puerta = ides.evaluar_puerta_se(
                tank, fl, fs,
                t0_paciencia=time.time(),
                restante_usd=max(float(config.ARENA_IGRIS_MORDIDA_USD) * 4, 50.0),
                activo=activo,
                perfiles=getattr(kaiser, "perfiles", None),
                tank_semaforo="VERDE",
                pipeline_ms=(digest.get("pipeline") or {}).get("total_ms"),
                margen_ocupado_pct=0.0,
            )

            origen = "ninguno"
            if alertas:
                origen = "kaiser"
            elif puerta.get("ok") and not require_kaiser:
                origen = "puerta"

            fila = {
                "activo": activo,
                "alertas_kaiser": len(alertas),
                "tipos_alerta": [a.get("tipo") for a in alertas],
                "tiene_libro": tiene_libro,
                "puerta_previa_ok": puerta.get("ok"),
                "puerta_motivo": puerta.get("motivo"),
                "spread_pct": puerta.get("spread_pct"),
                "umbral_pct": puerta.get("umbral_pct"),
                "origen_candidato": origen,
            }

            if origen in ("kaiser", "puerta"):
                res = await igris.arena_inyectar_activo(activo, origen="ARENA")
                fila["disparo_ok"] = res.get("ok")
                if res.get("ok"):
                    disparos += 1
                    if origen == "kaiser":
                        disparos_kaiser += 1
                    else:
                        disparos_puerta += 1
                    await bellion.anotar(
                        "ARENA", "DISPARO_OK",
                        f"{activo} dual §E virtual ({origen})",
                    )
                    print(f"[arena]   OK {activo} ({origen}) spread={puerta.get('spread_pct')}")
                else:
                    esperas += 1
                    fila["disparo_motivo"] = "inyectar_fallido"
                    print(f"[arena]   FAIL {activo} inyectar")
            else:
                esperas += 1
                fila["disparo_ok"] = False
                fila["disparo_motivo"] = (
                    "sin_alerta_kaiser" if require_kaiser else "sin_alerta_ni_puerta"
                )
                print(
                    f"[arena]   skip {activo} libro={tiene_libro} "
                    f"puerta={puerta.get('motivo')} kaiser={len(alertas)}"
                )

            for f, p in tusk.pesos.items():
                pesos_acumulados[f] = dict(p)
            resultados.append(fila)

        dt_barrido = time.time() - t_barrido
        reporte = {
            "ts": time.time(),
            "segundos_ojos": seg,
            "segundos_barrido": round(dt_barrido, 2),
            "equity_mock_usd": equity,
            "config": {
                "umbral_pct": config.ARENA_IGRIS_UMBRAL_PCT,
                "mordida_usd": config.ARENA_IGRIS_MORDIDA_USD,
                "fills_virtuales": config.ARENA_IGRIS_FILLS_VIRTUALES,
                "sin_rangos": config.ARENA_IGRIS_SIN_RANGOS,
                "sin_banda_delta": config.ARENA_IGRIS_SIN_BANDA_DELTA,
                "tusk_limpio_por_activo": tusk_limpio,
                "require_kaiser": require_kaiser,
                "vision_manto": "ask_bid",
                "activos_pedidos": activos_cfg,
            },
            "kaiser_oportunidad_manto": len(morado_fresco),
            "kaiser_alertas_igris": len(alertas_totales),
            "oportunidad_manto_top": [
                {
                    "base": a.get("base"),
                    "spread_pct": (a.get("datos") or {}).get("spread_pct"),
                    "umbral_pct": (a.get("datos") or {}).get("umbral_pct"),
                }
                for a in morado_fresco[:15]
            ],
            "disparos_ok": disparos,
            "disparos_via_kaiser": disparos_kaiser,
            "disparos_via_puerta": disparos_puerta,
            "esperas_o_fallos": esperas,
            "pesos_finales": pesos_acumulados,
            "resultados": resultados,
        }

        out_path = ROOT / "data" / "arena_igris_report.json"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(reporte, indent=2, ensure_ascii=False), encoding="utf-8")

        await bellion.anotar(
            "ARENA", "FIN",
            f"OK {disparos}/{len(resultados)} kaiser={disparos_kaiser} "
            f"puerta={disparos_puerta} barrido={dt_barrido:.1f}s",
        )
        print(json.dumps({
            "disparos_ok": disparos,
            "via_kaiser": disparos_kaiser,
            "via_puerta": disparos_puerta,
            "oportunidad_manto": len(morado_fresco),
            "barrido_s": round(dt_barrido, 2),
            "total": len(resultados),
            "reporte": str(out_path),
        }, indent=2))
        return reporte
    finally:
        for t in tasks:
            t.cancel()
        for t in tasks:
            try:
                await t
            except asyncio.CancelledError:
                pass


def main() -> int:
    parser = argparse.ArgumentParser(description="Arena Igris Ask/Bid (~2 min ojos)")
    parser.add_argument("--segundos", type=float, default=None)
    args = parser.parse_args()
    asyncio.run(run_arena(args.segundos))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
