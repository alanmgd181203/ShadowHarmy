#!/usr/bin/env python3
"""Sirve la página viva del teatro (ranking que se actualiza sola).

  python -u scripts/servir_teatro_live.py
  → http://127.0.0.1:8765/teatro_fusion.html   (panel fusionado — caza filtrada)
  → http://127.0.0.1:8765/teatro_mejor_beru.html (todos · mejor Beru)
  → http://127.0.0.1:8765/teatro_live.html     (matriz 4 salas)
"""
from __future__ import annotations

import argparse
import functools
import http.server
import os
import socketserver
import sys
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIR = ROOT / "data" / "coliseo" / "rango_juicio"


class NoCacheHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Evita que el browser congele teatro_*.html viejos entre recargas."""

    def end_headers(self) -> None:
        if self.path.endswith(".html") or self.path.endswith(".json"):
            self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
            self.send_header("Pragma", "no-cache")
            self.send_header("Expires", "0")
        super().end_headers()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--no-browser", action="store_true")
    ap.add_argument(
        "--page",
        default="teatro_fusion.html",
        help="Página de arranque (teatro_fusion.html | teatro_live.html)",
    )
    args = ap.parse_args()
    page = str(args.page or "teatro_fusion.html").lstrip("/")
    if not (DIR / page).exists():
        print(f"Falta {DIR / page}", file=sys.stderr)
        return 1
    os.chdir(DIR)
    handler = functools.partial(
        NoCacheHTTPRequestHandler,
        directory=str(DIR),
    )
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("127.0.0.1", int(args.port)), handler) as httpd:
        url = f"http://127.0.0.1:{int(args.port)}/{page}"
        print(f"Teatro live → {url}", flush=True)
        print(
            f"  también · http://127.0.0.1:{int(args.port)}/teatro_mejor_beru.html",
            flush=True,
        )
        print(
            f"  también · http://127.0.0.1:{int(args.port)}/teatro_live.html",
            flush=True,
        )
        print("Ctrl+C para cerrar", flush=True)
        if not args.no_browser:
            try:
                webbrowser.open(url)
            except Exception:
                pass
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\ncerrado", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
