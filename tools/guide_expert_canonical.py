#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""試験ガイド41本の正本原稿（populate スクリプト群から集約）。"""

from __future__ import annotations

from tools.populate_guide_articles_batch10 import NEW_ARTICLES as BATCH10
from tools.populate_guide_articles_batch20 import NEW_ARTICLES as BATCH20
from tools.populate_guide_articles_extra import NEW_ARTICLES as EXTRA
from tools.populate_guide_articles_phase2 import ARTICLES as PHASE2

CONTENT_KEYS = (
    "lead",
    "meta_description",
    "user_intent",
    "action_items",
    *(f"section_{i}_heading" for i in range(1, 8)),
    *(f"section_{i}_body" for i in range(1, 8)),
    *(f"faq_{i}_question" for i in range(1, 5)),
    *(f"faq_{i}_answer" for i in range(1, 5)),
)


def collect_canonical() -> dict[str, dict[str, str]]:
    """slug → 正本フィールド。後から読み込んだソースが優先。"""
    out: dict[str, dict[str, str]] = {}
    for source in (PHASE2, BATCH10, BATCH20, EXTRA):
        for art in source:
            slug = (art.get("slug") or "").strip()
            if not slug:
                continue
            bucket = out.setdefault(slug, {})
            for key in CONTENT_KEYS:
                val = (art.get(key) or "").strip()
                if val:
                    bucket[key] = val
    return out


def slugs() -> list[str]:
    return sorted(collect_canonical().keys())
