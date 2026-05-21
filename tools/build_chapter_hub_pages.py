#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""出題範囲7章のハブページ articles/chapters/*/index.html を生成する。"""

from __future__ import annotations

import csv
import html
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.html_footer import (  # noqa: E402
    breadcrumb_html,
    footer_href,
    site_page_footer,
    site_page_header,
    site_page_wrap_close,
    site_page_wrap_open,
)
from tools.site_config import brand_name, clean_origin, exam_name

GLOSSARY_CSV = ROOT / "data" / "glossary_terms.csv"
OUT_ROOT = ROOT / "articles" / "chapters"
BASE_DEFAULT = clean_origin()

HEAD_FONTS = """<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;600;700&display=swap" rel="stylesheet">"""

CHAPTERS = [
    {
        "slug": "chapter-01-role",
        "title": "第1章 メンタルヘルスケアの意義と管理監督者の役割",
        "summary": "メンタルヘルスケアの目的、管理監督者の役割、4つのケア、安全配慮などの基盤を学ぶ章です。",
        "keywords": ["管理監督者", "4つのケア", "安全配慮", "ラインケア", "心の健康づくり", "パワーハラスメント", "ストレスチェック", "過重労働"],
    },
    {
        "slug": "chapter-02-stress-basics",
        "title": "第2章 ストレスおよびメンタルヘルスに関する基礎知識",
        "summary": "ストレス反応、疾病、職業性ストレス、うつ病、発達障害などの基礎知識を学ぶ章です。",
        "keywords": ["ストレス", "うつ", "セリエ", "NIOSH", "コルチゾール", "発達障害", "ADHD", "ASD", "障害者雇用"],
    },
    {
        "slug": "chapter-03-workplace-eval",
        "title": "第3章 職場環境等の評価および改善の方法",
        "summary": "ストレス要因の把握、職場環境改善、PDCA、集団分析などを学ぶ章です。",
        "keywords": ["職場環境", "ストレス要因", "判定図", "集団分析", "改善", "PDCA", "ストレスチェック"],
    },
    {
        "slug": "chapter-04-individual-care",
        "title": "第4章 個々の労働者への配慮",
        "summary": "不調のサイン、過重労働防止、サポートの種類、個人情報の取り扱いなどを学ぶ章です。",
        "keywords": ["いつもと違う", "過重労働", "サポート", "個人情報", "要配慮", "管理監督者自身"],
    },
    {
        "slug": "chapter-05-consultation",
        "title": "第5章 労働者からの相談への対応",
        "summary": "傾聴、早期発見、危機対応、相談の基本姿勢を学ぶ章です。",
        "keywords": ["相談", "傾聴", "アクティブ", "自殺", "危機", "早期", "話を聴く"],
    },
    {
        "slug": "chapter-06-resources",
        "title": "第6章 社内外資源との連携",
        "summary": "産業保健スタッフ、EAP、外部相談機関などとの連携を学ぶ章です。",
        "keywords": ["産業医", "保健師", "EAP", "外部", "相談機関", "いのちの電話", "こころの耳", "NPO"],
    },
    {
        "slug": "chapter-07-return-to-work",
        "title": "第7章 心の健康問題をもつ復職者への支援",
        "summary": "休職・復職プロセス、復職支援プラン、フォローアップを学ぶ章です。",
        "keywords": ["復職", "休職", "プラン", "フォロー", "ステップ", "主治医"],
    },
]


def norm(s: str | None) -> str:
    return (s or "").strip()


def load_terms() -> list[dict]:
    rows = list(csv.DictReader(GLOSSARY_CSV.read_text(encoding="utf-8-sig").splitlines()))
    out = []
    for row in rows:
        term = norm(row.get("term"))
        if not term:
            continue
        out.append(
            {
                "term": term,
                "url_slug": norm(row.get("url_slug")) or "index",
                "blob": " ".join(
                    [
                        term,
                        norm(row.get("short_def")),
                        norm(row.get("explanation"))[:400],
                        norm(row.get("category")),
                    ]
                ),
            }
        )
    return out


def terms_for_chapter(ch: dict, terms: list[dict], limit: int = 40) -> list[dict]:
    picked: list[dict] = []
    for t in terms:
        blob = t["blob"]
        if any(kw in blob for kw in ch["keywords"]):
            picked.append(t)
    if len(picked) < 8:
        for t in terms:
            if t not in picked:
                picked.append(t)
            if len(picked) >= limit:
                break
    return picked[:limit]


def rel_css(rel_file: Path) -> str:
    depth = len(rel_file.parent.parts)
    return "/".join([".."] * depth) + "/site-pages.css?v=20260519-chapters"


def rel_theme_css(rel_file: Path) -> str:
    depth = len(rel_file.parent.parts)
    return "/".join([".."] * depth) + "/site-theme.css"


def public_url(base: str, rel_path: str) -> str:
    return f"{base.rstrip('/')}/{rel_path.lstrip('/')}"


