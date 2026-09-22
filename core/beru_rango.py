"""Beru rango (lineal) — wake eterno · Red desde Oz · saco ledger · sangre.

Doctrina Monarca 2026-08-22 (cirugía saco) · sin tope meta−ya (2026-08-23):
  · 0 absoluto = wake (no se mueve con Oz ni fill)
  · Perfil normal: Vacío/sangre ±1,2 % · Oz 0,2 % · Red 0,7 % simétrica · +$1/0,2 %
  · Perfil feria (paralelo): ±2,2 % · Oz 0,2 % · Red 1,2 % · +$1/0,2 %
  · Perfil piedra (OKX micro): misma geometría clásica · Red L 0,7 % / S 0,8 %
    · nace $0,20 · peldaños sumados (+$0,01 por peldaño) · semáforo por Santo
  · Estirón de sangre (2026-09-15): mapa +0,1 % / 0,5 % desde Oz-0 de campaña
    (primera Oz del lado; distinto de engorde_cero). Masa al armar = como 1,2 %.
  · Vacío/Red/Sangre nacen según perfil; engorde desde activación
  · Ledger saco = bitácora (no bloquea Vacío/Red)
  · Misma vela: sangre primero · sangre mata Red
  · Un vivo · manos OFF por defecto · SWAP USDT (OKX por defecto) · BERU_RANGO_PERFIL
"""
from __future__ import annotations

import json
import math
import os
from functools import lru_cache
from typing import Any

import core.config as config
from core import beru_mar


def vacio_adan_pct() -> float:
    """Activación del trailing semilla / sangre (± desde el wake)."""
    return float(getattr(config, "BERU_RANGO_VACIO_PCT", 0.012) or 0.012)


def oz_gap_pct() -> float:
    """Callback del trailing (distancia que persigue)."""
    return float(getattr(config, "BERU_RANGO_OZ_GAP_PCT", 0.002) or 0.002)


def red_activacion_pct(direccion: str | None = None) -> float:
    """Activación Red desde Oz. Piedra: L 0,7 % · S 0,8 %; normal/feria simétricos."""
    d = str(direccion or "").upper()
    if d == "SHORT":
        return float(getattr(config, "BERU_RANGO_RED_DESDE_OZ_SHORT_PCT", 0.007) or 0.007)
    if d == "LONG":
        return float(getattr(config, "BERU_RANGO_RED_DESDE_OZ_PCT", 0.007) or 0.007)
    return float(getattr(config, "BERU_RANGO_RED_DESDE_OZ_PCT", 0.007) or 0.007)


def red_desde_oz_pct(direccion: str | None = None) -> float:
    """Alias histórico = activación Red."""
    return red_activacion_pct(direccion)


def sangre_contraria_pct() -> float:
    return float(getattr(config, "BERU_RANGO_SANGRE_PCT", 0.012) or 0.012)


def sangre_estiron_activo() -> bool:
    """Estirón de mapa de sangre (Monarca 2026-09-15). OFF solo con env=0/false."""
    raw = os.getenv("BERU_RANGO_SANGRE_ESTIRON", "1")
    return str(raw or "1").strip().lower() not in ("0", "false", "no", "off")


def sangre_estiron_paso_pct() -> float:
    """Metro del frente: cada este % de camino desde Oz-0 de campaña → +1 tick."""
    return max(
        1e-9,
        float(
            os.getenv("BERU_RANGO_SANGRE_ESTIRON_PASO_PCT")
            or getattr(config, "BERU_RANGO_SANGRE_ESTIRON_PASO_PCT", 0.005)
            or 0.005
        ),
    )


def sangre_estiron_tick_pct() -> float:
    """Cuánto se aleja el llamado por cada paso de frente (+0,1 % doctrinal)."""
    return max(
        0.0,
        float(
            os.getenv("BERU_RANGO_SANGRE_ESTIRON_TICK_PCT")
            or getattr(config, "BERU_RANGO_SANGRE_ESTIRON_TICK_PCT", 0.001)
            or 0.001
        ),
    )


def limpiar_sangre_campana(beru: Any) -> None:
    """Fin de campaña (sangre ganó / wake): el próximo Oz vuelve a estirón 0."""
    if beru is None:
        return
    beru.sangre_campana_oz0_px = 0.0
    beru.sangre_campana_dir = ""


def actualizar_sangre_campana(beru: Any, oz_px: float, direccion: str) -> float:
    """Oz-0 de campaña del estirón — NO es engorde_cero (ese se pisa en cada Oz).

    Primera Oz de este lado (o tras flip): congela el 0.
    Oz siguientes del mismo lado: el 0 no se mueve.
    """
    if beru is None:
        return 0.0
    ox = float(oz_px or 0)
    d = str(direccion or "").upper()
    if ox <= 0 or d not in ("LONG", "SHORT"):
        return float(getattr(beru, "sangre_campana_oz0_px", 0) or 0)
    prev = float(getattr(beru, "sangre_campana_oz0_px", 0) or 0)
    prev_d = str(getattr(beru, "sangre_campana_dir", "") or "").upper()
    if prev <= 0 or prev_d != d:
        beru.sangre_campana_oz0_px = ox
        beru.sangre_campana_dir = d
        return ox
    return prev


def sangre_estiron_extra_pct(beru: Any, ancla_viva: float) -> float:
    """Extra de mapa: floor(|ancla − Oz0_campaña| / Oz0 / 0,5%) × 0,1%.

    Tumor a evitar: medir con engorde_cero (se actualiza en cada Oz del mismo
    lado y el estirón casi no crece).
    """
    if not sangre_estiron_activo() or beru is None:
        return 0.0
    cero = float(getattr(beru, "sangre_campana_oz0_px", 0) or 0)
    ancla = float(ancla_viva or 0)
    if cero <= 0 or ancla <= 0:
        return 0.0
    dist = abs(ancla - cero) / cero
    n = int(math.floor(dist / sangre_estiron_paso_pct() + 1e-12))
    if n <= 0:
        return 0.0
    return float(n) * sangre_estiron_tick_pct()


def sangre_mapa_pct(beru: Any, ancla_viva: float) -> float:
    """% de plantado de la oreja (1,2 % + estirón). No usar para masa/engorde."""
    return float(sangre_contraria_pct()) + float(sangre_estiron_extra_pct(beru, ancla_viva))


def oz0_detras_sangre_doctrinal(sangre_px: float, lado: str) -> float:
    """Oz virtual 1,2 % detrás de la oreja — engorde sordo al estirón del mapa.

    Si la sangre está al 1,2 % real del ancla, coincide con ese ancla.
    Si el mapa la alejó, la masa al armar cuenta solo el camino doctrinal 1,2 %.
    """
    sil = float(sangre_contraria_pct())
    px = float(sangre_px or 0)
    lado_u = str(lado or "").upper()
    if px <= 0 or sil <= 0 or sil >= 1.0:
        return 0.0
    if lado_u == "ABAJO":
        return px / (1.0 - sil)
    if lado_u == "ARRIBA":
        return px / (1.0 + sil)
    return 0.0


def masa_tramo_usd() -> float:
    """Base Vacío / tramo ($5). Piso Bybit se aplica en altar/manos."""
    return max(0.0, float(getattr(config, "BERU_RANGO_MASA_USD", 5.0) or 5.0))


def masa_red_usd() -> float:
    return max(0.0, float(getattr(config, "BERU_RANGO_MASA_RED_USD", 5.0) or 5.0))


def masa_sangre_usd() -> float:
    """Sangre parcial: $5 del tramo vivo."""
    return max(0.0, float(getattr(config, "BERU_RANGO_MASA_SANGRE_USD", 5.0) or 5.0))


def engorde_paso_usd() -> float:
    return max(0.0, float(getattr(config, "BERU_RANGO_ENGORDE_USD", 1.0) or 1.0))


def engorde_paso_pct() -> float:
    return max(1e-9, float(getattr(config, "BERU_RANGO_ENGORDE_PASO_PCT", 0.002) or 0.002))


def engorde_modo_peldaños_sumados() -> bool:
    m = str(getattr(config, "BERU_RANGO_ENGORDE_MODO", "") or "").lower()
    return m in ("peldaños_sumados", "peldaños", "sumados", "piedra")


def engorde_modo_hasta_oz() -> bool:
    """BTC inverso: masa = peldaños hasta la Oz (no hasta el detonante 1,2 %)."""
    m = str(getattr(config, "BERU_RANGO_ENGORDE_MODO", "") or "").lower()
    return m in ("hasta_oz", "btc_inverso", "oz")


def masa_paso_mar_usd() -> float:
    """Paso de cara del exchange (BTC inverso OKX = $10). 0 = sin forzar."""
    return max(0.0, float(getattr(config, "BERU_RANGO_MASA_PASO_MAR_USD", 0) or 0))


