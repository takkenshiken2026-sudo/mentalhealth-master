#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""affiliate-briefs の商品 URL を guide_articles.csv の related_links に反映する（メンタルヘルス）。"""

from __future__ import annotations

import csv
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "data" / "guide_articles.csv"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# 今回 URL を入れる比較記事（brief 必須）
TARGET_SLUGS = (
    "affiliate-textbooks-recommend",
    "affiliate-problem-books",
    "affiliate-correspondence-course",
    "affiliate-online-course-compare",
)


def split_semicolon(value: str) -> list[str]:
    return [x.strip() for x in (value or "").split(";") if x.strip()]


def join_semicolon(items: list[str]) -> str:
    return ";".join(items)


def is_asp_token(item: str) -> bool:
    target = item.split(":", 1)[0].strip()
    return target.startswith(("http://", "https://"))


def merge_related_links(existing: str, brief_related: list[str], asp_urls: list[str]) -> str:
    internal: list[str] = []
    asp_existing: list[str] = []
    for item in split_semicolon(existing):
        if is_asp_token(item):
            asp_existing.append(item.split(":", 1)[0].strip())
        else:
            internal.append(item)

    seen_internal: set[str] = set()
    merged_internal: list[str] = []
    for item in brief_related + internal:
        slug = item.split(":", 1)[0].strip()
        if slug.startswith(("http://", "https://")) or slug in seen_internal:
            continue
        seen_internal.add(slug)
        merged_internal.append(item)

    seen_asp: set[str] = set()
    merged_asp: list[str] = []
    for url in asp_urls + asp_existing:
        u = url.strip()
        if not u or u in seen_asp:
            continue
        seen_asp.add(u)
        merged_asp.append(u)

    return join_semicolon(merged_internal + merged_asp)


def main() -> int:
    from tools.affiliate_brief import (
        brief_products,
        load_affiliate_brief,
        product_affiliate_url,
    )

    rows: list[dict[str, str]] = []
    fieldnames: list[str] | None = None
    updated = 0

    with CSV_PATH.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        if not fieldnames:
            print("ERROR: empty CSV", file=sys.stderr)
            return 1
        for row in reader:
            slug = row.get("slug", "")
            if slug in TARGET_SLUGS:
                brief = load_affiliate_brief(slug)
                if not brief:
                    print(f"WARN: missing brief for {slug}", file=sys.stderr)
                else:
                    asp_urls = [
                        product_affiliate_url(p)
                        for p in brief_products(brief)
                        if product_affiliate_url(p)
                    ]
                    brief_related_raw = brief.get("related_links") or []
                    if isinstance(brief_related_raw, list):
                        brief_related = [str(x).strip() for x in brief_related_raw if str(x).strip()]
                    else:
                        brief_related = split_semicolon(str(brief_related_raw))
                    new_rl = merge_related_links(row.get("related_links", ""), brief_related, asp_urls)
                    if new_rl != row.get("related_links", ""):
                        row["related_links"] = new_rl
                        updated += 1
                        note = (row.get("revision_note") or "").strip()
                        stamp = "ASP URLをbriefから反映（draft維持）"
                        if stamp not in note:
                            row["revision_note"] = (note + "; " + stamp).strip("; ").strip()
            rows.append(row)

    orig_lines = sum(1 for _ in CSV_PATH.open(encoding="utf-8-sig"))
    fd, tmp = tempfile.mkstemp(suffix=".csv", dir=CSV_PATH.parent)
    try:
        with open(fd, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
        new_lines = sum(1 for _ in open(tmp, encoding="utf-8"))
        if new_lines != orig_lines:
            print(f"ERROR: line count {orig_lines} -> {new_lines}", file=sys.stderr)
            return 1
        shutil.move(tmp, CSV_PATH)
    finally:
        if Path(tmp).exists():
            Path(tmp).unlink()

    print(f"OK: updated related_links for {updated} affiliate row(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
