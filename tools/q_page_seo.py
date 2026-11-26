# -*- coding: utf-8 -*-
"""過去問・実践演習・一問一答の一覧／各問ページ向け SEO 文言（site-config.json の seoCopy）。"""

from __future__ import annotations

import html
import re

from tools.build_past_question_pages import meta_description
from tools.site_config import CONFIG, brand_name, brand_title_suffix, exam_name, static_question_modes

MODE_LABEL: dict[str, str] = {
    "past": "過去問",
    "practice": "実践演習",
    "ichimon": "一問一答",
}


def seo_copy() -> dict[str, str]:
    raw = CONFIG.get("seoCopy") if isinstance(CONFIG.get("seoCopy"), dict) else {}
    return {
        "mockExam": str(raw.get("mockExam") or "模試・模擬試験"),
        "studyModes": str(raw.get("studyModes") or "過去問・実践演習・一問一答"),
    }


def study_modes_note_html() -> str:
    """学習導線の短文。方針により各問・一覧ページでは非表示（空文字を返す）。"""
    return ""


def index_lead(mode: str) -> str:
    ex = exam_name()
    c = seo_copy()
    if mode == "past":
        return (
            f"{ex}の過去問を分野別にまとめています。"
            "すべてWeb上で無料で解け、PDFのダウンロードやアプリのインストールは不要です。スマホ・PCのブラウザでそのまま学習できます。"
            f"{c['mockExam']}前の出題傾向の確認や、{c['studyModes']}の中心コンテンツとして使えます。"
            "検索と絞り込みで目的の問題を探し、解説ページで正誤と解説を確認できます。"
        )
    if mode == "practice":
        return (
            f"{ex}の実践演習を分野別にまとめています。"
            f"{c['mockExam']}に近い形式で力を測る演習として、{c['studyModes']}と組み合わせて学習できます。"
            "各問題の解説ページで正誤を確認し、アプリで演習できます。"
        )
    return (
        f"{ex}の一問一答を年度・分野別にまとめています。"
        f"{c['mockExam']}前の知識確認や、{c['studyModes']}の隙間学習に使えます。"
        "検索と絞り込みのあと、解説ページからアプリ演習へ進めます。"
    )


def _about_cfg() -> dict:
    raw = CONFIG.get("seoAbout")
    return raw if isinstance(raw, dict) else {}


