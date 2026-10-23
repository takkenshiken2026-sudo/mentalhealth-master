#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""新種（grade）サイトを staging ビルドして public_site/<grade> に配置する。

背景: 既存ビルドツールは出力先を ROOT=Path(__file__).resolve().parents[1]
（= リポジトリルート）に固定するため、EXAM_SITE_ROOT や cwd を変えても出力先は
ルートのまま。II種を壊さず新種を生成する唯一の安全手段は、ツール一式を含む
リポジトリを使い捨てディレクトリへ丸ごとコピーし（parents[1] がその stage を指す）、
grade の site-config.json + data を上書きして build_all.py を回すこと。

手順:
  1) リポジトリを stage へ copytree（.git / public_site / grades / .github 等は除外）
  2) II種の生成物を stage から掃除（q / terms / 生成JS / ルート生成ファイル）
  3) grade の site-config.json と data/ を上書き
  4) rekey_grade で手書き本文のII種固有語を grade へ置換
  5) EXAM_SITE_ROOT=stage, EXAM_SKELETON=1 で build_all.py を実行
  6) stage/public_site を repo/public_site/<basePath名> へコピー

使い方:
    python3 tools/build_grade.py self
    python3 tools/build_grade.py master
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.grades import Grade, get_grade, secondary_grades  # noqa: E402
from tools.rekey_grade import rekey_stage  # noqa: E402

# stage へコピーしないもの（巨大・無関係・種別管理外）。
COPY_IGNORE = shutil.ignore_patterns(
    ".git",
    "public_site",
    "grades",
    ".github",
    "node_modules",
    "__pycache__",
    "*.pyc",
    ".pytest_cache",
    ".mypy_cache",
)

# 掃除する生成ツリー（build_all が種データから作り直す / 空ならシェルのみ）。
# articles はII種記事に生成マーカーが無く build_article_pages のクリーンが効かないため丸ごと除去
# （build_article_pages が articles/index.html を空で再生成する）。
PURGE_DIRS = ("q", "terms", "articles", "exam-dates")

# 掃除する生成JS。exam-site-data-* は build_all が再生成。
# eisei1-*/eisei2-* は現行SPA(index.html)が参照しないII種レガシーデータなので除去（リーク防止）。
PURGE_GLOBS = ("exam-site-data-*.js", "eisei1-*.js", "eisei2-*.js")

# 掃除するルート生成ファイル（config/テーマ/クローラ/サイトマップ）。build_all が種設定から再生成。
PURGE_FILES = ("sitemap.xml", "site-config.js", "site-theme.css", "CNAME", "robots.txt", "ads.txt")


def _purge_stage(site: Path) -> None:
    for d in PURGE_DIRS:
        p = site / d
        if p.is_dir():
            shutil.rmtree(p)
    for pattern in PURGE_GLOBS:
        for p in site.glob(pattern):
            p.unlink()
    for f in PURGE_FILES:
        p = site / f
        if p.is_file():
            p.unlink()


# II種 index.html に焼き込まれた「試験日検索」ナビ（exam-dates）。新種は exam-dates を
# 持たない（config に learningNavExtras なし・ページ未生成）ため staged index から除去する。
_EXAM_DATES_NAV_RE = re.compile(
    r'\s*<a class="(?:topnav-link|mobile-nav-item)" id="[tm]nav-exam-dates".*?</a>',
    re.S,
)


def _strip_exam_dates_nav(site: Path) -> None:
    index = site / "index.html"
    if not index.is_file():
        return
    text = index.read_text(encoding="utf-8")
    new = _EXAM_DATES_NAV_RE.sub("", text)
    if new != text:
        index.write_text(new, encoding="utf-8")


# II種 index.html の SPA 学習ナビに焼き込まれた「用語解説」(tnav-glossary / mnav-glossary)。
# navigation に terms を持たない種（用語解説を出さない種）では staged index から除去する。
# articles（試験ガイド）は SPA トップナビに無く footer（navigation.footer 駆動）のみのため、
# config から外せば連動して消える。
_GLOSSARY_NAV_RE = re.compile(
    r'\s*<a class="(?:topnav-link|mobile-nav-item)" id="[tm]nav-glossary".*?</a>',
    re.S,
)


