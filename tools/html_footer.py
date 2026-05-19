# -*- coding: utf-8 -*-
"""静的 HTML 用フッター（相対パス付き）と GA4 共通タグ。

- 測定IDを変えるときは GA4_MEASUREMENT_ID と site-analytics.js 内の DEFAULT_MID を揃える。
- 新規の手書き HTML では </body> 直前に analytics_snippet(Path('相対パス')) と同等の2行を置くか、
  生成ページでは site_page_footer の直後に analytics が付くので head に GA を書かない。
"""

from __future__ import annotations

import html
from pathlib import Path

from tools.site_config import (
    brand_mark,
    brand_name,
    contact_url,
    copyright_text,
    exam_name,
    footer_disclaimer,
    ga4_measurement_id,
    navigation_items,
)

FORM_URL = contact_url()

# GA4 測定ID（site-analytics.js の DEFAULT_MID と揃えること）
GA4_MEASUREMENT_ID = ga4_measurement_id()

# フッター注記・著作権（共通フッター・静的ガイドの表記揃え）
FOOTER_DISCLAIMER = footer_disclaimer()
SITE_COPYRIGHT = copyright_text()

# 静的ページ・生成 HTML 共通（Search Console / クローラ向け）
ROBOTS_INDEX_FOLLOW = '<meta name="robots" content="index, follow">'

SITE_HEADER_NAV = navigation_items("header")
SITE_FOOTER_NAV = navigation_items("footer")


def footer_href(rel_path: Path, site_rel: str) -> str:
    """rel_path: ROOT からの相対パス（例 q/past/y2025/q01/index.html）。site_rel: index.html / q/index.html 等。"""
    site_rel = site_rel.lstrip("/")
    parent = rel_path.parent
    parts = parent.parts
    if parent.as_posix() == "q" and site_rel == "q/index.html":
        return "index.html"
    if site_rel == "terms/index.html" and parts and parts[0] == "terms":
        return "index.html"
    if len(parts) >= 3 and parts[0] == "q" and parts[1] == "past" and site_rel == "q/index.html":
        prefix = "/".join([".."] * (len(parts) - 1))
        return prefix + "/index.html"
    up = len(parts)
    if len(parts) >= 3 and parts[0] == "q" and parts[1] == "past" and site_rel.startswith("q/") and site_rel.count("/") == 1:
        up = len(parts) - 1
    prefix = "/".join([".."] * up)
    if not prefix:
        return site_rel
    return prefix + "/" + site_rel


def analytics_snippet(rel_path: Path) -> str:
    """全静的ページ共通: フッター直後（</body> 直前想定）に置く GA4 タグ。相対パスで site-analytics.js を読む。"""
    src = html.escape(footer_href(rel_path, "site-analytics.js"))
    mid = html.escape(GA4_MEASUREMENT_ID)
    return (
        "<!-- GA4: tools/html_footer.analytics_snippet（測定IDは GA4_MEASUREMENT_ID） -->\n"
        f'<script>window.__GA4_MEASUREMENT_ID__="{mid}";</script>\n'
        f'<script defer src="{src}"></script>'
    )


def _breadcrumb_ol(rel_path: Path, items: list[tuple[str, str | None]]) -> str:
    lis: list[str] = []
    for text, href in items:
        if href:
            h = footer_href(rel_path, href) if not href.startswith("http") else href
            lis.append(f'<li><a href="{html.escape(h)}">{html.escape(text)}</a></li>')
        else:
            lis.append(f'<li aria-current="page">{html.escape(text)}</li>')
    crumbs = "\n        ".join(lis)
    return f"""<nav class="site-page-header-crumb" aria-label="パンくず">
      <ol class="q-breadcrumb">
        {crumbs}
      </ol>
    </nav>"""


