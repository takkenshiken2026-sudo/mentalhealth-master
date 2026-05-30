#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""mentalhealth-master の guide_articles.csv 量産テンプレを差し替え、編集品質基準まで引き上げる。"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.mentalhealth_guide_content_lib import (  # noqa: E402
    META_STUB,
    action_items_for,
    faq_answer_for,
    is_stub,
    key_points_for,
    lead_for,
    load_glossary_index,
    meta_description_for,
    section_body_for,
    term_for_hub_slug,
    topic_from_row,
    user_intent_for,
)

GUIDE_CSV = ROOT / "data" / "guide_articles.csv"
GLOSSARY_CSV = ROOT / "data" / "glossary_terms.csv"


def hub_extra_sections(row: dict[str, str], topic: str, slug: str, ctx: dict) -> int:
    """用語ハブ活用法ジャンルに不足セクションを追加。"""
    if row.get("genre") != "用語ハブ活用法":
        return 0
    changes = 0
    if not (row.get("section_4_heading") or "").strip():
        row["section_4_heading"] = "比較表・よくある誤答タブ"
        row["section_4_body"] = section_body_for(
            "比較表・よくある誤答タブ", topic, slug, row.get("genre") or "", ctx
        )
        changes += 1
    if not (row.get("section_5_heading") or "").strip():
        row["section_5_heading"] = "関連ガイドと演習への導線"
        row["section_5_body"] = section_body_for(
            "関連ガイドと演習への導線", topic, slug, row.get("genre") or "", ctx
        )
        changes += 1
    return changes


def upgrade_row(row: dict[str, str], glossary: dict[str, dict[str, str]]) -> int:
    changes = 0
    topic = topic_from_row(row)
    slug = (row.get("slug") or "").strip()
    genre = (row.get("genre") or "").strip()

    ctx: dict = {}
    if genre == "用語ハブ活用法":
        term_name, term_short = term_for_hub_slug(slug, row.get("title") or "", glossary)
        ctx["term_name"] = term_name
        ctx["term_short"] = term_short

    md = (row.get("meta_description") or "").strip()
    if len(md) < 70 or META_STUB in md or is_stub(md):
        row["meta_description"] = meta_description_for(row, topic)
        changes += 1

    ui = (row.get("user_intent") or "").strip()
    if is_stub(ui) or "読了後は行動チェックリストに沿って演習・用語確認まで進められる状態を目指します" in ui:
        if ui.count("読了後は行動チェックリスト") > 0 or len(ui) < 50 or is_stub(ui):
            row["user_intent"] = user_intent_for(topic, genre)
            changes += 1

    if not (row.get("key_points") or "").strip():
        row["key_points"] = key_points_for(row, topic)
        changes += 1

    new_lead = lead_for(row, topic)
    if new_lead != (row.get("lead") or "").strip():
        row["lead"] = new_lead
        changes += 1

    generic_action = "間違えた用語を用語解説で確認して解き直す"
    if generic_action in (row.get("action_items") or "") or len((row.get("action_items") or "").split(";")) < 3:
        row["action_items"] = action_items_for(topic, slug, genre)
        changes += 1

    for n in range(1, 8):
        hcol, bcol = f"section_{n}_heading", f"section_{n}_body"
        heading = (row.get(hcol) or "").strip()
        body = (row.get(bcol) or "").strip()
        if not heading:
            continue
        needs = (
            is_stub(body)
            or len(body) < 180
            or "<a href" in body
            or f"(記事:{slug})" not in body
        )
        if needs:
            row[bcol] = section_body_for(heading, topic, slug, genre, ctx)
            changes += 1

    for n in range(1, 5):
        qcol, acol = f"faq_{n}_question", f"faq_{n}_answer"
        q = (row.get(qcol) or "").strip()
        if q:
            row[acol] = faq_answer_for(q, topic, slug, row, faq_index=n)
            changes += 1

    changes += hub_extra_sections(row, topic, slug, ctx)

    return changes


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", type=Path, default=ROOT)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    guide_path = args.target / "data" / "guide_articles.csv"
    glossary_path = args.target / "data" / "glossary_terms.csv"
    if not guide_path.is_file():
        print(f"missing: {guide_path}", file=sys.stderr)
        return 1

    glossary = load_glossary_index(glossary_path)
    rows = list(csv.DictReader(guide_path.open(encoding="utf-8-sig")))
    total_changes = 0
    for row in rows:
        total_changes += upgrade_row(row, glossary)

    if args.dry_run:
        print(f"dry-run: would update {total_changes} cell(s) across {len(rows)} rows")
        return 0

    with guide_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys(), lineterminator="\n", extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    print(f"upgraded {guide_path}: {total_changes} cell(s) across {len(rows)} rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
