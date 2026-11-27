#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PWA 対応を生成する。

- manifest.webmanifest（ホーム画面追加用のアプリ情報）を site-config から生成
- sw.js（Service Worker：オフライン学習用の安全なキャッシュ）を生成
- 全公開 HTML の <head> に manifest リンク・PWA メタ・SW 登録を冪等注入

設計方針（本番・収益化サイトとして安全側に倒す）:
- Service Worker は「同一オリジンの GET」だけを対象にする。
  広告(AdSense)・解析(GA)・フォント・Supabase など別オリジンには一切介入しない。
- HTML ナビゲーションは「ネットワーク優先・失敗時のみキャッシュ」。
  → オンライン時は常に最新を配信し、古い内容に固定されない。オフライン時だけ学習を継続できる。
- 静的アセット(CSS/JS/画像)は stale-while-revalidate（即表示＋裏で更新）。
- ただし site-config.js はネットワーク優先。HTML（最新）と設定（古い保存分）の版ずれで、
  新機能の設定が読めずに表示されない不具合を防ぐ（数KBなので毎回の確認でも負担は小さい）。
- キャッシュ名に公開物（CORE_PRECACHE）の内容のハッシュを含める。中身が変わった公開では sw.js も
  変わるため、ブラウザが新しい SW を入れ、古いキャッシュを破棄し、ページを1回だけ自動で再読み込みする。

build_all.py から inject_adsense_head の後に呼び出す（生成 HTML を含む全ページへ反映）。
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.site_config import (  # noqa: E402
    brand_logo_lines,
    brand_name,
    exam_name,
    theme,
)

# SW のキャッシュ世代。sw.js の中身や precache 対象を変えたら上げる。
# 実際のキャッシュ名は「世代＋公開物の内容ハッシュ」（core_content_hash）なので、内容の更新だけなら上げなくてよい。
PWA_CACHE_VERSION = "v7"

PWA_HEAD_MARKER_START = "<!--PWA_HEAD-->"
PWA_HEAD_MARKER_END = "<!--/PWA_HEAD-->"

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

# オフラインでも学習できるよう先読みする「アプリの殻」。
# 404 でも install を失敗させない（allSettled）ので、存在しないものがあっても安全。
CORE_PRECACHE = [
    "/",
    "/index.html",
    "/site-pages.css",
    "/site-theme.css",
    "/seo-editorial.css",
    "/site-q-index.js",
    "/site-config.js",
    "/exam-site-data-past.js",
    "/exam-site-data-practice.js",
    "/exam-site-data-ichimondou.js",
    "/assets/brand/icon-192.png",
]


def _short_name() -> str:
    name = brand_name()
    if len(name) <= 12:
        return name
    top, bottom = brand_logo_lines()
    cand = (bottom or top or name).strip()
    return cand[:12] if cand else name[:12]


def build_manifest() -> str:
    t = theme()
    accent = str(t.get("accent") or "#4a6b5c")
    bg = str(t.get("background") or "#ffffff")
    data = {
        "name": brand_name(),
        "short_name": _short_name(),
        "description": f"{exam_name()}の過去問・一問一答・実践演習を無料で学べる学習アプリ。",
        "lang": "ja",
        "dir": "ltr",
        "start_url": "/?utm_source=pwa",
        "scope": "/",
        "display": "standalone",
        "orientation": "portrait",
        "background_color": bg,
        "theme_color": accent,
        "categories": ["education"],
        "icons": [
            {"src": "/assets/brand/icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any"},
            {"src": "/assets/brand/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any"},
            {"src": "/assets/brand/apple-touch-icon.png", "sizes": "180x180", "type": "image/png"},
        ],
    }
    return json.dumps(data, ensure_ascii=False, indent=2) + "\n"


def core_content_hash() -> str:
    """CORE_PRECACHE の公開物（ルート直下のファイル）の内容から短いハッシュを作る。"""
    h = hashlib.sha256()
    seen: set[str] = set()
    for url in CORE_PRECACHE:
        rel = "index.html" if url == "/" else url.lstrip("/")
        if rel in seen:
            continue
        seen.add(rel)
        path = ROOT / rel
        h.update(rel.encode("utf-8") + b"\0")
        if path.is_file():
            h.update(path.read_bytes())
        h.update(b"\0")
    return h.hexdigest()[:10]


