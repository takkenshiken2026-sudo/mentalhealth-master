#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""eisei1-master-data.js の演習問題から q/index.html（一覧）を生成する。"""

from __future__ import annotations

import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.html_footer import (  # noqa: E402
    ROBOTS_INDEX_FOLLOW,
    breadcrumb_html,
    site_page_footer,
    site_page_header,
    site_page_wrap_close,
    site_page_wrap_open,
)
from tools.site_config import brand_name, clean_origin, exam_name, fields

MASTER_JS = ROOT / "eisei1-master-data.js"
OUT = ROOT / "q" / "index.html"
SITEMAP = ROOT / "sitemap.xml"

HEAD_FONTS = """<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;600;700&display=swap" rel="stylesheet">"""


def extract_js_array_literal(src: str, start: int) -> str:
    """文字列内の括弧を無視して配列リテラルの終端を見つける。"""
    if src[start] != "[":
        raise ValueError("配列の開始 '[' が見つかりません")
    depth = 0
    in_string = False
    escape = False
    quote = ""
    for j in range(start, len(src)):
        ch = src[j]
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == quote:
                in_string = False
            continue
        if ch in ('"', "'"):
            in_string = True
            quote = ch
            continue
        if ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
            if depth == 0:
                return src[start : j + 1]
    raise ValueError("配列リテラルが閉じていません")


def extract_questions_array(src: str) -> list[dict]:
    marker = "const CSV_IMPORTED_QUESTIONS = "
    start = src.index(marker) + len(marker)
    while start < len(src) and src[start] in " \t\n\r":
        start += 1
    raw = extract_js_array_literal(src, start)
    raw = re.sub(r",\s*]", "]", raw)
    return json.loads(raw)


def field_label(field_id: str) -> str:
    for f in fields():
        if f.get("id") == field_id:
            return f.get("name", field_id)
    return field_id


def stem_preview(text: str, limit: int = 72) -> str:
    line = (text or "").split("\n")[0].strip()
    line = re.sub(r"\s+", " ", line)
    if len(line) <= limit:
        return line
    return line[: limit - 1] + "…"


def public_url(base: str, rel_path: str) -> str:
    return f"{base.rstrip('/')}/{rel_path.lstrip('/')}"


def ensure_sitemap_entry(url: str) -> None:
    if not SITEMAP.is_file():
        return
    text = SITEMAP.read_text(encoding="utf-8")
    if url in text:
        return
    block = f"""  <url>
    <loc>{html.escape(url)}</loc>
    <changefreq>weekly</changefreq>
  </url>
"""
    SITEMAP.write_text(text.replace("</urlset>", block + "</urlset>"), encoding="utf-8")


def build_html(questions: list[dict], base_url: str) -> str:
    by_field: dict[str, list[dict]] = {}
    for q in questions:
        fid = (q.get("field") or "other").strip()
        by_field.setdefault(fid, []).append(q)
    for fid in by_field:
        by_field[fid].sort(key=lambda x: int(x.get("num") or 0))

    known_ids = {f["id"] for f in fields()}
    field_order = [f["id"] for f in fields()] + sorted(k for k in by_field if k not in known_ids)

    category_counts: dict[str, int] = {}
    for fid, items in by_field.items():
        category_counts[field_label(fid)] = len(items)

    sections: list[str] = []
    for fid in field_order:
        items = by_field.get(fid)
        if not items:
            continue
        links = []
        for q in items:
            num = int(q.get("num") or 0)
            preview = stem_preview(q.get("text", ""))
            static_href = f"y2026/q{num:02d}/index.html"
            links.append(
                "<li>"
                f'<a href="{html.escape(static_href)}">'
                f'<span class="q-year-list-no">第{num}問</span>'
                f'<span class="q-year-list-cat">{html.escape(preview)}</span>'
                "</a>"
                f' <span class="q-year-list-app">(<a href="../index.html">アプリ</a>)</span>'
                "</li>"
            )
        sections.append(
            f'<section class="q-index-year-card q-year-section">'
            f'<motion.div class="q-index-year-head">'
            f"<h2>{html.escape(field_label(fid))}</h2>"
            f"<span>{len(items)}問</span>"
            f"</div>"
            f'<ol class="q-year-list">{"".join(links)}</ol>'
            f"</section>"
        )

    # fix accidental motion tag
    sections_html = (
        "".join(sections)
        .replace("<motion.div class=", "<motion.div class=")
        .replace("<motion.div", "<div")
        .replace("</motion.div>", "</div>")
    )

    chips = "".join(
        f'<span class="q-index-chip">{html.escape(cat)}<b>{count}</b></span>'
        for cat, count in sorted(category_counts.items())
    )

    rel_path = Path("q/index.html")
    total = len(questions)
    desc = (
        f"{exam_name()}の演習問題・過去問を分野別に一覧します。"
        f"全{total}問。アプリでは年度・分野の絞り込みや学習記録が使えます。"
    )

    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>過去問・演習問題一覧｜{html.escape(brand_name())}</title>
<meta name="description" content="{html.escape(desc)}">
{ROBOTS_INDEX_FOLLOW}
<link rel="canonical" href="{html.escape(public_url(base_url, "q/index.html"))}">
<meta property="og:type" content="website">
<meta property="og:title" content="過去問・演習問題一覧｜{html.escape(brand_name())}">
<meta property="og:description" content="{html.escape(desc)}">
<meta property="og:url" content="{html.escape(public_url(base_url, "q/index.html"))}">
{HEAD_FONTS}
<link rel="stylesheet" href="../site-pages.css">
<link rel="stylesheet" href="../site-theme.css">
</head>
<body>
{site_page_wrap_open()}
{site_page_header(rel_path, current="q")}
<main class="q-static-main">
  {breadcrumb_html(rel_path, [("トップ", "index.html"), ("過去問一覧", None)])}
  <section class="q-index-hero">
    <p class="q-index-kicker">Past Questions</p>
    <h1 class="q-h1">過去問・演習問題一覧</h1>
    <p class="q-index-lead">{html.escape(exam_name())}向けの演習問題を分野別に整理しています。各問の<strong>静的解説ページ</strong>（設問・解説）と<strong><a href="../index.html">学習アプリ</a></strong>（記録・絞り込み）の両方を利用できます。</p>
    <div class="q-index-stats" aria-label="収録状況">
      <span><b>{total}</b>問</span>
      <span><b>{len(by_field)}</b>分野</span>
    </div>
    <div class="q-index-chips" aria-label="分野別件数">{chips}</div>
    <p class="q-index-hero-action"><a href="../index.html">アプリで演習を始める</a></p>
  </section>
  <section class="q-index-years" aria-label="分野別の問題一覧">
    {sections_html}
  </section>
</main>
{site_page_footer(rel_path, current="q")}
{site_page_wrap_close()}
</body>
</html>
"""


def main() -> int:
    if not MASTER_JS.is_file():
        print(f"skip: {MASTER_JS} not found", file=sys.stderr)
        return 1
    questions = extract_questions_array(MASTER_JS.read_text(encoding="utf-8"))
    base = clean_origin()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(build_html(questions, base), encoding="utf-8")
    ensure_sitemap_entry(public_url(base, "q/index.html"))
    print(f"Wrote {OUT} ({len(questions)} questions)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
