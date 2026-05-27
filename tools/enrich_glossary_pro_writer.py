#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""用語339件を資格専門家×プロライター品質へ引き上げる最終リライト。"""

from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.enrich_glossary_quality import patch_top20  # noqa: E402
from tools.rewrite_glossary_handcrafted import (  # noqa: E402
    KNOWN_DEFINITIONS,
    PastBundle,
    SourceParts,
    build_core_from_key_point,
    build_past_bundle,
    find_past_row,
    is_broken_key_point,
    load_checklist,
    load_past_index,
    norm,
    parse_source,
    split_sents,
)

CSV_PATH = ROOT / "data" / "glossary_terms.csv"

CATEGORY_EXPERT: dict[str, str] = {
    "基礎・役割": (
        "メンタルヘルスII種の土台となる分野です。"
        "管理監督者は「診断しない・一人で抱え込まない・専門職につなぐ」という原則を、"
        "法令と日常のラインケアの両方から理解しておく必要があります。"
    ),
    "職場環境・配慮": (
        "個人の頑張りだけでなく、職場の仕組み・業務量・情報の扱い方が問われる分野です。"
        "「義務か努力義務か」「誰が実施主体か」「本人同意は必要か」の3点セットで読むと、"
        "選択肢の正誤が見えやすくなります。"
    ),
    "相談・連携・復職": (
        "相談から復職までの流れは、順序・担当者・情報共有の範囲がセットで出題されます。"
        "本人の話を聴くことから始まり、必要な情報だけを関係者間で共有する——"
        "このバランス感覚が試験でも実務でも重要です。"
    ),
}

EXAM_TIPS: dict[str, str] = {
    "基礎・役割": "根拠法令（労基法・労契法・労安法）の取り違えと、管理監督者が医学的判断をする肢に注意してください。",
    "職場環境・配慮": "数値・義務の有無・実施主体を表に整理し、個人結果と集団分析は目的が異なる点を押さえてください。",
    "相談・連携・復職": "手順の順序、主治医と産業医の役割、プライバシーと同意の範囲を、ケース問題で確認してください。",
}


def load_glossary_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader.fieldnames or []), list(reader)


GENERIC_FALLBACK = "メンタルヘルスII種で扱う重要語です"


def is_broken_definition(term: str, text: str) -> bool:
    t = norm(text)
    if not t:
        return True
    if GENERIC_FALLBACK in t:
        return True
    if "ことに関連する重要語" in t:
        return True
    if re.match(rf"^{re.escape(term)}は、{re.escape(term)}(?:は|（|。|」)", t):
        return True
    if "「" in t and "」" not in t:
        return True
    if t.endswith("ことに関連する重要語です。"):
        return True
    return False


def core_definition(term: str, src: SourceParts, short: str) -> str:
    if term in KNOWN_DEFINITIONS:
        return KNOWN_DEFINITIONS[term]
    candidates: list[str] = []
    if src.core:
        candidates.append(src.core)
    if src.key_point and not is_broken_key_point(term, src.key_point):
        candidates.append(build_core_from_key_point(term, src.key_point))
    if short:
        candidates.append(short.rstrip("。") + "。")
    if src.past_exam:
        pe = src.past_exam.rstrip("。")
        candidates.append(pe + "。" if pe.startswith(term) else f"{term}に関する要点は「{pe}」です。")
    for cand in candidates:
        if cand and not is_broken_definition(term, cand):
            return cand.rstrip("。") + "。"
    return f"{term}は、{GENERIC_FALLBACK.rstrip('。')}。"


def strip_redundant(text: str) -> str:
    out = text
    for pat in (
        r"名前だけ覚えるのではなく、.+?整理しましょう。",
        r"演習第\d+問の解説では、",
        r"職場では.+?理解しましょう。",
    ):
        out = re.sub(pat, "", out)
    return re.sub(r"\s+", " ", out).strip()


def build_expert_body(
    term: str,
    category: str,
    core: str,
    src: SourceParts,
    past: PastBundle | None,
    related: list[str],
    legal: str,
) -> str:
    paras: list[str] = []
    first = split_sents(core)[0] if split_sents(core) else core
    if first.rstrip("。") + "。" != core and len(split_sents(core)) > 1:
        paras.append(first if first.endswith("。") else first + "。")
        rest = core.replace(first, "", 1).strip()
        if rest:
            paras.append(rest if rest.endswith("。") else rest + "。")
    else:
        paras.append(core if core.endswith("。") else core + "。")

    paras.append(CATEGORY_EXPERT.get(category, CATEGORY_EXPERT["基礎・役割"]))

    if past and past.stem:
        stem = past.stem[:90].rstrip("。")
        correct = past.correct[:110].rstrip("。") if past.correct else ""
        paras.append(
            f"試験では、演習第{past.qno}問のように「{stem}…」といった場面設定で出ます。"
            f"正答の考え方は「{correct}…」に沿うものを選びます。"
        )
    elif src.past_exam:
        paras.append(
            f"演習では「{src.past_exam.rstrip('。')}」が正答のキーワードになる設問が多く、"
            f"制度の趣旨と逆の言い回しが誤答になりやすいです。"
        )

    if past and past.wrong_choices:
        w = past.wrong_choices[0][:85].rstrip("。")
        paras.append(
            f"ひっかけやすいのは「{w}…」のような選択肢です。"
            f"「{term}」の定義と照らし合わせ、言い切り（のみ・必ず・不要）がないか確かめましょう。"
        )

    if legal:
        paras.append(f"根拠としては{legal.rstrip('。')}が関連します。条文番号まで暗記より、趣旨と義務の種類を押さえてください。")

    if related:
        paras.append(
            f"理解を深めるには、{'・'.join(related[:3])}との違いを表にまとめると効果的です。"
            f"似た用語ほど、定義の一語の差が正誤を分けます。"
        )

    return "\n\n".join(paras)


