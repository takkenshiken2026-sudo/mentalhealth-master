#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""論述対策ページを生成する（hasEssay の種のみ）。

I種（master）など論述式のある種は navigation に「論述対策」(essays/index.html) を持つ。
本モジュールは data/essays.csv を読み、

  1. 論述テーマ一覧ハブ        essays/index.html
  2. テーマごとの自己採点ページ essays/<slug>/index.html

を生成する。論述は自由記述のため自動採点はできない。そこで各ページは
「設問 → 自分で答案を書く → 採点キーワード（チェックリスト＋配点）で自己採点
→ 模範解答・解説で確認」という自己採点（セルフチェック）型で構成する。

CSV が空（骨組み段階）のときはハブに「準備中」の導入だけを出す。
II種のように data/essays.csv が無い種では build_all から呼ばれても何もしない
（build_all 側で essays.csv の有無を見てから呼ぶ）。

CSV 列:
    essay_no, theme, category, question, model_answer,
    scoring_keywords, points_allocation, explanation

  - question / model_answer / explanation は段落を空行（または \\n）で区切れる。
  - scoring_keywords は「観点=配点」を全角｜または半角 | で区切る
    （配点を省くと配点なしのチェック項目として扱う）。
  - points_allocation は配点の総括（例: 合計10点）。空なら採点キーワードから自動合算。

使い方:
    python3 tools/build_essays_pages.py