def build_hub(ch: dict, terms: list[dict], rel_path: Path, base: str) -> str:
    rel = rel_path.as_posix()
    canonical = public_url(base, rel)
    title = f"{ch['title']}の学習ガイド｜{brand_name()}"
    desc = ch["summary"] + f" {exam_name()}の出題範囲に沿って用語と演習へ進めます。"
    chapter_terms = terms_for_chapter(ch, terms)
    term_lis = "\n".join(
        f'      <li><a href="{html.escape(footer_href(rel_path, "terms/" + t["url_slug"] + "/index.html"))}">{html.escape(t["term"])}</a></li>'
        for t in chapter_terms
    )
    q_index = footer_href(rel_path, "q/index.html")
    subjects = footer_href(rel_path, "articles/subjects/index.html")
    terms_index = footer_href(rel_path, "terms/index.html")
    study_plan = footer_href(rel_path, "articles/study-plan/index.html")
    exam_last = footer_href(rel_path, "articles/exam-last-minute/index.html")
    page_header = site_page_header(rel_path, current="articles")
    page_breadcrumb = breadcrumb_html(
        rel_path,
        [
            ("トップ", "index.html"),
            ("試験ガイド", "articles/index.html"),
            (ch["title"], None),
        ],
    )
    page_footer = site_page_footer(rel_path, current="articles")
    ld = {
        "@context": "https://schema.org",
        "@type": "CollectionPage",
        "name": ch["title"],
        "description": desc,
        "url": canonical,
    }
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(desc)}">
<meta name="robots" content="index, follow">
<link rel="canonical" href="{html.escape(canonical)}">
{HEAD_FONTS}
<link rel="stylesheet" href="{rel_css(rel_path)}">
<link rel="stylesheet" href="{rel_theme_css(rel_path)}">
<script type="application/ld+json">
{json.dumps(ld, ensure_ascii=False, indent=2)}
</script>
</head>
<body class="site-page">
{site_page_wrap_open()}
{page_header}
{page_breadcrumb}
<main class="site-main seo-article-main" id="main">
  <article>
    <h1 class="article-title">{html.escape(ch["title"])}</h1>
    <p class="article-lead">{html.escape(ch["summary"])}</p>
    <section class="seo-article-section">
      <h2>この章で押さえること</h2>
      <p>公式テキストの該当章を読んだあと、下の用語と<a href="{html.escape(q_index)}">演習問題一覧</a>で理解度を確認してください。試験全体の流れは<a href="{html.escape(subjects)}">出題範囲と7章</a>も参照してください。</p>
    </section>
    <section class="seo-article-section">
      <h2>関連用語（{len(chapter_terms)}件）</h2>
      <ul class="terms-idx-list">
{term_lis}
      </ul>
      <p><a href="{html.escape(terms_index)}">用語集一覧へ</a></p>
    </section>
    <section class="seo-action-box">
      <h2>次のステップ</h2>
      <ul>
        <li><a href="{html.escape(q_index)}">分野別の演習問題</a>で選択肢に慣れる</li>
        <li><a href="{html.escape(study_plan)}">学習計画</a>で章の優先順位を決める</li>
        <li><a href="{html.escape(exam_last)}">直前対策チェックリスト</a>で最終確認</li>
      </ul>
    </section>
  </article>
</main>
{page_footer}
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

    terms = load_terms()
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    for ch in CHAPTERS:
        out = OUT_ROOT / ch["slug"] / "index.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        rel = out.relative_to(ROOT)
        out.write_text(build_hub(ch, terms, rel, base), encoding="utf-8")

    index_out = OUT_ROOT / "index.html"
    rel = index_out.relative_to(ROOT)
    canonical = public_url(base, rel.as_posix())
    lis = "\n".join(
        f'      <li><a href="{html.escape(ch["slug"])}/index.html">{html.escape(ch["title"])}</a></li>'
        for ch in CHAPTERS
    )
    page_header = site_page_header(rel, current="articles")
    page_breadcrumb = breadcrumb_html(
        rel,
        [("トップ", "index.html"), ("試験ガイド", "articles/index.html"), ("7章ハブ", None)],
    )
    page_footer = site_page_footer(rel, current="articles")
    subjects_hub = footer_href(rel, "articles/subjects/index.html")
    q_hub = footer_href(rel, "q/index.html")
    index_html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>出題範囲7章ハブ｜{html.escape(brand_name())}</title>
<meta name="description" content="{exam_name()}の出題範囲7章ごとの学習入口。章別に用語と演習問題へ進めます。">
<meta name="robots" content="index, follow">
<link rel="canonical" href="{html.escape(canonical)}">
{HEAD_FONTS}
<link rel="stylesheet" href="{rel_css(rel)}">
<link rel="stylesheet" href="{rel_theme_css(rel)}">
</head>
<body class="site-page">
{site_page_wrap_open()}
{page_header}
{page_breadcrumb}
<main class="site-main seo-article-main" id="main">
  <h1 class="article-title">出題範囲7章ハブ</h1>
  <p class="article-lead">公式テキストの7章に対応する学習入口です。章ごとに用語と演習へ進んでください。</p>
  <ul class="chapter-hub-list">
{lis}
  </ul>
  <p><a href="{html.escape(subjects_hub)}">出題範囲の全体像</a> · <a href="{html.escape(q_hub)}">演習問題一覧</a></p>
</main>
{page_footer}
{site_page_wrap_close()}
</body>
</html>
"""
    index_out.write_text(index_html, encoding="utf-8")

    print(f"Wrote {len(CHAPTERS)} chapter hubs + index under {OUT_ROOT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
