"""El éxtasis en papel. Mira lo que habría hecho el escudo. No planta.

La memoria de estas miradas no es la del escudo vivo. El asiento
tosco no se toca. Mañana se lee el diario y se decide si despierta.
"""
from __future__ import annotations

import json
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
for _salida in (sys.stdout, sys.stderr):
    try:
        _salida.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from cirugias.escudo_dual.capas import _orden_de_salida, _quien_recibe
from cirugias.escudo_dual.elegir import RELACION_LENTA, relacion_vigente
from cirugias.escudo_dual.manos import REINA, REY, sentado
from cirugias.escudo_dual.ojo import ver
from cirugias.escudo_dual import tsunami

RAIZ = Path(__file__).resolve().parents[2]
MEMORIA = RAIZ / "data" / "beru" / "escudo" / "tsunami_papel.json"
ASIENTO = RAIZ / "data" / "beru" / "escudo" / "asiento_dual.json"
DIARIO = RAIZ / "data" / "beru" / "escudo" / "extasis_papel.jsonl"
ACIERTOS = RAIZ / "data" / "beru" / "escudo" / "extasis_acierto.json"
PAUSA = 15
MIRADAS = 2
SALE = 2.0 / 3.0
PISO = 30
MOVER = 0.0015
# entra, y la parte a la que se apaga. Nueve décimos no mueve el metal:
# pide 90 a favor y se desinfla si esa parte cae de 75.
BARRAS = (
    ("tres_cuartos", 0.75, SALE),
    ("cuatro_quintos", 0.80, SALE),
    ("nueve_decimos", 0.90, 0.75),
)


def _f(valor, default: float = 0.0) -> float:
    try:
        return float(valor)
    except (TypeError, ValueError):
        return default