"""

from __future__ import annotations

import csv
import html
import re
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


# ---- 相対パス（ページの深さに応じた ../ の数）---------------------------------

def _rel_prefix(rel_path: Path) -> str:
    """rel_path（ROOT 相対）から見たサイトルートへの ../ 連結。"""
    depth = len(rel_path.parent.parts)
    return "".join(["../"] * depth) if depth else ""


# ---- テキスト整形 ------------------------------------------------------------

def _paragraphs(text: str) -> str:
    """空行（または \\n）区切りのプレーンテキストを <p> 段落にする。"""
    blocks = re.split(r"\n\s*\n|\\n\s*\\n", _norm(text))
    out: list[str] = []
    for block in blocks:
        block = block.replace("\\n", "\n").strip()
        if not block:
            continue
        safe = "<br>".join(html.escape(line) for line in block.splitlines() if line.strip())
        if safe:
            out.append(f"<p>{safe}</p>")
    return "\n".join(out)


def parse_scoring_keywords(raw: str) -> list[tuple[str, int | None]]:
    """「観点=配点｜観点=配点」をパースして (label, points|None) のリストにする。"""
    items: list[tuple[str, int | None]] = []
    for chunk in re.split(r"[｜|]", _norm(raw)):
        chunk = chunk.strip()
        if not chunk:
            continue
        if "=" in chunk:
            label, _, pts = chunk.partition("=")
            label = label.strip()
            pts = pts.strip()
            items.append((label, int(pts) if pts.isdigit() else None))
        else:
            items.append((chunk, None))
    return items


# ---- スラッグ ----------------------------------------------------------------

def essay_slug(row: dict[str, str]) -> str:
    no = _norm(row.get("essay_no"))
    if no.isdigit():
        return f"essay-{int(no):02d}"
    safe = re.sub(r"[^a-z0-9-]+", "-", no.lower()).strip("-")
    return safe or "essay"


# ---- データ ------------------------------------------------------------------

def load_essays() -> list[dict[str, str]]:
    if not ESSAYS_CSV.is_file():
        return []
    text = ESSAYS_CSV.read_text(encoding="utf-8-sig")
    rows = [r for r in csv.DictReader(text.splitlines()) if _norm(r.get("theme")) or _norm(r.get("question"))]
    return rows


# ---- 自己採点ページ用の共通 <style>（テーマ変数を利用、ライト/ダーク両対応）----

ESSAY_STYLE = """
<style>
.essay-detail .essay-block{border:1px solid var(--border);border-radius:var(--r2,12px);padding:1rem 1.15rem;margin:1rem 0;background:var(--bg2);}
.essay-detail .essay-prompt{border-left:4px solid var(--accent);}
.essay-detail .essay-kicker{font-size:.8rem;font-weight:700;letter-spacing:.04em;color:var(--accent-text,var(--accent));margin:0 0 .4rem;}
.essay-detail .essay-howto{color:var(--text2);font-size:.95rem;}
.essay-detail ul.essay-checklist{list-style:none;padding:0;margin:.5rem 0;}
.essay-detail ul.essay-checklist li{display:flex;align-items:flex-start;gap:.6rem;padding:.55rem .2rem;border-bottom:1px solid var(--border);}
.essay-detail ul.essay-checklist li:last-child{border-bottom:none;}
.essay-detail ul.essay-checklist input{margin-top:.25rem;width:1.1rem;height:1.1rem;flex:0 0 auto;accent-color:var(--accent);}
.essay-detail .essay-point{margin-left:auto;flex:0 0 auto;font-weight:700;color:var(--accent-text,var(--accent));white-space:nowrap;}
.essay-detail .essay-score{font-weight:700;margin-top:.6rem;}
.essay-detail details.essay-reveal{margin:1rem 0;border:1px solid var(--border);border-radius:var(--r2,12px);background:var(--bg2);}
.essay-detail details.essay-reveal>summary{cursor:pointer;padding:.85rem 1.15rem;font-weight:700;list-style:none;}
.essay-detail details.essay-reveal>summary::-webkit-details-marker{display:none;}
.essay-detail details.essay-reveal>summary::before{content:"▶ ";color:var(--accent);}
.essay-detail details.essay-reveal[open]>summary::before{content:"▼ ";}
.essay-detail details.essay-reveal>.essay-reveal-body{padding:0 1.15rem 1rem;}
.essay-detail .essay-nav{margin:1.5rem 0;}
</style>
"""

ESSAY_SCORE_JS = """
<script>
(function(){
  var root=document.querySelector('.essay-checklist');
  var out=document.getElementById('essay-score-now');
  if(!root||!out)return;
  var boxes=root.querySelectorAll('input[type=checkbox][data-pt]');
  function recalc(){var s=0;boxes.forEach(function(b){if(b.checked)s+=parseInt(b.getAttribute('data-pt'),10)||0;});out.textContent=s;}
  boxes.forEach(function(b){b.addEventListener('change',recalc);});
  recalc();
})();
</script>
"""


# ---- ハブ --------------------------------------------------------------------

def _theme_cards_html(essays: list[dict[str, str]]) -> str:
    if not essays:
        return (
            '<section class="site-page-section" aria-labelledby="essays-empty">'
            '<h2 id="essays-empty">論述テーマは準備中です</h2>'
            f"<p>{html.escape(exam_name())}の論述対策（テーマ・模範解答・採点キーワード）は順次公開します。"
            "まずは用語解説と過去問で基礎を固めてください。</p>"
            "</section>"
        )
    items: list[str] = []
    for row in essays:
        slug = essay_slug(row)
        theme = html.escape(_norm(row.get("theme")) or _norm(row.get("question"))[:40])
        category = html.escape(_norm(row.get("category")))
        tag = f'<span class="essay-kicker">{category}</span>' if category else ""
        items.append(
            f'<li class="essay-block"><a href="{html.escape(slug)}/">'
            f"{tag}<strong>{theme}</strong></a></li>"
        )
    return (
        '<section class="site-page-section essay-detail" aria-labelledby="essays-list">'
        '<h2 id="essays-list">論述テーマ一覧</h2>'
        '<p class="essay-howto">各テーマは「設問 → 自分で答案を書く → 採点キーワードで自己採点 → '
        "模範解答・解説で確認」の順で学べます。</p>"
        '<ul class="essay-checklist" style="list-style:none">' + "\n".join(items) + "</ul>"
        "</section>"
    )


def build_index_html(essays: list[dict[str, str]]) -> str:
    rel_path = Path("essays/index.html")
    canonical = public_url("essays/index.html")
    pre = _rel_prefix(rel_path)
    title = f"論述対策｜{brand_name()}（{exam_name()}）"
    desc = f"{exam_name()}の論述式（記述）対策。テーマ・模範解答・採点キーワードで自己採点できます。"
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
<link rel="stylesheet" href="{pre}site-pages.css">
<link rel="stylesheet" href="{pre}site-theme.css">
{ESSAY_STYLE}</head>
<body class="{shell_body_class('essays-index-page')}">
{site_page_wrap_open()}
{site_page_header(rel_path, current="essays")}
<main class="site-page-main">
  {breadcrumb_html(rel_path, [("トップ", "index.html"), ("論述対策", None)])}
  <h1>論述対策</h1>
  <p class="site-page-lead">{html.escape(exam_name())}は論述式（記述）があります。論述は自由記述のため自動採点はできませんが、採点キーワード（観点）と配点で自分の答案を自己採点できるようにまとめています。</p>
  {_theme_cards_html(essays)}
</main>
{site_page_footer(rel_path, current="essays")}
{site_page_wrap_close()}
</body>
</html>
"""


# ---- 個別（自己採点）ページ --------------------------------------------------

def _checklist_html(items: list[tuple[str, int | None]]) -> tuple[str, int]:
    lis: list[str] = []
    total = 0
    for i, (label, pts) in enumerate(items):
        pt_attr = f' data-pt="{pts}"' if pts is not None else ""
        pt_text = f'<span class="essay-point">{pts}点</span>' if pts is not None else ""
        if pts is not None:
            total += pts
        cid = f"ck{i}"
        lis.append(
            f'<li><input type="checkbox" id="{cid}"{pt_attr}>'
            f'<label for="{cid}">{html.escape(label)}</label>{pt_text}</li>'
        )
    return "\n".join(lis), total


