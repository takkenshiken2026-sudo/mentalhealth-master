#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Create or refresh data/*.csv stubs for validate_csv (phase 1 foundation)."""

from __future__ import annotations

import csv
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
CHECKLIST = ROOT / "docs" / "glossary-terms-checklist.csv"

GUIDE_HEADER = [
    "slug",
    "genre",
    "title",
    "meta_description",
    "lead",
    "priority",
    "tags",
    "author_name",
    "author_profile",
    "reviewer_name",
    "reviewer_profile",
    "fact_checked_at",
    "primary_sources",
    "original_note",
    "user_intent",
    "action_items",
    "update_policy",
    "last_reviewed_at",
    "next_review_at",
    "source_checked_at",
    "content_status",
    "revision_note",
    "section_1_heading",
    "section_1_body",
    "section_2_heading",
    "section_2_body",
    "section_3_heading",
    "section_3_body",
    "section_4_heading",
    "section_4_body",
    "section_5_heading",
    "section_5_body",
    "faq_1_question",
    "faq_1_answer",
    "faq_2_question",
    "faq_2_answer",
    "related_links",
]

GLOSSARY_HEADER = [
    "term",
    "reading",
    "category",
    "tags",
    "short_def",
    "definition",
    "related_terms",
    "legal_basis",
    "importance",
    "explanation",
]

OFFICIAL_SOURCES = (
    "試験のご紹介（公式）|https://www.mental-health.ne.jp/about/;"
    "公開試験 受験要項（公式）|https://www.mental-health.ne.jp/guide/;"
    "公式テキスト（公式）|https://www.mental-health.ne.jp/text/"
)

AUTHOR = "メンタルヘルス二種マスター編集部"
AUTHOR_PROFILE = "メンタルヘルス・マネジメント検定II種向けの学習コンテンツを整理する編集チーム"
REVIEWER = "公式情報確認担当"
REVIEWER_PROFILE = "公開前に公式サイト・受験要項との照合を行う担当者"
FACT_DATE = "2026-05-19"


def write_csv(path: Path, header: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=header, extrasaction="ignore")
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in header})


