#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""One-command build for the exam-site template."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Default off: existing eisei1-*.js and hand-tuned HTML are preserved until CSV is complete.
FULL_BUILD = os.environ.get("EXAM_SITE_FULL_BUILD", "0") == "1"


def run(cmd: list[str]) -> None:
    print("+", " ".join(cmd))
    subprocess.run(cmd, cwd=ROOT, check=True)


def main() -> int:
    py = sys.executable
    if not (ROOT / "data" / "guide_articles.csv").is_file():
        run([py, "tools/bootstrap_data_csv.py"])
    run([py, "tools/validate_csv.py"])
    run([py, "tools/apply_site_config.py"])
    if FULL_BUILD:
        run([py, "tools/csv_to_exam_site_master.py"])
        run([py, "tools/glossary_csv_to_eisei_embed_js.py"])
        run([py, "tools/csv_to_eisei_ichimon_js.py"])
        run([py, "tools/build_past_question_pages.py"])
        run([py, "tools/build_article_pages.py"])
        run([py, "tools/build_glossary_pages.py"])
        run([py, "tools/validate_generated_seo.py"])
        run(["bash", "tools/prepare_public_site.sh"])
    else:
        run([py, "tools/build_seo_pipeline.py"])
        print()
        print("SEO pipeline done (quiz JS unchanged). Full rebuild: EXAM_SITE_FULL_BUILD=1 python3 tools/build_all.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
