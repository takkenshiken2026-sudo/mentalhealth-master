#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""論述対策ハブ essays/index.html を生成する（hasEssay の種のみ）。

I種（master）など論述式のある種は navigation に「論述対策」(essays/index.html) を持つ。
本モジュールは data/essays.csv を読み、論述テーマの一覧ハブを生成する。
CSV が空（骨組み段階）のときは「準備中」の導入だけを出す。個別の論述解説ページは
後続フェーズで追加する（現時点では一覧ハブのみ）。

II種のように data/essays.csv が無い種では build_all から呼ばれても何もしない
（build_all 側で essays.csv の有無を見てから呼ぶ）。

使い方:
    python3 tools/build_essays_pages.py
"""

from __future__ import annotations

import csv
import html
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.html_footer import (  # noqa: E402
    ROBOTS_INDEX_FOLLOW,
    breadcrumb_html,
    shell_body_class,
    site_page_footer,
    site_page_header,
    site_page_wrap_close,
    site_page_wrap_open,
)
from tools.seo_editorial_chrome import seo_brand_asset_tags, seo_editorial_head_fonts  # noqa: E402
from tools.site_config import brand_name, exam_name, public_url  # noqa: E402

ESSAYS_CSV = ROOT / "data" / "essays.csv"
ESSAYS_DIR = ROOT / "essays"


def _norm(value: str | None) -> str:
    return (value or "").strip()


def load_essays() -> list[dict[str, str]]:
    if not ESSAYS_CSV.is_file():
        return []
    text = ESSAYS_CSV.read_text(encoding="utf-8-sig")
    rows = [r for r in csv.DictReader(text.splitlines()) if _norm(r.get("theme")) or _norm(r.get("question"))]
    return rows


def _theme_cards_html(essays: list[dict[str, str]]) -> str:
    if not essays:
        return (
            '<section class="site-page-section" aria-labelledby="essays-empty">'
            '<h2 id="essays-empty">論述テーマは準備中です</h2>'
            f"<p>{html.escape(exam_name())}の論述対策（テーマ・模範解答・採点キーワード）は順次公開します。"
            "まずは用語解説と過去問で基礎を固めてください。</p>"
            "</section>"
        )
    cards: list[str] = []
    for row in essays:
        theme = html.escape(_norm(row.get("theme")) or _norm(row.get("question")))
        category = html.escape(_norm(row.get("category")))
        cards.append(
            '<article class="site-page-card">'
            + (f'<span class="site-page-card-tag">{category}</span>' if category else "")
            + f"<h2>{theme}</h2>"
            + "</article>"
        )
    return (
        '<section class="site-page-section" aria-labelledby="essays-list">'
        '<h2 id="essays-list">論述テーマ一覧</h2>'
        '<div class="site-page-card-grid">' + "\n".join(cards) + "</div>"
        "</section>"
    )


def build_index_html(essays: list[dict[str, str]]) -> str:
    rel_path = Path("essays/index.html")
    canonical = public_url("essays/index.html")
    title = f"論述対策｜{brand_name()}（{exam_name()}）"
    desc = f"{exam_name()}の論述式（記述）対策。テーマ・考え方・採点キーワードを整理します。"
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
{seo_brand_asset_tags(rel_path)}
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(desc)}">
{ROBOTS_INDEX_FOLLOW}
<link rel="canonical" href="{html.escape(canonical)}">
<meta property="og:type" content="website">
<meta property="og:title" content="{html.escape(title)}">
<meta property="og:description" content="{html.escape(desc)}">
<meta property="og:url" content="{html.escape(canonical)}">
<meta name="twitter:card" content="summary_large_image">
{seo_editorial_head_fonts()}
<link rel="stylesheet" href="../site-pages.css">
<link rel="stylesheet" href="../site-theme.css">
</head>
<body class="{shell_body_class('essays-index-page')}">
{site_page_wrap_open()}
{site_page_header(rel_path, current="essays")}
<main class="site-page-main">
  {breadcrumb_html(rel_path, [("トップ", "index.html"), ("論述対策", None)])}
  <h1>論述対策</h1>
  <p class="site-page-lead">{html.escape(exam_name())}は論述式（記述）があります。テーマごとの考え方・構成・採点キーワードを整理していきます。</p>
  {_theme_cards_html(essays)}
</main>
{site_page_footer(rel_path, current="essays")}
{site_page_wrap_close()}
</body>
</html>
"""


def main() -> int:
    if not ESSAYS_CSV.is_file():
        print(f"essays: {ESSAYS_CSV} が無いためスキップ（論述なしの種）")
        return 0
    essays = load_essays()
    ESSAYS_DIR.mkdir(parents=True, exist_ok=True)
    (ESSAYS_DIR / "index.html").write_text(build_index_html(essays), encoding="utf-8")
    print(f"Wrote essays/index.html（論述テーマ {len(essays)} 件）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
