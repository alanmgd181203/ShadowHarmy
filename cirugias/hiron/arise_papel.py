"""El papel junto a unos pocos, y el hacha de Iron.

Cuando la Oz ya se tocó, cierra solo lo condenado, y nunca más de lo
que queda. No abre una bolsa nueva. Igris no se toca.
"""
from __future__ import annotations

import json
import sys
import time
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from cirugias.hiron.masacre_precio import Sello, caja_con_lo_realizado, distancia_activador
from cirugias.hiron.subida import Subida
from cirugias.hiron.papel import cuenta_de_la_pierna, ganancia_de_la_pierna
from cirugias.hiron.viaje import Viaje

# Los primeros. El resto entra de a pocos, cuando el precio ya se alejó del quiebre.
FIJOS = ("LINK", "AZTEC", "CASHCAT", "GRASS", "FET")
NUEVOS_POR_LATIDO = 40
LEJOS_PARA_MIRAR = 0.012
RAIZ = Path(__file__).resolve().parents[2]
DIARIO = RAIZ / "data" / "beru" / "papel" / "latido.json"
PAUSA = 60


def _f(valor, default: float = 0.0) -> float:
    try:
        return float(valor)
    except (TypeError, ValueError):
        return default


def _color(activo: str) -> str:
    inf = RAIZ / "data" / "beru" / "rango" / activo / "manos_piedra_informe.json"
    try:
        geo = (json.loads(inf.read_text(encoding="utf-8")).get("snapshot") or {}).get("geometria") or {}
        red = float(geo.get("red_activacion_long_pct") or 0)
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        return "amarillo"
    if abs(red - 0.007) < 1e-6:
        return "verde"
    if abs(red - 0.014) < 1e-6:
        return "rojo"
    return "amarillo"


def _fills(okx, inst: str, desde_ms: int) -> list[dict]:
    """Órdenes ya hechas desde que nació esta posición. Solo lectura."""
    vistos: list[dict] = []
    after = ""
    for _ in range(40):
        params = {
            "instType": "SWAP",
            "instId": inst,
            "begin": str(desde_ms),
            "limit": "100",
        }
        if after:
            params["after"] = after
        batch = list(okx.get_private("/api/v5/trade/fills-history", params=params) or [])
        if not batch:
            break
        vistos.extend(x for x in batch if isinstance(x, dict))
        after = str(batch[-1].get("billId") or batch[-1].get("tradeId") or "")
        if len(batch) < 100 or not after:
            break
        time.sleep(0.15)
    vistos.sort(key=lambda fila: int(fila.get("ts") or 0))
    return vistos, len(vistos) >= 4000


def _talla(okx, inst: str) -> float:
    """Monedas de un contrato, las de la casa. No el estimado del notional."""
    pub = okx.get_public(
        "/api/v5/public/instruments",
        params={"instType": "SWAP", "instId": inst},
    ) or []
    if not pub or not isinstance(pub[0], dict):
        return 0.0
    return _f(pub[0].get("ctVal"))


def _afeitar_puerta(piezas: list[dict], pos: float) -> bool:
    """La orden del nacimiento a veces cierra el lado viejo y abre este.

    Ese cierre no es pierna de ahora. Solo se recorta en ese instante.
    Si el hueco no cabe ahí, no se inventa el resto.
    """
    if not piezas:
        return False
    neto = 0.0
    for pieza in piezas:
        neto += pieza["qty"] if pieza["lado"] == "buy" else -pieza["qty"]
    if pos < 0:
        sobra = pos - neto
        abre = "sell"
    else:
        sobra = neto - pos
        abre = "buy"
    if sobra < -1e-8:
        return False
    if sobra <= 1e-8:
        return True
    puerta = min(pieza["ts"] for pieza in piezas)
    queda = sobra
    for pieza in piezas:
        if pieza["ts"] != puerta or pieza["lado"] != abre:
            continue
        recorte = min(pieza["qty"], queda)
        pieza["qty"] -= recorte
        queda -= recorte
        if queda <= 1e-8:
            return True
    return False


