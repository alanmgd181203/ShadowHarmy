"""Igris Escudo BTC — contador puro (viejita + lab).

Beru no se toca. Igris mira el acumulado neto de Beru y calcula la meta
de cobertura en BTC (lado contrario × relación R).

No es el manto clásico L/S por Santo: es otro oficio (cobertura BTC de la
masa abierta de la legión).

R (Monarca 2026-09-23/24):
  · Lab/teatro: ``IGRIS_ESCUDO_BTC_R=1.0`` (u otro número) fija la relación.
  · Viejita (convivencia): ``IGRIS_ESCUDO_BTC_R=dinamico`` **o**
    ``IGRIS_ESCUDO_BTC_R_DINAMICO=1`` → TOTAL3/BTC con under-hedging
    (redondeo décima − 0.2, piso 1.0). Ver ``core.factor_relacion_r``.
  · Default config sin override: 1,5 fija (legado).

Gatillo de rebalanceo (Monarca 2026-09-23):
  · cada X dólares de movimiento del acumulado, O
  · cada X % de movimiento del acumulado (respecto a la ancla del último ajuste).
"""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import core.config as config


# --- Parámetros doctrinales (env / config; defaults del Monarca) ------------


def _r_dinamico_activo(env_val: str | None) -> bool:
    if env_val is None:
        return False
    s = str(env_val).strip().lower()
    return s in ("dinamico", "dynamic", "auto", "total3", "1", "true", "on", "si", "yes")


def escudo_relacion() -> float:
    """R = nocional_escudo / |acumulado_beru|.

    Prioridad:
      1. ``IGRIS_ESCUDO_BTC_R`` numérico (lab) o ``dinamico``
      2. ``IGRIS_ESCUDO_BTC_R_DINAMICO=1`` → factor TOTAL3 con descuento
      3. config fija (default 1,5)
    """
    raw = os.getenv("IGRIS_ESCUDO_BTC_R")
    if raw is not None and str(raw).strip() != "":
        s = str(raw).strip()
        if _r_dinamico_activo(s) and not s.replace(".", "", 1).isdigit():
            try:
                from core.factor_relacion_r import calcular_r

                return float(calcular_r())
            except Exception:
                return 1.0
        try:
            return max(0.0, float(s))
        except (TypeError, ValueError):
            return 1.0

    if _r_dinamico_activo(os.getenv("IGRIS_ESCUDO_BTC_R_DINAMICO")):
        try:
            from core.factor_relacion_r import calcular_r

            return float(calcular_r())
        except Exception:
            return 1.0

    return max(
        0.0,
        float(getattr(config, "IGRIS_ESCUDO_BTC_R", 1.5) or 1.5),
    )


def escudo_umbral_usd() -> float:
    """Cada cuántos USD de cambio en el acumulado Beru se rebalancea (0 = apagado)."""
    return max(
        0.0,
        float(
            os.getenv("IGRIS_ESCUDO_BTC_UMBRAL_USD")
            or getattr(config, "IGRIS_ESCUDO_BTC_UMBRAL_USD", 100.0)
            or 100.0
        ),
    )


def escudo_umbral_pct() -> float:
    """Cada cuánto % de cambio del acumulado (vs ancla) se rebalancea (0 = apagado).

    0.01 = 1 %. Se mide sobre |ancla|; si ancla≈0, solo manda el umbral USD.
    """
    return max(
        0.0,
        float(
            os.getenv("IGRIS_ESCUDO_BTC_UMBRAL_PCT")
            or getattr(config, "IGRIS_ESCUDO_BTC_UMBRAL_PCT", 0.01)
            or 0.01
        ),
    )


def escudo_polvo_usd() -> float:
    """Debajo de esto el acumulado cuenta como neutro (escudo 0)."""
    return max(
        0.0,
        float(
            os.getenv("IGRIS_ESCUDO_BTC_POLVO_USD")
            or getattr(config, "IGRIS_ESCUDO_BTC_POLVO_USD", 1.0)
            or 1.0
        ),
    )


def escudo_ord_tipo() -> str:
    """Tipo de orden del escudo BTC.

    Monarca 2026-09-24: entradas a **market** (fill inmediato).
    ``limit`` sigue disponible si se fuerza por env.
    """
    raw = str(
        os.getenv("IGRIS_ESCUDO_BTC_ORD_TIPO")
        or getattr(config, "IGRIS_ESCUDO_BTC_ORD_TIPO", "market")
        or "market"
    ).strip().lower()
    if raw in ("limit", "limitado", "maker", "post_only", "postonly"):
        return "limit"
    if raw in ("market", "mercado", "asalto", "taker"):
        return "market"
    return "market"


def escudo_limit_mover_activo() -> bool:
    """Si el límite no llena, Igris puede acercarlo al precio (sigue limit)."""
    env = os.getenv("IGRIS_ESCUDO_BTC_LIMIT_MOVER")
    if env is not None and str(env).strip() != "":
        return str(env).strip().lower() in ("1", "true", "yes", "on", "si", "sí")
    return bool(getattr(config, "IGRIS_ESCUDO_BTC_LIMIT_MOVER", True))


def escudo_limit_espera_s() -> float:
    """Segundos sin fill antes del primer (o siguiente) movimiento."""
    return max(
        1.0,
        float(
            os.getenv("IGRIS_ESCUDO_BTC_LIMIT_ESPERA_S")
            or getattr(config, "IGRIS_ESCUDO_BTC_LIMIT_ESPERA_S", 20.0)
            or 20.0
        ),
    )


def escudo_limit_paso_pct() -> float:
    """Cuánto acerca cada movimiento (fracción del mid). Default 0,03 %."""
    return max(
        0.0,
        float(
            os.getenv("IGRIS_ESCUDO_BTC_LIMIT_PASO_PCT")
            or getattr(config, "IGRIS_ESCUDO_BTC_LIMIT_PASO_PCT", 0.0003)
            or 0.0003
        ),
    )


def escudo_limit_max_moves() -> int:
    return max(
        0,
        int(
            float(
                os.getenv("IGRIS_ESCUDO_BTC_LIMIT_MAX_MOVES")
                or getattr(config, "IGRIS_ESCUDO_BTC_LIMIT_MAX_MOVES", 30)
                or 30
            )
        ),
    )


def escudo_limit_max_drift_pct() -> float:
    """Tope de distancia desde el px de origen al acercar (no persigue infinito)."""
    return max(
        0.0,
        float(
            os.getenv("IGRIS_ESCUDO_BTC_LIMIT_MAX_DRIFT_PCT")
            or getattr(config, "IGRIS_ESCUDO_BTC_LIMIT_MAX_DRIFT_PCT", 0.008)
            or 0.008
        ),
    )


def escudo_limit_offset_pct() -> float:
    """Holgura maker inicial vs mid (compra bajo / vende alto)."""
    return max(
        0.0,
        float(
            os.getenv("IGRIS_ESCUDO_BTC_LIMIT_OFFSET_PCT")
            or getattr(config, "IGRIS_ESCUDO_BTC_LIMIT_OFFSET_PCT", 0.0002)
            or 0.0002
        ),
    )


def precio_limite_inicial(lado: str, mid: float) -> float:
    """Px maker inicial: LONG bajo el mid, SHORT arriba del mid."""
    m = float(mid or 0)
    if m <= 0:
        return 0.0
    off = escudo_limit_offset_pct()
    lado_u = str(lado or "").upper()
    if lado_u == "LONG":
        return m * (1.0 - off)
    if lado_u == "SHORT":
        return m * (1.0 + off)
    return m


@dataclass
class LimiteEscudoPendiente:
    """Orden límite del escudo aún sin fill — puede moverse (nunca a market)."""

    lado: str = ""
    qty: float = 0.0
    px: float = 0.0
    px_origen: float = 0.0
    ts_planta: float = 0.0
    ts_ultimo_mov: float = 0.0
    n_moves: int = 0
    meta_usd: float = 0.0
    filled: bool = False
    cancelado: bool = False

    def vivo(self) -> bool:
        return (
            not self.filled
            and not self.cancelado
            and str(self.lado or "").upper() in ("LONG", "SHORT")
            and float(self.qty or 0) > 0
            and float(self.px or 0) > 0
        )


def plantar_limite_escudo(
    lado: str,
    qty: float,
    mid: float,
    *,
    meta_usd: float = 0.0,
    ahora: float | None = None,
) -> LimiteEscudoPendiente:
    """Planta un límite maker (siempre limit)."""
    ahora = float(ahora if ahora is not None else time.time())
    px = precio_limite_inicial(lado, mid)
    return LimiteEscudoPendiente(
        lado=str(lado or "").upper(),
        qty=float(qty or 0),
        px=float(px),
        px_origen=float(px),
        ts_planta=ahora,
        ts_ultimo_mov=ahora,
        n_moves=0,
        meta_usd=float(meta_usd or 0),
        filled=False,
        cancelado=False,
    )


