#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""data/glossary_terms.csv → eisei1shu 用語 UI 互換の eisei1-data-glossary.js"""

from __future__ import annotations

import csv
import json
import re
import sys
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.site_config import exam_name, legacy_glossary_cat

CSV_PATH = ROOT / "data" / "glossary_terms.csv"
OUT_JS = ROOT / "eisei1-data-glossary.js"
OUT_JS_GENERIC = ROOT / "exam-site-data-glossary.js"


def norm(s: str | None) -> str:
    return (s or "").strip()


def category_to_cat(col: str) -> str:
    return legacy_glossary_cat(norm(col))


def slug_id(term: str, i: int) -> str:
    h = hashlib.sha256(term.encode("utf-8")).hexdigest()[:16]
    return f"csv-{h}-{i}"


def main() -> int:
    if not CSV_PATH.is_file():
        print(f"入力がありません: {CSV_PATH}", file=sys.stderr)
        return 1
    rows = list(csv.DictReader(CSV_PATH.read_text(encoding="utf-8-sig").splitlines()))
    out: list[dict] = []
    for i, row in enumerate(rows):
        term = norm(row.get("term"))
        if not term:
            continue
        short_def = norm(row.get("short_def"))
        definition = norm(row.get("definition"))
        expl = norm(row.get("explanation"))
        desc_parts = [p for p in (definition, expl) if p]
        desc = "\n\n".join(desc_parts) if desc_parts else short_def or "（説明は未入力です。）"
        summary_src = short_def or definition[:120]
        summary = summary_src if len(summary_src) <= 200 else summary_src[:197] + "…"
        out.append(
            {
                "id": slug_id(term, i),
                "cat": category_to_cat(norm(row.get("category"))),
                "term": term,
                "reading": norm(row.get("reading")),
                "summary": summary or "概要",
                "desc": desc,
            }
        )

    header = (
        f"/* eisei1-data-glossary.js — {exam_name()} 用語（埋め込み）\n"
        " * 再生成: python3 tools/glossary_csv_to_eisei_embed_js.py\n"
        " */\n"
        "let GLOSSARY_DATA = "
    )
    payload = header + json.dumps(out, ensure_ascii=False, indent=2) + ";\n"
    OUT_JS.write_text(payload, encoding="utf-8")
    OUT_JS_GENERIC.write_text(payload, encoding="utf-8")
    print(f"Wrote {OUT_JS} ({len(out)} terms)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
