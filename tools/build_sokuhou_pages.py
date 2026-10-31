#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""メンタルヘルス・マネジメント検定 解答速報ページ /kaitou-sokuhou/ を生成する。

出力:
  - ハブ  : kaitou-sokuhou/index.html          … 回次一覧
  - 回次  : kaitou-sokuhou/<round>/index.html  … 各社速報リンク集 + 正答まとめ + 公式情報

データ（種ごとに data/ を上書きして運用）:
  - data/sokuhou_rounds.csv : 回次メタ（回・実施日・状態・成績照会予定 など）
  - data/sokuhou_links.csv  : 各社・各サイトの解答速報リンク（試験後に追記）

方針:
  - 問題文・選択肢の転載はしない。各社速報へのリンク誘導と、正答番号の比較のみ。
  - 全種（II種ルート + /master + /self）で build_grade 経由で動く。
  - site_config.public_url() が basePath を、exam_name() が種名を自動解決する。
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
LINKS_CSV = ROOT / "data" / "sokuhou_links.csv"
SOKUHOU_CSS_VER = "20261031-sokuhou"

AUTHOR_NAME = "編集部"
AUTHOR_PROFILE = (
    "メンタルヘルス・マネジメント検定の学習・演習コンテンツを運営する編集チーム。"
    "試験後の解答速報の収集・出典整理を担当しています。"
)
REVIEWER_NAME = "公式情報確認担当"
REVIEWER_PROFILE = "大阪商工会議所の公開試験情報と照合し、掲載の正確性を確認した担当者です。"
PRIMARY_SOURCES = [
    {"label": "メンタルヘルス・マネジメント検定試験（公式）", "url": "https://www.mental-health.ne.jp/"},
    {"label": "公開試験 受験要項（公式）", "url": "https://www.mental-health.ne.jp/guide/"},
]

KIND_LABELS = {
    "official": "公式",
    "school": "資格スクール・予備校",
    "crowd": "みんなで作る速報・投票型",
    "blog": "解説ブログ",
    "video": "動画（YouTube 等）",
    "other": "その他",
}

WEEKDAY_JP = ["月", "火", "水", "木", "金", "土", "日"]


def _norm(value: str | None) -> str:
    return (value or "").strip()


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
        f'<h2 id="{section_id}"><span class="section-heading-num">{section_num}</span>'
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


def links_section_html(links: list[dict[str, str]], status: str) -> str:
    if not links:
        if status == "upcoming":
            note = (
                "現在は試験前です。試験終了後（実施日の午後以降）に、各社・各サイトが公開する"
                "解答速報へのリンクを、公開時刻つきで随時追加します。更新をお待ちください。"
            )
        else:
            note = "解答速報のリンクを準備中です。公開が確認でき次第、出典つきで掲載します。"
        return _notice(note)

    # 種類ごとにグルーピングして一覧表示。
    order = ["official", "school", "crowd", "blog", "video", "other"]
    grouped: dict[str, list[dict[str, str]]] = {}
    for row in links:
        grouped.setdefault(_norm(row.get("kind")) or "other", []).append(row)

    blocks: list[str] = []
    for kind in order:
        items = grouped.get(kind)
        if not items:
            continue
        lis: list[str] = []
        for row in items:
            provider = html.escape(_norm(row.get("provider")) or "（提供元）")
            url = _norm(row.get("url"))
            published = _norm(row.get("published_at"))
            note = _norm(row.get("note"))
            meta_bits = []
            if published:
                meta_bits.append(f"更新 {html.escape(published)}")
            if note:
                meta_bits.append(html.escape(note))
            meta = f' <span class="sokuhou-link-meta">（{" ・ ".join(meta_bits)}）</span>' if meta_bits else ""
            if url:
                link = (
                    f'<a href="{html.escape(url, quote=True)}" target="_blank" '
                    f'rel="noopener noreferrer nofollow">{provider}</a>'
                )
            else:
                link = provider
            lis.append(f"<li>{link}{meta}</li>")
        label = html.escape(KIND_LABELS.get(kind, KIND_LABELS["other"]))
        blocks.append(
            f'<div class="sokuhou-link-group"><h3 class="sokuhou-link-group-title">{label}</h3>'
            f'<ul class="sokuhou-link-list">{"".join(lis)}</ul></div>'
        )
    return "".join(blocks)


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
        '解答速報はあくまで自己採点の目安としてご利用ください。'
        '最新の日程は<a href="https://www.mental-health.ne.jp/guide/" target="_blank" '
        'rel="noopener noreferrer">公式の受験要項</a>で必ずご確認ください。</p>'
    )
    return "".join(parts)