def decidir_mover_limite(
    pendiente: LimiteEscudoPendiente | None,
    mid: float,
    *,
    ahora: float | None = None,
) -> dict[str, Any]:
    """¿Conviene acercar el límite al mid? Sigue siendo limit (maker).

    Reglas (Monarca):
      · Solo si ``escudo_limit_mover_activo``.
      · Espera ``espera_s`` desde planta o último movimiento.
      · LONG: sube el px hacia el mid (sin cruzarlo con holgura maker).
      · SHORT: baja el px hacia el mid (sin cruzarlo).
      · Tope de movimientos y de drift desde el px de origen.
      · Nunca convierte a market.
    """
    ahora = float(ahora if ahora is not None else time.time())
    mid = float(mid or 0)
    if pendiente is None or not pendiente.vivo():
        return {
            "mover": False,
            "motivo": "sin_pendiente",
            "ordType": escudo_ord_tipo(),
        }
    if not escudo_limit_mover_activo():
        return {
            "mover": False,
            "motivo": "mover_apagado",
            "px": pendiente.px,
            "ordType": escudo_ord_tipo(),
        }
    if mid <= 0:
        return {
            "mover": False,
            "motivo": "sin_mid",
            "px": pendiente.px,
            "ordType": escudo_ord_tipo(),
        }
    max_m = escudo_limit_max_moves()
    if int(pendiente.n_moves) >= max_m:
        return {
            "mover": False,
            "motivo": "max_moves",
            "n_moves": pendiente.n_moves,
            "px": pendiente.px,
            "ordType": escudo_ord_tipo(),
        }
    espera = escudo_limit_espera_s()
    ref_ts = float(pendiente.ts_ultimo_mov or pendiente.ts_planta or 0)
    if ahora - ref_ts + 1e-9 < espera:
        return {
            "mover": False,
            "motivo": "espera",
            "faltan_s": round(espera - (ahora - ref_ts), 1),
            "px": pendiente.px,
            "ordType": escudo_ord_tipo(),
        }

    off = escudo_limit_offset_pct()
    paso = mid * escudo_limit_paso_pct()
    if paso <= 0:
        return {
            "mover": False,
            "motivo": "paso_cero",
            "px": pendiente.px,
            "ordType": escudo_ord_tipo(),
        }

    lado = str(pendiente.lado or "").upper()
    px_old = float(pendiente.px)
    px_origen = float(pendiente.px_origen or px_old)
    drift_max = escudo_limit_max_drift_pct()

    if lado == "LONG":
        # Maker buy: nunca ≥ mid; techo maker = mid*(1-off)
        techo = mid * (1.0 - off)
        px_new = min(px_old + paso, techo)
        if px_new <= px_old + 1e-12:
            return {
                "mover": False,
                "motivo": "ya_en_techo_maker",
                "px": px_old,
                "mid": mid,
                "ordType": escudo_ord_tipo(),
            }
        if abs(px_new - px_origen) / max(px_origen, 1e-12) > drift_max + 1e-15:
            return {
                "mover": False,
                "motivo": "max_drift",
                "px": px_old,
                "ordType": escudo_ord_tipo(),
            }
    elif lado == "SHORT":
        piso = mid * (1.0 + off)
        px_new = max(px_old - paso, piso)
        if px_new >= px_old - 1e-12:
            return {
                "mover": False,
                "motivo": "ya_en_piso_maker",
                "px": px_old,
                "mid": mid,
                "ordType": escudo_ord_tipo(),
            }
        if abs(px_new - px_origen) / max(px_origen, 1e-12) > drift_max + 1e-15:
            return {
                "mover": False,
                "motivo": "max_drift",
                "px": px_old,
                "ordType": escudo_ord_tipo(),
            }
    else:
        return {
            "mover": False,
            "motivo": "lado_invalido",
            "ordType": escudo_ord_tipo(),
        }

    return {
        "mover": True,
        "motivo": "acercar",
        "px_antes": px_old,
        "px_nuevo": float(px_new),
        "mid": mid,
        "lado": lado,
        "n_moves_despues": int(pendiente.n_moves) + 1,
        "ordType": escudo_ord_tipo(),  # sigue limit
        "frase": (
            f"mueve limit {lado} {px_old:.2f} → {px_new:.2f} "
            f"(mid {mid:.2f}, move #{int(pendiente.n_moves) + 1})"
        ),
    }


def aplicar_mover_limite(
    pendiente: LimiteEscudoPendiente,
    decision: dict[str, Any],
    *,
    ahora: float | None = None,
) -> LimiteEscudoPendiente:
    """Aplica un movimiento de límite en memoria (sim / pre-cable)."""
    ahora = float(ahora if ahora is not None else time.time())
    if not decision.get("mover"):
        return pendiente
    pendiente.px = float(decision.get("px_nuevo") or pendiente.px)
    pendiente.ts_ultimo_mov = ahora
    pendiente.n_moves = int(pendiente.n_moves) + 1
    return pendiente


def escudo_peldaño_usd() -> float:
    """Ancho del peldaño del escudo (USD).

    Sellado Monarca 2026-09-29: **$250**. El polvo sigue en 250.
    La meta no usa el piso en cada latido: ver ``neto_peldaño_atrasado``.
    """
    return max(
        1.0,
        float(
            os.getenv("IGRIS_ESCUDO_BTC_PELDANO_USD")
            or os.getenv("IGRIS_ESCUDO_BTC_PELDAÑO_USD")
            or getattr(config, "IGRIS_ESCUDO_BTC_PELDAÑO_USD", 250.0)
            or 250.0
        ),
    )


def escudo_activar_usd() -> float:
    """Primera silla: hay que pasar el polvo y un escalón más. No es el mismo dólar."""
    return max(
        0.0,
        float(
            os.getenv("IGRIS_ESCUDO_BTC_ACTIVAR_USD")
            or getattr(config, "IGRIS_ESCUDO_BTC_ACTIVAR_USD", 500.0)
            or 500.0
        ),
    )


def neto_peldaño_atrasado(
    neto: float,
    *,
    peldaño: float | None = None,
    activar: float | None = None,
    armado: bool = False,
    lado_armado: str = "",
    asentado: float | None = None,
) -> tuple[float, bool, str]:
    """Traduce neto Beru → neto efectivo del escudo.

    Sin asiento: piso (floor). Se arma al llegar a ``activar`` ($1000).
    Con asiento S: quieto mientras el neto real esté entre S−peldaño y
    S+peldaño, sin tocarlos. Al tocar el de arriba o el de abajo, el asiento
    nuevo es el piso del neto real (puede saltar más de un peldaño si el
    desbalance de verdad caminó). |neto| ≤ polvo o volteo de lado → 0.
    """
    import math

    p = float(peldaño) if peldaño is not None else escudo_peldaño_usd()
    act = float(activar) if activar is not None else escudo_activar_usd()
    p = max(1.0, p)
    n = float(neto or 0)
    polvo = float(escudo_polvo_usd() or 0)
    if polvo > 0 and abs(n) <= polvo + 1e-9:
        return 0.0, False, ""
    if abs(n) < 1e-12:
        return 0.0, False, ""
    # Lado Beru real (espejo): +acum → Beru SHORT
    lado_beru = "SHORT" if n > 0 else "LONG"
    lado_a = str(lado_armado or "").upper()
    if armado and lado_a and lado_beru != lado_a:
        return 0.0, False, ""
    stepped = math.floor(abs(n) / p + 1e-15) * p

    def _firmado(abs_step: float) -> tuple[float, bool, str]:
        if abs_step < 1e-12 or abs_step + 1e-12 < act:
            return 0.0, False, ""
        signed = abs_step if n > 0 else -abs_step
        return float(signed), True, lado_beru

    if not armado or asentado is None:
        return _firmado(stepped)

    S = abs(float(asentado))
    if S >= 1e-12:
        S = math.floor(S / p + 1e-15) * p
    if S < 1e-12:
        return _firmado(stepped)
    # Franja abierta: (S − peldaño, S + peldaño). En los bordes sí se mueve.
    lo = S - p
    hi = S + p
    if (lo + 1e-6) < abs(n) < (hi - 1e-6):
        return _firmado(S)
    return _firmado(stepped)



# --- Acumulado Beru --------------------------------------------------------


def acumulado_beru_neto(long_usd: float, short_usd: float) -> float:
    """Neto Beru en USD. Signo: + = más short; − = más long; 0 = neutro.

    Entrada: **posición abierta** (balanza OKX / masa del tramo).
    No usar el saco-ledger de cosechas: eso ya está realizado.
    """
    lo = max(0.0, float(long_usd or 0))
    sh = max(0.0, float(short_usd or 0))
    return sh - lo


def acumulado_efectivo(neto: float, *, polvo_usd: float | None = None) -> float:
    """Aplica polvo: |neto| < polvo → 0 (no pelear migajas)."""
    n = float(neto or 0)
    polvo = float(polvo_usd) if polvo_usd is not None else escudo_polvo_usd()
    if abs(n) + 1e-12 < polvo:
        return 0.0
    return n


# --- Meta escudo BTC -------------------------------------------------------


@dataclass(frozen=True)
class MetaEscudoBtc:
    """Meta de cobertura BTC para Igris."""

    lado: str  # LONG | SHORT | "" (neutro)
    usd: float  # nocional absoluto ≥ 0
    relacion: float
    acumulado_beru: float  # neto efectivo que originó la meta

    @property
    def signed_usd(self) -> float:
        """+ long BTC, − short BTC, 0 neutro."""
        if self.lado == "LONG":
            return float(self.usd)
        if self.lado == "SHORT":
            return -float(self.usd)
        return 0.0


def meta_escudo_btc(
    acumulado_beru: float,
    *,
    relacion: float | None = None,
    polvo_usd: float | None = None,
) -> MetaEscudoBtc:
    """Beru short → BTC long; Beru long → BTC short; neutro → 0.

    meta_usd = |acumulado_efectivo| × R
    """
    r = float(relacion) if relacion is not None else escudo_relacion()
    r = max(0.0, r)
    neto = acumulado_efectivo(acumulado_beru, polvo_usd=polvo_usd)
    if abs(neto) < 1e-12 or r <= 0:
        return MetaEscudoBtc(lado="", usd=0.0, relacion=r, acumulado_beru=0.0)
    usd = abs(neto) * r
    # neto + = Beru más short → escudo LONG BTC
    lado = "LONG" if neto > 0 else "SHORT"
    return MetaEscudoBtc(lado=lado, usd=float(usd), relacion=r, acumulado_beru=float(neto))


# --- Gatillo de rebalanceo -------------------------------------------------


