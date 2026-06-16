#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ASP未設定の講座系アフィリエイト導線を下書き化し、通常ガイドから外す。"""

from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.affiliate_links import is_trackable_asp_url
from tools.related_links import parse_related_link_token
CSV_PATH = ROOT / "data" / "guide_articles.csv"
SITE_CONFIG = ROOT / "site-config.json"

# ASP未設定の講座比較記事（公式直リンクのみ）
DRAFT_AFFILIATE_SLUGS = frozenset(
    {
        "affiliate-online-course-compare",
        "affiliate-correspondence-course",
        "affiliate-cram-school",
        "affiliate-retake-short-course",
        "affiliate-qualification-support-service",
    }
)

FUNNEL_BODY_SNIPPETS = (
    "動画中心で始めたい場合は、affiliate-online-course-compare でスタディング·Udemyの学習設計を比較し、当サイト演習量は維持したまま1講座に絞ると続きやすいです。",
    "週5時間未満が続く場合は、affiliate-correspondence-course でスタディング·産業能率大学·キャリカレを比較してから独学テキストと役割分担を決めると安全です。",
)

_HTTPS_TOKEN_RE = re.compile(r"https?://[^;]+")


def split_semicolon(value: str) -> list[str]:
    return [x.strip() for x in (value or "").split(";") if x.strip()]


def strip_funnel_body(text: str) -> str:
    out = text or ""
    for snippet in FUNNEL_BODY_SNIPPETS:
        out = out.replace(snippet, "")
    return out.strip()


def clean_related_links(value: str) -> str:
    kept: list[str] = []
    for item in split_semicolon(value):
        target, _label = parse_related_link_token(item)
        if target in DRAFT_AFFILIATE_SLUGS:
            continue
        if target.startswith(("http://", "https://")):
            if is_trackable_asp_url(target):
                kept.append(item)
            continue
        kept.append(item)
    return ";".join(kept)


def clean_prose_refs(text: str) -> str:
    if not text:
        return text
    out = strip_funnel_body(text)
    replacements = (
        ("affiliate-online-course-compareも参照してください。", ""),
        ("affiliate-online-course-compareも併読してください。", ""),
        ("affiliate-correspondence-courseで通信型の代替も比較する", ""),
        ("affiliate-correspondence-courseで通信型の代替も確認する", ""),
        ("affiliate-correspondence-courseで通信型の代替も比較してください。", ""),
        ("affiliate-correspondence-course:通信講座の比較", ""),
        ("通信講座比較記事（affiliate-correspondence-course）", "通信講座"),
        ("（オンライン講座比較記事）", ""),
        ("・通信講座 → [通信講座の比較](../affiliate-correspondence-course/)", ""),
        ("[通信講座の比較](../affiliate-correspondence-course/)", "通信講座（ASP確定後に比較記事を公開予定）"),
    )
    for old, new in replacements:
        out = out.replace(old, new)
    for slug in DRAFT_AFFILIATE_SLUGS:
        out = re.sub(
            rf"\[([^\]]*)\]\(\.\./{re.escape(slug)}/\)",
            r"\1",
            out,
        )
    out = re.sub(r"\s{2,}", " ", out)
    out = re.sub(r"。{2,}", "。", out)
    return out.strip()


def update_guide_rows(rows: list[dict[str, str]]) -> int:
    changed = 0
    for row in rows:
        slug = (row.get("slug") or "").strip()
        touched = False

        if slug in DRAFT_AFFILIATE_SLUGS:
            if (row.get("content_status") or "").strip() != "draft":
                row["content_status"] = "draft"
                touched = True
            note = (row.get("original_note") or "").strip()
            stamp = "ASP未設定のためdraft（講座公式直リンクは導線対象外）"
            if stamp not in note:
                row["original_note"] = f"{note} {stamp}".strip() if note else stamp
                touched = True

        new_rl = clean_related_links(row.get("related_links", ""))
        if new_rl != row.get("related_links", ""):
            row["related_links"] = new_rl
            touched = True

        for key, value in list(row.items()):
            if not value:
                continue
            if key.startswith("section_") and key.endswith("_body"):
                cleaned = clean_prose_refs(value)
                if slug not in DRAFT_AFFILIATE_SLUGS:
                    cleaned = strip_funnel_body(cleaned)
                if cleaned != value:
                    row[key] = cleaned
                    touched = True
            elif key.startswith("faq_") and key.endswith("_answer"):
                cleaned = clean_prose_refs(value)
                if cleaned != value:
                    row[key] = cleaned
                    touched = True

        if touched:
            changed += 1
    return changed


def update_site_config() -> bool:
    data = json.loads(SITE_CONFIG.read_text(encoding="utf-8"))
    picks = data.get("guideIndexPicks") or {}
    items = picks.get("items") or []
    new_items = [it for it in items if (it.get("href") or "").strip() not in {
        "affiliate-correspondence-course/",
        "affiliate-online-course-compare/",
    }]
    if len(new_items) == len(items):
        # 通信講座カードを初学者セットに差し替え（未実施時のみ）
        has_beginner = any(
            (it.get("href") or "").startswith("affiliate-beginner-material-set") for it in items
        )
        if not has_beginner and any((it.get("kind") or "") == "course" for it in items):
            new_items = [it for it in items if (it.get("kind") or "") != "course"]
            new_items.append(
                {
                    "kind": "material-set",
                    "kindLabel": "教材セット",
                    "title": "初学者向け教材セット【2026】",
                    "description": "テキスト1冊+問題集1冊の最小セット。無料演習と併用する購入順序を3パターン比較します。",
                    "href": "affiliate-beginner-material-set/",
                    "cta": "セットを比較する",
                    "image": "images/affiliate/mentalhealth-book-450258021x.webp",
                    "imageAlt": "メンタルヘルス・マネジメント検定試験公式テキスト Ⅱ種 ラインケアコース 第6版 表紙",
                }
            )
        else:
            return False
    picks["items"] = new_items
    picks["title"] = "おすすめのテキスト・問題集・教材セット"
    picks["lead"] = "2026年度版の比較記事から、テキスト・問題集・教材セットの選び方へ。"
    leads = picks.get("leadsByHub") or {}
    leads["articles"] = picks["lead"]
    leads["terms"] = "用語暗記と併用するテキスト・問題集の比較記事へ。"
    leads["q"] = "無料演習と併用する問題集・教材セットの比較記事へ。"
    picks["leadsByHub"] = leads
    picks["layout"] = "grid-3" if len(new_items) >= 3 else "grid-2"
    data["guideIndexPicks"] = picks
    SITE_CONFIG.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return True


def main() -> None:
    with CSV_PATH.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)
    if not fieldnames:
        raise SystemExit("guide_articles.csv: no header")

    changed = update_guide_rows(rows)
    config_changed = update_site_config()

    with CSV_PATH.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    print(f"CSV: {changed} row(s) updated; draft slugs: {sorted(DRAFT_AFFILIATE_SLUGS)}")
    print(f"site-config guideIndexPicks: {'updated' if config_changed else 'unchanged'}")


if __name__ == "__main__":
    main()