def _sello_de_subida(activo: str, lado: str, color: str, suelo: float) -> str | None:
    """La prisa, sellada al tocar el suelo. Si todavía no lo toca, no hay clase.

    El cero es la última Oz que quedó antes del suelo. No pone orden.
    """
    if suelo <= 0:
        return None
    ruta = RAIZ / "data" / "beru" / "rango" / activo / "manos_piedra_eventos.jsonl"
    if not ruta.is_file():
        return None
    ancla = None
    for linea in ruta.read_text(encoding="utf-8", errors="replace").splitlines():
        if "OZ_COSECHA" not in linea:
            continue
        try:
            row = json.loads(linea)
        except json.JSONDecodeError:
            continue
        if row.get("evento") != "OZ_COSECHA":
            continue
        det = row.get("detalle") or {}
        if str(det.get("dir") or "").upper() != lado:
            continue
        px = _f(det.get("fill"))
        ts = _f(row.get("ts"))
        if px <= 0 or ts <= 0:
            continue
        if lado == "SHORT" and px <= suelo:
            continue
        if lado == "LONG" and px >= suelo:
            continue
        if ancla is None or ts >= ancla[0]:
            ancla = (ts, px)
    if ancla is None:
        return None
    try:
        camino = _mechas(f"{activo}-USDT-SWAP", int(ancla[0] * 1000), int(time.time() * 1000))
    except Exception:
        return None
    subida = Subida(color, lado)
    subida.anclar_oz(ancla[1])
    subida.anclar_meta(suelo)
    for paso in camino:
        subida.ver(paso)
    return subida.clase()