def site_page_header(
    rel_path: Path,
    *,
    current: str | None = None,
    breadcrumb_items: list[tuple[str, str | None]] | None = None,
    wide: bool = False,
) -> str:
    """トップ（index.html）・about と同型の site-page ヘッダー（任意でパンくず付き）。"""
    root = html.escape(footer_href(rel_path, "index.html"))
    nav_links: list[str] = []
    for label, dest, key in SITE_HEADER_NAV:
        if dest.startswith("http"):
            href = dest
            nav_links.append(
                f'<a href="{html.escape(href)}" target="_blank" rel="noopener noreferrer">{html.escape(label)}</a>'
            )
        else:
            href = footer_href(rel_path, dest)
            cur = ' aria-current="page"' if current == key else ""
            nav_links.append(f'<a href="{html.escape(href)}"{cur}>{html.escape(label)}</a>')
    nav_html = "\n          ".join(nav_links)
    header_class = "site-page-header site-page-header--wide" if wide else "site-page-header"
    return f"""<header class="{header_class}">
      <div class="site-page-header-inner">
        <a class="site-page-brand" href="{root}">
          <span class="site-page-mark" title="サービス略称（差し替え）">{html.escape(brand_mark())}</span>
          <span class="site-page-brand-text">
            <span class="site-page-brand-name">{html.escape(brand_name())}</span>
            <span class="site-page-brand-sub">{html.escape(exam_name())}</span>
          </span>
        </a>
        <nav class="site-page-nav" aria-label="サイト内ナビゲーション">
          {nav_html}
        </nav>
      </div>
    </header>"""


def site_page_footer(rel_path: Path, *, current: str | None = None, wide: bool = False) -> str:
    """トップ（index.html）・about と同型の site-page フッター + GA4。"""
    links: list[str] = []
    for label, dest, key in SITE_FOOTER_NAV:
        if dest.startswith("http"):
            href = dest
            links.append(
                f'<a href="{html.escape(href)}" target="_blank" rel="noopener noreferrer">{html.escape(label)}</a>'
            )
        else:
            href = footer_href(rel_path, dest)
            links.append(f'<a href="{html.escape(href)}">{html.escape(label)}</a>')
    links_html = "\n          ".join(links)
    footer_class = "site-page-footer site-page-footer--wide" if wide else "site-page-footer"
    return f"""<footer class="{footer_class}">
      <div class="site-page-footer-inner">
        <div class="site-page-footer-links">
          {links_html}
        </div>
        <span class="site-page-footer-sep" aria-hidden="true"></span>
        <span class="site-page-footer-copy">{html.escape(SITE_COPYRIGHT)}</span>
      </div>
    </footer>
{analytics_snippet(rel_path)}"""


def site_page_wrap_open() -> str:
    return '<div class="site-page-wrap">'


def site_page_wrap_close() -> str:
    return "</div>"


def breadcrumb_html(rel_path: Path, items: list[tuple[str, str | None]]) -> str:
    """後方互換。新規は site_page_header(..., breadcrumb_items=...) を使用。"""
    return _breadcrumb_ol(rel_path, items)


def static_site_header(*, root_href: str, breadcrumb_items: list[tuple[str, str | None]]) -> str:
    """過去問など従来の q-static ヘッダー（パンくず付き）。"""
    lis: list[str] = []
    for text, href in breadcrumb_items:
        if href:
            lis.append(f'<li><a href="{html.escape(href)}">{html.escape(text)}</a></li>')
        else:
            lis.append(f'<li aria-current="page">{html.escape(text)}</li>')
    crumbs = "\n      ".join(lis)
    return f"""<header class="q-static-header">
  <p class="q-static-brand"><a href="{html.escape(root_href)}">{html.escape(brand_name())}</a>（{html.escape(exam_name())}）</p>
  <nav aria-label="パンくず">
    <ol class="q-breadcrumb">
      {crumbs}
    </ol>
  </nav>
</header>"""


def static_footer_block(rel_path: Path) -> str:
    """過去問など従来の q-static フッター + GA4。"""
    def h(dest: str) -> str:
        return html.escape(footer_href(rel_path, dest))

    return f"""<footer class="q-static-footer">
  <nav class="q-static-footer-nav" aria-label="サイトの他ページ">
    <a href="{h("index.html")}">トップ</a>
    <a href="{h("about.html")}">このサイトについて</a>
    <a href="{h("q/index.html")}">過去問一覧</a>
    <a href="{h("terms/index.html")}">用語集</a>
    <a href="{h("articles/index.html")}">試験ガイド</a>
    <a href="{h("related-sites.html")}">関連リンク</a>
    <a href="{h("privacy.html")}">プライバシー</a>
    <a href="{html.escape(FORM_URL)}" target="_blank" rel="noopener noreferrer">お問い合わせ</a>
  </nav>
  <p><small>{html.escape(FOOTER_DISCLAIMER)}</small></p>
  <p><small>{html.escape(SITE_COPYRIGHT)}</small></p>
</footer>
{analytics_snippet(rel_path)}"""
