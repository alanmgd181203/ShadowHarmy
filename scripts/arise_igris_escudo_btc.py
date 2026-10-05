#!/usr/bin/env python3
"""ARISE Igris Escudo BTC — vive con la balanza de Beru (viejita).

Lee balanza L/S (sin BTC) → peldaños → meta BTC inverso OKX.
Órdenes a market por defecto (Monarca 2026-09-24). Limit solo si se fuerza.

Candados (env):
  IGRIS_ESCUDO_BTC_ACTIVO=1
  IGRIS_ESCUDO_BTC_MODO=live|sim
  IGRIS_ESCUDO_BTC_LIVE_OK=1   # obligatorio para manos reales
  IGRIS_ESCUDO_BTC_ORD_TIPO=market
  IGRIS_ESCUDO_BTC_R=dinamico
  IGRIS_ESCUDO_BTC_FRENTE=inverso

Uso::
  python scripts/arise_igris_escudo_btc.py
  python scripts/arise_igris_escudo_btc.py --intervalo 45
  python scripts/arise_igris_escudo_btc.py --sim   # fuerza papel
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

_LOG = ROOT / "data" / "logs" / "arise_igris_escudo_out.log"


# Asiento del peldaño. Cuatrocientos dentro del mil no mueven el escudo.
_ASIENTO = {"armado": False, "lado": "", "valor": 0.0}
_ASIENTO_PATH = ROOT / "data" / "beru" / "escudo" / "asiento_dual.json"
_TSUNAMI_PATH = ROOT / "data" / "beru" / "escudo" / "tsunami.json"


def _cargar_asiento() -> None:
    try:
        data = json.loads(_ASIENTO_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        return
    _ASIENTO["armado"] = bool(data.get("armado"))
    _ASIENTO["lado"] = str(data.get("lado") or "")
    _ASIENTO["valor"] = float(data.get("valor") or 0)


def _cruzar(snap: dict, boca: float) -> tuple[float, float]:
    """Casa (corto menos largo) más la boca. El mismo lado se suma, el otro se resta."""
    casa = float(snap.get("short_usd") or 0) - float(snap.get("long_usd") or 0)
    return casa + float(boca or 0), casa


def _proponer_asiento(neto: float) -> tuple[float, bool, str]:
    from cirugias.escudo_dual.elegir import asiento_en_banda

    return asiento_en_banda(
        neto,
        armado=bool(_ASIENTO["armado"]),
        lado=str(_ASIENTO["lado"] or ""),
        valor=_ASIENTO["valor"] if _ASIENTO["armado"] else None,
    )


def _sellar_asiento(valor: float, armado: bool, lado: str) -> None:
    _ASIENTO["valor"] = float(valor)
    _ASIENTO["armado"] = bool(armado)
    _ASIENTO["lado"] = str(lado or "")
    try:
        _ASIENTO_PATH.parent.mkdir(parents=True, exist_ok=True)
        _ASIENTO_PATH.write_text(json.dumps(_ASIENTO), encoding="utf-8")
    except OSError:
        pass


def _meta_capa(asiento: float, relacion: float) -> float:
    """El peldaño ya sentado, por la relación lenta del metal."""
    return float(asiento) * float(relacion)


def _reparto(
    asiento: float,
    reina_pos: float,
    rey_pos: float,
    *,
    permiso_rey: bool | None,
    permiso_reina: bool | None,
    relacion_rey: float,
    relacion_reina: float,
) -> tuple[float, float]:
    """Cuánto debe quedar en cada metal. No manda orden.

    Si la bolsa crece, la capa nueva entra al que acompaña.
    No vacía al que ya estaba. Si la bolsa baja, sale primero
    el que no acompaña.
    """
    from cirugias.escudo_dual.capas import _orden_de_salida, _quien_recibe

    rel = {"reina": float(relacion_reina), "rey": float(relacion_rey)}
    if asiento > 0:
        favor = {"reina": max(0.0, reina_pos), "rey": max(0.0, rey_pos)}
    elif asiento < 0:
        favor = {"reina": max(0.0, -reina_pos), "rey": max(0.0, -rey_pos)}
    else:
        return 0.0, 0.0
    bolsa = {
        nombre: (favor[nombre] / rel[nombre]) if rel[nombre] > 0 else 0.0
        for nombre in ("reina", "rey")
    }
    quiero = abs(float(asiento))
    tengo = bolsa["reina"] + bolsa["rey"]
    if quiero > tengo + 1.0:
        metal = _quien_recibe(permiso_rey, permiso_reina, rel["rey"], rel["reina"])
        if metal is not None and rel[metal] > 0:
            bolsa[metal] += quiero - tengo
    elif tengo > quiero + 1.0:
        sobra = tengo - quiero
        primero = _orden_de_salida(permiso_rey, permiso_reina)
        if primero == "rey":
            orden = ("rey", "reina")
        elif primero == "reina":
            orden = ("reina", "rey")
        else:
            elegido = _quien_recibe(permiso_rey, permiso_reina, rel["rey"], rel["reina"])
            orden = ("rey", "reina") if elegido == "reina" else ("reina", "rey")
        for nombre in orden:
            tomar = min(bolsa[nombre], sobra)
            bolsa[nombre] -= tomar
            sobra -= tomar
            if sobra <= 1.0:
                break
    signo = 1.0 if asiento > 0 else -1.0
    return signo * bolsa["reina"] * rel["reina"], signo * bolsa["rey"] * rel["rey"]


def _emit(msg: str) -> None:
    """Escribe al stdout (y al log si no está ya redirigido por el ritual)."""
    print(msg, flush=True)
    # Si el ritual ya redirige stdout al log, no reabrir el mismo archivo
    # (en Windows el doble handle tumba el proceso).
    if os.environ.get("IGRIS_ESCUDO_LOG_SOLO_STDOUT", "").strip() in (
        "1",
        "true",
        "yes",
        "on",
        "si",
    ):
        return
    try:
        _LOG.parent.mkdir(parents=True, exist_ok=True)
        with _LOG.open("a", encoding="utf-8") as fh:
            fh.write(msg + "\n")
    except Exception:
        pass


def _boot_env(*, forzar_sim: bool) -> None:
    os.environ.setdefault("BERU_MAR", "okx")
    os.environ["IGRIS_ESCUDO_BTC_ACTIVO"] = "1"
    os.environ.setdefault("IGRIS_ESCUDO_BTC_R", "dinamico")
    os.environ.setdefault("IGRIS_ESCUDO_BTC_FRENTE", "inverso")
    # Monarca: entradas a mercado (fill inmediato). Limit solo si se fuerza.
    os.environ["IGRIS_ESCUDO_BTC_ORD_TIPO"] = (
        os.environ.get("IGRIS_ESCUDO_BTC_ORD_TIPO") or "market"
    )
    # Chase más ágil (solo aplica si ORD_TIPO=limit).
    os.environ.setdefault("IGRIS_ESCUDO_BTC_LIMIT_ESPERA_S", "8")
    os.environ.setdefault("IGRIS_ESCUDO_BTC_LIMIT_PASO_PCT", "0.0015")
    os.environ.setdefault("IGRIS_ESCUDO_BTC_LIMIT_MAX_DRIFT_PCT", "0.02")
    os.environ.setdefault("IGRIS_ESCUDO_BTC_LIMIT_MAX_MOVES", "40")
    os.environ.setdefault("IGRIS_ESCUDO_BTC_LIMIT_OFFSET_PCT", "0.00015")
    if forzar_sim:
        os.environ["IGRIS_ESCUDO_BTC_MODO"] = "sim"
        os.environ.pop("IGRIS_ESCUDO_BTC_LIVE_OK", None)
    else:
        # Forzar live de esta sesión (no dejar que .env viejo deje sim).
        os.environ["IGRIS_ESCUDO_BTC_MODO"] = "live"
        os.environ["IGRIS_ESCUDO_BTC_LIVE_OK"] = "1"


def main() -> int:
    ap = argparse.ArgumentParser(description="ARISE Igris Escudo BTC")
    ap.add_argument("--intervalo", type=float, default=15.0)
    ap.add_argument("--sim", action="store_true", help="Forzar papel (sin LIVE_OK)")
    ap.add_argument("--una-vez", action="store_true")
    args = ap.parse_args()

    _boot_env(forzar_sim=bool(args.sim))

    from core import beru_rango_balanza as balanza
    from core import igris_escudo_btc as escudo

    # Preferir env de esta sesión (viejita) sobre config cacheada al import.
    modo_env = str(os.environ.get("IGRIS_ESCUDO_BTC_MODO", "") or "").strip().lower()
    modo = "sim" if args.sim else (modo_env or "live")
    if modo != "live":
        modo = "sim"
    live_ok = escudo.escudo_live_permitido() if modo == "live" else False

    _emit("=" * 56)
    _emit("  ARISE IGRIS ESCUDO BTC")
    _emit(f"  frente={escudo.escudo_familia()} {escudo.inst_escudo_btc()}")
    _emit(
        f"  peldano=${escudo.escudo_peldaño_usd():.0f} arma@${escudo.escudo_activar_usd():.0f} "
        f"R={escudo.escudo_relacion():.2f} ord={escudo.escudo_ord_tipo()}"
    )
    _emit(f"  modo={modo} LIVE_OK={live_ok} intervalo={args.intervalo}s")
    _emit("=" * 56)

    _cargar_asiento()

    if modo == "live" and not live_ok:
        _emit("FALLO: modo live sin LIVE_OK — aborto")
        return 2

    while True:
        hora = datetime.now().strftime("%H:%M:%S")
        try:
            snap = balanza.sellar_balanza()
            try:
                from cirugias.escudo_dual.bolsa import cazadores

                saltar = cazadores()
            except Exception:
                saltar = set()
            from cirugias.radar.voz import oir_boca

            boca = oir_boca(saltar=saltar)
            if boca is None:
                cruzado, casa = _cruzar(snap, 0.0)
                _emit(f"[{hora}] boca    · sin hojas, el escudo sigue con la casa")
            else:
                cruzado, casa = _cruzar(snap, float(boca))
                _emit(
                    f"[{hora}] boca    · casa {casa:.0f} + boca {float(boca):.0f} = {cruzado:.0f}"
                )
            if cruzado >= 0:
                snap["short_usd"] = float(cruzado)
                snap["long_usd"] = 0.0
            else:
                snap["short_usd"] = 0.0
                snap["long_usd"] = abs(float(cruzado))
            snap["frase"] = f"casa {casa:.0f} + boca {float(boca or 0):.0f}"
            asiento, armado, lado_as = _proponer_asiento(cruzado)
            asiento_mano = asiento
            try:
                from cirugias.escudo_dual import tsunami

                foto = tsunami.paso(
                    tsunami.hojas_vivas(),
                    cruzado=float(cruzado),
                    path=_TSUNAMI_PATH,
                )
                _emit(f"[{hora}] {foto.get('frase')}")
                # Papel hasta que el Monarca diga despertar. Sin esta palabra el metal no se mueve.
                vivo = str(os.environ.get("IGRIS_EXTASIS", "papel") or "papel").strip().lower() == "vivo"
                if (
                    vivo
                    and foto.get("extasis")
                    and abs(float(cruzado)) > float(escudo.escudo_polvo_usd() or 0)
                ):
                    asiento_mano = float(foto.get("asiento") or 0)
                elif foto.get("extasis"):
                    _emit(
                        f"[{hora}] éxtasis · papel, el metal sigue en {asiento_mano:.0f}"
                    )
            except Exception as exc_tsu:
                _emit(f"[{hora}] tsunami · {exc_tsu}")
            # La correa vieja ya no planta. Las manos son las del rey o la reina.
            aplicar = False
            try:
                from cirugias.escudo_dual.elegir import (
                    frase_eleccion,
                    metal_de_la_siguiente,
                    relacion_vigente,
                )

                elegido = metal_de_la_siguiente()
                relacion = relacion_vigente(asiento)
                from cirugias.escudo_dual.desinflar import fraccion
                from cirugias.escudo_dual.manos import REINA as _REINA_INST

                parte, frase_def = fraccion("cripto", float(cruzado), _REINA_INST)
                asiento_def = float(asiento_mano) * parte
                _emit(
                    f"[{hora}] banda   · asiento {asiento:.0f} "
                    f"reina {relacion['reina']:.2f} rey {relacion['rey']:.2f}"
                )
                _emit(f"[{hora}] {frase_def}")
                _emit(f"[{hora}] capa    · {frase_eleccion(elegido)}")
                from cirugias.escudo_dual.ojo import ver
                from cirugias.escudo_dual.manos import REINA, REY, ajustar, sentado

                dato = ver()
                pos_reina = sentado(REINA)
                pos_rey = sentado(REY)
                if pos_reina is None or pos_rey is None:
                    _emit(f"[{hora}] capa    · un metal no se ve, no planto")
                else:
                    meta_reina, meta_rey = _reparto(
                        asiento_def,
                        pos_reina,
                        pos_rey,
                        permiso_rey=dato.get("permiso_rey"),
                        permiso_reina=dato.get("permiso_reina"),
                        relacion_rey=relacion["rey"],
                        relacion_reina=relacion["reina"],
                    )
                    frases = []
                    for nombre, inst, meta, pos in (
                        ("reina", REINA, meta_reina, pos_reina),
                        ("rey", REY, meta_rey, pos_rey),
                    ):
                        if abs(meta - pos) <= 1.0:
                            continue
                        hecho = ajustar(meta, inst)
                        frases.append(f"{nombre} {hecho.get('frase')}")
                    if not frases:
                        _sellar_asiento(asiento, armado, lado_as)
                        _emit(f"[{hora}] capas   · ya en la capa")
                    else:
                        if all("rechaz" not in f and "ciego" not in f and "sin " not in f for f in frases):
                            _sellar_asiento(asiento, armado, lado_as)
                        _emit(f"[{hora}] capas   · {' · '.join(frases)}")
                if elegido is None and abs(float(cruzado)) + 1e-9 >= escudo.escudo_activar_usd():
                    _emit(f"[{hora}] capa    · nadie acompaña, no entra capa nueva")
            except Exception as exc_ojo:
                _emit(f"[{hora}] capa    · ojo {exc_ojo}")
            lat = escudo.latido_escudo(
                snap=snap,
                ojos_live=False,
                forzar_modo=modo,
                aplicar_manos=aplicar,
            )
            frase = escudo.frase_latido(lat)
            mov = (lat.get("mover_limite") or {}).get("frase") or ""
            bal = snap.get("frase") or ""
            r_ahora = escudo.escudo_relacion()
            _emit(f"[{hora}] balanza · {bal}")
            _emit(f"[{hora}] R={r_ahora:.2f} (dinamico, viejita)")
            _emit(f"[{hora}] escudo  · {frase}")
            if mov:
                _emit(f"[{hora}] limite  · {mov}")
            manos = lat.get("manos") or {}
            if manos.get("frase") and manos.get("aplicado"):
                _emit(f"[{hora}] manos   · {manos.get('frase')}")
            elif manos.get("aviso") and not manos.get("ok"):
                _emit(f"[{hora}] manos   · {manos.get('aviso')}")
        except Exception as exc:
            _emit(f"[{hora}] error: {exc}")

        if args.una_vez:
            return 0
        time.sleep(max(10.0, float(args.intervalo)))


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\nIgris Escudo sellado.", flush=True)
        raise SystemExit(0)
