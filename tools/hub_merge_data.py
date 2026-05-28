#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""知識ハブ CSV 統合出力の共通ヘルパー（S30 + S31、プレミアムFAQ適用）."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Callable

from tools.hub_faq_expand import expand_all as expand_short_faqs  # noqa: E402


def merge_rows(*groups: list[dict]) -> list[dict]:
    seen: set[str] = set()
    out: list[dict] = []
    for group in groups:
        for row in group:
            slug = row["slug"]
            if slug in seen:
                raise ValueError(f"duplicate slug: {slug}")
            seen.add(slug)
            out.append(row)
    return out


def write_csv(path: Path, header: list[str], rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=header, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def write_hub_csvs(
    data_dir: Path,
    *,
    header_compare: list[str],
    header_numbers: list[str],
    header_mistakes: list[str],
    comparisons: list[dict],
    numbers: list[dict],
    mistakes: list[dict],
    apply_premium: Callable[[list[dict]], list[dict]] | None = None,
) -> None:
    if apply_premium:
        comparisons = apply_premium(comparisons)
        numbers = apply_premium(numbers)
        mistakes = apply_premium(mistakes)
    comparisons = expand_short_faqs(comparisons)
    numbers = expand_short_faqs(numbers)
    mistakes = expand_short_faqs(mistakes)
    write_csv(data_dir / "comparisons.csv", header_compare, comparisons)
    write_csv(data_dir / "numbers.csv", header_numbers, numbers)
    write_csv(data_dir / "mistakes.csv", header_mistakes, mistakes)
    print(
        f"wrote compare={len(comparisons)} numbers={len(numbers)} mistakes={len(mistakes)}"
    )
