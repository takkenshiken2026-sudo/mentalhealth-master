#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""廃止した用語解説セクション（terms/ 配下）の旧 URL に noindex リダイレクト HTML を置く。

用語解説ページ自体は削除済みだが、ブックマーク・検索エンジン・外部リンクからの
アクセスが 404 にならないよう、旧 URL ごとにトップページへのリダイレクト stub を生成する。
対象 URL は data/terms_retired_urls.txt（削除時に記録した一覧）。
生成物は noindex なので sitemap には載らない。
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
URL_LIST = ROOT / "data" / "terms_retired_urls.txt"
TERMS_DIR = ROOT / "terms"

# 旧用語 URL の統一リダイレクト先（サイトのトップ）。
TARGET = "/"

REDIRECT_HTML = """<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta http-equiv="refresh" content="0;url={url}">
<link rel="canonical" href="https://mentalhealth-master.jp{url}">
<meta name="robots" content="noindex, follow">
<title>メンタルヘルス二種マスターへ移動中…</title>
<script>location.replace({url_js});</script>
</head>
<body>
<p>このページは移動しました。<a href="{url}">トップページへ移動します</a>。</p>
</body>
</html>
"""


def build_all() -> int:
    # 旧用語 URL は II種（プライマリ）ルートにのみ存在した。副種（EXAM_SKELETON の
    # 骨組みビルド）は terms/ を持たないため、リダイレクト stub も生成しない。
    if os.environ.get("EXAM_SKELETON"):
        print("build_terms_retire_redirects: EXAM_SKELETON のためスキップ（副種に旧用語 URL なし）")
        return 0
    if not URL_LIST.is_file():
        print(f"build_terms_retire_redirects: {URL_LIST} がありません（スキップ）")
        return 0
    count = 0
    for line in URL_LIST.read_text(encoding="utf-8").splitlines():
        rel = line.strip()
        if not rel or not rel.endswith(".html"):
            continue
        if not rel.startswith("terms/"):
            continue
        out = ROOT / rel
        # 用語ページが再生成されていれば（通常は無い）上書きしない。
        if out.is_file():
            continue
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(
            REDIRECT_HTML.format(url=TARGET, url_js=repr(TARGET)),
            encoding="utf-8",
        )
        count += 1
    print(f"Wrote {count} terms retire redirect(s) under terms/ → {TARGET}")
    return 0


if __name__ == "__main__":
    raise SystemExit(build_all())
