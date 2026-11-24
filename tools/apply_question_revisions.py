#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
問題の修正定義（data/revisions/*.json）を、II種の問題 CSV へ反映する。

反映先（1つの定義から連動して更新する）:
  - data/practice_questions.csv            実践演習（正本）
  - data/past_questions.csv                過去問（実践演習 第1〜300問の旧版。同じ番号を同期）
  - data/ichimon_questions.csv             一問一答（正本）
  - data/past_questions_marubatsu_all_explanations.csv
                                           一問一答の取り込み元（import スクリプトで上書きされないよう同期）

使い方:
  python3 tools/apply_question_revisions.py data/revisions/line_2026-11_kiso.json --dry-run
  python3 tools/apply_question_revisions.py data/revisions/line_2026-11_kiso.json
  python3 tools/apply_question_revisions.py --check            # 整合検査のみ
  python3 tools/apply_question_revisions.py --sync-past        # 過去問 1〜300 を実践演習に一括同期

反映後は必ず `python3 tools/build_site.py`（または build_all.py）で再生成する。
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
PRACTICE = DATA / "practice_questions.csv"
PAST = DATA / "past_questions.csv"
ICHIMON = DATA / "ichimon_questions.csv"
MARUBATSU = DATA / "past_questions_marubatsu_all_explanations.csv"

PRACTICE_FIELDS = {
    "stem", "preamble", "statement_a", "statement_b", "statement_c", "statement_d",
    "choice_1", "choice_2", "choice_3", "choice_4", "correct",
    "explanation", "explanation_summary", "explanation_correct",
    "explanation_choices", "explanation_point", "category", "tags",
}
ICHIMON_FIELDS = {
    "question", "answer", "explanation", "explanation_summary",
    "explanation_correct", "explanation_opposite", "explanation_point",
    "category", "tags", "source", "note",
}
# 過去問 CSV と実践演習 CSV で共通する列（過去問の同期対象）
PAST_SYNC_FIELDS = [
    "category", "stem", "choice_1", "choice_2", "choice_3", "choice_4", "correct",
    "explanation", "explanation_choices", "explanation_correct",
    "explanation_summary", "explanation_point",
]
PAST_SYNC_MAX_NO = 300


class Table:
    """CSV を書式（改行コード・BOM）ごと保持して読み書きする。"""

    def __init__(self, path: Path):
        self.path = path
        raw = path.read_text(encoding="utf-8")
        self.bom = raw.startswith("﻿")
        text = raw.lstrip("﻿")
        self.lineterminator = "\r\n" if "\r\n" in text.split("\n", 1)[0] + "\n" else "\n"
        reader = csv.DictReader(io.StringIO(text))
        self.fieldnames = list(reader.fieldnames or [])
        self.rows = list(reader)
        self.original = raw

    def render(self) -> str:
        out = io.StringIO()
        w = csv.DictWriter(out, fieldnames=self.fieldnames, lineterminator=self.lineterminator)
        w.writeheader()
        w.writerows(self.rows)
        return ("﻿" if self.bom else "") + out.getvalue()

    def save(self) -> bool:
        text = self.render()
        if text == self.original:
            return False
        self.path.write_text(text, encoding="utf-8")
        return True


def index_by(rows: list[dict], key: str) -> dict[str, dict]:
    return {r[key].strip(): r for r in rows}


# ---------------------------------------------------------------- 反映

def apply_practice(entries: list[dict], practice: Table, past: Table, log: list[str]) -> None:
    by_no = index_by(practice.rows, "question_no")
    past_by_no = index_by(past.rows, "question_no")
    for ent in entries:
        no = str(ent["no"])
        row = by_no.get(no)
        if row is None:
            raise SystemExit(f"実践演習 第{no}問が見つかりません")
        for field, value in ent["set"].items():
            if field not in PRACTICE_FIELDS:
                raise SystemExit(f"実践演習 第{no}問: 未対応の列 {field}")
            if row.get(field, "") != value:
                log.append(f"実践{no} {field}")
                row[field] = value
        # 過去問（同じ番号の旧版）へ同期
        if int(no) <= PAST_SYNC_MAX_NO and no in past_by_no:
            sync_past_row(row, past_by_no[no], log, label=f"過去問{no}")


def sync_past_row(prow: dict, past_row: dict, log: list[str], *, label: str) -> None:
    for field in PAST_SYNC_FIELDS:
        if field in past_row and past_row[field] != prow.get(field, ""):
            log.append(f"{label} {field}")
            past_row[field] = prow.get(field, "")


def apply_ichimon(entries: list[dict], ichimon: Table, marubatsu: Table, log: list[str]) -> None:
    by_id = index_by(ichimon.rows, "id")
    mb_by_id = index_by(marubatsu.rows, "id")
    for ent in entries:
        ids = ent["ids"]
        rows_spec = ent.get("rows", {})
        extra = set(rows_spec) - set(ids)
        if extra:
            raise SystemExit(f"一問一答: rows にあって ids にない id {sorted(extra)}")
        for rid in ids:
            row = by_id.get(rid)
            if row is None:
                raise SystemExit(f"一問一答 {rid} が見つかりません")
            values = dict(ent.get("set", {}))
            values.update(rows_spec.get(rid, {}))
            for field, value in values.items():
                if field not in ICHIMON_FIELDS:
                    raise SystemExit(f"一問一答 {rid}: 未対応の列 {field}")
                if field == "answer" and value not in ("○", "×"):
                    raise SystemExit(f"一問一答 {rid}: answer は ○ か × のみ: {value!r}")
                if row.get(field, "") != value:
                    log.append(f"{rid} {field}")
                    row[field] = value
                mb = mb_by_id.get(rid)
                if mb is not None and field in mb and mb[field] != value:
                    mb[field] = value


# ---------------------------------------------------------------- 検査

NUM_REF = re.compile(r"[（(]([1-4])[）)]")


def check_practice(practice: Table) -> list[str]:
    errs: list[str] = []
    for r in practice.rows:
        no = r["question_no"]
        cor = r["correct"].strip()
        if cor not in {"1", "2", "3", "4"}:
            errs.append(f"実践{no}: correct が不正 {cor!r}")
            continue
        for c in range(1, 5):
            if not r[f"choice_{c}"].strip():
                errs.append(f"実践{no}: choice_{c} が空")
        refs = set(NUM_REF.findall(r["explanation_correct"]))
        if refs and refs != {cor}:
            errs.append(f"実践{no}: explanation_correct の番号 {sorted(refs)} が正答 {cor} と不一致")
        keys = set(re.findall(r"(?:^|;)\s*([1-4]):", r["explanation_choices"]))
        if cor in keys:
            errs.append(f"実践{no}: explanation_choices に正答 {cor} の項目がある")
        # 『…とする（n）が最も不適切』のように explanation 本文で正答番号を名指ししている場合
        for m in re.finditer(r"[（(]([1-4])[）)]が(?:最も)?(?:不)?適切", r["explanation"]):
            if m.group(1) != cor:
                errs.append(f"実践{no}: explanation が（{m.group(1)}）を正答扱い（正答は {cor}）")
    return errs


def check_past_sync(practice: Table, past: Table) -> list[str]:
    diffs: list[str] = []
    past_by_no = index_by(past.rows, "question_no")
    for r in practice.rows:
        no = r["question_no"]
        if int(no) > PAST_SYNC_MAX_NO or no not in past_by_no:
            continue
        p = past_by_no[no]
        fields = [f for f in PAST_SYNC_FIELDS if f in p and p[f] != r.get(f, "")]
        if fields:
            diffs.append(f"過去問{no}: {', '.join(fields)}")
    return diffs


def check_ichimon(ichimon: Table, marubatsu: Table) -> tuple[list[str], list[str]]:
    errs: list[str] = []
    warns: list[str] = []
    mb = index_by(marubatsu.rows, "id")
    for r in ichimon.rows:
        rid = r["id"]
        if r["answer"] not in ("○", "×"):
            errs.append(f"{rid}: answer が不正 {r['answer']!r}")
        if re.search(r"という(?:記述|内容)は正しい。$", r["question"]):
            warns.append(f"{rid}: 「〜という記述は正しい」型の文が残っている")
        if "「「" in r["question"]:
            warns.append(f"{rid}: かぎかっこが二重")
        m = mb.get(rid)
        if m is not None:
            for f in ("question", "answer", "explanation", "category"):
                if f in m and m[f] != r[f]:
                    errs.append(f"{rid}: 取り込み元 CSV と {f} が不一致")
    return errs, warns


# ---------------------------------------------------------------- 本体

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("revision", nargs="?", type=Path, help="data/revisions/*.json")
    ap.add_argument("--dry-run", action="store_true", help="書き込まずに変更点だけ表示")
    ap.add_argument("--check", action="store_true", help="整合検査のみ行う")
    ap.add_argument("--sync-past", action="store_true", help="過去問 1〜300 を実践演習に一括同期")
    args = ap.parse_args()

    practice, past = Table(PRACTICE), Table(PAST)
    ichimon, marubatsu = Table(ICHIMON), Table(MARUBATSU)
    log: list[str] = []

    if args.revision:
        spec = json.loads(args.revision.read_text(encoding="utf-8"))
        apply_practice(spec.get("practice", []), practice, past, log)
        apply_ichimon(spec.get("ichimon", []), ichimon, marubatsu, log)

    if args.sync_past:
        past_by_no = index_by(past.rows, "question_no")
        for r in practice.rows:
            no = r["question_no"]
            if int(no) <= PAST_SYNC_MAX_NO and no in past_by_no:
                sync_past_row(r, past_by_no[no], log, label=f"過去問{no}")

    if log:
        print(f"変更 {len(log)} 件")
        for line in log:
            print("  " + line)

    ichimon_errs, ichimon_warns = check_ichimon(ichimon, marubatsu)
    errs = check_practice(practice) + ichimon_errs
    past_diffs = check_past_sync(practice, past)

    if not args.dry_run and not args.check and log:
        for t in (practice, past, ichimon, marubatsu):
            if t.save():
                print(f"wrote: {t.path.relative_to(ROOT)}")

    if past_diffs:
        print(f"[WARN] 過去問と実践演習の食い違い {len(past_diffs)} 問（--sync-past で解消）")
        for d in past_diffs[:10]:
            print("  " + d)
    if ichimon_warns:
        print(f"[WARN] 一問一答の文型・表記 {len(ichimon_warns)} 件（未点検の分野を含む）")
    if errs:
        print(f"[ERROR] 整合検査 {len(errs)} 件")
        for e in errs:
            print("  " + e)
        return 1
    print("整合検査: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
