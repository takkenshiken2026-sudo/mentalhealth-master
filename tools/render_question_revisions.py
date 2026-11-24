#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修正定義（data/revisions/*.json）から、確認用の対照表（変更前／変更後）を Markdown で出力する。
反映前の CSV と比べるので、apply_question_revisions.py を実行する前に使う。

  python3 tools/render_question_revisions.py data/revisions/line_2026-11_kiso.json \
      -o reports/revisions/line_2026-11_kiso.md
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

FIELD_LABELS = {
    "stem": "問題文",
    "choice_1": "選択肢1",
    "choice_2": "選択肢2",
    "choice_3": "選択肢3",
    "choice_4": "選択肢4",
    "correct": "正答",
    "explanation": "解説（アプリ表示）",
    "explanation_summary": "解説の要約",
    "explanation_correct": "正解の理由（静的ページ表示）",
    "explanation_choices": "誤りの選択肢の理由（非表示列）",
    "explanation_point": "学習のヒント",
    "question": "問題文",
    "answer": "正答",
}
DISPLAY_ORDER = list(FIELD_LABELS)
KIND_ORDER = {"A2": 0, "C": 1, "B": 2, "D": 3}


def load(name: str, key: str) -> dict[str, dict]:
    with (DATA / name).open(encoding="utf-8-sig", newline="") as f:
        return {r[key]: r for r in csv.DictReader(f)}


def quote(text: str) -> str:
    return "\n".join("> " + (line or " ") for line in (text or "（空）").split("\n"))


def render(spec: dict) -> str:
    practice = load("practice_questions.csv", "question_no")
    ichimon = load("ichimon_questions.csv", "id")
    meta = spec.get("meta", {})
    kinds = meta.get("kinds", {})
    p_entries = spec.get("practice", [])
    i_entries = spec.get("ichimon", [])

    out: list[str] = [f"# {meta.get('title', '問題修正の対照表')}", ""]

    # 集計
    def count(entries, n_rows):
        c: dict[str, int] = {}
        for e in entries:
            c[e["kind"]] = c.get(e["kind"], 0) + n_rows(e)
        return c

    pc = count(p_entries, lambda e: 1)
    ic = count(i_entries, lambda e: len(e["ids"]))
    out += ["## 集計", "", "| 区分 | 意味 | 実践演習 | 一問一答 |", "|---|---|---|---|"]
    for k in sorted(kinds, key=lambda x: KIND_ORDER.get(x, 9)):
        out.append(f"| {k} | {kinds[k]} | {pc.get(k, 0)}問 | {ic.get(k, 0)}件 |")
    out.append(f"| 計 | | {len(p_entries)}問 | {sum(len(e['ids']) for e in i_entries)}件 |")
    decide = [str(e["no"]) for e in p_entries if e.get("needs_decision")]
    out += ["", "- 実践演習の変更は、同じ番号の過去問（第1〜300問）にも同時に反映します。"]
    if decide:
        out.append(f"- **ご判断が必要な項目**: 実践 {', '.join(decide)}（各項目の理由欄を参照）")
    if meta.get("sources"):
        out += ["", "根拠とした公表資料:", ""] + [f"- {s}" for s in meta["sources"]]
    out.append("")

    # 実践演習
    out += ["## 実践演習", ""]
    for e in sorted(p_entries, key=lambda e: (KIND_ORDER.get(e["kind"], 9), e["no"])):
        no = str(e["no"])
        row = practice[no]
        flag = "【要判断】" if e.get("needs_decision") else ""
        out += [f"### 実践{no}（区分 {e['kind']}）{flag}", "", f"**理由**: {e['reason']}", ""]
        for field in sorted(e["set"], key=lambda f: DISPLAY_ORDER.index(f) if f in DISPLAY_ORDER else 99):
            before = row.get(field, "")
            after = e["set"][field]
            if before == after:
                continue
            label = FIELD_LABELS.get(field, field)
            out += [f"**{label}**", "", "変更前", "", quote(before), "", "変更後", "", quote(after), ""]
        out.append("---")
        out.append("")

    # 一問一答
    out += ["## 一問一答", ""]
    for e in sorted(i_entries, key=lambda e: (KIND_ORDER.get(e["kind"], 9), e["ids"][0])):
        flag = "【要判断】" if e.get("needs_decision") else ""
        out += [f"### {e['ids'][0]}〜{e['ids'][-1][-4:]}（区分 {e['kind']}）{flag}" if len(e["ids"]) > 1
                else f"### {e['ids'][0]}（区分 {e['kind']}）{flag}", "", f"**理由**: {e['reason']}", ""]
        common = e.get("set", {})
        rows_spec = e.get("rows", {})
        changed_rows = [rid for rid in e["ids"] if rid in rows_spec]
        if changed_rows:
            out += ["| ID | 変更前 | 変更後 |", "|---|---|---|"]
            for rid in changed_rows:
                cur = ichimon[rid]
                new = rows_spec[rid]
                bq = cur["question"].replace("|", "｜")
                aq = new.get("question", cur["question"]).replace("|", "｜")
                ba, aa = cur["answer"], new.get("answer", cur["answer"])
                mark = "（○×変更）" if ba != aa else ""
                out.append(f"| {rid} | {ba} {bq} | {aa} {aq}{mark} |")
            out.append("")
            for rid in changed_rows:
                if "explanation" in rows_spec[rid]:
                    out += [f"**{rid} の解説**", "", "変更前", "", quote(ichimon[rid]["explanation"]), "",
                            "変更後", "", quote(rows_spec[rid]["explanation"]), ""]
        if "explanation" in common:
            before = ichimon[e["ids"][0]]["explanation"]
            out += [f"**解説（{len(e['ids'])}件共通）**", "", "変更前", "", quote(before), "",
                    "変更後", "", quote(common["explanation"]), ""]
        out.append("---")
        out.append("")
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("revision", type=Path)
    ap.add_argument("-o", "--output", type=Path)
    args = ap.parse_args()
    spec = json.loads(args.revision.read_text(encoding="utf-8"))
    text = render(spec)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
        print(f"wrote: {args.output}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
