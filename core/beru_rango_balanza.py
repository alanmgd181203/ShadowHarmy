"""Balanza de la legión — peso LONG vs SHORT (sin BTC).

Oído del Monarca. Fuente primaria = posiciones reales OKX (no sellos locales).
Los sellos ``manos_piedra_informe`` parpadean vacío en reconciliación Tusk y
hacían saltar el short (p.ej. 0.7k ↔ 1.4k) sin que la bolsa se moviera.
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from core import beru_rango_paths

EXCLUIR_BASES = frozenset({"BTC", "BTCUSDT", "BTCPERP"})


def _f(x: Any, default: float = 0.0) -> float:
    try:
        return float(x)
    except (TypeError, ValueError):
        return default


def _es_bolsa(activo: str) -> bool:
    """La casa de las acciones. No entra en el manto de las monedas."""
    try:
        from cirugias.escudo_dual.bolsa import es_cazador

        return es_cazador(activo)
    except Exception:
        return False


def _excluir(activo: str) -> bool:
    a = str(activo or "").strip().upper()
    if not a:
        return True
    if a in EXCLUIR_BASES:
        return True
    if a.startswith("BTC"):
        return True
    return False


def _lado_norm(lado: Any) -> str:
    s = str(lado or "").strip().upper()
    if s in ("LONG", "BUY", "L"):
        return "LONG"
    if s in ("SHORT", "SELL", "S"):
        return "SHORT"
    return ""


def medir_desde_okx() -> dict[str, Any]:
    """Suma notionalUsd de SWAP USDT en la cuenta (verdad de casa)."""
    from core import okx_rest

    now = time.time()
    long_usd = 0.0
    short_usd = 0.0
    n_long = 0
    n_short = 0
    por_santo: list[dict[str, Any]] = []
    excluidos: list[str] = []

    rows = okx_rest.get_private("/api/v5/account/positions", params={"instType": "SWAP"})
    for r in rows or []:
        if not isinstance(r, dict):
            continue
        inst = str(r.get("instId") or "")
        if not inst.endswith("-USDT-SWAP"):
            continue
        act = inst.split("-")[0].upper()
        if _excluir(act) or _es_bolsa(act):
            excluidos.append(act)
            continue
        pos = _f(r.get("pos"))
        if abs(pos) <= 1e-12:
            continue
        nu = abs(_f(r.get("notionalUsd")))
        if nu <= 1e-12:
            px = _f(r.get("markPx") or r.get("last") or r.get("avgPx"))
            if px > 0:
                # fallback: contratos * ctVal * px si hace falta
                try:
                    from core import lote_okx

                    ct = _f(lote_okx.filtros_lote(f"{act}USDT_LINEAL").get("ctVal"), 1.0)
                    nu = abs(pos) * ct * px
                except Exception:
                    nu = abs(pos) * px
        if nu <= 1e-12:
            continue
        pos_side = str(r.get("posSide") or "net").lower()
        if pos_side == "long" or (pos_side == "net" and pos > 0):
            long_usd += nu
            n_long += 1
            por_santo.append({"activo": act, "long": round(nu, 4), "short": 0.0})
        else:
            short_usd += nu
            n_short += 1
            por_santo.append({"activo": act, "long": 0.0, "short": round(nu, 4)})

    total = long_usd + short_usd
    pct_l = (100.0 * long_usd / total) if total > 1e-12 else 0.0
    pct_s = (100.0 * short_usd / total) if total > 1e-12 else 0.0
    frase = (
        f"L ${long_usd:.0f} ({pct_l:.0f}%) · S ${short_usd:.0f} ({pct_s:.0f}%) · "
        f"{n_long}L / {n_short}S · sin BTC · casa OKX"
    )
    return {
        "ts": now,
        "fuente": "okx_positions",
        "excluye": sorted(EXCLUIR_BASES),
        "excluidos_vistos": sorted(set(excluidos)),
        "n_informes": 0,
        "n_frescos": len(por_santo),
        "max_age_s": 0.0,
        "long_usd": round(long_usd, 2),
        "short_usd": round(short_usd, 2),
        "total_usd": round(total, 2),
        "net_long_usd": round(long_usd - short_usd, 2),
        "pct_long": round(pct_l, 1),
        "pct_short": round(pct_s, 1),
        "n_long": n_long,
        "n_short": n_short,
        "n_santos_con_pos": len(por_santo),
        "frase": frase,
        "por_santo": sorted(por_santo, key=lambda r: -(r["long"] + r["short"])),
    }


def medir_desde_informes(
    *,
    root: Path | None = None,
    max_age_s: float = 600.0,
) -> dict[str, Any]:
    """LEGADO / respaldo: suma sellos locales (puede parpadear)."""
    base = root or beru_rango_paths.RANGO_DIR
    now = time.time()
    long_usd = 0.0
    short_usd = 0.0
    n_long = 0
    n_short = 0
    n_santos_con_pos = 0
    n_informes = 0
    n_frescos = 0
    excluidos: list[str] = []
    por_santo: list[dict[str, Any]] = []

    for path in sorted(base.glob("*/manos_piedra_informe.json")):
        n_informes += 1
        activo = path.parent.name.upper()
        if _excluir(activo) or _es_bolsa(activo):
            excluidos.append(activo)
            continue
        age = now - path.stat().st_mtime
        if age > max_age_s:
            continue
        n_frescos += 1
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        pos = data.get("posicion") or []
        if not isinstance(pos, list) or not pos:
            continue
        l_s = 0.0
        s_s = 0.0
        for p in pos:
            if not isinstance(p, dict):
                continue
            lado = _lado_norm(p.get("lado") or p.get("side"))
            masa = _f(p.get("masa_usd"))
            if masa <= 0:
                qty = abs(_f(p.get("qty")))
                px = _f(p.get("precio") or p.get("avgPx") or p.get("avg_px"))
                masa = qty * px if qty > 0 and px > 0 else 0.0
            if masa <= 1e-12 or not lado:
                continue
            if lado == "LONG":
                l_s += masa
            else:
                s_s += masa
        if l_s <= 1e-12 and s_s <= 1e-12:
            continue
        n_santos_con_pos += 1
        if l_s > 1e-12:
            long_usd += l_s
            n_long += 1
        if s_s > 1e-12:
            short_usd += s_s
            n_short += 1
        por_santo.append(
            {
                "activo": activo,
                "long": round(l_s, 4),
                "short": round(s_s, 4),
                "age_s": round(age, 1),
            }
        )

    total = long_usd + short_usd
    pct_l = (100.0 * long_usd / total) if total > 1e-12 else 0.0
    pct_s = (100.0 * short_usd / total) if total > 1e-12 else 0.0
    frase = (
        f"L ${long_usd:.0f} ({pct_l:.0f}%) · S ${short_usd:.0f} ({pct_s:.0f}%) · "
        f"{n_long}L / {n_short}S · sin BTC · sellos"
    )
    return {
        "ts": now,
        "fuente": "manos_piedra_informe",
        "excluye": sorted(EXCLUIR_BASES),
        "excluidos_vistos": excluidos,
        "n_informes": n_informes,
        "n_frescos": n_frescos,
        "max_age_s": max_age_s,
        "long_usd": round(long_usd, 2),
        "short_usd": round(short_usd, 2),
        "total_usd": round(total, 2),
        "net_long_usd": round(long_usd - short_usd, 2),
        "pct_long": round(pct_l, 1),
        "pct_short": round(pct_s, 1),
        "n_long": n_long,
        "n_short": n_short,
        "n_santos_con_pos": n_santos_con_pos,
        "frase": frase,
        "por_santo": sorted(por_santo, key=lambda r: -(r["long"] + r["short"])),
    }


_ULTIMA_CASA: dict[str, Any] | None = None


def _guardar_eco_casa(snap: dict[str, Any]) -> None:
    global _ULTIMA_CASA
    if str(snap.get("fuente") or "") != "okx_positions":
        return
    _ULTIMA_CASA = {
        k: v
        for k, v in snap.items()
        if k != "por_santo"
    }
    _ULTIMA_CASA["por_santo"] = list(snap.get("por_santo") or [])
    _ULTIMA_CASA["ts_eco"] = float(snap.get("ts") or time.time())


def _leer_eco_casa(*, motivo: str = "") -> dict[str, Any] | None:
    """Última lectura OKX buena (memoria o disco). No usa sellos parpadeantes."""
    global _ULTIMA_CASA
    now = time.time()
    if _ULTIMA_CASA and str(_ULTIMA_CASA.get("fuente") or "") == "okx_positions":
        eco = dict(_ULTIMA_CASA)
        age = now - float(eco.get("ts_eco") or eco.get("ts") or now)
        eco["fuente"] = "okx_eco"
        eco["eco_age_s"] = round(age, 1)
        eco["aviso"] = motivo or "okx_temporal"
        eco["frase"] = (
            f"L ${float(eco.get('long_usd') or 0):.0f} "
            f"({float(eco.get('pct_long') or 0):.0f}%) · "
            f"S ${float(eco.get('short_usd') or 0):.0f} "
            f"({float(eco.get('pct_short') or 0):.0f}%) · "
            f"{int(eco.get('n_long') or 0)}L / {int(eco.get('n_short') or 0)}S · "
            f"sin BTC · eco OKX {age:.0f}s"
        )
        return eco
    # disco
    try:
        path = beru_rango_paths.balanza_legion()
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            if str(data.get("fuente") or "") in ("okx_positions", "okx_eco"):
                data["fuente"] = "okx_eco"
                age = now - float(data.get("ts") or now)
                data["eco_age_s"] = round(age, 1)
                data["aviso"] = motivo or "okx_temporal"
                data["frase"] = (
                    f"L ${float(data.get('long_usd') or 0):.0f} "
                    f"({float(data.get('pct_long') or 0):.0f}%) · "
                    f"S ${float(data.get('short_usd') or 0):.0f} "
                    f"({float(data.get('pct_short') or 0):.0f}%) · "
                    f"{int(data.get('n_long') or 0)}L / {int(data.get('n_short') or 0)}S · "
                    f"sin BTC · eco OKX {age:.0f}s"
                )
                data["por_santo"] = list(data.get("top") or [])
                return data
    except Exception:
        pass
    return None


def medir_desde_okx_con_reintento() -> dict[str, Any]:
    """OKX con un reintento corto ante 429 / red."""
    from core import okx_rest

    ultimo: Exception | None = None
    for i in range(2):
        try:
            return medir_desde_okx()
        except Exception as exc:
            ultimo = exc
            msg = str(exc)
            if i == 0 and ("429" in msg or "50011" in msg or "Too Many" in msg):
                time.sleep(1.6)
                continue
            break
    assert ultimo is not None
    raise ultimo


def medir_balanza(*, max_age_s: float = 600.0) -> dict[str, Any]:
    """Casa OKX. Si OKX falla: eco de la última casa buena (NUNCA sellos parpadeantes)."""
    _ = max_age_s
    try:
        from core import okx_rest

        if not okx_rest.credenciales_ok():
            raise RuntimeError("sin_credenciales_okx")
        snap = medir_desde_okx_con_reintento()
        _guardar_eco_casa(snap)
        return snap
    except Exception as exc:
        eco = _leer_eco_casa(motivo=f"okx_fallo:{exc}")
        if eco:
            return eco
        # Solo si nunca hubo casa: sellos con aviso grueso (mejor que cero).
        snap = medir_desde_informes(max_age_s=max_age_s)
        snap["aviso"] = f"okx_fallo_sin_eco:{exc}"
        snap["frase"] = (snap.get("frase") or "") + " · AVISO sellos inestables"
        return snap


def medir_bolsa() -> dict[str, Any]:
    """Solo la casa de las acciones. El metal del escudo no entra en la suma."""
    from core import okx_rest

    if not okx_rest.credenciales_ok():
        raise RuntimeError("sin_credenciales_okx")
    now = time.time()
    long_usd = 0.0
    short_usd = 0.0
    n_long = 0
    n_short = 0
    por_santo: list[dict[str, Any]] = []
    rows = okx_rest.get_private("/api/v5/account/positions", params={"instType": "SWAP"})
    for r in rows or []:
        if not isinstance(r, dict):
            continue
        inst = str(r.get("instId") or "")
        if not inst.endswith("-USDT-SWAP"):
            continue
        act = inst.split("-")[0].upper()
        if act in ("US100", "US500") or not _es_bolsa(act):
            continue
        pos = _f(r.get("pos"))
        if abs(pos) <= 1e-12:
            continue
        nu = abs(_f(r.get("notionalUsd")))
        if nu <= 1e-12:
            px = _f(r.get("markPx") or r.get("last") or r.get("avgPx"))
            nu = abs(pos) * px if px > 0 else 0.0
        if nu <= 1e-12:
            continue
        pos_side = str(r.get("posSide") or "net").lower()
        if pos_side == "long" or (pos_side == "net" and pos > 0):
            long_usd += nu
            n_long += 1
            por_santo.append({"activo": act, "long": round(nu, 4), "short": 0.0})
        else:
            short_usd += nu
            n_short += 1
            por_santo.append({"activo": act, "long": 0.0, "short": round(nu, 4)})
    total = long_usd + short_usd
    return {
        "ts": now,
        "fuente": "okx_bolsa",
        "long_usd": round(long_usd, 2),
        "short_usd": round(short_usd, 2),
        "total_usd": round(total, 2),
        "n_long": n_long,
        "n_short": n_short,
        "n_santos_con_pos": n_long + n_short,
        "por_santo": por_santo,
        "frase": f"bolsa L ${long_usd:.0f} · S ${short_usd:.0f}",
    }


def sellar_balanza_bolsa(*, out: Path | None = None) -> dict[str, Any]:
    """Sello aparte. No pisa la balanza de las monedas."""
    snap = medir_bolsa()
    path = out or (beru_rango_paths.RANGO_DIR / "balanza_bolsa.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snap, ensure_ascii=False, indent=2), encoding="utf-8")
    snap["path"] = str(path)
    return snap


def sellar_balanza(
    *,
    root: Path | None = None,
    max_age_s: float = 600.0,
    out: Path | None = None,
) -> dict[str, Any]:
    """Mide y escribe ``data/beru/rango/balanza_legion.json``."""
    _ = root  # OKX no usa root; se conserva firma
    snap = medir_balanza(max_age_s=max_age_s)
    path = out or beru_rango_paths.balanza_legion()
    path.parent.mkdir(parents=True, exist_ok=True)
    slim = {k: v for k, v in snap.items() if k != "por_santo"}
    slim["top"] = (snap.get("por_santo") or [])[:12]
    # No pisar un sello OKX bueno con un eco vacío raro: si eco, sí escribir (misma cifra).
    path.write_text(json.dumps(slim, ensure_ascii=False, indent=2), encoding="utf-8")
    snap["path"] = str(path)
    return snap