@dataclass(frozen=True)
class DecisionRebalanceo:
    """¿Hay que ajustar el escudo BTC?"""

    debe: bool
    motivo: str  # "" | usd | pct | ambos | primera
    delta_usd: float
    delta_pct: float  # fracción vs |ancla|; 0 si ancla≈0
    acumulado_ahora: float
    acumulado_ancla: float
    meta: MetaEscudoBtc


def _delta_pct(ahora: float, ancla: float) -> float:
    base = abs(float(ancla or 0))
    if base < 1e-9:
        return 0.0
    return abs(float(ahora) - float(ancla)) / base


def debe_rebalancear_escudo(
    acumulado_ahora: float,
    acumulado_ancla: float | None,
    *,
    umbral_usd: float | None = None,
    umbral_pct: float | None = None,
    relacion: float | None = None,
    polvo_usd: float | None = None,
    escudo_vivo_signed_usd: float | None = None,
) -> DecisionRebalanceo:
    """True si el acumulado Beru se movió ≥ umbral USD **o** ≥ umbral %.

    También True si ``escudo_vivo_signed_usd`` viene y el bocado vs meta
    (``|target_igris − igris_vivo|``) ≥ umbral USD — rearme por desviación
    (God Mode / teatro: Igris no espera Oz; sigue la masa de Beru).

    - Primera vez (ancla is None): siempre debe (plantar escudo inicial).
    - Ambos umbrales en 0: nunca (salvo primera o desviación con umbral>0).
    - Tras ajustar, el llamador debe **sellar ancla = acumulado_ahora**.
    """
    ahora = acumulado_efectivo(acumulado_ahora, polvo_usd=polvo_usd)
    meta = meta_escudo_btc(ahora, relacion=relacion, polvo_usd=polvo_usd)
    u_usd = float(umbral_usd) if umbral_usd is not None else escudo_umbral_usd()
    u_pct = float(umbral_pct) if umbral_pct is not None else escudo_umbral_pct()
    polvo = float(polvo_usd) if polvo_usd is not None else escudo_polvo_usd()
    # Mínimo para que Igris mueva manos: polvo (lab: desde ~$1, no ±100)
    min_engage = max(polvo, 1e-9)

    if acumulado_ancla is None:
        # Duerme solo si aún no hay neto (bajo el polvo, p.ej. <$1)
        if abs(ahora) + 1e-12 < min_engage:
            return DecisionRebalanceo(
                debe=False,
                motivo="",
                delta_usd=0.0,
                delta_pct=0.0,
                acumulado_ahora=ahora,
                acumulado_ancla=0.0,
                meta=meta,
            )
        return DecisionRebalanceo(
            debe=True,
            motivo="primera",
            delta_usd=0.0,
            delta_pct=0.0,
            acumulado_ahora=ahora,
            acumulado_ancla=0.0,
            meta=meta,
        )

    ancla = acumulado_efectivo(float(acumulado_ancla), polvo_usd=polvo_usd)
    d_usd = abs(ahora - ancla)
    d_pct = _delta_pct(ahora, ancla)

    # Apertura: neto efectivo cruza el polvo (lab desde ~$1)
    if abs(ancla) < 1e-9 and abs(ahora) + 1e-12 >= min_engage:
        return DecisionRebalanceo(
            debe=True,
            motivo="apertura",
            delta_usd=float(abs(ahora)),
            delta_pct=0.0,
            acumulado_ahora=ahora,
            acumulado_ancla=ancla,
            meta=meta,
        )
    # Cierre: solo cuando el neto cae a polvo (~0), no al bajar de $100
    if abs(ahora) < 1e-9 and abs(ancla) + 1e-12 >= min_engage:
        return DecisionRebalanceo(
            debe=True,
            motivo="cierre",
            delta_usd=float(abs(ancla)),
            delta_pct=0.0,
            acumulado_ahora=ahora,
            acumulado_ancla=ancla,
            meta=meta,
        )

    por_usd = u_usd > 0 and d_usd + 1e-12 >= u_usd
    por_pct = u_pct > 0 and d_pct + 1e-15 >= u_pct
    # Rearme por desfase Igris vs meta (mismo umbral USD doctrinal)
    desv_escudo = 0.0
    por_desv = False
    if escudo_vivo_signed_usd is not None and u_usd > 0:
        desv_escudo = abs(float(meta.signed_usd) - float(escudo_vivo_signed_usd))
        por_desv = desv_escudo + 1e-12 >= u_usd

    if por_desv and not (por_usd or por_pct):
        motivo = "desviacion"
    elif por_usd and por_pct:
        motivo = "ambos"
    elif por_usd:
        motivo = "usd"
    elif por_pct:
        motivo = "pct"
    elif por_desv:
        motivo = "desviacion"
    else:
        motivo = ""

    return DecisionRebalanceo(
        debe=bool(por_usd or por_pct or por_desv),
        motivo=motivo,
        delta_usd=float(max(d_usd, desv_escudo) if por_desv else d_usd),
        delta_pct=float(d_pct),
        acumulado_ahora=ahora,
        acumulado_ancla=ancla,
        meta=meta,
    )


def bocado_ajuste_usd(meta: MetaEscudoBtc, escudo_vivo_signed_usd: float) -> float:
    """Cuánto falta para la meta (signed): + hay que comprar/aumentar long BTC.

    ``escudo_vivo_signed_usd``: + long vivo, − short vivo (misma convención que meta.signed_usd).
    """
    return float(meta.signed_usd) - float(escudo_vivo_signed_usd or 0)


# --- Ojos: ver el manto / acumulado Beru ------------------------------------


@dataclass(frozen=True)
class VisionMantoBeru:
    """Lo que Igris ve de la posición abierta Beru (balanza sin BTC)."""

    long_usd: float
    short_usd: float
    acumulado_neto: float  # + short dominante
    acumulado_efectivo: float
    fuente: str
    frase: str
    ts: float
    ok: bool
    aviso: str = ""


def vision_desde_snap(snap: dict[str, Any] | None) -> VisionMantoBeru:
    """Traduce un snap de balanza (OKX / eco / sellos) al lenguaje del escudo."""
    if not isinstance(snap, dict) or not snap:
        return VisionMantoBeru(
            long_usd=0.0,
            short_usd=0.0,
            acumulado_neto=0.0,
            acumulado_efectivo=0.0,
            fuente="",
            frase="sin_snap",
            ts=0.0,
            ok=False,
            aviso="sin_snap",
        )
    lo = float(snap.get("long_usd") or 0)
    sh = float(snap.get("short_usd") or 0)
    neto = acumulado_beru_neto(lo, sh)
    # Preferir neto de balanza si trae net_long (signo inverso: long−short)
    # Escudo usa short−long; no mezclar. Siempre recalcular.
    ef = acumulado_efectivo(neto)
    return VisionMantoBeru(
        long_usd=lo,
        short_usd=sh,
        acumulado_neto=neto,
        acumulado_efectivo=ef,
        fuente=str(snap.get("fuente") or ""),
        frase=str(snap.get("frase") or ""),
        ts=float(snap.get("ts") or 0),
        ok=True,
        aviso=str(snap.get("aviso") or ""),
    )


def mirar_manto_beru(
    *,
    live: bool = True,
    max_age_s: float = 600.0,
    snap: dict[str, Any] | None = None,
) -> VisionMantoBeru:
    """Igris abre los ojos al acumulado Beru.

    - ``snap``: si viene, no toca red (teatro / tests).
    - ``live=True``: balanza OKX (o eco / sellos si falla).
    - ``live=False``: solo lee el sello ``balanza_legion.json`` si existe.
    """
    if snap is not None:
        return vision_desde_snap(snap)

    from core import beru_rango_balanza as balanza
    from core import beru_rango_paths as paths

    if live:
        try:
            s = balanza.medir_balanza(max_age_s=max_age_s)
            return vision_desde_snap(s)
        except Exception as exc:
            # Último recurso: disco
            try:
                p = paths.balanza_legion()
                if p.exists():
                    import json

                    data = json.loads(p.read_text(encoding="utf-8"))
                    v = vision_desde_snap(data)
                    return VisionMantoBeru(
                        long_usd=v.long_usd,
                        short_usd=v.short_usd,
                        acumulado_neto=v.acumulado_neto,
                        acumulado_efectivo=v.acumulado_efectivo,
                        fuente=v.fuente or "disco",
                        frase=v.frase,
                        ts=v.ts,
                        ok=v.ok,
                        aviso=f"live_fallo:{exc}",
                    )
            except Exception:
                pass
            return VisionMantoBeru(
                long_usd=0.0,
                short_usd=0.0,
                acumulado_neto=0.0,
                acumulado_efectivo=0.0,
                fuente="",
                frase="",
                ts=0.0,
                ok=False,
                aviso=f"ciego:{exc}",
            )

    # solo disco
    try:
        import json

        p = paths.balanza_legion()
        if not p.exists():
            return VisionMantoBeru(
                long_usd=0.0,
                short_usd=0.0,
                acumulado_neto=0.0,
                acumulado_efectivo=0.0,
                fuente="",
                frase="sin_sello_balanza",
                ts=0.0,
                ok=False,
                aviso="sin_sello_balanza",
            )
        data = json.loads(p.read_text(encoding="utf-8"))
        return vision_desde_snap(data)
    except Exception as exc:
        return VisionMantoBeru(
            long_usd=0.0,
            short_usd=0.0,
            acumulado_neto=0.0,
            acumulado_efectivo=0.0,
            fuente="",
            frase="",
            ts=0.0,
            ok=False,
            aviso=f"disco_fallo:{exc}",
        )


def _fila_es_escudo_btc(inst: str) -> bool:
    """BTC-USD-SWAP (inverso) o BTC-USDT-SWAP (lineal)."""
    inst_u = str(inst or "").strip().upper()
    if inst_u in ("BTC-USDT-SWAP", "BTC-USD-SWAP"):
        return True
    if not inst_u.startswith("BTC-") or not inst_u.endswith("-SWAP"):
        return False
    return "USDT" in inst_u or inst_u == "BTC-USD-SWAP"