def build_expert_mistakes(term: str, past: PastBundle | None, raw: str) -> str:
    items: list[str] = []
    if past and past.wrong_choices:
        for w in past.wrong_choices[:2]:
            w = w[:100].rstrip("。")
            items.append(f"「{w}…」のように{term}の内容と合わない選択肢")
    if raw:
        for part in raw.split(";"):
            part = part.strip()[:90]
            if part and part not in "".join(items):
                items.append(part.rstrip("。"))
    if not items:
        items = [
            f"「{term}」と逆の内容を述べた選択肢",
            "言い切り表現（のみ・必ず・不要）を見逃す",
        ]
    return "\n".join(f"・{x}" for x in items[:3])


def build_expert_key_summary(
    term: str,
    short: str,
    category: str,
    past: PastBundle | None,
    example_q: str,
    example_a: str,
) -> str:
    plain = short.rstrip("。")
    parts = [f"一言で言うと、{plain}。"]

    if example_q and len(example_q) > 20:
        q = example_q[:95].rstrip("。")
        mark = "誤り（×）" if example_a.startswith("×") else "正しい考え方"
        parts.append(
            f"具体例：試験に「{q}…」と出たとき、{mark}かどうかを判断できるかがポイントです。"
        )
    elif past and past.wrong_choices:
        w = past.wrong_choices[0][:80].rstrip("。")
        parts.append(f"具体例：「{w}…」のような肢は、{term}の趣旨と合わないことが多いです。")

    tip = EXAM_TIPS.get(category, EXAM_TIPS["基礎・役割"])
    parts.append(f"試験官の視点：{tip}")

    if past and past.correct:
        parts.append(f"演習第{past.qno}問の正答は「{past.correct[:95].rstrip('。')}…」の考え方に近いものです。")

    return "\n\n".join(parts)


def build_expert_memory(
    term: str,
    short: str,
    category: str,
    related: list[str],
    past: PastBundle | None,
) -> str:
    core = short.split("、")[0].split("（")[0][:45].rstrip("。")
    if core.startswith(term):
        core = core[len(term) :].lstrip("は、").strip() or core
    steps = [
        f"①定義：{term}＝{core}",
        f"②分野：{category}の用語一覧に位置づけ",
    ]
    if past:
        steps.append(f"③演習：第{past.qno}問の正答キーワードを横書き")
    else:
        steps.append("③演習：関連問題を1問解いて正誤を確認")
    if related:
        steps.append(f"④比較：{'・'.join(related[:2])}との違いを1行ずつ")
    else:
        steps.append("④比較：似た用語があれば表で整理")
    steps.append("⑤直前：誤答肢の言い切り（のみ・必ず）を声に出してチェック")
    return "\n".join(steps)


