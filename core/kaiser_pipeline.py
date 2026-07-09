"""Pipeline Kaiser→Greed — latencia, estabilidad del spread, abort."""
from __future__ import annotations

import time
from collections import deque
from typing import Any

import core.config as config


def estimar_pipeline_ms(
    tank_latencia_ms: float = 0.0,
    kaiser_calc_ms: float = 0.0,
) -> dict[str, float]:
    """Suma tramos configurables + latencia Tank + último cálculo Kaiser."""
    alert = float(getattr(config, "PIPELINE_KAISER_ALERT_MS", 5))
    greed = float(getattr(config, "PIPELINE_GREED_DECIDE_MS", 15))
    exec_ms = float(getattr(config, "PIPELINE_EXECUTE_MS", 50))
    total = tank_latencia_ms + kaiser_calc_ms + alert + greed + exec_ms
    return {
        "tank_ms": round(tank_latencia_ms, 2),
        "kaiser_calc_ms": round(kaiser_calc_ms, 2),
        "alerta_ms": alert,
        "greed_decide_ms": greed,
        "execute_ms": exec_ms,
        "total_ms": round(total, 2),
    }


def clave_oportunidad(base: str, tipo_spread: str) -> str:
    return f"{base.upper()}:{tipo_spread}"


class RastreadorSpread:
    """Historial corto de spread por cruce — detectar flash muerto."""

    def __init__(self, max_len: int | None = None):
        self.max_len = max_len or getattr(config, "PIPELINE_SPREAD_HIST_LEN", 12)
        self._hist: dict[str, deque] = {}

    def registrar(self, clave: str, spread_pct: float, ts: float | None = None):
        ts = ts or time.time()
        if clave not in self._hist:
            self._hist[clave] = deque(maxlen=self.max_len)
        self._hist[clave].append((ts, float(spread_pct)))

    def spread_estable_para_pipeline(
        self,
        clave: str,
        spread_actual: float,
        pipeline_ms: float,
    ) -> tuple[bool, str]:
        """
        True si el spread no colapsó en la ventana del pipeline.
        Sin historial → aceptar (primer avistamiento).
        """
        hist = self._hist.get(clave)
        if not hist or len(hist) < 2:
            return True, "SIN_HISTORIAL"

        ventana_s = pipeline_ms / 1000.0
        ahora = time.time()
        en_ventana = [(t, s) for t, s in hist if (ahora - t) <= ventana_s]
        if len(en_ventana) < 2:
            return True, "VENTANA_CORTA"

        spreads = [s for _, s in en_ventana]
        pico = max(spreads)
        if pico <= 0:
            return False, "SPREAD_CERO"

        ratio = spread_actual / pico
        min_ratio = float(getattr(config, "PIPELINE_SPREAD_MIN_RATIO", 0.65))
        if ratio < min_ratio:
            return False, f"SPREAD_COLAPSO_{ratio:.2f}"
        return True, "OK"


class ColaOportunidadesGreed:
    """Oportunidades vivas hacia Greed; abort si mueren antes de manos."""

    def __init__(self):
        self._vivas: dict[str, dict] = {}

    @staticmethod
    def _oid(op: dict) -> str:
        base = op.get("base", "?")
        tipo = op.get("tipo_spread", "?")
        fc = (op.get("frentes") or {}).get("compra", "")
        return f"{base}:{tipo}:{fc}"

    def registrar_o_actualizar(self, op: dict, pipeline_ms: float) -> dict:
        oid = self._oid(op)
        ahora = time.time()
        ttl_s = pipeline_ms / 1000.0 * float(getattr(config, "PIPELINE_TTL_FACTOR", 3.0))
        ttl_s = max(ttl_s, float(getattr(config, "PIPELINE_TTL_MIN_S", 0.5)))

        prev = self._vivas.get(oid)
        entry = {
            **op,
            "oid": oid,
            "estado": "VIVA",
            "ts_primera": prev["ts_primera"] if prev else ahora,
            "ts_ultima": ahora,
            "expira_ts": ahora + ttl_s,
            "pipeline_ms": pipeline_ms,
        }
        self._vivas[oid] = entry
        return entry

    def abortar(self, oid: str, motivo: str) -> dict | None:
        entry = self._vivas.get(oid)
        if not entry:
            return None
        entry["estado"] = "ABORTADA"
        entry["abort_motivo"] = motivo
        entry["ts_abort"] = time.time()
        return dict(entry)

    def limpiar_expiradas(self) -> list[dict]:
        ahora = time.time()
        abortadas: list[dict] = []
        for oid, entry in list(self._vivas.items()):
            if entry.get("estado") == "ABORTADA":
                if ahora - float(entry.get("ts_abort") or 0) > 30:
                    del self._vivas[oid]
                continue
            if ahora > float(entry.get("expira_ts") or 0):
                ab = self.abortar(oid, "EXPIRADA_PIPELINE")
                if ab:
                    abortadas.append(ab)
        return abortadas

    def revalidar(
        self,
        op_actual: dict | None,
        *,
        oid: str | None = None,
        pipeline_ms: float,
        tank_semaforo: str,
    ) -> dict | None:
        """Re-evalúa oportunidad; abort si ya no cumple."""
        oid = oid or self._oid(op_actual or {})
        entry = self._vivas.get(oid)
        if not entry or entry.get("estado") != "VIVA":
            return None

        if tank_semaforo == "ROJO":
            return self.abortar(oid, "TANK_ROJO")

        if not op_actual:
            return self.abortar(oid, "DESAPARECIDA")

        from core import ancla

        neto = float(op_actual.get("regalo_neto_pct_est") or 0)
        fees = float(op_actual.get("fees_total_pct") or 0)
        if not ancla.cumple_regla_neto_vs_fees(neto, fees):
            return self.abortar(oid, "NETO_BAJO_FEES")

        max_u = float(op_actual.get("entrada_maxima_usd") or 0)
        min_ord = float(op_actual.get("min_order_usd_cruce") or 0)
        if max_u < min_ord:
            return self.abortar(oid, "BAJO_MIN_PAR")

        bruto = float(op_actual.get("spread_bruto_pct") or 0)
        bruto0 = float(entry.get("spread_bruto_pct") or 0)
        if bruto0 > 0 and bruto < bruto0 * float(getattr(config, "PIPELINE_SPREAD_MIN_RATIO", 0.65)):
            return self.abortar(oid, "SPREAD_CAYO")

        entry.update({
            **op_actual,
            "ts_ultima": time.time(),
            "expira_ts": time.time() + pipeline_ms / 1000.0 * float(getattr(config, "PIPELINE_TTL_FACTOR", 3.0)),
        })
        return None

    def entries_vivas(self) -> list[tuple[str, dict]]:
        return [(k, dict(v)) for k, v in self._vivas.items() if v.get("estado") == "VIVA"]

    def cola_vivas(self) -> list[dict]:
        return [v for _, v in self.entries_vivas()]

    def abortadas_recientes(self) -> list[dict]:
        return [dict(v) for v in self._vivas.values() if v.get("estado") == "ABORTADA"]
