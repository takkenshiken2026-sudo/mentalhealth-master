#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Write mentalhealth knowledge hub S30 helpers."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

HEADER_COMPARE = [
    "slug", "title", "category", "tags", "summary", "col_labels", "compare_rows",
    "article_title", "article_lead", "exam_points", "common_mistakes", "memory_tip",
    "related_terms", "faq_1_question", "faq_1_answer", "faq_2_question", "faq_2_answer",
    "faq_3_question", "faq_3_answer", "faq_4_question", "faq_4_answer",
]
HEADER_NUMBERS = [
    "slug", "title", "category", "tags", "summary", "highlight", "item_rows",
    "article_title", "article_lead", "exam_points", "common_mistakes", "memory_tip",
    "related_terms", "faq_1_question", "faq_1_answer", "faq_2_question", "faq_2_answer",
    "faq_3_question", "faq_3_answer", "faq_4_question", "faq_4_answer",
]
HEADER_MISTAKES = [
    "slug", "title", "category", "tags", "summary", "confusion_point", "pattern_rows",
    "article_title", "article_lead", "exam_points", "common_mistakes", "memory_tip",
    "related_terms", "faq_1_question", "faq_1_answer", "faq_2_question", "faq_2_answer",
    "faq_3_question", "faq_3_answer", "faq_4_question", "faq_4_answer",
]


def _faq(qa: list[tuple[str, str]]) -> dict[str, str]:
    out: dict[str, str] = {}
    for i, (q, a) in enumerate(qa, start=1):
        out[f"faq_{i}_question"] = q
        out[f"faq_{i}_answer"] = a
    return out


def _rows(*items: dict) -> str:
    return json.dumps(list(items), ensure_ascii=False)


_OFFICIAL = (
    "数値・日程・合格基準は日本産業衛生協会の公開資料と"
    "メンタルヘルス・マネジメント検定II種の試験要項で必ず確認してください。"
)


def cmp(
    slug: str,
    title: str,
    cat: str,
    tags: str,
    summary: str,
    labels: str,
    axes: list[tuple[str, list[str]]],
    article_title: str,
    lead: str,
    points: str,
    mistakes: str,
    tip: str,
    related: str,
    qa: list[tuple[str, str]],
) -> dict:
    return {
        "slug": slug,
        "title": title,
        "category": cat,
        "tags": tags,
        "summary": summary,
        "col_labels": labels,
        "compare_rows": _rows(*[{"axis": a, "cols": c} for a, c in axes]),
        "article_title": article_title,
        "article_lead": lead,
        "exam_points": points,
        "common_mistakes": mistakes,
        "memory_tip": tip,
        "related_terms": related,
        **_faq(qa),
    }


def num(
    slug: str,
    title: str,
    cat: str,
    tags: str,
    summary: str,
    highlight: str,
    items: list[tuple[str, str, str]],
    article_title: str,
    lead: str,
    points: str,
    mistakes: str,
    tip: str,
    related: str,
    qa: list[tuple[str, str]],
) -> dict:
    return {
        "slug": slug,
        "title": title,
        "category": cat,
        "tags": tags,
        "summary": summary,
        "highlight": highlight,
        "item_rows": _rows(*[{"item": i, "value": v, "note": n} for i, v, n in items]),
        "article_title": article_title,
        "article_lead": lead,
        "exam_points": points,
        "common_mistakes": mistakes,
        "memory_tip": tip,
        "related_terms": related,
        **_faq(qa),
    }


def mis(
    slug: str,
    title: str,
    cat: str,
    tags: str,
    summary: str,
    confusion: str,
    patterns: list[tuple[str, str, str, str]],
    article_title: str,
    lead: str,
    points: str,
    mistakes: str,
    tip: str,
    related: str,
    qa: list[tuple[str, str]],
) -> dict:
    return {
        "slug": slug,
        "title": title,
        "category": cat,
        "tags": tags,
        "summary": summary,
        "confusion_point": confusion,
        "pattern_rows": _rows(
            *[{"topic": t, "wrong": w, "correct": c, "trap": p} for t, w, c, p in patterns]
        ),
        "article_title": article_title,
        "article_lead": lead,
        "exam_points": points,
        "common_mistakes": mistakes,
        "memory_tip": tip,
        "related_terms": related,
        **_faq(qa),
    }