def _mechas(inst: str, desde_ms: int, hasta_ms: int) -> list[float]:
    import urllib.request

    puntos: list[tuple[int, float, float, float, float]] = []
    cursor = hasta_ms + 60_000
    for _ in range(90):
        url = (
            "https://www.okx.com/api/v5/market/history-candles"
            f"?instId={inst}&bar=1m&limit=100&after={cursor}"
        )
        req = urllib.request.Request(url, headers={"User-Agent": "ShadowHarmy-subida"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        filas = data.get("data") or []
        if not filas:
            break
        viejo = None
        for fila in filas:
            ts = int(fila[0])
            abre, alto, bajo, cierra = (float(fila[1]), float(fila[2]), float(fila[3]), float(fila[4]))
            viejo = ts if viejo is None else min(viejo, ts)
            if desde_ms <= ts <= hasta_ms and cierra > 0:
                puntos.append((ts, abre, alto, bajo, cierra))
        if viejo is None or viejo <= desde_ms:
            break
        cursor = viejo
    puntos.sort()
    camino: list[float] = []
    visto: set[int] = set()
    for ts, abre, alto, bajo, cierra in puntos:
        if ts in visto:
            continue
        visto.add(ts)
        if cierra >= abre:
            camino.extend((abre, bajo, alto, cierra))
        else:
            camino.extend((abre, alto, bajo, cierra))
    return camino


def _mira_iron(
    lado: str,
    suelo: float | None,
    marca: float,
    clase: str | None = None,
) -> dict:
    """Si nacería, y dónde sentaría la Oz. Nacer no cierra. No hay orden."""
    mira = {
        "lejos": None,
        "cierra": 0,
        "ordenes": 0,
        "clase": clase,
        "estado": "sin suelo",
    }
    if not suelo or suelo <= 0 or marca <= 0:
        return mira
    if lado == "SHORT":
        lejos = (float(suelo) - marca) / float(suelo)
    else:
        lejos = (marca - float(suelo)) / float(suelo)
    mira["lejos"] = round(lejos, 4)
    nombres = (clase,) if clase in ("dificil", "normal", "limpia") else ("dificil", "normal", "limpia")
    gap_sello = None
    nace_sello = False
    for nombre in nombres:
        gap = distancia_activador(nombre)
        nace = gap is not None and lejos + 1e-12 >= gap
        mira[f"nace_{nombre}"] = nace
        if nace and gap is not None:
            factor = (1.0 + gap) if lado == "SHORT" else (1.0 - gap)
            mira[f"oz_{nombre}"] = round(marca * factor, 8)
        if nombre == clase:
            gap_sello = gap
            nace_sello = nace
    if clase in ("dificil", "normal", "limpia"):
        if lejos < 0:
            mira["estado"] = f"subida {clase}, antes del suelo"
        elif not nace_sello:
            mira["estado"] = f"subida {clase}, aun no nace"
        else:
            cuanto = "" if gap_sello is None else f" a {round(gap_sello * 100, 1)}"
            mira["estado"] = f"subida {clase}, oz{cuanto} detras, no cierra"
        return mira
    if lejos < 0:
        mira["estado"] = "antes del suelo"
    elif not mira.get("nace_dificil"):
        mira["estado"] = "en el suelo, aun no nace"
    elif mira.get("nace_limpia"):
        mira["estado"] = "naceria, la oz detras, no cierra"
    else:
        mira["estado"] = "naceria solo si la subida no fue limpia"
    return mira


def _iron_vivo(
    memoria: dict,
    activo: str,
    nacimiento: int,
    lado: str,
    color: str,
    suelo: float | None,
    marca: float,
    monedas: float,
) -> dict:
    """Recuerda la prisa y la Oz. No la planta y no cierra."""
    clave = f"{activo}:{int(nacimiento)}"
    previo = memoria.get(clave) if isinstance(memoria.get(clave), dict) else {}
    clase = previo.get("clase") if previo.get("clase") in ("dificil", "normal", "limpia") else None
    en_terreno = False
    if suelo and marca > 0:
        if lado == "SHORT":
            en_terreno = marca <= float(suelo)
        else:
            en_terreno = marca >= float(suelo)
    if clase is None and suelo and en_terreno:
        try:
            clase = _sello_de_subida(activo, lado, color, float(suelo))
        except Exception:
            clase = None
    quieto = bool(previo.get("quieto")) and _f(previo.get("suelo")) > 0
    suelo_uso = _f(previo.get("suelo")) if quieto else suelo
    gap = distancia_activador(clase) if clase else None
    lejos = None
    if suelo_uso and marca > 0:
        if lado == "SHORT":
            lejos = (float(suelo_uso) - marca) / float(suelo_uso)
        else:
            lejos = (marca - float(suelo_uso)) / float(suelo_uso)
    nace = gap is not None and lejos is not None and lejos + 1e-12 >= gap
    nota = {
        "clase": clase,
        "quieto": quieto,
        "suelo": None if not suelo_uso else float(suelo_uso),
        "nacido": bool(previo.get("nacido")),
        "extremo": _f(previo.get("extremo")),
        "oz": _f(previo.get("oz")),
        "condenadas": _f(previo.get("condenadas")),
        "tocada": bool(previo.get("tocada")),
    }
    if nace and not nota["quieto"] and suelo_uso and gap is not None:
        factor = (1.0 + gap) if lado == "SHORT" else (1.0 - gap)
        nota.update(
            {
                "quieto": True,
                "suelo": float(suelo_uso),
                "nacido": True,
                "extremo": marca,
                "oz": marca * factor,
                "condenadas": abs(monedas),
                "tocada": False,
            }
        )
    elif nota["nacido"] and gap is not None and marca > 0:
        extremo = nota["extremo"] or marca
        if lado == "SHORT" and marca < extremo:
            extremo = marca
        if lado == "LONG" and marca > extremo:
            extremo = marca
        factor = (1.0 + gap) if lado == "SHORT" else (1.0 - gap)
        oz = extremo * factor
        tocada = nota["tocada"]
        if not tocada:
            if lado == "SHORT" and marca >= oz * (1.0 - 1e-12):
                tocada = True
            if lado == "LONG" and marca <= oz * (1.0 + 1e-12):
                tocada = True
        nota.update({"extremo": extremo, "oz": oz, "tocada": tocada, "quieto": True})
    memoria[clave] = {
        "clase": nota["clase"],
        "quieto": nota["quieto"],
        "suelo": None if not nota["suelo"] else round(float(nota["suelo"]), 8),
        "nacido": nota["nacido"],
        "extremo": None if not nota["extremo"] else round(float(nota["extremo"]), 8),
        "oz": None if not nota["oz"] else round(float(nota["oz"]), 8),
        "condenadas": None if not nota["condenadas"] else round(float(nota["condenadas"]), 6),
        "tocada": nota["tocada"],
        "cortado": bool(previo.get("cortado")),
        "orden": previo.get("orden") or "",
        "confia": bool(previo.get("confia")),
    }
    mira = _mira_iron(lado, suelo_uso, marca, clase if nota["quieto"] or clase else clase)
    if nota["nacido"] and nota["oz"]:
        nombre = clase or "limpia"
        mira[f"oz_{nombre}"] = round(float(nota["oz"]), 8)
        mira["extremo"] = round(float(nota["extremo"] or marca), 8)
        mira["cierra"] = 0
        if nota["tocada"]:
            queda = abs(monedas)
            techo = float(nota["condenadas"] or queda)
            mira["cerraria"] = round(min(queda, techo), 6)
            mira["estado"] = "ya corto" if previo.get("cortado") else "la oz tocada, el hacha cae"
        else:
            mira["estado"] = f"subida {clase}, oz detras del extremo, no cierra"
    return mira


def _uno(okx, activo: str, fila: dict, memoria: dict) -> dict:
    inst = f"{activo}-USDT-SWAP"
    pos = _f(fila.get("pos"))
    marca = _f(fila.get("markPx") or fila.get("last"))
    promedio = _f(fila.get("avgPx"))
    notional = abs(_f(fila.get("notionalUsd")))
    lado = "LONG" if pos > 0 else "SHORT"
    salida = {
        "activo": activo,
        "lado": lado,
        "color": _color(activo),
        "confia": False,
    }
    if abs(pos) <= 1e-12 or marca <= 0 or notional <= 1e-12 or promedio <= 0:
        salida["nota"] = "sin bolsa"
        return salida
    contrato = _talla(okx, inst)
    if contrato <= 0:
        salida["nota"] = "sin talla"
        return salida
    monedas_casa = pos * contrato
    nacimiento = int(_f(fila.get("cTime")))
    ordenes, cortado = _fills(okx, inst, nacimiento)
    limite = int(_f(fila.get("uTime")))
    piezas = []
    for orden in ordenes:
        ts = int(_f(orden.get("ts")))
        if limite > 0 and ts > limite:
            continue
        qty = _f(orden.get("fillSz"))
        px = _f(orden.get("fillPx"))
        if qty <= 0 or px <= 0:
            continue
        piezas.append(
            {
                "ts": ts,
                "lado": "buy" if str(orden.get("side") or "").lower() == "buy" else "sell",
                "qty": qty,
                "px": px,
            }
        )
    cabe = _afeitar_puerta(piezas, pos)
    toques = []
    for pieza in piezas:
        if pieza["qty"] <= 1e-12:
            continue
        qty = pieza["qty"] * contrato
        cambio = qty if pieza["lado"] == "buy" else -qty
        toques.append((cambio, abs(cambio) * pieza["px"]))
    cuenta = cuenta_de_la_pierna(toques, lado)
    replay = _f(cuenta.get("monedas"))
    holgura = max(0.02, 0.02 * abs(monedas_casa))
    cuadra = cabe and (not cortado) and abs(replay - monedas_casa) <= holgura
    pierna = _f(cuenta.get("pierna"))
    promesa = ganancia_de_la_pierna(pierna)
    viaje = Viaje(lado)
    viaje.cantidad = abs(monedas_casa)
    viaje.caja = caja_con_lo_realizado(
        lado, promedio, viaje.cantidad, _f(fila.get("realizedPnl"))
    )
    sello = Sello(salida["color"])
    suelo = sello.leer_papel(viaje, pierna, marca, None) if cuadra else None
    desde_quiebre = None
    desde_marca = None
    if suelo and promedio > 0 and marca > 0:
        if lado == "SHORT":
            desde_quiebre = (promedio - suelo) / promedio
            desde_marca = (marca - suelo) / marca
        else:
            desde_quiebre = (suelo - promedio) / promedio
            desde_marca = (suelo - marca) / marca
    salida.update(
        {
            "confia": cuadra,
            "pierna": round(pierna, 4),
            "promesa": None if promesa is None else round(promesa, 4),
            "montada": round(notional, 2),
            "suelo": None if suelo is None else round(float(suelo), 8),
            "desde_quiebre": None if desde_quiebre is None else round(desde_quiebre, 4),
            "desde_marca": None if desde_marca is None else round(desde_marca, 4),
            "casa": round(monedas_casa, 6),
            "replay": round(replay, 6),
            "nacimiento": nacimiento,
            "ordenes_leidas": len(toques),
            "nota": "historia cortada" if cortado else ("cuadra" if cuadra else "no cuadra"),
            "iron": _iron_vivo(
                memoria,
                activo,
                nacimiento,
                lado,
                salida["color"],
                float(suelo) if suelo else None,
                marca,
                abs(monedas_casa),
            ),
        }
    )
    clave = f"{activo}:{nacimiento}"
    if isinstance(memoria.get(clave), dict):
        memoria[clave]["confia"] = bool(cuadra)
    return salida


def _lejos_del_quiebre(fila: dict) -> float:
    pos = _f(fila.get("pos"))
    marca = _f(fila.get("markPx") or fila.get("last"))
    promedio = _f(fila.get("avgPx"))
    if abs(pos) <= 1e-12 or marca <= 0 or promedio <= 0:
        return 0.0
    if pos < 0:
        return (promedio - marca) / promedio
    return (marca - promedio) / promedio


def _nombres_del_latido(por_nombre: dict, memoria: dict) -> list[str]:
    """Los cinco, los que Iron ya sentó, y unos pocos que ya se alejaron."""
    nombres: list[str] = []
    vistos: set[str] = set()

    def suma(nombre: str) -> None:
        if not nombre or nombre == "BTC" or nombre in vistos:
            return
        vistos.add(nombre)
        nombres.append(nombre)

    for nombre in FIJOS:
        suma(nombre)
    for clave, nota in memoria.items():
        if isinstance(nota, dict) and nota.get("nacido"):
            suma(str(clave).split(":")[0])
    candidatos = []
    for nombre, fila in por_nombre.items():
        if nombre in vistos or nombre == "BTC":
            continue
        lejos = _lejos_del_quiebre(fila)
        if lejos + 1e-12 < LEJOS_PARA_MIRAR:
            continue
        candidatos.append((lejos, nombre))
    candidatos.sort(reverse=True)
    for _, nombre in candidatos[:NUEVOS_POR_LATIDO]:
        suma(nombre)
    return nombres


def _ya_sentado(activo: str, fila: dict, memoria: dict) -> dict | None:
    """Si Iron ya nació en esta bolsa, solo mueve la Oz. No vuelve a leer la pierna."""
    pos = _f(fila.get("pos"))
    marca = _f(fila.get("markPx") or fila.get("last"))
    if abs(pos) <= 1e-12 or marca <= 0:
        return None
    nacimiento = int(_f(fila.get("cTime")))
    nota = memoria.get(f"{activo}:{nacimiento}")
    if not isinstance(nota, dict) or not nota.get("nacido") or not nota.get("confia"):
        return None
    if not nota.get("suelo"):
        return None
    lado = "LONG" if pos > 0 else "SHORT"
    mira = _iron_vivo(
        memoria,
        activo,
        nacimiento,
        lado,
        _color(activo),
        float(nota["suelo"]),
        marca,
        _f(nota.get("condenadas")),
    )
    return {
        "activo": activo,
        "lado": lado,
        "color": _color(activo),
        "confia": True,
        "nacimiento": nacimiento,
        "nota": "sigue",
        "iron": mira,
    }


MEMORIA = DIARIO.parent / "iron_memoria.json"


def _cargar_memoria() -> dict:
    try:
        dato = json.loads(MEMORIA.read_text(encoding="ascii"))
    except (OSError, json.JSONDecodeError):
        return {}
    return dato if isinstance(dato, dict) else {}


def _guardar_memoria(dato: dict) -> None:
    MEMORIA.parent.mkdir(parents=True, exist_ok=True)
    temporal = MEMORIA.with_suffix(".tmp")
    temporal.write_text(json.dumps(dato, ensure_ascii=True, indent=2), encoding="ascii")
    temporal.replace(MEMORIA)


def _hacha(okx, fila: dict, memoria: dict) -> str:
    """Cierra lo condenado, una vez. Si la cuenta no está en neto, no manda."""
    if not fila.get("confia"):
        return ""
    nacimiento = int(_f(fila.get("nacimiento")))
    clave = f"{fila.get('activo')}:{nacimiento}"
    nota = memoria.get(clave) if isinstance(memoria.get(clave), dict) else None
    if not nota or not nota.get("tocada") or nota.get("cortado") or not nota.get("nacido"):
        return ""
    condenadas = _f(nota.get("condenadas"))
    if condenadas <= 0:
        return ""
    cfg = okx.get_private("/api/v5/account/config") or []
    if str((list(cfg) or [{}])[0].get("posMode") or "") != "net_mode":
        return ""
    inst = f"{fila.get('activo')}-USDT-SWAP"
    pub = okx.get_public(
        "/api/v5/public/instruments",
        params={"instType": "SWAP", "instId": inst},
    ) or []
    ins = pub[0] if pub else {}
    ct = _f(ins.get("ctVal"))
    lot = _f(ins.get("lotSz"))
    if ct <= 0 or lot <= 0:
        return ""
    rows = okx.get_private(
        "/api/v5/account/positions",
        params={"instType": "SWAP", "instId": inst},
    ) or []
    bolsa = next(
        (x for x in rows if isinstance(x, dict) and str(x.get("instId")) == inst),
        None,
    )
    if not bolsa or str(bolsa.get("mgnMode") or "") != "cross":
        return ""
    if int(_f(bolsa.get("cTime"))) != nacimiento:
        return ""
    pos = _f(bolsa.get("pos"))
    lado = str(fila.get("lado") or "")
    if lado == "SHORT" and pos >= 0:
        return ""
    if lado == "LONG" and pos <= 0:
        return ""
    monedas = abs(pos) * ct
    if monedas <= 1e-12:
        return ""
    pasos = int((min(monedas, condenadas) / ct) / lot + 1e-9)
    contratos = pasos * lot
    if contratos <= 0 or contratos * ct > condenadas + 1e-6 or contratos > abs(pos) + 1e-9:
        return ""
    sz = f"{contratos:.8f}".rstrip("0").rstrip(".")
    cuerpo = {
        "instId": inst,
        "tdMode": "cross",
        "side": "buy" if lado == "SHORT" else "sell",
        "ordType": "market",
        "sz": sz,
        "reduceOnly": True,
        "clOrdId": ("HIR" + uuid.uuid4().hex[:16])[:32],
    }
    data = okx.post_private("/api/v5/trade/order", cuerpo)
    fila0 = (list(data or [{}]) or [{}])[0]
    if str((fila0 or {}).get("sCode") or "0") not in ("0", ""):
        return ""
    nota["cortado"] = True
    nota["orden"] = str((fila0 or {}).get("ordId") or "")
    memoria[clave] = nota
    if contratos * ct + 1e-6 >= monedas:
        corte = _f(bolsa.get("markPx")) or _f(bolsa.get("last")) or _f(bolsa.get("avgPx"))
        if corte > 0:
            from cirugias.hiron.fantasma_vivo import sellar_corte

            sellar_corte(str(fila.get("activo") or ""), corte)
    return nota["orden"]


def latido() -> dict:
    from core import okx_rest

    if not okx_rest.credenciales_ok():
        raise RuntimeError("papel: sin llaves de lectura")
    filas = okx_rest.get_private("/api/v5/account/positions", params={"instType": "SWAP"}) or []
    por_nombre = {}
    for fila in filas:
        if not isinstance(fila, dict):
            continue
        inst = str(fila.get("instId") or "")
        if not inst.endswith("-USDT-SWAP"):
            continue
        por_nombre[inst.split("-")[0].upper()] = fila
    memoria = _cargar_memoria()
    cazadores = []
    for nombre in _nombres_del_latido(por_nombre, memoria):
        fila = por_nombre.get(nombre) or {}
        sentado = _ya_sentado(nombre, fila, memoria)
        cazadores.append(sentado or _uno(okx_rest, nombre, fila, memoria))
    ordenes = []
    for fila in cazadores:
        try:
            hecha = _hacha(okx_rest, fila, memoria)
        except Exception:
            hecha = ""
        if hecha:
            ordenes.append(hecha)
    _guardar_memoria({k: v for k, v in memoria.items() if isinstance(v, dict)})
    cuerpo = {
        "ts": time.time(),
        "manos": "hacha",
        "ordenes": len(ordenes),
        "iron": "corta lo condenado",
        "igris": "no tocado",
        "cazadores": cazadores,
    }
    DIARIO.parent.mkdir(parents=True, exist_ok=True)
    temporal = DIARIO.with_suffix(".tmp")
    temporal.write_text(json.dumps(cuerpo, ensure_ascii=True, indent=2), encoding="ascii")
    temporal.replace(DIARIO)
    try:
        with (DIARIO.parent / "latido.log").open("a", encoding="ascii") as libro:
            libro.write(f"PAPEL_VIVO {int(cuerpo['ts'])} ordenes {cuerpo['ordenes']}\n")
    except OSError:
        pass
    return cuerpo


def main() -> None:
    una = "--una-vez" in set(sys.argv)
    while True:
        try:
            cuerpo = latido()
        except Exception as exc:
            print(f"hacha calla {exc}", flush=True)
            if una:
                return
            time.sleep(PAUSA)
            continue
        for fila in cuerpo["cazadores"]:
            print(
                f"{fila['activo']} {fila.get('lado', '')} {fila.get('nota', '')} "
                f"promesa {fila.get('promesa')} "
                f"iron {(fila.get('iron') or {}).get('estado')}",
                flush=True,
            )
        print("PAPEL_VIVO", flush=True)
        if una:
            return
        time.sleep(PAUSA)


if __name__ == "__main__":
    main()
