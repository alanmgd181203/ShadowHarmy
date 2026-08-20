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

    async def pulso(self, precio: float | None = None) -> dict[str, Any]:
        beru = self.vivo
        if beru is None or beru.estado in ("COSECHADO", "FOSIL_BLOQUEADO"):
            return {"ok": False, "motivo": "sin_vivo"}
        px = float(precio or 0) or self._precio_lineal(self._activo)
        if px <= 0:
            return {"ok": False, "motivo": "sin_precio"}

        if beru.estado == "ACECHANDO":
            if bool(getattr(beru, "es_relevo_cazador", False)) or float(
                getattr(beru, "ultima_hoz_tocada_precio", 0) or 0
            ) > 0:
                if beru_rango.toca_red_continuacion(beru, px):
                    masa = beru_rango.armar_tramo_desde_red(beru, precio=px)
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
                    }
                if beru_rango.toca_sangre(beru, px):
                    masa = beru_rango.armar_tramo_desde_sangre(beru, precio=px)
                    await self._tras_armar(beru, origen="SANGRE", masa=masa)
                    return {"ok": True, "evento": "ARMAR_SANGRE", "masa": masa, "dir": beru.direccion}
            else:
                lado = beru_rango.toca_vacio(beru, px)
                if lado:
                    masa = beru_rango.armar_tramo_desde_vacio(beru, lado, precio=px)
                    await self._tras_armar(beru, origen=f"VACIO_{lado}", masa=masa)
                    return {"ok": True, "evento": f"ARMAR_{lado}", "masa": masa, "dir": beru.direccion}
            return {"ok": True, "evento": "ACECHO"}

        if beru.estado == "CAZANDO":
            beru_rango.actualizar_trailing_oz(beru, px)
            if self._manos():
                await beru_rango_altar.seguir_trailing(
                    self.bridge, beru, activo=self._activo,
                )
            if beru_rango.toca_oz(beru, px):
                fill = float(beru.oz_adan or px)
                masa_hecha = float(getattr(beru, "masa", 0) or 0)
                if self._manos():
                    fill_casa = await self._consultar_fill(beru)
                    if fill_casa:
                        fill = float(fill_casa.get("avgPrice") or fill)
                    else:
                        # Cerebro detona: Market de entrada en Bybit
                        await beru_rango_altar.disparar_entrada_market(
                            self.bridge, beru, activo=self._activo, masa_usd=masa_hecha,
                        )
                        fill = float(px)
                beru_rango.cosechar_oz_y_mover_cero(beru, fill)
                await self.bel.anotar(
                    "BERU_RANGO", "OZ_COSECHA",
                    f"{beru.uid} trailing Oz @{fill:.6f} → 0 · sangre {beru.sangre_lado} "
                    f"{beru_rango.sangre_contraria_pct()*100:.1f}% · "
                    f"Red @{beru.red_adan:.6f} (${beru_rango.masa_red_usd():.0f}).",
                )
                self._bitacora(
                    "OZ_COSECHA",
                    detalle=f"0={fill} sangre={beru.sangre_lado} red={beru.red_adan}",
                    precio=fill,
                    masa_usd=masa_hecha,
                )
                return {
                    "ok": True,
                    "evento": "OZ_COSECHA",
                    "cero": fill,
                    "sangre": getattr(beru, "sangre_lado", ""),
                    "red": beru.red_adan,
                    "masa_hecha": masa_hecha,
                }
            return {"ok": True, "evento": "CAZA"}

        return {"ok": False, "motivo": f"estado_{beru.estado}"}

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
            try:
                plan = beru_rango_altar.plan_trailing_entrada(
                    beru, activo=self._activo, masa_usd=masa,
                )
                await beru_rango_altar.armar_condicional(self.bridge, beru, plan)
            except ValueError as exc:
                await self.bel.anotar(
                    "BERU_RANGO", "ALTAR_PLAN_FALLIDO", f"{beru.uid}: {exc}",
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
        status = str((estado.datos or {}).get("orderStatus") or estado.mensaje or "")
        if status != "Filled":
            return None
        return {
            "avgPrice": float((estado.datos or {}).get("avgPrice") or beru.oz_adan or 0),
            "cumExecQty": float((estado.datos or {}).get("cumExecQty") or 0),
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
            "cero": beru.centro_local,
            "oz": beru.oz_adan,
            "red": beru.red_adan,
            "trail_extremo": getattr(beru, "trail_extremo", 0),
            "masa": beru.masa,
            "sangre_lado": getattr(beru, "sangre_lado", ""),
            "cosechas": int(getattr(beru, "cosechas_continuas", 0) or 0),
            "escalones_red": int(getattr(beru, "rango_escalones_red", 0) or 0),
        }
        return out
