"""Tusk — ritual permanente Funding LTC → Funding USDT → UTA, por pasos.

Cada invocación materializa como máximo una mutación:
1) convertir solo el activo que está en FUND a USDT;
2) transferir ese USDT desde FUND a UNIFIED;
3) verificar que ya no queda activo en FUND y que apareció USDT en UTA.

El orden evita mezclar el aporte nuevo con LTC que ya pueda servir como
colateral de un manto inverso dentro de UNIFIED.

Sin ``permitir_manos`` el módulo solo inspecciona y propone. Está diseñado para
ser idempotente: repetir un paso ya cumplido no vuelve a mover ni convertir.
"""
from __future__ import annotations

from decimal import Decimal, ROUND_DOWN
from pathlib import Path
from typing import Any
import json
import os
import time
import uuid


CUENTA_FUNDING = "FUND"
CUENTA_UTA = "UNIFIED"
CONVERT_UTA = "eb_convert_uta"
CONVERT_FUNDING = "eb_convert_funding"

_ROOT = Path(__file__).resolve().parents[1]
_RUTA_DIARIO = _ROOT / "data" / "tusk_caja_usdt_estado.json"


def _f(value: Any, default: float = 0.0) -> float:
    try:
        return float(value if value not in ("", None) else default)
    except (TypeError, ValueError):
        return default


def _ok(response: dict[str, Any] | None) -> bool:
    return isinstance(response, dict) and int(response.get("retCode") or 0) == 0


def _mensaje(response: dict[str, Any] | None) -> str:
    if not isinstance(response, dict):
        return "respuesta_invalida"
    return str(response.get("retMsg") or "")


def _cantidad_texto(value: float, decimales: int = 8) -> str:
    step = Decimal(1).scaleb(-max(0, int(decimales)))
    number = Decimal(str(max(0.0, float(value or 0)))).quantize(step, rounding=ROUND_DOWN)
    return format(number, "f").rstrip("0").rstrip(".") or "0"


def ruta_diario(path: str | Path | None = None) -> Path:
    if path:
        return Path(path)
    raw = os.getenv("TUSK_CAJA_USDT_DIARIO", "").strip()
    return Path(raw) if raw else _RUTA_DIARIO


def _diario_vacio() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "activo": "LTC",
        "paso": "idle",
        "transfer_id": None,
        "request_id": None,
        "quote_tx_id": None,
        "amount": None,
        "estado": "IDLE",
        "ultimo": {},
        "actualizado_ts": 0.0,
    }


def cargar_diario(path: str | Path | None = None) -> dict[str, Any]:
    libro = ruta_diario(path)
    if not libro.exists():
        return _diario_vacio()
    try:
        raw = json.loads(libro.read_text(encoding="utf-8"))
    except Exception:
        return _diario_vacio()
    out = _diario_vacio()
    if isinstance(raw, dict):
        out.update(raw)
    return out


def guardar_diario(estado: dict[str, Any], path: str | Path | None = None) -> dict[str, Any]:
    out = _diario_vacio()
    out.update(dict(estado or {}))
    out["actualizado_ts"] = time.time()
    path_out = ruta_diario(path)
    path_out.parent.mkdir(parents=True, exist_ok=True)
    tmp = path_out.with_suffix(path_out.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    if path_out.exists():
        path_out.unlink()
    os.rename(tmp, path_out)
    return out


def _id_estable(clave: str, seed: str) -> str:
    """UUID determinista para reintentos idempotentes del mismo paso."""
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"shadowharmy:{clave}:{seed}"))


def consultar_transferencia(session: Any, transfer_id: str) -> dict[str, Any]:
    if not transfer_id:
        return {"ok": False, "motivo": "sin_transfer_id"}
    try:
        response = session.get_internal_transfer_records(transferId=str(transfer_id))
    except Exception as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
    rows = ((response or {}).get("result") or {}).get("list") or []
    row = rows[0] if rows else {}
    status = str(row.get("status") or "").upper()
    return {
        "ok": _ok(response),
        "status": status,
        "success": status == "SUCCESS",
        "pending": status in {"PENDING", "STATUS_UNKNOWN", ""},
        "mensaje": _mensaje(response),
        "fila": row,
    }


