#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
data/past_questions.csv から静的問題ページ q/past/... を生成し、
q/index.html・sitemap.xml・robots.txt を更新する。
"""

from __future__ import annotations

import csv
import html
import json
import re
import shutil
import sys
from pathlib import Path
from xml.sax.saxutils import escape as xml_escape

ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.html_footer import (
    ROBOTS_INDEX_FOLLOW,
    breadcrumb_html,
    site_page_footer,
    site_page_header,
    site_page_wrap_close,
    site_page_wrap_open,
    static_footer_block,
    static_site_header,
)
from tools.site_config import brand_name, clean_origin, exam_name
from tools.sitemap_utils import collect_sitemap_urls, write_sitemap

DATA_CSV = ROOT / "data" / "past_questions.csv"
Q_ROOT = ROOT / "q"
BASE_DEFAULT = clean_origin()
HEAD_FONTS = """<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;600;700&display=swap" rel="stylesheet">"""

LABELS = [("ア", "statement_a"), ("イ", "statement_b"), ("ウ", "statement_c"), ("エ", "statement_d")]


def norm(s: str | None) -> str:
    return (s or "").strip()


def parse_correct(raw: str) -> int | None:
    raw = norm(raw)
    if not raw:
        return None
    try:
        n = int(raw)
    except ValueError:
        return None
    if 1 <= n <= 5:
        return n
    return None


def build_stem_html(row: dict) -> str:
    parts: list[str] = []
    stem = norm(row.get("stem"))
    preamble = norm(row.get("preamble"))
    br = "<br>\n"
    if stem:
        parts.append(f"<p>{html.escape(stem).replace(chr(10), br)}</p>")
    if preamble:
        parts.append(f"<p>{html.escape(preamble).replace(chr(10), br)}</p>")
    stmts: list[tuple[str, str]] = []
    for lab, key in LABELS:
        t = norm(row.get(key))
        if t:
            stmts.append((lab, t))
    if stmts:
        lis = "".join(
            f"<li><strong>{html.escape(lab)}</strong> {html.escape(t).replace(chr(10), br)}</li>"
            for lab, t in stmts
        )
        parts.append(f'<ol class="q-stmt-list" style="list-style:none;padding-left:0;">{lis}</ol>')
    return "\n".join(parts) if parts else "<p>（問題文なし）</p>"


def meta_description(text: str, limit: int = 155) -> str:
    one = re.sub(r"\s+", " ", text).strip()
    if len(one) <= limit:
        return one
    return one[: limit - 1] + "…"


def rel_to_root(rel_file: Path) -> str:
    depth = len(rel_file.parent.parts)
    return "/".join([".."] * depth) + "/index.html"


def rel_to_q_index(rel_file: Path) -> str:
    """q/past/.../index.html から q/index.html へ"""
    depth = len(rel_file.parent.parts)
    up = max(depth - 1, 1)
    return "/".join([".."] * up) + "/index.html"


def rel_css(rel_file: Path) -> str:
    depth = len(rel_file.parent.parts)
    return "/".join([".."] * depth) + "/site-pages.css?v=20260518-qwide"


def rel_theme_css(rel_file: Path) -> str:
    depth = len(rel_file.parent.parts)
    return "/".join([".."] * depth) + "/site-theme.css"


def public_url(base: str, rel_path: str) -> str:
    return f"{base.rstrip('/')}/{rel_path.lstrip('/')}"


def load_rows() -> list[dict]:
    text = DATA_CSV.read_text(encoding="utf-8-sig")
    return list(csv.DictReader(text.splitlines()))


def page_dict(row: dict, line_no: int) -> dict:
    year = int(row["exam_year"])
    qno = int(row["question_no"])
    opts = [norm(row.get(f"choice_{i}")) for i in range(1, 6) if norm(row.get(f"choice_{i}"))]
    if not all(opts):
        raise ValueError(f"line {line_no}: 選択肢欠け {year}-{qno}")
    inv = norm(row.get("is_invalidated", "")).upper() == "TRUE"
    cor = parse_correct(row.get("correct"))
    if cor is None and not inv:
        raise ValueError(f"line {line_no}: 正答なし {year}-{qno}")
    wareki = norm(row.get("exam_wareki"))
    cat = norm(row.get("category"))
    typ = norm(row.get("type")) or "single"
    stem_plain = norm(row.get("stem"))
    exp = norm(row.get("explanation")) or "（解説は未入力です。）"
    return {
        "year": year,
        "qno": qno,
        "wareki": wareki,
        "category": cat,
        "type": typ,
        "stem_html": build_stem_html(row),
        "stem_plain": stem_plain,
        "opts": opts,
        "correct": cor,
        "is_exempt": norm(row.get("is_exempt", "")).upper() == "TRUE",
        "is_invalidated": inv,
        "note": norm(row.get("note")),
        "exp": exp,
        "id": f"past-{year}-{qno:02d}",
        "rel_path": f"q/past/y{year}/q{qno:02d}/index.html",
    }


