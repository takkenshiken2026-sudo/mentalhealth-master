#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""試験ガイド・用語詳細の編集品質（専門家・プロライター水準）の共通判定."""

from __future__ import annotations

import re
from dataclasses import dataclass

# 専門家記事らしい具体性（実データに基づく信号のみ）。
# ※「例えば」「たとえば」「例：」は量産文が偽の例示で加点を稼ぐ温床になるため含めない。
CONCRETENESS_RE = re.compile(
    r"\d|％|%|条|項|科目|分野|領域|公式テキスト|厚生労働省|指針|しかし|一方で|具体的"
)

# --- 量産テンプレの構造パターン / 他資格混入（published 本文・FAQ で ERROR）---

# 作り物の例示日付（M/D（曜）のスラッシュ表記）。実在の試験日は「3月21日（日）」等の漢字表記で書く。
FABRICATED_DATE_RE = re.compile(r"\d{1,2}/\d{1,2}（[日月火水木金土]）")

# 量産文がフラグメントを連ねる長ダッシュ（——）
EMDASH_CHAIN = "——"

# メンタルヘルス・マネジメント検定に存在しない他資格テンプレ由来の語（ERROR）。
# 誤検出を避けるため高精度な語のみ。除外した語と理由:
#  - 「衛生管理者」: 職場の衛生管理者は連携先として正当に登場する
#  - 「CBT」: 認知行動療法（Cognitive Behavioral Therapy）として正当
#  - 「電卓」: 持ち物記事で「電卓は不可」等の正当な言及がある
#  - 「公式」「計算」単体: 公式テキスト/公式情報など正当用例が多い
OTHER_EXAM_VOCAB: tuple[str, ...] = (
    "指定数量",
    "35条書面",
    "宅地建物取引",
    "宅建",
    "危険物取扱",
    "簿記",
    "仕訳",
    "計算問題",
    "計算ドリル",
    "計算式",
    "割合の計算",
)

# 読者本文に露出してはいけない内部 slug 風の英ハイフン語（URL/タグ除外後に検出）。
_ASCII_SLUG_RE = re.compile(r"[a-z]{2,}(?:-[a-z0-9]{2,})+")
_HTML_TAG_RE = re.compile(r"<[^>]+>")
_URL_RE = re.compile(r"https?://\S+")
ASCII_SLUG_LEAK_ALLOW: frozenset[str] = frozenset(
    {"line-care", "work-life-balance", "e-mail"}
)

# 公開前に必ず消す雛形マーカー（ERROR）
EDITORIAL_PLACEHOLDER_MARKERS: tuple[str, ...] = (
    "【記入】",
    "【本文を記入】",
    "【リードを記入】",
    "【短い定義】",
    "【定義】",
    "【誤解】",
    "【覚え方】",
    "【例題】",
    "【解説を記入】",
    "【40文字以上】",
    "【選択肢の論点を記入】",
    "【読者が",
    "差し替えてください",
    "プレースホルダ",
)

# 量産・scaffold 後の使い回し禁止（ERROR — published の section / FAQ）
EDITORIAL_BOILERPLATE_PHRASES: tuple[str, ...] = (
    "の観点で整理します",
    "制度・数値・日程は年度や改正で変わるため、学習前と申込前には試験実施団体（公式）の最新情報を確認してください",
    "非公式まとめは参考程度にし、最終判断は必ず公式要項に置きます",
    "このサイトでは過去問・用語解説・比較表を組み合わせ",
    "間違えた問題は理由を短くメモし、関連用語で定義と選択肢の論点を確認してから同分野へ戻ると定着しやすくなります",
    "まず公式要項で最新の制度を確認してください。本サイトでは過去問演習と用語解説で",
    "数値や期限は資格ごとに異なるため、本文の例は必ず公式情報と照合してください",
    "に関する質問「",
    "理解度を具体的に確かめられます",
    "付箋を付けながら読み",
    "演習で同テーマの設問を1問以上解いて確認",
)

# 薄い・AI丸投げっぽい定型（WARN）
EDITORIAL_GENERIC_PHRASES: tuple[str, ...] = (
    "について説明します",
    "について解説します",
    "が重要です",
    "を理解することが大切",
    "押さえておきましょう",
    "覚えておきましょう",
    "確認することが大切",
    "本番前には試験実施団体の公式情報もあわせて確認してください",
    "制度や数値は年度や改正で変わるため",
)

