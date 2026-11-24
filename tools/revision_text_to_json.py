#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
簡易テキスト形式の修正定義 → data/revisions/*.json（apply_question_revisions.py の入力）。

  python3 tools/revision_text_to_json.py data/revisions/src/line_kiso_b1.txt \
      -o data/revisions/line_2026-11_level_kiso_b1.json

書式（1行1項目。「キー: 値」。空行と # で始まる行は無視）:

  title: 見出し
  category: 分野名
  @@ 7 C L3            ← 実践演習 第7問。区分（A2/B/C/D）と難易度（L1〜L3）
  理由: 変更理由
  問題文: ...
  ア: ... / イ: ... / ウ: ... / エ: ...   ← 組合せ問題の記述（statement_a〜d）
  1: ... / 2: ... / 3: ... / 4: ...       ← 選択肢
  正答: 2
  解説: ...（アプリ表示の explanation）
  要約: ...（explanation_summary）
  正解の理由: ...（explanation_correct。静的ページの表示）
  誤肢: 1:...;3:...;4:...（explanation_choices）
  一問一答解説: ...（この問題に対応する一問一答4件の共通解説）
  ichi-0025 ×: 文      ← 一問一答（○ または ×）

  @@ 12 B L2 のあとに 理由 だけを書くと、難易度（tags）のみの変更になる。
  一問一答は、実践第n問（n≦300）に対応する ichi-(4n-3)〜ichi-(4n) を1グループとして扱う。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

PRACTICE_KEYS = {
    "問題文": "stem",
    "ア": "statement_a",
    "イ": "statement_b",
    "ウ": "statement_c",
    "エ": "statement_d",
    "1": "choice_1",
    "2": "choice_2",
    "3": "choice_3",
    "4": "choice_4",
    "正答": "correct",
    "解説": "explanation",
    "要約": "explanation_summary",
    "正解の理由": "explanation_correct",
    "誤肢": "explanation_choices",
}
KINDS = {
    "A2": "正答の訂正（正しい選択肢そのものが変わる）",
    "B": "記述の修正（正答は不変）",
    "C": "問題の作り直し（難易度引き上げ）",
    "D": "解説のみの修正",
}
HEAD = re.compile(r"^@@\s+(\d+)\s+(A2|B|C|D)\s+L([1-3])\s*$")
ICHI = re.compile(r"^(ichi-\d{4})\s+([○×])\s*[:：]\s*(.+)$")


def ichimon_ids(no: int) -> list[str]:
    return [f"ichi-{(no - 1) * 4 + k:04d}" for k in range(1, 5)]


def parse(text: str, path: str) -> dict:
    meta = {"grade": "line", "kinds": KINDS, "sources": []}
    practice: list[dict] = []
    ichimon: list[dict] = []
    cur: dict | None = None
    cur_ichi: dict | None = None

    def close() -> None:
        nonlocal cur, cur_ichi
        if cur is not None:
            practice.append(cur)
        if cur_ichi is not None and (cur_ichi.get("rows") or cur_ichi.get("set")):
            ichimon.append(cur_ichi)
        cur, cur_ichi = None, None

    for ln, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        m = HEAD.match(line)
        if m:
            close()
            no, kind, lv = int(m.group(1)), m.group(2), m.group(3)
            cur = {"no": no, "kind": kind, "reason": "", "set": {"tags": f"演習;level{lv}"}}
            cur_ichi = {"ids": ichimon_ids(no) if no <= 300 else [], "kind": kind, "reason": "", "rows": {}}
            continue
        mi = ICHI.match(line)
        if mi:
            if cur_ichi is None:
                sys.exit(f"{path}:{ln}: @@ より前に一問一答があります")
            rid, ans, q = mi.groups()
            if rid not in cur_ichi["ids"]:
                sys.exit(f"{path}:{ln}: {rid} は実践第{cur['no']}問に対応する一問一答ではありません")
            cur_ichi["rows"][rid] = {"question": q.strip(), "answer": ans}
            continue
        if ":" not in line and "：" not in line:
            sys.exit(f"{path}:{ln}: 「キー: 値」の形式ではありません: {line[:40]}")
        key, val = re.split(r"\s*[:：]\s*", line, maxsplit=1)
        val = val.strip()
        if cur is None:
            if key == "出典":
                meta["sources"].append(val)
            elif key in ("title", "category", "difficulty_policy"):
                meta[key] = val
            else:
                sys.exit(f"{path}:{ln}: 不明な見出し項目 {key}")
            continue
        if key == "理由":
            cur["reason"] = val
            cur_ichi["reason"] = f"実践{cur['no']}の修正に連動。" + val
        elif key == "一問一答解説":
            cur_ichi.setdefault("set", {})["explanation"] = val
        elif key in PRACTICE_KEYS:
            cur["set"][PRACTICE_KEYS[key]] = val
        else:
            sys.exit(f"{path}:{ln}: 不明な項目 {key}")
    close()

    for e in practice:
        if not e["reason"]:
            sys.exit(f"{path}: 実践{e['no']} に 理由 がありません")
    for e in ichimon:
        missing = [i for i in e["ids"] if i not in e["rows"]]
        if e["rows"] and missing:
            sys.exit(f"{path}: {e['ids'][0]} のグループで一問一答が不足: {missing}")
    return {"meta": meta, "practice": practice, "ichimon": ichimon}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("source", type=Path)
    ap.add_argument("-o", "--output", type=Path, required=True)
    args = ap.parse_args()
    spec = parse(args.source.read_text(encoding="utf-8"), str(args.source))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(spec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote: {args.output}（実践 {len(spec['practice'])} 問・一問一答 {sum(len(e['rows']) for e in spec['ichimon'])} 件）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
