#!/usr/bin/env python3
"""HTTP del Pergamino — sirve el repo + POST seguro de marcha_despliegue.json.

Sustituye `python -m http.server` para que el altar pueda guardar el ritmo
sin Vite. Solo escribe data/marcha_despliegue.json.
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
MARCHA_REL = Path("data") / "marcha_despliegue.json"
MARCHAS_OK = frozenset({"tactico", "marcha_forzada", "asalto"})


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
        data["marcha_id"] = mid
        out = ROOT / MARCHA_REL
        out.parent.mkdir(parents=True, exist_ok=True)
        tmp = out.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
        if out.exists():
            out.unlink()
        tmp.rename(out)
        body = json.dumps({"ok": True, **data}).encode("utf-8")
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
