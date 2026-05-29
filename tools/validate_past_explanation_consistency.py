#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""過去問 CSV・生成 HTML の正答と解説の整合性を検証する。"""

from __future__ import annotations

import csv
import re
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.q_explanation import build_explanation_html, norm, parse_explanation_choices

CSV_PATH = ROOT / "data" / "past_questions.csv"
Q_PAST = ROOT / "q" / "past"

CIRC = "①②③④"
_GARBLED_LAW = re.compile(r"解説では「(?:※|の[^」]{0,8}法|者[^」]{0,12}法|ただし[^」]{0,8}法)")


@dataclass
class Finding:
    level: str  # ERROR | WARN
    qid: str
    message: str


def qid(row: dict) -> str:
    return f"{row['exam_year']}-Q{row['question_no']}"


def choice_marked_wrong(text: str, n: int) -> bool:
    c = CIRC[n - 1]
    patterns = [
        rf"[（(]{n}[）)]\s*(?:は|が)?\s*(?:誤|正しくない|不適切|該当しない|対象外|違反|誤り)",
        rf"{c}\s*(?:誤|正しくない|不適切|違反)",
        rf"選択肢\s*{n}\s*は\s*(?:誤|不適切|正しくない|違反|誤り)",
        rf"[（(]{n}[）)]\s*誤",
        rf"{c}誤",
    ]
    return any(re.search(p, text) for p in patterns)


def stated_correct_number(text: str) -> int | None:
    for pat in (
        r"正答は\s*[（(]?(\d+)[）)]?",
        r"正解は\s*(\d+)\s*です",
        r"正しいのは\s*[（(]?(\d+)[）)]?",
    ):
        m = re.search(pat, text)
        if m:
            return int(m.group(1))
    return None


def validate_csv_row(row: dict) -> list[Finding]:
    findings: list[Finding] = []
    if row.get("is_invalidated", "").upper() == "TRUE":
        return findings
    try:
        correct = int(row["correct"])
    except (TypeError, ValueError):
        return findings

    q = qid(row)
    exp = norm(row.get("explanation"))
    exp_correct = norm(row.get("explanation_correct"))
    exp_summary = norm(row.get("explanation_summary"))
    all_core = " ".join(x for x in (exp, exp_correct, exp_summary) if x)

    stated = stated_correct_number(all_core)
    if stated is not None and stated != correct:
        findings.append(
            Finding("ERROR", q, f"解説が正答（{stated}）と記載しているが correct={correct}")
        )

    if choice_marked_wrong(all_core, correct):
        stem = norm(row.get("stem"))
        if not re.search(r"不適切|誤っている|誤り", stem):
            findings.append(
                Finding("ERROR", q, f"正答（{correct}）が解説本文で誤りと記載されている")
            )

    parsed = parse_explanation_choices(norm(row.get("explanation_choices")))
    if correct in parsed:
        findings.append(
            Finding("ERROR", q, f"explanation_choices に正答肢（{correct}）の解説が含まれる")
        )

    for n, note in parsed.items():
        if n == correct:
            continue
        if stated_correct_number(note) == n and "正答ではない" not in note:
            findings.append(
                Finding("ERROR", q, f"誤肢（{n}）の解説が正答であると読める: {note[:80]}")
            )

    return findings


def validate_rendered_html(row: dict) -> list[Finding]:
    findings: list[Finding] = []
    if row.get("is_invalidated", "").upper() == "TRUE":
        return findings
    try:
        correct = int(row["correct"])
    except (TypeError, ValueError):
        return findings

    q = qid(row)
    opts = [row.get(f"choice_{i}", "") for i in range(1, 5)]
    page = {
        "stem": row.get("stem", ""),
        "stem_plain": row.get("stem", ""),
        "opts": opts,
        "correct": correct,
        "category": row.get("category", ""),
        "is_invalidated": False,
    }
    html = build_explanation_html(page, row)

    ans_m = re.search(r"q-exp-correct-opt.*?<strong>（(\d+)）</strong>", html, re.DOTALL)
    if ans_m and int(ans_m.group(1)) != correct:
        findings.append(
            Finding(
                "ERROR",
                q,
                f"解説 HTML の正解肢が（{ans_m.group(1)}）だが correct={correct}",
            )
        )

    wrong_m = re.search(
        r"q-exp-wrong-h.*?(?:q-exp-tip-h|q-similar|</div>\s*</section>\s*<section)",
        html,
        re.DOTALL,
    )
    if wrong_m:
        wrong_html = wrong_m.group()
        for cm in re.finditer(r'q-exp-choice-num">（(\d+)）', wrong_html):
            n = int(cm.group(1))
            if n != correct:
                continue
            note_m = re.search(
                rf'q-exp-choice-num">（{n}）.*?</span></p>'
                rf'<p class="q-exp-choice-note">(.*?)</p>',
                wrong_html,
                re.DOTALL,
            )
            note = re.sub(r"<[^>]+>", " ", note_m.group(1)) if note_m else ""
            findings.append(
                Finding("ERROR", q, f"正答（{correct}）が「他の選択肢」に掲載: {note[:80]}")
            )

    if _GARBLED_LAW.search(html):
        findings.append(Finding("WARN", q, "解説に断片的・不正な法令引用（根拠の記述が異なります）"))

    if "根拠の記述が異なります" in html:
        findings.append(Finding("WARN", q, "旧テンプレ「根拠の記述が異なります」が残存"))

    return findings


def validate_static_html(row: dict) -> list[Finding]:
    findings: list[Finding] = []
    try:
        correct = int(row["correct"])
        year = row["exam_year"]
        num = int(row["question_no"])
    except (TypeError, ValueError):
        return findings

    q = qid(row)
    for fmt in (f"q{num:02d}", f"q{num}"):
        path = Q_PAST / f"y{year}" / fmt / "index.html"
        if not path.is_file():
            continue
        html = path.read_text(encoding="utf-8")
        ans_m = re.search(r"正答は\s*<strong>（(\d+)）</strong>", html)
        if ans_m and int(ans_m.group(1)) != correct:
            findings.append(
                Finding(
                    "ERROR",
                    q,
                    f"{path.name}: 表示正答（{ans_m.group(1)}）≠ CSV correct={correct}",
                )
            )
        break
    return findings


def main() -> int:
    if not CSV_PATH.is_file():
        print(f"error: CSV not found: {CSV_PATH}", file=sys.stderr)
        return 1

    rows = list(csv.DictReader(CSV_PATH.read_text(encoding="utf-8-sig").splitlines()))
    all_findings: list[Finding] = []
    for row in rows:
        all_findings.extend(validate_csv_row(row))
        all_findings.extend(validate_rendered_html(row))
        all_findings.extend(validate_static_html(row))

    errors = [f for f in all_findings if f.level == "ERROR"]
    warns = [f for f in all_findings if f.level == "WARN"]

    print(f"past_questions rows={len(rows)} errors={len(errors)} warnings={len(warns)}")
    for f in errors:
        print(f"  ERROR [{f.qid}] {f.message}")
    for f in warns[:30]:
        print(f"  WARN  [{f.qid}] {f.message}")
    if len(warns) > 30:
        print(f"  ... +{len(warns) - 30} more warnings")

    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
