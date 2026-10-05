"""Tsunami y éxtasis. El escudo vivo no entra aquí hasta que el Monarca lo despierte.

Debajo de la última cosecha la bandera es verde: espera long.
Encima es roja: espera short. El que no recuerda cosecha se calla.
El dormido, con la bandera quieta un día entero, no vota.
El que caza sí vota, aunque lleve rato con el mismo color.

Entra si tres cuartos del mismo color se sostienen dos miradas.
Sale si ese color cae de dos tercios. Con menos de treinta voces, no hay tsunami.

En el éxtasis el escalón de quinientos se quita. La bolsa se sienta
en el cruce exacto, y la masa prometida —la que todavía no está en la
boca— se suma o se resta. No cruza el cero en el mismo latido.
La relación del rey o de la reina la pone el reparto, no esta cuenta.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

DIA = 86400.0
HOJA_FRESCA = 180.0
PISO_VOTOS = 30
ENTRA = 0.75
SALE = 2.0 / 3.0
MIRADAS = 2
MEMORIA_VIVA = 300.0

_MEMORIA = {"color": "", "seguidas": 0, "extasis": False, "ts": 0.0}


def marcar_bandera(beru, precio: float, ahora: float | None = None) -> str:
    """La deja puesta en el cazador. La hoja la publica después."""
    cosecha = float(getattr(beru, "ultima_hoz_tocada_precio", 0) or 0)
    px = float(precio or 0)
    cuando = float(ahora if ahora is not None else time.time())
    if cosecha <= 0 or px <= 0 or px == cosecha:
        beru.bandera_tsunami = ""
        beru.masa_tsunami = 0.0
        return ""
    color = "verde" if px < cosecha else "roja"
    previa = str(getattr(beru, "bandera_tsunami", "") or "")
    if color != previa or float(getattr(beru, "bandera_desde", 0) or 0) <= 0:
        beru.bandera_tsunami = color
        beru.bandera_desde = cuando
    else:
        beru.bandera_tsunami = color
    beru.masa_tsunami = _masa_de_la_oz(beru, color)
    return color


def _masa_de_la_oz(beru, color: str) -> float:
    """La Oz del llamado. Si ya está cazando ese lado, ya va en la mente."""
    estado = str(getattr(beru, "estado", "") or "").upper()
    lado = str(getattr(beru, "direccion", "") or "").upper()
    mismo = (color == "verde" and lado == "LONG") or (color == "roja" and lado == "SHORT")
    if estado == "CAZANDO" and mismo:
        return 0.0
    from core.beru_rango import masa_al_llamado

    return max(0.0, float(masa_al_llamado(beru) or 0))


def vota(hoja: dict, ahora: float) -> bool:
    """Una hoja. El informe viejo no vota. El dormido de un día tampoco."""
    ts = float(hoja.get("ts") or 0)
    if ts <= 0 or ahora - ts > HOJA_FRESCA:
        return False
    vivo = hoja.get("vivo") if isinstance(hoja.get("vivo"), dict) else {}
    if not vivo and isinstance(hoja.get("snapshot"), dict):
        vivo = hoja["snapshot"].get("vivo") or {}
    if not isinstance(vivo, dict):
        return False
    color = str(vivo.get("bandera_tsunami") or "")
    if color not in ("verde", "roja"):
        return False
    if str(vivo.get("estado") or "").upper() == "CAZANDO":
        return True
    desde = float(vivo.get("bandera_desde") or 0)
    if desde <= 0:
        return False
    return ahora - desde < DIA


def asiento_en_extasis(cruzado: float, promesa: float, color: str) -> float:
    """El cruce al dólar, más o menos la promesa. No pasa al otro lado."""
    n = float(cruzado or 0)
    if abs(n) < 1e-9 or color not in ("verde", "roja"):
        return 0.0
    signo = 1.0 if n > 0 else -1.0
    mismo_lado = (signo > 0 and color == "roja") or (signo < 0 and color == "verde")
    mag = abs(n)
    p = max(0.0, float(promesa or 0))
    if mismo_lado:
        mag += p
    else:
        mag = max(0.0, mag - p)
    return signo * mag


def metal_promesa_uno(cruzado: float, promesa: float, color: str, relacion: float) -> float:
    """Las monedas de ahora, por la relación. La promesa, peso por peso.

    No cruza al otro lado en el mismo latido. El papel lo usa.
    El escudo vivo, todavía no.
    """
    n = float(cruzado or 0)
    if abs(n) < 1e-9 or color not in ("verde", "roja"):
        return 0.0
    signo = 1.0 if n > 0 else -1.0
    mismo_lado = (signo > 0 and color == "roja") or (signo < 0 and color == "verde")
    base = abs(n) * max(0.0, float(relacion or 0))
    p = max(0.0, float(promesa or 0))
    if mismo_lado:
        mag = base + p
    else:
        mag = max(0.0, base - p)
    return signo * mag


def _mirar(verde: int, roja: int) -> None:
    total = verde + roja
    if total < PISO_VOTOS:
        _MEMORIA["color"] = ""
        _MEMORIA["seguidas"] = 0
        _MEMORIA["extasis"] = False
        return
    if verde / total + 1e-12 >= ENTRA:
        color = "verde"
    elif roja / total + 1e-12 >= ENTRA:
        color = "roja"
    else:
        color = ""
    if _MEMORIA["extasis"]:
        cual = str(_MEMORIA["color"] or "")
        parte = verde if cual == "verde" else roja if cual == "roja" else 0
        if cual not in ("verde", "roja") or parte / total + 1e-12 < SALE:
            _MEMORIA["color"] = ""
            _MEMORIA["seguidas"] = 0
            _MEMORIA["extasis"] = False
        return
    if not color:
        _MEMORIA["color"] = ""
        _MEMORIA["seguidas"] = 0
        return
    if color == _MEMORIA["color"]:
        _MEMORIA["seguidas"] = int(_MEMORIA["seguidas"]) + 1
    else:
        _MEMORIA["color"] = color
        _MEMORIA["seguidas"] = 1
    if int(_MEMORIA["seguidas"]) >= MIRADAS:
        _MEMORIA["extasis"] = True


def _promesa(hojas: list[dict], color: str, ahora: float) -> float:
    if color not in ("verde", "roja"):
        return 0.0
    total = 0.0
    for hoja in hojas:
        if not vota(hoja, ahora):
            continue
        vivo = hoja.get("vivo") if isinstance(hoja.get("vivo"), dict) else {}
        if not vivo and isinstance(hoja.get("snapshot"), dict):
            vivo = hoja["snapshot"].get("vivo") or {}
        if str((vivo or {}).get("bandera_tsunami") or "") != color:
            continue
        total += max(0.0, float((vivo or {}).get("masa_tsunami") or 0))
    return total


def _cargar(path: Path, ahora: float) -> None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        return
    ts = float(data.get("ts") or 0)
    if ts <= 0 or ahora - ts > MEMORIA_VIVA:
        return
    _MEMORIA["color"] = str(data.get("color") or "")
    _MEMORIA["seguidas"] = int(data.get("seguidas") or 0)
    _MEMORIA["extasis"] = bool(data.get("extasis"))
    _MEMORIA["ts"] = ts


def _guardar(path: Path, ahora: float) -> None:
    _MEMORIA["ts"] = ahora
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(_MEMORIA), encoding="utf-8")
    except OSError:
        pass


def paso(
    hojas: list[dict],
    *,
    cruzado: float,
    ahora: float | None = None,
    path: Path | None = None,
) -> dict:
    """Una mirada. No manda orden. El asiento tosco no se pisa aquí."""
    cuando = float(ahora if ahora is not None else time.time())
    if path is not None and _MEMORIA["ts"] <= 0:
        _cargar(path, cuando)
    verde = 0
    roja = 0
    for hoja in hojas:
        if not vota(hoja, cuando):
            continue
        vivo = hoja.get("vivo") if isinstance(hoja.get("vivo"), dict) else {}
        if not vivo and isinstance(hoja.get("snapshot"), dict):
            vivo = hoja["snapshot"].get("vivo") or {}
        color = str((vivo or {}).get("bandera_tsunami") or "")
        if color == "verde":
            verde += 1
        elif color == "roja":
            roja += 1
    _mirar(verde, roja)
    color = str(_MEMORIA["color"] or "") if _MEMORIA["extasis"] else ""
    promesa = _promesa(hojas, color, cuando) if _MEMORIA["extasis"] else 0.0
    asiento = asiento_en_extasis(cruzado, promesa, color) if _MEMORIA["extasis"] else None
    if path is not None:
        _guardar(path, cuando)
    return {
        "extasis": bool(_MEMORIA["extasis"]),
        "color": color,
        "verde": verde,
        "roja": roja,
        "seguidas": int(_MEMORIA["seguidas"]),
        "promesa": promesa,
        "asiento": asiento,
        "frase": _frase(verde, roja, promesa, asiento),
    }


def _frase(verde: int, roja: int, promesa: float, asiento: float | None) -> str:
    if not _MEMORIA["extasis"]:
        return (
            f"tsunami · verde {verde} roja {roja}, mirada {_MEMORIA['seguidas']}, "
            "el escudo sigue tosco"
        )
    return (
        f"éxtasis {_MEMORIA['color']} · verde {verde} roja {roja} · "
        f"promesa {promesa:.0f} · bolsa {float(asiento or 0):.0f}"
    )


def hojas_vivas() -> list[dict]:
    """Las hojas del campamento. El rey del escudo no vota."""
    from core.beru_rango_paths import RANGO_DIR

    if not RANGO_DIR.is_dir():
        return []
    hojas = []
    for inf in RANGO_DIR.glob("*/manos_piedra_informe.json"):
        if inf.parent.name.upper() == "BTC":
            continue
        try:
            data = json.loads(inf.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            continue
        if isinstance(data, dict):
            hojas.append(data)
    return hojas


def olvidar_memoria() -> None:
    """Solo el papel. El vivo no la llama."""
    _MEMORIA["color"] = ""
    _MEMORIA["seguidas"] = 0
    _MEMORIA["extasis"] = False
    _MEMORIA["ts"] = 0.0