def _nav_keys(site: Path, section: str) -> set[str]:
    try:
        cfg = json.loads((site / "site-config.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return set()
    return {e.get("key") for e in (cfg.get("navigation", {}).get(section) or [])}


def _strip_absent_section_nav(site: Path) -> None:
    """navigation に無いセクション（用語解説=terms / 試験ガイド=articles）の、
    SPA index.html に焼き込まれたナビ・リンクを除去する。

    静的ヘッダー/メインフッターは navigation 駆動なので config から外せば消えるが、
    SPA トップナビの用語解説(tnav/mnav-glossary)と、SPA 二次フッターの関連ページ行
    （「… ・ 用語集 ・ 試験ガイド ・ …」）は index.html に焼き込まれているため個別に除去する。
    """
    index = site / "index.html"
    if not index.is_file():
        return
    present = _nav_keys(site, "header") | _nav_keys(site, "footer")
    absent = [k for k in ("terms", "articles") if k not in present]
    if not absent:
        return
    text = index.read_text(encoding="utf-8")
    orig = text
    if "terms" in absent:
        text = _GLOSSARY_NAV_RE.sub("", text)  # SPA トップナビ/モバイルナビの用語解説
    # 二次フッターの関連ページ行から、該当セクションのアンカーを先頭の区切り（ ・ ）ごと除去。
    for key in absent:
        text = re.sub(
            rf'\s*・\s*<a[^>]*href="[^"]*{key}/index[^"]*"[^>]*>.*?</a>',
            "",
            text,
            flags=re.S,
        )
    if text != orig:
        index.write_text(text, encoding="utf-8")


def _overlay_grade(site: Path, grade: Grade) -> None:
    shutil.copy2(grade.config_path, site / "site-config.json")
    data_dst = site / "data"
    if data_dst.is_dir():
        shutil.rmtree(data_dst)
    shutil.copytree(grade.data_dir, data_dst)


def build(grade_id: str, *, keep_stage: bool = False) -> Path:
    grade = get_grade(grade_id)
    if grade.primary:
        raise SystemExit(f"'{grade_id}' はプライマリ種（ルート運用）です。build_all.py を使ってください。")
    name = grade.base_path.lstrip("/")
    if not name:
        raise SystemExit(f"'{grade_id}' に basePath がありません（grades.json を確認）。")

    stage_root = Path(tempfile.mkdtemp(prefix=f"gradebuild-{grade_id}-"))
    site = stage_root / "site"
    try:
        print(f"[{grade_id}] stage: {site}")
        shutil.copytree(REPO_ROOT, site, ignore=COPY_IGNORE, symlinks=False)
        _purge_stage(site)
        _overlay_grade(site, grade)
        rekey_stage(grade_id, site)
        _strip_exam_dates_nav(site)
        _strip_absent_section_nav(site)

        env = {**os.environ, "EXAM_SITE_ROOT": str(site), "EXAM_SKELETON": "1"}
        subprocess.run([sys.executable, "tools/build_all.py"], cwd=site, check=True, env=env)

        src_out = site / "public_site"
        if not src_out.is_dir():
            raise SystemExit(f"[{grade_id}] stage に public_site が生成されませんでした: {src_out}")
        dst_out = REPO_ROOT / "public_site" / name
        if dst_out.exists():
            shutil.rmtree(dst_out)
        dst_out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(src_out, dst_out)
        print(f"[{grade_id}] -> {dst_out.relative_to(REPO_ROOT)}")
        return dst_out
    finally:
        if keep_stage:
            print(f"[{grade_id}] stage を保持: {stage_root}")
        else:
            shutil.rmtree(stage_root, ignore_errors=True)


def main() -> int:
    ap = argparse.ArgumentParser(description="新種サイトを staging ビルドして public_site/<grade> に配置")
    ap.add_argument("grade", nargs="?", help="種ID（self / master）。省略時は全副種。")
    ap.add_argument("--keep-stage", action="store_true", help="デバッグ用に stage を残す")
    args = ap.parse_args()

    if args.grade:
        build(args.grade, keep_stage=args.keep_stage)
    else:
        for g in secondary_grades():
            build(g.id, keep_stage=args.keep_stage)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