def build_expert_faq(
    term: str,
    category: str,
    short: str,
    src: SourceParts,
    past: PastBundle | None,
    mistakes: str,
    related: list[str],
    example_q: str,
) -> dict[str, str]:
    faq1 = short.rstrip("。") + "。"
    if src.extra_sents:
        extra = src.extra_sents[0]
        if extra.rstrip("。") not in faq1:
            faq1 += extra if extra.endswith("。") else extra + "。"

    if past:
        faq2 = (
            f"演習第{past.qno}問のように、{term}の意味や制度の位置づけを問う4択が出ます。"
            f"正答は「{past.correct[:70].rstrip('。')}…」の趣旨と一致するものを選びます。"
            f"ケース文を読んでから選択肢を見る順番が安全です。"
        )
    else:
        faq2 = (
            f"{category}分野では、{term}の定義と「誰が」「何を」担うかがセットで問われます。"
            f"関連演習で正答の言い回しを確認し、似た用語との違いも押さえてください。"
        )

    trap = ""
    if past and past.wrong_choices:
        trap = past.wrong_choices[0][:75].rstrip("。")
    elif mistakes:
        trap = mistakes.replace("・", "").split("\n")[0][:75]
    faq3 = (
        f"「{trap}…」のように、{term}の内容と逆のことを書いた選択肢に注意してください。"
        f"定義と1語ずつ照合し、「〜のみ」「〜不要」などの言い切りを見逃さないでください。"
        if trap
        else f"似た用語との混同と、言い切り表現（のみ・必ず・不要）の2点が誤答の主因です。"
    )

    if related:
        faq4 = (
            f"ノートに「{term}＝定義1行」と関連語（{'・'.join(related[:3])}）の違いを表形式で書き、"
            f"演習1問で定着を確認するのが効率的です。"
        )
    else:
        faq4 = (
            f"定義・職場での役割・試験の注意点を3行メモにまとめ、"
            f"週1回は関連演習で正誤を確認すると記憶が定着します。"
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


def build_expert_lead(term: str, category: str, short: str) -> str:
    hook = short[:75].rstrip("。")
    return (
        f"この記事では、メンタルヘルスII種（{category}）の「{term}」を、"
        f"試験対策の現場で使える形に整理しました。"
        f"{hook}。"
        f"意味・職場での位置づけ・演習の出方・覚え方まで、順を追って確認できます。"
    )


def build_expert_explanation(term: str, past: PastBundle | None, src: SourceParts) -> str:
    if past and past.wrong_choices:
        w = past.wrong_choices[0][:75].rstrip("。")
        base = past.correct[:90].rstrip("。") if past.correct else src.past_exam[:90].rstrip("。")
        return (
            f"演習第{past.qno}問では「{base}…」が正答の軸です。"
            f"誤りになりやすいのは「{w}…」のように、{term}の趣旨と合わない肢です。"
            f"定義→担当者→根拠の順で選択肢を確認しましょう。"
        )
    if src.past_exam:
        return (
            f"演習では「{src.past_exam.rstrip('。')}」が正答の要点です。"
            f"「{term}」と矛盾する限定表現に注意し、制度の趣旨と照らし合わせてください。"
        )
    return (
        f"「{term}」は、定義・担当者・根拠法令の3点をセットで確認する設問が中心です。"
        f"似た用語との境界もあわせて整理してください。"
    )


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
    valid: set[str],
    top20_terms: set[str],
) -> None:
    term = norm(row.get("term"))
    if not term:
        return

    category = norm(row.get("category"))
    text = checklist.get(term) or norm(row.get("definition"))
    src = parse_source(term, text)
    past_row = find_past_row(term, norm(row.get("practice_question")), past_index)
    past = build_past_bundle(past_row)
    related = filter_related(norm(row.get("related_terms")), valid)
    row["related_terms"] = ";".join(related)
    legal = norm(row.get("legal_basis"))
    short = norm(row.get("short_def")) or split_sents(src.core)[0]
    if is_broken_definition(term, short):
        short = split_sents(src.core)[0] if split_sents(src.core) else ""

    core = core_definition(term, src, short)
    row["short_def"] = split_sents(core)[0] if split_sents(core) else core
    if len(row["short_def"]) > 145:
        row["short_def"] = row["short_def"][:143] + "…"

    if term not in top20_terms or len(norm(row.get("term_detail_body"))) < 400:
        row["term_detail_body"] = build_expert_body(
            term, category, core, src, past, related, legal
        )
    else:
        body = strip_redundant(norm(row.get("term_detail_body")))
        if len(body) < 500:
            row["term_detail_body"] = build_expert_body(
                term, category, core, src, past, related, legal
            )
        else:
            row["term_detail_body"] = body

    row["key_summary"] = build_expert_key_summary(
        term, row["short_def"], category, past,
        norm(row.get("example_question")), norm(row.get("example_answer")),
    )
    row["common_mistakes"] = build_expert_mistakes(
        term, past, norm(row.get("common_mistakes"))
    )
    row["memory_tip"] = build_expert_memory(term, row["short_def"], category, related, past)
    row["explanation"] = build_expert_explanation(term, past, src)
    row["article_lead"] = build_expert_lead(term, category, row["short_def"])

    pts: list[str] = []
    if row["short_def"]:
        pts.append(row["short_def"].rstrip("。"))
    if src.key_point:
        pts.append(src.key_point.rstrip("。"))
    if past and past.correct:
        pts.append(f"演習第{past.qno}問：{past.correct[:85].rstrip('。')}")
    row["exam_points"] = ";".join(dict.fromkeys(pts))[:500]

    for k, v in build_expert_faq(
        term, category, row["short_def"], src, past,
        row["common_mistakes"], related,
        norm(row.get("example_question")),
    ).items():
        row[k] = v


def main() -> int:
    checklist = load_checklist()
    past_index = load_past_index()
    top20_terms = set(patch_top20().keys())

    fieldnames, rows = load_glossary_csv(CSV_PATH)
    valid = {norm(r.get("term")) for r in rows if norm(r.get("term"))}

    for row in rows:
        enrich_row(row, checklist, past_index, valid, top20_terms)

    with CSV_PATH.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

    avg_body = sum(len(norm(r.get("term_detail_body"))) for r in rows) // len(rows)
    faq4 = sum(1 for r in rows if norm(r.get("faq_4_answer")))
    print(f"glossary_pro: terms={len(rows)}, avg_body={avg_body}, faq4={faq4}/{len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
