#!/usr/bin/env python3
"""Manto de la bolsa. Misma ley que el de las monedas. Papel hasta decirlo.

Rey: el índice grande. Reina: la rápida. Las dos son lineales.
No pisa el sello ni el asiento del manto de las monedas.
No despierta cazadores.
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

_LOG = ROOT / "data" / "logs" / "arise_igris_escudo_bolsa_out.log"
_ASIENTO = ROOT / "data" / "beru" / "escudo" / "asiento_bolsa.json"
_SELLO = ROOT / "data" / "beru" / "escudo" / "relacion_sello_bolsa.json"
_MEMORIA = {"armado": False, "lado": "", "valor": 0.0}


def _emit(msg: str) -> None:
    print(msg, flush=True)
    if os.environ.get("IGRIS_BOLSA_LOG_SOLO_STDOUT", "").strip().lower() in (
        "1", "true", "yes", "on", "si",
    ):
        return
    try:
        _LOG.parent.mkdir(parents=True, exist_ok=True)
        with _LOG.open("a", encoding="utf-8") as fh:
            fh.write(msg + "\n")
    except OSError:
        pass


def _cargar() -> None:
    try:
        data = json.loads(_ASIENTO.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        return
    _MEMORIA["armado"] = bool(data.get("armado"))
    _MEMORIA["lado"] = str(data.get("lado") or "")
    _MEMORIA["valor"] = float(data.get("valor") or 0)


def _guardar(valor: float, armado: bool, lado: str) -> None:
    _MEMORIA["valor"] = float(valor)
    _MEMORIA["armado"] = bool(armado)
    _MEMORIA["lado"] = str(lado or "")
    try:
        _ASIENTO.parent.mkdir(parents=True, exist_ok=True)
        _ASIENTO.write_text(json.dumps(_MEMORIA), encoding="utf-8")
    except OSError:
        pass


def _reparto(asiento, reina_pos, rey_pos, *, permiso_rey, permiso_reina, relacion_rey, relacion_reina):
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


def main() -> int:
    ap = argparse.ArgumentParser(description="Manto de la bolsa")
    ap.add_argument("--intervalo", type=float, default=15.0)
    ap.add_argument("--vivo", action="store_true", help="Manos reales. Exige IGRIS_BOLSA_LIVE_OK=1")
    ap.add_argument("--una-vez", action="store_true")
    args = ap.parse_args()
    vivo = bool(args.vivo) and str(os.environ.get("IGRIS_BOLSA_LIVE_OK", "") or "") == "1"

    from cirugias.escudo_dual.bolsa import REINA, REY, cazadores
    from cirugias.escudo_dual.elegir import asiento_en_banda, relacion_vigente
    from cirugias.escudo_dual.ojo_bolsa import ver
    from core import beru_rango_balanza as balanza

    _emit("=" * 56)
    _emit("  MANTO DE LA BOLSA")
    _emit(f"  reina={REINA} rey={REY}")
    _emit(f"  manos={'vivas' if vivo else 'papel'} intervalo={args.intervalo}s")
    _emit("=" * 56)
    _cargar()

    while True:
        hora = datetime.now().strftime("%H:%M:%S")
        try:
            try:
                snap = balanza.sellar_balanza_bolsa()
            except Exception as exc:
                _emit(f"[{hora}] casa   · ciega, no planto ({exc})")
                if args.una_vez:
                    return 0
                time.sleep(max(10.0, float(args.intervalo)))
                continue
            casa = float(snap.get("short_usd") or 0) - float(snap.get("long_usd") or 0)
            boca_bolsa = oir_boca_solo(cazadores())
            cruzado = casa if boca_bolsa is None else casa + float(boca_bolsa)
            _emit(
                f"[{hora}] casa   · {casa:.0f}"
                + ("" if boca_bolsa is None else f" + boca {float(boca_bolsa):.0f}")
                + f" = {cruzado:.0f}"
            )
            asiento, armado, lado = asiento_en_banda(
                cruzado,
                armado=bool(_MEMORIA["armado"]),
                lado=str(_MEMORIA["lado"] or ""),
                valor=_MEMORIA["valor"] if _MEMORIA["armado"] else None,
            )
            relacion = relacion_vigente(asiento, _SELLO)
            from cirugias.escudo_dual.desinflar import fraccion

            parte, frase_def = fraccion("bolsa", float(cruzado), REINA)
            asiento_def = float(asiento) * parte
            try:
                dato = ver()
            except Exception:
                dato = {}
            _emit(
                f"[{hora}] banda  · asiento {asiento:.0f} "
                f"reina {relacion['reina']:.2f} rey {relacion['rey']:.2f}"
            )
            _emit(f"[{hora}] {frase_def}")
            if not vivo:
                _guardar(asiento, armado, lado)
                _emit(f"[{hora}] papel  · no planto")
            else:
                from cirugias.escudo_dual.manos_bolsa import ajustar, sentado

                pos_reina = sentado(REINA)
                pos_rey = sentado(REY)
                if pos_reina is None or pos_rey is None:
                    _emit(f"[{hora}] capa   · un metal no se ve, no planto")
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
                    if frases and all(
                        "rechaz" not in f and "ciego" not in f and "sin " not in f for f in frases
                    ):
                        _guardar(asiento, armado, lado)
                    elif not frases:
                        _guardar(asiento, armado, lado)
                        frases.append("ya en la capa")
                    _emit(f"[{hora}] capas  · {' · '.join(frases)}")
        except Exception as exc:
            _emit(f"[{hora}] error: {exc}")
        if args.una_vez:
            return 0
        time.sleep(max(10.0, float(args.intervalo)))


def oir_boca_solo(queda: set[str]) -> float | None:
    """Solo las hojas de esta casa. None si ninguna habla."""
    import json as _json

    from core.beru_rango_paths import RANGO_DIR

    if not RANGO_DIR.is_dir():
        return None
    vistos = 0
    total = 0.0
    for inf in RANGO_DIR.glob("*/manos_piedra_informe.json"):
        nombre = inf.parent.name.upper()
        if nombre not in queda:
            continue
        try:
            data = _json.loads(inf.read_text(encoding="utf-8"))
        except (OSError, _json.JSONDecodeError, TypeError, ValueError):
            continue
        vivo = data.get("vivo")
        if not isinstance(vivo, dict):
            vivo = (data.get("snapshot") or {}).get("vivo")
        if not isinstance(vivo, dict) or "voz_intencion" not in vivo:
            continue
        vistos += 1
        total += float(vivo.get("voz_intencion") or 0)
    if vistos == 0:
        return None
    return float(total)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\nManto de la bolsa sellado.", flush=True)
        raise SystemExit(0)