def consultar_convert(session: Any, quote_tx_id: str, *, account_type: str = CONVERT_FUNDING) -> dict[str, Any]:
    if not quote_tx_id:
        return {"ok": False, "motivo": "sin_quote_tx_id"}
    try:
        response = session.get_convert_status(
            quoteTxId=str(quote_tx_id),
            accountType=account_type,
        )
    except Exception as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
    result = (response or {}).get("result") or {}
    status = str(result.get("exchangeStatus") or result.get("status") or "").lower()
    return {
        "ok": _ok(response),
        "status": status,
        "success": status == "success",
        "pending": status in {"init", "processing", ""},
        "mensaje": _mensaje(response),
        "resultado": result,
    }


def _balance_desde_respuesta(response: dict[str, Any] | None) -> dict[str, float]:
    """Tolera formas pybit actuales y anteriores del balance por moneda."""
    result = (response or {}).get("result") or {}
    balance = result.get("balance") or {}
    if isinstance(balance, list):
        balance = balance[0] if balance else {}
    if not isinstance(balance, dict):
        balance = {}
    wallet = _f(
        balance.get("walletBalance"),
        _f(balance.get("balance"), _f(result.get("walletBalance"))),
    )
    transferible = _f(
        balance.get("transferBalance"),
        _f(
            balance.get("transferableBalance"),
            _f(result.get("transferBalance"), wallet),
        ),
    )
    return {
        "wallet": max(0.0, wallet),
        "transferible": max(0.0, transferible),
    }


def leer_balance(session: Any, account_type: str, coin: str) -> dict[str, Any]:
    try:
        response = session.get_coin_balance(
            accountType=str(account_type).upper(),
            coin=str(coin).upper(),
        )
    except Exception as exc:
        return {
            "ok": False,
            "account_type": str(account_type).upper(),
            "coin": str(coin).upper(),
            "error": f"{type(exc).__name__}: {exc}",
            "wallet": 0.0,
            "transferible": 0.0,
        }
    amounts = _balance_desde_respuesta(response)
    return {
        "ok": _ok(response),
        "account_type": str(account_type).upper(),
        "coin": str(coin).upper(),
        "ret_code": int(response.get("retCode") or 0),
        "mensaje": _mensaje(response),
        **amounts,
    }


def inspeccionar(session: Any, activo: str = "LTC") -> dict[str, Any]:
    coin = str(activo or "LTC").upper()
    funding = leer_balance(session, CUENTA_FUNDING, coin)
    funding_usdt = leer_balance(session, CUENTA_FUNDING, "USDT")
    uta = leer_balance(session, CUENTA_UTA, coin)
    usdt = leer_balance(session, CUENTA_UTA, "USDT")
    ok = all(row.get("ok") for row in (funding, funding_usdt, uta, usdt))
    if not ok:
        siguiente = "BLOQUEADO_LECTURA"
    elif _f(funding.get("transferible")) > 0:
        siguiente = "CONVERTIR_FUNDING"
    elif _f(funding_usdt.get("transferible")) > 0:
        siguiente = "TRANSFERIR_USDT"
    else:
        siguiente = "LISTO_USDT"
    return {
        "ok": ok,
        "activo": coin,
        "funding": funding,
        "funding_usdt": funding_usdt,
        "uta_activo": uta,
        "uta_usdt": usdt,
        "siguiente": siguiente,
    }


