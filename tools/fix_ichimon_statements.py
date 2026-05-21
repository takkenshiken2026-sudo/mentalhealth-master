#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""一問一答CSVの問題文を、4択過去問の stem + 選択肢から ○× 判定文に再構成する。

index.html の adaptStemMcInstructionsForIchimondou / buildIchiJudgementSentence と同等のロジック。
"""

from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.validate_ichimon_statements import is_judgement_sentence, norm_key

DATA_CSV = ROOT / "data" / "past_questions_marubatsu_all_explanations.csv"
PAST_CSV = ROOT / "data" / "past_questions.csv"

STEM_STRIPS = [
    r"次の記述のうち[、,　\s]*誤りがあるものはどれか[。．]?",
    r"次の記述のうち[、,　\s]*誤っているものはどれか[。．]?",
    r"次の記述のうち[、,　\s]*正しいものはどれか[。．]?",
    r"次の記述について[、,　\s]*誤っているものはどれか[。．]?",
    r"次の記述について[、,　\s]*正しいものはどれか[。．]?",
    r"次の各記述のうち[、,　\s]*誤っているものはどれか[。．]?",
    r"次の各記述のうち[、,　\s]*正しいものはどれか[。．]?",
    r"次の各記述について[、,　\s]*正しいものはどれか[。．]?",
    r"次のうち[、,　\s]*誤っているものはどれか[。．]?",
    r"次のうち[、,　\s]*正しいものはどれか[。．]?",
    r"次の記述について[、,　\s]*適切なものはどれか[。．]?",
    r"誤っている記述はどれか[。．]?",
    r"誤りがあるものはどれか[。．]?",
    r"正しい記述はどれか[。．]?",
    r"誤っているものはどれか[。．]?",
    r"誤りのあるものはどれか[。．]?",
    r"適切なものはどれか[。．]?",
    r"妥当なものはどれか[。．]?",
    r"正しくないものはどれか[。．]?",
    r"正しいものはどれか[。．]?",
]

WRAP_STEM_END = re.compile(
    r"(として|について|に関して|に関する|の場合|において|に関する判例の立場として)$"
)
PREDICATE_IN_OPT = re.compile(
    r"(である|できる|できない|必要がある|必要はない|該当する|該当しない|"
    r"有効である|無効である|正しい|誤りである)$"
)


def adapt_stem(text: str) -> str:
    s = (text or "").strip()
    for pat in STEM_STRIPS:
        s = re.sub(pat, "", s)
    s = re.sub(
        r"以下の(?:1から4までの|１から４までの)?記述のうち[、,　\s]*[^。．]*(?:を選びなさい|はどれか|どれか)[。．]?",
        "",
        s,
    )
    s = re.sub(
        r"次の(?:1から4までの|１から４までの)?記述のうち[、,　\s]*[^。．]*(?:を選びなさい|はどれか|どれか)[。．]?",
        "",
        s,
    )
    s = re.sub(
        r"(?:正しい|誤っている|適切な|不適切な|妥当な|正しくない)もの(?:がいくつあるか)?(?:を選びなさい|はどれか|どれか)[。．]?",
        "",
        s,
    )
    s = re.sub(
        r"(?:正しい|誤っている|適切な|不適切な|妥当な|正しくない)記述(?:がいくつあるか)?(?:を選びなさい|はどれか|どれか)[。．]?",
        "",
        s,
    )
    s = re.sub(
        r"(?:誤り|誤りのある|誤りがある)もの(?:がいくつあるか)?(?:を選びなさい|はどれか|どれか)[。．]?",
        "",
        s,
    )
    s = re.sub(r"(?:組合せ|組み合わせ)(?:はどれか|を選びなさい)[。．]?", "", s)
    s = re.sub(
        r"最も(?:適切|不適切|妥当|正しい|誤った|誤っている)な(?:もの|組み合わせ|組合せ|記述|ケース|機関|要素|内容|事項|者|例|型)を一つ選びなさい[。．]?",
        "",
        s,
    )
    s = re.sub(r"一つ選びなさい[。．]?", "", s)
    s = re.sub(r"次のうち[、,　\s]*", "", s)
    s = re.sub(r"([^。．]+?)(?:もの|記述|項目|内容|の)はどれか[。．]?", r"\1ものとして", s)
    s = re.sub(r"([^。．]+?)に含まれるのはどれか[。．]?", r"\1に含まれるものとして", s)
    s = re.sub(r"([^。．]+?)はどれか[。．]?", r"\1として", s)
    s = re.sub(r"についての\s*$", "について", s)
    s = re.sub(r"に関する\s*$", "に関して", s)
    s = re.sub(r"[、，]\s*$", "", s, flags=re.M)
    s = re.sub(r"\n{3,}", "\n\n", s)
    s = re.sub(r"([。．!?！？])\s*\1+", r"\1", s)
    return s.strip()


def normalize_option_sentence(opt: str) -> str:
    body = (opt or "").strip()
    if not body:
        return ""
    if re.search(r"[。．!?！？]$", body):
        return body
    return body + "。"


def build_judgement_sentence(stem: str, opt: str) -> str:
    s = re.sub(r"[、，。．\s　]+$", "", (stem or "").strip())
    o = re.sub(r"[。．\s　]+$", "", (opt or "").strip())
    if not s:
        return normalize_option_sentence(o)
    if not o:
        return normalize_option_sentence(s)
    if re.match(r"^[①②③④⑤]", o):
        topic = s.rstrip("。")
        if "組み合わせ" in stem or "組合せ" in stem:
            return f"{topic}、「{o}」の組み合わせは正しい。"
        return f"{topic}、「{o}」という内容は正しい。"
    if WRAP_STEM_END.search(s) or (
        not re.search(r"[。．!?！？]$", o) and not PREDICATE_IN_OPT.search(o)
    ):
        return f"{s}、「{o}」という記述は正しい。"
    return f"{s}、「{o}」という記述は正しい。"


def build_option_index() -> dict[str, list[tuple[str, str, str]]]:
    """opt_key -> [(stem, opt, explanation_summary)]"""
    index: dict[str, list[tuple[str, str, str]]] = {}
    if not PAST_CSV.is_file():
        return index
    with PAST_CSV.open(encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            stem = (row.get("stem") or "").strip()
            exp = (row.get("explanation") or row.get("explanation_summary") or "").strip()
            for i in range(1, 5):
                opt = (row.get(f"choice_{i}") or "").strip()
                if not opt:
                    continue
                index.setdefault(norm_key(opt), []).append((stem, opt, exp))
    return index


def lookup_stem(
    question: str,
    index: dict[str, list[tuple[str, str, str]]],
    explanation: str = "",
) -> str:
    hits = index.get(norm_key(question), [])
    if not hits:
        return ""
    exp = (explanation or "").strip()

    def score(hit: tuple[str, str, str]) -> int:
        stem, _opt, stem_exp = hit
        s = 0
        # 解説・設問のキーワード一致で stem を選ぶ（同じ選択肢が複数過去問にある場合）
        for token in re.findall(r"[\u4e00-\u9fff]{4,}", exp + stem_exp):
            if token in stem:
                s += len(token)
        return s

    return max(hits, key=score)[0]


def fix_question(
    question: str,
    index: dict[str, list[tuple[str, str, str]]],
    explanation: str = "",
) -> str:
    q = (question or "").strip()
    if is_judgement_sentence(q):
        return q
    if re.search(r"選びなさい|という記述は正しい|の組み合わせは正しい", q):
        m = re.match(r"^(.+?)、「(.+)」(?:の組み合わせ|という記述)は正しい。?$", q)
        if m:
            stem_raw = m.group(1)
            q = m.group(2)
        else:
            stem_raw = ""
    else:
        stem_raw = ""
    if not stem_raw:
        stem_raw = lookup_stem(q, index, explanation)
    if not stem_raw:
        # ①②③ 形式で stem が取れない場合のフォールバック
        if re.match(r"^[①②③④⑤]", q):
            return f"次の組み合わせは正しい：{q}。"
        if q.endswith("場合"):
            return f"次のケースは安全配慮義務違反が問われうる例として正しい：{q}。"
        return q
    stem = adapt_stem(stem_raw)
    return build_judgement_sentence(stem, q)


def main() -> int:
    if not DATA_CSV.is_file():
        print(f"入力がありません: {DATA_CSV}", file=sys.stderr)
        return 1
    index = build_option_index()
    text = DATA_CSV.read_text(encoding="utf-8-sig")
    rows = list(csv.DictReader(text.splitlines()))
    if not rows:
        print("行がありません", file=sys.stderr)
        return 1
    fieldnames = list(rows[0].keys())
    changed = 0
    for row in rows:
        old = (row.get("question") or "").strip()
        new = fix_question(old, index, row.get("explanation") or "")
        if new != old:
            row["question"] = new
            changed += 1
    with DATA_CSV.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)
    print(f"Updated {changed} / {len(rows)} rows in {DATA_CSV}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
