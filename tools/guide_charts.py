# -*- coding: utf-8 -*-
"""試験ガイド記事に埋め込む合格率の推移グラフ（inline SVG）＋データ表を生成する。

記事本文（guide_articles.csv の section_body）は生HTMLを通さない（エスケープされる）ため、
本文中にプレーンなマーカー（CHART_MARKER）を1行だけ置き、build_article_pages.py が
生成後のHTMLに対して本グレードのグラフ＋表ブロックへ置換する。

データ出典: 大阪商工会議所「結果・受験者データ」 https://www.mental-health.ne.jp/data/
（実受験者数を分母に算出。合格者数÷実受験者数＝公式合格率で全回の整合を確認済み）
"""

from __future__ import annotations

# 本文に置くプレーンなマーカー（英大文字のみ・用語自動リンクや装飾の対象外）
CHART_MARKER = "PASSRATECHARTMARKER"

# (回, 実施年, 実施月, 受験者, 実受験者, 合格者, 合格率)
_II = [
    (29, 2020, 11, 11294, 10343, 5840, 56.5), (30, 2021, 3, 12113, 10686, 7285, 68.2),
    (31, 2021, 11, 11046, 10053, 4664, 46.4), (32, 2022, 3, 12663, 11128, 7763, 69.8),
    (33, 2022, 11, 12175, 10998, 6401, 58.2), (34, 2023, 3, 13340, 11918, 6444, 54.1),
    (35, 2023, 11, 12973, 11781, 6661, 56.5), (36, 2024, 3, 13934, 12483, 9137, 73.2),
    (37, 2024, 11, 13065, 11802, 7141, 60.5), (38, 2025, 3, 14362, 12745, 6985, 54.8),
    (39, 2025, 11, 14169, 12887, 6160, 47.8), (40, 2026, 3, 15558, 13865, 10819, 78.0),
]
_III = [
    (29, 2020, 11, 5516, 5046, 4361, 86.4), (30, 2021, 3, 5661, 5051, 4135, 81.9),
    (31, 2021, 11, 5849, 5371, 3824, 71.2), (32, 2022, 3, 5402, 4849, 3121, 64.4),
    (33, 2022, 11, 6002, 5458, 3787, 69.4), (34, 2023, 3, 5600, 5035, 3995, 79.3),
    (35, 2023, 11, 5344, 4888, 3515, 71.9), (36, 2024, 3, 5174, 4648, 3353, 72.1),
    (37, 2024, 11, 5477, 5060, 3758, 74.3), (38, 2025, 3, 5940, 5341, 4157, 77.8),
    (39, 2025, 11, 5617, 5139, 3347, 65.1), (40, 2026, 3, 6090, 5496, 3831, 69.7),
]
# I種は年1回（11月）のみ実施
_I = [
    (29, 2020, 11, 1571, 1276, 272, 21.3), (31, 2021, 11, 1866, 1521, 301, 19.8),
    (33, 2022, 11, 2000, 1628, 287, 17.6), (35, 2023, 11, 1961, 1587, 325, 20.5),
    (37, 2024, 11, 2184, 1731, 362, 20.9), (39, 2025, 11, 2111, 1710, 331, 19.4),
]

# グレード別の設定（site_config.exam_grade() の戻り値をキーにする）
_GRADES = {
    "II種": dict(rows=_II, kana="ラインケア", span="第29回〜第40回", xmode="ym", accent="#1C7A40", dark="#145e30"),
    "III種": dict(rows=_III, kana="セルフケア", span="第29回〜第40回", xmode="ym", accent="#3f6b7a", dark="#30545f"),
    "I種": dict(rows=_I, kana="マスター", span="2020年〜2025年", xmode="y", accent="#6b4a5c", dark="#533a48"),
}


def _avg(rows):
    return sum(r[6] for r in rows) / len(rows)


