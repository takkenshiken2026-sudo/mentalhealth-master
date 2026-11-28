#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""種（級/コース）間の相互導線を生成する。

grades.json の published=true の種だけを対象に、各サイトから他の級サイトへ
移動できるリンクを作る。URL は basePath をまたぐため絶対URL（origin + basePath）。
現在の種は base_path() で判定し、切替UIでは「閲覧中」として非リンク表示にする。

- course_switcher_html(): トップ(index.html)用の級切替バンド（全公開種、現在種を強調）。
- other_courses_section_html(): related-sites.html 用の「他のコース」節（他種のみ）。

いずれも公開種が1つしか無ければ空文字（＝何も出さない）を返す。
"""

from __future__ import annotations

import html
import re

from tools.grades import published_grades
from tools.site_config import base_path, clean_origin

# 表示順（難易度順: III種→II種→I種）。未知IDは末尾。
_ORDER = {"self": 0, "line": 1, "master": 2}


def course_entries() -> list[dict]:
    """公開種を表示順で返す。{id,label,short_label,url,current} のリスト。"""
    origin = clean_origin().rstrip("/")
    cur = base_path().rstrip("/")
    entries: list[dict] = []
    for g in published_grades():
        bp = g.base_path.rstrip("/")
        url = f"{origin}{bp}/" if bp else f"{origin}/"
        entries.append(
            {
                "id": g.id,
                "label": g.label,
                "short_label": g.short_label,
                "url": url,
                "current": bp == cur,
            }
        )
    entries.sort(key=lambda e: _ORDER.get(e["id"], 99))
    return entries


def _course_sub(label: str) -> str:
    """「III種（セルフケアコース）」→「セルフケアコース」。括弧が無ければ空文字。"""
    m = re.search(r"（(.+?)）", label)
    return m.group(1) if m else ""


def course_switcher_html() -> str:
    """トップページ用の級切替（全公開種・現在種を強調表示）。

    スマホでも場所を取らないよう、級を横1列の切替ボタンで並べる（各ボタンは級名＋コース名の2行）。
    """
    entries = course_entries()
    if len(entries) < 2:
        return ""
    seg_base = (
        "flex:1 1 0;min-width:0;display:flex;flex-direction:column;align-items:center;justify-content:center;"
        "gap:1px;padding:6px 4px;text-decoration:none;line-height:1.25;text-align:center"
    )
    segs: list[str] = []
    for i, e in enumerate(entries):
        short = html.escape(e["short_label"] or e["label"])
        sub = html.escape(_course_sub(e["label"]))
        sep = "" if i == 0 else "border-left:1px solid var(--accent);"
        inner = (
            f'<span style="font-weight:700;font-size:.9rem">{short}</span>'
            + (f'<span style="font-size:.7rem;opacity:.85">{sub}</span>' if sub else "")
        )
        if e["current"]:
            segs.append(
                f'<span class="course-switch-pill course-switch-pill--current" aria-current="page" '
                f'style="{seg_base};{sep}background:var(--accent);color:#fff">{inner}</span>'
            )
        else:
            segs.append(
                f'<a class="course-switch-pill" href="{html.escape(e["url"])}" '
                f'style="{seg_base};{sep}background:var(--bg);color:var(--accent)">{inner}</a>'
            )
    return (
        "\n      <!--COURSE_SWITCH_START-->"
        '<nav class="course-switch" aria-label="対策する級（コース）を切り替える" '
        'style="display:flex;margin:14px 0 8px;border:1px solid var(--accent);border-radius:10px;overflow:hidden">'
        + "".join(segs)
        + "</nav><!--COURSE_SWITCH_END-->"
    )


# 冪等な差し替え用マーカー。
COURSE_SWITCH_MARKER_START = "<!--COURSE_SWITCH_START-->"
COURSE_SWITCH_MARKER_END = "<!--COURSE_SWITCH_END-->"


def other_courses_section_html() -> str:
    """related-sites.html 用の「他のコース」節（現在種を除く他の公開種）。"""
    others = [e for e in course_entries() if not e["current"]]
    if not others:
        return ""
    lis = "\n".join(
        f'    <li><a href="{html.escape(e["url"])}">{html.escape(e["label"])}の対策サイト</a></li>'
        for e in others
    )
    return (
        '\n<section class="site-page-section" aria-labelledby="sec-courses">\n'
        '  <h2 id="sec-courses">他のコース（同じ検定の他の級）</h2>\n'
        "  <p>メンタルヘルス・マネジメント検定の他の級（コース）も、同じ使い方で対策できます。</p>\n"
        f"  <ul>\n{lis}\n  </ul>\n"
        "</section>"
    )