def build_service_worker(content_hash: str = "") -> str:
    cache = f"mhm-pwa-{PWA_CACHE_VERSION}" + (f"-{content_hash}" if content_hash else "")
    core = json.dumps(CORE_PRECACHE, ensure_ascii=False)
    return f"""/* Service Worker（自動生成: tools/build_pwa.py）
 * 方針: 同一オリジンGETのみ対象。HTMLはネットワーク優先、静的はSWR。
 * 別オリジン(広告/解析/フォント/Supabase)には介入しない。
 */
const CACHE = '{cache}';
const CORE = {core};

self.addEventListener('install', (event) => {{
  self.skipWaiting();
  event.waitUntil((async () => {{
    const c = await caches.open(CACHE);
    // 1件でも失敗してinstallを止めないよう個別に追加する
    await Promise.allSettled(CORE.map((u) => c.add(new Request(u, {{ cache: 'reload' }}))));
  }})());
}});

self.addEventListener('activate', (event) => {{
  event.waitUntil((async () => {{
    const keys = await caches.keys();
    await Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)));
    await self.clients.claim();
  }})());
}});

self.addEventListener('fetch', (event) => {{
  const req = event.request;
  if (req.method !== 'GET') return;
  let url;
  try {{ url = new URL(req.url); }} catch (e) {{ return; }}
  // 同一オリジンのみ介入（広告・解析・フォント・外部APIはネットワークに委ねる）
  if (url.origin !== self.location.origin) return;

  // HTMLナビゲーション: ネットワーク優先・失敗時のみキャッシュ（古い内容に固定しない）
  if (req.mode === 'navigate') {{
    event.respondWith((async () => {{
      try {{
        const net = await fetch(req);
        try {{ const c = await caches.open(CACHE); c.put(req, net.clone()); }} catch (e) {{}}
        return net;
      }} catch (e) {{
        const cached = (await caches.match(req)) || (await caches.match('/index.html')) || (await caches.match('/'));
        return cached || Response.error();
      }}
    }})());
    return;
  }}

  // 設定ファイル: ネットワーク優先（HTMLとの版ずれ防止）・失敗時のみキャッシュ
  if (/\\/site-config\\.js$/.test(url.pathname)) {{
    event.respondWith((async () => {{
      try {{
        const net = await fetch(req, {{ cache: 'no-cache' }});
        if (net && net.status === 200) {{
          try {{ const c = await caches.open(CACHE); c.put(req, net.clone()); }} catch (e) {{}}
        }}
        return net;
      }} catch (e) {{
        return (await caches.match(req)) || Response.error();
      }}
    }})());
    return;
  }}

  // 静的アセット: stale-while-revalidate（即表示＋裏で更新）
  event.respondWith((async () => {{
    const cached = await caches.match(req);
    const fetchP = fetch(req).then((net) => {{
      if (net && net.status === 200 && net.type === 'basic') {{
        caches.open(CACHE).then((c) => c.put(req, net.clone())).catch(() => {{}});
      }}
      return net;
    }}).catch(() => null);
    return cached || (await fetchP) || Response.error();
  }})());
}});
"""


def pwa_head_snippet() -> str:
    short = _short_name()
    # HTML 属性として安全な短縮名（英数・日本語のみ想定だが念のためエスケープ）
    import html as _html

    short_attr = _html.escape(short, quote=True)
    return (
        f"{PWA_HEAD_MARKER_START}\n"
        '<link rel="manifest" href="/manifest.webmanifest">\n'
        '<meta name="mobile-web-app-capable" content="yes">\n'
        '<meta name="apple-mobile-web-app-capable" content="yes">\n'
        '<meta name="apple-mobile-web-app-status-bar-style" content="default">\n'
        f'<meta name="apple-mobile-web-app-title" content="{short_attr}">\n'
        '<link rel="apple-touch-icon" sizes="192x192" href="/assets/brand/icon-192.png">\n'
        # 既存の SW が制御していた画面（古いキャッシュで表示中）だけ、新しい SW に
        # 切り替わった時点で1回だけ再読み込みし、最新の問題データを表示する。
        # 初回訪問（制御なし）では再読み込みしない。
        "<script>if('serviceWorker' in navigator){"
        "var _swHad=!!navigator.serviceWorker.controller,_swReloaded=false;"
        "navigator.serviceWorker.addEventListener('controllerchange',function(){"
        "if(!_swHad||_swReloaded)return;_swReloaded=true;window.location.reload();});"
        "window.addEventListener('load',function(){"
        "navigator.serviceWorker.register('/sw.js').catch(function(){});});}</script>\n"
        f"{PWA_HEAD_MARKER_END}"
    )


def _strip_pwa_block(text: str) -> str:
    import re

    pattern = re.compile(
        rf"{re.escape(PWA_HEAD_MARKER_START)}[\s\S]*?{re.escape(PWA_HEAD_MARKER_END)}\s*"
    )
    return pattern.sub("", text)


def inject_pwa_head(html_text: str) -> str:
    """<head> 内に PWA タグを冪等注入する。"""
    text = _strip_pwa_block(html_text)
    if "</head>" not in text:
        return text
    return text.replace("</head>", f"{pwa_head_snippet()}\n</head>", 1)


def iter_html_files(root: Path) -> list[Path]:
    out: list[Path] = []
    for path in root.rglob("*.html"):
        if any(part in SKIP_DIRS for part in path.relative_to(root).parts):
            continue
        out.append(path)
    return sorted(out)


def main() -> int:
    # 1) 全 HTML の <head> に PWA タグを注入
    updated = 0
    for path in iter_html_files(ROOT):
        old = path.read_text(encoding="utf-8")
        new = inject_pwa_head(old)
        if new != old:
            path.write_text(new, encoding="utf-8")
            updated += 1

    # 2) manifest / sw.js を生成（キャッシュ名は注入後の公開物の内容から決める）
    (ROOT / "manifest.webmanifest").write_text(build_manifest(), encoding="utf-8")
    content_hash = core_content_hash()
    (ROOT / "sw.js").write_text(build_service_worker(content_hash), encoding="utf-8")
    print(
        f"build_pwa: manifest.webmanifest / sw.js を生成（キャッシュ mhm-pwa-{PWA_CACHE_VERSION}-{content_hash}）、"
        f"{updated} ページに PWA タグを注入"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