def _nocional_usd_fila_escudo(row: dict[str, Any]) -> float:
    """Nocional abs de una pierna BTC. Si notionalUsd viene 0 tras fill, usa pos×ctVal."""
    pos = abs(float(row.get("pos") or 0))
    if pos <= 1e-12:
        return 0.0
    nu = abs(float(row.get("notionalUsd") or 0))
    if nu > 1e-9:
        return nu
    inst = str(row.get("instId") or "").upper()
    # Inverso OKX: face USD = |pos| × ctVal (ctVal=100)
    if inst == "BTC-USD-SWAP" or ("USD-SWAP" in inst and "USDT" not in inst):
        ct = float(filtros_escudo_btc("inverso").get("ctVal") or 100)
        return float(pos) * ct
    # Lineal: |pos| × ctVal × px
    px = float(row.get("markPx") or row.get("last") or row.get("avgPx") or 0)
    ct = float(filtros_escudo_btc("lineal").get("ctVal") or 0.01)
    if px > 0 and ct > 0:
        return float(pos) * ct * px
    return 0.0


def mirar_escudo_btc_detalle_okx() -> dict[str, Any]:
    """Ojo del escudo BTC con candado anti-ceguera.

    - ``ciego=True``: API falló / sin llaves → **no** inventar 0 (tumor de doble asalto).
    - ``ciego=False`` + signed=0: casa confirma plano (piernas vacías).
    - Si hay ``pos`` pero ``notionalUsd`` aún en 0 (post-market), estima por contratos.
    """
    try:
        from core import okx_rest

        if not okx_rest.credenciales_ok():
            return {
                "ok": False,
                "ciego": True,
                "signed": None,
                "fuente": "sin_credenciales",
                "aviso": "sin_credenciales_okx",
            }
        rows = okx_rest.get_private(
            "/api/v5/account/positions", params={"instType": "SWAP"}
        )
    except Exception as exc:
        return {
            "ok": False,
            "ciego": True,
            "signed": None,
            "fuente": "okx_error",
            "aviso": str(exc)[:160],
        }

    signed = 0.0
    n_piernas = 0
    for r in rows or []:
        if not isinstance(r, dict):
            continue
        if not _fila_es_escudo_btc(str(r.get("instId") or "")):
            continue
        pos = float(r.get("pos") or 0)
        if abs(pos) <= 1e-12:
            continue
        nu = _nocional_usd_fila_escudo(r)
        if nu <= 1e-12:
            continue
        n_piernas += 1
        side = str(r.get("posSide") or "net").lower()
        if side == "long" or (side == "net" and pos > 0):
            signed += nu
        else:
            signed -= nu
    return {
        "ok": True,
        "ciego": False,
        "signed": float(signed),
        "piernas": n_piernas,
        "fuente": "okx_positions",
        "aviso": "",
    }


def mirar_escudo_btc_vivo_okx() -> float:
    """Nocional firmado del escudo (+ long, − short).

    Compat: si el ojo está ciego devuelve ``0.0`` — preferir
    ``mirar_escudo_btc_detalle_okx`` en latidos live (no plantar a ciegas).
    """
    det = mirar_escudo_btc_detalle_okx()
    if det.get("ciego"):
        return 0.0
    return float(det.get("signed") or 0.0)


def escudo_veda_s() -> float:
    """Segundos de veda tras plantar (anti ida-vuelta). Default 25s ≈ 1–2 latidos."""
    return max(
        0.0,
        float(
            os.getenv("IGRIS_ESCUDO_BTC_VEDA_S")
            or getattr(config, "IGRIS_ESCUDO_BTC_VEDA_S", 25.0)
            or 25.0
        ),
    )


# --- Estado mínimo (ancla) — sin manos ------------------------------------


