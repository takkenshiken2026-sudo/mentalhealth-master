#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""問題の難易度（レベル1〜5）を data/question_levels.csv から読む。

- 判定基準: docs/question-difficulty-rubric.md
- kind=practice … 実践演習の question_no（過去問の第N問は実践演習の第N問と同じ問題のため共通）
- kind=ichimon  … 一問一答の id（ichi-0001 など）
- ファイルが無い種（III種・I種のビルドでは data/ が差し替わる）では空を返し、レベルを付けない。
"""

from __future__ import annotations

import csv
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEVELS_CSV = ROOT / "data" / "question_levels.csv"


@lru_cache(maxsize=1)
def load_levels() -> dict[tuple[str, str], int]:
    if not LEVELS_CSV.is_file():
        return {}
    out: dict[tuple[str, str], int] = {}
    with LEVELS_CSV.open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            kind = (row.get("kind") or "").strip()
            qid = (row.get("id") or "").strip()
            try:
                level = int((row.get("level") or "").strip())
            except ValueError:
                continue
            if kind and qid and 1 <= level <= 5:
                out[(kind, qid)] = level
    return out


def practice_level(question_no: int) -> int | None:
    return load_levels().get(("practice", str(int(question_no))))


def ichimon_level(ichi_id: str) -> int | None:
    return load_levels().get(("ichimon", str(ichi_id).strip()))
