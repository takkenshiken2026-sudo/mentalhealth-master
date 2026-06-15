#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""学習系ガイドへ公開済み affiliate 比較記事の導線を追加する（メンタルヘルス二種）。"""

from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "data" / "guide_articles.csv"

AFFILIATE_TITLES = {
    "affiliate-textbooks-recommend": "メンタルヘルス・マネジメント検定II種のおすすめテキスト3選【2026年度版·独学】",
    "affiliate-problem-books": "メンタルヘルス・マネジメント検定II種のおすすめ問題集3選【2026年度版·過去問】",
    "affiliate-online-course-compare": "メンタルヘルス・マネジメント検定II種のオンライン講座比較【動画·2026年度版】",
    "affiliate-correspondence-course": "メンタルヘルス・マネジメント検定II種の通信講座比較【2026年度版·独学併用】",
}

BODY = {
    "affiliate-textbooks-recommend": (
        "テキスト1冊は、affiliate-textbooks-recommend で公式第6版·TAC·サクッとわかるの3冊を比較してから固定すると途中で変えずに済みます。"
    ),
    "affiliate-problem-books": (
        "演習1冊は、affiliate-problem-books で過去問2025·能率協会·TACの3冊を比較してから100問120分演習に組み込むと迷いが減ります。"
    ),
    "affiliate-online-course-compare": (
        "動画中心で始めたい場合は、affiliate-online-course-compare でスタディング·Udemyの学習設計を比較し、当サイト演習量は維持したまま1講座に絞ると続きやすいです。"
    ),
    "affiliate-correspondence-course": (
        "週5時間未満が続く場合は、affiliate-correspondence-course でスタディング·産業能率大学·キャリカレを比較してから独学テキストと役割分担を決めると安全です。"
    ),
}

GUIDE_AFFILIATE: dict[str, tuple[str, int]] = {
    "overview": ("affiliate-textbooks-recommend", 2),
    "self-study-guide": ("affiliate-textbooks-recommend", 2),
    "textbook-selection": ("affiliate-textbooks-recommend", 2),
    "problem-book-selection": ("affiliate-problem-books", 2),
    "correspondence-course-guide": ("affiliate-correspondence-course", 2),
    "self-study-start": ("affiliate-correspondence-course", 2),
    "study-plan": ("affiliate-textbooks-recommend", 2),
    "study-plan-3months": ("affiliate-textbooks-recommend", 2),
    "study-plan-6months": ("affiliate-textbooks-recommend", 2),
    "study-plan-1year": ("affiliate-textbooks-recommend", 2),
    "study-plan-working": ("affiliate-correspondence-course", 2),
    "study-plan-beginner": ("affiliate-textbooks-recommend", 2),
    "first-30-days-plan": ("affiliate-textbooks-recommend", 2),
    "balance-work-study": ("affiliate-correspondence-course", 2),
    "self-study-without-school": ("affiliate-online-course-compare", 2),
    "self-study-schedule": ("affiliate-correspondence-course", 2),
    "past-questions-study": ("affiliate-problem-books", 2),
    "past-questions-by-field": ("affiliate-problem-books", 2),
    "past-questions-review-cycle": ("affiliate-problem-books", 2),
    "past-questions-wrong-reasons": ("affiliate-problem-books", 2),
    "timed-practice": ("affiliate-problem-books", 2),
    "mock-exam-how-to": ("affiliate-problem-books", 2),
    "drill-volume-guide": ("affiliate-problem-books", 2),
    "final-day-checklist": ("affiliate-problem-books", 2),
    "plateau-breakthrough": ("affiliate-correspondence-course", 2),
}

SECONDARY_AFFILIATE: dict[str, str] = {
    "overview": "affiliate-problem-books",
    "self-study-guide": "affiliate-problem-books",
    "textbook-selection": "affiliate-problem-books",
    "correspondence-course-guide": "affiliate-online-course-compare",
    "study-plan-working": "affiliate-online-course-compare",
    "balance-work-study": "affiliate-textbooks-recommend",
    "self-study-without-school": "affiliate-textbooks-recommend",
    "past-questions-study": "affiliate-textbooks-recommend",
    "final-day-checklist": "affiliate-textbooks-recommend",
}


def _split_related(value: str) -> list[str]:
    return [x.strip() for x in (value or "").split(";") if x.strip()]


def _append_related(value: str, token: str) -> str:
    parts = _split_related(value)
    slug = token.split(":", 1)[0]
    if any(p.split(":", 1)[0] == slug for p in parts):
        return ";".join(parts)
    parts.append(token)
    return ";".join(parts)


def _append_body(body: str, aff_slug: str) -> str:
    sentence = BODY[aff_slug]
    if aff_slug in (body or ""):
        return body
    text = (body or "").rstrip()
    if not text:
        return sentence
    if not text.endswith("。"):
        text += "。"
    return text + sentence


def apply_guide_updates(rows: list[dict[str, str]]) -> int:
    by_slug = {r["slug"]: r for r in rows}
    changed = 0
    for slug, (aff_slug, sec_n) in GUIDE_AFFILIATE.items():
        row = by_slug.get(slug)
        if not row or (row.get("content_status") or "").strip() != "published":
            continue
        body_key = f"section_{sec_n}_body"
        old_body = row.get(body_key, "")
        new_body = _append_body(old_body, aff_slug)
        if new_body != old_body:
            row[body_key] = new_body

        token = f"{aff_slug}:{AFFILIATE_TITLES[aff_slug]}"
        new_rl = _append_related(row.get("related_links", ""), token)
        sec = SECONDARY_AFFILIATE.get(slug)
        if sec:
            new_rl = _append_related(new_rl, f"{sec}:{AFFILIATE_TITLES[sec]}")
        if new_rl != row.get("related_links", "") or new_body != old_body:
            row["related_links"] = new_rl
            changed += 1
    return changed


def main() -> None:
    with CSV_PATH.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)
    if not fieldnames:
        raise SystemExit("guide_articles.csv: no header")

    changed = apply_guide_updates(rows)

    with CSV_PATH.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    print(f"Guide funnel: {len(GUIDE_AFFILIATE)} targets, {changed} row(s) updated")


if __name__ == "__main__":
    main()
