"""Altar del cazador continuo — simulación fiel (manos OFF).

Un solo oficio y una sola arma para los cuatro grados: CAZA CONDICIONAL.
Al tocar Red se cancela la carta vieja y se planta otra en la nueva Hoz; la
masa suma el engorde del grado. Mariscal hace su trailing con Beru moviendo
esa misma Hoz, no con un arma distinta de la casa.

Sin manos reales: solo memoria + bitácora de eventos. Place/cancel en exchange
sigue dormido (BERU_MANOS).
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from core import beru_cazador
from core import beru_continuo as bc
from core.beru_capital import grado_desde_tier
from core.models import BeruShip


ARMAS_CONDICIONAL = frozenset({"SOLDADO", "CAPITAN", "GENERAL", "MARISCAL"})
ARMA_CONDICIONAL = "CONDICIONAL"


def grado_de_barco(beru: Any) -> str:
    tid = str(getattr(beru, "tier_id", "") or "")
    if tid:
        return str(grado_desde_tier(tid)).upper()
    g = str(getattr(beru, "grado", "") or "").upper()
    if g in ARMAS_CONDICIONAL:
        return g
    return beru_cazador.grado_de_barco(beru)


def arma_de_grado(grado: str) -> str:
    _ = grado
    return ARMA_CONDICIONAL


def arma_de_barco(beru: Any) -> str:
    return arma_de_grado(grado_de_barco(beru))


def sincronizar_arma(beru: Any) -> str:
    arma = arma_de_barco(beru)
    beru.arma_cazador = arma
    return arma


@dataclass
class EventoAltar:
    tipo: str
    grado: str
    arma: str
    precio: float
    masa: float
    oz_adan: float = 0.0
    red_adan: float = 0.0
    detalle: str = ""

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ResultadoPulso:
    eventos: list[EventoAltar] = field(default_factory=list)
    estado: str = ""
    masa: float = 0.0
    arma: str = ""
    relevo: BeruShip | None = None


def registrar_red_tocada(beru: Any) -> tuple[float, float]:
    """Guarda la Red que el precio tocó ANTES de mover Hoz/Red otro paso."""
    pct = float(getattr(beru, "red_pct", 0) or 0)
    precio = float(getattr(beru, "red_adan", 0) or 0)
    if pct == 0.0 or precio <= 0:
        return 0.0, 0.0
    beru.ultima_red_tocada_pct = pct
    beru.ultima_red_tocada_precio = precio
    return pct, precio


def _uid_relevo(beru: Any, activo: str) -> str:
    gen = int(getattr(beru, "generacion", 1) or 1) + 1
    cola = str(getattr(beru, "uid", "") or "")[-12:].replace(":", "_")
    return f"BERU_SEM_{str(activo or 'ETH').upper()}_R{gen}_{cola}"


def enterrar_red(beru: Any) -> None:
    """Funeral en memoria. En live se llamará solo tras confirmar cancelación."""
    beru.masa = 0.0
    beru.masa_tramo_usd = 0.0
    beru.oz_pct = 0.0
    beru.red_pct = 0.0
    beru.oz_adan = 0.0
    beru.red_adan = 0.0
    if hasattr(beru, "qty_base_ejecutada"):
        beru.qty_base_ejecutada = 0.0
    beru.funeral_red_confirmado = True


def crear_relevo_desde_hoz(
    beru: Any,
    precio_fill: float,
    *,
    activo: str,
    fill_confirmado: bool,
) -> BeruShip | None:
    """Cierra la caza. Planta sangre ±1.1 desde la Hoz y Red en tendencia.

    El llamado de sangre no es condicional. Si la Red gana, la sangre se apaga.
    """
    _assert_sin_tumor(beru)
    if not fill_confirmado:
        return None
    if bool(getattr(beru, "relevo_creado", False)):
        return None

    grado = grado_de_barco(beru)
    fill = float(precio_fill or 0)
    if fill <= 0:
        return None

    hoz_pct = float(getattr(beru, "oz_pct", 0) or 0)
    beru.precio_salida_real = fill
    beru.estado = "COSECHADO"
    enterrar_red(beru)
    beru.ultima_hoz_tocada_pct = hoz_pct
    beru.ultima_hoz_tocada_precio = fill

    if grado == "MARISCAL":
        beru.relevo_creado = True
        return None

    hijo = bc.plantar_orejas_post_hoz(
        beru, fill, activo=activo, grado=grado,
    )
    if hijo is None:
        return None
    beru.relevo_creado = True
    return hijo


def _evento(
    tipo: str,
    beru: Any,
    precio: float,
    *,
    detalle: str = "",
) -> EventoAltar:
    grado = grado_de_barco(beru)
    return EventoAltar(
        tipo=tipo,
        grado=grado,
        arma=arma_de_grado(grado),
        precio=float(precio or 0),
        masa=float(getattr(beru, "masa", 0) or 0),
        oz_adan=float(getattr(beru, "oz_adan", 0) or 0),
        red_adan=float(getattr(beru, "red_adan", 0) or 0),
        detalle=detalle,
    )


def _assert_sin_tumor(beru: Any) -> None:
    """Candado: la ruta viva no revive negociador / ping-pong / mega."""
    modo = str(getattr(beru, "modo_combate", "") or "").upper()
    if modo and modo not in ("CAZA", ""):
        raise AssertionError(f"tumor modo_combate={modo}")
    if bool(getattr(beru, "ciclo_infinito", False)):
        raise AssertionError("tumor ciclo_infinito")
    if bool(getattr(beru, "neg_post_cazador", False)):
        raise AssertionError("tumor neg_post_cazador")
    if float(getattr(beru, "masa_congelada", 0) or 0) > 1e-9:
        raise AssertionError("tumor masa_congelada")
    estado = str(getattr(beru, "estado", "") or "")
    if estado in (
        "NEGOCIANDO",
        "ESPERANDO_CONDICIONAL",
        "ESPERANDO_ABISMO",
        "FUSIONADO",
    ):
        raise AssertionError(f"tumor estado={estado}")


def pulsar_cazador_sim(
    beru: Any,
    precio: float,
    *,
    activo: str = "ETH",
    engorde: bool = True,
) -> ResultadoPulso:
    """Un latido de simulación: arma + masa según Red; cosecha al tocar Hoz."""
    _assert_sin_tumor(beru)
    px = float(precio or 0)
    out = ResultadoPulso()
    if px <= 0:
        out.estado = str(getattr(beru, "estado", "") or "")
        return out

    grado = grado_de_barco(beru)
    arma = sincronizar_arma(beru)
    estado = str(getattr(beru, "estado", "") or "")

    if estado == "ACECHANDO":
        oreja = bc.decidir_oreja_acecho(beru, px)
        if not oreja:
            out.estado = estado
            out.arma = arma
            return out
        masa = bc.armar_tramo(beru, px, activo=activo, grado=grado, oreja=oreja)
        sincronizar_arma(beru)
        tipo = "ARMAR_CONDICIONAL"
        out.eventos.append(
            _evento(
                tipo,
                beru,
                px,
                detalle=(
                    f"llamado {bc.distancia_llamado_pct(beru)*100:.2f}% · "
                    f"Hoz {bc.distancia_hoz_pct(beru)*100:.2f}% · masa ${masa:.2f}"
                ),
            )
        )
        out.estado = beru.estado
        out.masa = float(beru.masa or 0)
        out.arma = arma
        _assert_sin_tumor(beru)
        return out

    if estado != "CAZANDO":
        out.estado = estado
        out.arma = arma
        return out

    # Hoz primero: vuelve el precio y cobra el tramo.
    if beru_cazador.toca_oz(px, beru.direccion, float(beru.oz_adan or 0)):
        masa_tramo = float(beru.masa or 0)
        tipo = "COSECHA_CONDICIONAL"
        out.eventos.append(
            _evento(tipo, beru, px, detalle=f"transmuta ${masa_tramo:.2f}"),
        )
        relevo = crear_relevo_desde_hoz(
            beru, px, activo=activo, fill_confirmado=True,
        )
        out.estado = beru.estado
        out.masa = 0.0
        out.arma = arma
        out.relevo = relevo
        _assert_sin_tumor(beru)
        return out

    if beru_cazador.toca_red(px, beru.direccion, float(beru.red_adan or 0)):
        registrar_red_tocada(beru)
        masa_extra = (
            float(beru_cazador.engorde_paso_usd(activo, grado)) if engorde else 0.0
        )
        bc.avanzar_frontera(beru, masa_extra)
        sincronizar_arma(beru)
        tipo = "MOVER_CONDICIONAL"
        detalle = (
            f"quita carta vieja · planta Hoz nueva · +${masa_extra:.2f} "
            f"→ tramo ${float(beru.masa or 0):.2f}"
        )
        out.eventos.append(_evento(tipo, beru, px, detalle=detalle))

    out.estado = str(beru.estado or "")
    out.masa = float(getattr(beru, "masa", 0) or 0)
    out.arma = arma
    _assert_sin_tumor(beru)
    return out


def simular_camino(
    beru: Any,
    precios: list[float],
    *,
    activo: str = "ETH",
    engorde: bool = True,
) -> list[EventoAltar]:
    """Recorre un camino de precios; devuelve la bitácora del altar."""
    bitacora: list[EventoAltar] = []
    for px in precios:
        r = pulsar_cazador_sim(beru, float(px), activo=activo, engorde=engorde)
        bitacora.extend(r.eventos)
    return bitacora


def resumen_bitacora(eventos: list[EventoAltar]) -> dict[str, Any]:
    contadores: dict[str, int] = {}
    for e in eventos:
        contadores[e.tipo] = contadores.get(e.tipo, 0) + 1
    return {
        "n_eventos": len(eventos),
        "contadores": contadores,
        "armas": sorted({e.arma for e in eventos}),
        "grados": sorted({e.grado for e in eventos}),
    }