def _asiento_tosco() -> dict:
    try:
        data = json.loads(ASIENTO.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        return {"armado": False, "lado": "", "valor": 0.0}
    if not isinstance(data, dict):
        return {"armado": False, "lado": "", "valor": 0.0}
    return data


def _reparto(asiento: float, reina_pos: float, rey_pos: float, dato: dict) -> tuple[float, float]:
    """La misma cuenta de las capas. No manda orden."""
    rel = {"reina": float(RELACION_LENTA["reina"]), "rey": float(RELACION_LENTA["rey"])}
    permiso_rey = dato.get("permiso_rey")
    permiso_reina = dato.get("permiso_reina")
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


def _vacio_barra() -> dict:
    return {
        "seguidas": 0,
        "color": "",
        "encendido": False,
        "abiertos": [],
        "quince": {"acierto": 0, "falso": 0, "quieto": 0},
        "hora": {"acierto": 0, "falso": 0, "quieto": 0},
    }


def _libro() -> dict:
    try:
        dato = json.loads(ACIERTOS.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        dato = {}
    if not isinstance(dato, dict):
        dato = {}
    for nombre, _entra, _sale in BARRAS:
        if not isinstance(dato.get(nombre), dict):
            dato[nombre] = _vacio_barra()
    return dato


def _guardar_libro(dato: dict) -> None:
    ACIERTOS.parent.mkdir(parents=True, exist_ok=True)
    ACIERTOS.write_text(json.dumps(dato), encoding="utf-8")


def _retorno(antes: dict, ahora: dict) -> float | None:
    movimientos = []
    for nombre, viejo in antes.items():
        nuevo = ahora.get(nombre)
        if not viejo or not nuevo or float(viejo) <= 0 or float(nuevo) <= 0:
            continue
        movimientos.append(float(nuevo) / float(viejo) - 1.0)
    if len(movimientos) < 3:
        return None
    return sum(movimientos) / len(movimientos)


def _juicio(mov: float | None, color: str) -> str | None:
    if mov is None or color not in ("verde", "roja"):
        return None
    if abs(mov) < MOVER:
        return "quieto"
    a_favor = mov < 0 if color == "roja" else mov > 0
    return "acierto" if a_favor else "falso"


def _mirar_barra(
    barra: dict,
    verde: int,
    roja: int,
    ultimos: dict,
    ahora: float,
    entra: float,
    sale: float,
) -> bool:
    total = verde + roja
    if total < PISO or len(ultimos) < 3:
        barra["seguidas"] = 0
        barra["color"] = ""
        barra["encendido"] = False
    else:
        parte_verde = verde / total
        parte_roja = roja / total
        if parte_verde + 1e-12 >= entra:
            color = "verde"
        elif parte_roja + 1e-12 >= entra:
            color = "roja"
        else:
            color = ""
        if barra.get("encendido"):
            cual = str(barra.get("color") or "")
            parte = parte_verde if cual == "verde" else parte_roja if cual == "roja" else 0
            if cual not in ("verde", "roja") or parte + 1e-12 < sale:
                barra["encendido"] = False
                barra["seguidas"] = 0
                barra["color"] = ""
        elif not color:
            barra["seguidas"] = 0
            barra["color"] = ""
        else:
            if color == barra.get("color"):
                barra["seguidas"] = int(barra.get("seguidas") or 0) + 1
            else:
                barra["color"] = color
                barra["seguidas"] = 1
            if int(barra["seguidas"]) >= MIRADAS:
                barra["encendido"] = True
                barra["abiertos"].append(
                    {
                        "ts": ahora,
                        "color": color,
                        "ultimos": dict(ultimos),
                        "quince": "",
                        "hora": "",
                    }
                )
    quedan = []
    for caso in list(barra.get("abiertos") or []):
        if not isinstance(caso, dict):
            continue
        edad = ahora - float(caso.get("ts") or ahora)
        mov = _retorno(caso.get("ultimos") or {}, ultimos)
        for nombre, segundos in (("quince", 15 * 60), ("hora", 60 * 60)):
            if caso.get(nombre):
                continue
            if edad + 1e-9 < segundos:
                continue
            voto = _juicio(mov, str(caso.get("color") or ""))
            if voto:
                caso[nombre] = voto
                barra[nombre][voto] = int(barra[nombre].get(voto) or 0) + 1
        if not caso.get("hora"):
            quedan.append(caso)
    barra["abiertos"] = quedan[-40:]
    return bool(barra.get("encendido"))


def latido() -> dict:
    from core import beru_rango_balanza as balanza
    from core.igris_escudo_btc import escudo_polvo_usd
    from cirugias.radar.voz import oir_boca

    snap = balanza.medir_balanza()
    try:
        from cirugias.escudo_dual.bolsa import cazadores

        saltar = cazadores()
    except Exception:
        saltar = set()
    boca = oir_boca(saltar=saltar)
    casa = _f(snap.get("short_usd")) - _f(snap.get("long_usd"))
    cruzado = casa if boca is None else casa + float(boca)
    sentado_archivo = _asiento_tosco()
    from cirugias.escudo_dual.elegir import asiento_en_banda

    tosco, _, _ = asiento_en_banda(
        cruzado,
        armado=bool(sentado_archivo.get("armado")),
        lado=str(sentado_archivo.get("lado") or ""),
        valor=_f(sentado_archivo.get("valor")) if sentado_archivo.get("armado") else None,
    )
    hojas = tsunami.hojas_vivas()
    foto = tsunami.paso(hojas, cruzado=float(cruzado), path=MEMORIA)
    reina_ahora = sentado(REINA)
    rey_ahora = sentado(REY)
    dato = ver()
    reina_tosca = rey_tosca = None
    if reina_ahora is not None and rey_ahora is not None:
        reina_tosca, rey_tosca = _reparto(float(tosco), reina_ahora, rey_ahora, dato)
    verde = int(foto.get("verde") or 0)
    roja = int(foto.get("roja") or 0)
    ultimos = dato.get("ultimos") if isinstance(dato.get("ultimos"), dict) else {}
    ahora = time.time()
    libro = _libro()
    marcas = {}
    for nombre, entra, sale in BARRAS:
        marcas[nombre] = _mirar_barra(
            libro[nombre], verde, roja, ultimos, ahora, entra, sale
        )
    _guardar_libro(libro)
    color = str(libro["tres_cuartos"].get("color") or "") if marcas["tres_cuartos"] else ""
    promesa = tsunami._promesa(hojas, color, ahora) if color else 0.0
    # La reina es el metal sentado. Su relacion queda en las monedas.
    # La promesa no se multiplica.
    relacion = relacion_vigente(float(tosco))
    destino = float(tosco)
    if marcas["tres_cuartos"] and abs(cruzado) > float(escudo_polvo_usd() or 0):
        destino = tsunami.metal_promesa_uno(
            float(cruzado),
            promesa,
            color,
            float(relacion["reina"]),
        )
    reina_papel = destino
    if reina_ahora is not None and destino and (reina_ahora > 0) != (destino > 0):
        reina_papel = 0.0
    return {
        "ts": ahora,
        "hora": datetime.now().strftime("%H:%M:%S"),
        "modo": "papel",
        "metal": "no tocado",
        "correccion": "promesa peso por peso",
        "relacion_fija": {"rey": relacion["rey"], "reina": relacion["reina"]},
        "relacion_ventana": dato.get("relaciones"),
        "boca": None if boca is None else round(float(boca), 1),
        "casa": round(casa, 1),
        "cruzado": round(cruzado, 1),
        "tosco": round(float(tosco), 1),
        "extasis": bool(marcas["tres_cuartos"]),
        "cuatro_quintos": bool(marcas["cuatro_quintos"]),
        "nueve_decimos": bool(marcas["nueve_decimos"]),
        "color": color if marcas["tres_cuartos"] else "",
        "verde": verde,
        "roja": roja,
        "miradas": int(foto.get("seguidas") or 0),
        "promesa": round(promesa, 1),
        "asiento_extasis": None if foto.get("asiento") is None else round(_f(foto.get("asiento")), 1),
        "mano": round(float(destino), 1),
        "reina_ahora": None if reina_ahora is None else round(float(reina_ahora), 1),
        "reina_papel": None if reina_papel is None else round(float(reina_papel), 1),
        "rey_ahora": None if rey_ahora is None else round(float(rey_ahora), 1),
        "rey_papel": None if rey_tosca is None else round(float(rey_tosca), 1),
        "reina_tosca": None if reina_tosca is None else round(float(reina_tosca), 1),
        "acierto": {
            nombre: {
                "quince": libro[nombre]["quince"],
                "hora": libro[nombre]["hora"],
            }
            for nombre, _entra, _sale in BARRAS
        },
        "frase": foto.get("frase") or "",
    }


def _anotar(fila: dict) -> None:
    DIARIO.parent.mkdir(parents=True, exist_ok=True)
    with DIARIO.open("a", encoding="utf-8") as libro:
        libro.write(json.dumps(fila, ensure_ascii=False) + "\n")
    print(
        f"PAPEL {fila['hora']} {fila['frase']} · 4/5 {int(bool(fila.get('cuatro_quintos')))} · "
        f"9/10 {int(bool(fila.get('nueve_decimos')))} · "
        f"tosco {fila['tosco']} · mano {fila['mano']} · reina {fila['reina_ahora']} a {fila['reina_papel']}",
        flush=True,
    )


def main() -> None:
    print("EXTASIS_PAPEL el metal no se mueve", flush=True)
    while True:
        try:
            _anotar(latido())
        except Exception as exc:
            print(f"papel calla {exc}", flush=True)
        time.sleep(PAUSA)


if __name__ == "__main__":
    main()
