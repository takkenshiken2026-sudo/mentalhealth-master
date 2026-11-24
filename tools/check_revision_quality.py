#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
難易度引き上げ用の修正定義（data/revisions/*.json）を、反映前の CSV と合わせて点検する。

  python3 tools/check_revision_quality.py data/revisions/line_2026-11_level_kiso_b1.json

点検内容:
  - 単一選択で、最も長い選択肢が正答になっていないか（同じ長さが複数あれば可）
  - 組合せ問題（記述ア〜エあり）で、選択肢の重複がないか・各選択肢がア〜エの○×をすべて含むか
  - 選択肢の重複
  - 一問一答4件の○×の内訳（全件同じ記号は警告）
"""

from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


def main() -> int:
    spec = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    with (DATA / "practice_questions.csv").open(encoding="utf-8-sig", newline="") as f:
        practice = {r["question_no"]: r for r in csv.DictReader(f)}
    errs: list[str] = []
    warns: list[str] = []
    for e in spec.get("practice", []):
        no = str(e["no"])
        row = dict(practice[no])
        row.update(e["set"])
        cor = int(row["correct"])
        choices = [row[f"choice_{i}"] for i in range(1, 5)]
        if len(set(choices)) < 4:
            errs.append(f"実践{no}: 選択肢が重複しています")
        is_combo = bool(row.get("statement_a"))
        if is_combo:
            for i, c in enumerate(choices, start=1):
                marks = re.findall(r"([アイウエ])\s*([○×])", c)
                if [m[0] for m in marks] != ["ア", "イ", "ウ", "エ"]:
                    errs.append(f"実践{no}: 組合せの選択肢{i}がア〜エの○×をすべて含んでいません: {c}")
        else:
            lens = [len(c) for c in choices]
            mx = max(lens)
            if lens[cor - 1] == mx and lens.count(mx) == 1:
                errs.append(f"実践{no}: 最も長い選択肢（{cor}）が正答です {lens}")
    for e in spec.get("ichimon", []):
        rows = e.get("rows", {})
        if len(rows) == 4:
            ans = [rows[i]["answer"] for i in e["ids"]]
            if len(set(ans)) == 1:
                warns.append(f"{e['ids'][0]}〜: 4件すべて {ans[0]}")
    for w in warns:
        print("[WARN]", w)
    for x in errs:
        print("[ERROR]", x)
    print(f"点検: エラー {len(errs)} 件・警告 {len(warns)} 件")
    return 1 if errs else 0


if __name__ == "__main__":
    raise SystemExit(main())
