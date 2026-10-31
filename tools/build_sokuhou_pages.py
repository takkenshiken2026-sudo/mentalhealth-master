#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""メンタルヘルス・マネジメント検定 解答速報（自己採点）ページ /kaitou-sokuhou/ を生成する。

出力:
  - ハブ  : kaitou-sokuhou/index.html          … 回次一覧
  - 回次  : kaitou-sokuhou/<round>/index.html  … 本サイト独自解答＋問題別の自己採点ツール

データ（種ごとに data/ を上書きして運用）:
  - data/sokuhou_rounds.csv  : 回次メタ（回・実施日・状態・成績照会・採点基準 など）
  - data/sokuhou_answers.csv : 本サイト独自の解答（問番号・正答・配点・選択肢数・分野）

方針:
  - 掲載する解答は「本サイト独自の参考解答」。公式の標準解答ではない。
  - 問題文・選択肢の本文は転載しない（問番号と正答番号のみ）。
  - 全種（II種ルート + /master + /self）で build_grade 経由で動く。
"""

from __future__ import annotations

import csv
import html
import json
import sys
from datetime import date, datetime
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
from tools.knowledge_hub_seo import faq_section_html  # noqa: E402
from tools.seo_editorial_chrome import (  # noqa: E402
    seo_brand_asset_tags,
    seo_editorial_article_class,
    seo_editorial_head_fonts,
    seo_editorial_stylesheet_links,
)
from tools.site_config import brand_name, exam_name, public_url  # noqa: E402

PAGE_SLUG = "kaitou-sokuhou"
OUTPUT_DIR = ROOT / PAGE_SLUG
ROUNDS_CSV = ROOT / "data" / "sokuhou_rounds.csv"
ANSWERS_CSV = ROOT / "data" / "sokuhou_answers.csv"
SOKUHOU_CSS_VER = "20261031-sokuhou"

AUTHOR_NAME = "編集部"
AUTHOR_PROFILE = (
    "メンタルヘルス・マネジメント検定の学習・演習コンテンツを運営する編集チーム。"
    "本サイト独自の参考解答の作成・検証を担当しています。"
)
REVIEWER_NAME = "解答作成・確認担当"
REVIEWER_PROFILE = "公式の出題範囲・テキストと照合し、本サイト独自解答の根拠を確認した担当者です。"
PRIMARY_SOURCES = [
    {"label": "メンタルヘルス・マネジメント検定試験（公式）", "url": "https://www.mental-health.ne.jp/"},
    {"label": "公開試験 受験要項（公式）", "url": "https://www.mental-health.ne.jp/guide/"},
]

WEEKDAY_JP = ["月", "火", "水", "木", "金", "土", "日"]


def _norm(value: str | None) -> str:
    return (value or "").strip()


def _int(value: str | None, default: int = 0) -> int:
    try:
        return int(float(_norm(value)))
    except (TypeError, ValueError):
        return default


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    text = path.read_text(encoding="utf-8-sig")
    return [dict(row) for row in csv.DictReader(text.splitlines())]


def _jp_date(iso: str) -> str:
    iso = _norm(iso)
    if not iso:
        return ""
    try:
        d = datetime.strptime(iso, "%Y-%m-%d").date()
    except ValueError:
        return iso
    return f"{d.year}年{d.month}月{d.day}日（{WEEKDAY_JP[d.weekday()]}）"


def _answers_for(answers: list[dict[str, str]]) -> list[dict]:
    """解答CSV行を採点用の辞書リストへ整形（問番号順）。"""
    out: list[dict] = []
    for row in answers:
        no = _int(row.get("q_no"))
        correct = _norm(row.get("correct"))
        if not no or not correct:
            continue
        out.append(
            {
                "no": no,
                "correct": _int(row.get("correct")) if correct.isdigit() else correct,
                "points": _int(row.get("points"), 2) or 2,
                "choices": _int(row.get("choices"), 4) or 4,
                "field": _norm(row.get("field")),
            }
        )
    out.sort(key=lambda r: r["no"])
    return out


def quality_panel_html(fact_checked_at: str) -> str:
    rows = [
        f"<tr><th>運営</th><td>{html.escape(AUTHOR_NAME)}（{html.escape(AUTHOR_PROFILE)}）</td></tr>",
        f"<tr><th>確認</th><td>{html.escape(REVIEWER_NAME)}（{html.escape(REVIEWER_PROFILE)}）</td></tr>",
        f"<tr><th>最終更新日</th><td>{html.escape(fact_checked_at)}</td></tr>",
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
        '<section class="seo-quality-panel" aria-labelledby="sokuhou-quality-title">'
        '<h2 id="sokuhou-quality-title">このページの信頼性について</h2>'
        '<table class="seo-info-table"><tbody>'
        + "".join(rows)
        + "</tbody></table></section>"
    )


def section_wrap(heading: str, inner_html: str, section_num: int, section_id: str) -> str:
    return (
        f'<section class="seo-article-section" aria-labelledby="{section_id}">'
        f'<h2 id="{section_id}"><span class="sokuhou-num">{section_num}</span>'
        f"{html.escape(heading)}</h2>{inner_html}</section>"
    )


def _notice(text: str) -> str:
    return f'<p class="sokuhou-notice">{html.escape(text)}</p>'


def exam_info_table_html(round_row: dict[str, str], exam_date_jp: str) -> str:
    rows = [
        f"<tr><th>試験区分</th><td>{html.escape(exam_name())}</td></tr>",
        f"<tr><th>回次</th><td>{html.escape(_norm(round_row.get('exam_label')))}（公開試験）</td></tr>",
        f"<tr><th>実施日</th><td>{html.escape(exam_date_jp)}</td></tr>",
        "<tr><th>主催</th><td>大阪商工会議所・施行商工会議所</td></tr>",
    ]
    return '<table class="seo-info-table"><tbody>' + "".join(rows) + "</tbody></table>"


def selfcheck_widget_html(
    round_row: dict[str, str], exam_date_jp: str, canonical: str, answers: list[dict]
) -> str:
    """問題ごとに解答を入力して採点する自己採点ツール（本サイト独自解答で照合）。"""
    label = _norm(round_row.get("exam_label")) or f"第{_norm(round_row.get('round'))}回"
    score_pass = _norm(round_row.get("score_pass"))
    score_note = _norm(round_row.get("score_note"))
    pass_attr = f' data-pass="{html.escape(score_pass, quote=True)}"' if score_pass else ""

    note_html = (
        f'<p class="sokuhou-selfcheck-note">{html.escape(score_note)}</p>' if score_note else ""
    )

    # 解答データが未投入なら、採点UIの代わりに準備中メッセージ。
    if not answers:
        body = _notice(
            "試験後に本サイト独自の解答を公開し、ここで問題ごとに自己採点できるようにします。"
            "公開までお待ちください。"
        )
        answers_json = "[]"
        total = 0
    else:
        answers_json = json.dumps(answers, ensure_ascii=False, separators=(",", ":"))
        total = sum(a["points"] for a in answers)
        body = (
            '<p class="sokuhou-selfcheck-lead">問題ごとに自分の解答を選ぶと、本サイトの独自解答と照合して'
            '得点を自動計算し、合格ラインに届いているかを判定します。結果はカード画像にして'
            ' X（旧Twitter）へシェアできます。</p>'
            '<div class="sokuhou-grid" id="sokuhou-grid" aria-label="問題ごとの解答入力"></div>'
            '<div class="sokuhou-grid-actions">'
            '<button type="button" id="sokuhou-judge" class="sokuhou-btn-primary">採点する</button>'
            '<button type="button" id="sokuhou-clear" class="sokuhou-btn-ghost">クリア</button>'
            "</div>"
            '<div class="sokuhou-result" id="sokuhou-result" hidden></div>'
            '<div class="sokuhou-share" id="sokuhou-share" hidden>'
            '<canvas id="sokuhou-canvas" class="sokuhou-canvas" width="1200" height="630" '
            'aria-label="自己採点の結果画像"></canvas>'
            '<div class="sokuhou-share-actions">'
            '<button type="button" id="sokuhou-share-native" class="sokuhou-btn-primary" hidden>画像付きでシェア</button>'
            '<button type="button" id="sokuhou-post-x" class="sokuhou-btn-x">X でポスト</button>'
            '<button type="button" id="sokuhou-save-img" class="sokuhou-btn-ghost">画像を保存</button>'
            "</div>"
            '<p class="sokuhou-share-note">X のポスト画面には画像を自動で添付できません。'
            '「画像を保存」した画像を手動で添付してください（スマホは「画像付きでシェア」で X アプリに共有できます）。</p>'
            "</div>"
        )

    return (
        '<section class="sokuhou-selfcheck" id="sokuhou-selfcheck"'
        f' data-exam="{html.escape(exam_name(), quote=True)}"'
        f' data-label="{html.escape(label, quote=True)}"'
        f' data-total="{total}"{pass_attr}'
        f' data-url="{html.escape(canonical, quote=True)}"'
        f' data-date="{html.escape(exam_date_jp, quote=True)}"'
        ' data-hashtags="メンタルヘルスマネジメント検定,自己採点">'
        '<h2 class="sokuhou-selfcheck-title">自己採点（問題ごとに入力）</h2>'
        f"{body}"
        f'<script type="application/json" id="sokuhou-answers">{answers_json}</script>'
        f"{note_html}"
        '<p class="sokuhou-selfcheck-disclaimer">※ 本ツールは本サイト独自の参考解答で採点します（公式の標準解答ではありません）。'
        '正式な合否・得点は公式の成績照会・結果通知でご確認ください。入力した解答はこの端末内だけで処理され、外部へ送信・保存されません。</p>'
        "</section>"
    )


def answer_key_html(answers: list[dict], status: str) -> str:
    """本サイト独自解答の一覧（折りたたみ）。未投入時は準備中。"""
    if not answers:
        if status == "upcoming":
            return _notice("試験後に本サイト独自の解答を公開します。公開までお待ちください。")
        return _notice("独自解答を準備中です。公開まで今しばらくお待ちください。")

    has_field = any(a["field"] for a in answers)
    head = "<tr><th>問</th><th>本サイト独自解答</th><th>配点</th>" + ("<th>分野</th>" if has_field else "") + "</tr>"
    body_rows = []
    for a in answers:
        field_td = f"<td>{html.escape(a['field'])}</td>" if has_field else ""
        body_rows.append(
            f'<tr><td>問{a["no"]}</td><td class="sokuhou-ans">{html.escape(str(a["correct"]))}</td>'
            f'<td>{a["points"]}点</td>{field_td}</tr>'
        )
    table = (
        '<table class="seo-info-table sokuhou-answer-table"><thead>'
        + head
        + "</thead><tbody>"
        + "".join(body_rows)
        + "</tbody></table>"
    )
    return (
        '<details class="sokuhou-answer-details"><summary>独自解答の一覧を表示</summary>'
        '<p class="sokuhou-answer-note">下記は本サイトが独自に作成した参考解答です。公式の標準解答ではありません。</p>'
        + table
        + "</details>"
    )


def official_info_html(round_row: dict[str, str]) -> str:
    rf = _jp_date(round_row.get("result_from_iso", ""))
    rt = _jp_date(round_row.get("result_to_iso", ""))
    official_note = _norm(round_row.get("official_note"))
    parts: list[str] = []
    if official_note:
        parts.append(f"<p>{html.escape(official_note)}</p>")
    if rf and rt:
        parts.append(
            "<table class=\"seo-info-table\"><tbody>"
            f"<tr><th>成績照会（Web）</th><td>{html.escape(rf)} 〜 {html.escape(rt)} の予定</td></tr>"
            "</tbody></table>"
        )
    parts.append(
        '<p>合否・得点は、公式の成績照会または結果通知が正式な結果です。'
        '本ページの独自解答・自己採点はあくまで目安としてご利用ください。'
        '最新の日程は<a href="https://www.mental-health.ne.jp/guide/" target="_blank" '
        'rel="noopener noreferrer">公式の受験要項</a>で必ずご確認ください。</p>'
    )
    return "".join(parts)


def self_scoring_html() -> str:
    return (
        "<p>合格の目安は、おおむね満点の70%以上とされています（配点・基準は回により異なる場合があります）。"
        "本サイトの独自解答は参考であり、確定情報ではありません。公式の結果を待ってください。</p>"
        "<ul>"
        "<li>独自解答は<strong>非公式の推定</strong>を含みます。公式の標準解答とは異なる場合があります。</li>"
        "<li>マークのずれ・転記ミスがないか、問題番号と選択肢を落ち着いて照合しましょう。</li>"
        "<li>ボーダー前後のときは、確定発表まで結果を断定しないのが安全です。</li>"
        "</ul>"
    )


def related_links_html() -> str:
    candidates: list[tuple[str, str, Path]] = [
        ("../../index.html", "トップ（学習コンテンツ）", ROOT / "index.html"),
        ("../../exam-dates/", "試験日検索・日程", ROOT / "exam-dates" / "index.html"),
        ("../../q/index.html", "過去問一覧", ROOT / "q" / "index.html"),
        ("../../terms/index.html", "用語解説一覧", ROOT / "terms" / "index.html"),
    ]
    items = "".join(
        f'<a class="related-link" href="{html.escape(href, quote=True)}">{html.escape(label)}</a>'
        for href, label, path in candidates
        if path.is_file()
    )
    if not items:
        return ""
    return (
        '<div class="related-box"><div class="related-box-title">関連コンテンツ</div>'
        f'<div class="related-links">{items}</div></div>'
    )


def disclaimer_html() -> str:
    return (
        '<section class="seo-article-section sokuhou-disclaimer" aria-labelledby="sokuhou-disclaimer-title">'
        '<h2 id="sokuhou-disclaimer-title"><span class="sokuhou-num">★</span>掲載方針・ご注意</h2>'
        "<p>本ページに掲載する解答は、<strong>本サイトが独自に作成した参考解答</strong>です。"
        "主催団体による公式の標準解答ではありません。試験問題および選択肢の本文は、主催団体の著作物のため転載していません。</p>"
        "<p>独自解答・自己採点の結果は参考情報であり、正答・合否を保証するものではありません。"
        "正式な結果は公式の成績照会・結果通知をご確認ください。記載に誤りがある場合はお問い合わせください。</p>"
        "</section>"
    )


def faq_items(round_row: dict[str, str], exam_date_jp: str) -> list[dict[str, str]]:
    label = _norm(round_row.get("exam_label"))
    return [
        {
            "question": f"{label}の解答はいつ公開されますか？",
            "answer": (
                f"試験当日（{exam_date_jp}）の試験終了後に、本サイト独自の解答を順次公開します。"
                "公開後は、このページで問題ごとに自己採点できます。"
            ),
        },
        {
            "question": "この解答は公式のものですか？",
            "answer": (
                "いいえ。本ページの解答は本サイトが独自に作成した参考解答です。公式の標準解答ではありません。"
                "正式な合否・得点は公式の成績照会・結果通知でご確認ください。"
            ),
        },
        {
            "question": "自己採点の点数で合否はわかりますか？",
            "answer": (
                "自己採点は目安です。合格の目安はおおむね満点の70%ですが、ボーダー前後の場合は"
                "公式の結果を待つことをおすすめします。"
            ),
        },
    ]


def build_round_page(round_row: dict[str, str], answers: list[dict]) -> str:
    round_id = _norm(round_row.get("round"))
    exam_label = _norm(round_row.get("exam_label")) or f"第{round_id}回"
    status = _norm(round_row.get("status")) or "upcoming"
    exam_date_jp = _jp_date(round_row.get("exam_date_iso", ""))
    rel_path = Path(PAGE_SLUG) / round_id / "index.html"
    canonical = public_url(f"{PAGE_SLUG}/{round_id}/")
    today = date.today().isoformat()

    page_title = f"{exam_label}{exam_name()} 解答速報・自己採点｜{exam_date_jp}"
    desc = (
        f"{exam_label}{exam_name()}（{exam_date_jp}実施）の解答速報。本サイト独自の解答と、"
        "問題ごとに自己採点できるツールを掲載。合格ライン判定・結果画像の X シェアに対応します。"
    )

    faq_list = faq_items(round_row, exam_date_jp)
    body_parts: list[str] = []
    body_parts.append(selfcheck_widget_html(round_row, exam_date_jp, canonical, answers))
    num = 1
    body_parts.append(section_wrap("本サイト独自の解答", answer_key_html(answers, status), num, "sokuhou-sec-answers"))
    num += 1
    body_parts.append(section_wrap("試験の基本情報", exam_info_table_html(round_row, exam_date_jp), num, "sokuhou-sec-info"))
    num += 1
    body_parts.append(section_wrap("公式の標準解答・成績照会の予定", official_info_html(round_row), num, "sokuhou-sec-official"))
    num += 1
    body_parts.append(section_wrap("合格ラインと自己採点の注意", self_scoring_html(), num, "sokuhou-sec-score"))
    num += 1
    body_parts.append(quality_panel_html(today))
    body_parts.append(faq_section_html(faq_list, heading_id="sokuhou-faq", section_num=num))
    body_parts.append(disclaimer_html())
    related = related_links_html()
    if related:
        body_parts.append(related)

    graph: list[dict] = [
        {
            "@type": "WebPage",
            "@id": canonical + "#webpage",
            "url": canonical,
            "name": page_title,
            "description": desc,
            "inLanguage": "ja-JP",
            "isPartOf": {"@type": "WebSite", "name": brand_name(), "url": public_url("index.html")},
            "about": exam_name(),
        },
        {
            "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "トップ", "item": public_url("index.html")},
                {"@type": "ListItem", "position": 2, "name": "解答速報", "item": public_url(f"{PAGE_SLUG}/")},
                {"@type": "ListItem", "position": 3, "name": f"{exam_label} 解答速報", "item": canonical},
            ],
        },
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
        },
    ]
    json_ld = {"@context": "https://schema.org", "@graph": graph}

    header = site_page_header(rel_path, current=PAGE_SLUG)
    footer = site_page_footer(rel_path, current=None)
    crumb = breadcrumb_html(
        rel_path,
        [("トップ", "../../index.html"), ("解答速報", "../index.html"), (f"{exam_label} 解答速報", None)],
    )
    article_class = seo_editorial_article_class(extra="sokuhou-page")
    lead = (
        f"{exam_label}{exam_name()}（{exam_date_jp}実施）の解答速報・自己採点ページです。"
        "本サイト独自の解答で、問題ごとに点数を計算し合格ラインを判定します。試験後に順次更新します。"
    )

    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
{seo_brand_asset_tags(rel_path)}
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html.escape(page_title)}</title>
<meta name="description" content="{html.escape(desc)}">
{ROBOTS_INDEX_FOLLOW}
<link rel="canonical" href="{html.escape(canonical)}">
<meta property="og:type" content="website">
<meta property="og:title" content="{html.escape(page_title)}">
<meta property="og:description" content="{html.escape(desc)}">
<meta property="og:url" content="{html.escape(canonical)}">
<meta name="twitter:card" content="summary_large_image">
{seo_editorial_head_fonts()}
{seo_editorial_stylesheet_links(rel_path, site_pages_ver=SOKUHOU_CSS_VER)}
<script type="application/ld+json">
{json.dumps(json_ld, ensure_ascii=False, indent=2)}
</script>
</head>
<body class="{shell_body_class('sokuhou-page')}">
{site_page_wrap_open()}
{header}
<main class="seo-article-main">
{crumb}
<article class="{article_class}">
<div class="article-meta">
<span class="meta-category">解答速報</span>
<span class="meta-updated">最終更新日：{html.escape(today)}</span>
</div>
<h1 class="article-title">{html.escape(page_title)}</h1>
<p class="article-lead" id="sokuhou-lead">{html.escape(lead)}</p>
{"".join(body_parts)}
</article>
</main>
{footer}
{site_page_wrap_close()}
<script src="../../sokuhou-selfcheck.js" defer></script>
</body>
</html>
"""


