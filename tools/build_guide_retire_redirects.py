#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""archived ガイド記事の articles/{slug}/ へ noindex リダイレクト HTML を書く。"""

from __future__ import annotations

import csv
import html
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.editorial_quality import norm  # noqa: E402

RETIRED_JSON = ROOT / "data" / "guide_retired.json"
SITE_CONFIG = ROOT / "site-config.json"


def site_origin() -> str:
    """site-config.json の siteOrigin（末尾スラッシュなし）。無ければ空文字（相対 URL にフォールバック）。"""
    if SITE_CONFIG.is_file():
        try:
            data = json.loads(SITE_CONFIG.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return ""
        return norm(data.get("siteOrigin")).rstrip("/")
    return ""

REDIRECT_HTML = """<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta http-equiv="refresh" content="0;url={url}">
<link rel="canonical" href="{url}">
<meta name="robots" content="noindex, follow">
<title>記事移動中…</title>
<script>location.replace({url_js});</script>
</head>
<body>
<p>新しい記事へ移動します。<a href="{url}">こちら</a></p>
</body>
</html>
"""


def load_retired_map() -> dict[str, str]:
    mapping: dict[str, str] = {}
    if RETIRED_JSON.is_file():
        data = json.loads(RETIRED_JSON.read_text(encoding="utf-8"))
        for slug, target in (data.get("redirects") or {}).items():
            mapping[norm(slug)] = norm(target)
    csv_path = ROOT / "data" / "guide_articles.csv"
    if csv_path.is_file():
        with csv_path.open(encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                if norm(row.get("content_status")) != "archived":
                    continue
                slug = norm(row.get("slug"))
                note = norm(row.get("original_note"))
                target = ""
                for part in note.split(";"):
                    if part.startswith("retire_redirect:"):
                        target = part.split(":", 1)[1].strip()
                        break
                if slug and target:
                    mapping.setdefault(slug, target)
    return mapping


def article_redirect_href(target: str, origin: str = "") -> str:
    """転送先 URL を組み立てる。

    origin（siteOrigin）があれば、転送先記事の canonical と同じ絶対 URL
    （https://…/articles/{slug}/）を返す。旧 slug が chapters/… のように
    階層を持つ場合も正しく解決でき、評価の引き継ぎ先が canonical と一致する。
    origin が無いときは articles/{slug}/index.html からの相対 URL。
    """
    t = norm(target)
    if t.startswith(("http://", "https://")):
        return t
    if origin and not t.startswith("../"):
        return f"{origin}/articles/{t.strip('/')}/"
    if t.startswith("../"):
        base = t.rstrip("/")
        if base.endswith(".html"):
            return base
        return f"{base}/index.html"
    slug = t.rstrip("/")
    return f"../{slug}/index.html"


def write_redirect(articles_dir: Path, slug: str, target_slug: str, origin: str = "") -> None:
    out_dir = articles_dir / slug
    out_dir.mkdir(parents=True, exist_ok=True)
    rel = article_redirect_href(target_slug, origin)
    esc = html.escape(rel, quote=True)
    (out_dir / "index.html").write_text(
        REDIRECT_HTML.format(url=esc, url_js=repr(rel)),
        encoding="utf-8",
    )
    marker = out_dir / ".generated-by-exam-site"
    if marker.is_file():
        marker.unlink()


def _is_published_slug(slug: str) -> bool:
    with (ROOT / "data" / "guide_articles.csv").open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            if norm(row.get("slug")) == slug and norm(row.get("content_status")) != "archived":
                return True
    return False


def main() -> int:
    mapping = load_retired_map()
    articles_dir = ROOT / "articles"
    articles_dir.mkdir(parents=True, exist_ok=True)
    origin = site_origin()
    count = 0
    for slug, target in sorted(mapping.items()):
        if not target:
            continue
        if (articles_dir / slug / ".generated-by-exam-site").is_file() or (
            ROOT / "data" / "guide_articles.csv"
        ).is_file() and _is_published_slug(slug):
            # 現行記事と同じ slug は上書きしない（転送表の誤登録対策）
            print(f"skip: articles/{slug}/ は現行記事のため転送しません")
            continue
        write_redirect(articles_dir, slug, target, origin)
        count += 1
    print(f"Wrote {count} retired guide redirect(s) under articles/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