def build_question_html(page: dict, rel_path: Path, base_url: str) -> str:
    title_mid = f"{page['wareki']} 第{page['qno']}問・{page['category']}"
    title = f"{title_mid}｜{brand_name()}（{exam_name()}）"
    desc = meta_description(page["stem_plain"] or page["category"])
    canonical = public_url(base_url, page["rel_path"])
    root_idx = rel_to_root(rel_path)
    css_href = rel_css(rel_path)
    theme_href = rel_theme_css(rel_path)

    opts_html = "".join(
        f'<li class="q-opt"><span class="q-opt-num">（{i}）</span> {html.escape(o)}</li>'
        for i, o in enumerate(page["opts"], start=1)
    )

    if page["is_invalidated"] or page["correct"] is None:
        ans_block = (
            "<p>本問は試験上「出題無効」となった年度があります（"
            + html.escape(page["note"] or "公式の扱いを確認してください")
            + "）。学習用に選択肢のみ掲載します。</p>"
        )
    else:
        ans_block = f'<p>正答は <strong>（{page["correct"]}）</strong> です。</p>'

    badges = []
    if page["is_exempt"]:
        badges.append('<span class="q-badge">試験免除出題</span>')
    if page["is_invalidated"]:
        badges.append('<span class="q-badge q-badge-warn">出題無効</span>')
    badge_html = ("<p class=\"q-badges\">" + " ".join(badges) + "</p>") if badges else ""

    exp_html = html.escape(page["exp"]).replace("\n", "<br>\n")

    json_ld = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "WebPage",
                "@id": canonical + "#webpage",
                "url": canonical,
                "name": title,
                "description": desc,
                "inLanguage": "ja-JP",
            },
            {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "トップ", "item": public_url(base_url, "index.html")},
                    {"@type": "ListItem", "position": 2, "name": "過去問一覧", "item": public_url(base_url, "q/index.html")},
                    {"@type": "ListItem", "position": 3, "name": title_mid, "item": canonical},
                ],
            },
        ],
    }

    site_header = site_page_header(
        rel_path,
        current="q",
    )
    site_breadcrumb = breadcrumb_html(
        rel_path,
        [("トップ", "index.html"), ("過去問一覧", "q/index.html"), (title_mid, None)],
    )
    site_footer = site_page_footer(rel_path, current="q")

    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(desc)}">
{ROBOTS_INDEX_FOLLOW}
<link rel="canonical" href="{html.escape(canonical)}">
<meta property="og:type" content="article">
<meta property="og:title" content="{html.escape(title)}">
<meta property="og:description" content="{html.escape(desc)}">
<meta property="og:url" content="{html.escape(canonical)}">
<meta name="twitter:card" content="summary">
{HEAD_FONTS}
<link rel="stylesheet" href="{html.escape(css_href)}">
<link rel="stylesheet" href="{html.escape(theme_href)}">
<script type="application/ld+json">
{json.dumps(json_ld, ensure_ascii=False, indent=2)}
</script>
</head>
<body>
{site_page_wrap_open()}
{site_header}
<main class="q-static-main">
  {site_breadcrumb}
  <p class="q-meta"><span class="q-id">ID: <code>{html.escape(page["id"])}</code></span> · <span>{html.escape(page["category"])}</span> · <span>{html.escape(page["type"])}</span></p>
  {badge_html}
  <h1 class="q-h1">{html.escape(title_mid)}</h1>
  <section class="q-block" aria-labelledby="q-stem-h">
    <h2 id="q-stem-h" class="q-h2">問題</h2>
    <div class="q-stem">{page["stem_html"]}</div>
  </section>
  <section class="q-block" aria-labelledby="q-opts-h">
    <h2 id="q-opts-h" class="q-h2">選択肢</h2>
    <ol class="q-opts">
      {opts_html}
    </ol>
  </section>
  <section class="q-block q-answer" aria-labelledby="q-ans-h">
    <h2 id="q-ans-h" class="q-h2">正答</h2>
    {ans_block}
  </section>
  <section class="q-block" aria-labelledby="q-exp-h">
    <h2 id="q-exp-h" class="q-h2">解説</h2>
    <div class="q-exp">{exp_html}</div>
  </section>
  <p class="q-app-link"><a href="{html.escape(root_idx)}">アプリで演習する</a></p>
