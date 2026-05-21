#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""一問一答（past_questions_marubatsu_all_explanations.csv）の問題文が ○× 判定文として成立するか検証する。"""

from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_CSV = ROOT / "data" / "past_questions_marubatsu_all_explanations.csv"

MC_REMNANT = re.compile(
    r"(どれか|選びなさい|次の記述のうち|次の各記述|次のうち|いくつあるか|何個|個数)"
)

PREDICATE_END = re.compile(
    r"(である|ない|する|できる|できない|必要がある|必要はない|該当する|該当しない|"
    r"含まれる|及ぶ|及ばない|認められる|認められない|行う|行わない|"
    r"義務|禁止|可能|不可|例である|ものである|場合がある|場合はない|"
    r"とされる|という|となる|にならない|うる|いる|ある|ない|いう|正しい)[。．!?！？]?$"
)


def norm_key(s: str) -> str:
    return re.sub(r"\s+", "", (s or "").strip())


def is_judgement_sentence(question: str) -> bool:
    st = (question or "").strip()
    if len(st) < 10:
        return False
    if MC_REMNANT.search(st):
        return False
    if re.search(
        r"(という記述は正しい|の組み合わせは正しい|次の組み合わせは正しい|"
        r"次のケースは.+として正しい)",
        st,
    ):
        return True
    if re.match(r"^[①②③④⑤]", st) and not PREDICATE_END.search(st):
        return False
    if not re.search(r"[。．!?！？]$", st):
        if not PREDICATE_END.search(st):
            return False
    if re.search(r"場合\s*$", st) and not PREDICATE_END.search(st):
        return False
    return True


def load_rows() -> list[dict[str, str]]:
    text = DATA_CSV.read_text(encoding="utf-8-sig")
    return list(csv.DictReader(text.splitlines()))


def main() -> int:
    if not DATA_CSV.is_file():
        print(f"入力がありません: {DATA_CSV}", file=sys.stderr)
        return 1
    rows = load_rows()
    bad: list[tuple[str, str]] = []
    seen: dict[str, str] = {}
    dup: list[tuple[str, str, str]] = []
    for row in rows:
        rid = (row.get("id") or "").strip()
        q = (row.get("question") or "").strip()
        if not is_judgement_sentence(q):
            bad.append((rid, q))
        k = norm_key(q)
        if k in seen:
            dup.append((rid, seen[k], q))
        else:
            seen[k] = rid
    print(f"rows={len(rows)} bad={len(bad)} duplicate_questions={len(dup)}")
    if bad:
        print("\n--- 判定文として不十分（先頭20件）---")
        for rid, q in bad[:20]:
            print(f"{rid}: {q[:100]}")
        if len(bad) > 20:
            print(f"... 他 {len(bad) - 20} 件")
    if dup:
        print("\n--- 問題文重複 ---")
        for a, b, q in dup[:10]:
            print(f"{a} / {b}: {q[:60]}")
    return 1 if bad or dup else 0


if __name__ == "__main__":
    raise SystemExit(main())
