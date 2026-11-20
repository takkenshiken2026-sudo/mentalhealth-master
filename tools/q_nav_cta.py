"""問題ページの「連番ナビ（前/次）」と「解く機能への CTA」を生成する共有モジュール。

過去問演習・実践演習・一問一答の各ビルダーから呼び出す。検索流入で個別ページに
着地したユーザーを、(1) 次の問題へ回遊させ、(2) 「解く」機能へ送り込むことを狙う。

rel_href は各ビルダーが持つ相対パス解決関数をそのまま渡して使う（循環 import 回避）。
"""

from __future__ import annotations

import html
import re
from pathlib import Path
from typing import Callable, Optional

RelHref = Callable[[Path, str], str]

# 各モードの並び順キー（この順序の隣接ページが「前/次の問題」になる）
_SORT_KEYS = {
    "past": lambda p: (p.get("year", 0), p.get("qno", 0)),
    "practice": lambda p: p.get("qno", 0),
    "ichimon": lambda p: _ichimon_num(p.get("id", "")),
}

# モード別のラベル・リンク設定
MODE_CONFIG = {
    "past": {
        "app_href": "index.html#past",
        "index_href": "q/index.html",
        "index_label": "過去問一覧",
        "solve_label": "過去問を解く",
        "mode_label": "過去問演習",
    },
    "practice": {
        "app_href": "index.html#orig",
        "index_href": "q/practice/index.html",
        "index_label": "実践演習一覧",
        "solve_label": "実践演習を解く",
        "mode_label": "実践演習",
    },
    "ichimon": {
        "app_href": "index.html#ichimondou",
        "index_href": "q/ichimon/index.html",
        "index_label": "一問一答一覧",
        "solve_label": "一問一答を解く",
        "mode_label": "一問一答",
    },
}


def _ichimon_num(rid: str) -> int:
    m = re.search(r"(\d+)", rid or "")
    return int(m.group(1)) if m else 0


def _seq_label(mode: str, page: dict) -> str:
    """連番ナビに表示する短いラベル。"""
    if mode in ("past", "practice"):
        return f'第{page.get("qno")}問'
    return str(page.get("id") or "")


def sequence_neighbors(
    all_pages: list[dict], current: dict, mode: str
) -> tuple[Optional[dict], Optional[dict]]:
    """current の前後ページを返す（存在しなければ None）。"""
    key = _SORT_KEYS[mode]
    ordered = sorted(all_pages, key=key)
    rels = [p.get("rel_path") for p in ordered]
    try:
        i = rels.index(current.get("rel_path"))
    except ValueError:
        return None, None
    prev_page = ordered[i - 1] if i > 0 else None
    next_page = ordered[i + 1] if i + 1 < len(ordered) else None
    return prev_page, next_page


def sequence_nav_html(
    rel_path: Path,
    mode: str,
    all_pages: list[dict],
    current: dict,
    rel_href: RelHref,
) -> str:
    """前の問題 / 一覧 / 次の問題 の3連ナビを生成する。"""
    cfg = MODE_CONFIG[mode]
    prev_page, next_page = sequence_neighbors(all_pages, current, mode)

    def cell(page: Optional[dict], direction: str, dir_label: str) -> str:
        if page is None:
            return (
                f'<span class="q-seq-link q-seq-{direction} is-disabled" aria-disabled="true">'
                f'<span class="q-seq-dir">{html.escape(dir_label)}</span>'
                f'<span class="q-seq-label">—</span></span>'
            )
        href = html.escape(rel_href(rel_path, page["rel_path"]))
        label = html.escape(_seq_label(mode, page))
        return (
            f'<a class="q-seq-link q-seq-{direction}" href="{href}">'
            f'<span class="q-seq-dir">{html.escape(dir_label)}</span>'
            f'<span class="q-seq-label">{label}</span></a>'
        )

    index_cell = (
        '<a class="q-seq-link q-seq-index" '
        f'href="{html.escape(rel_href(rel_path, cfg["index_href"]))}">'
        '<span class="q-seq-dir">一覧</span>'
        f'<span class="q-seq-label">{html.escape(cfg["index_label"])}</span></a>'
    )

    return (
        '<nav class="q-seq-nav" aria-label="問題の連番ナビゲーション">'
        + cell(prev_page, "prev", "← 前の問題")
        + index_cell
        + cell(next_page, "next", "次の問題 →")
        + "</nav>"
    )


def solve_cta_html(
    rel_path: Path,
    mode: str,
    current: dict,
    rel_href: RelHref,
) -> str:
    """「解く」機能（アプリ）へ誘導する CTA カードを生成する。"""
    cfg = MODE_CONFIG[mode]
    category = (current.get("category") or "").strip()
    cat_phrase = f"「{category}」分野を中心に、" if category else ""
    body = (
        "読むだけで終えず、本番と同じ出題形式で解くと知識が定着します。"
        f"{cat_phrase}{cfg['mode_label']}をこのまま続けて力試ししましょう。"
    )
    app = html.escape(rel_href(rel_path, cfg["app_href"]))
    return (
        '<aside class="q-solve-cta" aria-labelledby="q-solve-cta-h">'
        '<div class="q-solve-cta-main">'
        '<p class="q-solve-cta-eyebrow">このまま力試し</p>'
        f'<h2 id="q-solve-cta-h" class="q-solve-cta-title">{html.escape(cfg["solve_label"])}モードで演習する</h2>'
        f'<p class="q-solve-cta-text">{html.escape(body)}</p>'
        "</div>"
        '<div class="q-solve-cta-actions">'
        f'<a class="q-solve-cta-btn q-solve-cta-btn--primary" href="{app}">{html.escape(cfg["solve_label"])} ▶</a>'
        "</div>"
        "</aside>"
    )
