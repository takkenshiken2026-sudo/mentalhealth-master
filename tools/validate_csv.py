#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Validate template CSV files before generating the site."""

from __future__ import annotations

import csv
import re
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.site_config import category_to_field_map

DATA_DIR = ROOT / "data"


@dataclass
class Issue:
    level: str
    path: Path
    line: int | None
    message: str

    def format(self) -> str:
        rel = self.path.relative_to(ROOT)
        loc = f"{rel}:{self.line}" if self.line else str(rel)
        return f"[{self.level}] {loc} - {self.message}"


class Validator:
    def __init__(self) -> None:
        self.issues: list[Issue] = []
        self.category_map = category_to_field_map()

    def error(self, path: Path, line: int | None, message: str) -> None:
        self.issues.append(Issue("ERROR", path, line, message))

    def warn(self, path: Path, line: int | None, message: str) -> None:
        self.issues.append(Issue("WARN", path, line, message))

    def read_csv(self, path: Path, required: set[str]) -> tuple[list[str], list[dict[str, str]]]:
        if not path.is_file():
            self.error(path, None, "CSVファイルが見つかりません")
            return [], []
        text = path.read_text(encoding="utf-8-sig")
        if not text.strip():
            self.error(path, None, "CSVが空です")
            return [], []

        first_line = text.splitlines()[0] if text.splitlines() else ""
        headers = next(csv.reader([first_line])) if first_line else []
        dupes = sorted({h for h in headers if headers.count(h) > 1})
        for h in dupes:
            self.error(path, 1, f"列名が重複しています: {h}")

        rows = list(csv.DictReader(text.splitlines()))
        fieldnames = list(rows[0].keys()) if rows else (headers or [])
        missing = sorted(required - set(fieldnames))
        for col in missing:
            self.error(path, 1, f"必須列がありません: {col}")
        if missing:
            return fieldnames, rows
        if not rows:
            self.error(path, None, "データ行がありません")
        return fieldnames, rows

    @staticmethod
    def norm(value: object) -> str:
        return str(value or "").strip()

    @staticmethod
    def truthy(value: object) -> bool:
        return str(value or "").strip().upper() == "TRUE"

    def require_text(self, path: Path, row: dict[str, str], line: int, col: str) -> str:
        value = self.norm(row.get(col))
        if not value:
            self.error(path, line, f"{col} が空です")
        return value

    def require_int(self, path: Path, row: dict[str, str], line: int, col: str, *, min_value: int | None = None) -> int | None:
        raw = self.require_text(path, row, line, col)
        if not raw:
            return None
        try:
            value = int(raw)
        except ValueError:
            self.error(path, line, f"{col} は整数で入力してください: {raw!r}")
            return None
        if min_value is not None and value < min_value:
            self.error(path, line, f"{col} は {min_value} 以上にしてください: {value}")
        return value

    def validate_category(self, path: Path, row: dict[str, str], line: int) -> str:
        category = self.require_text(path, row, line, "category")
        if category and category not in self.category_map:
            allowed = ", ".join(sorted(self.category_map.keys()))
            self.error(path, line, f"未登録の category です: {category!r}（site-config.json の fields[].name / aliases に追加してください。利用可能: {allowed}）")
        return category

    def validate_choices_and_correct(self, path: Path, row: dict[str, str], line: int, *, allow_invalidated: bool) -> None:
        for i in range(1, 5):
            self.require_text(path, row, line, f"choice_{i}")
        invalidated = allow_invalidated and self.truthy(row.get("is_invalidated"))
        correct = self.norm(row.get("correct"))
        if invalidated and not correct:
            return
        if not correct:
            self.error(path, line, "correct が空です")
            return
        try:
            n = int(correct)
        except ValueError:
            self.error(path, line, f"correct は 1〜5 の整数で入力してください: {correct!r}")
            return
        choices = [self.norm(row.get(f"choice_{i}")) for i in range(1, 6)]
        max_choice = max([i for i, value in enumerate(choices, start=1) if value] or [4])
        if not 1 <= n <= max_choice:
            self.error(path, line, f"correct は 1〜{max_choice} の範囲で入力してください: {n}")

    def validate_past_questions(self) -> None:
        path = DATA_DIR / "past_questions.csv"
        required = {
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
        }
        _, rows = self.read_csv(path, required)
        seen: set[tuple[int, int]] = set()
        for idx, row in enumerate(rows, start=2):
            year = self.require_int(path, row, idx, "exam_year", min_value=1900)
            qno = self.require_int(path, row, idx, "question_no", min_value=1)
            if year is not None and qno is not None:
                key = (year, qno)
                if key in seen:
                    self.error(path, idx, f"exam_year + question_no が重複しています: {year}-{qno}")
                seen.add(key)
            self.require_text(path, row, idx, "exam_wareki")
            self.require_text(path, row, idx, "type")
            self.validate_category(path, row, idx)
            self.require_text(path, row, idx, "stem")
            self.require_text(path, row, idx, "explanation")
            self.validate_choices_and_correct(path, row, idx, allow_invalidated=True)

    def validate_original_questions(self) -> None:
        path = DATA_DIR / "original_questions.csv"
        required = {
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
        }
        _, rows = self.read_csv(path, required)
        seen: set[int] = set()
        for idx, row in enumerate(rows, start=2):
            qno = self.require_int(path, row, idx, "question_no", min_value=1)
            if qno is not None:
                if qno in seen:
                    self.error(path, idx, f"question_no が重複しています: {qno}")
                seen.add(qno)
            self.require_text(path, row, idx, "type")
            self.validate_category(path, row, idx)
            self.require_text(path, row, idx, "stem")
            self.require_text(path, row, idx, "explanation")
            self.validate_choices_and_correct(path, row, idx, allow_invalidated=False)

    def validate_ichimon(self) -> None:
        path = DATA_DIR / "past_questions_marubatsu_all_explanations.csv"
        required = {"id", "question", "answer", "explanation", "category"}
        _, rows = self.read_csv(path, required)
        seen: set[str] = set()
        for idx, row in enumerate(rows, start=2):
            rid = self.require_text(path, row, idx, "id")
            if rid:
                if rid in seen:
                    self.error(path, idx, f"id が重複しています: {rid}")
                seen.add(rid)
                if len(rid.split("-")) != 3:
                    self.warn(path, idx, f"id は YYYY-問番号-枝番 形式を推奨します: {rid}")
            self.validate_category(path, row, idx)
            self.require_text(path, row, idx, "question")
            self.require_text(path, row, idx, "explanation")
            answer = self.require_text(path, row, idx, "answer")
            if answer and answer not in {"○", "〇", "×", "✕", "╳"}:
                self.error(path, idx, f"answer は ○ または × で入力してください: {answer!r}")

    def validate_glossary(self) -> None:
        path = DATA_DIR / "glossary_terms.csv"
        required = {
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
        }
        _, rows = self.read_csv(path, required)
        seen: set[tuple[str, str]] = set()
        for idx, row in enumerate(rows, start=2):
            term = self.require_text(path, row, idx, "term")
            reading = self.require_text(path, row, idx, "reading")
            if term:
                key = (term, reading)
                if key in seen:
                    self.error(path, idx, f"term + reading が重複しています: {term} / {reading}")
                seen.add(key)
            self.validate_category(path, row, idx)
            self.require_text(path, row, idx, "short_def")
            self.require_text(path, row, idx, "definition")
            self.require_text(path, row, idx, "explanation")
            importance = self.norm(row.get("importance"))
            if importance and importance not in {"A", "B", "C", "S"}:
                self.warn(path, idx, f"importance は A/B/C/S のいずれかを推奨します: {importance}")
            for col in (
                "article_title",
                "article_lead",
                "term_detail_body",
                "exam_points",
                "common_mistakes",
                "memory_tip",
                "example_question",
                "example_answer",
            ):
                if col in row and self.norm(row.get(col)) and len(self.norm(row.get(col))) < 12:
                    self.warn(path, idx, f"{col} は詳細記事用の任意列です。本文としては短めです")

    def validate_guide_articles(self) -> None:
        path = DATA_DIR / "guide_articles.csv"
        required = {
            "slug",
            "genre",
            "title",
            "meta_description",
            "lead",
            "priority",
            "section_1_heading",
            "section_1_body",
        }
        _, rows = self.read_csv(path, required)
        seen: set[str] = set()
        for idx, row in enumerate(rows, start=2):
            slug = self.require_text(path, row, idx, "slug")
            if slug:
                if slug in seen:
                    self.error(path, idx, f"slug が重複しています: {slug}")
                seen.add(slug)
                if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", slug):
                    self.error(path, idx, f"slug は半角英数字とハイフンで入力してください: {slug}")
            self.require_text(path, row, idx, "genre")
            self.require_text(path, row, idx, "title")
            self.require_text(path, row, idx, "meta_description")
            self.require_text(path, row, idx, "lead")
            self.require_int(path, row, idx, "priority", min_value=1)
            self.require_text(path, row, idx, "section_1_heading")
            self.require_text(path, row, idx, "section_1_body")
            for col in ("author_name", "fact_checked_at", "primary_sources", "original_note", "action_items"):
                if col in row and not self.norm(row.get(col)):
                    self.warn(path, idx, f"{col} はSEO品質確認用の推奨列です")
            for item in [x.strip() for x in self.norm(row.get("primary_sources")).split(";") if x.strip()]:
                if "|" in item:
                    label, url = [x.strip() for x in item.split("|", 1)]
                    if not label or not url.startswith(("http://", "https://")):
                        self.warn(path, idx, f"primary_sources は ラベル|URL 形式を推奨します: {item}")
            for n in range(1, 4):
                q = self.norm(row.get(f"faq_{n}_question"))
                a = self.norm(row.get(f"faq_{n}_answer"))
                if bool(q) != bool(a):
                    self.warn(path, idx, f"faq_{n}_question と faq_{n}_answer はセットで入力してください")
                if q and not q.endswith(("?", "？")):
                    self.warn(path, idx, f"faq_{n}_question は質問文として入力してください: {q}")
                if a and re.fullmatch(r"[a-z0-9][a-z0-9-]*:.+", a):
                    self.warn(path, idx, f"faq_{n}_answer に related_links らしき値が入っています: {a}")
            related = self.norm(row.get("related_links"))
            if related:
                for item in [x.strip() for x in related.split(";") if x.strip()]:
                    target = item.split(":", 1)[0].strip()
                    if target.startswith(("http://", "https://")):
                        continue
                    if target and target not in seen and not re.fullmatch(r"[a-z0-9][a-z0-9-]*", target):
                        self.warn(path, idx, f"related_links の内部リンク先 slug 形式を確認してください: {target}")

    def run(self) -> int:
        self.validate_past_questions()
        self.validate_original_questions()
        self.validate_ichimon()
        self.validate_glossary()
        self.validate_guide_articles()

        for issue in self.issues:
            print(issue.format(), file=sys.stderr if issue.level == "ERROR" else sys.stdout)

        errors = [i for i in self.issues if i.level == "ERROR"]
        warnings = [i for i in self.issues if i.level == "WARN"]
        if errors:
            print(f"CSV validation failed: {len(errors)} error(s), {len(warnings)} warning(s)", file=sys.stderr)
            return 1
        print(f"CSV validation passed: {warnings and str(len(warnings)) + ' warning(s)' or 'no warnings'}")
        return 0


def main() -> int:
    return Validator().run()


if __name__ == "__main__":
    raise SystemExit(main())
