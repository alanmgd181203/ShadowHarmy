"""Cliente REST OKX v5 — firma y transporte (Beru / manos)."""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

import core.config as config


class OkxRestError(RuntimeError):
  def __init__(self, code: str, msg: str, *, data: Any = None):
    super().__init__(f"OKX {code}: {msg}")
    self.code = str(code)
    self.msg = str(msg)
    self.data = data


def _base_url() -> str:
  flag = str(getattr(config, "OKX_FLAG", "0") or "0").strip()
  if flag == "1":
    return "https://www.okx.com"
  return "https://www.okx.com"


def _credenciales() -> tuple[str, str, str]:
  key = str(getattr(config, "OKX_API_KEY", "") or "")
  secret = str(getattr(config, "OKX_API_SECRET", "") or "")
  phrase = str(getattr(config, "OKX_PASSPHRASE", "") or "")
  return key, secret, phrase


def credenciales_ok() -> bool:
  k, s, p = _credenciales()
  return bool(k and s and p)


def _sign(secret: str, ts: str, method: str, path: str, body: str) -> str:
  msg = f"{ts}{method.upper()}{path}{body}"
  mac = hmac.new(secret.encode("utf-8"), msg.encode("utf-8"), hashlib.sha256)
  return base64.b64encode(mac.digest()).decode("utf-8")


def _request(
  method: str,
  path: str,
  *,
  params: dict[str, Any] | None = None,
  body: dict[str, Any] | list[Any] | None = None,
  auth: bool = False,
  timeout: float = 15.0,
) -> Any:
  query = ""
  if params:
    query = "?" + urllib.parse.urlencode(
      {k: str(v) for k, v in params.items() if v is not None}
    )
  url = f"{_base_url()}{path}{query}"
  payload = ""
  headers = {
    "User-Agent": "ShadowHarmy/beru-okx",
    "Content-Type": "application/json",
  }
  if auth:
    key, secret, phrase = _credenciales()
    if not (key and secret and phrase):
      raise OkxRestError("0", "Sin credenciales OKX")
    ts = time.strftime("%Y-%m-%dT%H:%M:%S.", time.gmtime()) + f"{int(time.time() * 1000) % 1000:03d}Z"
    if body:
      payload = json.dumps(body, separators=(",", ":"))
    sign_path = f"{path}{query}"
    headers.update({
      "OK-ACCESS-KEY": key,
      "OK-ACCESS-SIGN": _sign(secret, ts, method, sign_path, payload),
      "OK-ACCESS-TIMESTAMP": ts,
      "OK-ACCESS-PASSPHRASE": phrase,
    })
    if str(getattr(config, "OKX_FLAG", "0") or "0") == "1":
      headers["x-simulated-trading"] = "1"
  data = payload.encode("utf-8") if payload else None
  req = urllib.request.Request(url, data=data, headers=headers, method=method.upper())
  try:
    with urllib.request.urlopen(req, timeout=timeout) as resp:
      raw = resp.read().decode("utf-8", errors="replace")
  except urllib.error.HTTPError as exc:
    raw = exc.read().decode("utf-8", errors="replace")
    try:
      parsed = json.loads(raw or "{}")
    except json.JSONDecodeError:
      raise OkxRestError(str(exc.code), raw or str(exc)) from exc
    code = str(parsed.get("code") or exc.code)
    msg = str(parsed.get("msg") or raw)
    raise OkxRestError(code, msg, data=parsed.get("data")) from exc
  except (urllib.error.URLError, TimeoutError, OSError) as exc:
    raise OkxRestError("NET", str(exc)) from exc
  try:
    parsed = json.loads(raw or "{}")
  except json.JSONDecodeError as exc:
    raise OkxRestError("JSON", raw[:200]) from exc
  code = str(parsed.get("code") or "")
  if code not in ("0", ""):
    raise OkxRestError(code, str(parsed.get("msg") or "?"), data=parsed.get("data"))
  return parsed.get("data")


def get_public(path: str, *, params: dict[str, Any] | None = None) -> Any:
  return _request("GET", path, params=params, auth=False)


def get_private(path: str, *, params: dict[str, Any] | None = None) -> Any:
  return _request("GET", path, params=params, auth=True)


def post_private(path: str, body: dict[str, Any] | list[Any]) -> Any:
  return _request("POST", path, body=body, auth=True)


def instruments(inst_type: str) -> list[dict[str, Any]]:
  data = get_public("/api/v5/public/instruments", params={"instType": inst_type})
  return list(data or [])


def instruments_swap() -> list[dict[str, Any]]:
  return instruments("SWAP")


def tickers(inst_type: str) -> list[dict[str, Any]]:
  data = get_public("/api/v5/market/tickers", params={"instType": inst_type})
  return list(data or [])


def ticker_swap(inst_id: str) -> dict[str, Any]:
  data = get_public(
    "/api/v5/market/ticker",
    params={"instId": inst_id},
  )
  rows = list(data or [])
  return rows[0] if rows else {}


def tickers_swap_usdt() -> list[dict[str, Any]]:
  return [r for r in tickers("SWAP") if str(r.get("instId") or "").endswith("-USDT-SWAP")]


def order_book(inst_id: str, *, sz: int = 50) -> tuple[list[list[float]], list[list[float]]]:
  """Libro OKX → bids/asks como [[precio, qty_base], ...] usando ctVal del catálogo."""
  from core import lote_okx

  data = get_public("/api/v5/market/books", params={"instId": inst_id, "sz": str(int(sz))})
  row = (list(data or []) or [{}])[0]
  base = str(inst_id or "").split("-")[0].upper()
  frente = f"{base}USDT_LINEAL"
  ct = float(lote_okx.filtros_lote(frente).get("ctVal") or 1.0)

  def _conv(side: list) -> list[list[float]]:
    out: list[list[float]] = []
    for lvl in side or []:
      try:
        p = float(lvl[0])
        sz_c = float(lvl[1])
      except (IndexError, TypeError, ValueError):
        continue
      if p > 0 and sz_c > 0:
        out.append([p, sz_c * ct])
    return out

  return _conv(row.get("bids") or []), _conv(row.get("asks") or [])
