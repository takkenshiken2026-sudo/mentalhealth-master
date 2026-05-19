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


def list_item_html(q: dict, fid: str) -> str:
    num = int(q.get("num") or 0)
    preview = stem_preview(q.get("text", ""))
    static_href = f"y2026/q{num:02d}/index.html"
    search_blob = html.escape(f"第{num}問 {preview}", quote=True)
    return (
        f'<li class="q-year-list-item" data-field="{html.escape(fid)}" '
        f'data-num="{num}" data-search="{search_blob}">'
        f'<a class="q-year-list-link" href="{html.escape(static_href)}">'
        f'<span class="q-year-list-no">第{num}問</span>'
        f'<span class="q-year-list-cat">{html.escape(preview)}</span>'
        f"</a>"
        f'<a class="q-year-list-app-btn" href="../index.html" '
        f'aria-label="第{num}問をアプリで演習">アプリ</a>'
        f"</li>"
    )


def build_html(questions: list[dict], base_url: str) -> str:
    by_field: dict[str, list[dict]] = {}
    for q in questions:
        fid = (q.get("field") or "other").strip()
        by_field.setdefault(fid, []).append(q)
    for fid in by_field:
        by_field[fid].sort(key=lambda x: int(x.get("num") or 0))

    known_ids = {f["id"] for f in fields()}
    field_order = [f["id"] for f in fields()] + sorted(k for k in by_field if k not in known_ids)

    sections: list[str] = []
    for fid in field_order:
        items = by_field.get(fid)
        if not items:
            continue
        links = [list_item_html(q, fid) for q in items]
        sections.append(
            f'<section id="q-index-field-{html.escape(fid)}" '
            f'class="q-index-year-card q-year-section" data-field="{html.escape(fid)}">'
            '<div class="q-index-year-head">'
            f"<h2>{html.escape(field_label(fid))}</h2>"
            f'<span class="q-index-year-count">{len(items)}問</span>'
            f"</div>"
            f'<ol class="q-year-list">{"".join(links)}</ol>'
            f"</section>"
        )

    sections_html = "".join(sections)

    chips: list[str] = []
    filter_chips: list[str] = [
        '<button type="button" class="q-index-filter-chip on" data-field="all">すべて</button>'
    ]
    jump_links: list[str] = []
    for f in fields():
        fid = str(f["id"])
        name = str(f.get("name") or fid)
        count = len(by_field.get(fid, []))
        if not count:
            continue
        chips.append(
            f'<a class="q-index-chip" href="#q-index-field-{html.escape(fid)}">'
            f"{html.escape(name)}<b>{count}</b></a>"
        )
        filter_chips.append(
            f'<button type="button" class="q-index-filter-chip" data-field="{html.escape(fid)}">'
            f"{html.escape(name)}</button>"
        )
        jump_links.append(
            f'<a class="q-index-jump-link" href="#q-index-field-{html.escape(fid)}">'
            f"{html.escape(name)}</a>"
        )
    chips_html = "".join(chips)
    filter_chips_html = "".join(filter_chips)
    jump_links_html = "".join(jump_links)

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
<link rel="stylesheet" href="../site-pages.css?v=20260520-q-index-ux">
<link rel="stylesheet" href="../site-theme.css">
</head>
<body>
{site_page_wrap_open()}
{site_page_header(rel_path, current="q", wide=True)}
<main class="q-static-main q-index-main">
  {breadcrumb_html(rel_path, [("トップ", "index.html"), ("過去問一覧", None)])}
  <section class="q-index-hero">
    <p class="q-index-kicker">Past Questions</p>
    <h1 class="q-h1">過去問・演習問題一覧</h1>
    <p class="q-index-lead">{html.escape(exam_name())}向けの演習問題を分野別に整理しています。<strong>設問文をクリック</strong>で静的解説へ、<strong><a href="../index.html">アプリ</a></strong>で演習・記録ができます。</p>
    <div class="q-index-stats" aria-label="収録状況">
      <span><b>{total}</b>問</span>
      <span><b>{len(by_field)}</b>分野</span>
    </div>
    <div class="q-index-chips" aria-label="分野へジャンプ">{chips_html}</div>
    <p class="q-index-hero-action"><a href="../index.html">アプリで演習を始める</a></p>
  </section>
  <div class="q-index-toolbar" role="search" aria-label="問題の検索と絞り込み">
    <div class="q-index-toolbar-meta">
      <span class="q-index-pill">全 <span id="q-index-total">{total}</span> 問</span>
      <span class="q-index-pill q-index-pill--hit" id="q-index-hit" hidden></span>
    </div>
    <div class="q-index-search">
      <label class="visually-hidden" for="q-index-q">問題を検索</label>
      <input id="q-index-q" type="search" inputmode="search" autocomplete="off" placeholder="キーワード・問題番号（例：ストレスチェック、42、第42問）">
    </div>
    <div class="q-index-filter" aria-label="分野で絞り込み">{filter_chips_html}</div>
    <nav class="q-index-jump" aria-label="分野へジャンプ">{jump_links_html}</nav>
  </div>
  <p id="q-index-empty" class="q-index-empty hide" role="status">該当する問題がありません。検索語や分野フィルタを変えてください。</p>
  <section class="q-index-years" aria-label="分野別の問題一覧">
    {sections_html}
  </section>
</main>
{site_page_footer(rel_path, current="q", wide=True)}
{site_page_wrap_close()}
<script>
(() => {{
  const q = document.getElementById('q-index-q');
  const hitEl = document.getElementById('q-index-hit');
  const emptyEl = document.getElementById('q-index-empty');
  const filterBtns = Array.from(document.querySelectorAll('.q-index-filter-chip[data-field]'));
  const sections = Array.from(document.querySelectorAll('.q-year-section[data-field]'));
  let activeField = 'all';
  function norm(s) {{
    return (s || '').toString().trim().toLowerCase();
  }}
  function matchItem(li, query) {{
    if (!query) return true;
    const search = norm(li.dataset.search);
    const num = String(li.dataset.num || '');
    if (search.includes(query)) return true;
    if (query === num || query === `第${{num}}問` || query === `第${{num}}`) return true;
    const digits = query.replace(/\\D/g, '');
    return Boolean(digits && num === digits);
  }}
  function apply() {{
    const query = norm(q?.value);
    let shown = 0;
    sections.forEach((sec) => {{
      const fid = sec.dataset.field || '';
      const fieldOk = activeField === 'all' || fid === activeField;
      const items = Array.from(sec.querySelectorAll('.q-year-list-item'));
      let anyInSec = 0;
      items.forEach((li) => {{
        const ok = fieldOk && matchItem(li, query);
        li.classList.toggle('hide', !ok);
        if (ok) {{
          anyInSec++;
          shown++;
        }}
      }});
      sec.classList.toggle('hide', !anyInSec);
    }});
    if (hitEl) {{
      const filtering = Boolean(query) || activeField !== 'all';
      hitEl.hidden = !filtering;
      hitEl.textContent = filtering ? `表示：${{shown}}件` : '';
    }}
    if (emptyEl) {{
      emptyEl.classList.toggle('hide', shown > 0);
    }}
  }}
  q?.addEventListener('input', apply);
  filterBtns.forEach((btn) => {{
    btn.addEventListener('click', () => {{
      filterBtns.forEach((b) => b.classList.remove('on'));
      btn.classList.add('on');
      activeField = btn.dataset.field || 'all';
      apply();
    }});
  }});
  apply();
}})();
</script>
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
