# -*- coding: utf-8 -*-
"""検定の種（grade）レジストリ grades.json を読むヘルパー。

既存ツールは「1サイトルート = 1種」で動く（tools/site_config.py が
EXAM_SITE_ROOT / cwd から site-config.json を解決する）。本モジュールは
その外側で「どの種がどのルート・どの basePath に住むか」だけを管理する。
既存II種サイト（ルート）には一切影響しない純粋な追加レイヤー。
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = REPO_ROOT / "grades.json"


@dataclass(frozen=True)
class Grade:
    id: str
    label: str
    short_label: str
    exam_name: str
    root: Path          # サイトルートの絶対パス（EXAM_SITE_ROOT に渡せる）
    base_path: str      # 公開時のサブパス（例: "/self"、II種は ""）
    primary: bool
    has_essay: bool
    published: bool     # build_site.py（本番公開）の対象か。false は未公開（ビルドは可能）。

    @property
    def config_path(self) -> Path:
        return self.root / "site-config.json"

    @property
    def data_dir(self) -> Path:
        return self.root / "data"


def _load_registry() -> dict:
    if not REGISTRY_PATH.is_file():
        raise FileNotFoundError(f"grades.json が見つかりません: {REGISTRY_PATH}")
    data = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or "grades" not in data:
        raise ValueError("grades.json は {\"grades\": [...]} 形式にしてください")
    return data


def load_grades() -> list[Grade]:
    out: list[Grade] = []
    for row in _load_registry()["grades"]:
        root = (REPO_ROOT / str(row["root"])).resolve()
        out.append(
            Grade(
                id=str(row["id"]),
                label=str(row.get("label") or row["id"]),
                short_label=str(row.get("shortLabel") or row["id"]),
                exam_name=str(row.get("examName") or ""),
                root=root,
                base_path=str(row.get("basePath") or "").rstrip("/"),
                primary=bool(row.get("primary")),
                has_essay=bool(row.get("hasEssay")),
                published=bool(row.get("published", True)),
            )
        )
    return out


def get_grade(grade_id: str) -> Grade:
    for g in load_grades():
        if g.id == grade_id:
            return g
    raise KeyError(f"未知の grade: {grade_id}")


def primary_grade() -> Grade:
    grades = load_grades()
    for g in grades:
        if g.primary:
            return g
    return grades[0]


def secondary_grades() -> list[Grade]:
    return [g for g in load_grades() if not g.primary]


def published_grades() -> list[Grade]:
    """本番公開対象の種（published=true）。build_site.py が公開に使う。"""
    return [g for g in load_grades() if g.published]


def published_secondary_grades() -> list[Grade]:
    """本番公開対象の副種（プライマリ=II種を除く published=true）。"""
    return [g for g in load_grades() if not g.primary and g.published]


if __name__ == "__main__":
    for g in load_grades():
        flag = "primary" if g.primary else ("essay" if g.has_essay else "sub")
        print(f"{g.id:7s} [{flag:7s}] base='{g.base_path or '/'}' root={g.root}")
