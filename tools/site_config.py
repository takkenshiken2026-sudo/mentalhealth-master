# -*- coding: utf-8 -*-
"""Central site configuration helpers for the exam-site template."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "site-config.json"


def load_config() -> dict[str, Any]:
    if not CONFIG_PATH.is_file():
        raise FileNotFoundError(f"site-config.json が見つかりません: {CONFIG_PATH}")
    cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    if not isinstance(cfg, dict):
        raise ValueError("site-config.json は JSON object にしてください")
    return cfg


CONFIG = load_config()


def clean_origin() -> str:
    return str(CONFIG.get("siteOrigin") or "").rstrip("/")


def brand_name() -> str:
    return str(CONFIG.get("brandName") or "Sampleマスター")


def brand_mark() -> str:
    return str(CONFIG.get("brandMark") or brand_name()[:1] or "S")


def exam_name() -> str:
    return str(CONFIG.get("examName") or "◯◯試験")


def contact_url() -> str:
    return str(CONFIG.get("contactUrl") or "#")


def ga4_measurement_id() -> str:
    return str(CONFIG.get("ga4MeasurementId") or "").strip()


def copyright_text() -> str:
    configured = str(CONFIG.get("copyright") or "").strip()
    if configured:
        return configured
    host = clean_origin().replace("https://", "").replace("http://", "").strip("/")
    suffix = f"・{host}" if host else ""
    return f"© 2026 {brand_name()}学習支援{suffix}"


def footer_disclaimer() -> str:
    return str(CONFIG.get("footerDisclaimer") or "")


def official_organization() -> str:
    return str(CONFIG.get("officialOrganization") or "試験実施団体")


def external_links() -> list[dict[str, str]]:
    raw = CONFIG.get("externalLinks") or []
    if not isinstance(raw, list):
        return []
    out: list[dict[str, str]] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        url = str(item.get("url") or "").strip()
        label = str(item.get("label") or "").strip()
        if url and label:
            out.append(
                {
                    "url": url,
                    "label": label,
                    "description": str(item.get("description") or "").strip(),
                }
            )
    return out


def primary_external_link() -> dict[str, str]:
    links = external_links()
    if links:
        return links[0]
    return {
        "url": "https://example.com/",
        "label": official_organization(),
        "description": "試験日程・要項・合格発表などの公式情報を確認してください。",
    }


DEFAULT_HEADER_NAV = [
    {"label": "トップ", "href": "index.html", "key": "top"},
    {"label": "このサイトについて", "href": "about.html", "key": "about"},
    {"label": "過去問一覧", "href": "q/index.html", "key": "q"},
    {"label": "用語集", "href": "terms/index.html", "key": "terms"},
    {"label": "試験ガイド", "href": "articles/index.html", "key": "articles"},
    {"label": "関連リンク", "href": "related-sites.html", "key": "related"},
    {"label": "プライバシー", "href": "privacy.html", "key": "privacy"},
]

DEFAULT_FOOTER_NAV = [
    *DEFAULT_HEADER_NAV,
    {"label": "お問い合わせ", "href": "__CONTACT__", "key": "contact"},
]


def navigation_items(section: str) -> list[tuple[str, str, str]]:
    nav = CONFIG.get("navigation") or {}
    raw = nav.get(section) if isinstance(nav, dict) else None
    if not isinstance(raw, list) or not raw:
        raw = DEFAULT_FOOTER_NAV if section == "footer" else DEFAULT_HEADER_NAV
    out: list[tuple[str, str, str]] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        label = str(item.get("label") or "").strip()
        href = str(item.get("href") or "").strip()
        key = str(item.get("key") or "").strip()
        if href == "__CONTACT__":
            href = contact_url()
        if label and href:
            out.append((label, href, key or label))
    return out


def theme() -> dict[str, str]:
    raw = CONFIG.get("theme") or {}
    if not isinstance(raw, dict):
        raw = {}
    defaults = {
        "accent": "#333333",
        "accentText": "#ffffff",
        "background": "#f0f0f1",
        "surface": "#ffffff",
        "surfaceAlt": "#f4f4f5",
        "text": "#111111",
        "textMuted": "#555555",
        "border": "rgba(0, 0, 0, 0.09)",
        "radius": "10px",
        "navWidth": "1080px",
        "contentWidth": "1080px",
    }
    return {k: str(raw.get(k) or v) for k, v in defaults.items()}


def write_site_theme_css() -> None:
    t = theme()
    css = f""":root {{
  --ink: {t["accent"]};
  --sel: {t["accent"]};
  --accent: {t["accent"]};
  --accent-text: {t["accentText"]};
  --bg: {t["surface"]};
  --bg2: {t["surfaceAlt"]};
  --page-bg: {t["background"]};
  --text: {t["text"]};
  --text2: {t["textMuted"]};
  --border: {t["border"]};
  --r2: {t["radius"]};
  --site-nav-w: {t["navWidth"]};
  --site-content-w: {t["contentWidth"]};
  --site-readable-w: min(860px, {t["contentWidth"]});
}}
body {{
  background: var(--page-bg);
}}
.site-page-mark,
.terms-idx-chip.on,
.gcat-btn.active {{
  background: var(--accent);
  color: var(--accent-text);
}}
"""
    (ROOT / "site-theme.css").write_text(css, encoding="utf-8")


def fields() -> list[dict[str, Any]]:
    out = CONFIG.get("fields") or []
    if not isinstance(out, list) or not out:
        raise ValueError("site-config.json の fields は1件以上の配列にしてください")
    return out


def field_ids() -> list[str]:
    return [str(f["id"]) for f in fields()]


def field_labels() -> dict[str, str]:
    return {str(f["id"]): str(f.get("name") or f["id"]) for f in fields()}


def category_to_field_map() -> dict[str, str]:
    mapping: dict[str, str] = {}
    for f in fields():
        fid = str(f["id"])
        names = [f.get("name"), *(f.get("aliases") or [])]
        for name in names:
            if name:
                mapping[str(name)] = fid
    return mapping


def category_order() -> list[str]:
    out: list[str] = []
    for f in fields():
        for name in [f.get("name"), *(f.get("aliases") or [])]:
            if name and str(name) not in out:
                out.append(str(name))
    return out


def legacy_glossary_cat(category: str) -> str:
    fid = category_to_field_map().get(category)
    if not fid:
        return "limit"
    for f in fields():
        if str(f["id"]) == fid:
            return str(f.get("legacyGlossaryCat") or fid)
    return fid


def css_safe_field_id(field_id: str) -> str:
    safe = re.sub(r"[^a-zA-Z0-9_-]+", "-", field_id).strip("-")
    return safe or "field"


def public_url(rel_path: str) -> str:
    return f"{clean_origin()}/{rel_path.lstrip('/')}"


def write_site_config_js() -> None:
    payload = {
        "brandName": brand_name(),
        "brandMark": brand_mark(),
        "examName": exam_name(),
        "siteOrigin": clean_origin(),
        "contactUrl": contact_url(),
        "ga4MeasurementId": ga4_measurement_id(),
        "theme": theme(),
        "navigation": {
            "header": [
                {"label": label, "href": href, "key": key}
                for label, href, key in navigation_items("header")
            ],
            "footer": [
                {"label": label, "href": href, "key": key}
                for label, href, key in navigation_items("footer")
            ],
        },
        "fields": [
            {
                "id": str(f["id"]),
                "name": str(f.get("name") or f["id"]),
                "aliases": [str(a) for a in (f.get("aliases") or [])],
                "legacyGlossaryCat": str(f.get("legacyGlossaryCat") or f["id"]),
            }
            for f in fields()
        ],
    }
    (ROOT / "site-config.js").write_text(
        "window.SITE_CONFIG = "
        + json.dumps(payload, ensure_ascii=False, indent=2)
        + ";\n",
        encoding="utf-8",
    )


def write_crawler_files() -> None:
    origin = clean_origin()
    host = origin.replace("https://", "").replace("http://", "").strip("/")
    (ROOT / "CNAME").write_text(host + "\n", encoding="utf-8")
    (ROOT / "robots.txt").write_text(
        "User-agent: *\n"
        "Allow: /\n\n"
        f"Sitemap: {origin}/sitemap.xml\n",
        encoding="utf-8",
    )


def sync_config_files() -> None:
    write_site_config_js()
    write_site_theme_css()
    write_crawler_files()


if __name__ == "__main__":
    sync_config_files()
    print("Synced site-config.js, CNAME, robots.txt from site-config.json")
