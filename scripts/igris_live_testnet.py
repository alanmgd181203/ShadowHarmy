#!/usr/bin/env python3
"""
Checklist 3.10.7b — Igris live testnet (órdenes reales en Bybit DEMO).

Sin Beru / sin Greed. Ojos mainnet WS. Manos testnet HTTP.
Umbral §E = fees (prod), no micro de arena. Mordida tope por LIVE_IGRIS_MORDIDA_MAX_USD.

  python scripts/igris_live_testnet.py
  python scripts/igris_live_testnet.py --segundos 90 --activos ETH,BTC,LTC

ABORTA si MODO_TESTNET!=True o faltan API keys.
No reescribe .env: solo fuerza flags en esta sesión.
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

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# --- Sesión 3.10.7b (antes de importar config) ---
os.environ["LIVE_IGRIS_TESTNET"] = "true"
os.environ["MODO_TESTNET"] = "True"
os.environ["MODO_SIMULACION"] = "False"
os.environ["ARENA_IGRIS_ACTIVA"] = "false"
os.environ["ARENA_IGRIS_FILLS_VIRTUALES"] = "false"
os.environ["ARENA_IGRIS_SIN_RANGOS"] = "true"  # verificación: elige activos sin grado Beru
os.environ["ARENA_IGRIS_SIN_BANDA_DELTA"] = "true"
# Puerta §E en live = fees (prod). Micro arena solo si ARENA_IGRIS_ACTIVA.
os.environ["ARENA_IGRIS_SIN_PACIENCIA"] = "false"
os.environ["IGRIS_EVENT_DRIVEN"] = "true"
os.environ["IGRIS_BOOTSTRAP_ON_START"] = "false"
os.environ["GREED_KAISER_ENABLED"] = "false"
os.environ["GREED_VIP_ENABLED"] = "false"
os.environ["GREED_BASIS_HOLD_ENABLED"] = "false"
os.environ["GREED_MULTICRUCE_ENABLED"] = "false"
os.environ["SAFE_MODE"] = "true"

import core.config as config
from core.bellion import BellionAuditor
from core.bridge import BybitBridge
from core import igris_manto as im
from core import igris_despliegue as ides
from core import kaiser_indicators as ki
from core.trinidad import aplicar_a_config, refrescar_config
from generales.igris import IgrisEscudo
from generales.kaiser import KaiserVocero
from generales.tank import TankCluster
from generales.tusk import TuskBoveda


def _activos_cfg(raw: str | None) -> list[str]:
    s = (raw or getattr(config, "LIVE_IGRIS_ACTIVOS", "ETH,BTC,LTC") or "ETH,BTC,LTC").strip()
    if s.lower() in ("flota", "all", "*"):
        path = ROOT / "config" / "diccionario_beru_flota_manto.json"
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            lista = (data.get("meta") or {}).get("activos") or []
            if lista:
                return sorted(str(a).upper() for a in lista)
        return ["ETH", "BTC", "LTC"]
    return [a.strip().upper() for a in s.split(",") if a.strip()]


def _contar_ordenes_historial(path: Path, desde_ts: float) -> dict:
    out = {"orden_enviada": 0, "orden_fallida": 0, "engorde_dual": 0, "lineas": 0}
    if not path.exists():
        return out
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except Exception:
        return out
    for line in lines[-400:]:
        out["lineas"] += 1
        u = line.upper()
        if "ORDEN_ENVIADA" in u:
            out["orden_enviada"] += 1
        if "ORDEN_FALLIDA" in u or "ORDEN FALLIDA" in u:
            out["orden_fallida"] += 1
        if "ENGORDE_DUAL" in u or "BOOTSTRAP_MANTO" in u:
            out["engorde_dual"] += 1
    return out


async def run_live(segundos: float | None, activos_arg: str | None) -> dict:
    aplicar_a_config(config)
    try:
        refrescar_config()
        aplicar_a_config(config)
    except Exception:
        print("[live-igris] trinidad cache local")

    # Reafirmar sesión (por si .env / trinidad sobrescribió)
    config.LIVE_IGRIS_TESTNET = True
    config.TESTNET = True
    config.MODO_SIMULACION = False
    config.ARENA_IGRIS_ACTIVA = False
    config.ARENA_IGRIS_FILLS_VIRTUALES = False
    config.ARENA_IGRIS_SIN_RANGOS = True
    config.ARENA_IGRIS_SIN_BANDA_DELTA = True
    config.ARENA_IGRIS_SIN_PACIENCIA = False  # live: umbral fees, no micro arena
    config.IGRIS_EVENT_DRIVEN = True
    config.IGRIS_BOOTSTRAP_ON_START = False
    config.GREED_KAISER_ENABLED = False
    config.GREED_VIP_ENABLED = False
    config.GREED_BASIS_HOLD_ENABLED = False
    config.GREED_MULTICRUCE_ENABLED = False
    config.SAFE_MODE = True

    if not config.API_KEY or not config.API_SECRET:
        raise SystemExit("ABORT: faltan BYBIT_API_KEY / BYBIT_API_SECRET en .env")
    if not config.TESTNET:
        raise SystemExit("ABORT: MODO_TESTNET debe ser True (campo de entrenamiento)")

    seg = float(
        segundos
        if segundos is not None
        else getattr(config, "LIVE_IGRIS_SEGUNDOS_OJOS", 90)
    )
    activos = _activos_cfg(activos_arg)
    max_usd = float(getattr(config, "LIVE_IGRIS_MORDIDA_MAX_USD", 12.0))
    require_kaiser = bool(getattr(config, "LIVE_IGRIS_REQUIRE_KAISER", False))

    bellion = BellionAuditor()
    tusk = TuskBoveda(bellion)
    tank = TankCluster(tusk, bellion, ticker_base=config.TICKER_BASE)
    kaiser = KaiserVocero(tank, bellion)
    bridge = BybitBridge(tank, tusk, bellion, config.API_KEY, config.API_SECRET)
    igris = IgrisEscudo(tusk, tank, bellion, bridge=bridge, kaiser=kaiser)

    tasks = [
        asyncio.create_task(bridge.conectar()),
        asyncio.create_task(tank.vigilar_aguas()),
        asyncio.create_task(bridge.hilo_sincronizacion_nav()),
    ]

    print("")
    print("=" * 52)
    print("  Shadow Army — Igris LIVE TESTNET (3.10.7b)")
    print("  Manos: Bybit DEMO · Ojos: mainnet WS")
    print(f"  Ojos: {seg:.0f}s · Activos: {','.join(activos)}")
    print(f"  Mordida max: ${max_usd:.0f}/pata · Umbral: fees (prod)")
    print("  Greed/Beru: hibernados en esta sesión")
    print("=" * 52)
    print("")

    t_hist = time.time()
    try:
        # NAV real testnet
        await asyncio.sleep(2)
        try:
            w = bridge.session.get_wallet_balance(accountType="UNIFIED")
            if w.get("retCode") == 0:
                nav = float(w["result"]["list"][0].get("totalEquity", 0) or 0)
                disp = float(w["result"]["list"][0].get("totalAvailableBalance", 0) or 0)
                margen = ((nav - disp) / nav * 100) if nav > 0 else 0.0
                await tusk.actualizar_nav_real(nav, margen)
                print(f"[live-igris] NAV testnet ${nav:.2f} · margen {margen:.1f}%")
            else:
                print(f"[live-igris] wallet aviso: {w.get('retMsg')}")
        except Exception as e:
            print(f"[live-igris] wallet no leido: {e}")

        t0 = time.time()
        while time.time() - t0 < seg:
            await asyncio.sleep(min(10.0, max(0.5, seg - (time.time() - t0))))
            preview = ki.interpretar_oportunidades_manto(tank, activos)
            print(
                f"[live-igris] ojos {time.time()-t0:.0f}/{seg:.0f}s | "
                f"OPORTUNIDAD_MANTO={len(preview)}"
            )

        digest = kaiser.refrescar()
        alertas = list(kaiser.consumir("IGRIS"))
        morado = ki.interpretar_oportunidades_manto(tank, activos)
        alertas_idx: dict[str, list] = {}
        for a in alertas + morado:
            if a.get("tipo") != "OPORTUNIDAD_MANTO":
                continue
            b = str(a.get("base", "")).upper()
            alertas_idx.setdefault(b, []).append(a)

        await bellion.anotar(
            "LIVE_IGRIS", "INICIO",
            f"morado={len(morado)} activos={len(activos)} max_usd={max_usd}",
        )
        print(
            f"[live-igris] Barrido LIVE | OPORTUNIDAD_MANTO={len(morado)} | "
            f"digest Igris={len(alertas)}"
        )

        resultados: list[dict] = []
        disparos = disparos_kaiser = disparos_puerta = esperas = 0
        t_barrido = time.time()

        for activo in activos:
            print(f"[live-igris] -> {activo} ...", flush=True)
            fl, fs = im.frentes_bootstrap(activo)
            bids_l, asks_l = ides.libro_tank(tank, fl)
            bids_s, asks_s = ides.libro_tank(tank, fs)
            tiene_libro = bool(bids_l or asks_l) and bool(bids_s or asks_s)

            puerta = ides.evaluar_puerta_se(
                tank, fl, fs,
                t0_paciencia=time.time(),
                restante_usd=max_usd,
                activo=activo,
                perfiles=getattr(kaiser, "perfiles", None),
                tank_semaforo="VERDE",
                pipeline_ms=(digest.get("pipeline") or {}).get("total_ms"),
                margen_ocupado_pct=float(tusk.margen_ocupado or 0),
            )
            alertas_a = alertas_idx.get(activo, [])
            origen = "ninguno"
            if alertas_a:
                origen = "kaiser"
            elif puerta.get("ok") and not require_kaiser:
                origen = "puerta"

            fila = {
                "activo": activo,
                "alertas_kaiser": len(alertas_a),
                "tiene_libro": tiene_libro,
                "puerta_ok": puerta.get("ok"),
                "puerta_motivo": puerta.get("motivo"),
                "spread_pct": puerta.get("spread_pct"),
                "umbral_pct": puerta.get("umbral_pct"),
                "origen_candidato": origen,
            }

            if origen in ("kaiser", "puerta"):
                res = await igris.live_inyectar_activo(
                    activo, max_usd=max_usd, origen="LIVE_TESTNET",
                )
                fila["disparo_ok"] = res.get("ok")
                if res.get("ok"):
                    disparos += 1
                    if origen == "kaiser":
                        disparos_kaiser += 1
                    else:
                        disparos_puerta += 1
                    await bellion.anotar(
                        "LIVE_IGRIS", "DISPARO_OK",
                        f"{activo} dual §E LIVE ({origen}) max=${max_usd}",
                    )
                    print(
                        f"[live-igris]   OK LIVE {activo} ({origen}) "
                        f"spread={puerta.get('spread_pct')}"
                    )
                else:
                    esperas += 1
                    fila["disparo_motivo"] = "inyectar_fallido"
                    print(f"[live-igris]   FAIL {activo} inyectar")
            else:
                esperas += 1
                fila["disparo_ok"] = False
                fila["disparo_motivo"] = (
                    "sin_alerta_kaiser" if require_kaiser else "sin_alerta_ni_puerta"
                )
                print(
                    f"[live-igris]   skip {activo} libro={tiene_libro} "
                    f"puerta={puerta.get('motivo')} kaiser={len(alertas_a)}"
                )
            resultados.append(fila)

        dt_barrido = time.time() - t_barrido
        hist = _contar_ordenes_historial(ROOT / "data" / "historial_hierro.jsonl", t_hist)
        pesos = {f: dict(p) for f, p in tusk.pesos.items()}

        criterio_ok = disparos >= 1 and hist["orden_enviada"] >= 1
        criterio_parcial = disparos >= 1  # fill Tusk sin log Bridge (raro)
        veredicto = (
            "PASS_LIVE"
            if criterio_ok
            else ("PASS_PARCIAL_SIN_LOG_BRIDGE" if criterio_parcial else "SIN_DISPARO_MERCADO")
        )

        reporte = {
            "checklist": "3.10.7b",
            "ts": time.time(),
            "veredicto": veredicto,
            "segundos_ojos": seg,
            "segundos_barrido": round(dt_barrido, 2),
            "config": {
                "testnet": True,
                "modo_simulacion": False,
                "arena_activa": False,
                "fills_virtuales": False,
                "vision_manto": "ask_bid_fees",
                "mordida_max_usd": max_usd,
                "activos": activos,
                "require_kaiser": require_kaiser,
                "greed_hibernado": True,
            },
            "kaiser_oportunidad_manto": len(morado),
            "disparos_ok": disparos,
            "disparos_via_kaiser": disparos_kaiser,
            "disparos_via_puerta": disparos_puerta,
            "esperas_o_fallos": esperas,
            "historial_resumen": hist,
            "pesos_tusk": pesos,
            "oportunidad_manto_top": [
                {
                    "base": a.get("base"),
                    "spread_pct": (a.get("datos") or {}).get("spread_pct"),
                    "umbral_pct": (a.get("datos") or {}).get("umbral_pct"),
                    "modo": (a.get("datos") or {}).get("modo_umbral"),
                }
                for a in morado[:15]
            ],
            "resultados": resultados,
            "como_cerrar_checklist": (
                "PASS_LIVE => marcar 3.10.7b [x] en migracion/16_CHECKLIST_MAESTRO.md "
                "y confirmar posiciones L inverse + S lineal en Bybit testnet UI."
            ),
        }

        out_path = ROOT / "data" / "igris_live_testnet_report.json"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(reporte, indent=2, ensure_ascii=False), encoding="utf-8")

        await bellion.anotar(
            "LIVE_IGRIS", "FIN",
            f"{veredicto} OK={disparos}/{len(resultados)} "
            f"kaiser={disparos_kaiser} puerta={disparos_puerta} "
            f"bridge_ordenes={hist['orden_enviada']}",
        )
        resumen = {
            "veredicto": veredicto,
            "disparos_ok": disparos,
            "via_kaiser": disparos_kaiser,
            "via_puerta": disparos_puerta,
            "oportunidad_manto": len(morado),
            "orden_enviada_log": hist["orden_enviada"],
            "barrido_s": round(dt_barrido, 2),
            "reporte": str(out_path),
        }
        print(json.dumps(resumen, indent=2))
        print("")
        if veredicto == "PASS_LIVE":
            print("[live-igris] CHECKLIST 3.10.7b listo para marcar OK.")
        elif veredicto == "SIN_DISPARO_MERCADO":
            print(
                "[live-igris] Proceso OK pero mercado sin spread >= fees. "
                "Reintentar mas tarde o ampliar LIVE_IGRIS_ACTIVOS."
            )
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
    parser = argparse.ArgumentParser(description="Igris live testnet 3.10.7b")
    parser.add_argument("--segundos", type=float, default=None)
    parser.add_argument("--activos", type=str, default=None)
    args = parser.parse_args()
    asyncio.run(run_live(args.segundos, args.activos))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
