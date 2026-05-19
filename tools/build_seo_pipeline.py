#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SEO 拡張ビルド（クイズ JS は触らない）。
用語フェーズ3・ガイド追記・章ハブ・過去問静的ページ・sitemap 統一。
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(cmd: list[str]) -> None:
    print("+", " ".join(cmd))
    subprocess.run(cmd, cwd=ROOT, check=True)


def main() -> int:
    py = sys.executable
    run([py, "tools/enrich_glossary_terms_phase3.py"])
    run([py, "tools/populate_guide_articles_extra.py"])
    run([py, "tools/populate_guide_articles_batch20.py"])
    run([py, "tools/populate_guide_articles_batch10.py"])
    run([py, "tools/build_article_pages.py"])
    run([py, "tools/build_glossary_pages.py"])
    run([py, "tools/build_chapter_hub_pages.py"])
    run([py, "tools/export_orig_to_past_questions_csv.py"])
    run([py, "tools/build_past_question_pages.py"])
    run([py, "tools/build_q_index_from_master.py"])
    run([py, "tools/apply_site_config.py"])
    print()
    print("SEO pipeline complete (quiz JS unchanged).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
