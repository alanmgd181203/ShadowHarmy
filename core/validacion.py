"""
Validación de checklist — lectura de estado real del Ejército.
Cada check devuelve: pass | fail | pending | stub | skip
"""
from __future__ import annotations

import json
import os
import re
import time
from dataclasses import asdict, dataclass, field
from typing import Any, Callable, Literal

import core.config as config

CheckStatus = Literal["pass", "fail", "pending", "stub", "skip"]
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")


@dataclass
class CheckResult:
    id: str
    fase: str
    titulo: str
    status: CheckStatus
    detalle: str = ""
    meta: dict = field(default_factory=dict)


@dataclass
class InformeValidacion:
    ts: float
    checks: list[CheckResult]
    resumen: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "ts": self.ts,
            "resumen": self.resumen,
            "checks": [asdict(c) for c in self.checks],
        }


def _ruta(relativa: str) -> str:
    return os.path.join(ROOT, relativa)


def _leer_json(ruta: str) -> dict | None:
    if not os.path.exists(ruta):
        return None
    try:
        with open(ruta, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def _contar_eventos_bellion(general: str, accion: str, historial: str | None = None) -> int:
    ruta = historial or _ruta(f"data/historial_{config.FASE_ACTUAL.lower()}.jsonl")
    if not os.path.exists(ruta):
        return 0
    patron = re.compile(rf"\[{general}\] {re.escape(accion)}:")
    count = 0
    with open(ruta, encoding="utf-8") as f:
        for linea in f:
            if patron.search(linea):
                count += 1
    return count


def _buscar_par_caza_cosecha(historial: str | None = None) -> tuple[bool, str]:
    """True si existe al menos un CAZA seguido eventualmente por COSECHA en el historial."""
    ruta = historial or _ruta(f"data/historial_{config.FASE_ACTUAL.lower()}.jsonl")
    if not os.path.exists(ruta):
        return False, "Sin historial Bellion"
    caza_visto = False
    ultimo_caza_ts = None
    with open(ruta, encoding="utf-8") as f:
        for linea in f:
            if "[BERU] CAZA:" in linea and "CAZA_BLOQUEADA" not in linea and "CAZA_ORDEN" not in linea:
                caza_visto = True
                m = re.match(r"\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\]", linea)
                ultimo_caza_ts = m.group(1) if m else None
            if caza_visto and "[BERU] COSECHA:" in linea:
                return True, f"Ciclo detectado (CAZA {ultimo_caza_ts or '?'} → COSECHA)"
    if caza_visto:
        return False, "Hay CAZA pero aún no COSECHA en historial"
    return False, "Sin eventos BERU CAZA en historial"


# --- Checks individuales ---


def check_pentiverso_dual() -> CheckResult:
    ruta = _ruta("data/validacion_m2.json")
    data = _leer_json(ruta)
    if not data:
        return CheckResult(
            "3.1", "3", "Pentiverso dual LTC+BTC (10 mares)",
            "pending", "Ejecutar: python scripts/validar_m2.py",
        )
    pent = data.get("pentiverso", {})
    n = pent.get("mares_con_precio", 0)
    esperados = len(config.MARES_PENTIVERSO_ALL)
    ok = pent.get("ok_pentiverso", False) and n == esperados
    return CheckResult(
        "3.1", "3", "Pentiverso dual LTC+BTC (10 mares)",
        "pass" if ok else "fail",
        f"{n}/{esperados} mares con precio",
        {"mares_con_precio": n, "esperados": esperados},
    )


def check_persistencia() -> CheckResult:
    ruta = _ruta("data/validacion_m2.json")
    data = _leer_json(ruta)
    if not data:
        return CheckResult("3.3", "3", "Persistencia ley_de_sucesion", "pending", "Correr validar_m2.py")
    pers = data.get("persistencia", {})
    ok = pers.get("ok_sucesion") and pers.get("ok_recovery")
    return CheckResult(
        "3.3", "3", "Persistencia ley_de_sucesion + recovery",
        "pass" if ok else "fail",
        pers.get("ruta", "data/estado_hierro.json"),
    )


def check_ciclo_ejercito(historial: str | None = None) -> CheckResult:
    ok, detalle = _buscar_par_caza_cosecha(historial)
    reporte = _leer_json(_ruta("data/validacion_ciclo_ejercito.json"))
    if reporte and reporte.get("ok_ciclo"):
        detalle = reporte.get("detalle", detalle)
        ok = True
    if ok:
        return CheckResult("3.6.1", "3", "Ciclo CAZA → COSECHA en Bellion", "pass", detalle)
    n_caza = _contar_eventos_bellion("BERU", "CAZA", historial)
    n_cosecha = _contar_eventos_bellion("BERU", "COSECHA", historial)
    return CheckResult(
        "3.6.1", "3", "Ciclo CAZA → COSECHA en Bellion",
        "pending",
        f"{detalle} | CAZA={n_caza} COSECHA={n_cosecha}. "
        "Simular: python scripts/probar_ciclo_beru.py | Live: arise.py testnet",
        {"caza": n_caza, "cosecha": n_cosecha},
    )


def check_modo_simulacion_gate() -> CheckResult:
    """3.6.2 — live solo tras ciclo validado."""
    ciclo = check_ciclo_ejercito()
    if config.MODO_SIMULACION:
        return CheckResult(
            "3.6.2", "3", "Gate MODO_SIMULACION=False",
            "pass" if ciclo.status == "pass" else "pending",
            "MODO_SIMULACION=True (seguro). "
            + ("Listo para probar live en testnet." if ciclo.status == "pass"
               else "Esperar 3.6.1 antes de MODO_SIMULACION=False"),
        )
    if ciclo.status != "pass":
        return CheckResult(
            "3.6.2", "3", "Gate MODO_SIMULACION=False",
            "fail",
            "MODO_SIMULACION=False SIN ciclo CAZA→COSECHA validado — volver a True",
        )
    return CheckResult(
        "3.6.2", "3", "Gate MODO_SIMULACION=False",
        "pass",
        "Live testnet habilitado (ciclo documentado)",
    )


def check_bootstrap_manto_codigo() -> CheckResult:
    # Fracción 0 = sizing vía beru_capital (sin tope 25%); código debe tener BOOTSTRAP_MANTO
    ok_cfg = hasattr(config, "BOOTSTRAP_MANTO_FRACCION")
    igris = _ruta("generales/igris.py")
    src = open(igris, encoding="utf-8").read() if os.path.exists(igris) else ""
    tiene = "BOOTSTRAP_MANTO" in src and "rangos_activo" in src
    return CheckResult(
        "3.5", "3", "Bootstrap manto Igris (código)",
        "pass" if ok_cfg and tiene else "fail",
        f"BOOTSTRAP_MANTO_FRACCION={getattr(config, 'BOOTSTRAP_MANTO_FRACCION', '?')} · beru_capital",
    )


def check_greed_usdt_usdc() -> CheckResult:
    greed = _ruta("generales/greed.py")
    mercado_py = _ruta("core/mercado.py")
    if not os.path.exists(greed) or not os.path.exists(mercado_py):
        return CheckResult("3.2.1", "3", "Greed USDT×USDC dual", "fail", "Archivos faltantes")
    g = open(greed, encoding="utf-8").read()
    m = open(mercado_py, encoding="utf-8").read()
    ok = "escanear_mejor_regalo_usdt_usdc" in g and "escanear_mejor_regalo_usdt_usdc" in m
    return CheckResult(
        "3.2.1", "3", "Greed mezcla USDT×USDC (LTC+BTC)",
        "pass" if ok else "fail",
        "Radar cross USDT/USDC por activo",
    )


def check_telegram() -> CheckResult:
    ruta = _ruta("core/telegram.py")
    if not os.path.exists(ruta):
        return CheckResult("4.1.1", "4", "core/telegram.py", "pending", "Pendiente Fase 4")
    contenido = open(ruta, encoding="utf-8").read()
    if "NotImplementedError" in contenido or "STUB" in contenido.upper():
        return CheckResult("4.1.1", "4", "Telegram enviar_telegram", "stub", "Stub listo — falta token en .env")
    if "async def enviar_telegram" in contenido:
        return CheckResult("4.1.1", "4", "Telegram enviar_telegram", "pass", "Implementado")
    return CheckResult("4.1.1", "4", "Telegram enviar_telegram", "fail", "Archivo incompleto")


def check_safe_mode() -> CheckResult:
    if not hasattr(config, "SAFE_MODE"):
        return CheckResult("4.2.1", "4", "SAFE_MODE flag", "pending", "Añadir SAFE_MODE en config")
    if config.SAFE_MODE:
        return CheckResult("4.2.1", "4", "SAFE_MODE activo", "pass", "Modo seguro ON — Beru caza permitida (doctrina 23)")
    return CheckResult("4.2.1", "4", "SAFE_MODE flag", "stub", "Flag definido; lógica Fase 4.2")


def check_env_keys() -> CheckResult:
    ok = bool(config.API_KEY and config.API_SECRET)
    if getattr(config, "TESTNET", False):
        etiqueta = "BYBIT_TESTNET_API_KEY/SECRET"
    else:
        etiqueta = "BYBIT_API_KEY/SECRET (mainnet)"
    return CheckResult(
        "0.3", "0", ".env BYBIT keys",
        "pass" if ok else "fail",
        f"Keys presentes ({etiqueta})" if ok else f"Faltan {etiqueta}",
    )


def check_m1_roundtrip() -> CheckResult:
    data = _leer_json(_ruta("data/m1_btc_roundtrip.json"))
    if not data:
        return CheckResult("2.5.1", "2", "Trade redondo testnet M1", "pending", "Sin data/m1_btc_roundtrip.json")
    ok = data.get("open_positions_remaining") == 0 and data.get("buy_order_id")
    return CheckResult(
        "2.5.1", "2", "Trade redondo testnet M1",
        "pass" if ok else "fail",
        f"{data.get('symbol')} pnl={data.get('pnl_usd')}",
    )


def check_tank_sentidos_panorama() -> CheckResult:
    """3.7 — desvío índice / panorama (informe opcional)."""
    ruta = _ruta("data/validacion_panorama_tank.json")
    data = _leer_json(ruta)
    spreads = _ruta("core/spreads.py")
    binance = _ruta("core/binance_ref.py")
    codigo_ok = (
        os.path.exists(spreads)
        and "calcular_desvios_indice" in open(spreads, encoding="utf-8").read()
        and os.path.exists(binance)
    )
    if not codigo_ok:
        return CheckResult("3.7", "3", "Sentidos Tank Fase 1+2 (código)", "fail", "Faltan spreads.py/binance_ref.py")
    if not data:
        return CheckResult(
            "3.7", "3", "Sentidos Tank Fase 1+2",
            "pending",
            "Ejecutar: python scripts/validar_panorama_tank.py --segundos 35",
        )
    desv = data.get("desvios_indice", {})
    top = desv.get("top_n", 0) or len(desv.get("filas_muestra") or [])
    matriz = data.get("matriz_spreads_top", 0)
    ok = top > 0 or matriz > 0
    refs = (data.get("panorama_global") or {}).get("refs_binance", 0)
    detalle = f"desvios_top={top} matriz_top={matriz} refs_binance={refs}"
    if refs == 0 and ok:
        detalle += " (Binance puede estar bloqueado por geo)"
    return CheckResult(
        "3.7", "3", "Sentidos Tank Fase 1+2",
        "pass" if ok else "fail",
        detalle,
    )


def check_greed_kaiser_pipeline() -> CheckResult:
    greed = _ruta("generales/greed.py")
    mision = _ruta("core/greed_mision.py")
    pipeline = _ruta("core/kaiser_pipeline.py")
    if not all(os.path.exists(p) for p in (greed, mision, pipeline)):
        return CheckResult("3.8.14", "3", "Pipeline Kaiser→Greed", "fail", "Archivos faltantes")
    g = open(greed, encoding="utf-8").read()
    ok = "consumir_greed" in g and "resolver_plan" in open(mision, encoding="utf-8").read()
    return CheckResult(
        "3.8.14", "3", "Pipeline Kaiser→Greed",
        "pass" if ok else "fail",
        "Greed consume cola Kaiser + greed_mision",
    )


def check_greed_omnimercado_v1() -> CheckResult:
    mods = ("core/greed_multicruce.py", "core/greed_basis.py", "core/greed_sizing.py")
    missing = [m for m in mods if not os.path.exists(_ruta(m))]
    if missing:
        return CheckResult("3.2.3", "3", "Greed omnimercado v1", "fail", f"Faltan: {missing}")
    smokes = (
        "scripts/validar_greed_multicruce_smoke.py",
        "scripts/validar_greed_basis_smoke.py",
    )
    sm_missing = [s for s in smokes if not os.path.exists(_ruta(s))]
    det = "multicruce + basis hold"
    if sm_missing:
        det += f" (smokes faltantes: {sm_missing})"
        return CheckResult("3.2.3", "3", "Greed omnimercado v1", "pending", det)
    return CheckResult("3.2.3", "3", "Greed omnimercado v1", "pass", det)


def check_beru_proto() -> CheckResult:
    mods = ("core/beru_tier.py", "core/beru_capital.py", "core/beru_rail.py")
    missing = [m for m in mods if not os.path.exists(_ruta(m))]
    if missing:
        return CheckResult("3.5.7", "3", "Beru Proto (capital + rail)", "fail", f"Faltan: {missing}")
    beru = open(_ruta("generales/beru.py"), encoding="utf-8").read()
    ok = "beru_rail" in beru
    return CheckResult(
        "3.5.7", "3", "Beru Proto (capital + rail)",
        "pass" if ok else "stub",
        "beru_tier + beru_capital + beru_rail",
    )


def check_igris_manto_se() -> CheckResult:
    manto = _ruta("core/igris_manto.py")
    desp = _ruta("core/igris_despliegue.py")
    igris = _ruta("generales/igris.py")
    if not os.path.exists(manto):
        return CheckResult("3.5.8", "3", "Igris §E manto", "fail", "Falta igris_manto.py")
    if not os.path.exists(desp):
        return CheckResult("3.5.8", "3", "Igris §E manto", "fail", "Falta igris_despliegue.py")
    i = open(igris, encoding="utf-8").read()
    m = open(manto, encoding="utf-8").read()
    d = open(desp, encoding="utf-8").read()
    ok = (
        "igris_manto" in i
        and "frentes_bootstrap" in m
        and "evaluar_puerta_se" in d
        and "igris_despliegue" in i
        and "_inyectar_dual_paciente" in i
    )
    if not ok:
        return CheckResult("3.5.8", "3", "Igris §E manto", "fail", "Falta cableo igris paciente §E")
    return CheckResult(
        "3.5.8", "3", "Igris §E manto", "pass",
        "dual §E Ask/Bid + fees break-even + urgencia + micro-mordidas",
    )


def check_fase3_cerrada() -> CheckResult:
    subs = [
        check_pentiverso_dual(), check_persistencia(), check_greed_usdt_usdc(),
        check_bootstrap_manto_codigo(), check_ciclo_ejercito(), check_modo_simulacion_gate(),
        check_greed_kaiser_pipeline(), check_greed_omnimercado_v1(), check_beru_proto(),
        check_igris_manto_se(),
    ]
    fails = [c for c in subs if c.status == "fail"]
    pending = [c for c in subs if c.status in ("pending", "stub")]
    if fails:
        return CheckResult("3.0", "3", "Fase 3 M2 cerrada", "fail", f"Fallos: {[c.id for c in fails]}")
    if pending:
        stubs = [c.id for c in pending]
        return CheckResult(
            "3.0", "3", "Fase 3 M2 cerrada", "stub",
            f"Gates OK; parcial: {stubs}",
        )
    return CheckResult("3.0", "3", "Fase 3 M2 cerrada", "pass", "Todos los gates Fase 3 OK")


# Registro de checks por fase
CHECKS_FASE: dict[str, list[Callable[[], CheckResult]]] = {
    "0": [check_env_keys],
    "2": [check_m1_roundtrip],
    "3": [
        check_fase3_cerrada,
        check_pentiverso_dual,
        check_persistencia,
        check_greed_usdt_usdc,
        check_bootstrap_manto_codigo,
        check_ciclo_ejercito,
        check_modo_simulacion_gate,
        check_tank_sentidos_panorama,
        check_greed_kaiser_pipeline,
        check_greed_omnimercado_v1,
        check_beru_proto,
        check_igris_manto_se,
    ],
    "4": [check_telegram, check_safe_mode],
}


def ejecutar_checks(fases: list[str] | None = None) -> InformeValidacion:
    fases = fases or ["0", "2", "3", "4"]
    resultados: list[CheckResult] = []
    for f in fases:
        for fn in CHECKS_FASE.get(f, []):
            resultados.append(fn())
    resumen: dict[str, int] = {}
    for c in resultados:
        resumen[c.status] = resumen.get(c.status, 0) + 1
    return InformeValidacion(ts=time.time(), checks=resultados, resumen=resumen)


def advertir_gates() -> None:
    """Llamar al arranque de arise.py — avisos sin bloquear."""
    ciclo = check_ciclo_ejercito()
    sim = check_modo_simulacion_gate()
    if sim.status == "fail":
        print(f"\n[⚠️ GATE] {sim.detalle}\n")
    elif ciclo.status == "pending":
        print(f"\n[ℹ️ CHECKLIST] 3.6.1 pendiente: {ciclo.detalle}\n")
    if config.SAFE_MODE:
        print("[🛡️ SAFE_MODE] Activo — Greed pausado; Beru/Igris según doctrina 23\n")


def guardar_informe(informe: InformeValidacion, ruta: str | None = None) -> str:
    dest = ruta or _ruta("data/validacion_checklist.json")
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(dest, "w", encoding="utf-8") as f:
        json.dump(informe.to_dict(), f, indent=2, ensure_ascii=False)
    return dest
