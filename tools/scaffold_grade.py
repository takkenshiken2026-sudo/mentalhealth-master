#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""新しい種（grade）のデータ雛形を作る。

メインサイト（II種）の data/*.csv のヘッダー行だけをコピーして、
grades/<id>/data/ に空の CSV を作る（スキーマを完全一致させるため）。
論述のある種（hasEssay）には essays.csv を追加する。
既存データは上書きしない（--force で明示上書き）。

使い方:
    python3 tools/scaffold_grade.py self
    python3 tools/scaffold_grade.py master
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.grades import get_grade

# メイン(II種) data/ 直下から雛形化する CSV。サブディレクトリは対象外。
SOURCE_DATA_DIR = ROOT / "data"

# 論述（記述式）用スキーマ。I種など hasEssay の種にのみ作成する。
ESSAY_HEADER = (
    "essay_no,theme,category,question,model_answer,"
    "scoring_keywords,points_allocation,explanation"
)


def header_of(csv_path: Path) -> str:
    with csv_path.open(encoding="utf-8-sig") as f:
        first = f.readline().rstrip("\n").rstrip("\r")
    return first


def scaffold(grade_id: str, force: bool) -> int:
    grade = get_grade(grade_id)
    if grade.primary:
        print(f"[skip] '{grade_id}' はプライマリ種（ルート運用）なので雛形不要です。")
        return 0

    out_dir = grade.data_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    created, skipped = 0, 0
    for src in sorted(SOURCE_DATA_DIR.glob("*.csv")):
        dst = out_dir / src.name
        if dst.exists() and not force:
            skipped += 1
            continue
        if dst.exists() and dst.read_text(encoding="utf-8").strip():
            # 中身のある既存ファイルは --force でも守る（誤消去防止）。
            print(f"[keep] 中身のある既存ファイルは上書きしません: {dst.relative_to(ROOT)}")
            skipped += 1
            continue
        dst.write_text(header_of(src) + "\n", encoding="utf-8")
        created += 1

    if grade.has_essay:
        essays = out_dir / "essays.csv"
        if essays.exists() and essays.read_text(encoding="utf-8").strip() and not force:
            print(f"[keep] {essays.relative_to(ROOT)} は既存（中身あり）のため維持")
        else:
            essays.write_text(ESSAY_HEADER + "\n", encoding="utf-8")
            created += 1

    print(f"[{grade_id}] 雛形: 作成 {created} / スキップ {skipped}  -> {out_dir.relative_to(ROOT)}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="新しい種のデータ雛形を作る")
    ap.add_argument("grade", help="種ID（grades.json の id、例: self / master）")
    ap.add_argument("--force", action="store_true", help="空の既存ファイルを再生成する")
    args = ap.parse_args()
    return scaffold(args.grade, args.force)


if __name__ == "__main__":
    raise SystemExit(main())
