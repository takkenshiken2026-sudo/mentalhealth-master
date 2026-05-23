#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
data/past_questions.csv（演習300問・4択）→ data/practice_questions.csv

メンタルヘルス二種マスター専用。past_questions.csv は演習問題プールとして運用している。

  python3 tools/import_mentalhealth_past_to_practice_csv.py
  python3 tools/import_mentalhealth_past_to_practice_csv.py --dry-run
"""

from __future__ import annotations

import argparse
import csv
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "past_questions.csv"
OUTPUT = ROOT / "data" / "practice_questions.csv"

PRACTICE_COLUMNS = [
    "question_no",
    "type",
    "category",
    "tags",
    "stem",
    "preamble",
    "statement_a",
    "statement_b",
    "statement_c",
    "statement_d",
    "choice_1",
    "choice_2",
    "choice_3",
    "choice_4",
    "correct",
    "explanation",
    "explanation_summary",
    "explanation_correct",
    "explanation_choices",
    "explanation_point",
]


def norm(s: str | None) -> str:
    return (s or "").strip()


def row_to_practice(qno: int, row: dict, line_no: int) -> dict[str, str]:
    stem = norm(row.get("stem"))
    if not stem:
        raise ValueError(f"行 {line_no}: stem が空")
    opts = [norm(row.get(f"choice_{i}")) for i in range(1, 5)]
    if not all(opts):
        raise ValueError(f"行 {line_no}: 選択肢 (1)〜(4) が欠けています")
    raw_ans = norm(row.get("correct"))
    if not raw_ans.isdigit() or not (1 <= int(raw_ans) <= 4):
        raise ValueError(f"行 {line_no}: correct が不正: {raw_ans!r}")
    category = norm(row.get("category"))
    if not category:
        raise ValueError(f"行 {line_no}: category が空")
    tags = norm(row.get("tags")) or "演習"
    return {
        "question_no": str(qno),
        "type": norm(row.get("type")) or "single",
        "category": category,
        "tags": tags,
        "stem": stem,
        "preamble": norm(row.get("preamble")),
        "statement_a": norm(row.get("statement_a")),
        "statement_b": norm(row.get("statement_b")),
        "statement_c": norm(row.get("statement_c")),
        "statement_d": norm(row.get("statement_d")),
        "choice_1": opts[0],
        "choice_2": opts[1],
        "choice_3": opts[2],
        "choice_4": opts[3],
        "correct": raw_ans,
        "explanation": norm(row.get("explanation")) or "（解説は未入力です。）",
        "explanation_summary": norm(row.get("explanation_summary")),
        "explanation_correct": norm(row.get("explanation_correct")),
        "explanation_choices": norm(row.get("explanation_choices")),
        "explanation_point": norm(row.get("explanation_point")),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="past_questions.csv → practice_questions.csv")
    ap.add_argument("--source", type=Path, default=SOURCE)
    ap.add_argument("--output", type=Path, default=OUTPUT)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-backup", action="store_true")
    args = ap.parse_args()

    if not args.source.is_file():
        print(f"error: {args.source} がありません", file=sys.stderr)
        return 1

    rows_out: list[dict[str, str]] = []
    with args.source.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, start=2):
            rows_out.append(row_to_practice(len(rows_out) + 1, row, i))

    if not rows_out:
        print("error: 取り込み行がありません", file=sys.stderr)
        return 1

    print(f"practice_questions: {len(rows_out)} 問（{args.source.name}）")
    if args.dry_run:
        return 0

    if args.output.is_file() and not args.no_backup:
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        backup = args.output.with_suffix(f".csv.bak.{ts}")
        shutil.copy2(args.output, backup)
        print(f"backup: {backup.name}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=PRACTICE_COLUMNS, lineterminator="\n")
        w.writeheader()
        w.writerows(rows_out)
    print(f"wrote: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