def build_hub_page(rounds: list[dict[str, str]]) -> str:
    rel_path = Path(PAGE_SLUG) / "index.html"
    canonical = public_url(f"{PAGE_SLUG}/")
    today = date.today().isoformat()
    page_title = f"{exam_name()} 解答速報・自己採点｜回次一覧"
    desc = (
        f"{exam_name()}の解答速報・自己採点。各回について本サイト独自の解答と、問題ごとに"
        "自己採点できるツールを回次ごとに掲載します。"
    )

    def _key(r: dict[str, str]) -> str:
        return _norm(r.get("exam_date_iso")) or _norm(r.get("round"))

    rounds_sorted = sorted(rounds, key=_key, reverse=True)
    cards: list[str] = []
    for r in rounds_sorted:
        rid = _norm(r.get("round"))
        label = _norm(r.get("exam_label")) or f"第{rid}回"
        djp = _jp_date(r.get("exam_date_iso", ""))
        href = html.escape(f"{rid}/", quote=True)
        cards.append(
            f'<li class="sokuhou-round-card"><a href="{href}">'
            f'<span class="sokuhou-round-card-title">{html.escape(label)} 解答速報・自己採点</span>'
            f'<span class="sokuhou-round-card-date">{html.escape(djp)} 実施</span>'
            "</a></li>"
        )
    cards_html = f'<ul class="sokuhou-round-list">{"".join(cards)}</ul>' if cards else _notice("公開準備中です。")

    intro = (
        f"<p>{html.escape(exam_name())}の各回について、本サイト独自の解答と、問題ごとに点数を計算できる"
        "自己採点ツールを公開します。問題・選択肢の本文は転載しません。</p>"
    )

    graph = [
        {
            "@type": "WebPage",
            "@id": canonical + "#webpage",
            "url": canonical,
            "name": page_title,
            "description": desc,
            "inLanguage": "ja-JP",
            "isPartOf": {"@type": "WebSite", "name": brand_name(), "url": public_url("index.html")},
            "about": exam_name(),
        },
        {
            "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "トップ", "item": public_url("index.html")},
                {"@type": "ListItem", "position": 2, "name": "解答速報", "item": canonical},
            ],
        },
    ]
    json_ld = {"@context": "https://schema.org", "@graph": graph}

    header = site_page_header(rel_path, current=PAGE_SLUG)
    footer = site_page_footer(rel_path, current=None)
    crumb = breadcrumb_html(rel_path, [("トップ", "../index.html"), ("解答速報", None)])
    article_class = seo_editorial_article_class(extra="sokuhou-page sokuhou-hub")

    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
{seo_brand_asset_tags(rel_path)}
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html.escape(page_title)}</title>
<meta name="description" content="{html.escape(desc)}">
{ROBOTS_INDEX_FOLLOW}
<link rel="canonical" href="{html.escape(canonical)}">
<meta property="og:type" content="website">
<meta property="og:title" content="{html.escape(page_title)}">
<meta property="og:description" content="{html.escape(desc)}">
<meta property="og:url" content="{html.escape(canonical)}">
<meta name="twitter:card" content="summary_large_image">
{seo_editorial_head_fonts()}
{seo_editorial_stylesheet_links(rel_path, site_pages_ver=SOKUHOU_CSS_VER)}
<script type="application/ld+json">
{json.dumps(json_ld, ensure_ascii=False, indent=2)}
</script>
</head>
<body class="{shell_body_class('sokuhou-page')}">
{site_page_wrap_open()}
{header}
<main class="seo-article-main">
{crumb}
<article class="{article_class}">
<div class="article-meta">
<span class="meta-category">解答速報</span>
<span class="meta-updated">最終更新日：{html.escape(today)}</span>
</div>
<h1 class="article-title">{html.escape(page_title)}</h1>
<p class="article-lead">{html.escape(exam_name())}の解答速報・自己採点を回次ごとにまとめています。</p>
{intro}
{cards_html}
{disclaimer_html()}
</article>
</main>
{footer}
{site_page_wrap_close()}
</body>
</html>
"""


def main() -> int:
    rounds = _read_csv(ROUNDS_CSV)
    if not rounds:
        print("build_sokuhou_pages: data/sokuhou_rounds.csv が無い/空のためスキップ")
        return 0
    answers_rows = _read_csv(ANSWERS_CSV)
    answers_by_round: dict[str, list[dict[str, str]]] = {}
    for row in answers_rows:
        answers_by_round.setdefault(_norm(row.get("round")), []).append(row)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "index.html").write_text(build_hub_page(rounds), encoding="utf-8")
    print(f"Wrote {PAGE_SLUG}/index.html")
    for r in rounds:
        rid = _norm(r.get("round"))
        if not rid:
            continue
        rdir = OUTPUT_DIR / rid
        rdir.mkdir(parents=True, exist_ok=True)
        answers = _answers_for(answers_by_round.get(rid, []))
        page = build_round_page(r, answers)
        (rdir / "index.html").write_text(page, encoding="utf-8")
        print(f"Wrote {PAGE_SLUG}/{rid}/index.html（独自解答 {len(answers)} 問）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
