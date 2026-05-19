#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""フェーズ3: glossary_terms.csv に SEO 列・url_slug・関連用語を付与する。"""

from __future__ import annotations

import csv
import re
from collections import defaultdict
from pathlib import Path

import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

CSV_PATH = ROOT / "data" / "glossary_terms.csv"

from tools.term_url_slug import load_legacy_map, url_slug_for  # noqa: E402

EXTRA_COLS = [
    "url_slug",
    "article_title",
    "article_lead",
    "term_detail_body",
    "exam_points",
    "common_mistakes",
    "memory_tip",
    "example_question",
    "example_answer",
    "faq_1_question",
    "faq_1_answer",
    "faq_2_question",
    "faq_2_answer",
    "faq_3_question",
    "faq_3_answer",
]


def norm(s: str | None) -> str:
    return (s or "").strip()


def split_sentences(s: str, limit: int = 4) -> list[str]:
    text = re.sub(r"\s+", " ", s or "").strip()
    if not text:
        return []
    out = [p.strip() for p in re.findall(r"[^。！？]+[。！？]?", text) if p.strip()]
    return out[:limit]


def related_from_text(text: str) -> list[str]:
    m = re.search(r"関連する用語として[、,]?([^。]+)", text)
    if not m:
        return []
    chunk = m.group(1)
    parts = re.split(r"[、,]|もあわせて", chunk)
    return [p.strip() for p in parts if p.strip() and len(p.strip()) <= 40][:3]


def main() -> int:
    text = CSV_PATH.read_text(encoding="utf-8-sig")
    reader = csv.DictReader(text.splitlines())
    fieldnames = list(reader.fieldnames or [])
    for col in EXTRA_COLS:
        if col not in fieldnames:
            fieldnames.append(col)

    rows = list(reader)
    by_cat: dict[str, list[str]] = defaultdict(list)
    for row in rows:
        t = norm(row.get("term"))
        if t:
            by_cat[norm(row.get("category"))].append(t)

    legacy_map = load_legacy_map()
    used_slugs: dict[str, str] = {}

    for row in rows:
        term = norm(row.get("term"))
        reading = norm(row.get("reading")) or term
        short_def = norm(row.get("short_def"))
        definition = norm(row.get("definition"))
        explanation = norm(row.get("explanation"))
        category = norm(row.get("category"))
        importance = norm(row.get("importance"))

        if not norm(row.get("url_slug")):
            row["url_slug"] = url_slug_for(term, reading, used_slugs, legacy_map)

        if not norm(row.get("article_title")):
            row["article_title"] = f"{term}とは？意味・根拠・試験で押さえるポイント"

        if not norm(row.get("article_lead")):
            row["article_lead"] = (
                f"{term}は、{category}分野で頻出の用語です。"
                f"{short_def or definition}"
                "本記事では意味、試験での出題の仕方、混同しやすい点を整理します。"
            )

        if not norm(row.get("term_detail_body")):
            body = definition
            if explanation and explanation != definition:
                body = f"{definition}\n\n{explanation}"
            row["term_detail_body"] = body

        if not norm(row.get("exam_points")):
            pts = split_sentences(explanation, 4)
            row["exam_points"] = ";".join(pts) if pts else short_def

        if not norm(row.get("common_mistakes")):
            row["common_mistakes"] = (
                f"{term}は、似た用語や近い制度と混同されやすいことがあります。"
                "選択肢では「常に〜」「必ず〜」「〜のみ」といった断定表現に注意し、"
                "公式テキストと用語の定義・適用場面をセットで確認してください。"
            )

        if not norm(row.get("memory_tip")) and importance in ("A", "S"):
            row["memory_tip"] = f"「{term}」は{category}の重要語。定義→誰が何をするか→連携先の順で覚えると整理しやすい。"

        rel = norm(row.get("related_terms"))
        if not rel:
            auto = related_from_text(explanation)
            if not auto:
                peers = [t for t in by_cat.get(category, []) if t != term][:3]
                auto = peers
            if auto:
                row["related_terms"] = ";".join(auto)

        if not norm(row.get("faq_1_question")):
            row["faq_1_question"] = f"{term}とは何ですか？"
            row["faq_1_answer"] = short_def or definition
            row["faq_2_question"] = f"{term}は試験でどのように問われますか？"
            row["faq_2_answer"] = (
                f"定義の確認に加え、管理監督者の役割や職場での対応場面と結びつけて問われることが多い用語です。"
                f"{split_sentences(explanation, 1)[0] if explanation else short_def}"
            )
            row["faq_3_question"] = f"{term}を学習するときの注意点は？"
            row["faq_3_answer"] = (
                "単語だけでなく、ラインケア・安全配慮・専門職連携の流れの中で意味を確認してください。"
                "数値や義務の有無は法令改正で変わる場合があるため、受験前に公式情報も確認してください。"
            )

    with CSV_PATH.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

    print(f"Updated {CSV_PATH} ({len(rows)} terms, phase3 columns)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
