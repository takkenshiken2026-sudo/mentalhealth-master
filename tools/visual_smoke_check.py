#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Capture screenshots for key pages when Playwright is available."""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PATHS = [
    "index.html",
    "q/index.html",
    "terms/index.html",
    "articles/index.html",
    "about.html",
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8765")
    parser.add_argument("--out", default="visual-smoke")
    args = parser.parse_args()

    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        print("Playwright が見つかりません。スクリーンショット確認を行う場合は次を実行してください:")
        print("  python3 -m pip install playwright")
        print("  python3 -m playwright install chromium")
        print("その後、別ターミナルで `python3 -m http.server 8765` を起動してから再実行します。")
        print("確認対象URL:")
        for path in DEFAULT_PATHS:
            print(f"  {args.base_url.rstrip('/')}/{path}")
        return 0

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    out_dir = ROOT / args.out / stamp
    out_dir.mkdir(parents=True, exist_ok=True)
    base = args.base_url.rstrip("/")

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1280, "height": 900}, device_scale_factor=1)
        for path in DEFAULT_PATHS:
            url = f"{base}/{path}"
            page.goto(url, wait_until="networkidle")
            name = path.replace("/", "__").replace(".html", "") or "index"
            page.screenshot(path=str(out_dir / f"{name}.png"), full_page=True)
            print(f"captured {url}")
        mobile = browser.new_page(viewport={"width": 390, "height": 844}, is_mobile=True)
        mobile.goto(f"{base}/index.html", wait_until="networkidle")
        mobile.screenshot(path=str(out_dir / "index__mobile.png"), full_page=True)
        browser.close()
    print(f"Screenshots written to {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
