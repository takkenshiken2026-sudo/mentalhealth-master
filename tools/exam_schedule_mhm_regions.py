#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""メン管検定 公開試験の受験地（15都市）と地方ブロック。"""

from __future__ import annotations

OFFICIAL_GUIDE_URL = "https://www.mental-health.ne.jp/guide/"

# (受験地, 地方ブロック) — 公式要項の受験地一覧順
MHM_CITIES: list[tuple[str, str]] = [
    ("札幌", "北海道"),
    ("仙台", "東北"),
    ("さいたま", "関東"),
    ("千葉", "関東"),
    ("東京", "関東"),
    ("横浜", "関東"),
    ("新潟", "甲信越"),
    ("浜松", "東海"),
    ("名古屋", "東海"),
    ("京都", "近畿"),
    ("大阪", "近畿"),
    ("神戸", "近畿"),
    ("広島", "中国"),
    ("高松", "四国"),
    ("福岡", "九州"),
]


def region_blocks() -> list[tuple[str, list[tuple[str, str]]]]:
    order: list[str] = []
    groups: dict[str, list[tuple[str, str]]] = {}
    for city, block in MHM_CITIES:
        if block not in groups:
            order.append(block)
            groups[block] = []
        groups[block].append((city, block))
    return [(block, groups[block]) for block in order]