# 読みやすさ（WARN）— glossary_term_rules と共有
READABILITY_FRAGMENTS: tuple[tuple[str, str], ...] = (
    ("当該", "誰・何を指すかを具体的に書く"),
    ("前述", "前の段落を読んでいない読者にも伝わる書き方にする"),
    ("において", "「では」「で」など平易な言い換えを検討する"),
    ("ものとする", "法令原文の写しではなく、自分の言葉で説明する"),
    ("及び", "「と」「や」など日常語に置き換える"),
    ("することができる", "「できます」に簡潔化する"),
    ("することが可能", "「できます」に簡潔化する"),
)

# --- 試験ガイド（published 行の ERROR 下限は guide_article_rules が参照）---
GUIDE_PRO = {
    "lead": 80,
    "lead_max": 200,
    "meta_description_min": 70,
    "meta_description_max": 165,
    "user_intent": 50,
    "action_item_min": 3,
    "action_item_each": 10,
    "section_count": 5,
    "section_body": 180,
    "faq_answer": 100,
    "related_links": 2,
}

# --- 用語詳細（ERROR 下限は glossary_term_rules.GLOSSARY_MIN_LENGTHS が正本）---
GLOSSARY_PRO = {
    "article_lead": 60,
    "term_detail_body": 180,
    "definition": 50,
    "explanation": 80,
    "common_mistakes": 40,
    "memory_tip": 25,
    "faq_answer": 100,
    "exam_points_as": 3,
    "related_terms_as": 3,
    "paragraphs_in_body": 2,
    "max_sentence_chars": 72,
}

# 編集合格（expert_pass）— 用語詳細の SEO・読者価値の正本下限
GLOSSARY_EXPERT = {
    "article_lead": 80,
    "term_detail_body": 350,
    "definition": 80,
    "explanation": 120,
    "common_mistakes": 60,
    "memory_tip": 40,
    "faq_answer": 120,
    "exam_points_min": 3,
    "exam_points_as": 4,
    "related_terms": 3,
    "related_links_min": 2,
    "paragraphs_in_body": 2,
    "max_sentence_chars": 72,
    "min_faq_concrete": 2,
    "expert_tag": "編集合格",
}


@dataclass(frozen=True)
class EditorialIssue:
    level: str  # ERROR | WARN
    column: str
    message: str


def norm(value: object) -> str:
    return str(value or "").strip()


def split_semicolon(value: str) -> list[str]:
    return [x.strip() for x in value.split(";") if x.strip()]


def split_paragraphs(text: str) -> list[str]:
    return [p.strip() for p in re.split(r"\n{2,}", norm(text)) if p.strip()]


def placeholder_hits(text: str) -> list[str]:
    return [m for m in EDITORIAL_PLACEHOLDER_MARKERS if m in text]


def generic_phrase_hits(text: str) -> list[str]:
    return [p for p in EDITORIAL_GENERIC_PHRASES if p in text]


def readability_issues(text: str, column: str) -> list[EditorialIssue]:
    issues: list[EditorialIssue] = []
    for fragment, hint in READABILITY_FRAGMENTS:
        if fragment in text:
            issues.append(EditorialIssue("WARN", column, f"読みにくい表現「{fragment}」: {hint}"))
    return issues


def placeholder_issues(text: str, column: str) -> list[EditorialIssue]:
    hits = placeholder_hits(text)
    if not hits:
        return []
    shown = "、".join(hits[:3])
    return [
        EditorialIssue(
            "ERROR",
            column,
            f"未執筆の雛形マーカーが残っています（{shown}）。専門家レベルの本文に差し替えてください",
        )
    ]


def boilerplate_hits(text: str) -> list[str]:
    return [p for p in EDITORIAL_BOILERPLATE_PHRASES if p in text]


def boilerplate_issues(text: str, column: str) -> list[EditorialIssue]:
    """量産テンプレ・記事間コピペの禁止句。"""
    hits = boilerplate_hits(text)
    if not hits:
        return []
    shown = "、".join(f"「{h[:24]}…」" if len(h) > 24 else f"「{h}」" for h in hits[:3])
    return [
        EditorialIssue(
            "ERROR",
            column,
            f"機械的な共通文が含まれています（{shown}）。記事固有のオリジナル文に全面差し替えてください",
        )
    ]


def fabricated_date_hits(text: str) -> list[str]:
    return FABRICATED_DATE_RE.findall(text or "")


def other_exam_vocab_hits(text: str) -> list[str]:
    return [w for w in OTHER_EXAM_VOCAB if w in (text or "")]