</main>
{site_footer}
{site_page_wrap_close()}
</body>
</html>
"""


def build_q_index(pages: list[dict], base_url: str) -> str:
    by_year: dict[int, list[dict]] = {}
    by_category: dict[str, int] = {}
    for p in pages:
        by_year.setdefault(p["year"], []).append(p)
        by_category[p["category"]] = by_category.get(p["category"], 0) + 1
    for y in by_year:
        by_year[y].sort(key=lambda x: x["qno"])

    year_blocks = []
    for y in sorted(by_year.keys()):
        links = []
        for p in by_year[y]:
            rel = p["rel_path"]
            href = rel[2:] if rel.startswith("q/") else rel
            label = f"第{p['qno']}問"
            links.append(
                '<li>'
                f'<a href="{html.escape(href)}">'
                f'<span class="q-year-list-no">{html.escape(label)}</span>'
                f'<span class="q-year-list-cat">{html.escape(p["category"])}</span>'
                '</a>'
                '</li>'
            )
        heading = by_year[y][0]["wareki"] if y > 9999 else f"{y}年（{by_year[y][0]['wareki']}）"
        year_blocks.append(
            f'<section class="q-index-year-card"><div class="q-index-year-head"><h2>{html.escape(heading)}</h2>'
            f'<span>{len(by_year[y])}問</span></div>'
            f'<ol class="q-year-list">{"".join(links)}</ol></section>'
        )

    category_chips = "".join(
        f'<span class="q-index-chip">{html.escape(cat)}<b>{count}</b></span>'
        for cat, count in sorted(by_category.items())
    )
    year_count = len(by_year)

    rel_path = Path("q/index.html")
    q_index_header = site_page_header(
        rel_path,
        current="q",
    )
    q_index_breadcrumb = breadcrumb_html(rel_path, [("トップ", "index.html"), ("過去問一覧", None)])
    q_index_footer = site_page_footer(rel_path, current="q")

    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>過去問一覧｜{html.escape(brand_name())}（{html.escape(exam_name())}）</title>
<meta name="description" content="{html.escape(exam_name())}の過去問を年度別に一覧するページです。">
{ROBOTS_INDEX_FOLLOW}
<link rel="canonical" href="{html.escape(public_url(base_url, "q/index.html"))}">
{HEAD_FONTS}
<link rel="stylesheet" href="../site-pages.css?v=20260518-qwide">
<link rel="stylesheet" href="../site-theme.css">
</head>
<body>
{site_page_wrap_open()}
{q_index_header}
<main class="q-static-main">
  {q_index_breadcrumb}
  <section class="q-index-hero">
    <p class="q-index-kicker">Past Questions</p>
    <h1 class="q-h1">過去問一覧</h1>
    <p class="q-index-lead">{html.escape(exam_name())}の過去問を年度別に整理しています。静的ページで確認し、アプリでは年度・分野の絞り込みや学習記録を使えます。</p>
    <div class="q-index-stats" aria-label="過去問の収録状況">
      <span><b>{len(pages)}</b>問</span>
      <span><b>{year_count}</b>年度</span>
      <span><b>{len(by_category)}</b>分野</span>
    </div>
    <div class="q-index-chips" aria-label="分野別件数">{category_chips}</div>
    <p class="q-index-hero-action"><a href="../index.html#past">アプリで過去問を開く</a></p>
  </section>
  <section class="q-index-years" aria-label="年度別過去問">
    {"".join(year_blocks)}
  </section>
</main>
{q_index_footer}
{site_page_wrap_close()}
</body>
</html>
"""


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default=BASE_DEFAULT)
    args = ap.parse_args()
    base = args.base_url.rstrip("/")

    rows = load_rows()
    pages = [page_dict(r, i) for i, r in enumerate(rows, start=2)]

    past_root = Q_ROOT / "past"
    if past_root.is_dir():
        shutil.rmtree(past_root)
    past_root.mkdir(parents=True, exist_ok=True)
    for p in pages:
        rel = Path(p["rel_path"])
        out_file = ROOT / rel
        out_file.parent.mkdir(parents=True, exist_ok=True)
        html_out = build_question_html(p, out_file.relative_to(ROOT), base)
        out_file.write_text(html_out, encoding="utf-8")

    write_sitemap(collect_sitemap_urls(base), ROOT / "sitemap.xml")

    robots = ROOT / "robots.txt"
    robots.write_text(
        "User-agent: *\nAllow: /\n\nSitemap: "
        + f"{base}/sitemap.xml\n",
        encoding="utf-8",
    )

    print(f"Wrote {len(pages)} question pages under {past_root}")
    print(f"Updated {ROOT / 'sitemap.xml'} (run build_q_index_from_master.py for q/index.html)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
