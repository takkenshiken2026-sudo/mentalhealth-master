# -*- coding: utf-8 -*-
"""mentalhealth S30: 既存CSVを読み込み、slugを固定してPythonリスト化."""

from __future__ import annotations

import csv
from pathlib import Path

from tools.hub_slug_maps import COMPARE_SLUGS, MISTAKES_SLUGS, NUMBERS_SLUGS
from tools.write_mentalhealth_hub_s30 import DATA


def _load(name: str, slugs: list[str]) -> list[dict]:
    path = DATA / name
    with path.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    if len(rows) < len(slugs):
        raise ValueError(f"{name}: need {len(slugs)} rows, got {len(rows)}")
    out: list[dict] = []
    for i, slug in enumerate(slugs):
        row = dict(rows[i])
        row["slug"] = slug
        out.append(row)
    return out


COMPARISONS = _load("comparisons.csv", COMPARE_SLUGS)
NUMBERS = _load("numbers.csv", NUMBERS_SLUGS)
MISTAKES = _load("mistakes.csv", MISTAKES_SLUGS)