def transferir_funding_a_uta(
    session: Any,
    *,
    activo: str = "LTC",
    amount: float | None = None,
    permitir_manos: bool = False,
    diario_path: str | Path | None = None,
) -> dict[str, Any]:
    foto = inspeccionar(session, activo)
    if not foto.get("ok"):
        return {"ok": False, "paso": "transferir", "motivo": "lectura_fallida", "foto": foto}
    disponible = _f(foto["funding_usdt"].get("transferible"))
    solicitado = disponible if amount is None else min(disponible, max(0.0, float(amount)))
    texto = _cantidad_texto(solicitado)
    if solicitado <= 0:
        return {
            "ok": True,
            "paso": "transferir",
            "omitido": True,
            "motivo": "sin_saldo_funding",
            "foto": foto,
        }
    if not permitir_manos:
        return {
            "ok": True,
            "paso": "transferir",
            "simulado": True,
            "activo": "USDT",
            "amount": texto,
            "desde": CUENTA_FUNDING,
            "hacia": CUENTA_UTA,
            "foto": foto,
        }

    diario = cargar_diario(diario_path)
    seed = f"USDT:{texto}:{foto['activo']}"
    transfer_id = str(diario.get("transfer_id") or "") or _id_estable("transfer-usdt", seed)
    if diario.get("estado") == "TRANSFER_PENDIENTE" and diario.get("transfer_id"):
        prev = consultar_transferencia(session, str(diario["transfer_id"]))
        if prev.get("success"):
            diario["estado"] = "TRANSFER_CONFIRMADO"
            diario["ultimo"] = prev
            guardar_diario(diario, diario_path)
            return {
                "ok": True,
                "paso": "transferir",
                "recuperado": True,
                "transfer_id": diario["transfer_id"],
                "consulta": prev,
            }
        if prev.get("pending"):
            return {
                "ok": False,
                "paso": "transferir",
                "motivo": "transfer_pendiente",
                "transfer_id": diario["transfer_id"],
                "consulta": prev,
            }

    diario.update({
        "activo": foto["activo"],
        "paso": "transferir",
        "transfer_id": transfer_id,
        "amount": texto,
        "estado": "TRANSFER_PENDIENTE",
    })
    guardar_diario(diario, diario_path)
    try:
        response = session.create_internal_transfer(
            transferId=transfer_id,
            coin="USDT",
            amount=texto,
            fromAccountType=CUENTA_FUNDING,
            toAccountType=CUENTA_UTA,
        )
    except Exception as exc:
        # Puede haber llegado al exchange: consultar antes de inventar otro ID.
        consulta = consultar_transferencia(session, transfer_id)
        if consulta.get("success"):
            diario["estado"] = "TRANSFER_CONFIRMADO"
            diario["ultimo"] = consulta
            guardar_diario(diario, diario_path)
            return {
                "ok": True,
                "paso": "transferir",
                "recuperado": True,
                "transfer_id": transfer_id,
                "consulta": consulta,
            }
        return {
            "ok": False,
            "paso": "transferir",
            "activo": "USDT",
            "amount": texto,
            "transfer_id": transfer_id,
            "error": f"{type(exc).__name__}: {exc}",
            "consulta": consulta,
        }
    consulta = consultar_transferencia(session, transfer_id)
    ok = _ok(response) or bool(consulta.get("success"))
    diario["estado"] = "TRANSFER_CONFIRMADO" if consulta.get("success") else (
        "TRANSFER_PENDIENTE" if consulta.get("pending") else "TRANSFER_FALLIDO"
    )
    diario["ultimo"] = {"respuesta": response, "consulta": consulta}
    guardar_diario(diario, diario_path)
    return {
        "ok": ok,
        "paso": "transferir",
        "activo": "USDT",
        "amount": texto,
        "transfer_id": transfer_id,
        "mensaje": _mensaje(response),
        "consulta": consulta,
        "resultado": (response.get("result") or {}) if isinstance(response, dict) else {},
    }


def _fila_convert(response: dict[str, Any] | None, coin: str) -> dict[str, Any] | None:
    rows = ((response or {}).get("result") or {}).get("coins") or []
    target = str(coin).upper()
    return next((row for row in rows if str(row.get("coin") or "").upper() == target), None)


def limites_convert(
    session: Any,
    activo: str = "LTC",
    *,
    account_type: str = CONVERT_FUNDING,
) -> dict[str, Any]:
    coin = str(activo or "LTC").upper()
    try:
        response = session.get_convert_coin_list(
            accountType=account_type,
            side=0,
        )
    except Exception as exc:
        return {"ok": False, "activo": coin, "error": f"{type(exc).__name__}: {exc}"}
    row = _fila_convert(response, coin)
    if not _ok(response) or not row:
        return {
            "ok": False,
            "activo": coin,
            "mensaje": _mensaje(response),
            "motivo": "activo_no_convertible",
        }
    return {
        "ok": not bool(row.get("disableFrom")),
        "activo": coin,
        "account_type": account_type,
        "balance": _f(row.get("balance")),
        "u_balance": _f(row.get("uBalance")),
        "min": _f(row.get("singleFromMinLimit")),
        "max": _f(row.get("singleFromMaxLimit")),
        "precision": int(row.get("accuracyLength") or 8),
        "disable_from": bool(row.get("disableFrom")),
    }


def _spot_last(session: Any, activo: str) -> float:
    try:
        response = session.get_tickers(category="spot", symbol=f"{str(activo).upper()}USDT")
        rows = ((response or {}).get("result") or {}).get("list") or []
        return _f((rows[0] if rows else {}).get("lastPrice"))
    except Exception:
        return 0.0


