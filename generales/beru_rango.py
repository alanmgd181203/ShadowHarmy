"""Beru rango — General lineal (Oz = trailing 0,2 tras Vacío ±1,2).

No reemplaza al Beru spot fósil. Manos/hilo OFF hasta GO del Monarca.
"""
from __future__ import annotations

import time
import uuid
from typing import Any

from core import beru_rango
from core import beru_rango_altar
from core.models import BeruShip
import core.config as config


class BeruRango:
    """Vacío arma trailing · Oz 0,2 detrás del extremo · Red ladder $5."""

    def __init__(self, tusk, bellion, tank, bridge=None, kaiser=None):
        self.tusk = tusk
        self.bel = bellion
        self.tank = tank
        self.bridge = bridge
        self.kaiser = kaiser
        self.vivo: BeruShip | None = None
        self._activo = str(getattr(config, "BERU_RANGO_ACTIVO", "ETH") or "ETH").upper()

    def _manos(self) -> bool:
        return beru_rango.manos_activas() and self.bridge is not None

    def _precio_lineal(self, activo: str | None = None) -> float:
        act = str(activo or self._activo).upper()
        precios = getattr(self.tank, "precios", None) or {}
        for clave in (f"{act}USDT_LINEAL", f"{act}USDT", f"{act}USDT_SPOT"):
            try:
                px = float(precios.get(clave) or 0)
            except (TypeError, ValueError):
                px = 0.0
            if px > 0:
                return px
        return 0.0

    def _bitacora(self, evento: str, detalle: str = "", **extra) -> None:
        if not bool(getattr(config, "BERU_RANGO_BITACORA", True)):
            return
        uid = getattr(self.vivo, "uid", "") if self.vivo else ""
        bits = " ".join(f"{k}={v}" for k, v in extra.items() if v is not None)
        print(
            f"[BERU_RANGO] {evento} {uid} {detalle} {bits}".strip(),
            flush=True,
        )

    async def despertar(self, precio: float | None = None, *, activo: str | None = None) -> BeruShip:
        act = str(activo or self._activo).upper()
        self._activo = act
        px = float(precio or 0) or self._precio_lineal(act)
        if px <= 0:
            raise ValueError("BeruRango: sin precio lineal para despertar")
        if self.vivo is not None and self.vivo.estado not in ("COSECHADO", "FOSIL_BLOQUEADO"):
            self.vivo.estado = "COSECHADO"
            await self.bel.anotar(
                "BERU_RANGO", "UN_VIVO",
                f"Archiva {self.vivo.uid} antes de nacer el nuevo.",
            )
        beru = BeruShip(
            uid=f"RANGO_{act}_{uuid.uuid4().hex[:8]}",
            centro_local=px,
            masa=0.0,
            direccion="",
            estado="ACECHANDO",
            modo_combate="RANGO",
            frente_asignado=f"{act}USDT_LINEAL",
            ts_wake=time.time(),
            engorde_bloqueado=True,
        )
        beru_rango.despertar(beru, px, activo=act)
        self.vivo = beru
        await self.bel.anotar(
            "BERU_RANGO", "WAKE",
            f"{beru.uid} 0={px:.6f} Vacío ±{beru_rango.vacio_adan_pct()*100:.1f}% "
            f"→ trailing Oz {beru_rango.trailing_dist_pct()*100:.1f}% · "
            f"masa ${beru_rango.masa_tramo_usd():.2f} · Red→${beru_rango.masa_red_usd():.0f}.",
        )
        self._bitacora("WAKE", detalle=f"0={px}", precio=px, masa_usd=beru_rango.masa_tramo_usd())
        return beru

    async def pulso(
        self,
        precio: float | None = None,
        latido: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        beru = self.vivo
        if beru is None or beru.estado in ("COSECHADO", "FOSIL_BLOQUEADO"):
            return {"ok": False, "motivo": "sin_vivo"}
        lat = dict(latido or {})
        px = (
            float(precio or 0)
            or float(lat.get("last") or 0)
            or self._precio_lineal(self._activo)
        )
        if px <= 0:
            return {"ok": False, "motivo": "sin_precio"}

        if beru.estado == "ACECHANDO":
            await self._purgar_altar_acecho(beru)
            if bool(getattr(beru, "es_relevo_cazador", False)) or float(
                getattr(beru, "ultima_hoz_tocada_precio", 0) or 0
            ) > 0:
                # Misma vela: sangre gana el latido entero, luego Red.
                # (Antes: high tocaba Red y cortaba el for → nunca oía el low de sangre.)
                trig = ""
                px_arm = px
                for sample in beru_rango.secuencia_latido(px, lat):
                    if beru_rango.toca_sangre(beru, sample):
                        trig, px_arm = "SANGRE", sample
                        break
                if not trig:
                    for sample in beru_rango.secuencia_latido(px, lat):
                        if beru_rango.toca_red_activacion(beru, sample):
                            trig, px_arm = "RED", sample
                            break
                if trig == "SANGRE":
                    masa = beru_rango.armar_tramo_desde_sangre(beru, precio=px_arm)
                    if masa <= 0:
                        return {"ok": True, "evento": "ACECHO", "nota": "sangre_sin_masa"}
                    await self._tras_armar(beru, origen="SANGRE", masa=masa)
                    return {
                        "ok": True,
                        "evento": "ARMAR_SANGRE",
                        "masa": masa,
                        "dir": beru.direccion,
                    }
                if trig == "RED":
                    masa = beru_rango.armar_tramo_desde_red(beru, precio=px_arm)
                    if masa <= 0:
                        return {"ok": True, "evento": "ACECHO", "nota": "red_sin_masa"}
                    beru.uid = (
                        f"RANGO_{self._activo}_R"
                        f"{int(getattr(beru, 'rango_escalones_red', 1) or 1)}_"
                        f"{uuid.uuid4().hex[:6]}"
                    )
                    await self._tras_armar(beru, origen="RED", masa=masa)
                    return {
                        "ok": True,
                        "evento": "ARMAR_RED",
                        "masa": masa,
                        "dir": beru.direccion,
                        "escalon": int(getattr(beru, "rango_escalones_red", 0) or 0),
                        "nota": "Red meta-saco -> trailing callback 0.2",
                    }
            else:
                lado = (
                    beru_rango.toca_vacio_en_latido(beru, px, lat)
                    or beru_rango.toca_vacio(beru, px)
                )
                if lado:
                    masa = beru_rango.armar_tramo_desde_vacio(beru, lado, precio=px)
                    if masa <= 0:
                        return {"ok": True, "evento": "ACECHO", "nota": "vacio_sin_masa"}
                    await self._tras_armar(beru, origen=f"VACIO_{lado}", masa=masa)
                    return {
                        "ok": True,
                        "evento": f"ARMAR_{lado}",
                        "masa": masa,
                        "dir": beru.direccion,
                    }
            return {"ok": True, "evento": "ACECHO"}

        if beru.estado == "CAZANDO":
            # Tras armar (sangre/Red/Vacío): mechas del mismo vaso no cuentan
            # hasta que el rastro huya del precio de activación.
            px_trail = beru_rango.precio_trail_caza(beru, px, lat)
            beru_rango.actualizar_trailing_oz(beru, px_trail)
            if self._manos():
                if not str(getattr(beru, "altar_link_id", "") or ""):
                    await self._intentar_sello_entrada(
                        beru, float(getattr(beru, "masa", 0) or 0), origen="REPARAR_SELLO",
                    )
                await beru_rango_altar.seguir_trailing(
                    self.bridge, beru, activo=self._activo,
                )
            if beru_rango.toca_oz_en_latido(beru, px, lat) or beru_rango.toca_oz(beru, px):
                oz_viva = float(beru.oz_adan or 0)
                masa_hecha = float(getattr(beru, "masa", 0) or 0)
                extremo = float(getattr(beru, "trail_extremo", 0) or 0)
                dir_caza = str(getattr(beru, "direccion", "") or "").upper()
                wake = beru_rango.cero_wake(beru)
                if self._manos():
                    pack = await self._confirmar_fill_oz_manos(
                        beru, oz_viva=oz_viva, px=px, masa_hecha=masa_hecha,
                    )
                    if pack is None:
                        await self.bel.anotar(
                            "BERU_RANGO",
                            "OZ_SIN_FILL",
                            f"{beru.uid} Oz @{oz_viva:.6f} sin plata en casa "
                            f"({dir_caza} · doctrina: no cosechar mapa)",
                        )
                        print(
                            f"[RANGO] OZ_SIN_FILL {self._activo} Oz @{oz_viva:.6f} "
                            f"— esperando fill/posición",
                            flush=True,
                        )
                        return {"ok": True, "evento": "CAZA", "nota": "oz_sin_fill_casa"}
                    fill = float(pack.get("avgPrice") or oz_viva or px)
                else:
                    # Ojos / teatro: fill del mapa (sin manos).
                    fill = oz_viva or float(px)
                beru_rango.cosechar_oz_y_mover_cero(
                    beru, fill, oz_despliegue=oz_viva or None,
                )
                if self._manos():
                    await beru_rango_altar.cancelar_pendiente(
                        self.bridge,
                        beru,
                        activo=self._activo,
                        motivo="POST_OZ_COSECHA",
                    )
                    beru_rango_altar.limpiar_sello_altar(beru)
                await self.bel.anotar(
                    "BERU_RANGO", "OZ_COSECHA",
                    f"{beru.uid} Oz peldaño @{oz_viva:.6f} fill @{fill:.6f} · wake={wake:.6f} · "
                    f"sangre act. {beru.sangre_lado} "
                    f"{beru_rango.sangre_contraria_pct()*100:.1f}% · "
                    f"Red trailing act. @{beru.red_adan:.6f} "
                    f"(callback {beru_rango.trailing_dist_pct()*100:.1f}% · "
                    f"${beru_rango.masa_red_usd():.0f}) · extremo={extremo:.6f}.",
                )
                self._bitacora(
                    "OZ_COSECHA",
                    detalle=(
                        f"wake={wake} oz={oz_viva} fill={fill} sangre={beru.sangre_lado} "
                        f"red={beru.red_adan} extremo={extremo}"
                    ),
                    precio=fill,
                    masa_usd=masa_hecha,
                )
                return {
                    "ok": True,
                    "evento": "OZ_COSECHA",
                    "cero": wake,
                    "fill": fill,
                    "oz_despliegue": oz_viva,
                    "sangre": getattr(beru, "sangre_lado", ""),
                    "red": beru.red_adan,
                    "masa_hecha": masa_hecha,
                    "trail_extremo": extremo,
                    "oz": oz_viva,
                    "dir": dir_caza,
                }
            return {"ok": True, "evento": "CAZA"}

        return {"ok": False, "motivo": f"estado_{beru.estado}"}

    async def _purgar_altar_acecho(self, beru: BeruShip) -> None:
        """Acecho sin Oz no debe arrastrar Stop del altar (sello huérfano)."""
        if not self._manos():
            return
        if float(getattr(beru, "oz_adan", 0) or 0) > 0:
            return
        link = str(getattr(beru, "altar_link_id", "") or "")
        oid = str(getattr(beru, "altar_order_id", "") or "")
        if not link and not oid:
            return
        await beru_rango_altar.cancelar_pendiente(
            self.bridge,
            beru,
            activo=self._activo,
            motivo="ACECHO_SIN_OZ",
        )
        beru_rango_altar.limpiar_sello_altar(beru)

    async def _reconciliar_casa(self) -> None:
        if self.tusk is None or self.bridge is None:
            return
        if not hasattr(self.bridge, "get_positions"):
            return
        try:
            await self.tusk.reconciliar_con_exchange(self.bridge, activo=self._activo)
        except Exception:
            pass

    def _posicion_tramo_casa(self, beru: BeruShip) -> dict[str, float] | None:
        """Pierna viva en Tusk alineada con la dirección de la caza."""
        from core import beru_rango_panel

        d = str(getattr(beru, "direccion", "") or "").upper()
        if d not in ("LONG", "SHORT"):
            return None
        umbral = max(0.05, float(getattr(beru, "masa", 0) or 0) * 0.08)
        for row in beru_rango_panel.posicion_desde_tusk(self.tusk, self._activo):
            if str(row.get("lado") or "").upper() != d:
                continue
            masa = float(row.get("masa_usd") or 0)
            if masa + 1e-9 < umbral:
                continue
            px = float(row.get("precio") or 0)
            if px <= 0:
                continue
            return {"avgPrice": px, "masa_usd": masa, "orderStatus": "Filled"}
        return None

    async def _intentar_sello_entrada(
        self, beru: BeruShip, masa: float, *, origen: str,
    ) -> bool:
        """Coloca Stop en Oz o Market si el last ya pasó la Oz."""
        if not self._manos():
            return True
        px_now = self._precio_lineal(self._activo)
        if not beru_rango_altar.stop_trigger_valido(beru, px_now):
            oz = float(getattr(beru, "oz_adan", 0) or 0)
            await self.bel.anotar(
                "BERU_RANGO",
                "ALTAR_SKIP_STOP",
                f"{beru.uid} {origen}: last={px_now:.6f} ya pasó Oz @{oz:.6f} · Market",
            )
            mkt = await beru_rango_altar.disparar_entrada_market(
                self.bridge, beru, activo=self._activo, masa_usd=masa,
            )
            if not getattr(mkt, "exito", False):
                msg = str(getattr(mkt, "mensaje", "") or "market_rechazada")
                await self.bel.anotar(
                    "BERU_RANGO",
                    "ALTAR_MARKET_ARM_FALLIDO",
                    f"{beru.uid} {origen}: {msg}",
                )
                print(
                    f"[RANGO] ALTAR_MARKET_ARM_FALLIDO {self._activo} {origen}: {msg}",
                    flush=True,
                )
                return False
            await self._reconciliar_casa()
            return True
        try:
            plan = beru_rango_altar.plan_trailing_entrada(
                beru, activo=self._activo, masa_usd=masa,
            )
            res = await beru_rango_altar.armar_condicional(
                self.bridge, beru, plan,
            )
            if getattr(res, "exito", False):
                return True
            msg = str(getattr(res, "mensaje", "") or "orden_rechazada")
            if "110092" in msg or "expect Rising" in msg or "expect Falling" in msg:
                await self.bel.anotar(
                    "BERU_RANGO",
                    "ALTAR_STOP_INVALIDO",
                    f"{beru.uid}: {msg} · sin Stop · Oz→Market",
                )
                beru_rango_altar.limpiar_sello_altar(beru)
                mkt = await beru_rango_altar.disparar_entrada_market(
                    self.bridge, beru, activo=self._activo, masa_usd=masa,
                )
                if getattr(mkt, "exito", False):
                    await self._reconciliar_casa()
                    return True
            else:
                await self.bel.anotar(
                    "BERU_RANGO",
                    "ALTAR_ORDEN_FALLIDA",
                    f"{beru.uid} {origen}: {msg} · sin sello en exchange",
                )
                print(
                    f"[RANGO] ALTAR_ORDEN_FALLIDA {self._activo} {origen}: {msg}",
                    flush=True,
                )
            return False
        except ValueError as exc:
            await self.bel.anotar(
                "BERU_RANGO", "ALTAR_PLAN_FALLIDO", f"{beru.uid}: {exc}",
            )
            return False

    async def _confirmar_fill_oz_manos(
        self,
        beru: BeruShip,
        *,
        oz_viva: float,
        px: float,
        masa_hecha: float,
    ) -> dict[str, float] | None:
        """Fill = plata en casa. Sin avg ni posición → no cosechar."""
        fill_casa = await self._consultar_fill(beru)
        if fill_casa and float(fill_casa.get("avgPrice") or 0) > 0:
            return fill_casa

        await self._reconciliar_casa()
        pos = self._posicion_tramo_casa(beru)
        if pos:
            return pos

        await beru_rango_altar.cancelar_pendiente(
            self.bridge,
            beru,
            activo=self._activo,
            motivo="PRE_MARKET_OZ",
        )
        beru_rango_altar.limpiar_sello_altar(beru)
        mkt = await beru_rango_altar.disparar_entrada_market(
            self.bridge, beru, activo=self._activo, masa_usd=masa_hecha,
        )
        if not getattr(mkt, "exito", False):
            msg_m = str(getattr(mkt, "mensaje", "") or "market_rechazada")
            await self.bel.anotar(
                "BERU_RANGO",
                "ALTAR_MARKET_FALLIDO",
                f"{beru.uid} Oz @{oz_viva:.6f}: {msg_m}",
            )
            print(
                f"[RANGO] ALTAR_MARKET_FALLIDO {self._activo}: {msg_m}",
                flush=True,
            )
            return None

        await self._reconciliar_casa()
        pos = self._posicion_tramo_casa(beru)
        if pos:
            return pos

        datos = getattr(mkt, "datos", None) or {}
        avg = float(datos.get("avgPrice") or datos.get("fillPx") or 0)
        if avg > 0:
            return {"avgPrice": avg, "orderStatus": "Filled"}
        return None

    async def _tras_armar(self, beru: BeruShip, *, origen: str, masa: float) -> None:
        await self.bel.anotar(
            "BERU_RANGO", "ARMAR",
            f"{beru.uid} {origen} → trailing {beru.direccion} "
            f"Oz @{beru.oz_adan:.6f} (0,2 detrás de extremo {getattr(beru, 'trail_extremo', 0):.6f}) "
            f"Red @{beru.red_adan:.6f} (${masa:.2f}).",
        )
        self._bitacora(
            "ARMAR",
            detalle=origen,
            direccion=beru.direccion,
            oz_adan=beru.oz_adan,
            red_adan=beru.red_adan,
            masa_usd=masa,
            trail_extremo=getattr(beru, "trail_extremo", None),
        )
        if self._manos():
            ok = await self._intentar_sello_entrada(beru, masa, origen=origen)
            if not ok:
                print(
                    f"[RANGO] sello pendiente {self._activo} {origen} "
                    f"— CAZA sin altar hasta fill",
                    flush=True,
                )

    async def _consultar_fill(self, beru: BeruShip) -> dict | None:
        link = str(getattr(beru, "altar_link_id", "") or "")
        if not link or self.bridge is None:
            return None
        act = self._activo
        symbol = f"{act}USDT"
        estado = await self.bridge.get_order_status(
            symbol, link_id=link, category="linear", order_filter="StopOrder",
        )
        if not getattr(estado, "exito", False):
            return None
        datos = estado.datos or {}
        status = str(datos.get("orderStatus") or estado.mensaje or "")
        if status != "Filled":
            return None
        # Rechazar fill fantasma: lado distinto o precio lejos de la Oz viva.
        side = str(datos.get("side") or "").upper()
        d = str(getattr(beru, "direccion", "") or "").upper()
        if d == "SHORT" and side == "BUY":
            return None
        if d == "LONG" and side == "SELL":
            return None
        avg = float(datos.get("avgPrice") or 0)
        oz = float(getattr(beru, "oz_adan", 0) or 0)
        if avg <= 0:
            # OKX algo «effective» sin avg — no inventar fill desde el mapa.
            return None
        if oz > 0 and abs(avg - oz) / oz > 0.01:
            # >1% de la Oz: casi seguro sello viejo o slip extremo — no contaminar 0.
            return None
        return {
            "avgPrice": avg,
            "cumExecQty": float(datos.get("cumExecQty") or 0),
            "orderStatus": status,
        }

    def snapshot(self) -> dict[str, Any]:
        g = beru_rango.resumen_geometria()
        beru = self.vivo
        out = {
            "oficio": "RANGO",
            "activo": self._activo,
            "manos": self._manos(),
            "geometria": g,
            "vivo": None,
        }
        if beru is None:
            return out
        out["vivo"] = {
            "uid": beru.uid,
            "estado": beru.estado,
            "direccion": beru.direccion,
            "cero": beru_rango.cero_wake(beru),
            "oz": beru.oz_adan,
            "oz_despliegue": float(getattr(beru, "oz_despliegue_px", 0) or 0),
            "red": beru.red_adan,
            "trail_extremo": getattr(beru, "trail_extremo", 0),
            "masa": beru.masa,
            "saco_long": float(getattr(beru, "saco_long_usd", 0) or 0),
            "saco_short": float(getattr(beru, "saco_short_usd", 0) or 0),
            "sangre_lado": getattr(beru, "sangre_lado", ""),
            "sangre": float(getattr(beru, "sangre_adan", 0) or 0),
            "sangre_adan": float(getattr(beru, "sangre_adan", 0) or 0),
            "cosechas": int(getattr(beru, "cosechas_continuas", 0) or 0),
            "escalones_red": int(getattr(beru, "rango_escalones_red", 0) or 0),
            "ultima_hoz_direccion": getattr(beru, "ultima_hoz_direccion", "") or "",
            "altar_link_id": getattr(beru, "altar_link_id", "") or "",
            "altar_order_id": getattr(beru, "altar_order_id", "") or "",
            "altar_trigger_price": float(getattr(beru, "altar_trigger_price", 0) or 0),
            "altar_revision": int(getattr(beru, "altar_revision", 0) or 0),
            "altar_order_status": getattr(beru, "altar_order_status", "") or "",
        }
        return out
