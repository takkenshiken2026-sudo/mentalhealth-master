#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""data/question_levels.csv の一部の行を更新する（難易度の見直し・作り直し後の再判定用）。

  python3 tools/update_question_levels.py "p5:4比 p26:3例 i0017:3制 ..."
    p<番号>  … 実践演習（過去問の同じ番号も共通）
    i<番号>  … 一問一答 ichi-<番号4桁>
    値は「レベル(1〜5)＋根拠の記号」。判定基準は docs/question-difficulty-rubric.md
"""

from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "data" / "question_levels.csv"
TOKEN = re.compile(r"^([pi])(\d+):([1-5])(\S+)$")


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    with CSV_PATH.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    index = {(r["kind"], r["id"]): r for r in rows}
    changed = 0
    for tok in " ".join(sys.argv[1:]).split():
        m = TOKEN.match(tok)
        if not m:
            raise SystemExit(f"形式が違います: {tok}")
        kind = "practice" if m.group(1) == "p" else "ichimon"
        qid = str(int(m.group(2))) if kind == "practice" else f"ichi-{int(m.group(2)):04d}"
        row = index.get((kind, qid))
        if row is None:
            raise SystemExit(f"見つかりません: {kind} {qid}")
        row["level"], row["basis"] = m.group(3), m.group(4)
        changed += 1
    with CSV_PATH.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["kind", "id", "level", "basis"])
        w.writeheader()
        w.writerows(rows)
    print(f"updated {changed} rows: {CSV_PATH.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