def redondear_masa_paso_mar(masa: float) -> float:
    """Baja al múltiplo del paso mar (10, 20, 30…)."""
    m = max(0.0, float(masa or 0))
    paso = masa_paso_mar_usd()
    if paso <= 0 or m <= 0:
        return m
    import math

    return math.floor(m / paso + 1e-12) * paso


def oz_px_desde_extremo(extremo: float, *, short: bool) -> float:
    """Oz = extremo ± callback (0,2 %). SHORT baja; LONG sube."""
    return _oz_desde_extremo(extremo, short=short)


def _oz0_engorde(beru: Any) -> float:
    """0 del engorde hasta-Oz: última Oz, o wake si aún no hubo cosecha."""
    oz0 = float(getattr(beru, "engorde_cero_oz_px", 0) or 0)
    if oz0 > 0:
        return oz0
    return float(cero_wake(beru) or 0)


def masa_hasta_oz_usd(beru: Any, oz_px: float) -> float:
    """Peldaños desde Oz-0/wake hasta el precio de la Oz × $ / 0,1 %.

    Usa ``round`` (no floor) para que 1,012×0,998 ≈ 0,9976 % cuente como
    10 peldaños (= Oz doctrinal ±1,0 %), no 9.
    """
    oz0 = _oz0_engorde(beru)
    ox = float(oz_px or 0)
    if oz0 <= 0 or ox <= 0:
        return 0.0
    dist = abs(ox - oz0) / oz0 / engorde_paso_pct()
    n = max(0, int(round(dist)))
    return redondear_masa_paso_mar(float(n) * engorde_paso_usd())


def redondeo_floor_manos() -> bool:
    """Piedra OKX: fracción inferior (floor) + cola de centavos."""
    return engorde_modo_peldaños_sumados()


def limpiar_masa_pendiente(beru: Any) -> None:
    """Borra deuda de redondeo (nuevo ciclo sangre inverso)."""
    if beru is None:
        return
    beru.masa_pendiente_usd = 0.0


def red_tope_pierna_usd() -> float:
    """Tope opcional: no reengordar Red mismo lado. Default OFF (0).

    Doctrina Monarca: $100/$300 = involución de *masa nacimiento* (paz→medio→pesado
    según semáforo), NO apagar al Santo. Red y sangre siguen chambeando; solo
    nacen más chicos. El tope por 0,1 % es techo del peldaño ($0,50 no sube a
    $0,51), no un candado de silencio.

    Solo si el Monarca pone ``BERU_RANGO_RED_TOPE_PIERNA_USD`` (p.ej. 100) se
    bloquea Red same-side. ``0`` o vacío = desactivado.
    """
    raw = os.environ.get("BERU_RANGO_RED_TOPE_PIERNA_USD")
    if raw is None or str(raw).strip() == "":
        return 0.0
    try:
        return max(0.0, float(raw))
    except (TypeError, ValueError):
        return 0.0


def red_bloqueada_por_pierna(
    beru: Any,
    *,
    pierna_casa_usd: float = 0.0,
) -> bool:
    """True solo si hay tope explícito env y pierna/saco same-side lo supera.

    Default: nunca bloquea. Sangre (contraria) no usa este candado.
    """
    tope = red_tope_pierna_usd()
    if tope <= 0 or beru is None:
        return False
    d = str(getattr(beru, "ultima_hoz_direccion", "") or "").upper()
    if d not in ("LONG", "SHORT"):
        return False
    saco = saco_lado_usd(beru, d)
    pierna = max(saco, float(pierna_casa_usd or 0))
    return pierna + 1e-9 >= tope


def registrar_masa_doctrinal(beru: Any, masa: float) -> None:
    if beru is None:
        return
    beru.masa_doctrinal_usd = max(0.0, float(masa or 0))


def _masa_suma_peldaños(
    n: int,
    base: float,
    step: float,
    *,
    tope_por_peldaño: float = 0.0,
) -> float:
    """Suma k=1..n de min(base + (k-1)*step, tope). tope=0 → serie libre."""
    if n <= 0:
        return 0.0
    if tope_por_peldaño <= 0:
        return float(n) * base + float(step) * float(n) * float(n - 1) / 2.0
    total = 0.0
    for k in range(1, n + 1):
        term = base + float(k - 1) * step
        total += min(term, tope_por_peldaño)
    return total


def _masa_delta_peldaños(
    n: int,
    offset: int,
    base: float,
    step: float,
    *,
    tope_por_peldaño: float = 0.0,
) -> float:
    """Masa viva = peldaños n − offset (una orden; serie $0,20 + $0,21 + …).

    ``tope_por_peldaño``: techo por cada 0,1 % (semáforo), no tope de orden entera.
    """
    if n <= offset:
        return max(0.0, base)
    delta = (
        _masa_suma_peldaños(n, base, step, tope_por_peldaño=tope_por_peldaño)
        - _masa_suma_peldaños(offset, base, step, tope_por_peldaño=tope_por_peldaño)
    )
    return max(base, delta)


def masa_peldaños_sumados_usd(
    n: int,
    *,
    offset: int = 0,
    base: float | None = None,
    step: float | None = None,
    tope_por_peldaño: float = 0.0,
) -> float:
    b = float(base if base is not None else masa_tramo_usd())
    s = float(step if step is not None else engorde_paso_usd())
    return _masa_delta_peldaños(
        int(n), int(offset), b, s, tope_por_peldaño=float(tope_por_peldaño or 0),
    )


def _base_masa_origen(origen: str, beru: Any | None = None) -> float:
    if beru is not None and engorde_modo_peldaños_sumados():
        from core import beru_rango_semaforo as sem

        sb = sem.serie_base_usd(beru)
        if sb is not None:
            return sb
    origen_u = str(origen or "").upper()
    if origen_u == "SANGRE":
        return masa_sangre_usd()
    if origen_u == "RED":
        return masa_red_usd()
    return masa_tramo_usd()


def _ref_engorde(beru: Any) -> tuple[float, int]:
    oz0 = float(getattr(beru, "engorde_cero_oz_px", 0) or 0)
    offset = int(getattr(beru, "engorde_peldaño_offset", 0) or 0)
    ancla = float(getattr(beru, "engorde_ancla_px", 0) or 0)
    if oz0 > 0:
        return oz0, offset
    return ancla, offset


def _masa_viva_en_px(beru: Any, px: float, *, base: float) -> float:
    ref, offset = _ref_engorde(beru)
    if ref <= 0 or px <= 0:
        return base
    n = peldaños_entre(ref, px)
    tope = engorde_tope_usd(beru) if engorde_modo_peldaños_sumados() else 0.0
    return _masa_delta_peldaños(
        n, offset, base, engorde_paso_usd(), tope_por_peldaño=tope,
    )


def _preparar_engorde_desde_oz(
    beru: Any,
    *,
    precio: float,
    base: float,
) -> tuple[float, float]:
    """Calcula masa viva y ancla Oz-0 para sangre/Red tras cosecha."""
    oz0 = float(getattr(beru, "engorde_cero_oz_px", 0) or getattr(beru, "oz_despliegue_px", 0) or 0)
    px = float(precio or 0)
    if oz0 <= 0 or px <= 0 or not engorde_modo_peldaños_sumados():
        return float(base), 0.0
    offset = int(getattr(beru, "engorde_peldaño_offset", 0) or 0)
    tope = engorde_tope_usd(beru)
    masa = _masa_delta_peldaños(
        peldaños_entre(oz0, px), offset, base, engorde_paso_usd(), tope_por_peldaño=tope,
    )
    return masa, oz0


def _piedra_tier_normalizado(tier: str | None) -> str:
    t = str(tier or "medio").strip().lower()
    if t in ("ceñido", "cenido", "ceni", "ce"):
        return "cenido"
    if t in ("ancho", "wide", "a"):
        return "ancho"
    if t in ("medio", "medium", "default", "m"):
        return "medio"
    return "medio"


def _tope_por_tier(tier: str) -> float:
    tiers = getattr(config, "BERU_RANGO_PIEDRA_TIERS", {}) or {}
    return float(tiers.get(_piedra_tier_normalizado(tier), 0.8) or 0.8)


def _ruta_piedra_asignacion() -> str:
    return str(
        os.getenv("BERU_RANGO_PIEDRA_ASIGNACION_PATH")
        or getattr(config, "BERU_RANGO_PIEDRA_ASIGNACION_PATH", "")
        or ""
    )


