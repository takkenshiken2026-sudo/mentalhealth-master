#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""用語339件の読みやすさ向上（文体・要点の具体例・覚え方・FAQ4件）。

正本: data/glossary_terms.csv
前提: rewrite_glossary_handcrafted.py 実行後に適用する。
"""

from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.rewrite_glossary_handcrafted import (  # noqa: E402
    PastBundle,
    SourceParts,
    build_past_bundle,
    find_past_row,
    load_checklist,
    load_past_index,
    norm,
    parse_source,
    split_sents,
)

CSV_PATH = ROOT / "data" / "glossary_terms.csv"

NEW_COLUMNS = ("key_summary", "faq_4_question", "faq_4_answer")

SIMPLIFY_REPLACEMENTS: tuple[tuple[str, str], ...] = (
    ("根拠・対象・責任主体がずれる", "意味やルールと合わない"),
    ("定義・根拠・担当者のいずれかがずれていないか確認", "定義や制度の内容と合っているか確かめましょう"),
    ("制度の趣旨と矛盾する場合があります", "制度の考え方と逆の内容になることがあります"),
    ("単語暗記より、誰が何を担うか・根拠法令は何かをセットで押さえます", "名前だけ覚えるのではなく、「誰が」「何を」するのかまでセットで整理しましょう"),
    ("関連用語（", "あわせて覚えたい用語（"),
    ("）との違いもセットで整理してください", "）の違いも、表にまとめると覚えやすくなります"),
    ("演習キーワード：", "試験で出やすいキーワード："),
    ("試験で押さえる要点：", "ここが試験のポイント："),
    ("誤り肢の例：", "間違えやすい選択肢の例："),
    ("誤答肢の参考：", "ほかの間違えやすい選択肢："),
    ("管理監督者が医学的診断をせず、観察と専門職連携の文脈で理解します", "管理監督者は診断をせず、様子を見て専門家につなぐ立場だと理解しましょう"),
    ("定義・演習の出題パターン・混同点を整理します", "意味・試験の出方・混同しやすい点を、わかりやすく整理します"),
    ("定義と選択肢を1語ずつ照合してください", "選択肢を1つずつ読み、定義と合うか確かめましょう"),
)

CATEGORY_WORKPLACE: dict[str, str] = {
    "基礎・役割": "職場では、管理監督者が医学的な診断をせず、観察と専門職への連携が基本になります。",
    "職場環境・配慮": "職場では、個人の努力だけでなく、環境や仕組みをどう整えるかまで含めて考えます。",
    "相談・連携・復職": "職場では、本人の話を聴いたうえで、産業医・主治医・社外の相談先につなぐ流れが大切です。",
}


def ensure_columns(fieldnames: list[str]) -> list[str]:
    out = list(fieldnames)
    for col in NEW_COLUMNS:
        if col not in out:
            insert_at = out.index("faq_3_answer") + 1 if "faq_3_answer" in out else len(out)
            out.insert(insert_at, col)
    return out


def simplify_text(text: str) -> str:
    out = norm(text)
    if not out:
        return out
    for old, new in SIMPLIFY_REPLACEMENTS:
        out = out.replace(old, new)
    out = re.sub(r"ことに関連する重要語です", "試験で押さえる用語です", out)
    out = re.sub(r"\s+", " ", out)
    return out.strip()


def first_sentence(text: str, max_len: int = 120) -> str:
    sents = split_sents(text)
    s = sents[0] if sents else text
    if len(s) > max_len:
        s = s[: max_len - 1] + "…"
    return s.rstrip("。")


def build_concrete_example(
    term: str,
    category: str,
    past: PastBundle | None,
    example_q: str,
    example_a: str,
) -> str:
    if example_q and len(example_q) > 15:
        q = example_q[:95].rstrip("。")
        if len(example_q) > 95:
            q += "…"
        if example_a.startswith("×"):
            return (
                f"試験では「{q}」のような選択肢が出ることがあります。"
                f"この場合は誤り（×）で、{term}の意味と照らし合わせて判断します。"
            )
        return f"試験では「{q}」のような選択肢で、{term}の理解を確かめられます。"

    if past and past.wrong_choices:
        w = past.wrong_choices[0][:80].rstrip("。")
        return (
            f"例えば「{w}…」と書かれた選択肢は、{term}の内容と合わないことが多いです。"
            f"「〜のみ」「〜不要」のような言い切りに注意しましょう。"
        )

    workplace = CATEGORY_WORKPLACE.get(category, CATEGORY_WORKPLACE["基礎・役割"])
    return f"{workplace} {term}は、この流れの中でどこに位置づくかをイメージすると理解しやすくなります。"


def build_key_summary(
    term: str,
    short: str,
    category: str,
    src: SourceParts,
    past: PastBundle | None,
    example_q: str,
    example_a: str,
) -> str:
    plain = simplify_text(first_sentence(short or src.core))
    parts = [f"一言で言うと、{plain.rstrip('。')}。"]

    example = build_concrete_example(term, category, past, example_q, example_a)
    parts.append(example)

    if src.key_point:
        kp = src.key_point[:100].rstrip("。")
        parts.append(f"試験では「{kp}」のような表現が、正答のヒントになることがあります。")
    elif past and past.correct:
        kp = past.correct[:100].rstrip("。")
        parts.append(f"演習第{past.qno}問では「{kp}…」の趣旨が正答になります。")

    return "\n\n".join(parts)


def build_memory_tip_detailed(
    term: str,
    short: str,
    category: str,
    related: list[str],
    past: PastBundle | None,
    mistakes: str,
) -> str:
    def_line = first_sentence(short, 80).rstrip("。")
    if def_line.startswith(term):
        rest = def_line[len(term) :].lstrip("は、").strip()
        def_line = rest or def_line
    steps = [f"①定義メモ：{term}＝{def_line}"]

    if past:
        steps.append(f"②演習連携：演習第{past.qno}問の正答キーワードを横に書いておく")
    else:
        steps.append(f"②分野整理：{category}の用語一覧に{term}を1行追加する")

    trap = ""
    if past and past.wrong_choices:
        trap = past.wrong_choices[0][:55].rstrip("。")
    elif mistakes:
        trap = mistakes.split(";")[0][:55].rstrip("。")
    if trap:
        steps.append(f"③誤答チェック：「{trap}…」のような言い切り（のみ・必ず・不要）に注意")
    else:
        steps.append("③誤答チェック：「〜のみ」「〜不要」など、言い切りすぎた選択肢は疑う")

    if related:
        steps.append(f"④関連整理：{'・'.join(related[:3])}と表で並べて違いを書く")
    else:
        steps.append("④確認：関連演習を1問だけ解いて、正誤を確認する")

    return "\n".join(steps)


def build_faq_four(
    term: str,
    category: str,
    short: str,
    src: SourceParts,
    past: PastBundle | None,
    mistakes: str,
    related: list[str],
    example_q: str,
) -> dict[str, str]:
    plain_short = simplify_text(short)

    faq1 = plain_short.rstrip("。") + "。"
    if src.extra_sents:
        for s in src.extra_sents[:2]:
            s2 = simplify_text(s)
            if s2.rstrip("。") not in faq1 and len(s2) > 12:
                faq1 += s2 if s2.endswith("。") else s2 + "。"
                break

    if past:
        faq2 = (
            f"演習第{past.qno}問のように、「{term}の意味や制度の位置づけはどれか」"
            f"という選択肢問題で出ます。正答は「{past.correct[:70].rstrip('。')}…」の考え方に近いものを選びます。"
        )
    elif example_q:
        faq2 = (
            f"「{example_q[:80].rstrip('。')}…」のような選択肢で、"
            f"{term}の理解を確かめる問題が出ます。意味と選択肢を1つずつ照らし合わせましょう。"
        )
    else:
        faq2 = (
            f"{category}分野では、{term}の意味と「誰が」「何を」担うかがセットで問われます。"
            f"関連演習で正答の言い回しを確認してください。"
        )

    if past and past.wrong_choices:
        w = past.wrong_choices[0][:100].rstrip("。")
        faq3 = (
            f"「{w}…」のように、{term}の内容と合わない選択肢に注意してください。"
            f"「〜のみ」「〜不要」など、言い切り表現を見逃さないでください。"
        )
    elif mistakes:
        m1 = mistakes.split(";")[0][:120].rstrip("。")
        faq3 = f"「{m1}」のように、{term}の内容と逆のことを書いた選択肢に注意してください。定義と1語ずつ照合すると安全です。"
    else:
        faq3 = "似た用語との混同と、言い切り表現（のみ・必ず・不要）の2点に注意してください。"

    if related:
        faq4 = (
            f"覚え方のコツは、{term}の定義を1行で書き、"
            f"関連用語（{'・'.join(related[:3])}）との違いを表にまとえることです。"
            f"演習で1問解いて定着を確認しましょう。"
        )
    elif past:
        faq4 = (
            f"ノートに「{term}＝定義1行」と「演習第{past.qno}問の正答キーワード」を横並びで書くと、"
            f"試験直前の復習がしやすくなります。"
        )
    else:
        faq4 = (
            f"定義を1行、職場での役割を1行、試験の注意点を1行——の3行メモにすると、"
            f"{term}を整理しやすくなります。"
        )

    return {
        "faq_1_question": f"{term}とは何ですか？",
        "faq_1_answer": faq1,
        "faq_2_question": f"{term}は試験でどう出題されますか？",
        "faq_2_answer": faq2,
        "faq_3_question": f"{term}で間違えやすい点は？",
        "faq_3_answer": faq3,
        "faq_4_question": f"{term}の覚え方・関連用語は？",
        "faq_4_answer": faq4,
    }


def simplify_body(text: str) -> str:
    out = simplify_text(text)
    if not out:
        return out
    # 長い段落を2文ごとに改行
    sents = split_sents(out)
    if len(sents) <= 3:
        return out
    chunks: list[str] = []
    buf: list[str] = []
    for s in sents:
        buf.append(s if s.endswith("。") else s + "。")
        if len(buf) >= 2:
            chunks.append("".join(buf))
            buf = []
    if buf:
        chunks.append("".join(buf))
    return "\n\n".join(chunks)


def simplify_lead(term: str, category: str, short: str, old_lead: str) -> str:
    hook = first_sentence(short or old_lead, 70).rstrip("。")
    return (
        f"このページでは、{exam_label()}の「{term}」を、専門用語をできるだけ少なく使って説明します。"
        f"{hook}。"
        f"意味・試験の出方・覚え方まで、順番に確認できます。"
    )


def exam_label() -> str:
    return "メンタルヘルスII種"


def filter_related(raw: str, valid: set[str]) -> list[str]:
    out: list[str] = []
    for t in re.split(r"[;、,]", raw):
        t = t.strip()
        if not t or "確認すると理解" in t or len(t) > 35:
            continue
        if t in valid and t not in out:
            out.append(t)
    return out[:4]


def enrich_row(
    row: dict[str, str],
    checklist: dict[str, str],
    past_index: dict[int, dict[str, str]],
    valid_terms: set[str],
) -> None:
    term = norm(row.get("term"))
    if not term:
        return

    category = norm(row.get("category"))
    text = checklist.get(term) or norm(row.get("definition"))
    src = parse_source(term, text)
    past_row = find_past_row(term, norm(row.get("practice_question")), past_index)
    past = build_past_bundle(past_row)
    related = filter_related(norm(row.get("related_terms")), valid_terms)

    short = simplify_text(norm(row.get("short_def")) or first_sentence(src.core))
    row["short_def"] = short

    example_q = norm(row.get("example_question"))
    example_a = norm(row.get("example_answer"))
    mistakes = norm(row.get("common_mistakes"))

    row["key_summary"] = build_key_summary(term, short, category, src, past, example_q, example_a)
    row["memory_tip"] = build_memory_tip_detailed(term, short, category, related, past, mistakes)

    for k, v in build_faq_four(term, category, short, src, past, mistakes, related, example_q).items():
        row[k] = v

    if norm(row.get("term_detail_body")):
        row["term_detail_body"] = simplify_body(norm(row.get("term_detail_body")))
    if norm(row.get("explanation")):
        row["explanation"] = simplify_text(norm(row.get("explanation")))
    if norm(row.get("article_lead")):
        row["article_lead"] = simplify_lead(term, category, short, norm(row.get("article_lead")))


def load_glossary_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)
    return fieldnames, rows


def main() -> int:
    checklist = load_checklist()
    past_index = load_past_index()

    fieldnames, rows = load_glossary_csv(CSV_PATH)
    fieldnames = ensure_columns(fieldnames)
    valid = {norm(r.get("term")) for r in rows if norm(r.get("term"))}

    for row in rows:
        enrich_row(row, checklist, past_index, valid)

    with CSV_PATH.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

    has_summary = sum(1 for r in rows if norm(r.get("key_summary")))
    faq4 = sum(1 for r in rows if norm(r.get("faq_4_question")) and norm(r.get("faq_4_answer")))
    mem_lines = sum(1 for r in rows if norm(r.get("memory_tip")).count("\n") >= 3)
    print(
        f"readability: terms={len(rows)}, key_summary={has_summary}/{len(rows)}, "
        f"faq4={faq4}/{len(rows)}, memory_4steps={mem_lines}/{len(rows)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
