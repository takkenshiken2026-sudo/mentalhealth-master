#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""全種（II種ルート + 各新種）をビルドし public_site/ 配下に配置する。

手順:
  1) tools/build_all.py … II種（プライマリ種）を public_site/ ルートへ（従来どおり・無改変）。
     ※ prepare_public_site.sh が public_site を rm -rf するため必ず最初。
  2) 各副種を tools/build_grade.py で public_site/<basePath名>（self / master）へ。
  3) public_site/sitemap-index.xml を生成し、全種の sitemap.xml を参照。
  4) public_site/robots.txt の Sitemap 行を全種ぶんに書き換え。
  5) ルート CNAME を1本に統一（全種同一ホスト）。

ローカルで II種だけ素早く確認したいときは従来どおり `python3 tools/build_all.py`。
CI（本番公開）はこの build_site.py を使う。

使い方:
    python3 tools/build_site.py
"""

from __future__ import annotations

import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import build_grade  # noqa: E402
from tools.grades import load_grades, primary_grade, secondary_grades  # noqa: E402
from tools.site_config import clean_origin  # noqa: E402

PUBLIC = ROOT / "public_site"


def _sitemap_urls() -> list[str]:
    """全種の sitemap.xml の絶対URL。origin はプライマリ種（basePath 無し）。"""
    origin = clean_origin()
    urls: list[str] = []
    for g in load_grades():
        bp = g.base_path.strip("/")
        if bp:
            urls.append(f"{origin}/{bp}/sitemap.xml")
        else:
            urls.append(f"{origin}/sitemap.xml")
    return urls


def write_sitemap_index() -> None:
    today = date.today().isoformat()
    entries = "\n".join(
        f"  <sitemap>\n    <loc>{u}</loc>\n    <lastmod>{today}</lastmod>\n  </sitemap>"
        for u in _sitemap_urls()
    )
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{entries}\n"
        "</sitemapindex>\n"
    )
    (PUBLIC / "sitemap-index.xml").write_text(xml, encoding="utf-8")
    print(f"Wrote public_site/sitemap-index.xml（{len(_sitemap_urls())} サイトマップ参照）")


def rewrite_robots() -> None:
    """robots.txt の Sitemap 行を全種ぶん + 索引に置換。"""
    robots = PUBLIC / "robots.txt"
    origin = clean_origin()
    lines = ["User-agent: *", "Allow: /", ""]
    lines += [f"Sitemap: {u}" for u in _sitemap_urls()]
    lines.append(f"Sitemap: {origin}/sitemap-index.xml")
    robots.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("Rewrote public_site/robots.txt（全種サイトマップを掲載）")


def ensure_single_cname() -> None:
    """全種同一ホスト。副種配下の CNAME は不要なので削除（ルートの1本を正とする）。"""
    for g in secondary_grades():
        name = g.base_path.strip("/")
        nested = PUBLIC / name / "CNAME"
        if nested.is_file():
            nested.unlink()


def run(cmd: list[str]) -> None:
    print("+", " ".join(cmd))
    subprocess.run(cmd, cwd=ROOT, check=True)


def main() -> int:
    # 1) II種（prepare_public_site.sh が public_site を rm -rf するので最初に）。
    run([sys.executable, "tools/build_all.py"])

    if not (PUBLIC / "index.html").is_file():
        raise SystemExit("build_all.py の後に public_site/index.html がありません。")

    # 2) 各副種を public_site/<name> へ。
    for g in secondary_grades():
        build_grade.build(g.id)

    # 3-5) サイトマップ索引 / robots / CNAME 統一。
    write_sitemap_index()
    rewrite_robots()
    ensure_single_cname()

    grades = ", ".join(f"{g.short_label}({g.base_path or '/'})" for g in load_grades())
    print(f"build_site: 完了 — {grades}（primary: {primary_grade().short_label}）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
