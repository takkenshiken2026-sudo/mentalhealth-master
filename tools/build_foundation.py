#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 1 foundation build: CSV bootstrap, validation, site-config sync.
Does NOT regenerate quiz JS or HTML pages (avoids overwriting production embeds).
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
    run([py, "tools/bootstrap_data_csv.py"])
    run([py, "tools/validate_csv.py"])
    run([py, "tools/apply_site_config.py"])
    run([py, "tools/build_q_index_from_master.py"])
    print()
    print("Foundation build complete.")
    print("- site-config.json → site-config.js, site-theme.css, robots.txt")
    print("- data/*.csv ready for guide/glossary generators")
    print()
    print("Next: SEO pages (terms, guides, past q static) without touching quiz JS:")
    print("  python3 tools/build_seo_pipeline.py")
    print("  or: python3 tools/build_all.py")
    print("Full (WARNING: regenerates quiz JS): EXAM_SITE_FULL_BUILD=1 python3 tools/build_all.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