def self_scoring_html() -> str:
    return (
        "<p>合格の目安は、おおむね満点の70%以上とされています（配点・基準は回により異なる場合があります）。"
        "複数の速報で正答が割れている設問は、確定情報ではありません。公式の結果を待ってください。</p>"
        "<ul>"
        "<li>速報は<strong>非公式の推定</strong>を含みます。提供元ごとに正答が異なることがあります。</li>"
        "<li>マークのずれ・転記ミスがないか、問題番号と選択肢を落ち着いて照合しましょう。</li>"
        "<li>ボーダー前後のときは、確定発表まで結果を断定しないのが安全です。</li>"
        "</ul>"
    )


def selfcheck_widget_html(round_row: dict[str, str], exam_date_jp: str, canonical: str) -> str:
    """自己採点チェッカー（合格ライン判定＋結果画像のXシェア）。入力は端末内のみで処理。"""
    label = _norm(round_row.get("exam_label")) or f"第{_norm(round_row.get('round'))}回"
    score_max = _norm(round_row.get("score_max")) or "100"
    score_pass = _norm(round_row.get("score_pass"))
    score_note = _norm(round_row.get("score_note"))

    pass_attr = f' data-pass="{html.escape(score_pass, quote=True)}"' if score_pass else ""
    if score_pass:
        hint = f"合格ライン：{html.escape(score_pass)}点以上（{html.escape(score_max)}点満点）"
    else:
        hint = f"{html.escape(score_max)}点満点"
    note_html = (
        f'<p class="sokuhou-selfcheck-note">{html.escape(score_note)}</p>' if score_note else ""
    )

    return (
        '<section class="sokuhou-selfcheck" id="sokuhou-selfcheck"'
        f' data-exam="{html.escape(exam_name(), quote=True)}"'
        f' data-label="{html.escape(label, quote=True)}"'
        f' data-max="{html.escape(score_max, quote=True)}"{pass_attr}'
        f' data-url="{html.escape(canonical, quote=True)}"'
        f' data-date="{html.escape(exam_date_jp, quote=True)}"'
        ' data-hashtags="メンタルヘルスマネジメント検定,解答速報">'
        '<h2 class="sokuhou-selfcheck-title">自己採点チェッカー（合格ライン判定）</h2>'
        '<p class="sokuhou-selfcheck-lead">自己採点した得点を入力すると、合格ラインに届いているかを判定します。'
        '結果はカード画像にして X（旧Twitter）へシェアできます。</p>'
        '<div class="sokuhou-selfcheck-form">'
        '<label class="sokuhou-score-label" for="sokuhou-score">自己採点の得点</label>'
        '<div class="sokuhou-score-input">'
        '<input type="number" id="sokuhou-score" min="0" inputmode="numeric" autocomplete="off" placeholder="例: 78">'
        f'<span class="sokuhou-score-unit">/ {html.escape(score_max)}点</span>'
        "</div>"
        f'<p class="sokuhou-pass-hint">{hint}</p>'
        '<button type="button" id="sokuhou-judge" class="sokuhou-btn-primary">判定する</button>'
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
        f"{note_html}"
        '<p class="sokuhou-selfcheck-disclaimer">※ 自己採点の目安です。正式な合否・得点は公式の成績照会・結果通知でご確認ください。'
        '入力した得点はこの端末内だけで処理され、外部へ送信・保存されません。</p>'
        "</section>"
    )


def related_links_html() -> str:
    # 種によって存在しないページ（exam-dates など）はリンク切れになるため実在チェックで絞る。
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
        '<h2 id="sokuhou-disclaimer-title"><span class="section-heading-num">★</span>掲載方針・ご注意</h2>'
        "<p>本ページは、各社・各サイトが公開する解答速報を整理し、出典へのリンクでご案内する"
        "<strong>まとめページ</strong>です。試験問題および選択肢の本文は、主催団体の著作物のため転載しません。</p>"
        "<p>掲載する正答は各提供元の発表に基づく参考情報であり、当サイトが正答を保証するものではありません。"
        "正式な結果は公式の成績照会・結果通知をご確認ください。記載に誤り・リンク切れがある場合はお問い合わせください。</p>"
        "</section>"
    )


