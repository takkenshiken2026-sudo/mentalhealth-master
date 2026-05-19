#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""用語の公開 URL スラッグ（安定・衝突回避）。"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEGACY_MAP_PATH = ROOT / "docs" / "glossary-article-slugs.json"

READABLE_OVERRIDES: dict[str, str] = {
    "ストレス": "stress",
    "うつ病": "utsu-byo",
    "ストレスチェック": "stress-check",
    "安全配慮義務": "anzen-hairyo-gimu",
    "ラインケア": "line-care",
    "パワーハラスメント": "power-harassment",
    "36協定": "36-kyotei",
    "SSRI": "ssri",
    "SNRI": "snri",
    "ILO（国際労働機関）": "ilo",
    "NPO（民間非営利組織）": "npo",
}


def norm(s: str | None) -> str:
    return (s or "").strip()


def legacy_slug_id(term: str, reading: str, legacy_map: dict[str, str]) -> str:
    if term in legacy_map:
        return legacy_map[term]
    base = f"{term.strip()}|{reading.strip()}"
    h = hashlib.sha256(base.encode("utf-8")).hexdigest()[:16]
    return f"g-{h}"


def ascii_slug(term: str) -> str | None:
    t = term.strip()
    m = re.match(r"^([A-Za-z][A-Za-z0-9]*)", t)
    if m:
        return m.group(1).lower()
    m2 = re.match(r"^([0-9]+[A-Za-z0-9]*)", t)
    if m2:
        return re.sub(r"[^a-z0-9]+", "-", m2.group(1).lower()).strip("-")
    inner = re.search(r"（([A-Za-z][A-Za-z0-9\s]+)）", t)
    if inner:
        s = re.sub(r"[^a-z0-9]+", "-", inner.group(1).lower()).strip("-")
        if len(s) >= 2:
            return s
    return None


def url_slug_for(term: str, reading: str, used: dict[str, str], legacy_map: dict[str, str]) -> str:
    if term in READABLE_OVERRIDES:
        base = READABLE_OVERRIDES[term]
    else:
        base = ascii_slug(term) or legacy_slug_id(term, reading, legacy_map)
    base = re.sub(r"[^a-z0-9-]+", "-", base.lower()).strip("-") or legacy_slug_id(term, reading, legacy_map)
    if base not in used:
        used[base] = term
        return base
    leg = legacy_slug_id(term, reading, legacy_map)
    if leg not in used:
        used[leg] = term
        return leg
    n = 2
    while True:
        cand = f"{base}-{n}"
        if cand not in used:
            used[cand] = term
            return cand
        n += 1


def load_legacy_map() -> dict[str, str]:
    if not LEGACY_MAP_PATH.is_file():
        return {}
    return json.loads(LEGACY_MAP_PATH.read_text(encoding="utf-8"))
