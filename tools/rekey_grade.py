#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""II種（ルート）の手書きHTML/JSを新種（grade）ブランドへ「リキー」する。

build_grade.py が staging にコピーしたII種生ファイル（index.html / about.html /
privacy.html / related-sites.html / articles/index.html / site-analytics.js）には、
II種のブランド名・試験名・コース名が本文に焼き込まれている。apply_site_config の
プレースホルダー置換は既に消費済みのため本文プロセには効かない（chrome=ヘッダ/
フッタ/canonical/OG/GA4 は apply_site_config の正規表現上書きが config から再導出
するので別途対応不要）。本モジュールは本文プロセのII種固有語を grade 側へ置換する。

置換は「最長一致優先」。ルート/grade 両 site-config.json から機械生成したマップに、
examGrade 由来のコース名・級トークンの補助マップを足す。brandMark（例 "M"）は
単体ラテン1字で誤爆するため置換対象にしない（chrome 側が処理する）。

使い方（通常は build_grade.py から呼ぶ）:
    python3 tools/rekey_grade.py <grade_id> <stage_dir>
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.grades import get_grade  # noqa: E402

# staging 上でリキー対象にする手書きファイル（ROOT 相対）。
REKEY_TARGETS = (
    "index.html",
    "about.html",
    "privacy.html",
    "related-sites.html",
    "articles/index.html",
    "site-analytics.js",
)

# 級（examGrade）→ コース名の正本。II種=ラインケアコース。
COURSE_BY_GRADE = {
    "II種": "ラインケアコース",
    "III種": "セルフケアコース",
    "I種": "マスターコース",
}
# 級 → コースのケア種別（"ラインケア" 等の単体語）。
CARE_BY_GRADE = {
    "II種": "ラインケア",
    "III種": "セルフケア",
    "I種": "マスター",
}
# 級 → 漢数字「種」（"二種" 等の単体語）。
KANJI_GRADE = {
    "II種": "二種",
    "III種": "三種",
    "I種": "一種",
}


def _load_cfg(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def build_rekey_map(root_cfg: dict, grade_cfg: dict) -> list[tuple[str, str]]:
    """II種→grade の置換ペアを最長一致優先で返す。空/同値/自明な誤爆源は除外。"""
    pairs: dict[str, str] = {}

    # config 由来（複合語を先に消費させる）。
    for key in ("brandName", "examName", "brandLogoBottom", "officialOrganization"):
        src = str(root_cfg.get(key) or "").strip()
        dst = str(grade_cfg.get(key) or "").strip()
        if src and dst and src != dst:
            pairs[src] = dst

    # examGrade 由来の補助（II種固定 → grade の級）。
    grade_tok = str(grade_cfg.get("examGrade") or "").strip()
    if grade_tok in ("III種", "I種"):
        # コース名・ケア種別・級トークン（単体）。
        if COURSE_BY_GRADE.get(grade_tok):
            pairs["ラインケアコース"] = COURSE_BY_GRADE[grade_tok]
        if CARE_BY_GRADE.get(grade_tok):
            pairs["ラインケア"] = CARE_BY_GRADE[grade_tok]
        pairs["II種"] = grade_tok
        if KANJI_GRADE.get(grade_tok):
            pairs["二種"] = KANJI_GRADE[grade_tok]

    # 最長一致優先（長い src から適用）。
    return sorted(pairs.items(), key=lambda kv: len(kv[0]), reverse=True)


def rekey_text(text: str, mapping: list[tuple[str, str]]) -> str:
    for src, dst in mapping:
        text = text.replace(src, dst)
    return text


def rekey_stage(grade_id: str, stage_dir: Path) -> int:
    grade = get_grade(grade_id)
    root_cfg = _load_cfg(REPO_ROOT / "site-config.json")
    grade_cfg = _load_cfg(grade.config_path)
    mapping = build_rekey_map(root_cfg, grade_cfg)
    if not mapping:
        print(f"[rekey:{grade_id}] 置換ペアなし（スキップ）")
        return 0

    changed = 0
    for rel in REKEY_TARGETS:
        path = stage_dir / rel
        if not path.is_file():
            continue
        old = path.read_text(encoding="utf-8")
        new = rekey_text(old, mapping)
        if new != old:
            path.write_text(new, encoding="utf-8")
            changed += 1
    print(
        f"[rekey:{grade_id}] {changed} ファイル更新 / {len(mapping)} ペア "
        f"(例: {mapping[0][0]!r}→{mapping[0][1]!r})"
    )
    return 0


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__)
        return 2
    grade_id = sys.argv[1]
    stage_dir = Path(sys.argv[2]).resolve()
    return rekey_stage(grade_id, stage_dir)


if __name__ == "__main__":
    raise SystemExit(main())
