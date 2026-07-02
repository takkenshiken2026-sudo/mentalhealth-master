#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""メン管II種 試験日検索ページ exam-dates/index.html を生成する。"""

from __future__ import annotations

import html
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.exam_schedule_mhm_table import (  # noqa: E402
    exam_schedule_table_html,
    latest_fetched_at,
    load_schedule_rows,
    upcoming_rows,
)
from tools.exam_schedule_page_content import (  # noqa: E402
    META_DESCRIPTION,
    PAGE_LEAD,
    PAGE_SLUG,
    PAGE_TITLE,
    faq_items,
    page_sections,
)
from tools.html_footer import (  # noqa: E402
    ROBOTS_INDEX_FOLLOW,
    breadcrumb_html,
    shell_body_class,
    site_page_footer,
    site_page_header,
    site_page_wrap_close,
    site_page_wrap_open,
)
from tools.knowledge_hub_seo import faq_section_html  # noqa: E402
from tools.seo_body_markup import seo_section_body_html  # noqa: E402
from tools.seo_editorial_chrome import (  # noqa: E402
    seo_brand_asset_tags,
    seo_editorial_article_class,
    seo_editorial_head_fonts,
    seo_editorial_stylesheet_links,
)
from tools.site_config import brand_name, exam_name, public_url  # noqa: E402

OUTPUT_DIR = ROOT / PAGE_SLUG
REL_PATH = Path(PAGE_SLUG) / "index.html"
EXAM_DATES_CSS_VER = "20260628-exam-schedule-filter"

AUTHOR_NAME = "メンタル二種マスター編集部"
AUTHOR_PROFILE = (
    "メンタルヘルス・マネジメント検定II種（ラインケア）の学習設計·演習運用を専門とする編集チーム。"
    "7領域100問120分の演習導線づくりを担当しています。"
)
REVIEWER_NAME = "公式情報確認担当"
REVIEWER_PROFILE = (
    "公益財団法人 日本産業衛生協会の公開試験要項と照合し、"
    "サイト内リンクの整合を確認した担当者です。"
)
PRIMARY_SOURCES = [
    {
        "label": "公開試験 受験要項（公式）",
        "url": "https://www.mental-health.ne.jp/guide/",
    },
    {
        "label": "試験のご紹介（公式）",
        "url": "https://www.mental-health.ne.jp/about/",
    },
]


def quality_panel_html(fact_checked_at: str) -> str:
    rows = [
        f"<tr><th>執筆</th><td>{html.escape(AUTHOR_NAME)}（{html.escape(AUTHOR_PROFILE)}）</td></tr>",
        f"<tr><th>確認</th><td>{html.escape(REVIEWER_NAME)}（{html.escape(REVIEWER_PROFILE)}）</td></tr>",
        f"<tr><th>事実確認日</th><td>{html.escape(fact_checked_at)}</td></tr>",
        (
            "<tr><th>主な参照元</th><td><ul class=\"quality-source-list\">"
            + "".join(
                f'<li><a href="{html.escape(s["url"])}" target="_blank" rel="noopener noreferrer">'
                f'{html.escape(s["label"])}</a></li>'
                for s in PRIMARY_SOURCES
            )
            + "</ul></td></tr>"
        ),
    ]
    return (
        '<section class="seo-quality-panel" aria-labelledby="quality-panel-title">'
        '<h2 id="quality-panel-title">このページの信頼性について</h2>'
        '<table class="seo-info-table"><tbody>'
        + "".join(rows)
        + "</tbody></table></section>"
    )


def section_html(heading: str, body: str, section_num: int, section_id: str) -> str:
    body_html = seo_section_body_html(body)
    return (
        f'<section class="seo-article-section" aria-labelledby="{section_id}">'
        f'<h2 id="{section_id}"><span class="section-heading-num">{section_num}</span>'
        f"{html.escape(heading)}</h2>{body_html}</section>"
    )


def related_links_html() -> str:
    links = [
        ("../articles/exam-schedule/", "試験日程·12週逆算"),
        ("../articles/exam-application-flow/", "申込みの流れ"),
        ("../articles/exam-venue-and-region/", "会場·受験地の選び方"),
        ("../articles/study-plan/", "学習計画の立て方"),
        ("../terms/index.html", "用語解説一覧"),
    ]
    items = "".join(
        f'<a class="related-link" href="{html.escape(href, quote=True)}">{html.escape(label)}</a>'
        for href, label in links
    )
    return (
        '<div class="related-box"><div class="related-box-title">関連コンテンツ</div>'
        f'<div class="related-links">{items}</div></div>'
    )


