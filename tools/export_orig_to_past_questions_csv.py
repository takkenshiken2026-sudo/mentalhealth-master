#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""eisei1-master-data.js の演習問題を data/past_questions.csv に書き出す（JSは上書きしない）。"""

from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.build_q_index_from_master import extract_questions_array  # noqa: E402

MASTER_JS = ROOT / "eisei1-master-data.js"
OUT = ROOT / "data" / "past_questions.csv"

FIELD_TO_CAT = {
    "law": "基礎・役割",
    "rights": "職場環境・配慮",
    "limit": "相談・連携・復職",
}

HEADER = [
    "exam_year",
    "exam_wareki",
    "question_no",
    "type",
    "category",
    "stem",
    "choice_1",
    "choice_2",
    "choice_3",
    "choice_4",
    "correct",
    "is_invalidated",
    "explanation",
]


def main() -> int:
    src = MASTER_JS.read_text(encoding="utf-8")
    questions = extract_questions_array(src)
    rows: list[dict[str, str]] = []
    for q in questions:
        if q.get("year") != "orig":
            continue
        field = q.get("field", "law")
        opts = q.get("opts") or []
        while len(opts) < 4:
            opts.append("")
        ans = q.get("ans", 0)
        try:
            correct = int(ans) + 1
        except (TypeError, ValueError):
            correct = 1
        if correct < 1 or correct > 4:
            correct = 1
        text = q.get("text") or ""
        stem = text
        m = re.search(r"\n\n科目:\s*", text)
        if m:
            stem = text[: m.start()].strip()
        rows.append(
            {
                "exam_year": "2026",
                "exam_wareki": "演習",
                "question_no": str(q.get("num", len(rows) + 1)),
                "type": "single",
                "category": FIELD_TO_CAT.get(field, "基礎・役割"),
                "stem": stem,
                "choice_1": opts[0],
                "choice_2": opts[1],
                "choice_3": opts[2],
                "choice_4": opts[3],
                "correct": str(correct),
                "is_invalidated": "FALSE",
                "explanation": q.get("exp") or "",
            }
        )

    with OUT.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=HEADER)
        w.writeheader()
        w.writerows(rows)

    print(f"Wrote {len(rows)} rows to {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
