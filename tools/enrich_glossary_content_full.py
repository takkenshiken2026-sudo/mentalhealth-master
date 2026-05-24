#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""用語CSV全件のコンテンツ品質向上（オリジナリティ重視）。

文字数の水増しは行わず、definition・演習問題CSVから用語固有の情報だけを再構成する。
"""

from __future__ import annotations

import csv
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.enrich_glossary_quality import (  # noqa: E402
    CATEGORY_MISTAKES,
    FLAT_BOILER_MARKERS,
    GENERIC_SHORT_DEF_RE,
    patch_top20,
)

CSV_PATH = ROOT / "data" / "glossary_terms.csv"
PAST_QUESTIONS_CSV = ROOT / "data" / "past_questions.csv"

GENERIC_CATEGORY_RE = re.compile(
    r"^(?:.+は、)?(?:精神症状、身体症状|メンタルヘルスケアの意義|管理監督者の役割|"
    r"相談対応|職場環境の評価|ストレスや疾病の基礎理解).+用語です。?"
)
WORKPLACE_BOILER = re.compile(
    r"職場では、用語の意味だけでなく、誰が対応し、どの情報を共有し、どの専門職につなぐかまで確認します。"
)
PRACTICE_BOILER = re.compile(
    r"実務では、(?:用語を単独で覚えるのではなく、ラインケア・安全配慮・専門職連携の流れに置いて確認します|"
    r"個人の努力だけでなく、職場の仕組みや環境をどう変えるかまで考えると理解が深まります|"
    r"本人の安心感を保ちつつ、社内外の支援先とどのタイミングで連携するかを意識します)。"
)
RELATED_RE = re.compile(r"関連する用語として[、,]?([^。]+)もあわせて確認")
KEY_POINT_RE = re.compile(r"まず「([^」]+)」")
PAST_Q_RE = re.compile(r"過去問・演習では「([^」]+)」")
LINECARE_RE = re.compile(r"ラインケアの視点では、([^。]+。)")

# 旧版パディング（再実行時に除去）
STRIP_PATTERNS: tuple[str, ...] = (
    "復習の際は、",
    "試験直前は、",
    "単独記述より、制度全体の中での位置づけ",
    "を覚えたら、本サイトの関連演習問題で正答肢の表現を確認し、",
    "間違えた選択肢が根拠・対象範囲・責任主体のどれでずれているかをメモしてください。",
    "演習問題で間違えた際は、用語記事に戻り定義と試験ポイントを再確認してください。",
    "正答肢のキーワードをそのまま暗記するより、",
    "なぜ他の肢が誤りか（根拠・対象・責任のどれがずれているか）を言語化すると定着します。",
    "関連演習を解いた後、",
    "の記事に戻って定義と正答キーワードを照合してください。",
    "は演習で定義・担当者・数値の組み合わせ出題が多い。",
)

KNOWN_DEFINITIONS: dict[str, str] = {
    "SSRI": (
        "SSRI（選択的セロトニン再取り込み阻害薬）は、脳内の神経伝達物質セロトニンの再取り込みを抑え、"
        "セロトニンの働きを高める抗うつ薬の一種です。うつ病やパニック障害などの治療に用いられますが、"
        "管理監督者が薬の適否を判断するものではありません。"
    ),
    "SNRI": (
        "SNRIは、セロトニンとノルアドレナリンの再取り込みを阻害する抗うつ薬で、"
        "うつ病などの治療に用いられることがあります。"
    ),
    "セロトニン": "セロトニンは脳内の神経伝達物質の一つで、気分、睡眠、食欲などと関連して説明されます。",
    "ドーパミン": "ドーパミンは脳内の神経伝達物質の一つで、報酬系、意欲、注意などと関連します。",
    "PDCAサイクル": (
        "PDCAサイクルは、Plan（計画）→Do（実施）→Check（評価）→Act（改善）"
        "の循環で職場改善を進める手法です。"
    ),
}


GENERIC_LINECARE = "管理監督者が医学的判断を抱え込まず、職場で観察できる事実と専門職への連携を分けて理解することが重要"


@dataclass
class ParsedDefinition:
    core: str = ""
    key_point: str = ""
    past_exam: str = ""
    linecare: str = ""
    related: list[str] = field(default_factory=list)
    substantive: list[str] = field(default_factory=list)


@dataclass
class PastQuestionContext:
    question_no: int = 0
    stem: str = ""
    correct: str = ""
    trap_hints: list[str] = field(default_factory=list)


def norm(s: str | None) -> str:
    return (s or "").strip()


def split_sentences(text: str) -> list[str]:
    if not text:
        return []
    return [p.strip() for p in re.findall(r"[^。！？]+[。！？]?", text) if p.strip()]


def is_generic_short(s: str) -> bool:
    return bool(GENERIC_SHORT_DEF_RE.match(s) or GENERIC_CATEGORY_RE.match(s))


def strip_boilerplate(text: str) -> str:
    out = text
    for marker in FLAT_BOILER_MARKERS:
        if marker in out:
            out = out[: out.index(marker)].strip()
    out = WORKPLACE_BOILER.sub("", out)
    out = PRACTICE_BOILER.sub("", out)
    if "ラインケアの視点では" in out:
        out = out.split("ラインケアの視点では")[0].strip()
    m = RELATED_RE.search(out)
    if m:
        out = out[: m.start()].strip()
    return re.sub(r"\s+", " ", out).strip()


def strip_legacy_padding(text: str) -> str:
    """旧版の文字数パディングを除去。"""
    out = text
    for pat in STRIP_PATTERNS:
        while pat in out:
            idx = out.index(pat)
            end = out.find("。", idx)
            if end == -1:
                out = out[:idx].strip()
                break
            out = (out[:idx] + out[end + 1 :]).strip()
    return re.sub(r"\s+", " ", out).strip()


def looks_like_definition(s: str) -> bool:
    return any(m in s for m in ("とは", "をいう", "制度", "義務", "支援", "検査", "協定", "モデル")) and len(s) >= 20


def infer_term_type(term: str, category: str) -> str:
    if any(k in term for k in ("法", "協定", "義務", "規制", "条項", "罰", "賠償")):
        return "legal"
    if any(k in term for k in ("症", "障害", "病", "薬", "治療", "症状", "精神", "うつ", "統合")):
        return "medical"
    if any(k in term for k in ("相談", "電話", "EAP", "ホットライン", "センター", "NPO", "機関")):
        return "resource"
    if any(k in term for k in ("ステップ", "復職", "休職", "プラン", "フォロー", "段階")):
        return "procedure"
    if any(k in term for k in ("ストレスチェック", "職場環境", "ハラスメント", "判定図", "集団分析")):
        return "workplace"
    if any(k in term for k in ("傾聴", "リスニング", "コミュニケーション", "共感", "質問")):
        return "communication"
    if any(k in term for k in ("モデル", "理論", "法則", "セリエ", "NIOSH", "JD-R")):
        return "model"
    if category == "職場環境・配慮":
        return "workplace"
    if category == "相談・連携・復職":
        return "procedure"
    return "general"


def parse_definition(term: str, definition: str, short_def: str) -> ParsedDefinition:
    raw = norm(definition)
    text = strip_boilerplate(raw)
    parsed = ParsedDefinition()

    if term in KNOWN_DEFINITIONS:
        parsed.core = KNOWN_DEFINITIONS[term]

    m_key = KEY_POINT_RE.search(raw)
    if m_key:
        parsed.key_point = m_key.group(1).strip()

    m_past = PAST_Q_RE.search(raw)
    if m_past:
        parsed.past_exam = m_past.group(1).strip()

    m_lc = LINECARE_RE.search(raw)
    if m_lc:
        parsed.linecare = m_lc.group(1).strip()

    m_rel = RELATED_RE.search(raw)
    if m_rel:
        chunk = m_rel.group(1)
        parsed.related = [p.strip() for p in re.split(r"[、,]|もあわせて", chunk) if p.strip()]

    for sent in split_sentences(text):
        if is_generic_short(sent) or is_generic_sentence(sent):
            continue
        if sent.startswith("まず") or "出題上のポイント" in sent or sent.startswith("過去問"):
            continue
        if len(sent) > 15:
            parsed.substantive.append(sent)

    if not parsed.core:
        if short_def and not is_generic_short(short_def):
            parsed.core = short_def.rstrip("。") + "。"
        elif parsed.substantive:
            parsed.core = parsed.substantive[0]
        elif parsed.key_point and looks_like_definition(parsed.key_point):
            parsed.core = parsed.key_point.rstrip("。") + "。"
        else:
            parsed.core = f"{term}は、メンタルヘルスII種の試験範囲で扱う重要語です。"

    return parsed


def search_keys(term: str) -> list[str]:
    keys = [term]
    if "（" in term:
        keys.append(term.split("（")[0])
        inner = term.split("（", 1)[1].rstrip("）")
        if inner:
            keys.append(inner)
    return keys


def is_generic_sentence(s: str) -> bool:
    return GENERIC_LINECARE in s or is_generic_short(s)


def extract_traps(correct_idx: str, explanation_choices: str) -> list[str]:
    traps: list[str] = []
    for part in (explanation_choices or "").split(";"):
        part = part.strip()
        if not part or part.startswith(f"{correct_idx}:"):
            continue
        for sent in split_sentences(part):
            sent = re.sub(r"^\d+:\s*", "", sent).strip()
            if len(sent) < 18:
                continue
            if any(k in sent for k in ("のみ", "必ず", "だけ", "限定", "混同", "取り違", "矛盾", "不要", "誤り")):
                if sent not in traps:
                    traps.append(sent[:140])
    return traps[:3]


def row_to_past_context(r: dict[str, str]) -> PastQuestionContext:
    correct_idx = str(r.get("correct") or "")
    return PastQuestionContext(
        question_no=int(r["question_no"]),
        stem=norm(r.get("stem")),
        correct=norm(r.get("explanation_correct") or r.get("explanation")),
        trap_hints=extract_traps(correct_idx, r.get("explanation_choices") or ""),
    )


def find_past_row_by_path(practice_path: str, past_rows: list[dict[str, str]]) -> dict[str, str] | None:
    m = re.search(r"q(\d+)$", practice_path.replace("-", ""))
    if not m:
        return None
    qno = int(m.group(1))
    for r in past_rows:
        if (
            r.get("exam_year") == "2026"
            and r.get("exam_wareki") == "演習"
            and int(r.get("question_no") or 0) == qno
        ):
            return r
    return None


def find_past_context(
    term: str,
    past_rows: list[dict[str, str]],
    practice_path: str = "",
) -> PastQuestionContext | None:
    if practice_path:
        linked = find_past_row_by_path(practice_path, past_rows)
        if linked:
            return row_to_past_context(linked)

    best: PastQuestionContext | None = None
    best_score = 0

    for r in past_rows:
        if r.get("exam_year") != "2026" or r.get("exam_wareki") != "演習":
            continue
        blob = " ".join(str(r.get(k, "")) for k in r)
        score = 0
        for key in search_keys(term):
            if len(key) >= 3 and key in blob:
                score += len(key)
        if term in r.get("stem", ""):
            score += 30
        if score <= best_score:
            continue
        best = row_to_past_context(r)
        best_score = score

    return best


def filter_related(raw: str, parsed_related: list[str], valid_terms: set[str]) -> list[str]:
    out: list[str] = []
    candidates = parsed_related or [
        t.strip() for t in re.split(r"[;、,]", raw) if t.strip()
    ]
    for t in candidates:
        if "確認すると理解" in t or len(t) > 30:
            continue
        if t in valid_terms and t not in out:
            out.append(t)
    return out[:4]


def build_short_def(parsed: ParsedDefinition) -> str:
    core = parsed.core
    if len(core) > 130:
        sents = split_sentences(core)
        core = sents[0] if sents else core[:128] + "…"
    return core


def build_term_detail_body(
    term: str,
    parsed: ParsedDefinition,
    legal: str,
    related_terms: str,
    past_ctx: PastQuestionContext | None,
    term_type: str,
    valid_terms: set[str],
) -> str:
    parts: list[str] = []
    seen: set[str] = set()

    def add(s: str) -> None:
        s = strip_legacy_padding(s.strip())
        if s and s not in seen and len(s) > 8:
            seen.add(s)
            parts.append(s)

    add(parsed.core.rstrip("。") + "。")

    for sent in parsed.substantive[1:4]:
        if sent.rstrip("。") + "。" != parsed.core:
            add(sent)

    if parsed.linecare and term_type not in ("legal", "workplace", "model"):
        if GENERIC_LINECARE not in parsed.linecare:
            add(parsed.linecare)

    if past_ctx and past_ctx.correct:
        add(f"演習第{past_ctx.question_no}問では、{past_ctx.correct}")

    if legal:
        add(f"法令・根拠：{legal.rstrip('。')}。")

    rel = filter_related(related_terms, parsed.related, valid_terms)
    if rel:
        add(f"あわせて確認したい関連用語：{'、'.join(rel)}。")

    return "".join(parts)


def build_explanation(
    term: str,
    parsed: ParsedDefinition,
    past_ctx: PastQuestionContext | None,
) -> str:
    if past_ctx and past_ctx.correct:
        base = past_ctx.correct.rstrip("。")
        if past_ctx.trap_hints:
            traps = "／".join(
                re.sub(r"解説[^。]*。", "", h).strip()[:80].rstrip("。")
                for h in past_ctx.trap_hints[:2]
                if len(h) > 15
            )
            if traps:
                return (
                    f"演習第{past_ctx.question_no}問の正答要点：{base}。"
                    f"誤りになりやすい肢：{traps}。"
                )
        return f"演習第{past_ctx.question_no}問（{term}関連）の正答要点：{base}。"
    if parsed.past_exam:
        return (
            f"演習では「{parsed.past_exam.rstrip('。')}」が正答のキーワードになることがあります。"
            f"「{term}」単独の定義確認より、近い制度・数値・担当者との違いを比較する問題に注意してください。"
        )
    if parsed.key_point:
        return (
            f"選択肢では「{parsed.key_point.rstrip('。')}」と矛盾する記述が誤りになりやすいです。"
            f"「のみ」「必ず」などの限定表現が定義と合うかを確認してください。"
        )
    return (
        f"「{term}」は定義確認に加え、近い制度・数値・担当者との違いを比較する問題に注意してください。"
    )


def build_exam_points(
    parsed: ParsedDefinition,
    category: str,
    past_ctx: PastQuestionContext | None,
) -> str:
    pts: list[str] = []
    if parsed.core:
        pts.append(split_sentences(parsed.core)[0] if split_sentences(parsed.core) else parsed.core)
    if parsed.key_point:
        pts.append(parsed.key_point.rstrip("。"))
    if parsed.past_exam:
        pts.append(parsed.past_exam.rstrip("。"))
    if past_ctx and past_ctx.correct:
        short = past_ctx.correct[:100] + ("…" if len(past_ctx.correct) > 100 else "")
        pts.append(f"演習第{past_ctx.question_no}問：{short.rstrip('。')}")
    if len(pts) < 3:
        pts.append(f"{category}分野で担当者・義務・手順がセットで問われる")
    return ";".join(pts[:4])


def build_article_lead(term: str, parsed: ParsedDefinition, category: str) -> str:
    hook = split_sentences(parsed.core)[0] if split_sentences(parsed.core) else parsed.core
    if len(hook) > 70:
        hook = hook[:68] + "…"
    return (
        f"{category}分野の「{term}」について、"
        f"試験で問われる定義と職場での見方を整理します。"
        f"{hook.rstrip('。')}。"
    )


def build_memory_tip(term: str, parsed: ParsedDefinition, past_ctx: PastQuestionContext | None) -> str:
    if past_ctx:
        return (
            f"演習第{past_ctx.question_no}問を解き、正答肢のキーワードと「{term}」の定義を"
            f"ノートの表に並べて比較する。"
        )
    if parsed.past_exam:
        return f"「{parsed.past_exam[:50].rstrip('。')}」を{term}の演習キーワードとしてメモする。"
    if parsed.key_point:
        return f"定義＋「{parsed.key_point[:40].rstrip('。')}」の2行メモで整理。"
    return f"{term}：定義→関連演習→間違えた肢の理由、の順で復習。"


def build_faq(
    term: str,
    parsed: ParsedDefinition,
    category: str,
    short_def: str,
    past_ctx: PastQuestionContext | None,
) -> dict[str, str]:
    faq1 = short_def.rstrip("。") + "。"
    for sent in parsed.substantive[:2]:
        if sent.rstrip("。") + "。" != faq1 and sent not in faq1:
            faq1 += sent if sent.endswith("。") else sent + "。"
            break

    if past_ctx:
        faq2 = (
            f"演習第{past_ctx.question_no}問のように、{term}の定義や制度の位置づけを"
            f"選択肢形式で問う問題が出ます。正答は「{past_ctx.correct[:80].rstrip('。')}…」"
            f"の趣旨と一致する肢です。"
        )
    elif parsed.past_exam:
        faq2 = (
            f"「{parsed.past_exam.rstrip('。')}」といったキーワードが正答に含まれる"
            f"設問が多いです。定義だけでなく、演習の正答肢表現と照合して覚えてください。"
        )
    else:
        faq2 = (
            f"{category}分野では、{term}の意味に加え、誰が担うか・何が義務かが"
            f"セットで問われることがあります。"
        )

    faq3_by_cat = {
        "基礎・役割": "根拠法令（労基法・労契法・労安法）の取り違えに注意し、管理監督者が医学的判断を抱え込まない点も確認してください。",
        "職場環境・配慮": "数値基準・義務の有無・実施主体の混同に注意。個人結果と集団分析は目的が異なります。",
        "相談・連携・復職": "手順の順序、主治医と産業医の役割、プライバシーと同意の範囲をセットで整理してください。",
    }

    return {
        "faq_1_question": f"{term}とは何ですか？",
        "faq_1_answer": faq1,
        "faq_2_question": f"{term}は試験でどのように問われますか？",
        "faq_2_answer": faq2,
        "faq_3_question": f"{term}を学習するときの注意点は？",
        "faq_3_answer": faq3_by_cat.get(category, faq3_by_cat["基礎・役割"]),
    }


def build_common_mistakes(
    category: str,
    existing: str,
    past_ctx: PastQuestionContext | None,
    parsed: ParsedDefinition,
) -> str:
    if past_ctx and past_ctx.trap_hints:
        cleaned = []
        for h in past_ctx.trap_hints[:3]:
            t = re.sub(r"解説の要点[^。]*。", "", h).strip()
            t = re.sub(r"正答[^。]*確認[^。]*。", "", t).strip()
            if len(t) > 15:
                cleaned.append(t[:100].rstrip("。"))
        if cleaned:
            return ";".join(cleaned)
    if existing and "似た用語や近い制度と混同" not in existing:
        parts = [p.strip() for p in existing.split(";") if p.strip()]
        if len(parts) >= 2 and not all("管理監督者が医学" in p for p in parts):
            return existing
    if parsed.key_point:
        return f"「{parsed.key_point[:50].rstrip('。')}」と矛盾する選択肢に注意"
    return CATEGORY_MISTAKES.get(category, "類似語・近い制度との境界を確認").split(";")[0]


def build_example_qa(past_ctx: PastQuestionContext | None) -> tuple[str, str]:
    if not past_ctx or not past_ctx.stem:
        return "", ""
    q = past_ctx.stem if len(past_ctx.stem) <= 140 else past_ctx.stem[:138] + "…"
    a = past_ctx.correct[:200] if past_ctx.correct else "演習問題の解説を参照してください。"
    return q, a


def enrich_row(
    row: dict[str, str],
    past_rows: list[dict[str, str]],
    skip_terms: set[str],
    valid_terms: set[str],
) -> bool:
    term = norm(row.get("term"))
    if not term or term in skip_terms:
        return False

    definition = norm(row.get("definition"))
    category = norm(row.get("category"))
    legal = norm(row.get("legal_basis"))
    related_terms = norm(row.get("related_terms"))
    term_type = infer_term_type(term, category)

    parsed = parse_definition(term, definition, norm(row.get("short_def")))
    past_ctx = find_past_context(term, past_rows, norm(row.get("practice_question")))

    new_short = build_short_def(parsed)
    row["short_def"] = new_short
    row["term_detail_body"] = build_term_detail_body(
        term, parsed, legal, related_terms, past_ctx, term_type, valid_terms
    )
    row["explanation"] = build_explanation(term, parsed, past_ctx)
    row["exam_points"] = build_exam_points(parsed, category, past_ctx)
    row["article_lead"] = build_article_lead(term, parsed, category)
    row["memory_tip"] = build_memory_tip(term, parsed, past_ctx)
    row["common_mistakes"] = build_common_mistakes(
        category, norm(row.get("common_mistakes")), past_ctx, parsed
    )

    for k, v in build_faq(term, parsed, category, new_short, past_ctx).items():
        row[k] = v

    ex_q, ex_a = build_example_qa(past_ctx)
    if ex_q and ex_a:
        row["example_question"] = ex_q
        row["example_answer"] = ex_a

    return True


def cleanup_top20_padding(rows: list[dict[str, str]], top20: set[str]) -> int:
    """頻出20語の term_detail_body から旧パディングを除去。"""
    n = 0
    for row in rows:
        if norm(row.get("term")) not in top20:
            continue
        body = norm(row.get("term_detail_body"))
        cleaned = strip_legacy_padding(body)
        if cleaned != body:
            row["term_detail_body"] = cleaned
            n += 1
    return n


def main() -> int:
    skip = set(patch_top20().keys())

    text = CSV_PATH.read_text(encoding="utf-8-sig")
    reader = csv.DictReader(text.splitlines())
    fieldnames = list(reader.fieldnames or [])
    rows = list(reader)

    past_rows: list[dict[str, str]] = []
    if PAST_QUESTIONS_CSV.is_file():
        past_rows = list(csv.DictReader(PAST_QUESTIONS_CSV.read_text(encoding="utf-8-sig").splitlines()))

    valid_terms = {norm(r.get("term")) for r in rows if norm(r.get("term"))}

    n = 0
    for row in rows:
        if enrich_row(row, past_rows, skip, valid_terms):
            n += 1

    cleaned = cleanup_top20_padding(rows, skip)

    with CSV_PATH.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

    # 品質監査（文字数ではなく定型文率）
    pad_hits = sum(
        1 for r in rows if any(p in (r.get("term_detail_body") or "") for p in STRIP_PATTERNS[:3])
    )
    past_linked = sum(
        1 for r in rows if "演習第" in (r.get("explanation") or "") or "演習第" in (r.get("term_detail_body") or "")
    )
    print(
        f"content_full: enriched={n}, top20_preserved={len(skip)}, "
        f"top20_padding_removed={cleaned}, boilerplate_remaining={pad_hits}, "
        f"past_question_linked={past_linked}/{len(rows)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
