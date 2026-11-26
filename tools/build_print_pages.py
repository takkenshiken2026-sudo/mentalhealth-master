#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""過去問の印刷・PDF保存用ページを生成する（q/print/）。

- q/print/index.html … 印刷用の入口（分野ごとの印刷セットと、予想模試・問題集への導線）。index, follow。
- q/print/field-N/index.html … 分野ごとの印刷ページ（問題編 → 改ページ → 解答編：正解と1行の要点）。
  選択肢ごとの詳しい解説は Web（各問ページ）に残し、紙には載せない。
  内容が過去問一覧・各問ページと重なるため noindex, follow（入口ページを検索の受け皿にする）。

背景: GSC（2026-08〜10）で「過去問 pdf / ダウンロード」系の検索が約2,300表示あり、
1〜2位でもクリック率が同順位帯の半分前後だった（印刷して解きたい需要に応えていなかった）。
PDF ファイルは配らず、ブラウザの印刷機能（「PDFとして保存」を含む）で使う形にする。

過去問が無い種（I種など）では何も生成しない。
"""

from __future__ import annotations

import html
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.build_past_question_pages import (  # noqa: E402
    is_demo_past_question_row,
    load_rows,
    norm,
    page_dict,
    rel_href,
)
from tools.guide_index_picks_ui import build_guide_index_picks_html, guide_index_picks  # noqa: E402
from tools.html_footer import (  # noqa: E402
    ROBOTS_INDEX_FOLLOW,
    ROBOTS_NOINDEX_FOLLOW,
    breadcrumb_html,
    shell_body_class,
    site_page_footer,
    site_page_header,
    site_page_wrap_close,
    site_page_wrap_open,
)
from tools.seo_editorial_chrome import seo_brand_asset_tags  # noqa: E402
from tools.site_config import (  # noqa: E402
    brand_title_suffix,
    excluded_past_exam_years,
    exam_name,
    fields,
    public_url,
)

PRINT_ROOT = ROOT / "q" / "print"
CIRCLED = "①②③④⑤⑥"

PRINT_CSS = """
.print-page .print-body{padding:0 16px;max-width:760px}
.print-page .print-body > ol{padding-left:1.5em;line-height:1.8}
.print-page .print-actions{display:flex;flex-wrap:wrap;gap:10px;margin:14px 0 18px}
.print-page .print-btn{display:inline-block;padding:10px 18px;border-radius:999px;border:0;background:var(--accent);color:#fff;font-weight:700;font-size:.95rem;cursor:pointer;text-decoration:none}
.print-page .print-btn--ghost{background:transparent;color:var(--accent);border:1px solid var(--accent)}
.print-page .print-howto{font-size:.88rem;line-height:1.7;color:var(--text2);margin:0 0 12px}
.print-page .print-sets{list-style:none;padding:0;margin:12px 0 20px;display:grid;gap:10px}
.print-page .print-sets a{display:block;padding:14px 16px;border:1px solid var(--border);border-radius:12px;text-decoration:none;color:var(--text);background:var(--bg)}
.print-page .print-sets a strong{display:block;font-size:1rem}
.print-page .print-sets a span{display:block;font-size:.85rem;color:var(--text2);margin-top:2px}
.print-sheet h2{font-size:1.15rem;margin:26px 0 10px;padding-bottom:6px;border-bottom:2px solid var(--accent)}
.print-q{margin:0 0 18px;break-inside:avoid;page-break-inside:avoid}
.print-q h3{font-size:.95rem;margin:0 0 6px}
.print-q .print-stem p{margin:0 0 6px;line-height:1.7}
.print-q ol.print-choices{list-style:none;padding-left:0;margin:6px 0 0}
.print-q ol.print-choices li{margin:2px 0;line-height:1.6}
.print-q .print-answer-box{margin-top:6px;font-size:.85rem;color:var(--text2)}
.print-key{border-collapse:collapse;margin:8px 0 18px;font-size:.85rem}
.print-key th,.print-key td{border:1px solid var(--border);padding:3px 8px;text-align:center}
.print-exp{margin:0 0 14px;break-inside:avoid;page-break-inside:avoid;line-height:1.7;font-size:.92rem}
.print-exp h3{font-size:.92rem;margin:0 0 4px}
.print-exp p{margin:0 0 4px}
.print-exp-more{font-size:.88rem;margin:0 0 10px}
.print-sample-note{margin:0 0 12px;padding:12px 14px;border-radius:10px;background:var(--bg2);font-size:.92rem;line-height:1.7}
.print-cta{margin:22px 0 8px;padding:14px 16px;border:2px solid var(--accent);border-radius:12px;break-inside:avoid;page-break-inside:avoid}
.print-cta p{margin:0 0 6px;line-height:1.7}
.print-cta .print-cta-url{font-size:.85rem;word-break:break-all}
.print-only{display:none}
@media print{
  @page{size:A4;margin:14mm 12mm}
  .print-page .print-body{padding:0;max-width:none}
  body{background:#fff !important}
  .site-shell-header,.site-page-footer,.site-footer,footer,.site-page-header-crumb,.hub-promo,.print-actions,.print-howto,.no-print,
  ins.adsbygoogle,.adsbygoogle,iframe,.q-index-top{display:none !important}
  .print-only{display:block}
  .print-sheet h2{border-bottom-color:#000}
  .print-break{break-before:page;page-break-before:always}
  a{color:#000;text-decoration:none}
  .print-cta{border-color:#000}
}
"""


def _choices_html(opts: list[str]) -> str:
    items = []
    for i, t in enumerate(opts):
        mark = CIRCLED[i] if i < len(CIRCLED) else f"({i + 1})"
        items.append(f"<li>{mark} {html.escape(t)}</li>")
    return '<ol class="print-choices">' + "".join(items) + "</ol>"


def _correct_label(cor) -> str:
    if isinstance(cor, int) and 1 <= cor <= len(CIRCLED):
        return CIRCLED[cor - 1]
    return html.escape(str(cor))


def _mock_cta_html(*, printable: bool) -> str:
    """予想模試・問題集への導線。印刷物にも残るよう URL を文字でも載せる。"""
    picks = guide_index_picks()
    if not picks:
        return ""
    items = [it for it in picks.get("items") or [] if str(it.get("href") or "").startswith("http")]
    if not items:
        return ""
    rows = []
    for it in items:
        title = html.escape(str(it.get("title") or ""))
        desc = html.escape(str(it.get("description") or ""))
        href = html.escape(str(it.get("href") or ""), quote=True)
        url_line = f'<span class="print-cta-url print-only">{href}</span>' if printable else ""
        rows.append(
            f'<p><strong><a href="{href}" target="_blank" rel="noopener">{title}</a></strong><br>'
            f"{desc}{'<br>' + url_line if url_line else ''}</p>"
        )
    head = "過去問を解き終えたら、本番形式で仕上げ"
    lead = "本番と同じ形式・時間配分で紙で解くなら、予想模試（PDF3回分・解説付き）が使えます。分野ごとに弱点を固めるなら分野別問題集も使えます。"
    return (
        f'<section class="print-cta" aria-label="{html.escape(head)}">'
        f"<p><strong>{html.escape(head)}</strong></p><p>{html.escape(lead)}</p>"
        + "".join(rows)
        + "</section>"
    )


def _head(rel: Path, *, title: str, desc: str, canonical: str, robots: str) -> str:
    depth = len(rel.parent.parts)
    up = "../" * depth
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
{seo_brand_asset_tags(rel)}
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(desc)}">
<meta property="og:title" content="{html.escape(title)}">
<meta property="og:description" content="{html.escape(desc)}">
{robots}
<link rel="canonical" href="{html.escape(canonical)}">
<link rel="stylesheet" href="{up}site-pages.css">
<link rel="stylesheet" href="{up}site-theme.css">
<style>{PRINT_CSS}</style>
</head>
"""


def build_field_page(
    rel: Path, field_name: str, pages: list[dict], *, set_no: int, total_sets: int, field_total: int
) -> str:
    ex = exam_name()
    sample = len(pages) < field_total
    label = "印刷用サンプル" if sample else "印刷用"
    title = f"{ex} 過去問 {label}（{field_name}・{len(pages)}問）｜{brand_title_suffix()}"
    desc = (
        f"{ex}の過去問「{field_name}」{len(pages)}問の{label}ページ。問題編と解答編（正解と要点）に分かれ、"
        "ブラウザの印刷機能でA4に印刷したり、PDFとして保存したりできます。"
    )
    rest = field_total - len(pages)
    sample_html = (
        f'<p class="print-sample-note">この印刷用は「{html.escape(field_name)}」{field_total}問のうち{len(pages)}問のサンプルです。'
        f"残りの{rest}問は、過去問一覧からWeb上で解説付きで解けます。"
        "本番と同じ形式・時間配分で紙で解きたい場合は、下の予想模試（PDF3回分・解説付き）を使ってください。</p>"
        if sample
        else ""
    )
    q_parts = []
    for p in pages:
        q_parts.append(
            f'<div class="print-q"><h3>第{p["qno"]}問</h3>'
            f'<div class="print-stem">{p["stem_html"]}</div>{_choices_html(p["opts"])}'
            '<p class="print-answer-box">解答欄（　　　）</p></div>'
        )
    key_cells = "".join(
        f"<tr><th>第{p['qno']}問</th><td>{_correct_label(p['correct'])}</td></tr>" for p in pages
    )
    # 印刷物には「正解と要点（1行の理由）」だけを載せ、選択肢ごとの詳しい解説は Web で読む形にする。
    # 無料で全部そろった紙の問題集にせず、有料の分野別問題集・予想模試との重なりを抑えるため（2026-11）。
    exp_parts = []
    for p, row in pages_rows(pages):
        why = norm(row.get("explanation_correct")) or norm(row.get("explanation_summary"))
        body = f"<p>{html.escape(why)}</p>" if why else ""
        exp_parts.append(
            f'<div class="print-exp"><h3>第{p["qno"]}問　正解 {_correct_label(p["correct"])}</h3>{body}</div>'
        )
    q_url = public_url("q/index.html")
    more_lead = f"このサンプル以外の{rest}問と、" if sample else ""
    more_html = (
        f'<p class="print-exp-more">{more_lead}選択肢ごとの詳しい解説は、Webの過去問一覧から各問を開くと読めます'
        f'（<a href="{html.escape(rel_href(rel, "q/index.html"))}">過去問一覧</a>'
        f'<span class="print-only">：{html.escape(q_url)}</span>）。</p>'
    )
    crumb = breadcrumb_html(
        rel,
        [("トップ", "index.html"), ("過去問一覧", "q/index.html"), ("印刷・PDF保存", "q/print/index.html"), (field_name, None)],
    )
    hub_href = html.escape(rel_href(rel, "q/print/index.html"))
    q_href = html.escape(rel_href(rel, "q/index.html"))
    return (
        _head(rel, title=title, desc=desc, canonical=public_url(rel.as_posix()), robots=ROBOTS_NOINDEX_FOLLOW)
        + f"""<body class="{shell_body_class('print-page')}">
{site_page_wrap_open()}
{site_page_header(rel, current="q")}
<main class="site-page-main print-page">
  {crumb}
  <h1>{html.escape(ex)} 過去問 {label}：{html.escape(field_name)}（{len(pages)}問）</h1>
  <div class="print-body">
  {sample_html}
  <p class="print-howto">「印刷する」を押すと、問題編と解答編（正解と要点）がA4で印刷されます（解答編は新しいページから始まります）。印刷画面で送信先を「PDFとして保存」にすると、PDFファイルとして保存できます。画面で解く場合は<a href="{q_href}">過去問一覧</a>から1問ずつ解けます。</p>
  <div class="print-actions"><button type="button" class="print-btn" onclick="window.print()">印刷する／PDFとして保存</button><a class="print-btn print-btn--ghost" href="{hub_href}">ほかの分野を選ぶ</a></div>
  {build_guide_index_picks_html(rel)}
  <div class="print-sheet">
    <p class="print-only">{html.escape(ex)} 過去問 {label}（{html.escape(field_name)}・{len(pages)}問）　セット{set_no}/{total_sets}　{html.escape(brand_title_suffix())}</p>
    <h2>問題編：{html.escape(field_name)}</h2>
    {''.join(q_parts)}
    <h2 class="print-break">解答編（正解と要点）：{html.escape(field_name)}</h2>
    {more_html}
    <table class="print-key"><tbody>{key_cells}</tbody></table>
    {''.join(exp_parts)}
    {_mock_cta_html(printable=True)}
  </div>
  </div>
</main>
{site_page_footer(rel, current="q")}
{site_page_wrap_close()}
</body>
</html>
"""
    )


_ROWS_BY_ID: dict[str, dict] = {}


def pages_rows(pages: list[dict]):
    for p in pages:
        yield p, _ROWS_BY_ID.get(p["id"], {})


def build_hub_page(rel: Path, sets: list[tuple[str, str, int, int]], total: int) -> str:
    ex = exam_name()
    printed = sum(n for _h, _name, n, _t in sets)
    sample = printed < total
    if sample:
        title = f"{ex} 過去問を印刷・PDF保存【分野別サンプル{printed}問・解答付き・無料】｜{brand_title_suffix()}"
        desc = (
            f"{ex}の過去問から、分野ごとのサンプル計{printed}問を印刷・PDF保存できます（問題編と解答編）。"
            f"全{total}問はWebで解説付きで解けます。本番形式で紙で解くなら予想模試（PDF3回分）も使えます。"
        )
        intro = (
            f"{ex}の過去問から、分野ごとにサンプル（計{printed}問）を印刷できるようにまとめました。"
            "各セットは「問題編」と「解答編（正解と要点）」に分かれていて、A4で印刷すると紙で解いて答え合わせができます。"
            f"全{total}問は過去問一覧からWeb上で解説付きで解けます。"
        )
    else:
        title = f"{ex} 過去問を印刷・PDF保存【{total}問・解答と要点付き・無料】｜{brand_title_suffix()}"
        desc = (
            f"{ex}の過去問{total}問を、分野ごとに印刷・PDF保存できます。問題編と解答編（正解と要点）に分かれたA4の印刷用ページを無料で公開。"
            "ブラウザの印刷機能から「PDFとして保存」を選ぶとPDFファイルになります。"
        )
        intro = (
            f"{ex}の過去問{total}問を、分野ごとに印刷できるようにまとめました。"
            "各セットは「問題編」と「解答編（正解と要点）」に分かれていて、A4で印刷すると紙で解いて答え合わせができます。"
            "選択肢ごとの詳しい解説は、Webの各問ページで読めます。"
        )
    crumb = breadcrumb_html(rel, [("トップ", "index.html"), ("過去問一覧", "q/index.html"), ("印刷・PDF保存", None)])
    set_items = "".join(
        f'<li><a href="{html.escape(rel_href(rel, href))}"><strong>{html.escape(name)}'
        + (f"（サンプル{n}問／全{t}問）" if n < t else f"（{n}問）")
        + "</strong><span>問題編＋解答編（正解と要点）　印刷・PDF保存</span></a></li>"
        for href, name, n, t in sets
    )
    q_href = html.escape(rel_href(rel, "q/index.html"))
    return (
        _head(rel, title=title, desc=desc, canonical=public_url("q/print/index.html"), robots=ROBOTS_INDEX_FOLLOW)
        + f"""<body class="{shell_body_class('print-page')}">
{site_page_wrap_open()}
{site_page_header(rel, current="q")}
<main class="site-page-main print-page">
  {crumb}
  <h1>{html.escape(ex)} 過去問を印刷・PDF保存</h1>
  <div class="print-body">
  <p>{html.escape(intro)}</p>
  <h2>分野を選んで印刷する</h2>
  <ul class="print-sets">{set_items}</ul>
  {build_guide_index_picks_html(rel)}
  <h2>PDFとして保存する方法</h2>
  <ol>
    <li>上の一覧から分野を選び、印刷用ページを開く</li>
    <li>「印刷する／PDFとして保存」ボタンを押す（スマホはブラウザの共有・印刷メニューから）</li>
    <li>印刷画面の送信先（プリンター）で「PDFとして保存」を選んで保存する</li>
  </ol>
  <p>画面で1問ずつ解いて正誤と解説をすぐ確認したい場合は、<a href="{q_href}">過去問一覧</a>を使ってください。</p>
  {_mock_cta_html(printable=False)}
  </div>
</main>
{site_page_footer(rel, current="q")}
{site_page_wrap_close()}
</body>
</html>
"""
    )


def main() -> int:
    rows = load_rows()
    skip_years = excluded_past_exam_years()
    pages: list[dict] = []
    for i, row in enumerate(rows, start=2):
        if norm(row.get("is_invalidated", "")).upper() == "TRUE":
            continue
        if is_demo_past_question_row(row, excluded_exam_years=skip_years):
            continue
        p = page_dict(row, i)
        _ROWS_BY_ID[p["id"]] = row
        pages.append(p)
    if PRINT_ROOT.is_dir():
        shutil.rmtree(PRINT_ROOT)
    if not pages:
        print("build_print_pages: 過去問が無いためスキップ")
        return 0
    pages.sort(key=lambda p: (p["year"], p["qno"]))
    sets: list[tuple[str, str, int]] = []
    groups = []
    for f in fields():
        name = str(f.get("name") or "")
        names = {name, *[str(a) for a in (f.get("aliases") or [])]}
        grp = [p for p in pages if p["category"] in names]
        if grp:
            groups.append((name, grp))
    # 印刷できる問題数を分野ごとに絞る（site-config.json printSamplePerField、未設定なら全問）。
    # 有料の予想模試・分野別問題集との食い合いを抑えるため（2026-11）。各分野の先頭（問題番号順）から採る。
    from tools.site_config import CONFIG

    try:
        limit = int(CONFIG.get("printSamplePerField") or 0)
    except (TypeError, ValueError):
        limit = 0
    for n, (name, grp) in enumerate(groups, start=1):
        rel = Path(f"q/print/field-{n}/index.html")
        out = ROOT / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        shown = grp[:limit] if limit > 0 else grp
        out.write_text(
            build_field_page(rel, name, shown, set_no=n, total_sets=len(groups), field_total=len(grp)),
            encoding="utf-8",
        )
        sets.append((rel.as_posix(), name, len(shown), len(grp)))
    hub_rel = Path("q/print/index.html")
    (ROOT / hub_rel).write_text(build_hub_page(hub_rel, sets, len(pages)), encoding="utf-8")
    print(f"build_print_pages: {len(sets)} セット（印刷 {sum(s[2] for s in sets)}問／全{len(pages)}問）を q/print/ に生成")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
