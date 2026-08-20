"""Bóveda del Coliseo — velas (1m o 1s) en SQLite (Gran Consumo Jess).

Mercados: spot (gráficas / teatro) + linear + inverse (pares manto Igris).
Cada mercado×intervalo tiene su sqlite bajo data/coliseo/.
Bybit: interval "1" = 1 minuto · "1s" = 1 segundo (linear/inverse; spot suele no soportar 1s).
"""
from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
COLISEO_DIR = ROOT / "data" / "coliseo"

# Intervalo activo de la sesión (1 | 1s). Lo setea el ritual de noche.
_INTERVAL: str = "1"

MARKETS = ("spot", "linear", "inverse")


def set_interval(interval: str) -> str:
    """Activa 1 (minuto) o 1s (segundo) para rutas de bóveda/checkpoint."""
    global _INTERVAL
    raw = (interval or "1").strip().lower()
    if raw in ("1s", "s", "1sec", "segundo", "segundos"):
        _INTERVAL = "1s"
    else:
        _INTERVAL = "1"
    return _INTERVAL


def get_interval() -> str:
    return _INTERVAL


def interval_label() -> str:
    return "1s" if _INTERVAL == "1s" else "1m"


def boveda_path(market: str = "spot") -> Path:
    m = (market or "spot").strip().lower()
    suf = "1s" if _INTERVAL == "1s" else "1m"
    if m not in MARKETS:
        raise ValueError(f"mercado desconocido: {market}")
    return COLISEO_DIR / f"boveda_{m}_{suf}.sqlite"


# Compat paths antiguos (1m)
BOVEDA_PATH = COLISEO_DIR / "boveda_spot_1m.sqlite"
BOVEDA_LINEAR_PATH = COLISEO_DIR / "boveda_linear_1m.sqlite"
BOVEDA_INVERSE_PATH = COLISEO_DIR / "boveda_inverse_1m.sqlite"
PROGRESO_PATH = COLISEO_DIR / "PROGRESO.md"


def checkpoint_path() -> Path:
    suf = "1s" if _INTERVAL == "1s" else "1m"
    return COLISEO_DIR / f"checkpoint_{suf}.json"


CHECKPOINT_PATH = COLISEO_DIR / "checkpoint.json"  # legacy 1m alias
HEARTBEAT_PATH = COLISEO_DIR / "heartbeat.json"


def ck_key(base: str, market: str = "spot") -> str:
    """Clave de checkpoint: BASE@spot | BASE@linear | BASE@inverse."""
    return f"{str(base).upper()}@{(market or 'spot').strip().lower()}"


def ensure_dirs() -> None:
    COLISEO_DIR.mkdir(parents=True, exist_ok=True)


def connect(db_path: Path | None = None) -> sqlite3.Connection:
    ensure_dirs()
    path = db_path or boveda_path("spot")
    con = sqlite3.connect(str(path))
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA synchronous=NORMAL")
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS candles (
            base TEXT NOT NULL,
            ts INTEGER NOT NULL,
            open REAL NOT NULL,
            high REAL NOT NULL,
            low REAL NOT NULL,
            close REAL NOT NULL,
            PRIMARY KEY (base, ts)
        )
        """
    )
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS ingest_meta (
            base TEXT PRIMARY KEY,
            symbol TEXT,
            last_ts INTEGER,
            rows INTEGER,
            status TEXT,
            updated_ts REAL
        )
        """
    )
    return con


def connect_market(market: str = "spot") -> sqlite3.Connection:
    return connect(boveda_path(market))


def load_checkpoint() -> dict[str, Any]:
    ensure_dirs()
    path = checkpoint_path()
    # Legacy: checkpoint.json era 1m
    if not path.exists() and _INTERVAL == "1" and CHECKPOINT_PATH.exists():
        path = CHECKPOINT_PATH
    if not path.exists():
        return {"bases": {}, "fase": "ingest", "interval": _INTERVAL, "updated_ts": 0}
    data = json.loads(path.read_text(encoding="utf-8"))
    data.setdefault("interval", _INTERVAL)
    return data


def save_checkpoint(data: dict[str, Any]) -> None:
    ensure_dirs()
    data["updated_ts"] = time.time()
    data["interval"] = _INTERVAL
    checkpoint_path().write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    # Mantener alias legacy en 1m
    if _INTERVAL == "1":
        CHECKPOINT_PATH.write_text(
            json.dumps(data, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )


def write_heartbeat(*, fase: str, detalle: str, ok: bool = True) -> None:
    ensure_dirs()
    payload = {
        "ts": time.time(),
        "ts_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "fase": fase,
        "detalle": detalle[:400],
        "ok": ok,
        "interval": _INTERVAL,
    }
    HEARTBEAT_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def write_progreso(lines: Iterable[str]) -> None:
    ensure_dirs()
    body = "\n".join(lines) + "\n"
    PROGRESO_PATH.write_text(body, encoding="utf-8")


def upsert_candles(
    con: sqlite3.Connection,
    base: str,
    rows: list[tuple[int, float, float, float, float]],
) -> int:
    if not rows:
        return 0
    con.executemany(
        """
        INSERT OR REPLACE INTO candles(base, ts, open, high, low, close)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        [(base.upper(), ts, o, h, l, c) for ts, o, h, l, c in rows],
    )
    return len(rows)


def set_ingest_meta(
    con: sqlite3.Connection,
    base: str,
    *,
    symbol: str,
    last_ts: int,
    rows: int,
    status: str,
) -> None:
    con.execute(
        """
        INSERT INTO ingest_meta(base, symbol, last_ts, rows, status, updated_ts)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(base) DO UPDATE SET
            symbol=excluded.symbol,
            last_ts=excluded.last_ts,
            rows=excluded.rows,
            status=excluded.status,
            updated_ts=excluded.updated_ts
        """,
        (base.upper(), symbol, last_ts, rows, status, time.time()),
    )


def count_candles(con: sqlite3.Connection, base: str | None = None) -> int:
    if base:
        row = con.execute(
            "SELECT COUNT(*) FROM candles WHERE base=?", (base.upper(),)
        ).fetchone()
    else:
        row = con.execute("SELECT COUNT(*) FROM candles").fetchone()
    return int(row[0] if row else 0)


def max_ts(con: sqlite3.Connection, base: str) -> int | None:
    row = con.execute(
        "SELECT MAX(ts) FROM candles WHERE base=?", (base.upper(),)
    ).fetchone()
    if not row or row[0] is None:
        return None
    return int(row[0])


def load_candles(
    con: sqlite3.Connection,
    base: str,
    *,
    since_ts: int | None = None,
    until_ts: int | None = None,
) -> list[tuple[int, float, float, float, float]]:
    q = "SELECT ts, open, high, low, close FROM candles WHERE base=?"
    args: list[Any] = [base.upper()]
    if since_ts is not None:
        q += " AND ts>=?"
        args.append(int(since_ts))
    if until_ts is not None:
        q += " AND ts<=?"
        args.append(int(until_ts))
    q += " ORDER BY ts ASC"
    return [(int(r[0]), float(r[1]), float(r[2]), float(r[3]), float(r[4])) for r in con.execute(q, args)]
