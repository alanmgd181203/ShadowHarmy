#!/usr/bin/env python3
"""Genera PDF del pergamino Intestinos de Igris (Monarca)."""
from __future__ import annotations

import re
from pathlib import Path

from fpdf import FPDF

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "migracion" / "INTESTINOS_IGRIS_MAPA_FUGAS_2026-08-11.md"
OUT = ROOT / "migracion" / "INTESTINOS_IGRIS_MAPA_FUGAS_2026-08-11.pdf"
FONT = Path(r"C:\Windows\Fonts\arial.ttf")
FONT_B = Path(r"C:\Windows\Fonts\arialbd.ttf")


class Pergamino(FPDF):
    def footer(self) -> None:
        self.set_y(-12)
        self.set_font("Army", size=8)
        self.set_text_color(90, 90, 90)
        self.cell(0, 8, f"Shadow Army · Igris · pagina {self.page_no()}/{{nb}}", align="C")


def _clean(s: str) -> str:
    s = re.sub(r"\*\*(.+?)\*\*", r"\1", s)
    s = re.sub(r"\*(.+?)\*", r"\1", s)
    s = re.sub(r"`([^`]+)`", r"\1", s)
    repl = {
        "→": "->",
        "×": "x",
        "≥": ">=",
        "≤": "<=",
        "·": " · ",
        "—": " - ",
        "–": "-",
        "€": "EUR",
        "\u00a0": " ",
    }
    for a, b in repl.items():
        s = s.replace(a, b)
    return s.strip()


def _is_table_sep(line: str) -> bool:
    body = line.replace("|", "").replace(":", "").replace("-", "").replace(" ", "")
    return body == ""


def main() -> int:
    lines = SRC.read_text(encoding="utf-8").splitlines()
    pdf = Pergamino(format="A4")
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_font("Army", "", str(FONT))
    pdf.add_font("Army", "B", str(FONT_B))
    pdf.add_page()
    pdf.set_margins(18, 16, 18)
    left = 18

    i = 0
    while i < len(lines):
        line = lines[i].rstrip()
        i += 1

        if not line.strip():
            pdf.ln(2.5)
            continue

        if line.strip() == "---":
            y = pdf.get_y() + 1
            pdf.set_draw_color(170, 170, 170)
            pdf.line(left, y, pdf.w - left, y)
            pdf.ln(5)
            continue

        # Tabla -> filas como texto
        if line.lstrip().startswith("|"):
            rows = []
            row0 = line
            while True:
                if _is_table_sep(row0):
                    if i >= len(lines):
                        break
                    row0 = lines[i].rstrip()
                    i += 1
                    continue
                if not row0.lstrip().startswith("|"):
                    i -= 1
                    break
                cells = [_clean(c) for c in row0.strip().strip("|").split("|")]
                rows.append(cells)
                if i >= len(lines):
                    break
                row0 = lines[i].rstrip()
                i += 1
                if not row0.lstrip().startswith("|"):
                    i -= 1
                    break

            if rows:
                headers = rows[0]
                for cells in rows[1:]:
                    bits = []
                    for h, c in zip(headers, cells):
                        if c:
                            bits.append(f"{h}: {c}")
                    pdf.set_x(left)
                    pdf.set_font("Army", size=9)
                    pdf.set_text_color(35, 35, 35)
                    pdf.multi_cell(pdf.w - 2 * left, 5, " · ".join(bits) if bits else " · ".join(cells))
                    pdf.ln(0.5)
            continue

        pdf.set_x(left)
        usable = pdf.w - 2 * left

        if line.startswith("# "):
            pdf.set_font("Army", "B", 15)
            pdf.set_text_color(15, 15, 15)
            pdf.multi_cell(usable, 7.5, _clean(line[2:]))
            pdf.ln(2)
            continue
        if line.startswith("## "):
            pdf.ln(2)
            pdf.set_font("Army", "B", 12)
            pdf.set_text_color(25, 25, 25)
            pdf.multi_cell(usable, 6.5, _clean(line[3:]))
            pdf.ln(1)
            continue
        if line.startswith("### "):
            pdf.set_font("Army", "B", 10.5)
            pdf.set_text_color(35, 35, 35)
            pdf.multi_cell(usable, 5.8, _clean(line[4:]))
            pdf.ln(0.8)
            continue

        body = line
        if line.startswith("- "):
            body = "• " + line[2:]
        pdf.set_font("Army", size=10)
        pdf.set_text_color(20, 20, 20)
        pdf.multi_cell(usable, 5.2, _clean(body))
        pdf.ln(0.4)

    pdf.output(str(OUT))
    print(f"OK {OUT} bytes={OUT.stat().st_size}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