def index_about_html(mode: str) -> str:
    """過去問一覧ページに置く、試験概要・出題範囲・学習法・FAQ の SEO 本文。
    site-config.json の seoAbout を持つ種のみ出力（未設定種は空文字）。"""
    if mode != "past":
        return ""
    cfg = _about_cfg()
    if not cfg:
        return ""
    import json as _json

    e = html.escape
    parts: list[str] = ['<section class="q-seo-about site-prose" aria-labelledby="q-seo-about-h">']
    parts.append(f'<h2 id="q-seo-about-h">{e(exam_name())}とは</h2>')
    overview = str(cfg.get("overview") or "").strip()
    if overview:
        parts.append(f"<p>{e(overview)}</p>")

    facts = cfg.get("facts") or []
    if isinstance(facts, list) and facts:
        parts.append('<h3>試験の概要</h3>')
        parts.append('<table class="q-seo-table"><tbody>')
        for item in facts:
            if isinstance(item, (list, tuple)) and len(item) == 2:
                parts.append(f"<tr><th scope=\"row\">{e(str(item[0]))}</th><td>{e(str(item[1]))}</td></tr>")
        parts.append("</tbody></table>")

    scope = cfg.get("scope") or []
    if isinstance(scope, list) and scope:
        parts.append(f"<h3>{e(str(cfg.get('scopeHeading') or '出題範囲'))}</h3>")
        parts.append("<ul>" + "".join(f"<li>{e(str(s))}</li>" for s in scope) + "</ul>")

    study = cfg.get("study") or []
    if isinstance(study, list) and study:
        parts.append(f"<h3>{e(str(cfg.get('studyHeading') or '学習の進め方'))}</h3>")
        parts.append("<ol>" + "".join(f"<li>{e(str(s))}</li>" for s in study) + "</ol>")

    faq = cfg.get("faq") or []
    faq_pairs = [x for x in faq if isinstance(x, (list, tuple)) and len(x) == 2] if isinstance(faq, list) else []
    if faq_pairs:
        parts.append(f"<h3>{e(str(cfg.get('faqHeading') or 'よくある質問'))}</h3>")
        parts.append('<div class="q-seo-faq">')
        for q, a in faq_pairs:
            parts.append(f"<h4>{e(str(q))}</h4><p>{e(str(a))}</p>")
        parts.append("</div>")
        ld = {
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": [
                {
                    "@type": "Question",
                    "name": str(q),
                    "acceptedAnswer": {"@type": "Answer", "text": str(a)},
                }
                for q, a in faq_pairs
            ],
        }
        parts.append(
            '<script type="application/ld+json">'
            + _json.dumps(ld, ensure_ascii=False)
            + "</script>"
        )

    links = cfg.get("relatedLinks") or []
    link_pairs = [x for x in links if isinstance(x, (list, tuple)) and len(x) == 2] if isinstance(links, list) else []
    if link_pairs:
        parts.append(f"<h3>{e(str(cfg.get('relatedHeading') or '関連ページ'))}</h3>")
        parts.append(
            "<ul>"
            + "".join(f'<li><a href="{e(str(href))}">{e(str(label))}</a></li>' for href, label in link_pairs)
            + "</ul>"
        )

    parts.append("</section>")
    return "\n".join(parts)


def index_meta_description(mode: str, *, count: int) -> str:
    ex = exam_name()
    c = seo_copy()
    if mode == "past":
        base = (
            f"{ex}の過去問{count}問をWebで無料公開。全問に正解と解説付きで、"
            "スマホ・PCのブラウザから分野別にすぐ解け、分野ごとに印刷・PDF保存もできます。"
            f"{c['mockExam']}対策・{c['studyModes']}の学習に対応。"
        )
    elif mode == "practice":
        base = (
            f"{ex}の実践演習{count}問を分野別に掲載。"
            f"{c['mockExam']}前の演習として{c['studyModes']}と併用可能。"
            "検索・絞り込みと解説ページに対応。"
        )
    else:
        base = (
            f"{ex}の一問一答{count}問を年度・分野別に掲載。"
            f"{c['mockExam']}・本番前の{c['studyModes']}学習に対応。"
            "検索・絞り込みと解説に対応。"
        )
    return meta_description(base, 155)


_ICHIMON_META_SUFFIX_RE = re.compile(
    r"(は正しい|は誤り|は誤っている|は正しくない|は間違い)[。．]?\s*$"
)


def ichimon_meta_snippet(statement: str, *, answer: str = "") -> str:
    """一問一答 meta 用。設問末尾の「は正しい」等を除去（正答記号は answer_tail で付与）。"""
    s = (statement or "").strip()
    return _ICHIMON_META_SUFFIX_RE.sub("", s).rstrip("。． ")


def question_meta_description(
    mode: str,
    *,
    headline: str,
    category: str,
    body: str = "",
    answer_tail: str = "",
) -> str:
    """各問ページの meta description（問題文抜粋＋正答＋モード横断の一言）。"""
    c = seo_copy()
    prefix = f"{headline}・{category}。"
    if mode == "past":
        tail = f"{c['mockExam']}対策や{c['studyModes']}と併用して学習できます。"
    elif mode == "practice":
        tail = (
            f"{c['mockExam']}前の演習として{c['studyModes']}と併用できます。"
            "選択肢と解説を掲載。"
        )
    else:
        tail = f"{c['mockExam']}前の確認に。{c['studyModes']}と併用できます。正誤と解説を掲載。"
    ans = (answer_tail or "").strip()
    ans_part = f" 正答: {ans}。" if ans else ""
    core = body.strip() if body.strip() else tail
    if body.strip():
        combo = prefix + core + ans_part
        if len(combo) + len(tail) <= 140:
            return meta_description(combo + tail, 155)
        if len(combo) <= 150:
            return meta_description(combo, 155)
        return meta_description(prefix + core[: max(40, 120 - len(prefix) - len(ans_part))] + ans_part, 155)
    combo = prefix + ans_part + tail if ans_part else prefix + tail
    return meta_description(combo, 155)