def evaluar_quote(
    quote: dict[str, Any],
    *,
    spot_last: float,
    max_peaje_pct: float,
    ahora_ms: int | None = None,
) -> dict[str, Any]:
    result = (quote or {}).get("result") or {}
    from_amount = _f(result.get("fromAmount"))
    to_amount = _f(result.get("toAmount"))
    rate = to_amount / from_amount if from_amount > 0 else _f(result.get("exchangeRate"))
    spot = _f(spot_last)
    peaje = ((spot - rate) / spot * 100.0) if spot > 0 and rate > 0 else None
    expiry = int(_f(result.get("expiredTime")))
    now = int(ahora_ms if ahora_ms is not None else time.time() * 1000)
    vigente = expiry <= 0 or expiry > now
    peaje_ok = peaje is not None and peaje <= float(max_peaje_pct)
    return {
        "ok": _ok(quote) and bool(result.get("quoteTxId")) and vigente and peaje_ok,
        "quote_tx_id": str(result.get("quoteTxId") or ""),
        "from_amount": from_amount,
        "to_amount": to_amount,
        "exchange_rate": rate,
        "spot_last": spot,
        "peaje_pct": peaje,
        "max_peaje_pct": float(max_peaje_pct),
        "vigente": vigente,
        "expired_time": expiry,
        "mensaje": _mensaje(quote),
    }


def convertir_funding_a_usdt(
    session: Any,
    *,
    activo: str = "LTC",
    amount: float | None = None,
    max_peaje_pct: float = 0.75,
    permitir_manos: bool = False,
    diario_path: str | Path | None = None,
) -> dict[str, Any]:
    coin = str(activo or "LTC").upper()
    foto = inspeccionar(session, coin)
    if not foto.get("ok"):
        return {"ok": False, "paso": "convertir", "motivo": "lectura_fallida", "foto": foto}
    disponible = _f(foto["funding"].get("transferible"))
    limits = limites_convert(session, coin, account_type=CONVERT_FUNDING)
    if not limits.get("ok"):
        return {"ok": False, "paso": "convertir", "motivo": "convert_no_disponible", "limites": limits}
    solicitado = disponible if amount is None else min(disponible, max(0.0, float(amount)))
    solicitado = min(solicitado, _f(limits.get("max"), solicitado) or solicitado)
    texto = _cantidad_texto(solicitado, int(limits.get("precision") or 8))
    if solicitado <= 0:
        return {
            "ok": True,
            "paso": "convertir",
            "omitido": True,
            "motivo": "sin_saldo_funding",
            "foto": foto,
        }
    if solicitado < _f(limits.get("min")):
        return {
            "ok": False,
            "paso": "convertir",
            "motivo": "debajo_minimo_convert",
            "amount": texto,
            "limites": limits,
        }
    if not permitir_manos:
        return {
            "ok": True,
            "paso": "convertir",
            "simulado": True,
            "activo": coin,
            "hacia": "USDT",
            "cuenta": CUENTA_FUNDING,
            "amount": texto,
            "limites": limits,
            "foto": foto,
        }

    diario = cargar_diario(diario_path)
    if diario.get("estado") == "CONVERT_PENDIENTE" and diario.get("quote_tx_id"):
        prev = consultar_convert(session, str(diario["quote_tx_id"]))
        if prev.get("success"):
            diario["estado"] = "CONVERT_CONFIRMADO"
            diario["ultimo"] = prev
            guardar_diario(diario, diario_path)
            return {
                "ok": True,
                "paso": "convertir",
                "recuperado": True,
                "quote_tx_id": diario["quote_tx_id"],
                "consulta": prev,
            }
        if prev.get("pending"):
            return {
                "ok": False,
                "paso": "convertir",
                "motivo": "convert_pendiente",
                "quote_tx_id": diario["quote_tx_id"],
                "consulta": prev,
            }

    request_id = str(diario.get("request_id") or "") or _id_estable(
        "convert-ltc", f"{coin}:{texto}"
    )
    diario.update({
        "activo": coin,
        "paso": "convertir",
        "request_id": request_id,
        "amount": texto,
        "estado": "COTIZADO",
        "quote_tx_id": None,
    })
    guardar_diario(diario, diario_path)
    try:
        quote = session.request_a_quote(
            accountType=CONVERT_FUNDING,
            fromCoin=coin,
            toCoin="USDT",
            requestCoin=coin,
            requestAmount=texto,
            requestId=request_id,
        )
    except Exception as exc:
        return {
            "ok": False,
            "paso": "convertir",
            "motivo": "quote_fallida",
            "request_id": request_id,
            "error": f"{type(exc).__name__}: {exc}",
        }
    juicio = evaluar_quote(
        quote,
        spot_last=_spot_last(session, coin),
        max_peaje_pct=max_peaje_pct,
    )
    if not juicio.get("ok"):
        return {
            "ok": False,
            "paso": "convertir",
            "motivo": "quote_rechazada",
            "juicio": juicio,
            "request_id": request_id,
        }
    diario["quote_tx_id"] = juicio["quote_tx_id"]
    diario["estado"] = "CONVERT_PENDIENTE"
    guardar_diario(diario, diario_path)
    try:
        response = session.confirm_a_quote(quoteTxId=juicio["quote_tx_id"])
    except Exception as exc:
        consulta = consultar_convert(session, juicio["quote_tx_id"])
        if consulta.get("success"):
            diario["estado"] = "CONVERT_CONFIRMADO"
            diario["ultimo"] = consulta
            guardar_diario(diario, diario_path)
            return {
                "ok": True,
                "paso": "convertir",
                "recuperado": True,
                "juicio": juicio,
                "consulta": consulta,
            }
        return {
            "ok": False,
            "paso": "convertir",
            "motivo": "confirmacion_fallida",
            "juicio": juicio,
            "error": f"{type(exc).__name__}: {exc}",
            "consulta": consulta,
        }
    consulta = consultar_convert(session, juicio["quote_tx_id"])
    ok = _ok(response) or bool(consulta.get("success"))
    if consulta.get("success"):
        diario["estado"] = "CONVERT_CONFIRMADO"
    elif consulta.get("pending") or str(
        ((response or {}).get("result") or {}).get("exchangeStatus") or ""
    ).lower() in {"init", "processing"}:
        diario["estado"] = "CONVERT_PENDIENTE"
        ok = False
    else:
        diario["estado"] = "CONVERT_FALLIDO" if not ok else "CONVERT_CONFIRMADO"
    diario["ultimo"] = {"respuesta": response, "consulta": consulta, "juicio": juicio}
    guardar_diario(diario, diario_path)
    return {
        "ok": ok and diario["estado"] == "CONVERT_CONFIRMADO",
        "paso": "convertir",
        "activo": coin,
        "amount": texto,
        "juicio": juicio,
        "mensaje": _mensaje(response),
        "consulta": consulta,
        "resultado": (response.get("result") or {}) if isinstance(response, dict) else {},
    }


