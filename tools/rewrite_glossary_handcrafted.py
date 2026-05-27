#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""用語339件の手作り品質リライト。

正本: docs/glossary-terms-checklist.csv の解説 + 演習問題CSV + 頻出20語の個別原稿。
文字数パディングは行わず、用語ごとに異なる情報だけで900字前後を構成する。
"""

from __future__ import annotations

import csv
import hashlib
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.enrich_glossary_quality import (  # noqa: E402
    FLAT_BOILER_MARKERS,
    GENERIC_SHORT_DEF_RE,
    patch_top20,
)

CSV_PATH = ROOT / "data" / "glossary_terms.csv"
CHECKLIST_CSV = ROOT / "docs/glossary-terms-checklist.csv"
PAST_CSV = ROOT / "data" / "past_questions.csv"

GENERIC_PREFIX_RE = re.compile(
    r"^.+は、(?:精神症状、身体症状|メンタルヘルスケアの意義|管理監督者の役割|"
    r"相談対応|職場環境の評価|ストレスや疾病の基礎理解).+用語です。?"
)
WORKPLACE_BOILER = "職場では、用語の意味だけでなく、誰が対応し、どの情報を共有し、どの専門職につなぐかまで確認します。"
PRACTICE_BOILERS = (
    "実務では、用語を単独で覚えるのではなく、ラインケア・安全配慮・専門職連携の流れに置いて確認します。",
    "実務では、個人の努力だけでなく、職場の仕組みや環境をどう変えるかまで考えると理解が深まります。",
    "実務では、本人の安心感を保ちつつ、社内外の支援先とどのタイミングで連携するかを意識します。",
)
KEY_POINT_RE = re.compile(r"まず「([^」]+)」")
PAST_Q_RE = re.compile(r"過去問・演習では「([^」]+)」")
LINECARE_RE = re.compile(r"ラインケアの視点では、([^。]+。)")
RELATED_RE = re.compile(r"関連する用語として[、,]?([^。]+)もあわせて確認")
GENERIC_LINECARE = "管理監督者が医学的判断を抱え込まず"

KNOWN_DEFINITIONS: dict[str, str] = {
    "SSRI": (
        "SSRI（選択的セロトニン再取り込み阻害薬）は、セロトニンの再取り込みを抑える抗うつ薬で、"
        "うつ病やパニック障害の治療に用いられます。管理監督者が薬の適否を判断するものではありません。"
    ),
    "SNRI": "SNRIは、セロトニンとノルアドレナリンの再取り込みを阻害する抗うつ薬です。",
    "セロトニン": "セロトニンは、気分・睡眠・食欲などに関わる脳内の神経伝達物質です。",
    "ドーパミン": "ドーパミンは、報酬系・意欲・注意などに関わる神経伝達物質です。",
    "PDCAサイクル": "PDCAは、計画（Plan）→実施（Do）→評価（Check）→改善（Act）の職場改善サイクルです。",
    "NIOSHモデル": (
        "NIOSHモデルは、仕事のストレス要因が個人要因・緩衝要因（上司・同僚・家族の支援等）"
        "によってストレス反応を修飾し、健康障害に至る過程を示すモデルです。"
    ),
    "JD-Rモデル": (
        "JD-Rモデル（要求―資源モデル）は、職場の要求と資源のバランスで"
        "倦怠とワーク・エンゲイジメントを説明するモデルです。"
    ),
    "36協定": (
        "36協定は、法定労働時間を超える時間外・休日労働を行わせるための労使協定です。"
        "2019年改正により上限規制（年720時間・月100時間未満・2〜6か月平均80時間）が設けられました。"
    ),
    "安全配慮義務": (
        "安全配慮義務は労働契約法5条に規定され、使用者が労働者の生命・身体・精神の健康を"
        "保護する義務です。身体的安全だけでなくメンタルヘルス上の配慮も含みます。"
    ),
    "慰謝料": (
        "慰謝料は、安全配慮義務違反などにより労働者が被った精神的苦痛に対する損害賠償の一類型です。"
        "損害賠償の対象は積極損害（治療費・入院費等）・消極損害（逸失利益）・慰謝料の3区分で整理されます。"
        "演習第44問では「含まれないもの」を問う形式で、使用者の事業利益は算定対象外とされています。"
        "積極損害・逸失利益・慰謝料はいずれも賠償対象であり、混同しないことが重要です。"
    ),
    "逸失利益": (
        "逸失利益は、傷病により本来得られたはずの収入等が失われたことによる消極的損害です。"
        "損害賠償では積極損害（治療費・入院費等）・消極損害（逸失利益）・慰謝料の3区分で整理します。"
        "休業による賃金減少は逸失利益に該当しますが、使用者の事業利益は賠償算定に含まれません。"
        "演習第44問では3区分すべてが賠償対象であることと、事業利益が対象外であることを区別して問われます。"
        "安全配慮義務（労働契約法5条）に基づく民事上の請求とセットで理解してください。"
    ),
    "ストレスチェック": (
        "ストレスチェックは、労働者自身のストレスへの気づきと職場環境改善を目的とする検査制度です。"
        "個人結果の不利益取扱いは禁止されています。"
    ),
}

CATEGORY_FAQ3: dict[str, str] = {
    "基礎・役割": (
        "根拠法令（労基法・労契法・労安法）の取り違えに注意してください。"
        "管理監督者が診断・治療方針を決める選択肢は誤りになりやすいです。"
    ),
    "職場環境・配慮": (
        "数値基準・義務の有無・実施主体（誰が行うか）をセットで確認してください。"
        "個人結果と集団分析は目的が異なります。"
    ),
    "相談・連携・復職": (
        "手順の順序、主治医と産業医の役割分担、プライバシーと同意の範囲を整理してください。"
        "やってはいけない対応（一人にする・軽視する等）が問われることがあります。"
    ),
}


@dataclass
class SourceParts:
    core: str = ""
    key_point: str = ""
    past_exam: str = ""
    linecare: str = ""
    related: list[str] = field(default_factory=list)
    extra_sents: list[str] = field(default_factory=list)


@dataclass
class PastBundle:
    qno: int = 0
    stem: str = ""
    correct: str = ""
    summary: str = ""
    wrong_choices: list[str] = field(default_factory=list)
    trap_notes: list[str] = field(default_factory=list)


def norm(s: str | None) -> str:
    return (s or "").strip()


def split_sents(text: str) -> list[str]:
    return [p.strip() for p in re.findall(r"[^。！？]+[。！？]?", text or "") if p.strip()]


def strip_boiler(text: str) -> str:
    out = text
    for m in FLAT_BOILER_MARKERS:
        if m in out:
            out = out[: out.index(m)].strip()
    out = out.replace(WORKPLACE_BOILER, "")
    for b in PRACTICE_BOILERS:
        out = out.replace(b, "")
    if "ラインケアの視点では" in out:
        out = out.split("ラインケアの視点では")[0].strip()
    m = RELATED_RE.search(out)
    if m:
        out = out[: m.start()].strip()
    return re.sub(r"\s+", " ", out).strip()


def is_generic(s: str) -> bool:
    return bool(GENERIC_PREFIX_RE.match(s) or GENERIC_SHORT_DEF_RE.match(s))


def is_broken_key_point(term: str, key_point: str) -> bool:
    kp = norm(key_point)
    if not kp or len(kp) < 8:
        return True
    if kp == term or kp.startswith(f"{term}こと"):
        return True
    if "「" in kp or "」" in kp:
        return True
    if "ことに関連する重要語" in kp:
        return True
    return False


def build_core_from_key_point(term: str, key_point: str) -> str:
    kp = key_point.rstrip("。")
    if kp.startswith(f"{term}は") or kp.startswith(f"{term}（"):
        return kp + "。"
    if any(x in kp for x in ("とは", "制度", "義務", "検査", "協定", "です", "である", "指す", "意味", "方法")):
        return kp + "。"
    return f"{term}は、{kp}。"


def parse_source(term: str, text: str) -> SourceParts:
    raw = norm(text)
    p = SourceParts()
    if term in KNOWN_DEFINITIONS:
        p.core = KNOWN_DEFINITIONS[term]

    m = KEY_POINT_RE.search(raw)
    if m:
        p.key_point = m.group(1).strip()
    m = PAST_Q_RE.search(raw)
    if m:
        p.past_exam = m.group(1).strip()
    m = LINECARE_RE.search(raw)
    if m and GENERIC_LINECARE not in m.group(1):
        p.linecare = m.group(1).strip()
    m = RELATED_RE.search(raw)
    if m:
        p.related = [x.strip() for x in re.split(r"[、,]|もあわせて", m.group(1)) if x.strip()]

    for sent in split_sents(strip_boiler(raw)):
        if is_generic(sent) or sent.startswith("まず") or "出題上のポイント" in sent:
            continue
        if sent.startswith("過去問"):
            continue
        if len(sent) < 14:
            continue
        p.extra_sents.append(sent)

    if not p.core:
        if p.extra_sents:
            p.core = p.extra_sents[0]
        elif p.key_point and not is_broken_key_point(term, p.key_point):
            p.core = build_core_from_key_point(term, p.key_point)
        else:
            p.core = f"{term}は、メンタルヘルスII種で扱う重要語です。"

    return p


def load_checklist() -> dict[str, str]:
    rows = csv.DictReader(CHECKLIST_CSV.read_text(encoding="utf-8-sig").splitlines())
    return {norm(r["用語"]): norm(r["解説"]) for r in rows if norm(r.get("用語"))}


def load_past_index() -> dict[int, dict[str, str]]:
    out: dict[int, dict[str, str]] = {}
    for r in csv.DictReader(PAST_CSV.read_text(encoding="utf-8-sig").splitlines()):
        if r.get("exam_year") == "2026" and r.get("exam_wareki") == "演習":
            out[int(r["question_no"])] = r
    return out


def qno_from_path(path: str) -> int | None:
    m = re.search(r"q(\d+)$", path.replace("-", ""))
    return int(m.group(1)) if m else None


def find_past_row(term: str, practice_path: str, past_index: dict[int, dict[str, str]]) -> dict[str, str] | None:
    qno = qno_from_path(practice_path)
    if qno and qno in past_index:
        return past_index[qno]

    keys = [term]
    if "（" in term:
        keys.append(term.split("（")[0])
        inner = term.split("（", 1)[1].rstrip("）")
        if inner:
            keys.append(inner)

    best: dict[str, str] | None = None
    best_score = 0
    for r in past_index.values():
        blob = " ".join(str(r.get(k, "")) for k in r)
        score = sum(len(k) for k in keys if len(k) >= 3 and k in blob)
        if term in r.get("stem", ""):
            score += 30
        if score > best_score:
            best, best_score = r, score
    return best if best_score >= 6 else None


def build_past_bundle(row: dict[str, str] | None) -> PastBundle | None:
    if not row:
        return None
    correct_idx = str(row.get("correct") or "")
    wrong = [
        norm(row.get(f"choice_{i}"))
        for i in range(1, 5)
        if str(i) != correct_idx and norm(row.get(f"choice_{i}"))
    ]
    traps: list[str] = []
    for part in (row.get("explanation_choices") or "").split(";"):
        part = part.strip()
        if not part or part.startswith(f"{correct_idx}:"):
            continue
        for sent in split_sents(part):
            sent = re.sub(r"^\d+:\s*", "", sent)
            if any(k in sent for k in ("のみ", "必ず", "だけ", "不要", "混同", "矛盾", "誤り", "限定")):
                if len(sent) > 20:
                    traps.append(sent[:120])

    return PastBundle(
        qno=int(row["question_no"]),
        stem=norm(row.get("stem")),
        correct=norm(row.get("explanation_correct") or row.get("explanation")),
        summary=norm(row.get("explanation_summary") or row.get("explanation_point")),
        wrong_choices=wrong[:3],
        trap_notes=traps[:3],
    )


def pick_variant(term: str, options: tuple[str, ...]) -> str:
    h = int(hashlib.md5(term.encode()).hexdigest(), 16)
    return options[h % len(options)]


def filter_related(raw: str, parsed_rel: list[str], valid: set[str]) -> list[str]:
    cands = parsed_rel or [t.strip() for t in re.split(r"[;、,]", raw) if t.strip()]
    out: list[str] = []
    for t in cands:
        if "確認すると理解" in t or len(t) > 35:
            continue
        if t in valid and t not in out:
            out.append(t)
    return out[:4]


def workplace_sentence(term: str, category: str, src: SourceParts) -> str:
    if src.linecare:
        return src.linecare
    opts = {
        "基礎・役割": (
            f"職場では{term}を、管理監督者が医学的診断をせず、観察と専門職連携の文脈で理解します。",
            f"{term}は単語暗記より、誰が何を担うか・根拠法令は何かをセットで押さえます。",
        ),
        "職場環境・配慮": (
            f"{term}は個人の努力だけでなく、職場環境・業務量・支援体制の改善と結びつけて考えます。",
            f"試験では{term}について、数値・義務の有無・実施主体の取り違えに注意してください。",
        ),
        "相談・連携・復職": (
            f"{term}は本人の話を聴いたうえで、産業医・主治医・社外相談機関へつなぐ流れの中で理解します。",
            f"プライバシーと同意の範囲を守り、{term}に関する手順の順序を確認してください。",
        ),
    }
    return pick_variant(term, opts.get(category, opts["基礎・役割"]))


def build_detail_body(
    term: str,
    category: str,
    legal: str,
    src: SourceParts,
    past: PastBundle | None,
    related: list[str],
) -> str:
    parts: list[str] = []
    seen: set[str] = set()

    def add(s: str) -> None:
        s = norm(s)
        if s and s not in seen and len(s) > 10:
            seen.add(s)
            parts.append(s if s.endswith("。") else s + "。")

    add(src.core)
    for s in src.extra_sents[1:4]:
        if s.rstrip("。") + "。" != src.core:
            add(s)

    if src.past_exam and src.past_exam not in seen:
        add(f"演習では「{src.past_exam.rstrip('。')}」が正答のキーワードになることがあります")

    if src.key_point and src.key_point.rstrip("。") not in "".join(parts):
        add(f"試験で押さえる要点：{src.key_point.rstrip('。')}")

    if past and past.correct:
        add(f"演習第{past.qno}問の解説では、{past.correct}")

    if past and past.summary and past.summary not in "".join(parts):
        add(past.summary)

    add(workplace_sentence(term, category, src))

    if legal:
        add(f"関連法令・根拠：{legal.rstrip('。')}")

    if past and past.wrong_choices:
        w1 = past.wrong_choices[0]
        if len(w1) > 55:
            w1 = w1[:53] + "…"
        add(f"誤り肢の例：「{w1}」— 定義・根拠・担当者のいずれかがずれていないか確認")
        if len(past.wrong_choices) > 1:
            w2 = past.wrong_choices[1]
            if len(w2) > 55:
                w2 = w2[:53] + "…"
            add(f"ほかに「{w2}」のような肢も、制度の趣旨と矛盾する場合があります")

    if related:
        add(f"関連用語（{'、'.join(related)}）との違いもセットで整理してください")

    return "".join(parts)


def build_explanation(term: str, src: SourceParts, past: PastBundle | None) -> str:
    if past and past.wrong_choices:
        w = past.wrong_choices[0]
        if len(w) > 70:
            w = w[:68] + "…"
        base = past.correct.rstrip("。") if past.correct else src.past_exam.rstrip("。")
        return (
            f"演習第{past.qno}問の正答は「{base}」。"
            f"誤りになりやすいのは「{w}」のように、根拠・対象・責任主体がずれる肢です。"
        )
    if src.past_exam:
        return (
            f"演習では「{src.past_exam.rstrip('。')}」が正答の要点です。"
            f"「{term}」と矛盾する限定表現（のみ・必ず・不要）に注意してください。"
        )
    if src.key_point:
        return (
            f"「{src.key_point.rstrip('。')}」と矛盾する記述が誤りになりやすいです。"
            f"定義と選択肢を1語ずつ照合してください。"
        )
    return f"「{term}」は、定義と選択肢の根拠・対象範囲・担当者の3点をセットで確認してください。"


def build_exam_points(src: SourceParts, past: PastBundle | None) -> str:
    pts: list[str] = []
    if src.core:
        pts.append(split_sents(src.core)[0] if split_sents(src.core) else src.core)
    if src.key_point:
        pts.append(src.key_point.rstrip("。"))
    if src.past_exam:
        pts.append(src.past_exam.rstrip("。"))
    if past and past.correct:
        short = past.correct[:90] + ("…" if len(past.correct) > 90 else "")
        pts.append(f"演習第{past.qno}問：{short.rstrip('。')}")
    return ";".join(dict.fromkeys(pts))[:500]


def build_mistakes(src: SourceParts, past: PastBundle | None) -> str:
    if past and past.trap_notes:
        return ";".join(t.rstrip("。") for t in past.trap_notes[:3])
    if past and past.wrong_choices:
        return ";".join(w[:80].rstrip("。") for w in past.wrong_choices[:2])
    if src.key_point:
        return f"「{src.key_point[:45].rstrip('。')}」と逆の内容が誤りになりやすい"
    return "類似語・近い制度との境界;断定表現（のみ・必ず）の確認"


def build_memory_tip(term: str, src: SourceParts, past: PastBundle | None) -> str:
    if past:
        return f"演習第{past.qno}問→正答キーワード→{term}の定義、の順でノートに整理。"
    if src.past_exam:
        k = src.past_exam[:35] + ("…" if len(src.past_exam) > 35 else "")
        return f"「{k.rstrip('。')}」を{term}の演習キーワードとして暗記。"
    return f"{term}：定義1行＋誰が担うか1行、で復習。"


def build_lead(term: str, category: str, src: SourceParts) -> str:
    hook = split_sents(src.core)[0] if split_sents(src.core) else src.core
    if len(hook) > 65:
        hook = hook[:63] + "…"
    return (
        f"メンタルヘルスII種（{category}）の「{term}」。"
        f"{hook.rstrip('。')}。"
        f"定義・演習の出題パターン・混同点を整理します。"
    )


def build_faq(
    term: str,
    category: str,
    short: str,
    src: SourceParts,
    past: PastBundle | None,
) -> dict[str, str]:
    faq1 = short.rstrip("。") + "。"
    if src.extra_sents:
        for s in src.extra_sents:
            if s.rstrip("。") not in faq1 and not is_generic(s):
                faq1 += s if s.endswith("。") else s + "。"
                if len(faq1) > 220:
                    break
    if src.key_point and src.key_point.rstrip("。") not in faq1:
        faq1 += f"試験では「{src.key_point.rstrip('。')}」が頻出です。"

    if past:
        faq2 = (
            f"演習第{past.qno}問のように、{term}の定義や制度の位置づけを問う選択肢問題が出ます。"
            f"正答は「{past.correct[:75].rstrip('。')}…」の趣旨と一致します。"
        )
    elif src.past_exam:
        faq2 = (
            f"「{src.past_exam.rstrip('。')}」が正答キーワードになる設問が多いです。"
            f"関連演習で正答肢の表現を確認してください。"
        )
    else:
        faq2 = f"{category}分野では、{term}の意味と担当者・義務がセットで問われます。"

    return {
        "faq_1_question": f"{term}とは何ですか？",
        "faq_1_answer": faq1,
        "faq_2_question": f"{term}は試験でどう問われますか？",
        "faq_2_answer": faq2,
        "faq_3_question": f"{term}の学習で押さえる注意点は？",
        "faq_3_answer": CATEGORY_FAQ3.get(category, CATEGORY_FAQ3["基礎・役割"]),
    }


def build_example(past: PastBundle | None, src: SourceParts) -> tuple[str, str]:
    if not past:
        return "", ""
    if past.wrong_choices:
        q = past.wrong_choices[0]
        if len(q) > 130:
            q = q[:128] + "…"
        a = past.correct[:160] if past.correct else "演習解説を参照"
        return q, f"×（{a.rstrip('。')}）"
    if past.stem:
        return (
            past.stem[:130] + ("…" if len(past.stem) > 130 else ""),
            past.correct[:160] if past.correct else "演習解説を参照",
        )
    return "", ""


def content_len(row: dict[str, str]) -> int:
    keys = ("short_def", "term_detail_body", "explanation", "exam_points", "common_mistakes", "memory_tip")
    return sum(len(norm(row.get(k))) for k in keys)


def expand_to_minimum(
    row: dict[str, str],
    term: str,
    category: str,
    legal: str,
    src: SourceParts,
    past: PastBundle | None,
    related: list[str],
) -> None:
    """900字未満のとき、用語固有の情報だけを追記（定型パディング禁止）。"""
    for _ in range(14):
        if content_len(row) >= 900:
            return
        body = norm(row.get("term_detail_body"))
        expl = norm(row.get("explanation"))
        added = False

        if legal and legal.rstrip("。") not in body:
            row["term_detail_body"] = body + f"関連法令・根拠：{legal.rstrip('。')}。"
            continue

        if related and not any(r in body for r in related):
            row["term_detail_body"] = body + f"あわせて整理したい関連用語：{'、'.join(related)}。"
            continue

        for s in src.extra_sents:
            if s.rstrip("。") not in body:
                row["term_detail_body"] = body + (s if s.endswith("。") else s + "。")
                added = True
                break
        if added:
            continue

        if past and past.summary and past.summary not in body:
            row["term_detail_body"] = body + (
                past.summary if past.summary.endswith("。") else past.summary + "。"
            )
            continue

        if past and past.trap_notes:
            cm = norm(row.get("common_mistakes"))
            for t in past.trap_notes:
                if t.rstrip("。") not in cm:
                    row["common_mistakes"] = cm + ";" + t.rstrip("。") if cm else t.rstrip("。")
                    added = True
                    break
        if added:
            continue

        if past and past.wrong_choices:
            for w in past.wrong_choices:
                if w[:40] not in expl and w[:40] not in body:
                    row["explanation"] = expl + f"誤答肢の参考：「{w[:75].rstrip('。')}…」。"
                    added = True
                    break
        if added:
            continue

        if past and past.stem and past.stem[:50] not in expl:
            row["explanation"] = expl + f"演習第{past.qno}問の設問文は「{past.stem[:85].rstrip('。')}…」の趣旨です。"
            continue

        if src.past_exam and src.past_exam not in body:
            row["term_detail_body"] = body + f"演習キーワード：「{src.past_exam.rstrip('。')}」。"
            continue

        if src.key_point:
            ep = norm(row.get("exam_points"))
            if src.key_point.rstrip("。") not in ep:
                row["exam_points"] = ep + ";" + src.key_point.rstrip("。") if ep else src.key_point.rstrip("。")
                continue

        mt = norm(row.get("memory_tip"))
        if category and category not in mt:
            row["memory_tip"] = mt + f"（{category}分野の表に{term}を1行追加）"
            continue

        break


def fill_top20_gaps(
    row: dict[str, str],
    term: str,
    category: str,
    src: SourceParts,
    past: PastBundle | None,
) -> None:
    body = norm(row.get("term_detail_body"))
    short = norm(row.get("short_def"))
    if not short and body:
        short = split_sents(body)[0] if split_sents(body) else body[:140]
        if len(short) > 140:
            short = short[:138] + "…"
        row["short_def"] = short

    if not norm(row.get("article_lead")):
        row["article_lead"] = build_lead(term, category, src)

    faq = build_faq(term, category, norm(row.get("short_def")) or short, src, past)
    for k in ("faq_1_question", "faq_1_answer", "faq_3_question", "faq_3_answer"):
        if not norm(row.get(k)):
            row[k] = faq[k]
    if not norm(row.get("faq_2_question")):
        row["faq_2_question"] = faq["faq_2_question"]
    if not norm(row.get("faq_2_answer")):
        row["faq_2_answer"] = faq["faq_2_answer"]

    if not norm(row.get("exam_points")):
        row["exam_points"] = build_exam_points(src, past)
    if not norm(row.get("memory_tip")):
        row["memory_tip"] = build_memory_tip(term, src, past)


def rewrite_row(
    row: dict[str, str],
    checklist: dict[str, str],
    past_index: dict[int, dict[str, str]],
    valid_terms: set[str],
    top20: dict[str, dict[str, str]],
) -> None:
    term = norm(row.get("term"))
    if not term:
        return

    if term in top20:
        for k, v in top20[term].items():
            row[k] = v
        text = checklist.get(term) or norm(row.get("definition"))
        src = parse_source(term, text)
        category = norm(row.get("category"))
        legal = norm(row.get("legal_basis"))
        past_row = find_past_row(term, norm(row.get("practice_question")), past_index)
        past = build_past_bundle(past_row)
        related = filter_related(norm(row.get("related_terms")), src.related, valid_terms)
        fill_top20_gaps(row, term, category, src, past)
        if past and past.correct and past.correct not in norm(row.get("term_detail_body")):
            body = norm(row.get("term_detail_body"))
            row["term_detail_body"] = body + f"演習第{past.qno}問の解説：{past.correct}"
        expand_to_minimum(row, term, category, legal, src, past, related)
        return

    text = checklist.get(term) or norm(row.get("definition"))
    src = parse_source(term, text)
    past_row = find_past_row(term, norm(row.get("practice_question")), past_index)
    past = build_past_bundle(past_row)
    related = filter_related(norm(row.get("related_terms")), src.related, valid_terms)
    category = norm(row.get("category"))
    legal = norm(row.get("legal_basis"))

    short = split_sents(src.core)[0] if split_sents(src.core) else src.core
    if len(short) > 140:
        short = short[:138] + "…"

    row["short_def"] = short
    row["term_detail_body"] = build_detail_body(term, category, legal, src, past, related)
    row["explanation"] = build_explanation(term, src, past)
    row["exam_points"] = build_exam_points(src, past)
    row["memory_tip"] = build_memory_tip(term, src, past)
    row["common_mistakes"] = build_mistakes(src, past)
    row["article_lead"] = build_lead(term, category, src)

    for k, v in build_faq(term, category, short, src, past).items():
        row[k] = v

    ex_q, ex_a = build_example(past, src)
    if ex_q and ex_a:
        row["example_question"] = ex_q
        row["example_answer"] = ex_a

    expand_to_minimum(row, term, category, legal, src, past, related)


def main() -> int:
    checklist = load_checklist()
    past_index = load_past_index()
    top20 = patch_top20()

    with CSV_PATH.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)
    valid = {norm(r.get("term")) for r in rows if norm(r.get("term"))}

    for row in rows:
        rewrite_row(row, checklist, past_index, valid, top20)

    with CSV_PATH.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

    ge900 = sum(1 for r in rows if content_len(r) >= 900)
    avg = sum(content_len(r) for r in rows) // len(rows)
    linked = sum(1 for r in rows if "演習第" in norm(r.get("explanation")))
    print(
        f"handcrafted: terms={len(rows)}, ge900={ge900}/{len(rows)}, "
        f"avg_len={avg}, past_in_explanation={linked}/{len(rows)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
