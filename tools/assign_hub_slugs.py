#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""hub_slug_maps の slug を comparisons / numbers / mistakes.csv に付与."""

from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
DATA = ROOT / "data"

from tools.hub_slug_maps import COMPARE_SLUGS, MISTAKES_SLUGS, NUMBERS_SLUGS  # noqa: E402


def _apply(path: Path, slugs: list[str]) -> int:
    with path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        header = list(reader.fieldnames or [])
        rows = list(reader)
    if len(rows) != len(slugs):
        raise SystemExit(f"{path.name}: expected {len(slugs)} rows, got {len(rows)}")
    for row, slug in zip(rows, slugs):
        row["slug"] = slug
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=header, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    return len(rows)


def main() -> None:
    n = _apply(DATA / "comparisons.csv", COMPARE_SLUGS)
    m = _apply(DATA / "numbers.csv", NUMBERS_SLUGS)
    k = _apply(DATA / "mistakes.csv", MISTAKES_SLUGS)
    print(f"assigned slugs: compare={n} numbers={m} mistakes={k}")


if __name__ == "__main__":
    main()