def _svg(rows, title, xmode):
    W, H = 760, 364
    ml, mr, mt, mb = 46, 14, 48, 54
    pw, ph = W - ml - mr, H - mt - mb
    y0 = mt + ph

    def y(v):
        return mt + ph * (1 - v / 100.0)

    n = len(rows)
    slot = pw / n
    barw = 30 if n >= 10 else 46
    avg = _avg(rows)
    desc = "、".join(f"第{r[0]}回{r[6]}%" for r in rows) + f"。{n}回平均は約{avg:.1f}%。"
    s = [
        f'<svg viewBox="0 0 {W} {H}" role="img" aria-labelledby="prchart-title prchart-desc" '
        f'class="prchart-svg" preserveAspectRatio="xMidYMid meet">',
        f'<title id="prchart-title">{title}</title>',
        f'<desc id="prchart-desc">{desc}</desc>',
    ]
    for gv in (0, 20, 40, 60, 80, 100):
        gy = y(gv)
        s.append(f'<line x1="{ml}" y1="{gy:.1f}" x2="{W-mr}" y2="{gy:.1f}" class="prchart-grid"/>')
        s.append(f'<text x="{ml-8}" y="{gy+4:.1f}" class="prchart-ylab" text-anchor="end">{gv}</text>')
    s.append(f'<line x1="{ml}" y1="{y0:.1f}" x2="{W-mr}" y2="{y0:.1f}" class="prchart-axis"/>')
    ay = y(avg)
    s.append(f'<line x1="{ml}" y1="{ay:.1f}" x2="{W-mr}" y2="{ay:.1f}" class="prchart-avg"/>')
    s.append('<text x="38" y="26" class="prchart-unit" text-anchor="end">(%)</text>')
    s.append(f'<line x1="{ml}" y1="22" x2="{ml+24}" y2="22" class="prchart-avg"/>')
    s.append(f'<text x="{ml+30}" y="26" class="prchart-avglab" text-anchor="start">{n}回平均 約{avg:.1f}%</text>')
    for i, r in enumerate(rows):
        cx = ml + slot * i + slot / 2
        bx = cx - barw / 2
        by = y(r[6])
        bh = y0 - by
        s.append('<g class="prchart-bar">')
        s.append(f'<title>第{r[0]}回（{r[1]}年{r[2]}月）合格率 {r[6]}%　実受験者{r[4]:,}人／合格者{r[5]:,}人</title>')
        s.append(f'<rect x="{bx:.1f}" y="{by:.1f}" width="{barw}" height="{bh:.1f}" rx="4" class="prchart-rect"/>')
        s.append(f'<text x="{cx:.1f}" y="{by-6:.1f}" class="prchart-val" text-anchor="middle">{r[6]:.0f}</text>')
        s.append(f'<text x="{cx:.1f}" y="{y0+18:.1f}" class="prchart-xlab" text-anchor="middle">{r[0]}</text>')
        lab = f"{str(r[1])[2:]}/{r[2]}" if xmode == "ym" else f"{r[1]}"
        s.append(f'<text x="{cx:.1f}" y="{y0+34:.1f}" class="prchart-xlab2" text-anchor="middle">{lab}</text>')
        s.append("</g>")
    foot = "回（下段＝実施年/月）" if xmode == "ym" else "回（下段＝実施年・いずれも11月実施）"
    s.append(f'<text x="{ml+pw/2:.1f}" y="{H-4}" class="prchart-axistitle" text-anchor="middle">{foot}</text>')
    s.append("</svg>")
    return "\n".join(s)


def _table(rows):
    tr = []
    for r in rows:
        tr.append(
            f'<tr><th scope="row">第{r[0]}回</th><td>{r[1]}年{r[2]}月</td>'
            f'<td class="num">{r[4]:,}</td><td class="num">{r[5]:,}</td>'
            f'<td class="num prchart-rate">{r[6]:.1f}％</td></tr>'
        )
    head = (
        '<thead><tr><th scope="col">回</th><th scope="col">実施時期</th>'
        '<th scope="col" class="num">実受験者数</th><th scope="col" class="num">合格者数</th>'
        '<th scope="col" class="num">合格率</th></tr></thead>'
    )
    return (
        '<div class="prchart-scroll"><table class="seo-info-table prchart-table">'
        + head + "<tbody>" + "".join(tr) + "</tbody></table></div>"
    )


def chart_block(grade: str) -> str:
    """グレード（例 'II種'）の合格率グラフ＋データ表ブロックのHTMLを返す。対象外は空文字。"""
    g = _GRADES.get((grade or "").strip())
    if not g:
        return ""
    rows = g["rows"]
    avg = _avg(rows)
    n = len(rows)
    title = f"メンタルヘルス・マネジメント検定{grade} 合格率の推移（{g['span']}）"
    svg = _svg(rows, title, g["xmode"])
    figcap = (
        f"図：{grade}（{g['kana']}）合格率の推移（{g['span']}）。棒の数値は各回の合格率（％）、"
        f"点線は{n}回の単純平均（約{avg:.1f}％）。合格率は実受験者数を分母に算出。"
        f"出典：大阪商工会議所「結果・受験者データ」をもとに編集部作成。"
    )
    tablecap = (
        '表の「実受験者数」は申込者ではなく当日実際に受験した人数で、合格率はこの実受験者数を分母に'
        '算出されています。出典：大阪商工会議所「'
        '<a href="https://www.mental-health.ne.jp/data/" target="_blank" rel="noopener noreferrer">'
        '結果・受験者データ</a>」（2026年11月19日確認）。'
    )
    if grade == "I種":
        tablecap += "I種（マスターコース）は年1回・11月のみの実施のため、3月実施回は含まれません。"
    style = f'--prchart-accent:{g["accent"]};--prchart-accent-dark:{g["dark"]}'
    return (
        f'<div class="prchart-block" style="{style}">'
        + '<figure class="prchart-figure"><div class="prchart-scroll">'
        + svg
        + f'</div><figcaption class="prchart-caption">{figcap}</figcaption></figure>'
        + '<p>回ごとの詳しい数値は次のとおりです。</p>'
        + _table(rows)
        + f'<p class="prchart-caption">{tablecap}</p>'
        + '</div>'
    )


import re

# 合格率の推移グラフを挿入する対象スラッグ
CHART_SLUG = "exam-difficulty"
_SEC2_HEADING = re.compile(r'(<h2 id="article-sec-2"[^>]*>.*?</h2>)', re.S)


def inject(html: str, slug: str, grade: str) -> str:
    """exam-difficulty 記事の section-2 見出し直後に、グレードのグラフ＋表ブロックを挿入する。

    本文（CSV）は生HTMLを通さないため、生成済みページHTMLに対して後挿入する。
    見出しを起点にするので本文テキストの表現に依存しない（堅牢）。
    """
    if (slug or "").strip() != CHART_SLUG:
        return html
    block = chart_block(grade)
    if not block:
        return html
    m = _SEC2_HEADING.search(html)
    if not m:
        return html
    return html[: m.end()] + block + html[m.end():]
