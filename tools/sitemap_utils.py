#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""サイト全体の sitemap URL 収集（canonical は *.html 形式で統一）。"""

from __future__ import annotations

from pathlib import Path
from xml.sax.saxutils import escape as xml_escape

ROOT = Path(__file__).resolve().parents[1]
TERMS_DIR = ROOT / "terms"
ARTICLES_DIR = ROOT / "articles"
Q_DIR = ROOT / "q"

STATIC_PAGES = (
    "index.html",
    "about.html",
    "privacy.html",
    "related-sites.html",
)


def public_url(base: str, rel_path: str) -> str:
    return f"{base.rstrip('/')}/{rel_path.lstrip('/')}"


def collect_sitemap_urls(base: str) -> list[str]:
    urls: list[str] = [public_url(base, "/")]

    for name in STATIC_PAGES:
        p = ROOT / name
        if p.is_file():
            urls.append(public_url(base, name))

    if ARTICLES_DIR.is_dir():
        for p in sorted(ARTICLES_DIR.rglob("index.html")):
            rel = p.relative_to(ROOT).as_posix()
            urls.append(public_url(base, rel))

    if Q_DIR.is_dir():
        for p in sorted(Q_DIR.rglob("index.html")):
            rel = p.relative_to(ROOT).as_posix()
            urls.append(public_url(base, rel))

    if (TERMS_DIR / "index.html").is_file():
        urls.append(public_url(base, "terms/index.html"))

    for p in sorted(TERMS_DIR.glob("g-*.html")):
        urls.append(public_url(base, p.relative_to(ROOT).as_posix()))

    for p in sorted(TERMS_DIR.iterdir()):
        if p.is_dir() and (p / "index.html").is_file():
            rel = (p / "index.html").relative_to(ROOT).as_posix()
            urls.append(public_url(base, rel))

    return urls


def write_sitemap(urls: list[str], out: Path) -> None:
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for u in sorted(set(urls)):
        lines.append("  <url>")
        lines.append(f"    <loc>{xml_escape(u)}</loc>")
        lines.append("    <changefreq>monthly</changefreq>")
        lines.append("  </url>")
    lines.append("</urlset>")
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
