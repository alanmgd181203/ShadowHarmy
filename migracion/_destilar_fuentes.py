"""One-shot extractor for migracion destillation. Run from repo root."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = Path(__file__).resolve().parent / "_fuentes_extraidas"
OUT.mkdir(parents=True, exist_ok=True)

MANUAL = ROOT / "manual_v2"
SANDBOX = MANUAL / "sandbox"

CODICE = [
    MANUAL / "01_capas_reglas.md",
    MANUAL / "02_perfiles_bots.md",
    MANUAL / "03_gestion_intercambios.md",
    MANUAL / "04_logica_tecnica.md",
]

SANDBOX_FILES = sorted(SANDBOX.glob("*.md")) if SANDBOX.is_dir() else []


def split_ideas(text: str) -> list[dict]:
    """Split manual blocks by chroma marker or ## header."""
    parts = re.split(r"(?=<!-- chroma:|\n## 💡|\n#### #)", text)
    ideas: list[dict] = []
    for part in parts:
        part = part.strip()
        if len(part) < 60:
            continue
        tag_m = re.search(r"#([A-Za-z_]+)", part)
        title_m = re.search(r"^#{1,4}\s+(.+)$", part, re.M)
        ideas.append(
            {
                "tag": f"#{tag_m.group(1)}" if tag_m else None,
                "title": (title_m.group(1).strip() if title_m else "")[:120],
                "chars": len(part),
                "preview": re.sub(r"\s+", " ", part[:400]),
                "body": part[:8000],
            }
        )
    return ideas


def main() -> None:
    catalog: dict = {"codice": [], "sandbox": [], "1m_topics": []}

    for path in CODICE:
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        rel = path.relative_to(ROOT).as_posix()
        ideas = split_ideas(text)
        catalog["codice"].append({"file": rel, "bytes": len(text), "ideas": ideas})
        (OUT / f"codice_{path.stem}.md").write_text(text, encoding="utf-8")

    for path in SANDBOX_FILES:
        text = path.read_text(encoding="utf-8", errors="replace")
        if len(text) < 200:
            continue
        rel = path.relative_to(ROOT).as_posix()
        ideas = split_ideas(text)
        catalog["sandbox"].append(
            {"file": rel, "bytes": len(text), "idea_count": len(ideas), "ideas": ideas}
        )
        (OUT / f"sandbox_{path.stem}.md").write_text(text, encoding="utf-8")

    # Topic scan on 1M.txt
    src = ROOT / "1M.txt"
    if src.is_file():
        text = src.read_text(encoding="utf-8", errors="replace")
        keywords = [
            "Igris", "Beru", "Tusk", "Tank", "Greed", "Iron", "Bellion",
            "Bybit", "place_order", "Telegram", "grid", "arbitraje",
            "Shadow Army", "Monarca", "liquidación", "LTC", "futuros",
            "spot", "márgen", "riesgo", "Surge", "Homunculus", "Lilit",
        ]
        for kw in keywords:
            count = len(re.findall(re.escape(kw), text, re.I))
            if count:
                catalog["1m_topics"].append({"keyword": kw, "count": count})
        catalog["1m_chars"] = len(text)

    (OUT / "catalog.json").write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Wrote catalog: {len(catalog['codice'])} codice, {len(catalog['sandbox'])} sandbox files")


if __name__ == "__main__":
    main()