def index_search_placeholder(mode: str) -> str:
    if mode == "ichimon":
        return "例：2026-01-1、分野、問題文…"
    return "例：第1問、分野、問題文…"


def index_search_index_suffix() -> str:
    """一覧 JSON の search 列に足す共通キーワード。"""
    c = seo_copy()
    return f"{c['mockExam']} {c['studyModes']}"


def index_h1(mode: str) -> str:
    """一覧ページの H1（試験名＋モード名を先頭に）。"""
    return f"{exam_name()} {MODE_LABEL[mode]}"


def index_page_title(mode: str, *, count: int | None = None) -> str:
    """一覧ページの <title>（試験名・モード・模試キーワード・ブランド）。

    過去問は GSC で「過去問 web / 無料 / pdf / ダウンロード」の検索が多いため、
    問題数と「Web無料・解説付き」を題名の前半に置く（2026-11 クリック率改善）。
    「PDF不要」は pdf・ダウンロードで探す人に「PDFは無い」と読まれるため使わない。
    """
    c = seo_copy()
    label = MODE_LABEL[mode]
    if mode == "past":
        if count:
            return f"{exam_name()} {label}{count}問【Web無料・解説付き・印刷/PDF保存OK】｜{brand_title_suffix()}"
        sub = "Web無料・模試対策"
    elif mode == "practice":
        sub = f"{c['mockExam']}前の演習"
    else:
        sub = f"{c['mockExam']}前の確認"
    return f"{exam_name()} {label}一覧｜{sub}｜{brand_name()}"


def past_year_display(year: int, wareki: str = "") -> str:
    """過去問の年度表示。exam_wareki があれば優先（20202 等の内部 ID を避ける）。"""
    w = (wareki or "").strip()
    if w:
        return w
    return f"{year}年"


def question_h1(
    mode: str,
    *,
    year: int = 0,
    qno: int = 0,
    question_id: str = "",
    category: str = "",
    year_label: str = "",
) -> str:
    """各問ページの H1（試験名＋モード＋識別子＋分野）。"""
    ex = exam_name()
    label = MODE_LABEL[mode]
    if mode == "past":
        yl = (year_label or "").strip() or past_year_display(year)
        return f"{ex} {label} {yl} 第{qno}問（{category}）"
    if mode == "practice":
        return f"{ex} {label} 第{qno}問（{category}）"
    return f"{ex} {label} {question_id}（{category}）"


def question_page_title(
    mode: str,
    *,
    year: int = 0,
    qno: int = 0,
    question_id: str = "",
    category: str = "",
    year_label: str = "",
) -> str:
    """各問ページの <title>。"""
    return (
        f"{question_h1(mode, year=year, qno=qno, question_id=question_id, category=category, year_label=year_label)}"
        f"｜{brand_name()}"
    )


def question_meta_headline(
    mode: str,
    *,
    year: int = 0,
    qno: int = 0,
    question_id: str = "",
    year_label: str = "",
) -> str:
    """各問 meta description の headline 用。"""
    ex = exam_name()
    label = MODE_LABEL[mode]
    if mode == "past":
        yl = (year_label or "").strip() or past_year_display(year)
        return f"{ex}の{label} {yl} 第{qno}問"
    if mode == "practice":
        return f"{ex}の{label} 第{qno}問"
    return f"{ex}の{label} {question_id}"