def ascii_slug_leak_hits(text: str) -> list[str]:
    """読者本文に残った内部 slug 風の英ハイフン語（URL・HTMLタグ・リンクパス除外後）。
    markdown リンク `[ラベル](../slug/)` や相対パスのリンク先は正当なので誤検出しない。"""
    stripped = _HTML_TAG_RE.sub(" ", text or "")
    stripped = _URL_RE.sub(" ", stripped)
    # markdown リンク先 ](...) と相対/絶対パス（../slug/ や /slug/）はリンクなので除外
    stripped = re.sub(r"\]\([^)]*\)", " ", stripped)
    stripped = re.sub(r"\.{0,2}/[A-Za-z0-9_./-]+", " ", stripped)
    out: list[str] = []
    for m in _ASCII_SLUG_RE.finditer(stripped):
        tok = m.group(0)
        if tok in ASCII_SLUG_LEAK_ALLOW:
            continue
        out.append(tok)
    return out


def structural_junk_issues(text: str, column: str) -> list[EditorialIssue]:
    """量産テンプレの構造パターン・他資格混入・内部slug露出（published で ERROR）。
    revision_note の自己申告では免除しない（常時適用）。"""
    issues: list[EditorialIssue] = []
    if not text:
        return issues
    dates = fabricated_date_hits(text)
    if dates:
        shown = "、".join(dates[:3])
        issues.append(
            EditorialIssue(
                "ERROR",
                column,
                f"量産テンプレの作り物の例示日付（{shown} など）が含まれています。"
                f"実在の公開試験日以外の日付例は使わないでください",
            )
        )
    if text.count(EMDASH_CHAIN) >= 2:
        issues.append(
            EditorialIssue(
                "ERROR",
                column,
                "「——」でフラグメントを連ねた量産文です。主語・述語のある通常の文章に書き直してください",
            )
        )
    vocab = other_exam_vocab_hits(text)
    if vocab:
        shown = "、".join(vocab[:3])
        issues.append(
            EditorialIssue(
                "ERROR",
                column,
                f"この検定に存在しない他資格の語が混入しています（{shown}）。"
                f"メンタルヘルス・マネジメント検定固有の内容に差し替えてください",
            )
        )
    leaks = ascii_slug_leak_hits(text)
    if leaks:
        shown = "、".join(dict.fromkeys(leaks))  # dedupe, keep order
        issues.append(
            EditorialIssue(
                "ERROR",
                column,
                f"本文に内部記事名（slug）が露出しています（{shown}）。"
                f"読者向けの記事タイトルや普通の語に置き換えてください",
            )
        )
    return issues


def generic_issues(text: str, column: str, *, min_hits: int = 2) -> list[EditorialIssue]:
    hits = generic_phrase_hits(text)
    if len(hits) < min_hits:
        return []
    return [
        EditorialIssue(
            "WARN",
            column,
            f"汎用・定型表現が多すぎます（{len(hits)}件）。資格固有の具体例・数値・手続に置き換えてください",
        )
    ]


def long_sentence_issues(text: str, column: str, *, max_chars: int) -> list[EditorialIssue]:
    issues: list[EditorialIssue] = []
    for para in split_paragraphs(text) or [text]:
        for sent in re.split(r"[。！？\n]", para):
            s = sent.strip()
            if len(s) > max_chars:
                issues.append(
                    EditorialIssue(
                        "WARN",
                        column,
                        f"1文が長すぎます（{len(s)}字）。{max_chars}字以内に分割すると読みやすくなります",
                    )
                )
                break
    return issues


def concreteness_issues(text: str, column: str) -> list[EditorialIssue]:
    if not text or CONCRETENESS_RE.search(text):
        return []
    return [
        EditorialIssue(
            "WARN",
            column,
            "具体性が不足しています。数字・期限・条文・例示・試験での見方のいずれかを入れてください",
        )
    ]


def duplicate_faq_answers(answers: list[str]) -> list[EditorialIssue]:
    normed = [re.sub(r"\s+", "", a) for a in answers if a]
    if len(normed) < 2:
        return []
    for i, a in enumerate(normed):
        for b in normed[i + 1 :]:
            if not a or not b:
                continue
            shorter, longer = (a, b) if len(a) <= len(b) else (b, a)
            if shorter in longer or _similar_ratio(shorter, longer) > 0.72:
                return [
                    EditorialIssue(
                        "WARN",
                        "faq_*_answer",
                        "FAQの回答が互いに似ています。定義・誤解・試験・次の行動で内容を分けてください",
                    )
                ]
    return []


def _similar_ratio(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    common = sum(1 for ch in a if ch in b)
    return common / max(len(a), len(b))


def is_published_guide(row: dict[str, str]) -> bool:
    status = norm(row.get("content_status")).lower()
    return status in {"", "published", "publish"}
