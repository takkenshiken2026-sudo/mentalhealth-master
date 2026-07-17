#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""全公開 HTML の <head> に AdSense スクリプトを注入する。

site-config.json の adsenseClientId が空ならマーカー付きブロックを除去する。
build_all.py から呼び出す（生成 HTML を含む全ページへ反映）。
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.html_footer import inject_adsense_head  # noqa: E402
from tools.site_config import adsense_client_id  # noqa: E402

SKIP_DIRS = {
    ".git",
    ".github",
    ".cursor",
    "node_modules",
    "public_site",
    "reports",
    "tools",
    "docs",
    "data",
}


def iter_html_files(root: Path) -> list[Path]:
    out: list[Path] = []
    for path in root.rglob("*.html"):
        if any(part in SKIP_DIRS for part in path.relative_to(root).parts):
            continue
        out.append(path)
    return sorted(out)


def main() -> int:
    client = adsense_client_id()
    updated = 0
    for path in iter_html_files(ROOT):
        old = path.read_text(encoding="utf-8")
        new = inject_adsense_head(old)
        if new != old:
            path.write_text(new, encoding="utf-8")
            updated += 1
    if client:
        print(f"inject_adsense_head: updated {updated} file(s) (client={client})")
    else:
        print(f"inject_adsense_head: adsenseClientId unset; cleared markers in {updated} file(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
