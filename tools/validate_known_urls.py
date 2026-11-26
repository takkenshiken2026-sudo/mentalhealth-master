#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""検索実績のある URL が公開物（public_site/）で 404 になっていないかを検証する。

背景: 2026-11-13 の記事ラインナップ刷新で、GSC に表示実績のある旧記事 URL 84 本が
転送なしの 404 になった。記事の廃止・slug 変更時に転送の登録漏れがあれば
ビルドを止めて気づけるようにする。

対象 URL: reports/gsc/*/pages.csv（GSC「ページ」シートの CSV 書き出し）の 1 列目。
判定: URL のパスに対応するファイルが public_site/ に存在すれば OK（中身が転送スタブでも可）。
      #以降・クエリ文字列は無視する。サイト外ドメインの URL は対象外。

失敗時の直し方: data/guide_retired.json の redirects に「旧slug: 転送先slug」を追加する
（記事以外の URL は、その URL に転送スタブを置く）。

使い方: python3 tools/validate_known_urls.py [--public-dir public_site]
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parents[1]
GSC_DIR = ROOT / "reports" / "gsc"


def site_host() -> str:
    cfg = ROOT / "site-config.json"
    try:
        origin = json.loads(cfg.read_text(encoding="utf-8")).get("siteOrigin") or ""
    except (OSError, json.JSONDecodeError):
        origin = ""
    return urlparse(origin).netloc.lower()


def known_urls() -> dict[str, str]:
    """パス → 出典 CSV（最初に見つかったもの）。"""
    host = site_host()
    found: dict[str, str] = {}
    for csv_path in sorted(GSC_DIR.glob("*/pages.csv")):
        with csv_path.open(encoding="utf-8-sig", newline="") as f:
            reader = csv.reader(f)
            next(reader, None)  # 見出し行
            for row in reader:
                if not row or not row[0].startswith(("http://", "https://")):
                    continue
                u = urlparse(row[0].strip())
                if host and u.netloc.lower() != host:
                    continue
                found.setdefault(unquote(u.path) or "/", str(csv_path.relative_to(ROOT)))
    return found


def resolve(public: Path, path: str) -> Path:
    rel = path.lstrip("/")
    if not rel or rel.endswith("/"):
        return public / rel / "index.html"
    p = public / rel
    if p.suffix:
        return p
    return p / "index.html"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--public-dir", default=str(ROOT / "public_site"))
    args = ap.parse_args()
    public = Path(args.public_dir)
    if not public.is_dir():
        print(f"validate_known_urls: {public} がありません（スキップ）")
        return 0
    urls = known_urls()
    if not urls:
        print("validate_known_urls: reports/gsc/*/pages.csv がありません（スキップ）")
        return 0
    missing = [(p, src) for p, src in sorted(urls.items()) if not resolve(public, p).is_file()]
    if missing:
        print(f"validate_known_urls: 検索実績のある URL のうち {len(missing)} 件が 404 です:", file=sys.stderr)
        for p, src in missing[:50]:
            print(f"  {p}  （出典 {src}）", file=sys.stderr)
        if len(missing) > 50:
            print(f"  …ほか {len(missing) - 50} 件", file=sys.stderr)
        print(
            "記事の廃止・slug 変更なら data/guide_retired.json の redirects に転送先を登録してください。",
            file=sys.stderr,
        )
        return 1
    print(f"validate_known_urls: OK（検索実績のある {len(urls)} URL すべて公開物に存在）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