def bootstrap_glossary() -> int:
    if not CHECKLIST.is_file():
        print(f"skip glossary: {CHECKLIST} not found", file=sys.stderr)
        return 0
    rows_out: list[dict[str, str]] = []
    with CHECKLIST.open(encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            term = (row.get("用語") or "").strip()
            if not term:
                continue
            category = (row.get("カテゴリ") or "").strip()
            definition = (row.get("解説") or "").strip()
            short = definition.split("。")[0] + "。" if definition else term
            if len(short) > 120:
                short = short[:117] + "…"
            rows_out.append(
                {
                    "term": term,
                    # フェーズ1: checklist に読みがないため term を仮置き（フェーズ3でひらがな整備）
                    "reading": term,
                    "category": category,
                    "tags": category,
                    "short_def": short,
                    "definition": definition,
                    "related_terms": "",
                    "legal_basis": "",
                    "importance": "A",
                    "explanation": definition[:500] if definition else short,
                }
            )
    write_csv(DATA / "glossary_terms.csv", GLOSSARY_HEADER, rows_out)
    print(f"wrote glossary_terms.csv ({len(rows_out)} rows)")
    return len(rows_out)


def article_row(
    slug: str,
    genre: str,
    title: str,
    meta: str,
    lead: str,
    priority: int,
    tags: str,
    sections: list[tuple[str, str]],
    faq: list[tuple[str, str]],
    related: str,
    note: str,
) -> dict[str, str]:
    row: dict[str, str] = {
        "slug": slug,
        "genre": genre,
        "title": title,
        "meta_description": meta,
        "lead": lead,
        "priority": str(priority),
        "tags": tags,
        "author_name": AUTHOR,
        "author_profile": AUTHOR_PROFILE,
        "reviewer_name": REVIEWER,
        "reviewer_profile": REVIEWER_PROFILE,
        "fact_checked_at": FACT_DATE,
        "primary_sources": OFFICIAL_SOURCES,
        "original_note": note,
        "user_intent": lead,
        "action_items": "公式情報を確認する;用語集で重要語を確認する;一問一答で弱点を洗い出す",
        "update_policy": "試験要項や公式ページが更新されたタイミングで本文と参照元を見直します。",
        "last_reviewed_at": FACT_DATE,
        "next_review_at": "2026-06-19",
        "source_checked_at": FACT_DATE,
        "content_status": "review_needed",
        "revision_note": "フェーズ1: CSV土台を追加。本文はルール準拠のリライト待ち。",
    }
    for i, (heading, body) in enumerate(sections[:5], start=1):
        row[f"section_{i}_heading"] = heading
        row[f"section_{i}_body"] = body
    for i, (q, a) in enumerate(faq[:2], start=1):
        row[f"faq_{i}_question"] = q
        row[f"faq_{i}_answer"] = a
    row["related_links"] = related
    return row


def bootstrap_guide_articles() -> None:
    rows = [
        article_row(
            "overview",
            "試験概要",
            "メンタルヘルス・マネジメント検定II種の概要と最初に確認するポイント",
            "メンタルヘルス・マネジメント検定II種（ラインケアコース）の対象者、出題内容、試験時間、合格基準を公式情報ベースで整理します。",
            "管理監督者向けのメンタルヘルス・マネジメント検定II種を受験する前に、試験の目的と出題範囲の全体像を押さえるための記事です。",
            10,
            "試験概要;公式情報",
            [
                ("独学前に公式情報を確認する", "試験日程・申込方法・出題範囲・合格基準は年度ごとに変わることがあります。学習前に公益財団法人 日本産業衛生協会の公式ページで最新の受験案内を確認してください。"),
                ("Ⅱ種（ラインケアコース）の目的を理解する", "管理監督者が部下のメンタルヘルス対策を進めるための知識を確認する試験です。気づく・聴く・つなぐ・職場環境を整える流れを意識して学習します。"),
                ("出題範囲を7領域で整理する", "公式テキストの7章構成（基礎・役割、ストレス基礎、職場環境、配慮、相談、連携、復職）に沿って用語と演習を進めると効率的です。"),
                ("このサイトでの学習の進め方", "用語集で重要語を確認し、一問一答とオリジナル問題で弱点を洗い出します。記録機能で復習対象を残せます。"),
                ("次に読むページ", "日程・勉強法・分野別の重要論点記事へ進み、学習計画を具体化します。"),
            ],
            [
                ("公式情報はどこで確認しますか？", "試験のご紹介、受験要項、公式テキストの各ページで確認します。非公式情報と異なる場合は公式を優先してください。"),
                ("誰が受験対象ですか？", "主に管理監督者・管理職向けのラインケアコースです。詳細は公式の対象者説明を確認してください。"),
            ],
            "schedule:試験日程・受験料;study-plan:勉強方法;subjects:出題範囲",
            "試験概要の入口記事。フェーズ2で信頼性ブロック付き本文へ拡張予定。",
        ),
        article_row(
            "schedule",
            "受験要項",
            "メンタルヘルス・マネジメント検定II種の試験日程・受験料・当日の持ち物",
            "公開試験の日程、受験料、試験時間、当日の持ち物を受験要項ベースで確認するためのガイドです。",
            "申込前に日程と費用、当日必要なものを漏れなく確認したい受験者向けの記事です。",
            20,
            "受験要項;日程",
            [
                ("最新の受験要項を開く", "公開試験の実施回、申込期間、受験料、会場情報は受験要項で確認します。年度が変わると更新されるため、申込直前にも再確認してください。"),
                ("試験当日の持ち物を準備する", "受験票、筆記用具、身分証明書など、要項に記載された持ち物を前日までに揃えます。"),
                ("試験時間と合格基準を確認する", "選択問題・試験時間・合格点は要項と試験のご紹介で確認します。学習計画の目標設定にも使います。"),
            ],
            [
                ("受験料はいくらですか？", "年度・実施回により異なるため、最新の受験要項で確認してください。"),
                ("申込後に日程を変更できますか？", "変更可否や手続きは受験要項・事務局案内に従ってください。"),
            ],
            "overview:試験概要;study-plan:勉強方法",
            "受験要項の要点整理。数値は申込前に要項で再確認。",
        ),
        article_row(
            "study-plan",
            "学習計画",
            "メンタルヘルス・マネジメント検定II種の勉強方法｜7章をどう進めるか",
            "7つの出題領域を基礎・職場環境・相談連携復職に分けて学ぶ勉強法を整理します。",
            "独学で合格を目指す管理監督者が、教材を増やす前に学習の順序と復習の仕組みを決めるための記事です。",
            30,
            "勉強法;学習計画",
            [
                ("全体像を7章で把握する", "公式テキストの章立てに沿い、まず各章のキーワードを用語集で一周します。"),
                ("演習と復習をセットにする", "一問一答で穴を見つけ、オリジナル問題で選択肢の読み方を練習します。間違えた問題は復習リストに残します。"),
                ("直前期は範囲を絞る", "新しい教材を増やしすぎず、間違えた分野と重要用語に集中します。"),
            ],
            [
                ("何週間で勉強すればよいですか？", "前提知識や1日の学習時間によります。余裕を持った計画を立て、週次で復習日を入れてください。"),
                ("過去問はありますか？", "公開状況は年度により異なります。本サイトの演習と公式テキストを中心に進め、公式情報も確認してください。"),
            ],
            "overview:試験概要;subjects:出題範囲;line-care:ラインケア",
            "学習計画のたたき台。フェーズ2で分量を拡張。",
        ),
        article_row(
            "subjects",
            "出題範囲",
            "メンタルヘルス・マネジメント検定II種の科目一覧・出題範囲｜7章を整理",
            "7章41トピックの出題範囲と、優先して確認したい論点を整理します。",
            "出題範囲の全体像を一覧で把握し、学習の優先順位を決めたい人向けの記事です。",
            40,
            "出題範囲;科目",
            [
                ("7領域の役割を理解する", "基礎・役割、ストレス基礎、職場環境、配慮、相談、連携、復職の各領域が試験全体を構成します。"),
                ("用語と演習を往復する", "各章の重要語を用語集で確認し、関連する一問一答・オリジナル問題で定着を確認します。"),
            ],
            [
                ("出題範囲は毎年変わりますか？", "公式テキストの改訂に合わせて見直されます。最新のテキスト情報を確認してください。"),
                ("どの分野から始めるべきですか？", "基礎・役割とストレス基礎を先に押さえ、その後職場環境・配慮へ進めると理解しやすいです。"),
            ],
            "study-plan:勉強方法;overview:試験概要",
            "科目一覧の索引記事。詳細表はフェーズ2で拡充。",
        ),
        article_row(
            "line-care",
            "分野別対策",
            "ラインケアとは？管理監督者が押さえる役割",
            "メンタルヘルス・マネジメント検定II種で重要なラインケアについて、気づき・相談・職場環境改善の観点から解説します。",
            "管理監督者としてラインケアの意味と実務での役割分担を整理したい人向けの記事です。",
            50,
            "ラインケア;重要論点",
            [
                ("ラインケアの4つのケアを整理する", "セルフケア、ラインケア、事業場内・外資源の役割を混同しないよう表で整理します。"),
                ("抱え込まない対応を確認する", "管理監督者は医学的診断や治療判断をせず、専門職への連携を意識します。"),
            ],
            [
                ("ラインケアは誰の役割ですか？", "主に管理監督者が担う職場でのケアです。産業医・保健師等との連携が重要です。"),
                ("セルフケアとの違いは？", "セルフケアは本人の対処、ラインケアは職場での支援・環境改善の流れです。"),
            ],
            "stress-check:ストレスチェック;return-to-work:職場復帰",
            "ラインケア論点の整理記事。",
        ),
        article_row(
            "stress-check",
            "制度理解",
            "ストレスチェック制度とは？二種で押さえるポイント",
            "ストレスチェック制度について、目的、集団分析、面接指導の考え方を試験向けに整理します。",
            "ストレスチェックの制度理解と管理監督者の関わり方を確認したい人向けの記事です。",
            60,
            "ストレスチェック;制度",
            [
                ("制度の目的を確認する", "労働者のストレスへの気づきと職場環境改善につなげる制度であることを押さえます。"),
                ("個人情報と集団分析の違い", "個人結果の取り扱いと、集団分析による職場改善の流れを分けて理解します。"),
            ],
            [
                ("結果は事業者に自動で渡りますか？", "原則、本人同意なく個人結果を事業者に提供することはできません。設問の意図を確認してください。"),
                ("管理監督者が実施者になれますか？", "実施者は医師・保健師等が担うのが基本です。誤り選択肢に注意してください。"),
            ],
            "line-care:ラインケア;subjects:出題範囲",
            "ストレスチェック制度の要点。",
        ),
        article_row(
            "return-to-work",
            "復職支援",
            "職場復帰支援の5ステップ｜二種で覚える流れ",
            "心の健康問題で休業した労働者の職場復帰支援について、5ステップの流れと管理監督者の役割を整理します。",
            "復職支援の手順と関係者の役割を試験用に整理したい人向けの記事です。",
            70,
            "復職支援;職場復帰",
            [
                ("5ステップの順序を覚える", "休業・診断・復帰判断・復帰決定・フォローアップの流れを順番通りに確認します。"),
                ("段階的復帰を理解する", "業務量・時間を調整しながら無理のない復帰を進める考え方を押さえます。"),
            ],
            [
                ("管理監督者が診断しますか？", "医学的診断は医師が行います。管理監督者は職場での配慮と連携が中心です。"),
                ("復職支援プランは誰が作りますか？", "関係者で協議して作成します。産業医・人事・本人などが関わる場面を理解します。"),
            ],
            "line-care:ラインケア;study-plan:勉強方法",
            "職場復帰支援の要点。",
        ),
    ]
    write_csv(DATA / "guide_articles.csv", GUIDE_HEADER, rows)
    print(f"wrote guide_articles.csv ({len(rows)} rows)")


def bootstrap_quiz_stubs() -> None:
    """Minimal rows so validate_csv passes. Full rebuild requires real CSV exports."""
    write_csv(
        DATA / "past_questions.csv",
        [
            "exam_year",
            "exam_wareki",
            "question_no",
            "type",
            "category",
            "stem",
            "choice_1",
            "choice_2",
            "choice_3",
            "choice_4",
            "correct",
            "is_invalidated",
            "explanation",
        ],
        [
            {
                "exam_year": "2026",
                "exam_wareki": "サンプル",
                "question_no": "1",
                "type": "single",
                "category": "基礎・役割",
                "stem": "（過去問CSVのプレースホルダー。本番データ投入前に置き換えてください）",
                "choice_1": "選択肢1",
                "choice_2": "選択肢2",
                "choice_3": "選択肢3",
                "choice_4": "選択肢4",
                "correct": "1",
                "is_invalidated": "FALSE",
                "explanation": "プレースホルダー行です。",
            }
        ],
    )
    write_csv(
        DATA / "original_questions.csv",
        [
            "question_no",
            "type",
            "category",
            "stem",
            "choice_1",
            "choice_2",
            "choice_3",
            "choice_4",
            "correct",
            "explanation",
        ],
        [
            {
                "question_no": "1",
                "type": "single",
                "category": "基礎・役割",
                "stem": "（オリジナル問題CSVのプレースホルダー。既存 eisei1-master-data.js を上書きしないよう FULL ビルド注意）",
                "choice_1": "選択肢1",
                "choice_2": "選択肢2",
                "choice_3": "選択肢3",
                "choice_4": "選択肢4",
                "correct": "1",
                "explanation": "プレースホルダー行です。",
            }
        ],
    )
    write_csv(
        DATA / "past_questions_marubatsu_all_explanations.csv",
        ["id", "question", "answer", "explanation", "category"],
        [
            {
                "id": "2026-01-1",
                "question": "（一問一答CSVプレースホルダー）",
                "answer": "○",
                "explanation": "プレースホルダー行です。",
                "category": "基礎・役割",
            }
        ],
    )
    print("wrote past_questions.csv, original_questions.csv, past_questions_marubatsu (stubs)")


def main() -> int:
    n = bootstrap_glossary()
    bootstrap_guide_articles()
    bootstrap_quiz_stubs()
    print("bootstrap_data_csv: done")
    if n == 0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
