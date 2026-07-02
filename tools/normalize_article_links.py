#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Normalize internal links that point to article detail pages to the
canonical directory form (articles/{slug}/ instead of articles/{slug}/index.html).

Article detail pages canonicalize to the trailing-slash URL, but many internal
links (and retire-redirect stub targets) still reference the .../index.html form.
That split signal makes Google index both URLs and dilutes ranking. This step
runs at the end of build_all so every emitted HTML agrees with the canonical.

Only article-detail targets are touched. Home / terms / q / glossary links and
non-index .html files are left unchanged.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# href / meta refresh url / JS location.replace that end in .../index.html
_PATTERNS = [
    re.compile(r'(href=")([^"]+?)(")'),
    re.compile(r'(content="\d+;\s*url=)([^"]+?)(")'),
    re.compile(r"(location\.replace\(')([^']+?)('\))"),
]
_INDEX_RE = re.compile(r'index\.html(?=[#?]|$)')


def _resolves_to_article_detail(html_path: Path, url: str) -> bool:
    """True if url (relative to html_path's dir) resolves to articles/<slug>/index.html."""
    if url.startswith(("http://", "https://", "//", "mailto:", "tel:", "#")):
        # absolute same-origin URLs handled separately below
        pass
    core = url.split("#", 1)[0].split("?", 1)[0]
    if not core.endswith("index.html"):
        return False
    if core.startswith(("http://", "https://")):
        # https://mentalhealth-master.jp/articles/<slug>/index.html
        m = re.search(r"//[^/]+/(.*)$", core)
        rel = m.group(1) if m else ""
    elif core.startswith("/"):
        rel = core.lstrip("/")
    else:
        base = html_path.parent
        try:
            rel = (base / core).resolve().relative_to(ROOT).as_posix()
        except ValueError:
            # link resolves outside the site root; leave it untouched
            return False
    return bool(re.fullmatch(r"articles/[^/]+/index\.html", rel))


def _rewrite_url(url: str) -> str:
    return _INDEX_RE.sub("", url, count=1)


def normalize_text(html_path: Path, text: str) -> tuple[str, int]:
    count = 0

    def repl(m: re.Match) -> str:
        nonlocal count
        pre, url, post = m.group(1), m.group(2), m.group(3)
        if _resolves_to_article_detail(html_path, url):
            new = _rewrite_url(url)
            if new != url:
                count += 1
                return f"{pre}{new}{post}"
        return m.group(0)

    for pat in _PATTERNS:
        text = pat.sub(repl, text)
    return text, count


def main() -> int:
    import sys
    apply = "--apply" in sys.argv
    total_links = files_changed = 0
    for path in ROOT.rglob("*.html"):
        if "public_site" in path.parts:
            continue
        text = path.read_text(encoding="utf-8")
        new, n = normalize_text(path, text)
        if n:
            total_links += n
            files_changed += 1
            if apply:
                path.write_text(new, encoding="utf-8")
    tag = "APPLIED" if apply else "DRY-RUN"
    print(f"{tag}: article-detail links normalized={total_links} files={files_changed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