def next_round_event_entries(rows: list[dict[str, str]], canonical: str) -> list[dict]:
    """直近の公開試験（最も早い開催日の回）を Event 構造化データで出力する。

    「メンタルヘルスマネジメント検定 日程 2026」等のクエリで日付リッチリザルトの
    対象になり得る。日付は要項準拠の exam_date_iso のみを使用し、本文には数値を
    固定しないサイト方針は維持する（Event は公式 CSV 由来の確定データのみ）。
    """
    dated = [r for r in upcoming_rows(rows) if r.get("exam_date_iso", "").strip()]
    if not dated:
        return []
    next_iso = min(r["exam_date_iso"].strip() for r in dated)
    exam = exam_name()
    events: list[dict] = []
    for row in dated:
        if row.get("exam_date_iso", "").strip() != next_iso:
            continue
        city = row.get("city", "").strip()
        label = row.get("round_label", "").strip()
        official = row.get("official_url", "").strip()
        name = " ".join(part for part in [exam, label, "公開試験"] if part)
        if city:
            name = f"{name}（{city}）"
        event = {
            "@type": "Event",
            "name": name,
            "startDate": next_iso,
            "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
            "eventStatus": "https://schema.org/EventScheduled",
            "url": canonical,
            "location": {
                "@type": "Place",
                "name": f"{city}会場" if city else "公開試験会場",
                "address": {
                    "@type": "PostalAddress",
                    "addressLocality": city or "日本",
                    "addressCountry": "JP",
                },
            },
        }
        if official:
            event["organizer"] = {
                "@type": "Organization",
                "name": "大阪商工会議所",
                "url": official,
            }
        events.append(event)
    return events


def build_page_html() -> str:
    schedule_rows = load_schedule_rows()
    fact_checked = (latest_fetched_at(schedule_rows) or date.today().isoformat())[:10]
    canonical = public_url(f"{PAGE_SLUG}/")
    title = f"{PAGE_TITLE}｜{brand_name()}"
    desc = META_DESCRIPTION

    faq_list = [{"question": q, "answer": a} for q, a in faq_items()]
    body_parts: list[str] = [
        exam_schedule_table_html(schedule_rows, section_num=None, show_heading=False, show_note=False),
        quality_panel_html(fact_checked),
    ]
    section_num = 1
    for idx, (heading, body) in enumerate(page_sections()):
        body_parts.append(section_html(heading, body, section_num, f"exam-dates-sec-{idx + 1}"))
        section_num += 1
    body_parts.append(
        faq_section_html(faq_list, heading_id="exam-dates-faq", section_num=section_num)
    )
    body_parts.append(related_links_html())

    graph: list[dict] = [
        {
            "@type": "WebPage",
            "@id": canonical + "#webpage",
            "url": canonical,
            "name": PAGE_TITLE,
            "description": desc,
            "inLanguage": "ja-JP",
            "isPartOf": {"@type": "WebSite", "name": brand_name(), "url": public_url("index.html")},
            "about": exam_name(),
        },
        {
            "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "トップ", "item": public_url("index.html")},
                {"@type": "ListItem", "position": 2, "name": PAGE_TITLE, "item": canonical},
            ],
        },
    ]
    if faq_list:
        graph.append(
            {
                "@type": "FAQPage",
                "@id": canonical + "#faq",
                "mainEntity": [
                    {
                        "@type": "Question",
                        "name": item["question"],
                        "acceptedAnswer": {"@type": "Answer", "text": item["answer"]},
                    }
                    for item in faq_list
                ],
            }
        )

    graph.extend(next_round_event_entries(schedule_rows, canonical))

    json_ld = {"@context": "https://schema.org", "@graph": graph}

    header = site_page_header(REL_PATH, current="exam-dates")
    footer = site_page_footer(REL_PATH, current=None)
    crumb = breadcrumb_html(
        REL_PATH,
        [
            ("トップ", "../index.html"),
            ("試験日検索", None),
        ],
    )

    article_class = seo_editorial_article_class(extra="exam-dates-page")

    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
{seo_brand_asset_tags(REL_PATH)}
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(desc)}">
{ROBOTS_INDEX_FOLLOW}
<link rel="canonical" href="{html.escape(canonical)}">
<meta property="og:type" content="website">
<meta property="og:title" content="{html.escape(PAGE_TITLE)}">
<meta property="og:description" content="{html.escape(desc)}">
<meta property="og:url" content="{html.escape(canonical)}">
<meta name="twitter:card" content="summary_large_image">
{seo_editorial_head_fonts()}
{seo_editorial_stylesheet_links(REL_PATH, site_pages_ver=EXAM_DATES_CSS_VER)}
<script type="application/ld+json">
{json.dumps(json_ld, ensure_ascii=False, indent=2)}
</script>
</head>
<body class="{shell_body_class('exam-dates-page')}">
{site_page_wrap_open()}
{header}
<main class="seo-article-main">
{crumb}
<article class="{article_class}">
<div class="article-meta">
<span class="meta-category">試験日検索</span>
<span class="meta-updated">更新日：{html.escape(fact_checked)}</span>
</div>
<h1 class="article-title">{html.escape(PAGE_TITLE)}</h1>
<p class="article-lead" id="exam-dates-lead">{html.escape(PAGE_LEAD)}</p>
{"".join(body_parts)}
</article>
</main>
{footer}
{site_page_wrap_close()}
</body>
</html>
"""


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUTPUT_DIR / "index.html"
    out.write_text(build_page_html(), encoding="utf-8")
    print(f"Wrote {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
