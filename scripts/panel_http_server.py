#!/usr/bin/env python3
"""HTTP del Pergamino — sirve el repo + POST marcha vía pase_director.guardar_marcha.

Sustituye `python -m http.server` para que el altar pueda guardar el ritmo
sin Vite. Solo escribe data/marcha_despliegue.json (vía motor).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core import pase_director as pd  # noqa: E402

MARCHA_REL = Path("data") / "marcha_despliegue.json"
MARCHAS_OK = frozenset(pd.MARCHAS.keys())


class PanelHandler(SimpleHTTPRequestHandler):
    def do_POST(self):  # noqa: N802
        path = (self.path or "").split("?", 1)[0]
        if path not in ("/data/marcha_despliegue.json", "data/marcha_despliegue.json"):
            self.send_error(405, "Only POST /data/marcha_despliegue.json")
            return
        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0 or length > 8192:
            self.send_error(400, "bad body")
            return
        try:
            raw = self.rfile.read(length)
            data = json.loads(raw.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError, OSError):
            self.send_error(400, "invalid json")
            return
        mid = str(data.get("marcha_id") or data.get("id") or "").strip().lower()
        if mid not in MARCHAS_OK:
            self.send_error(400, "marcha_id invalida")
            return
        dias = data.get("duracion_dias")
        if dias is None:
            dias = data.get("duracionDias")
        equity = data.get("equity_usd")
        if equity is None:
            equity = data.get("equity")
        try:
            payload = pd.guardar_marcha(
                mid,
                duracion_dias=float(dias) if dias is not None else None,
                equity_usd=float(equity) if equity is not None else None,
            )
        except ValueError as e:
            self.send_error(400, str(e))
            return
        except Exception as e:
            self.send_error(500, str(e)[:200])
            return
        body = json.dumps({"ok": True, **payload}).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))


def main() -> int:
    ap = argparse.ArgumentParser(description="Panel HTTP ShadowHarmy")
    ap.add_argument("--port", "-p", type=int, default=8080)
    ap.add_argument("--directory", "-d", default=str(ROOT))
    args = ap.parse_args()
    os.chdir(args.directory)
    handler = partial(PanelHandler, directory=args.directory)
    httpd = ThreadingHTTPServer(("0.0.0.0", args.port), handler)
    print(f"[panel_http] root={args.directory} port={args.port}", flush=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