@lru_cache(maxsize=4)
def _cargar_piedra_asignacion(ruta: str) -> dict[str, Any]:
    if not ruta or not os.path.exists(ruta):
        return {"activos": {}}
    try:
        with open(ruta, encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {"activos": {}}
    except (OSError, json.JSONDecodeError):
        return {"activos": {}}


def invalidar_piedra_asignacion() -> None:
    _cargar_piedra_asignacion.cache_clear()


def _piedra_asignacion() -> dict[str, Any]:
    return _cargar_piedra_asignacion(_ruta_piedra_asignacion())


def activo_desde_beru(beru: Any | None) -> str:
    if beru is None:
        return ""
    frente = str(getattr(beru, "frente_asignado", "") or "")
    if frente:
        return str(beru_mar.base_desde_frente(frente) or "").upper()
    uid = str(getattr(beru, "uid", "") or "")
    if uid.startswith("RANGO_"):
        parts = uid.split("_")
        if len(parts) >= 2:
            return parts[1].upper()
    return ""


def piedra_tier_activo(activo: str | None) -> str | None:
    """Legacy tier ancho/medio/cenido; también lee semaforo del JSON."""
    base = str(activo or "").upper()
    if not base:
        return None
    row = (_piedra_asignacion().get("activos") or {}).get(base)
    if not row:
        return None
    if isinstance(row, dict):
        tier = row.get("tier") or row.get("piedra_tier")
        if not tier:
            sem = row.get("semaforo") or row.get("color")
            if sem:
                s = str(sem).strip().lower()
                if s in ("verde", "ancho"):
                    return "ancho"
                if s in ("rojo", "cenido", "ceñido"):
                    return "cenido"
                return "medio"
    else:
        tier = row
    return _piedra_tier_normalizado(str(tier or "")) if tier else None


def engorde_tope_usd(beru: Any | None = None, *, activo: str | None = None) -> float:
    """Tope máx. de engorde por peldaño (cada 0,1 %). No es tope de orden entera."""
    if engorde_modo_peldaños_sumados():
        from core import beru_rango_semaforo as sem

        return sem.tope_masa_viva(beru, activo)
    base = str(activo or activo_desde_beru(beru) or "").upper()
    tier_asig = piedra_tier_activo(base) if base else None
    if tier_asig:
        return _tope_por_tier(tier_asig)
    tope = float(getattr(config, "BERU_RANGO_ENGORDE_TOPE_USD", 0) or 0)
    return max(0.0, tope)


def _limitar_masa_viva(viva: float, beru: Any | None = None) -> float:
    """Tope lineal normal/feria. Piedra: el tope va por peldaño en la serie, no aquí."""
    if engorde_modo_peldaños_sumados():
        return float(viva)
    tope = engorde_tope_usd(beru)
    if tope > 0:
        return min(float(viva), tope)
    return float(viva)


def piso_masa_usd(masa: float, *, minimo_bybit: float = 0.0) -> float:
    """max(masa doctrinal, mínimo Bybit del Santo)."""
    return max(float(masa or 0), float(minimo_bybit or 0), 0.0)


def peldaños_entre(a: float, b: float) -> int:
    """Cuántos pasos de engorde hay entre dos precios (referencia = a)."""
    a0 = float(a or 0)
    b0 = float(b or 0)
    if a0 <= 0 or b0 <= 0:
        return 0
    return int(abs(b0 - a0) / a0 / engorde_paso_pct() + 1e-12)


def meta_saco_usd(wake: float, precio: float, *, base: float | None = None) -> float:
    """Saco objetivo a esta profundidad: $5 + $1 × peldaños desde wake."""
    b = float(base if base is not None else masa_tramo_usd())
    w = float(wake or 0)
    px = float(precio or 0)
    if w <= 0 or px <= 0:
        return max(0.0, b)
    return max(0.0, b + float(peldaños_entre(w, px)) * engorde_paso_usd())


def saco_lado_usd(beru: Any, lado: str) -> float:
    """Masa ya cosechada en ese lado (ledger de la ola)."""
    d = str(lado or "").upper()
    if d == "LONG":
        return max(0.0, float(getattr(beru, "saco_long_usd", 0) or 0))
    if d == "SHORT":
        return max(0.0, float(getattr(beru, "saco_short_usd", 0) or 0))
    return 0.0


def registrar_saco(beru: Any, lado: str, masa: float) -> None:
    """Suma fill al ledger del lado (no doble-cuenta en el siguiente tramo)."""
    m = max(0.0, float(masa or 0))
    d = str(lado or "").upper()
    if d == "LONG":
        beru.saco_long_usd = saco_lado_usd(beru, "LONG") + m
    elif d == "SHORT":
        beru.saco_short_usd = saco_lado_usd(beru, "SHORT") + m


def meta_en_profundidad_usd(
    beru: Any, *, lado: str, precio: float, origen: str,
) -> float:
    """Meta informativa a esta profundidad ($5 + peldaños desde wake). No bloquea armas."""
    _ = str(lado or "").upper()
    px = float(precio or 0)
    origen_u = str(origen or "").upper()
    base = masa_red_usd() if origen_u == "RED" else masa_tramo_usd()
    return meta_saco_usd(cero_wake(beru), px, base=base)


def cupo_lado_usd(beru: Any, *, lado: str, precio: float, origen: str) -> float:
    """Alias histórico = meta a profundidad (ya no resta saco ni frena la escalera)."""
    return meta_en_profundidad_usd(beru, lado=lado, precio=precio, origen=origen)


def orden_nacimiento_usd(beru: Any, *, lado: str, precio: float, origen: str) -> float:
    """Vacío/Red nacen según perfil; piedra usa semáforo + bando pierna."""
    _ = lado
    px = float(precio or 0)
    origen_u = str(origen or "").upper()
    if engorde_modo_peldaños_sumados():
        from core import beru_rango_semaforo as sem

        return max(0.0, sem.preparar_nacimiento_tramo(beru, precio=px))
    if engorde_modo_hasta_oz():
        return 0.0
    base = masa_red_usd() if origen_u == "RED" else masa_tramo_usd()
    return max(0.0, base)


def _asegurar_oz0_wake(beru: Any) -> float:
    oz0 = float(getattr(beru, "engorde_cero_oz_px", 0) or 0)
    if oz0 > 0:
        return oz0
    wake = float(cero_wake(beru) or 0)
    if wake > 0:
        beru.engorde_cero_oz_px = wake
    return wake


def masa_arm_hasta_oz(beru: Any, px_activacion: float, *, short: bool) -> float:
    """Al detonar: masa = peldaños hasta la Oz (extremo − callback), no hasta el 1,2 %."""
    _asegurar_oz0_wake(beru)
    oz = oz_px_desde_extremo(float(px_activacion or 0), short=short)
    return masa_hasta_oz_usd(beru, oz)


# Alias: meta a profundidad (panel / lectura)
orden_vacio_red_usd = meta_en_profundidad_usd


def masa_tramo_viva_usd(beru: Any, precio: float | None = None) -> float:
    """Masa del tramo vivo — Vacío / Red / Sangre.

    Linear (normal/feria): base + peldaños × paso.
    Piedra sumados: serie $b + (b+s) + … desde ancla u Oz-0 (una orden).
    hasta_oz (BTC inverso): peldaños desde Oz-0 hasta el precio de la Oz.
    """
    origen = str(getattr(beru, "origen_tramo", "") or "").upper()
    px = float(precio or 0) or float(getattr(beru, "oz_adan", 0) or 0) or float(
        getattr(beru, "trail_extremo", 0) or 0
    )
    base = _base_masa_origen(origen, beru)
    if engorde_modo_hasta_oz():
        oz = float(getattr(beru, "oz_adan", 0) or 0)
        if oz <= 0 and px > 0:
            d = str(getattr(beru, "direccion", "") or "").upper()
            oz = oz_px_desde_extremo(px, short=(d == "SHORT"))
        return max(0.0, masa_hasta_oz_usd(beru, oz))
    if engorde_modo_peldaños_sumados():
        viva = _masa_viva_en_px(beru, px, base=base)
        return max(0.0, _limitar_masa_viva(viva, beru))
    ancla = float(getattr(beru, "engorde_ancla_px", 0) or 0) or px
    if ancla <= 0 or px <= 0:
        viva = base
    else:
        viva = base + float(peldaños_entre(ancla, px)) * engorde_paso_usd()
    return max(0.0, _limitar_masa_viva(viva, beru))


def masa_engordada_usd(beru: Any, precio: float | None = None) -> float:
    """Alias doctrinal = masa del tramo vivo."""
    return masa_tramo_viva_usd(beru, precio)


def actualizar_engorde(beru: Any, precio: float) -> bool:
    """Engorda el tramo vivo desde ancla ($5 + peldaños)."""
    if bool(getattr(beru, "engorde_bloqueado", True)):
        return False
    if str(getattr(beru, "estado", "") or "").upper() != "CAZANDO":
        return False
    nueva = masa_tramo_viva_usd(beru, precio)
    vieja = float(getattr(beru, "masa", 0) or 0)
    if nueva > vieja + 1e-9:
        beru.masa = nueva
        beru.masa_tramo_usd = nueva
        registrar_masa_doctrinal(beru, nueva)
        ancla = float(getattr(beru, "engorde_ancla_px", 0) or 0)
        if ancla > 0:
            beru.engorde_peldaños = peldaños_entre(ancla, precio)
        else:
            beru.engorde_peldaños = 0
        return True
    return False


def trailing_dist_pct() -> float:
    return float(getattr(config, "BERU_RANGO_TRAILING_PCT", 0) or 0) or oz_gap_pct()


def manos_activas() -> bool:
    return bool(getattr(config, "BERU_RANGO_MANOS", False))


def hilo_activo() -> bool:
    return bool(getattr(config, "BERU_RANGO_HILO", False))


def cero_wake(beru: Any) -> float:
    """0 absoluto del wake — no se mueve con Oz/fill."""
    w = float(getattr(beru, "cero_wake", 0) or 0)
    if w > 0:
        return w
    return float(getattr(beru, "centro_local", 0) or 0)


def cero_local(beru: Any) -> float:
    """Alias de medición: siempre el wake."""
    return cero_wake(beru)


def pct_desde_cero(beru: Any, precio: float) -> float:
    c = cero_wake(beru)
    px = float(precio or 0)
    if c <= 0 or px <= 0:
        return 0.0
    return (px - c) / c


def precio_desde_cero(beru: Any, pct: float) -> float:
    c = cero_wake(beru)
    if c <= 0:
        return 0.0
    return c * (1.0 + float(pct))


def ancla_mapa_red(oz_despliegue: float, fill: float, direccion: str) -> float:
    """Peldaño manda. Fill peor (hacia Red) sube ancla; fill mejor no comprime."""
    oz = float(oz_despliegue or 0)
    fill_px = float(fill or 0)
    if oz <= 0:
        return fill_px
    if fill_px <= 0:
        return oz
    d = str(direccion or "").upper()
    if d == "SHORT":
        # Red arriba: fill peor = más alto → ancla sube
        return max(oz, fill_px)
    # LONG: Red abajo: fill peor = más bajo → ancla baja
    return min(oz, fill_px)


def red_desde_ancla(ancla: float, direccion: str) -> float:
    d = str(direccion or "").upper()
    red_act = red_activacion_pct(d)
    a = float(ancla or 0)
    if a <= 0:
        return 0.0
    if d == "SHORT":
        return a * (1.0 + red_act)
    return a * (1.0 - red_act)


def despertar(beru: Any, precio: float, *, activo: str = "") -> None:
    px = float(precio or 0)
    if px <= 0:
        raise ValueError("beru_rango: precio de wake inválido")
    beru.cero_wake = px
    beru.centro_local = px
    beru.ancla_tramo = px
    beru.centro_manto = px  # mismo 0: wake = manto de referencia
    beru.modo_combate = "RANGO"
    beru.estado = "ACECHANDO"
    beru.direccion = ""
    beru.masa = 0.0
    beru.masa_tramo_usd = 0.0
    beru.oz_pct = 0.0
    beru.red_pct = 0.0
    beru.oz_adan = 0.0
    beru.red_adan = 0.0
    beru.oz_despliegue_px = 0.0
    beru.trail_extremo = 0.0
    beru.llamado_tramo_pct = vacio_adan_pct()
    beru.oreja_sangre_activa = True
    beru.oreja_red_activa = False
    beru.sangre_vista_dentro = False
    beru.es_relevo_cazador = False
    beru.engorde_bloqueado = True
    beru.engorde_peldaños = 0
    beru.engorde_ancla_px = 0.0
    beru.engorde_cero_oz_px = 0.0
    beru.engorde_peldaño_offset = 0
    beru.masa_pendiente_usd = 0.0
    beru.masa_doctrinal_usd = 0.0
    beru.altar_masa_colocada_usd = 0.0
    beru.saco_long_usd = 0.0
    beru.saco_short_usd = 0.0
    beru.sangre_lado = ""
    beru.sangre_adan = 0.0
    beru.rango_escalones_red = 0
    beru.origen_tramo = ""
    limpiar_sangre_campana(beru)
    if activo:
        m = str(
            getattr(config, "BERU_RANGO_MERCADO", "linear") or "linear"
        ).strip().lower()
        if m == "inverse":
            beru.frente_asignado = f"{str(activo).upper()}USD_INVERSE"
        else:
            beru.frente_asignado = f"{str(activo).upper()}USDT_LINEAL"


def marcar_visto_dentro(beru: Any, precio: float) -> None:
    if bool(getattr(beru, "sangre_vista_dentro", False)):
        return
    vac = vacio_adan_pct()
    if abs(pct_desde_cero(beru, precio)) <= vac + 1e-12:
        beru.sangre_vista_dentro = True


def toca_vacio(beru: Any, precio: float) -> str:
    """Activación ±1,2 del trailing semilla (desde wake)."""
    if str(getattr(beru, "estado", "") or "") != "ACECHANDO":
        return ""
    if bool(getattr(beru, "es_relevo_cazador", False)):
        return ""
    if not bool(getattr(beru, "oreja_sangre_activa", False)):
        return ""
    marcar_visto_dentro(beru, precio)
    if not bool(getattr(beru, "sangre_vista_dentro", False)):
        return ""
    vac = vacio_adan_pct()
    pct = pct_desde_cero(beru, precio)
    if pct >= vac - 1e-12:
        return "ARRIBA"
    if pct <= -vac + 1e-12:
        return "ABAJO"
    return ""


def _oz_desde_extremo(extremo: float, *, short: bool) -> float:
    gap = trailing_dist_pct()
    ex = float(extremo or 0)
    if ex <= 0:
        return 0.0
    if short:
        return ex * (1.0 - gap)
    return ex * (1.0 + gap)


def _plantar_trailing(
    beru: Any,
    *,
    short: bool,
    masa: float,
    precio_activacion: float,
    ancla_engorde: float | None = None,
) -> float:
    """Activación tocada → arma trailing (callback 0,2). Engorde ON en caza."""
    px = float(precio_activacion or 0)
    if px <= 0:
        return 0.0
    masa_f = float(masa or 0)
    if masa_f <= 1e-12:
        return 0.0
    beru.direccion = "SHORT" if short else "LONG"
    beru.trail_extremo = px
    oz_ancla = float(ancla_engorde or 0)
    if oz_ancla > 0 and (engorde_modo_peldaños_sumados() or engorde_modo_hasta_oz()):
        beru.engorde_cero_oz_px = oz_ancla
        beru.engorde_ancla_px = oz_ancla
    else:
        beru.engorde_ancla_px = px
        if not engorde_modo_peldaños_sumados() and not engorde_modo_hasta_oz():
            beru.engorde_cero_oz_px = 0.0
            beru.engorde_peldaño_offset = 0
    beru.oz_adan = _oz_desde_extremo(px, short=short)
    beru.oz_pct = pct_desde_cero(beru, beru.oz_adan)
    beru.red_adan = 0.0
    beru.red_pct = 0.0
    beru.llamado_tramo_pct = trailing_dist_pct()
    beru.masa = masa_f
    beru.masa_tramo_usd = masa_f
    registrar_masa_doctrinal(beru, masa_f)
    beru.estado = "CAZANDO"
    beru.oreja_sangre_activa = False
    beru.oreja_red_activa = False
    beru.engorde_bloqueado = False
    beru.engorde_peldaños = 0
    # Nuevo sello de altar en cada caza — no reutilizar link de un fill viejo.
    beru.altar_revision = int(getattr(beru, "altar_revision", 0) or 0) + 1
    beru.altar_link_id = ""
    beru.altar_order_id = ""
    beru.altar_order_status = ""
    beru.altar_trigger_price = 0.0
    beru.tramo_precio_activacion = px
    beru.caza_trail_iniciado = False
    # Recalcula: engorde desde ancla.
    actualizar_engorde(beru, px)
    return float(getattr(beru, "masa", 0) or masa_f)


def armar_tramo_desde_vacio(
    beru: Any, lado: str, precio: float | None = None,
) -> float:
    """Vacío ±1,2 → trailing; hasta_oz nace con masa hasta la Oz (~1 %)."""
    lado_u = str(lado or "").upper()
    vac = vacio_adan_pct()
    if lado_u == "ARRIBA":
        px = float(precio or 0) or precio_desde_cero(beru, vac)
        beru.origen_tramo = "VACIO"
        if engorde_modo_hasta_oz():
            orden = masa_arm_hasta_oz(beru, px, short=True)
        else:
            orden = orden_nacimiento_usd(beru, lado="SHORT", precio=px, origen="VACIO")
        if orden <= 1e-12:
            return 0.0
        oz0 = _asegurar_oz0_wake(beru) if engorde_modo_hasta_oz() else None
        return _plantar_trailing(
            beru, short=True, masa=orden, precio_activacion=px,
            ancla_engorde=oz0 if oz0 and oz0 > 0 else None,
        )
    if lado_u == "ABAJO":
        px = float(precio or 0) or precio_desde_cero(beru, -vac)
        beru.origen_tramo = "VACIO"
        if engorde_modo_hasta_oz():
            orden = masa_arm_hasta_oz(beru, px, short=False)
        else:
            orden = orden_nacimiento_usd(beru, lado="LONG", precio=px, origen="VACIO")
        if orden <= 1e-12:
            return 0.0
        oz0 = _asegurar_oz0_wake(beru) if engorde_modo_hasta_oz() else None
        return _plantar_trailing(
            beru, short=False, masa=orden, precio_activacion=px,
            ancla_engorde=oz0 if oz0 and oz0 > 0 else None,
        )
    return 0.0


def actualizar_trailing_oz(beru: Any, precio: float) -> bool:
    """Persigue el extremo; Oz callback; engorde doctrinal del tramo vivo."""
    if str(getattr(beru, "estado", "") or "") != "CAZANDO":
        return False
    px = float(precio or 0)
    if px <= 0:
        return False
    d = str(getattr(beru, "direccion", "") or "").upper()
    gap = trailing_dist_pct()
    extremo = float(getattr(beru, "trail_extremo", 0) or 0) or px
    oz_antes = float(getattr(beru, "oz_adan", 0) or 0)
    moved = False
    if d == "SHORT":
        if px > extremo + 1e-15:
            extremo = px
            moved = True
        beru.trail_extremo = extremo
        beru.oz_adan = extremo * (1.0 - gap)
    elif d == "LONG":
        if px < extremo - 1e-15 or extremo <= 0:
            extremo = px
            moved = True
        beru.trail_extremo = extremo
        beru.oz_adan = extremo * (1.0 + gap)
    else:
        return False
    beru.oz_pct = pct_desde_cero(beru, beru.oz_adan)
    if abs(float(beru.oz_adan) - oz_antes) > 1e-12:
        moved = True
    if engorde_modo_hasta_oz():
        oz_now = float(getattr(beru, "oz_adan", 0) or 0)
        if oz_now > 0 and actualizar_engorde(beru, oz_now):
            moved = True
    elif actualizar_engorde(beru, extremo):
        moved = True
    act = float(getattr(beru, "tramo_precio_activacion", 0) or 0)
    if act > 0 and not bool(getattr(beru, "caza_trail_iniciado", False)):
        eps = max(act * 1e-6, 1e-9)
        if d == "LONG" and extremo < act - eps:
            beru.caza_trail_iniciado = True
        elif d == "SHORT" and extremo > act + eps:
            beru.caza_trail_iniciado = True
    return moved


def toca_oz(beru: Any, precio: float) -> bool:
    """Callback del trailing: SHORT baja a Oz; LONG sube a Oz."""
    if str(getattr(beru, "estado", "") or "") != "CAZANDO":
        return False
    oz = float(getattr(beru, "oz_adan", 0) or 0)
    px = float(precio or 0)
    if oz <= 0 or px <= 0:
        return False
    d = str(getattr(beru, "direccion", "") or "").upper()
    if d == "SHORT":
        return px <= oz + 1e-12
    if d == "LONG":
        return px >= oz - 1e-12
    return False


def toca_sangre(beru: Any, precio: float) -> bool:
    """Activación sangre post-Oz: 1,2 % del peldaño Oz (contraria), no del last lejos."""
    if not bool(getattr(beru, "oreja_sangre_activa", False)):
        return False
    if str(getattr(beru, "estado", "") or "") != "ACECHANDO":
        return False
    if not (
        bool(getattr(beru, "es_relevo_cazador", False))
        or float(getattr(beru, "ultima_hoz_tocada_precio", 0) or 0) > 0
    ):
        return False
    px = float(precio or 0)
    if px <= 0:
        return False
    lado = str(getattr(beru, "sangre_lado", "") or "").upper()
    sangre_px = float(getattr(beru, "sangre_adan", 0) or 0)
    if sangre_px > 0:
        if lado == "ABAJO":
            return px <= sangre_px + 1e-12
        if lado == "ARRIBA":
            return px >= sangre_px - 1e-12
        oz_dir = str(getattr(beru, "ultima_hoz_direccion", "") or "").upper()
        if oz_dir == "SHORT":
            return px <= sangre_px + 1e-12
        if oz_dir == "LONG":
            return px >= sangre_px - 1e-12
        return False
    # Respaldo legacy: ±1,2 desde wake (semillas viejas sin sangre_adan).
    sil = float(getattr(beru, "llamado_tramo_pct", 0) or sangre_contraria_pct())
    pct = pct_desde_cero(beru, px)
    if lado == "ABAJO":
        return pct <= -sil + 1e-12
    if lado == "ARRIBA":
        return pct >= sil - 1e-12
    oz_dir = str(getattr(beru, "ultima_hoz_direccion", "") or "").upper()
    if oz_dir == "SHORT":
        return pct <= -sil + 1e-12
    if oz_dir == "LONG":
        return pct >= sil - 1e-12
    return False


def toca_red_activacion(beru: Any, precio: float) -> bool:
    """Activación del trailing Red (0,7 desde la Oz desplegada)."""
    if not bool(getattr(beru, "oreja_red_activa", False)):
        return False
    if str(getattr(beru, "estado", "") or "") != "ACECHANDO":
        return False
    if not bool(getattr(beru, "es_relevo_cazador", False)):
        return False
    red = float(getattr(beru, "red_adan", 0) or 0)
    px = float(precio or 0)
    if red <= 0 or px <= 0:
        return False
    d = str(getattr(beru, "ultima_hoz_direccion", "") or "").upper()
    if d == "SHORT":
        return px >= red - 1e-12
    if d == "LONG":
        return px <= red + 1e-12
    return False


def toca_red_continuacion(beru: Any, precio: float) -> bool:
    return toca_red_activacion(beru, precio)


def secuencia_latido(
    precio: float,
    latido: dict[str, Any] | None = None,
) -> list[float]:
    """Tratos en orden; si no hay, last + alto + bajo del vaso."""
    lat = latido or {}
    prints = [float(p) for p in (lat.get("prints") or []) if float(p or 0) > 0]
    if prints:
        return prints
    last = float(lat.get("last") or precio or 0)
    out: list[float] = []
    for px in (last, float(lat.get("high") or 0), float(lat.get("low") or 0)):
        if px > 0 and (not out or abs(out[-1] - px) > 1e-12):
            if px not in out:
                out.append(px)
    return out


def toca_red_activacion_en_latido(
    beru: Any,
    precio: float,
    latido: dict[str, Any] | None = None,
) -> bool:
    for px in secuencia_latido(precio, latido):
        if toca_red_activacion(beru, px):
            return True
    return False


def toca_sangre_en_latido(
    beru: Any,
    precio: float,
    latido: dict[str, Any] | None = None,
) -> bool:
    for px in secuencia_latido(precio, latido):
        if toca_sangre(beru, px):
            return True
    return False


def toca_vacio_en_latido(
    beru: Any,
    precio: float,
    latido: dict[str, Any] | None = None,
) -> str:
    for px in secuencia_latido(precio, latido):
        lado = toca_vacio(beru, px)
        if lado:
            return lado
    return ""


def mecha_caza_permitida(beru: Any) -> bool:
    """Mechas del vaso solo cuentan tras el rastro huir del precio de activación."""
    return bool(getattr(beru, "caza_trail_iniciado", False))


def precio_trail_caza(
    beru: Any,
    precio: float,
    latido: dict[str, Any] | None = None,
) -> float:
    """Extremo para trailing: sin mechas stale del vaso que disparó el armado."""
    px = float(precio or 0)
    if not mecha_caza_permitida(beru):
        return px
    lat = latido or {}
    px_trail = extremo_latido_trailing(beru, px, lat) or px
    d = str(getattr(beru, "direccion", "") or "").upper()
    if d == "SHORT":
        hi = float(lat.get("high") or 0)
        if hi > px_trail:
            px_trail = hi
    elif d == "LONG":
        lo = float(lat.get("low") or 0)
        if lo > 0 and (px_trail <= 0 or lo < px_trail):
            px_trail = lo
    return px_trail


def toca_oz_en_latido(
    beru: Any,
    precio: float,
    latido: dict[str, Any] | None = None,
) -> bool:
    if not mecha_caza_permitida(beru):
        return False
    for px in secuencia_latido(precio, latido):
        if toca_oz(beru, px):
            return True
    return False


def extremo_latido_trailing(
    beru: Any,
    precio: float,
    latido: dict[str, Any] | None = None,
) -> float:
    """Punta del latido hacia la caza: SHORT oye el alto; LONG el bajo."""
    seq = secuencia_latido(precio, latido)
    if not seq:
        return float(precio or 0)
    d = str(getattr(beru, "direccion", "") or "").upper()
    if d == "LONG":
        return min(seq)
    if d == "SHORT":
        return max(seq)
    return float(seq[-1])


def latido_rapido_s() -> float:
    return float(getattr(config, "BERU_RANGO_LATIDO_RAPIDO_S", 0.1) or 0.1)


def latido_cerca_pct() -> float:
    return float(getattr(config, "BERU_RANGO_LATIDO_CERCA_PCT", 0.002) or 0.002)


def latido_sugerido_s(
    beru: Any,
    precio: float | None = None,
    *,
    lento_s: float | None = None,
) -> float:
    """Cerca de orejas / cazando → latido rápido; lejos → lento."""
    lento = float(
        lento_s
        if lento_s is not None
        else getattr(config, "BERU_RANGO_LATIDO_LENTO_S", 1.5) or 1.5
    )
    rapido = latido_rapido_s()
    if beru is None:
        return max(0.05, lento)
    estado = str(getattr(beru, "estado", "") or "").upper()
    if estado == "CAZANDO":
        return max(0.05, rapido)
    px = float(precio or 0)
    if px <= 0:
        return max(0.05, lento)
    umbral = latido_cerca_pct()
    candidatos: list[float] = []
    red = float(getattr(beru, "red_adan", 0) or 0)
    if red > 0 and bool(getattr(beru, "oreja_red_activa", False)):
        candidatos.append(red)
    cero = cero_wake(beru)
    vac = vacio_adan_pct()
    if cero > 0 and not bool(getattr(beru, "es_relevo_cazador", False)):
        candidatos.extend([cero * (1.0 + vac), cero * (1.0 - vac)])
    lado = str(getattr(beru, "sangre_lado", "") or "").upper()
    sil = sangre_contraria_pct()
    if bool(getattr(beru, "oreja_sangre_activa", False)):
        sangre_px = float(getattr(beru, "sangre_adan", 0) or 0)
        if sangre_px > 0:
            candidatos.append(sangre_px)
        elif cero > 0:
            # Semilla / sello legacy sin sangre_adan: ±1,2 desde wake.
            if lado == "ABAJO":
                candidatos.append(cero * (1.0 - sil))
            elif lado == "ARRIBA":
                candidatos.append(cero * (1.0 + sil))
    for nivel in candidatos:
        if nivel <= 0:
            continue
        if abs(px - nivel) / nivel <= umbral + 1e-12:
            return max(0.05, rapido)
    return max(0.05, lento)


def _cancelar_red(beru: Any) -> None:
    """Sangre ganó: elimina el trailing Red que esperaba."""
    beru.oreja_red_activa = False
    beru.red_adan = 0.0
    beru.red_pct = 0.0


def _plantar_orejas_post_oz(beru: Any, ancla_red: float, direccion: str) -> None:
    """Tras Oz: sangre (1,2 %+estirón) del peldaño vivo + Red doctrinal.

    Wake (0) sigue eterno para meta/saco. El *llamado* de sangre no se queda
    clavado al wake: si la Red escala el frente, la sangre renace junto al Oz.

    ``llamado_tramo_pct`` = siempre 1,2 % doctrinal (masa/engorde sordos al
    estirón). El mapa (``sangre_adan``) sí puede alejarse con la campaña.
    """
    d = str(direccion or "").upper()
    red_act = red_activacion_pct(d)
    sil_doc = sangre_contraria_pct()
    ancla = float(ancla_red or 0)
    sil_mapa = sangre_mapa_pct(beru, ancla) if ancla > 0 else sil_doc
    # Sordo al estirón: cualquier código que lea el % del tramo ve 1,2 %.
    beru.llamado_tramo_pct = sil_doc
    beru.sangre_mapa_pct = float(sil_mapa)
    if d == "SHORT":
        beru.sangre_lado = "ABAJO"
        beru.sangre_adan = ancla * (1.0 - sil_mapa) if ancla > 0 else 0.0
        beru.red_adan = ancla * (1.0 + red_act) if ancla > 0 else 0.0
        beru.red_pct = red_act
    else:
        beru.sangre_lado = "ARRIBA"
        beru.sangre_adan = ancla * (1.0 + sil_mapa) if ancla > 0 else 0.0
        beru.red_adan = ancla * (1.0 - red_act) if ancla > 0 else 0.0
        beru.red_pct = -red_act
    beru.oreja_sangre_activa = True
    beru.oreja_red_activa = True


def restaurar_acecho_post_oz(
    beru: Any,
    *,
    cero: float,
    red: float,
    sangre_lado: str,
    ultima_hoz_direccion: str = "",
    escalones_red: int = 0,
    cosechas: int = 0,
    oz_despliegue: float = 0.0,
    saco_long: float = 0.0,
    saco_short: float = 0.0,
    sangre_campana_oz0: float = 0.0,
    sangre_campana_dir: str = "",
    sangre_sello_px: float = 0.0,
) -> None:
    """Reengancha acecho tras sello: wake / Red / sangre (sin nuevo wake)."""
    wake = float(cero or 0)
    if wake <= 0 or beru is None:
        return
    lado = str(sangre_lado or "").upper()
    hoz = str(ultima_hoz_direccion or "").upper()
    if not hoz:
        hoz = "LONG" if lado == "ARRIBA" else "SHORT" if lado == "ABAJO" else "LONG"
    red_px = float(red or 0)
    red_act = red_activacion_pct(hoz)
    oz_dep = float(oz_despliegue or 0)
    if red_px <= 0:
        ancla = oz_dep if oz_dep > 0 else wake
        red_px = red_desde_ancla(ancla, hoz)
    beru.cero_wake = wake
    beru.centro_local = wake
    beru.ancla_tramo = wake
    beru.centro_manto = wake
    beru.estado = "ACECHANDO"
    beru.direccion = ""
    beru.oz_adan = 0.0
    beru.oz_pct = 0.0
    beru.oz_despliegue_px = oz_dep
    beru.trail_extremo = 0.0
    beru.masa = 0.0
    beru.masa_tramo_usd = 0.0
    beru.sangre_vista_dentro = True
    beru.es_relevo_cazador = True
    beru.engorde_bloqueado = True
    beru.ultima_hoz_direccion = hoz
    beru.sangre_lado = lado or ("ABAJO" if hoz == "SHORT" else "ARRIBA")
    beru.llamado_tramo_pct = sangre_contraria_pct()
    beru.red_adan = red_px
    beru.red_pct = red_act if beru.sangre_lado == "ABAJO" else -red_act
    # Campana del estirón: sello nuevo la trae; sello viejo puede traer solo sangre abs.
    camp_oz = float(sangre_campana_oz0 or 0)
    camp_d = str(sangre_campana_dir or "").upper()
    if camp_oz > 0 and camp_d in ("LONG", "SHORT"):
        beru.sangre_campana_oz0_px = camp_oz
        beru.sangre_campana_dir = camp_d
    elif camp_oz > 0:
        beru.sangre_campana_oz0_px = camp_oz
        beru.sangre_campana_dir = hoz
    else:
        # Sin campana en sello: no inventar 0 con oz_dep (tumor: estirón 0 falso
        # o reinicio de campaña). Mejor conservar sangre absoluta del sello.
        beru.sangre_campana_oz0_px = 0.0
        beru.sangre_campana_dir = ""
    # Misma ancla que la Red viva (fill peor puede haber subido el peldaño).
    # Preferir oz_despliegue del sello: evita drift si la Red nació con % viejo.
    ancla_sangre = 0.0
    if oz_dep > 0:
        red_doctrinal = red_desde_ancla(oz_dep, hoz)
        if red_px > 0:
            mas_lejos = (
                (hoz == "SHORT" and red_px > red_doctrinal + 1e-12)
                or (hoz == "LONG" and red_px < red_doctrinal - 1e-12)
            )
            if mas_lejos:
                if beru.sangre_lado == "ABAJO":
                    ancla_sangre = red_px / (1.0 + red_act) if red_act < 1 else red_px
                else:
                    ancla_sangre = red_px / (1.0 - red_act) if red_act < 1 else red_px
            else:
                ancla_sangre = oz_dep
        else:
            ancla_sangre = oz_dep
    elif red_px > 0:
        if beru.sangre_lado == "ABAJO":
            ancla_sangre = red_px / (1.0 + red_act) if red_act < 1 else red_px
        else:
            ancla_sangre = red_px / (1.0 - red_act) if red_act < 1 else red_px
    if ancla_sangre <= 0:
        ancla_sangre = wake
    sangre_abs = float(sangre_sello_px or 0)
    if float(getattr(beru, "sangre_campana_oz0_px", 0) or 0) > 0:
        sil_mapa = sangre_mapa_pct(beru, ancla_sangre)
        beru.sangre_mapa_pct = float(sil_mapa)
        if beru.sangre_lado == "ABAJO":
            beru.sangre_adan = ancla_sangre * (1.0 - sil_mapa)
        else:
            beru.sangre_adan = ancla_sangre * (1.0 + sil_mapa)
    elif sangre_abs > 0:
        # Sello viejo con oreja ya plantada (posiblemente estirada): no achicar a 1,2 %.
        beru.sangre_adan = sangre_abs
        beru.sangre_mapa_pct = 0.0
    else:
        sil = sangre_contraria_pct()
        beru.sangre_mapa_pct = float(sil)
        if beru.sangre_lado == "ABAJO":
            beru.sangre_adan = ancla_sangre * (1.0 - sil)
        else:
            beru.sangre_adan = ancla_sangre * (1.0 + sil)
    beru.oreja_sangre_activa = True
    beru.oreja_red_activa = True
    beru.rango_escalones_red = int(escalones_red or 0)
    beru.cosechas_continuas = int(cosechas or 0)
    beru.saco_long_usd = max(0.0, float(saco_long or 0))
    beru.saco_short_usd = max(0.0, float(saco_short or 0))
    if (engorde_modo_peldaños_sumados() or engorde_modo_hasta_oz()) and oz_dep > 0:
        beru.engorde_cero_oz_px = float(oz_dep)
        beru.engorde_peldaño_offset = 0
    else:
        beru.engorde_cero_oz_px = 0.0
        beru.engorde_peldaño_offset = 0
    beru.altar_link_id = ""
    beru.altar_order_id = ""
    beru.altar_order_status = ""
    beru.altar_trigger_price = 0.0
    beru.altar_cancel_confirmado = False


def restaurar_caza_trailing(
    beru: Any,
    *,
    cero: float,
    direccion: str,
    oz: float,
    trail_extremo: float,
    masa: float,
    altar_link_id: str = "",
    altar_order_id: str = "",
    altar_trigger_price: float = 0.0,
    altar_revision: int = 0,
    sangre_lado: str = "",
    escalones_red: int = 0,
    cosechas: int = 0,
    uid: str = "",
    saco_long: float = 0.0,
    saco_short: float = 0.0,
    ultima_hoz_direccion: str = "",
    oz_despliegue: float = 0.0,
) -> None:
    """Reengancha CAZANDO mid-hunt: Oz + extremo + sello del altar (Stop vivo)."""
    if beru is None:
        return
    d = str(direccion or "").upper()
    if d not in ("LONG", "SHORT"):
        return
    c0 = float(cero or 0)
    oz_px = float(oz or 0)
    ext = float(trail_extremo or 0) or oz_px
    if c0 <= 0 or oz_px <= 0:
        return
    if uid:
        beru.uid = str(uid)
    beru.cero_wake = c0
    beru.centro_local = c0
    beru.ancla_tramo = c0
    beru.centro_manto = c0
    beru.estado = "CAZANDO"
    beru.direccion = d
    beru.trail_extremo = ext
    beru.oz_adan = oz_px
    beru.oz_pct = pct_desde_cero(beru, oz_px)
    beru.llamado_tramo_pct = trailing_dist_pct()
    beru.masa = float(masa or 0) or masa_tramo_usd()
    beru.masa_tramo_usd = float(beru.masa)
    beru.red_adan = 0.0
    beru.red_pct = 0.0
    beru.oreja_sangre_activa = False
    beru.oreja_red_activa = False
    beru.sangre_vista_dentro = True
    beru.es_relevo_cazador = True
    beru.engorde_bloqueado = False
    beru.sangre_lado = str(sangre_lado or "")
    beru.rango_escalones_red = int(escalones_red or 0)
    beru.cosechas_continuas = int(cosechas or 0)
    beru.saco_long_usd = max(0.0, float(saco_long or 0))
    beru.saco_short_usd = max(0.0, float(saco_short or 0))
    hoz = str(ultima_hoz_direccion or "").upper()
    if hoz in ("LONG", "SHORT"):
        beru.ultima_hoz_direccion = hoz
    oz_dep = float(oz_despliegue or 0)
    if oz_dep > 0:
        beru.oz_despliegue_px = oz_dep
        if engorde_modo_peldaños_sumados():
            beru.engorde_cero_oz_px = oz_dep
    beru.altar_revision = int(altar_revision or 0)
    beru.altar_link_id = str(altar_link_id or "")
    beru.altar_order_id = str(altar_order_id or "")
    beru.altar_order_status = "Untriggered" if beru.altar_link_id else ""
    beru.altar_trigger_price = float(altar_trigger_price or oz_px)
    beru.altar_cancel_confirmado = False
    beru.altar_entrada_disparada = False
    beru.altar_market_ts = 0.0
    # Snap de pierna: al reenganchar, baseline = saco no sirve; se fija al 1er reconcile
    beru.pierna_snap_usd = 0.0
    beru.pierna_snap_lado = d
    beru.pierna_snap_net_usd = 0.0


def cosechar_oz_y_mover_cero(
    beru: Any,
    precio_fill: float,
    *,
    oz_despliegue: float | None = None,
    masa_usd: float | None = None,
) -> float:
    """Trailing detonó: wake intacto; fill → Tusk; Red desde peldaño Oz.

    ``masa_usd``: si viene de manos, debe ser el notional real de OKX (delta /
    orden colocada). Sin eso, ojos/teatro usan la masa doctrinal del tramo.
    """
    oz_dep = float(
        oz_despliegue
        if oz_despliegue is not None
        else getattr(beru, "oz_adan", 0) or 0
    )
    fill = float(precio_fill or 0) or oz_dep
    if fill <= 0 and oz_dep <= 0:
        return 0.0
    if oz_dep <= 0:
        oz_dep = fill
    d = str(getattr(beru, "direccion", "") or "").upper()
    if masa_usd is not None and float(masa_usd) > 0:
        masa_hecha = float(masa_usd)
    else:
        masa_hecha = float(getattr(beru, "masa", 0) or 0) or masa_tramo_usd()
    wake = cero_wake(beru)
    beru.ultima_hoz_tocada_precio = fill
    beru.ultima_hoz_tocada_pct = pct_desde_cero(beru, fill) if wake > 0 else 0.0
    beru.ultima_hoz_direccion = d
    beru.ultima_masa_cosechada = masa_hecha
    beru.precio_entrada_real = fill
    beru.oz_despliegue_px = oz_dep
    if d in ("LONG", "SHORT"):
        registrar_saco(beru, d, masa_hecha)
    # Wake eterno — no pisar centro_local / cero_wake
    if wake > 0:
        beru.cero_wake = wake
        beru.centro_local = wake
        beru.ancla_tramo = wake
        beru.centro_manto = wake
    beru.estado = "ACECHANDO"
    beru.sangre_vista_dentro = True
    beru.es_relevo_cazador = True
    beru.engorde_bloqueado = True
    beru.engorde_ancla_px = 0.0
    if engorde_modo_peldaños_sumados() and oz_dep > 0:
        beru.engorde_cero_oz_px = float(oz_dep)
        beru.engorde_peldaño_offset = peldaños_entre(oz_dep, fill)
    elif engorde_modo_hasta_oz() and oz_dep > 0:
        beru.engorde_cero_oz_px = float(oz_dep)
        beru.engorde_peldaño_offset = 0
    else:
        beru.engorde_cero_oz_px = 0.0
        beru.engorde_peldaño_offset = 0
    beru.oz_adan = 0.0
    beru.oz_pct = 0.0
    beru.trail_extremo = 0.0
    beru.masa = 0.0
    beru.masa_tramo_usd = 0.0
    beru.direccion = ""
    beru.tramo_precio_activacion = 0.0
    beru.caza_trail_iniciado = False
    beru.pierna_snap_usd = 0.0
    beru.pierna_snap_lado = ""
    beru.pierna_snap_net_usd = 0.0
    ancla = ancla_mapa_red(oz_dep, fill, d)
    # Estirón: congelar Oz-0 de campaña ANTES de plantar orejas (no usar engorde_cero).
    actualizar_sangre_campana(beru, oz_dep, d)
    _plantar_orejas_post_oz(beru, ancla, d)
    beru.cosechas_continuas = int(getattr(beru, "cosechas_continuas", 0) or 0) + 1
    # Acecho: sin Stop heredado de la caza (cancel en manos vía cancelar_pendiente).
    beru.altar_link_id = ""
    beru.altar_order_id = ""
    beru.altar_order_status = ""
    beru.altar_trigger_price = 0.0
    beru.altar_cancel_confirmado = False
    beru.altar_entrada_disparada = False
    beru.altar_market_ts = 0.0
    return masa_sangre_usd()


def armar_tramo_desde_sangre(beru: Any, precio: float | None = None) -> float:
    """Sangre → trailing; mapa puede estar estirado · masa como si fuera 1,2 %.

    Al ganar sangre se cierra la campaña del estirón (limpiar campana).
    """
    limpiar_masa_pendiente(beru)
    _cancelar_red(beru)
    lado = str(getattr(beru, "sangre_lado", "") or "").upper()
    vac = vacio_adan_pct()
    sangre_px = float(getattr(beru, "sangre_adan", 0) or 0)
    # Fin de campaña: el próximo Oz del otro lado nace con estirón 0.
    limpiar_sangre_campana(beru)

    def _px_y_base(short: bool, px_default: float) -> tuple[float, float]:
        px = float(precio or 0) or px_default
        if engorde_modo_hasta_oz():
            base = masa_arm_hasta_oz(beru, px, short=short)
        elif engorde_modo_peldaños_sumados():
            from core import beru_rango_semaforo as sem

            base = sem.preparar_nacimiento_tramo(beru, precio=px)
        else:
            base = masa_sangre_usd()
        return px, base

    def _arm(short: bool, px: float, base: float, lado_sangre: str) -> float:
        beru.origen_tramo = "SANGRE"
        oz0_doc = oz0_detras_sangre_doctrinal(px, lado_sangre)
        if engorde_modo_hasta_oz():
            if oz0_doc > 0:
                beru.engorde_cero_oz_px = oz0_doc
                beru.engorde_peldaño_offset = 0
                masa = masa_arm_hasta_oz(beru, px, short=short)
            else:
                masa = base
                oz0_doc = _asegurar_oz0_wake(beru)
            return _plantar_trailing(
                beru, short=short, masa=masa, precio_activacion=px,
                ancla_engorde=oz0_doc if oz0_doc > 0 else None,
            )
        if engorde_modo_peldaños_sumados() and oz0_doc > 0:
            beru.engorde_cero_oz_px = oz0_doc
            beru.engorde_peldaño_offset = 0
            masa, _ = _preparar_engorde_desde_oz(beru, precio=px, base=base)
            masa = _limitar_masa_viva(masa, beru)
            return _plantar_trailing(
                beru, short=short, masa=masa, precio_activacion=px,
                ancla_engorde=oz0_doc,
            )
        # Normal / feria: masa fija de nacimiento; engorde desde activación.
        masa = _limitar_masa_viva(float(base), beru)
        return _plantar_trailing(
            beru, short=short, masa=masa, precio_activacion=px, ancla_engorde=None,
        )

    if lado == "ABAJO":
        px, base = _px_y_base(False, sangre_px or precio_desde_cero(beru, -vac))
        return _arm(False, px, base, "ABAJO")
    if lado == "ARRIBA":
        px, base = _px_y_base(True, sangre_px or precio_desde_cero(beru, vac))
        return _arm(True, px, base, "ARRIBA")
    oz_dir = str(getattr(beru, "ultima_hoz_direccion", "") or "").upper()
    if oz_dir == "SHORT":
        px, base = _px_y_base(False, float(precio or 0) or precio_desde_cero(beru, -vac))
        return _arm(False, px, base, "ABAJO")
    if oz_dir == "LONG":
        px, base = _px_y_base(True, float(precio or 0) or precio_desde_cero(beru, vac))
        return _arm(True, px, base, "ARRIBA")
    return 0.0


def armar_tramo_desde_red(beru: Any, precio: float | None = None) -> float:
    """Red → trailing; hasta_oz: masa hasta Oz (~0,5 % desde Oz-0 del tramo).

    Por defecto Red siempre chama (involución 100/300 solo achica nacimiento).
    Solo si hay ``BERU_RANGO_RED_TOPE_PIERNA_USD`` explícito y la pierna same-side
    lo supera, no reengorda Red — la sangre (contraria) sigue libre.
    """
    red = float(getattr(beru, "red_adan", 0) or 0)
    px = float(precio or 0) or red
    if px <= 0:
        return 0.0
    d = str(getattr(beru, "ultima_hoz_direccion", "") or "").upper()
    if d not in ("LONG", "SHORT"):
        return 0.0
    if red_bloqueada_por_pierna(beru):
        return 0.0
    beru.origen_tramo = "RED"
    short = d == "SHORT"
    if engorde_modo_hasta_oz():
        masa = masa_arm_hasta_oz(beru, px, short=short)
        oz0 = _asegurar_oz0_wake(beru)
        if masa <= 1e-12:
            return 0.0
        out = _plantar_trailing(
            beru, short=short, masa=masa, precio_activacion=px,
            ancla_engorde=oz0 if oz0 > 0 else None,
        )
        if out > 0:
            beru.rango_escalones_red = int(getattr(beru, "rango_escalones_red", 0) or 0) + 1
        return out
    if engorde_modo_peldaños_sumados():
        from core import beru_rango_semaforo as sem

        base = sem.preparar_nacimiento_tramo(beru, precio=px)
    else:
        base = masa_red_usd()
    masa, oz0 = _preparar_engorde_desde_oz(beru, precio=px, base=base)
    if not engorde_modo_peldaños_sumados():
        masa = orden_nacimiento_usd(beru, lado=d, precio=px, origen="RED")
    else:
        masa = _limitar_masa_viva(masa, beru)
    if masa <= 1e-12:
        return 0.0
    if d == "SHORT":
        out = _plantar_trailing(
            beru, short=True, masa=masa, precio_activacion=px, ancla_engorde=oz0 or None,
        )
    else:
        out = _plantar_trailing(
            beru, short=False, masa=masa, precio_activacion=px, ancla_engorde=oz0 or None,
        )
    if out > 0:
        beru.rango_escalones_red = int(getattr(beru, "rango_escalones_red", 0) or 0) + 1
    return out


def resumen_geometria() -> dict[str, float | str]:
    perfil = str(getattr(config, "BERU_RANGO_PERFIL", "normal") or "normal")
    red_long = red_activacion_pct("LONG")
    red_short = red_activacion_pct("SHORT")
    masa = masa_tramo_usd()
    tope = engorde_tope_usd()
    if masa <= 0.25:
        nacimiento = "piedra_usd"
    elif abs(masa - 5.0) < 0.01:
        nacimiento = "cinco_usd"
    else:
        nacimiento = f"masa_{masa:g}"
    out: dict[str, float | str] = {
        "oficio": "RANGO",
        "perfil": perfil,
        "mercado": str(getattr(config, "BERU_RANGO_MERCADO", "linear") or "linear").lower(),
        "vacio_pct": vacio_adan_pct(),
        "vacio_rol": "activacion_trailing",
        "oz_gap_pct": trailing_dist_pct(),
        "oz_modo": "trailing_callback",
        "red_activacion_pct": red_long,
        "red_activacion_long_pct": red_long,
        "red_activacion_short_pct": red_short,
        "red_desde_oz_pct": red_long,
        "red_modo": "trailing",
        "red_callback_pct": trailing_dist_pct(),
        "sangre_pct": sangre_contraria_pct(),
        "sangre_rol": "activacion_trailing",
        "sangre_estiron": "on" if sangre_estiron_activo() else "off",
        "sangre_estiron_paso_pct": sangre_estiron_paso_pct(),
        "sangre_estiron_tick_pct": sangre_estiron_tick_pct(),
        "masa_usd": masa,
        "masa_red_usd": masa_red_usd(),
        "masa_sangre_usd": masa_sangre_usd(),
        "trailing_pct": trailing_dist_pct(),
        "engorde_usd": engorde_paso_usd(),
        "engorde_paso_pct": engorde_paso_pct(),
        "engorde_modo": (
            "peldaños_sumados"
            if engorde_modo_peldaños_sumados()
            else ("hasta_oz" if engorde_modo_hasta_oz() else "linear")
        ),
        "engorde_tope_usd": tope,
        "piedra_tier": str(getattr(config, "BERU_RANGO_PIEDRA_TIER", "") or ""),
        "cero": "wake",
        "nacimiento": (
            "hasta_oz_peldaños"
            if engorde_modo_hasta_oz()
            else nacimiento
        ),
        "engorde": (
            "hasta_oz"
            if engorde_modo_hasta_oz()
            else "desde_activacion"
        ),
        "masa_paso_mar_usd": masa_paso_mar_usd(),
        "saco_techo": (
            "peldaños_sumados"
            if engorde_modo_peldaños_sumados()
            else ("engorde_tope" if tope > 0 else "sin_tope")
        ),
        "ladder_red": "si",
    }
    if engorde_modo_peldaños_sumados():
        from core import beru_rango_semaforo as sem

        sm = sem.resumen_semaforo()
        out["semaforo_default"] = str(sm.get("semaforo", "amarillo"))
        out["masa_nacimiento_paz"] = float(sm.get("masa_nacimiento", 0.30))
        out["tope_serie_default"] = float(sm.get("tope_serie", 0.80))
        out["pierna_umbral_medio"] = float(sm.get("umbral_medio", 100.0))
        out["pierna_umbral_pesado"] = float(sm.get("umbral_pesado", 300.0))
    return out