def build_detail_html(row: dict[str, str], *, prev_slug: str | None, next_slug: str | None) -> str:
    slug = essay_slug(row)
    rel_path = Path("essays") / slug / "index.html"
    canonical = public_url(f"essays/{slug}/index.html")
    pre = _rel_prefix(rel_path)
    theme = _norm(row.get("theme")) or _norm(row.get("question"))[:40]
    category = _norm(row.get("category"))
    question = _norm(row.get("question"))
    model_answer = _norm(row.get("model_answer"))
    explanation = _norm(row.get("explanation"))
    points_alloc = _norm(row.get("points_allocation"))

    kw_items = parse_scoring_keywords(row.get("scoring_keywords", ""))
    checklist, kw_total = _checklist_html(kw_items)
    total_label = points_alloc or (f"合計{kw_total}点" if kw_total else "")

    title = f"論述演習：{theme}｜{brand_name()}（{exam_name()}）"
    desc = f"{exam_name()}の論述演習「{theme}」。設問・採点キーワード・模範解答で自己採点できます。"

    cat_tag = f'<p class="essay-kicker">{html.escape(category)}</p>' if category else ""

    # 採点キーワード節
    if checklist:
        score_now = (
            f'<p class="essay-score">自己採点：<span id="essay-score-now">0</span> / '
            f'{kw_total}点</p>' if kw_total else ""
        )
        scoring_section = (
            '<section class="site-page-section essay-detail" aria-labelledby="scoring">'
            '<h2 id="scoring">採点キーワード（自己採点チェック）</h2>'
            '<p class="essay-howto">答案に次の観点を盛り込めたらチェックを入れてください。'
            "本番でも観点ごとに加点される考え方です。</p>"
            f'<ul class="essay-checklist">{checklist}</ul>'
            f"{score_now}"
            + (f'<p class="essay-howto">配点の目安：{html.escape(total_label)}</p>' if total_label else "")
            + "</section>"
        )
    else:
        scoring_section = ""

    model_section = (
        '<details class="essay-reveal essay-detail"><summary>模範解答を見る（まず自分で書いてから）</summary>'
        f'<div class="essay-reveal-body">{_paragraphs(model_answer)}</div></details>'
        if model_answer else ""
    )
    explanation_section = (
        '<details class="essay-reveal essay-detail"><summary>解説・書き方のポイント</summary>'
        f'<div class="essay-reveal-body">{_paragraphs(explanation)}</div></details>'
        if explanation else ""
    )

    nav_bits = ['<a href="../">← 論述テーマ一覧へ戻る</a>']
    if prev_slug:
        nav_bits.append(f'<a href="../{html.escape(prev_slug)}/">前のテーマ</a>')
    if next_slug:
        nav_bits.append(f'<a href="../{html.escape(next_slug)}/">次のテーマ</a>')
    nav_html = '<p class="essay-nav">' + "　|　".join(nav_bits) + "</p>"

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
<meta property="og:type" content="article">
<meta property="og:title" content="{html.escape(title)}">
<meta property="og:description" content="{html.escape(desc)}">
<meta property="og:url" content="{html.escape(canonical)}">
<meta name="twitter:card" content="summary_large_image">
{seo_editorial_head_fonts()}
<link rel="stylesheet" href="{pre}site-pages.css">
<link rel="stylesheet" href="{pre}site-theme.css">
{ESSAY_STYLE}</head>
<body class="{shell_body_class('essays-detail-page')}">
{site_page_wrap_open()}
{site_page_header(rel_path, current="essays")}
<main class="site-page-main essay-detail">
  {breadcrumb_html(rel_path, [("トップ", pre + "index.html"), ("論述対策", "../"), (theme, None)])}
  {cat_tag}
  <h1>{html.escape(theme)}</h1>
  <p class="site-page-lead">論述は自由記述のため自動採点はできません。まず設問に対して自分で答案を書き、下の採点キーワードで自己採点してから模範解答で確認しましょう。</p>

  <section class="site-page-section" aria-labelledby="prompt">
    <h2 id="prompt">設問</h2>
    <div class="essay-block essay-prompt">{_paragraphs(question)}</div>
    <p class="essay-howto">まずは解答用紙やメモに、自分の言葉で答案を書いてみてください。</p>
  </section>

  {scoring_section}
  {model_section}
  {explanation_section}
  {nav_html}
</main>
{ESSAY_SCORE_JS}{site_page_footer(rel_path, current="essays")}
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

    slugs = [essay_slug(r) for r in essays]
    for i, row in enumerate(essays):
        slug = slugs[i]
        prev_slug = slugs[i - 1] if i > 0 else None
        next_slug = slugs[i + 1] if i + 1 < len(slugs) else None
        out_dir = ESSAYS_DIR / slug
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "index.html").write_text(
            build_detail_html(row, prev_slug=prev_slug, next_slug=next_slug), encoding="utf-8"
        )
    print(f"Wrote essays/index.html + {len(essays)} detail page(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
