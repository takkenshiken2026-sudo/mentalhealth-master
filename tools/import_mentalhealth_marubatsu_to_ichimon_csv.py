#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
data/past_questions_marubatsu_all_explanations.csv → data/ichimon_questions.csv

メンタルヘルス二種マスター専用。SPA 用 eisei1-data-ichimon.js と同じソース。

  python3 tools/import_mentalhealth_marubatsu_to_ichimon_csv.py
  python3 tools/import_mentalhealth_marubatsu_to_ichimon_csv.py --dry-run
"""

from __future__ import annotations

import argparse
import csv
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "past_questions_marubatsu_all_explanations.csv"
OUTPUT = ROOT / "data" / "ichimon_questions.csv"

ICHIMON_COLUMNS = [
    "id",
    "question",
    "answer",
    "explanation",
    "explanation_summary",
    "explanation_correct",
    "explanation_opposite",
    "explanation_point",
    "category",
    "tags",
    "source",
    "note",
]

VALID_ANSWERS = {"○", "〇", "×", "✕", "╳"}


def norm(s: str | None) -> str:
    return (s or "").strip()


def normalize_answer(raw: str, line_no: int) -> str:
    s = norm(raw)
    if s == "〇":
        return "○"
    if s in ("✕", "╳"):
        return "×"
    if s not in VALID_ANSWERS:
        raise ValueError(f"行 {line_no}: answer が不正: {raw!r}")
    return s


def row_to_ichimon(row: dict, line_no: int) -> dict[str, str]:
    rid = norm(row.get("id"))
    if not rid:
        raise ValueError(f"行 {line_no}: id が空")
    question = norm(row.get("question"))
    if not question:
        raise ValueError(f"行 {line_no}: question が空")
    category = norm(row.get("category"))
    if not category:
        raise ValueError(f"行 {line_no}: category が空")
    exp = norm(row.get("explanation")) or "（解説は未入力です。）"
    return {
        "id": rid,
        "question": question,
        "answer": normalize_answer(row.get("answer", ""), line_no),
        "explanation": exp,
        "explanation_summary": norm(row.get("explanation_summary")),
        "explanation_correct": norm(row.get("explanation_correct")),
        "explanation_opposite": norm(row.get("explanation_opposite")),
        "explanation_point": norm(row.get("explanation_point")),
        "category": category,
        "tags": norm(row.get("tags")),
        "source": norm(row.get("source")),
        "note": norm(row.get("note")),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="marubatsu CSV → ichimon_questions.csv")
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
            rows_out.append(row_to_ichimon(row, i))

    if not rows_out:
        print("error: 取り込み行がありません", file=sys.stderr)
        return 1

    print(f"ichimon_questions: {len(rows_out)} 行（{args.source.name}）")
    if args.dry_run:
        return 0

    if args.output.is_file() and not args.no_backup:
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        backup = args.output.with_suffix(f".csv.bak.{ts}")
        shutil.copy2(args.output, backup)
        print(f"backup: {backup.name}")

    with args.output.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=ICHIMON_COLUMNS, lineterminator="\n")
        w.writeheader()
        w.writerows(rows_out)
    print(f"wrote: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