def faq_items(round_row: dict[str, str], exam_date_jp: str) -> list[dict[str, str]]:
    label = _norm(round_row.get("exam_label"))
    return [
        {
            "question": f"{label}の解答速報はいつ出ますか？",
            "answer": (
                f"一般に、各社・各サイトの解答速報は試験当日（{exam_date_jp}）の午後以降から順次公開されます。"
                "公開が確認でき次第、本ページに出典つきで追加します。"
            ),
        },
        {
            "question": "解答速報で合否はわかりますか？",
            "answer": (
                "速報は自己採点の目安です。正式な合否・得点は、公式の成績照会または結果通知で確定します。"
                "ボーダー前後の場合は、公式発表をお待ちください。"
            ),
        },
        {
            "question": "各社で正答が違うのはなぜですか？",
            "answer": (
                "試験直後の速報は非公式の推定を含むためです。公式の標準解答が公表されると正答が確定します。"
                "複数の速報を見比べ、割れている設問は確定情報として扱わないことをおすすめします。"
            ),
        },
    ]


def build_round_page(round_row: dict[str, str], links: list[dict[str, str]]) -> str:
    round_id = _norm(round_row.get("round"))
    exam_label = _norm(round_row.get("exam_label")) or f"第{round_id}回"
    status = _norm(round_row.get("status")) or "upcoming"
    exam_date_jp = _jp_date(round_row.get("exam_date_iso", ""))
    rel_path = Path(PAGE_SLUG) / round_id / "index.html"
    canonical = public_url(f"{PAGE_SLUG}/{round_id}/")
    today = date.today().isoformat()

    page_title = f"{exam_label}{exam_name()} 解答速報｜{exam_date_jp}・各社まとめ"
    desc = (
        f"{exam_label}{exam_name()}（{exam_date_jp}実施）の解答速報まとめ。"
        "各社・各サイトの解答速報へのリンク、正答の比較、公式の標準解答・成績照会の予定を掲載します。"
    )

    faq_list = faq_items(round_row, exam_date_jp)
    body_parts: list[str] = []
    body_parts.append(selfcheck_widget_html(round_row, exam_date_jp, canonical))
    num = 1
    body_parts.append(section_wrap("試験の基本情報", exam_info_table_html(round_row, exam_date_jp), num, "sokuhou-sec-info"))
    num += 1
    body_parts.append(section_wrap("各社・各サイトの解答速報リンク", links_section_html(links, status), num, "sokuhou-sec-links"))
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
        f"{exam_label}{exam_name()}（{exam_date_jp}実施）の解答速報まとめです。"
        "各社・各サイトの速報へのリンクと、公式の標準解答・成績照会の予定を、試験後に随時更新します。"
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
    page_title = f"{exam_name()} 解答速報｜各社まとめ・回次一覧"
    desc = (
        f"{exam_name()}の解答速報まとめ。各回の試験について、各社・各サイトの解答速報リンク、"
        "正答の比較、公式の標準解答・成績照会の予定を回次ごとに掲載します。"
    )

    # 実施日の新しい順。
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
            f'<span class="sokuhou-round-card-title">{html.escape(label)} 解答速報</span>'
            f'<span class="sokuhou-round-card-date">{html.escape(djp)} 実施</span>'
            "</a></li>"
        )
    cards_html = f'<ul class="sokuhou-round-list">{"".join(cards)}</ul>' if cards else _notice("公開準備中です。")

    intro = (
        f"<p>{html.escape(exam_name())}の各回について、試験後に各社・各サイトの解答速報を集めてご案内するまとめページです。"
        "問題・選択肢の本文は転載せず、出典へのリンクでご案内します。</p>"
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
<p class="article-lead">{html.escape(exam_name())}の解答速報を回次ごとにまとめています。</p>
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
    links = _read_csv(LINKS_CSV)
    links_by_round: dict[str, list[dict[str, str]]] = {}
    for row in links:
        links_by_round.setdefault(_norm(row.get("round")), []).append(row)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "index.html").write_text(build_hub_page(rounds), encoding="utf-8")
    print(f"Wrote {PAGE_SLUG}/index.html")
    for r in rounds:
        rid = _norm(r.get("round"))
        if not rid:
            continue
        rdir = OUTPUT_DIR / rid
        rdir.mkdir(parents=True, exist_ok=True)
        page = build_round_page(r, links_by_round.get(rid, []))
        (rdir / "index.html").write_text(page, encoding="utf-8")
        print(f"Wrote {PAGE_SLUG}/{rid}/index.html")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
