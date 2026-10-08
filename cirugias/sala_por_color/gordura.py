"""Puerta por gordura de la bolsa.

Encima del reloj de tres días. Sube con la posición neta y solo baja
con holgura. Nunca quita lo que el reloj ya ganó: se queda la sala
más alta de las dos. Si el mínimo del contrato no deja vivir en esa
sala, no sube.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

from cirugias.sala_por_color.sala import color_sala

SUBE_AMARILLO = 500.0
SUBE_ROJO = 1000.0
BAJA_ROJO = 800.0
BAJA_AMARILLO = 300.0

_RANGO = {"verde": 0, "amarillo": 1, "rojo": 2}
_MEM: dict[str, Any] = {"mtime": None, "filas": None}


def _ruta() -> Path:
    root = Path(__file__).resolve().parents[2]
    raw = os.getenv("BERU_SALA_GORDURA_PATH", "").strip()
    if raw:
        return Path(raw)
    return root / "data" / "beru" / "sala_cuota" / "gordura.json"


def _cargar() -> dict[str, dict]:
    ruta = _ruta()
    try:
        mtime = ruta.stat().st_mtime
    except OSError:
        _MEM["mtime"] = None
        _MEM["filas"] = {}
        return {}
    if _MEM.get("mtime") == mtime and isinstance(_MEM.get("filas"), dict):
        return _MEM["filas"]
    try:
        data = json.loads(ruta.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        data = {}
    filas = data.get("santos") if isinstance(data, dict) else {}
    if not isinstance(filas, dict):
        filas = {}
    limpio = {
        str(k).upper(): v
        for k, v in filas.items()
        if isinstance(v, dict)
    }
    _MEM["mtime"] = mtime
    _MEM["filas"] = limpio
    return limpio


def _guardar(filas: dict[str, dict]) -> None:
    """Escribe con tmp único y reintentos: muchos cuarteles pisan el mismo libro."""
    ruta = _ruta()
    ruta.parent.mkdir(parents=True, exist_ok=True)
    cuerpo = {
        "nota": (
            "Sube a amarillo >500, a rojo >1000. "
            "Baja a amarillo <=800, a verde <=300. "
            "Se une al reloj quedandose la sala mas alta."
        ),
        "santos": filas,
        "ts": time.time(),
    }
    texto = json.dumps(cuerpo, ensure_ascii=False, indent=2)
    # Memoria local siempre: si el disco pelea, el pulso no muere.
    _MEM["filas"] = filas
    ultimo_err: OSError | None = None
    for intento in range(8):
        tmp = ruta.parent / f"gordura.{os.getpid()}.{intento}.{int(time.time() * 1000)}.tmp"
        try:
            tmp.write_text(texto, encoding="utf-8")
            os.replace(str(tmp), str(ruta))
            try:
                _MEM["mtime"] = ruta.stat().st_mtime
            except OSError:
                _MEM["mtime"] = None
            return
        except OSError as exc:
            ultimo_err = exc
            try:
                tmp.unlink(missing_ok=True)
            except OSError:
                pass
            time.sleep(0.02 * (intento + 1))
    # Fallo de disco: no tumba al Beru; el siguiente pulso reintenta.
    if ultimo_err is not None:
        return


def actualizar(
    activo: str,
    neto: float,
    *,
    precio: float = 0.0,
    frente: str = "",
) -> str:
    """Recalcula y guarda la sala por gordura de ese santo."""
    nombre = str(activo or "").strip().upper()
    if not nombre:
        return "verde"
    try:
        filas = dict(_cargar())
        previa = str((filas.get(nombre) or {}).get("sala") or "verde")
        nueva = sala_por_neto(previa, neto)
        if _RANGO.get(nueva, 0) > _RANGO.get(color_sala(previa), 0):
            while nueva != "verde" and not puede_vivir(nueva, precio, frente):
                if nueva == "rojo":
                    nueva = "amarillo"
                else:
                    nueva = "verde"
                    break
        filas[nombre] = {
            "sala": nueva,
            "neto": round(abs(float(neto or 0)), 2),
            "ts": time.time(),
        }
        _guardar(filas)
        return nueva
    except OSError:
        return sala_memoria(nombre)


def sala_por_neto(sala_ahora: str | None, neto: float) -> str:
    """Una sola lectura de la histéresis. ``neto`` en dólares absolutos."""
    s = color_sala(sala_ahora) if sala_ahora else "verde"
    if s not in _RANGO:
        s = "verde"
    n = abs(float(neto or 0))
    if s == "rojo":
        if n <= BAJA_ROJO:
            s = "amarillo"
        else:
            return "rojo"
    if s == "amarillo":
        if n > SUBE_ROJO:
            return "rojo"
        if n <= BAJA_AMARILLO:
            return "verde"
        return "amarillo"
    if n > SUBE_ROJO:
        return "rojo"
    if n > SUBE_AMARILLO:
        return "amarillo"
    return "verde"


def unir(reloj: str | None, gordura: str | None) -> str:
    """La más alta de las dos. Sin color = verde."""
    a = color_sala(reloj) if reloj else "verde"
    b = color_sala(gordura) if gordura else "verde"
    if a not in _RANGO:
        a = "verde"
    if b not in _RANGO:
        b = "verde"
    return a if _RANGO[a] >= _RANGO[b] else b


def puede_vivir(color: str, precio: float, frente: str) -> bool:
    """Si el mínimo del contrato deja nacer en esa sala."""
    from core import beru_rango
    from core.beru_rango_semaforo import masa_nacimiento_por_bando, tope_serie_por_color
    from core.lote_okx import filtros_lote, floor_completo, masa_a_qty_piso_deuda

    col = color_sala(color)
    px = float(precio or 0)
    fr = str(frente or "").strip()
    if px <= 0 or not fr:
        return False
    # Sin piso real no adivinar: puerta cerrada (no minSz=1 fantasma).
    base = fr.replace("USDT_LINEAL", "").replace("-USDT-SWAP", "").upper()
    if base and not floor_completo(base):
        return False
    masa = float(masa_nacimiento_por_bando(col, "paz") or 0)
    tope = float(tope_serie_por_color(col) or 0)
    try:
        r = masa_a_qty_piso_deuda(masa, px, fr, ticket_min_si_cero=False)
    except Exception:
        return False
    if r.get("ok"):
        return True
    try:
        f = filtros_lote(fr)
        lot = float(f.get("lotSz") or 1.0)
        min_sz = float(f.get("minSz") or lot)
        ct = float(f.get("ctVal") or 1.0)
        min_usd = abs(min_sz) * ct * px
    except Exception:
        return False
    techo = max(masa, tope)
    cap = float(beru_rango.masa_armar_max_usd() or 0)
    if cap > 0:
        techo = min(techo, cap)
        if min_usd > cap + 1e-9:
            return False
    return min_usd <= techo + 1e-9


def sala_memoria(activo: str) -> str:
    fila = _cargar().get(str(activo or "").upper()) or {}
    return color_sala(str(fila.get("sala") or "verde"))