@dataclass
class EstadoEscudoBtc:
    """Memoria del último ajuste (ancla del acumulado Beru) + arma de peldaños."""

    acumulado_ancla: float | None = None
    meta_lado: str = ""
    meta_usd: float = 0.0
    peldaño_armado: bool = False
    peldaño_lado: str = ""  # LONG|SHORT del neto Beru al armar

    def tick(
        self,
        long_usd: float,
        short_usd: float,
        *,
        escudo_vivo_signed_usd: float | None = None,
    ) -> dict[str, Any]:
        """Un latido: neto crudo → peldaños atrasados → decide rebalanceo."""
        neto_crudo = acumulado_beru_neto(long_usd, short_usd)
        neto, armado, lado_p = neto_peldaño_atrasado(
            neto_crudo,
            armado=bool(self.peldaño_armado),
            lado_armado=str(self.peldaño_lado or ""),
            asentado=self.acumulado_ancla,
        )
        self.peldaño_armado = bool(armado)
        self.peldaño_lado = str(lado_p or "")
        vivo = 0.0 if escudo_vivo_signed_usd is None else float(escudo_vivo_signed_usd)
        # Umbral de rebalanceo por defecto = peldaño (cada escalón dispara)
        u_usd = escudo_umbral_usd()
        if u_usd <= 0:
            u_usd = escudo_peldaño_usd()
        dec = debe_rebalancear_escudo(
            neto,
            self.acumulado_ancla,
            umbral_usd=u_usd,
            polvo_usd=min(escudo_polvo_usd(), 1.0),
            escudo_vivo_signed_usd=(
                None if escudo_vivo_signed_usd is None else vivo
            ),
        )
        out: dict[str, Any] = {
            "acumulado_beru": dec.acumulado_ahora,
            "acumulado_crudo": float(neto_crudo),
            "peldaño_armado": bool(self.peldaño_armado),
            "peldaño_lado": self.peldaño_lado,
            "peldaño_usd": escudo_peldaño_usd(),
            "activar_usd": escudo_activar_usd(),
            "debe_rebalancear": dec.debe,
            "motivo": dec.motivo,
            "delta_usd": dec.delta_usd,
            "delta_pct": dec.delta_pct,
            "meta_lado": dec.meta.lado,
            "meta_usd": dec.meta.usd,
            "bocado_usd": bocado_ajuste_usd(dec.meta, vivo),
            "relacion": dec.meta.relacion,
        }
        if dec.debe:
            self.acumulado_ancla = dec.acumulado_ahora
            self.meta_lado = dec.meta.lado
            self.meta_usd = dec.meta.usd
            out["ancla_sellada"] = True
        else:
            out["ancla_sellada"] = False
        return out

    def tick_ojos(
        self,
        *,
        live: bool = True,
        leer_btc_vivo: bool = False,
        snap: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Latido con ojos: mira balanza Beru (+ opcional BTC vivo) y decide.

        Sin manos. ``live=False`` solo lee sello en disco.
        """
        vision = mirar_manto_beru(live=live, snap=snap)
        vivo_arg: float | None = None
        if leer_btc_vivo and live and snap is None:
            det = mirar_escudo_btc_detalle_okx()
            if not det.get("ciego"):
                vivo_arg = float(det.get("signed") or 0.0)
        out = self.tick(
            vision.long_usd,
            vision.short_usd,
            escudo_vivo_signed_usd=vivo_arg,
        )
        out["ojos_ok"] = vision.ok
        out["ojos_fuente"] = vision.fuente
        out["ojos_frase"] = vision.frase
        out["ojos_aviso"] = vision.aviso
        out["long_usd"] = vision.long_usd
        out["short_usd"] = vision.short_usd
        out["escudo_vivo_signed_usd"] = (
            float(vivo_arg) if vivo_arg is not None else 0.0
        )
        out["ojo_ciego"] = bool(leer_btc_vivo and vivo_arg is None and live)
        return out


# --- Modo + libro de papel (simulaciones primero) ---------------------------


def escudo_modo() -> str:
    """``sim`` (default) o ``live``. Live solo si el Monarca lo fuerza por env."""
    raw = str(
        os.getenv("IGRIS_ESCUDO_BTC_MODO")
        or getattr(config, "IGRIS_ESCUDO_BTC_MODO", "sim")
        or "sim"
    ).strip().lower()
    if raw in ("live", "real", "okx"):
        return "live"
    return "sim"


def escudo_live_permitido() -> bool:
    """Candado duro: live exige IGRIS_ESCUDO_BTC_LIVE_OK=1 además de modo live."""
    if escudo_modo() != "live":
        return False
    return str(os.getenv("IGRIS_ESCUDO_BTC_LIVE_OK", "") or "").strip() in (
        "1",
        "true",
        "yes",
        "si",
        "sí",
    )


@dataclass
class LibroEscudoSim:
    """Memoria persistente del escudo en papel (ancla + BTC firmado)."""

    acumulado_ancla: float | None = None
    meta_lado: str = ""
    meta_usd: float = 0.0
    escudo_signed_usd: float = 0.0  # + long BTC papel, − short
    n_ajustes: int = 0
    ts: float = 0.0
    modo: str = "sim"
    peldaño_armado: bool = False
    peldaño_lado: str = ""
    # True tras sentarse una vez en el escudo ya puesto (no re-sienta cada latido).
    histeresis_sentada: bool = False
    historial: list[dict[str, Any]] = field(default_factory=list)
    # Límite vivo (sin fill): Igris puede moverlo acercándolo al mid
    limite_pendiente: LimiteEscudoPendiente | None = None
    # Cirugía anti-tumor: veda + último vivo bueno
    ts_ultima_planta: float = 0.0
    veda_hasta_ts: float = 0.0
    lado_ultima_planta: str = ""
    vivo_ultimo_ok: float | None = None

    def a_estado(self) -> EstadoEscudoBtc:
        return EstadoEscudoBtc(
            acumulado_ancla=self.acumulado_ancla,
            meta_lado=self.meta_lado,
            meta_usd=self.meta_usd,
            peldaño_armado=bool(self.peldaño_armado),
            peldaño_lado=str(self.peldaño_lado or ""),
        )

    def sincronizar_desde_estado(self, st: EstadoEscudoBtc) -> None:
        self.acumulado_ancla = st.acumulado_ancla
        self.meta_lado = st.meta_lado
        self.meta_usd = st.meta_usd
        self.peldaño_armado = bool(getattr(st, "peldaño_armado", False))
        self.peldaño_lado = str(getattr(st, "peldaño_lado", "") or "")


def _path_libro(path: Path | None = None) -> Path:
    if path is not None:
        return path
    from core import beru_rango_paths as paths

    return paths.escudo_btc_sim()


def cargar_libro_sim(path: Path | None = None) -> LibroEscudoSim:
    p = _path_libro(path)
    if not p.exists():
        return LibroEscudoSim(modo="sim")
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return LibroEscudoSim(modo="sim")
    ancla = data.get("acumulado_ancla")
    lim_raw = data.get("limite_pendiente")
    lim: LimiteEscudoPendiente | None = None
    if isinstance(lim_raw, dict) and lim_raw:
        lim = LimiteEscudoPendiente(
            lado=str(lim_raw.get("lado") or ""),
            qty=float(lim_raw.get("qty") or 0),
            px=float(lim_raw.get("px") or 0),
            px_origen=float(lim_raw.get("px_origen") or lim_raw.get("px") or 0),
            ts_planta=float(lim_raw.get("ts_planta") or 0),
            ts_ultimo_mov=float(lim_raw.get("ts_ultimo_mov") or 0),
            n_moves=int(lim_raw.get("n_moves") or 0),
            meta_usd=float(lim_raw.get("meta_usd") or 0),
            filled=bool(lim_raw.get("filled") or False),
            cancelado=bool(lim_raw.get("cancelado") or False),
        )
        setattr(lim, "order_id", str(lim_raw.get("order_id") or ""))
        setattr(lim, "cl_ord_id", str(lim_raw.get("cl_ord_id") or ""))
        if not lim.vivo():
            lim = None
    return LibroEscudoSim(
        acumulado_ancla=None if ancla is None else float(ancla),
        meta_lado=str(data.get("meta_lado") or ""),
        meta_usd=float(data.get("meta_usd") or 0),
        escudo_signed_usd=float(data.get("escudo_signed_usd") or 0),
        n_ajustes=int(data.get("n_ajustes") or 0),
        ts=float(data.get("ts") or 0),
        modo=str(data.get("modo") or "sim"),
        peldaño_armado=bool(data.get("peldaño_armado") or False),
        peldaño_lado=str(data.get("peldaño_lado") or ""),
        histeresis_sentada=bool(data.get("histeresis_sentada") or False),
        historial=list(data.get("historial") or [])[-40:],
        limite_pendiente=lim,
        ts_ultima_planta=float(data.get("ts_ultima_planta") or 0),
        veda_hasta_ts=float(data.get("veda_hasta_ts") or 0),
        lado_ultima_planta=str(data.get("lado_ultima_planta") or ""),
        vivo_ultimo_ok=(
            None
            if data.get("vivo_ultimo_ok") is None
            else float(data.get("vivo_ultimo_ok"))
        ),
    )


def resetear_libro_escudo(
    path: Path | None = None,
    *,
    motivo: str = "despertar_desde_cero",
) -> LibroEscudoSim:
    """Borra memoria del escudo (ancla, peldaños, papel BTC).

    Para despertar el ejército desde 0: Igris no hereda manto de una vida anterior.
    Beru no se toca aquí — solo el libro de papel del escudo.
    """
    libro = LibroEscudoSim(modo="sim", ts=time.time())
    p = guardar_libro_sim(libro, path)
    try:
        _append_evento_sim(
            {
                "ts": time.time(),
                "evento": "reset_libro",
                "motivo": str(motivo or "despertar_desde_cero"),
                "path": str(p),
            }
        )
    except Exception:
        pass
    return libro


def guardar_libro_sim(libro: LibroEscudoSim, path: Path | None = None) -> Path:
    p = _path_libro(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    lim = libro.limite_pendiente
    lim_payload = None
    if lim is not None and lim.vivo():
        lim_payload = {
            "lado": lim.lado,
            "qty": float(lim.qty),
            "px": float(lim.px),
            "px_origen": float(lim.px_origen),
            "ts_planta": float(lim.ts_planta),
            "ts_ultimo_mov": float(lim.ts_ultimo_mov),
            "n_moves": int(lim.n_moves),
            "meta_usd": float(lim.meta_usd),
            "filled": bool(lim.filled),
            "cancelado": bool(lim.cancelado),
            "ordType": escudo_ord_tipo(),
            "order_id": str(getattr(lim, "order_id", "") or ""),
            "cl_ord_id": str(getattr(lim, "cl_ord_id", "") or ""),
        }
    payload = {
        "acumulado_ancla": libro.acumulado_ancla,
        "meta_lado": libro.meta_lado,
        "meta_usd": libro.meta_usd,
        "escudo_signed_usd": round(float(libro.escudo_signed_usd), 4),
        "n_ajustes": int(libro.n_ajustes),
        "ts": float(libro.ts or time.time()),
        "modo": libro.modo or "sim",
        "peldaño_armado": bool(libro.peldaño_armado),
        "peldaño_lado": str(libro.peldaño_lado or ""),
        "histeresis_sentada": bool(libro.histeresis_sentada),
        "historial": list(libro.historial or [])[-40:],
        "limite_pendiente": lim_payload,
        "ts_ultima_planta": float(libro.ts_ultima_planta or 0),
        "veda_hasta_ts": float(libro.veda_hasta_ts or 0),
        "lado_ultima_planta": str(libro.lado_ultima_planta or ""),
        "vivo_ultimo_ok": (
            None
            if libro.vivo_ultimo_ok is None
            else round(float(libro.vivo_ultimo_ok), 4)
        ),
    }
    p.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return p


def tick_limite_pendiente(
    libro: LibroEscudoSim,
    mid: float,
    *,
    ahora: float | None = None,
    persistir: bool = True,
) -> dict[str, Any]:
    """Latido del límite vivo: si no llenó, decide si acercarlo (sigue limit).

    No toca Beru. No convierte a market. Listo para cable live (amend precio).
    """
    ahora = float(ahora if ahora is not None else time.time())
    pend = libro.limite_pendiente
    decision = decidir_mover_limite(pend, mid, ahora=ahora)
    out: dict[str, Any] = {
        "ok": True,
        "ordType": escudo_ord_tipo(),
        "decision": decision,
        "movido": False,
    }
    if pend is None or not pend.vivo():
        out["aviso"] = "sin_limite_pendiente"
        return out
    out["px"] = pend.px
    out["lado"] = pend.lado
    out["n_moves"] = pend.n_moves
    if decision.get("mover"):
        aplicar_mover_limite(pend, decision, ahora=ahora)
        libro.limite_pendiente = pend
        out["movido"] = True
        out["px"] = pend.px
        out["n_moves"] = pend.n_moves
        out["frase"] = decision.get("frase") or "movió limit"
        if persistir:
            guardar_libro_sim(libro)
            _append_evento_sim(
                {
                    "ts": ahora,
                    "evento": "mover_limite",
                    "lado": pend.lado,
                    "px_antes": decision.get("px_antes"),
                    "px_nuevo": decision.get("px_nuevo"),
                    "mid": mid,
                    "n_moves": pend.n_moves,
                    "ordType": escudo_ord_tipo(),
                }
            )
    else:
        out["frase"] = f"limit quieto [{decision.get('motivo')}]"
    return out


def _append_evento_sim(ev: dict[str, Any], path: Path | None = None) -> None:
    try:
        from core import beru_rango_paths as paths

        p = path or paths.escudo_btc_sim_eventos()
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("a", encoding="utf-8") as f:
            f.write(json.dumps(ev, ensure_ascii=False) + "\n")
    except Exception:
        pass


def aplicar_bocado_papel(
    libro: LibroEscudoSim,
    bocado_usd: float,
    *,
    meta: MetaEscudoBtc | None = None,
    notional_real_signed: float | None = None,
) -> dict[str, Any]:
    """Aplica el bocado al libro de papel (sin exchange).

    Si ``notional_real_signed`` viene (tras redondeo de frente), el papel
    queda en ese nocional — no en el ideal doctrinal (la deuda queda fuera).
    """
    antes = float(libro.escudo_signed_usd)
    boc = float(bocado_usd or 0)
    if notional_real_signed is not None:
        despues = float(notional_real_signed)
    elif meta is not None:
        despues = float(meta.signed_usd)
    else:
        despues = antes + boc
    libro.escudo_signed_usd = despues
    if meta is not None:
        libro.meta_lado = meta.lado
        libro.meta_usd = float(meta.usd)
    libro.n_ajustes = int(libro.n_ajustes) + 1
    libro.ts = time.time()
    libro.modo = "sim"
    return {
        "ok": True,
        "modo": "sim",
        "bocado_pedido_usd": boc,
        "escudo_antes": antes,
        "escudo_despues": despues,
        "frase": f"papel {antes:.0f} → {despues:.0f} (bocado {boc:+.0f})",
    }


def manos_escudo_btc(
    libro: LibroEscudoSim,
    meta: MetaEscudoBtc,
    *,
    forzar_modo: str | None = None,
    precio: float | None = None,
    familia: str | None = None,
    redondear: bool = True,
    casa: Any | None = None,
) -> dict[str, Any]:
    """Manos del escudo: en sim ajusta papel; en live se niega hasta candado + cable futuro.

    En sim ajusta papel. En live: market por defecto (Monarca 2026-09-24);
    limit solo si se fuerza por env. Ver ``escudo_ord_tipo()``.
    Con ``precio`` + ``redondear``: aplica nocional real del frente (lineal|inverso).
    Si ``casa`` (CasaEscudoSim): cobra peaje Igris sobre el nocional movido.
    """
    modo = (forzar_modo or escudo_modo()).strip().lower()
    tipo_ord = escudo_ord_tipo()
    if modo != "live":
        boc = bocado_ajuste_usd(meta, libro.escudo_signed_usd)
        real_signed: float | None = None
        orden: dict[str, Any] = {}
        if redondear and precio is not None:
            # Redondea la META absoluta (no el delta) → papel = nocional real del frente
            if abs(meta.signed_usd) < 1e-12:
                real_signed = 0.0
                orden = {
                    "ok": True,
                    "qty": 0.0,
                    "notional_usd": 0.0,
                    "deuda_usd": 0.0,
                    "lado": "",
                    "familia": familia or escudo_familia(),
                    "ordType": tipo_ord,
                    "motivo": "meta_cero",
                }
            else:
                r = masa_a_qty_escudo(
                    abs(meta.usd), float(precio), familia=familia, modo="floor"
                )
                orden = {
                    **r,
                    "lado": meta.lado if r.get("ok") else "",
                    "bocado_pedido_usd": boc,
                    "ordType": tipo_ord,
                }
                if r.get("ok"):
                    signo = 1.0 if meta.lado == "LONG" else -1.0
                    real_signed = signo * float(r.get("notional_usd") or 0)
                    orden["signed_notional"] = real_signed
                elif r.get("motivo") == "qty_cero_deuda":
                    return {
                        "ok": False,
                        "modo": "sim",
                        "bloqueado": False,
                        "aviso": "redondeo_qty_cero",
                        "deuda_usd": r.get("deuda_usd"),
                        "paso_usd": r.get("paso_usd"),
                        "familia": r.get("familia"),
                        "frase": (
                            f"meta ${meta.usd:.0f} no alcanza 1 paso "
                            f"(paso≈{float(r.get('paso_usd') or 0):.0f}$) — espera"
                        ),
                        "orden": r,
                    }
        antes = float(libro.escudo_signed_usd)
        out = aplicar_bocado_papel(
            libro, boc, meta=meta, notional_real_signed=real_signed
        )
        if orden:
            out["orden"] = orden
            out["familia"] = orden.get("familia")
            out["deuda_redondeo_usd"] = orden.get("deuda_usd")
            out["paso_usd"] = orden.get("paso_usd")
            if real_signed is not None and orden.get("qty") is not None:
                out["frase"] = (
                    f"papel {out['escudo_antes']:.0f} → {out['escudo_despues']:.0f} "
                    f"({orden.get('familia')} qty={orden.get('qty')} "
                    f"deuda={float(orden.get('deuda_usd') or 0):.2f})"
                )
        # Peaje + libro de operaciones Igris (PnL al comprar caro / vender barato)
        if casa is not None and out.get("ok"):
            despues = float(libro.escudo_signed_usd)
            movido = abs(despues - antes)
            if movido > 1e-9:
                try:
                    if precio is not None and float(precio) > 0:
                        # Sync casa.escudo al "antes" del papel, luego asiento completo
                        casa.escudo_signed_usd = antes
                        asiento = casa.aplicar_ajuste_escudo(
                            despues, float(precio), nota="ajuste_escudo"
                        )
                        out["peaje_igris_usd"] = asiento.get("peaje")
                        out["pnl_igris_op"] = asiento.get("pnl_realizado")
                        out["op_igris"] = asiento
                    else:
                        peaje = casa.cobrar_peaje_igris(
                            movido, lados=1, nota="ajuste_escudo_sin_px"
                        )
                        casa.escudo_signed_usd = despues
                        out["peaje_igris_usd"] = peaje
                    out["casa"] = casa.resumen()
                except Exception as exc:
                    out["peaje_aviso"] = str(exc)
        return out

    if not escudo_live_permitido():
        return {
            "ok": False,
            "modo": "live",
            "bloqueado": True,
            "aviso": "live_bloqueado_falta_IGRIS_ESCUDO_BTC_LIVE_OK",
            "ordType": tipo_ord,
            "frase": "live cerrado — solo sim hasta orden del Monarca",
        }

    # Cable live OKX: market (o limit si se fuerza).
    try:
        from core import igris_escudo_manos_okx as manos_okx
    except Exception as exc:
        return {
            "ok": False,
            "modo": "live",
            "bloqueado": False,
            "aviso": f"manos_okx_import:{exc}",
            "ordType": tipo_ord,
            "frase": "no pude cargar manos OKX del escudo",
        }

    out_live = manos_okx.aplicar_meta_live_okx(libro, meta, precio=precio)
    out_live["ordType"] = tipo_ord
    return out_live


def sentar_histeresis_en_vivo(
    libro: LibroEscudoSim,
    vivo_signed: float,
    *,
    long_usd: float,
    short_usd: float,
) -> None:
    """Primera vida con histéresis: el asiento es el escudo ya abierto.

    Así el reinicio no compra ni vende solo por despertar. A partir de ahí,
    solo se mueve al peldaño vecino del desbalance real.
    """
    import math

    p = escudo_peldaño_usd()
    r = float(escudo_relacion() or 0)
    if r <= 1e-12:
        r = 1.5
    neto = acumulado_beru_neto(long_usd, short_usd)
    vivo = float(vivo_signed or 0)
    bruto = abs(vivo) / r
    libro.histeresis_sentada = True
    if bruto + 1e-9 < (p * 0.5):
        libro.acumulado_ancla = 0.0
        libro.peldaño_armado = False
        libro.peldaño_lado = ""
        libro.meta_lado = ""
        libro.meta_usd = 0.0
        return
    # Nunca se adelanta: el asiento es el piso del escudo ya puesto.
    asiento = math.floor(bruto / p + 1e-15) * p
    if asiento < 1e-12:
        libro.acumulado_ancla = 0.0
        libro.peldaño_armado = False
        libro.peldaño_lado = ""
        libro.meta_lado = ""
        libro.meta_usd = 0.0
        return
    # Signo del asiento = signo del neto Beru si ya hay lado; si no, el del escudo.
    if abs(neto) > 1e-9:
        signo = 1.0 if neto > 0 else -1.0
        lado = "SHORT" if neto > 0 else "LONG"
    else:
        signo = 1.0 if vivo > 0 else -1.0
        lado = "SHORT" if vivo > 0 else "LONG"
    libro.acumulado_ancla = float(signo * asiento)
    libro.peldaño_armado = True
    libro.peldaño_lado = lado
    libro.meta_usd = float(asiento * r)
    libro.meta_lado = "LONG" if signo > 0 else "SHORT"


def latido_escudo(
    *,
    long_usd: float | None = None,
    short_usd: float | None = None,
    snap: dict[str, Any] | None = None,
    libro: LibroEscudoSim | None = None,
    path_libro: Path | None = None,
    persistir: bool = True,
    aplicar_manos: bool = True,
    forzar_modo: str | None = None,
    ojos_live: bool = False,
    precio_btc: float | None = None,
    familia: str | None = None,
    casa: Any | None = None,
) -> dict[str, Any]:
    """Un latido completo listo para teatro: ojos → gatillo → manos sim.

    - Si vienen ``long_usd``/``short_usd`` o ``snap``: no toca OKX.
    - ``ojos_live=True`` sin snap: mira balanza real (solo lectura).
    - ``precio_btc``: activa redondeo del frente (lineal|inverso).
    - ``casa``: libro Tusk ($100 + peajes); cobra peaje Igris al ajustar.
    - Manos default = papel. Live bloqueado.
    """
    libro = libro if libro is not None else cargar_libro_sim(path_libro)
    modo = (forzar_modo or escudo_modo()).strip().lower()
    if modo != "live":
        modo = "sim"

    if snap is not None:
        vision = vision_desde_snap(snap)
        lo, sh = vision.long_usd, vision.short_usd
        ojos_meta = {
            "ojos_ok": vision.ok,
            "ojos_fuente": vision.fuente,
            "ojos_frase": vision.frase,
            "ojos_aviso": vision.aviso,
        }
    elif long_usd is not None and short_usd is not None:
        lo, sh = float(long_usd), float(short_usd)
        ojos_meta = {
            "ojos_ok": True,
            "ojos_fuente": "args",
            "ojos_frase": f"L ${lo:.0f} · S ${sh:.0f}",
            "ojos_aviso": "",
        }
    else:
        vision = mirar_manto_beru(live=ojos_live)
        lo, sh = vision.long_usd, vision.short_usd
        ojos_meta = {
            "ojos_ok": vision.ok,
            "ojos_fuente": vision.fuente,
            "ojos_frase": vision.frase,
            "ojos_aviso": vision.aviso,
        }

    st = libro.a_estado()
    # En sim el "vivo" es el libro de papel; en live se mira OKX BTC.
    ciego_btc = False
    aviso_ojo = ""
    if modo == "sim":
        vivo = float(libro.escudo_signed_usd)
    else:
        det = mirar_escudo_btc_detalle_okx()
        if det.get("ciego"):
            ciego_btc = True
            aviso_ojo = str(det.get("aviso") or "ojo_ciego")
            # Nunca tratar fallo de API como posición 0 (tumor de doble asalto).
            if libro.vivo_ultimo_ok is not None:
                vivo = float(libro.vivo_ultimo_ok)
            else:
                vivo = float(libro.escudo_signed_usd)
        else:
            vivo = float(det.get("signed") or 0.0)
            libro.vivo_ultimo_ok = vivo
    if (
        modo == "live"
        and not ciego_btc
        and not bool(getattr(libro, "histeresis_sentada", False))
    ):
        sentar_histeresis_en_vivo(libro, vivo, long_usd=lo, short_usd=sh)
        st = libro.a_estado()
    ancla_antes = st.acumulado_ancla
    lado_antes = st.meta_lado
    usd_antes = st.meta_usd
    decision = st.tick(lo, sh, escudo_vivo_signed_usd=vivo)

    # Precio BTC si hace falta (redondeo / límite live)
    px_btc = precio_btc
    if px_btc is None and (modo == "live" or aplicar_manos):
        try:
            from core import igris_escudo_manos_okx as manos_okx

            px_btc = manos_okx.mid_btc_escudo() or None
        except Exception:
            px_btc = None

    manos: dict[str, Any] = {"ok": False, "modo": modo, "aplicado": False}
    # Ciego + solo "desviacion": no plantar (el ojo mintió o la casa no respondió).
    if (
        aplicar_manos
        and decision.get("debe_rebalancear")
        and ciego_btc
        and str(decision.get("motivo") or "") == "desviacion"
    ):
        st.acumulado_ancla = ancla_antes
        st.meta_lado = lado_antes
        st.meta_usd = usd_antes
        libro.sincronizar_desde_estado(st)
        decision["ancla_sellada"] = False
        decision["escudo_vivo_signed_usd"] = vivo
        manos = {
            "ok": False,
            "modo": modo,
            "aplicado": False,
            "aviso": "ojo_ciego",
            "ciego": True,
            "vivo": vivo,
            "frase": f"ojo ciego ({aviso_ojo}) — no planta por desviacion",
        }
    elif aplicar_manos and decision.get("debe_rebalancear"):
        meta = meta_escudo_btc(float(decision["acumulado_beru"]))
        manos = manos_escudo_btc(
            libro,
            meta,
            forzar_modo=modo,
            precio=px_btc,
            familia=familia,
            redondear=px_btc is not None,
            casa=casa,
        )
        # Cirugía: aplicado solo si hubo orden real (no basta ok/ya_en_meta).
        aplicado_real = bool(manos.get("aplicado"))
        manos["aplicado"] = aplicado_real
        aviso_m = str(manos.get("aviso") or "")
        if aplicado_real or aviso_m in ("ya_en_meta", "veda_post_planta"):
            libro.sincronizar_desde_estado(st)
            decision["bocado_usd"] = 0.0
            decision["escudo_vivo_signed_usd"] = (
                float(libro.escudo_signed_usd)
                if modo == "sim"
                else float(
                    manos.get("vivo")
                    if manos.get("vivo") is not None
                    else libro.escudo_signed_usd
                )
            )
            if casa is not None and aplicado_real:
                neto = acumulado_beru_neto(lo, sh)
                lado_b = "SHORT" if neto > 0 else ("LONG" if neto < 0 else "")
                casa.sincronizar_posiciones(
                    beru_lado=lado_b,
                    beru_nocional_usd=abs(neto),
                    escudo_signed_usd=libro.escudo_signed_usd,
                )
        else:
            # No sellar ancla si las manos no movieron (live cerrado, veda, ciego…).
            st.acumulado_ancla = ancla_antes
            st.meta_lado = lado_antes
            st.meta_usd = usd_antes
            libro.sincronizar_desde_estado(st)
            decision["ancla_sellada"] = False
            decision["escudo_vivo_signed_usd"] = vivo
    elif decision.get("debe_rebalancear") and not aplicar_manos:
        # Solo mirar: no sellar ancla
        st.acumulado_ancla = ancla_antes
        st.meta_lado = lado_antes
        st.meta_usd = usd_antes
        libro.sincronizar_desde_estado(st)
        decision["ancla_sellada"] = False
        decision["escudo_vivo_signed_usd"] = vivo
    else:
        libro.sincronizar_desde_estado(st)
        decision["escudo_vivo_signed_usd"] = vivo

    # Límite pendiente: acercar px si no llenó (live = amend OKX; sim = memoria)
    mover_info: dict[str, Any] = {"movido": False}
    if aplicar_manos and libro.limite_pendiente is not None:
        try:
            if modo == "live":
                from core import igris_escudo_manos_okx as manos_okx

                mover_info = manos_okx.mover_limite_live_okx(libro, mid=px_btc)
            else:
                mover_info = tick_limite_pendiente(
                    libro, float(px_btc or 0) or 0.0, persistir=False
                )
        except Exception as exc_m:
            mover_info = {"movido": False, "aviso": str(exc_m)}

    out: dict[str, Any] = {
        **decision,
        **ojos_meta,
        "long_usd": lo,
        "short_usd": sh,
        "modo": modo,
        "manos": manos,
        "escudo_papel_usd": libro.escudo_signed_usd,
        "n_ajustes": libro.n_ajustes,
        "familia_escudo": familia or escudo_familia(),
        "frente_escudo": frente_escudo_btc(familia),
        "mover_limite": mover_info,
        "ordType": escudo_ord_tipo(),
        "ojo_ciego": bool(ciego_btc),
        "ojo_aviso": aviso_ojo,
    }
    if casa is not None:
        out["casa"] = casa.resumen()
        out["tusk_frase"] = casa.frase_tusk()


    if decision.get("debe_rebalancear") or manos.get("aplicado"):
        libro.historial.append(
            {
                "ts": time.time(),
                "acumulado": decision.get("acumulado_beru"),
                "motivo": decision.get("motivo"),
                "meta_lado": decision.get("meta_lado"),
                "meta_usd": decision.get("meta_usd"),
                "escudo": libro.escudo_signed_usd,
                "manos_ok": bool(manos.get("ok")),
            }
        )
        libro.historial = libro.historial[-40:]

    if persistir:
        libro.ts = time.time()
        guardar_libro_sim(libro, path_libro)
        _append_evento_sim({k: v for k, v in out.items() if k != "manos"} | {"manos": manos})

    return out


def frase_latido(out: dict[str, Any]) -> str:
    """Resumen corto para el Monarca / teatro."""
    acc = float(out.get("acumulado_beru") or 0)
    crudo = float(out.get("acumulado_crudo") or 0)
    lado = str(out.get("meta_lado") or "—") or "—"
    meta = float(out.get("meta_usd") or 0)
    papel = float(out.get("escudo_papel_usd") or 0)
    debe = bool(out.get("debe_rebalancear"))
    motivo = str(out.get("motivo") or "")
    manos = out.get("manos") or {}
    if debe and manos.get("aplicado") and str(out.get("modo") or "") == "live":
        tipo = str(manos.get("ordType") or out.get("ordType") or escudo_ord_tipo() or "market")
        verbo = "plantó market OKX" if tipo == "market" else "plantó limit OKX"
    elif debe and manos.get("aplicado"):
        verbo = "ajustó papel"
    elif debe and manos.get("bloqueado"):
        verbo = "quería ajustar (live cerrado)"
    elif debe:
        verbo = "debería ajustar"
    else:
        verbo = "en banda"
    return (
        f"Beru neto {acc:+.0f} (crudo {crudo:+.0f}) · escudo {lado} ${meta:.0f} · papel {papel:+.0f} · "
        f"{verbo}" + (f" [{motivo}]" if motivo else "")
    )


# --- Redondeos del escudo (solo Igris) — lineal | inverso --------------------
#
# Dos familias posibles (Monarca 2026-09-23):
#   · inverso = coin-margined (face USD / settle BTC) → BTCUSD_INVERSE  ← sellado
#   · lineal  = cotiza y liquida en la misma moneda (USDT) → BTCUSDT_LINEAL
# Beru no se toca. Esto no es el manto dual L+S.


def escudo_familia() -> str:
    """``lineal`` o ``inverso``. Default **inverso** (sellado Monarca 2026-09-23)."""
    raw = str(
        os.getenv("IGRIS_ESCUDO_BTC_FRENTE")
        or getattr(config, "IGRIS_ESCUDO_BTC_FRENTE", "inverso")
        or "inverso"
    ).strip().lower()
    if raw in ("lineal", "linear", "usdt", "btc-usdt"):
        return "lineal"
    if raw in ("inverso", "inverse", "coin", "usd_inverse", "btc-usd"):
        return "inverso"
    return "inverso"


def frente_escudo_btc(familia: str | None = None) -> str:
    fam = (familia or escudo_familia()).strip().lower()
    if fam == "inverso":
        return "BTCUSD_INVERSE"
    return "BTCUSDT_LINEAL"


def inst_escudo_btc(familia: str | None = None) -> str:
    fam = (familia or escudo_familia()).strip().lower()
    if fam == "inverso":
        return "BTC-USD-SWAP"
    return "BTC-USDT-SWAP"


def _filtros_escudo_lineal() -> dict[str, Any]:
    """USDT linear: notional = sz × ctVal × px (misma moneda)."""
    # Preferir catálogo sano de BTC; okx_minimos_orden a veces trae defaults basura (ctVal=1).
    sano: dict[str, Any] | None = None
    try:
        from core import lote_okx

        f = dict(lote_okx.filtros_lote("BTCUSDT_LINEAL"))
        ct = float(f.get("ctVal") or 0)
        lot = float(f.get("lotSz") or 0)
        # BTC lineal OKX real: ctVal=0.01, lotSz=0.01 → paso ~$10 @ 100k
        # Si ctVal≥1 y lot≥1 el catálogo está podrido para escudo.
        if 0 < ct < 1.0 and 0 < lot <= 1.0:
            sano = f
    except Exception:
        pass
    if sano is None:
        # Leer directo parametros_mercado si existe
        try:
            root = Path(__file__).resolve().parents[1]
            p = root / "data" / "okx_parametros_mercado.json"
            if p.exists():
                data = json.loads(p.read_text(encoding="utf-8"))
                row = (data.get("activos") or {}).get("BTC") or {}
                if row and float(row.get("ctVal") or 0) > 0:
                    sano = {
                        "instId": row.get("instId") or "BTC-USDT-SWAP",
                        "minSz": float(row.get("minSz") or 0.01),
                        "lotSz": float(row.get("lotSz") or 0.01),
                        "ctVal": float(row.get("ctVal") or 0.01),
                        "tickSz": float(row.get("tickSz") or 0.1),
                        "min_usd_est": float(row.get("min_usd_est") or 8.0),
                        "fuente": "okx_parametros_mercado",
                    }
        except Exception:
            pass
    if sano is None:
        sano = {
            "instId": "BTC-USDT-SWAP",
            "minSz": 0.01,
            "lotSz": 0.01,
            "ctVal": 0.01,
            "tickSz": 0.1,
            "min_usd_est": 8.0,
            "fuente": "default_okx_btc",
        }
    sano["familia"] = "lineal"
    sano["unidad"] = "contratos_ctval_px"
    sano["frente"] = "BTCUSDT_LINEAL"
    sano["instId"] = sano.get("instId") or "BTC-USDT-SWAP"
    return sano


def _filtros_escudo_inverso() -> dict[str, Any]:
    """Inverso BTC — face USD por contrato.

    OKX vivo verificado 2026-09-23 ``BTC-USD-SWAP``:
      ctVal=100 USD · lotSz=0.1 · minSz=0.1 → **paso = $10** (no $100).
    Override: ``IGRIS_ESCUDO_BTC_INV_CTVAL`` / ``_LOTSZ`` / ``_MINSZ``.
    """
    ct = float(os.getenv("IGRIS_ESCUDO_BTC_INV_CTVAL", "100") or 100)
    # Default OKX real: 0.1 contrato × 100 USD = $10 (antes el default lot=1 mentía $100)
    lot = float(os.getenv("IGRIS_ESCUDO_BTC_INV_LOTSZ", "0.1") or 0.1)
    mn = float(os.getenv("IGRIS_ESCUDO_BTC_INV_MINSZ", "0.1") or 0.1)

    mar = str(os.getenv("BERU_MAR") or getattr(config, "BERU_MAR", "okx") or "okx").strip().lower()

    # Casa Beru = OKX → no mezclar catálogo Bybit (otro mar)
    if mar != "bybit":
        return {
            "familia": "inverso",
            "unidad": "contratos_face_usd",
            "frente": "BTCUSD_INVERSE",
            "instId": "BTC-USD-SWAP",
            "minSz": mn,
            "lotSz": lot,
            "ctVal": ct,
            "tickSz": 0.1,
            "min_usd_est": ct * mn,
            "fuente": "okx_btc_usd_swap_vivo",
            "casa": "okx",
        }

    # Bybit: qty ≈ face USD (paso típico $1)
    try:
        from core import lote_bybit as lb

        fb = lb.filtros_lote("BTCUSD_INVERSE")
        if fb and float(fb.get("qtyStep") or fb.get("minOrderQty") or 0) > 0:
            return {
                "familia": "inverso",
                "unidad": "usd_contrato",
                "frente": "BTCUSD_INVERSE",
                "instId": "BTCUSD",
                "minSz": float(fb.get("minOrderQty") or 1),
                "lotSz": float(fb.get("qtyStep") or 1),
                "ctVal": 1.0,
                "tickSz": float(fb.get("tickSize") or 0.5),
                "min_usd_est": float(fb.get("minOrderQty") or 1),
                "fuente": "lote_bybit",
                "casa": "bybit",
            }
    except Exception:
        pass
    return {
        "familia": "inverso",
        "unidad": "contratos_face_usd",
        "frente": "BTCUSD_INVERSE",
        "instId": "BTC-USD-SWAP",
        "minSz": mn,
        "lotSz": lot,
        "ctVal": ct,
        "tickSz": 0.1,
        "min_usd_est": ct * mn,
        "fuente": "okx_inv_fallback",
        "casa": "okx",
    }


def filtros_escudo_btc(familia: str | None = None) -> dict[str, Any]:
    fam = (familia or escudo_familia()).strip().lower()
    if fam == "inverso":
        return _filtros_escudo_inverso()
    return _filtros_escudo_lineal()


def _redondear_paso_escudo(val: float, paso: float, modo: str = "floor") -> float:
    import math

    if paso <= 0:
        return float(val or 0)
    v = float(val or 0)
    if v <= 0:
        return 0.0
    n = v / paso
    if modo == "ceil":
        n = math.ceil(n - 1e-12)
    else:
        n = math.floor(n + 1e-12)
    if n <= 0:
        return 0.0
    return n * paso


def paso_usd_escudo(precio: float, familia: str | None = None) -> float:
    """Cuánto USD mueve un paso mínimo del frente escudo (granularidad)."""
    f = filtros_escudo_btc(familia)
    lot = float(f.get("lotSz") or 1.0)
    ct = float(f.get("ctVal") or 1.0)
    px = float(precio or 0)
    unidad = str(f.get("unidad") or "")
    if unidad == "usd_contrato":
        return lot  # Bybit inverse: 1 paso = lot USD
    if unidad == "contratos_face_usd":
        return lot * ct  # OKX inverse: lot × face USD
    # lineal: lot × ctVal × px
    if px <= 0:
        return 0.0
    return lot * ct * px


def masa_a_qty_escudo(
    masa_usd: float,
    precio: float,
    *,
    familia: str | None = None,
    modo: str = "floor",
    ticket_min_si_cero: bool = False,
) -> dict[str, Any]:
    """Meta/bocado USD → qty del frente escudo + deuda de redondeo.

    Regla Igris escudo (anti-tumor):
      · floor por defecto: no inventar contrato si no alcanza el paso.
      · deuda = objetivo − notional_real (cola en cabeza, no en el mar).
      · ``ticket_min_si_cero`` solo si el Monarca fuerza un primer contrato.
    """
    f = filtros_escudo_btc(familia)
    fam = str(f.get("familia") or escudo_familia())
    lot = float(f.get("lotSz") or 1.0)
    min_sz = float(f.get("minSz") or lot)
    ct = float(f.get("ctVal") or 1.0)
    px = float(precio or 0)
    objetivo = abs(float(masa_usd or 0))
    unidad = str(f.get("unidad") or "")
    paso_usd = round(paso_usd_escudo(px, fam), 6)

    if objetivo <= 0 or (unidad == "contratos_ctval_px" and px <= 0):
        return {
            "ok": False,
            "motivo": "masa_o_precio_cero",
            "qty": 0.0,
            "notional_usd": 0.0,
            "deuda_usd": round(objetivo, 6),
            "paso_usd": paso_usd,
            "familia": fam,
            "frente": f.get("frente"),
            "unidad": unidad,
        }

    # Bruto según unidad
    if unidad == "usd_contrato":
        bruto = objetivo  # Bybit inverse
        notional_fn = lambda q: float(q)
    elif unidad == "contratos_face_usd":
        bruto = objetivo / ct if ct > 0 else 0.0  # OKX inverse
        notional_fn = lambda q: float(q) * ct
    else:
        # lineal USDT
        bruto = objetivo / (ct * px) if (ct > 0 and px > 0) else 0.0
        notional_fn = lambda q: float(q) * ct * px

    qty = _redondear_paso_escudo(bruto, lot, modo if modo in ("floor", "ceil") else "floor")
    if qty + 1e-12 < min_sz:
        qty = 0.0
    notional = notional_fn(qty) if qty > 0 else 0.0
    deuda = max(0.0, objetivo - notional)

    if qty <= 0:
        if ticket_min_si_cero and objetivo > 0:
            qty = _redondear_paso_escudo(min_sz, lot, "ceil")
            notional = notional_fn(qty) if qty > 0 else 0.0
            deuda = max(0.0, objetivo - notional)
            if qty > 0:
                return {
                    "ok": True,
                    "qty": qty,
                    "notional_usd": round(notional, 6),
                    "deuda_usd": round(deuda, 6),
                    "paso_usd": paso_usd,
                    "familia": fam,
                    "frente": f.get("frente"),
                    "instId": f.get("instId"),
                    "unidad": unidad,
                    "ticket_min": True,
                }
        return {
            "ok": False,
            "motivo": "qty_cero_deuda",
            "qty": 0.0,
            "notional_usd": 0.0,
            "deuda_usd": round(objetivo, 6),
            "paso_usd": paso_usd,
            "familia": fam,
            "frente": f.get("frente"),
            "instId": f.get("instId"),
            "unidad": unidad,
        }

    return {
        "ok": True,
        "qty": qty,
        "notional_usd": round(notional, 6),
        "deuda_usd": round(deuda, 6),
        "paso_usd": paso_usd,
        "familia": fam,
        "frente": f.get("frente"),
        "instId": f.get("instId"),
        "unidad": unidad,
    }


def bocado_a_orden_escudo(
    bocado_signed_usd: float,
    precio: float,
    *,
    familia: str | None = None,
    modo: str = "floor",
) -> dict[str, Any]:
    """Traduce bocado firmado (+ long / − short) a lado + qty redondeada.

    Solo Igris escudo. No envía orden.
    """
    boc = float(bocado_signed_usd or 0)
    if abs(boc) < 1e-12:
        return {
            "ok": False,
            "motivo": "bocado_cero",
            "lado": "",
            "qty": 0.0,
            "notional_usd": 0.0,
            "deuda_usd": 0.0,
            "familia": familia or escudo_familia(),
        }
    lado = "LONG" if boc > 0 else "SHORT"
    r = masa_a_qty_escudo(abs(boc), precio, familia=familia, modo=modo)
    return {
        **r,
        "lado": lado if r.get("ok") else "",
        "bocado_pedido_usd": boc,
        "ordType": escudo_ord_tipo(),
        "signed_notional": (
            float(r.get("notional_usd") or 0) * (1.0 if boc > 0 else -1.0)
            if r.get("ok")
            else 0.0
        ),
    }
