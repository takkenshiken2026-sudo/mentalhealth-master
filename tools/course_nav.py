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


def course_switcher_html() -> str:
    """トップページ用の級切替バンド（全公開種・現在種を強調表示）。"""
    entries = course_entries()
    if len(entries) < 2:
        return ""
    pills: list[str] = []
    for e in entries:
        label = html.escape(e["label"])
        if e["current"]:
            pills.append(
                '<span class="course-switch-pill course-switch-pill--current" aria-current="page" '
                'style="padding:8px 14px;border-radius:999px;background:var(--accent);color:#fff;'
                'font-weight:700;font-size:.9rem;white-space:nowrap">'
                f"{label}<span style=\"opacity:.85;font-weight:600\">（閲覧中）</span></span>"
            )
        else:
            pills.append(
                f'<a class="course-switch-pill" href="{html.escape(e["url"])}" '
                'style="padding:8px 14px;border-radius:999px;border:1px solid var(--accent);'
                'color:var(--accent);text-decoration:none;font-weight:700;font-size:.9rem;'
                'white-space:nowrap;background:var(--bg)">'
                f"{label}</a>"
            )
    return (
        "\n      <!--COURSE_SWITCH_START-->"
        '<div class="course-switch" '
        'style="margin:18px 0 6px;padding:14px 16px;border:1px solid var(--border);'
        'border-radius:12px;background:var(--bg2)">'
        '<div style="font-size:.85rem;font-weight:700;color:var(--text2);margin-bottom:10px">'
        '対策する級（コース）を選ぶ</div>'
        '<div style="display:flex;flex-wrap:wrap;gap:8px">'
        + "".join(pills)
        + "</div></div><!--COURSE_SWITCH_END-->"
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