def ejecutar_paso(
    session: Any,
    paso: str,
    *,
    activo: str = "LTC",
    amount: float | None = None,
    max_peaje_pct: float = 0.75,
    permitir_manos: bool = False,
    diario_path: str | Path | None = None,
) -> dict[str, Any]:
    step = str(paso or "inspeccionar").strip().lower()
    if step in {"inspeccionar", "verificar"}:
        return inspeccionar(session, activo)
    if step == "transferir":
        return transferir_funding_a_uta(
            session,
            activo=activo,
            amount=amount,
            permitir_manos=permitir_manos,
            diario_path=diario_path,
        )
    if step == "convertir":
        return convertir_funding_a_usdt(
            session,
            activo=activo,
            amount=amount,
            max_peaje_pct=max_peaje_pct,
            permitir_manos=permitir_manos,
            diario_path=diario_path,
        )
    if step == "auto":
        foto = inspeccionar(session, activo)
        siguiente = str(foto.get("siguiente") or "")
        if siguiente == "CONVERTIR_FUNDING":
            return convertir_funding_a_usdt(
                session,
                activo=activo,
                amount=amount,
                max_peaje_pct=max_peaje_pct,
                permitir_manos=permitir_manos,
                diario_path=diario_path,
            )
        if siguiente == "TRANSFERIR_USDT":
            return transferir_funding_a_uta(
                session,
                activo=activo,
                amount=amount,
                permitir_manos=permitir_manos,
                diario_path=diario_path,
            )
        return foto
    return {"ok": False, "paso": step, "motivo": "paso_desconocido"}
