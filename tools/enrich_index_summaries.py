#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""知識ハブ一覧の「定義」「概要」列を、詳細記事の内容から一意の要約文に更新する。"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.build_glossary_pages import (  # noqa: E402
    _GENERIC_SNIPPET_SUFFIXES,
    _is_generic_index_snippet,
    terms_index_snippet,
)
from tools.rewrite_glossary_handcrafted import (  # noqa: E402
    KNOWN_DEFINITIONS,
    is_generic,
    parse_source,
)

GLOSSARY_CSV = ROOT / "data" / "glossary_terms.csv"
COMPARE_CSV = ROOT / "data" / "comparisons.csv"
NUMBERS_CSV = ROOT / "data" / "numbers.csv"
MISTAKES_CSV = ROOT / "data" / "mistakes.csv"

MAX_LEN = 220

GENERIC_NUMBER_STARTS = (
    "数値問題は数字そのものより",
    "復職・休職・面接・集団分析の数値は",
    "S33の数値は",
    "S34の数値は",
    "代表値は適用条件は対象者・規模を確認",
)
GENERIC_MISTAKE_STARTS = (
    "制度名が似ているため",
    "誤答は知識不足だけでなく",
    "復職・面接・集団分析は名称が似る",
    "再発防止・配置転換・産業保健師",
    "S32誤答はプロセスと主体",
    "S33誤答は",
    "S34誤答は",
)
GENERIC_COMPARE_PHRASES = (
    "目的・主体・時点を同時確認、比較軸を先に固定",
    "条文→ガイド→事例",
    "条件文の主語を下線",
    "実務プロセスの差を説明",
)
PLACEHOLDER_ITEM_VALUES = frozenset(
    {"要項・規則確認", "対象者・規模を確認", "年間計画で管理", "数値+条件で暗記"}
)
GENERIC_PATTERN_WRONGS = frozenset(
    {"名称だけで判断", "数字だけ比較", "時系列を逆に読む", "共有範囲を拡大"}
)

COMPARE_SUMMARY_BOILER = re.compile(
    r"5軸で整理|比較表で違いを整理|目的・主体・手続・数値・試験論点の5軸"
)
MISTAKE_SUMMARY_BOILER = re.compile(
    r"誤答を整理します|典型誤答を整理|誤答パターンを整理"
)
NUMBER_SUMMARY_BOILER = re.compile(
    r"早見表に整理します|代表数値を早見表|数値・条件・記録要件を、"
)

PLACEHOLDER_CELL = (
    "制度の役割を確認",
    "実務での運用を確認",
    "誰が主導するかを整理",
    "誰と連携するかを整理",
    "平時の対応かを確認",
    "発生後の対応かを確認",
    "キーワードで判別",
    "主語の入替えに注意",
    "比較軸を先に決める",
    "条件文を最後まで読む",
    "【記入】",
    "主語・目的の確認",
    "手順・対象の確認",
)

GENERIC_LEAD_MARKERS = (
    "S31では、用語の定義だけでなく制度運用の差",
    "S32では職場復帰・休職復職",
    "S33では再発防止・配置転換",
    "S34では",
    "比較軸を固定してから問題を読むと",
    "義務主体・実施手順・記録保存",
    "実務プロセスの差を説明できることを目標",
)

GENERIC_COMMON_MISTAKES = frozenset(
    {
        "主語の読み飛ばし",
        "時系列の逆転",
        "類似制度の混同",
        "制度名だけで判断する",
        "主語を読み飛ばす",
        "運用時点を混同する",
    }
)

FAQ_BOILER = (
    "用語解説・比較表・数値早見表とあわせて復習すると定着しやすくなります",
    "過去問で正誤の型を分類し、試験要項で数値・期限を照合してください",
)

TITLE_PAIR_RES = (
    re.compile(r"^(.+?)と(.+?)の違い(?:（[^）]+）)?$"),
    re.compile(r"^(.+?)と(.+?)の使い分け(?:（[^）]+）)?$"),
    re.compile(r"^(.+?)と(.+?)の整理(?:（[^）]+）)?$"),
    re.compile(r"^(.+?)と(.+?)の比較(?:（[^）]+）)?$"),
)

COMPARE_AXIS_PRIORITY = (
    "目的",
    "定義",
    "法的根拠",
    "主な対象",
    "位置づけ",
    "主体",
    "実施主体",
    "タイミング",
    "実施タイミング",
    "主な内容",
    "内容例",
)

# タイトルに含まれる語で、用語集に無い場合の短い補足
TOPIC_HINTS: dict[str, str] = {
    "一次予防": "疾病発生前に職場環境等のリスクを下げる段階",
    "二次予防": "早期発見・早期対応で悪化を防ぐ段階",
    "ハラスメント相談": "被害・当事者からの相談受付と初動対応",
    "通報対応": "事実確認・再発防止を含む調査・是正プロセス",
    "セルフケア": "本人が心身の健康を保つための自助的な取組",
    "産業医連携": "医師としての健康管理上の助言・意見",
    "人事調整": "休復職手続・就業条件・情報管理の調整",
    "長時間面接": "時間外労働が多い労働者への医師面接（労基法）",
    "健診フォロー": "健康診断結果に基づく保健指導・再検査等",
    "休職支援": "回復のための休業と職場での配慮",
    "就業配慮": "復職後の業務・時間・環境の具体的調整",
    "危機介入": "自傷・他害のおそれ等への緊急対応",
    "復職支援": "職場復帰プランと定着までの支援",
    "研修実施": "管理監督者等への計画的な教育・情報提供",
    "効果評価": "実施内容の評価と改善への反映",
    "ストレス要因分析": "職場全体の負担要因の把握",
    "組織改善": "分析結果に基づく職場環境の改善",
    "要項確認": "受験資格・合格基準・出題範囲の公式確認",
    "社内ルール確認": "社内規程と法令・ガイドラインの整合",
    "再発防止": "同種の問題の再発を防ぐための措置・体制",
    "初動対応": "問題発生直後の安全確保と初期対応",
    "配置転換": "業務・配置の変更による負担軽減",
    "産業保健師": "産業医の指示の下で行う衛生管理・保健業務",
    "産業医連携": "医師としての健康管理上の意見・助言",
    "過重労働防止": "時間外・休日労働の適正化と健康確保",
    "職場環境": "心理的・物理的負担要因の改善",
    "集団分析": "ストレスチェック結果の事業場単位の分析",
    "個別面接": "高ストレス者等への医師・保健師面接",
    "医師面接": "法令上の面接指導等における医師の面接",
    "産業医面接": "産業医による面接・意見表明",
    "休職手続": "休業に関する人事・労務上の手続",
    "復職手続": "復職に向けた調整・合意形成の手続",
    "職場復帰支援": "復職プランと段階的復職等の支援",
    "就業上の配慮": "業務内容・時間・配置等の具体的調整",
}


def norm(s: str | None) -> str:
    return (s or "").strip()


def split_sents(text: str) -> list[str]:
    return [p.strip() for p in re.findall(r"[^。！？]+[。！？]?", text or "") if p.strip()]


def normalize_periods(text: str) -> str:
    t = re.sub(r"\s+", " ", (text or "").strip())
    t = re.sub(r"[。！？]{2,}", "。", t)
    return t


def clean_article_title(title: str) -> str:
    t = norm(title)
    t = re.sub(r"\s+S\d+$", "", t)
    t = re.sub(r"｜メンタルヘルス.+$", "", t)
    t = re.sub(r"｜数値早見表$", "", t)
    t = re.sub(r"｜誤答パターン$", "", t)
    return t.strip()


def is_placeholder_number_items(row: dict[str, str]) -> bool:
    try:
        items = json.loads(row.get("item_rows") or "[]")
    except json.JSONDecodeError:
        return True
    if not items:
        return True
    for item in items:
        value = norm(item.get("value"))
        if not value or value in PLACEHOLDER_ITEM_VALUES:
            continue
        if any(x in value for x in ("【", "試験要点", "要項・規則確認")):
            continue
        if len(value) >= 6:
            return False
    return True


def is_generic_mistake_patterns(row: dict[str, str]) -> bool:
    try:
        patterns = json.loads(row.get("pattern_rows") or "[]")
    except json.JSONDecodeError:
        return True
    if not patterns:
        return True
    return all(norm(p.get("wrong")) in GENERIC_PATTERN_WRONGS for p in patterns)


def first_useful_faq(row: dict[str, str]) -> str:
    for i in range(1, 5):
        ans = strip_faq_boiler(norm(row.get(f"faq_{i}_answer")))
        for sent in split_sents(ans):
            if len(sent) >= 24 and not is_generic_lead(sent):
                if "用語解説・比較表" not in sent and "過去問で正誤" not in sent:
                    return sent
    return ""


def summary_is_generic(text: str, kind: str) -> bool:
    s = norm(text)
    if not s:
        return True
    if kind == "numbers":
        return any(s.startswith(p) for p in GENERIC_NUMBER_STARTS) or NUMBER_SUMMARY_BOILER.search(s)
    if kind == "mistakes":
        return any(s.startswith(p) for p in GENERIC_MISTAKE_STARTS) or MISTAKE_SUMMARY_BOILER.search(s)
    if kind == "compare":
        return any(p in s for p in GENERIC_COMPARE_PHRASES) or COMPARE_SUMMARY_BOILER.search(s)
    return False


def clamp(text: str, limit: int = MAX_LEN) -> str:
    t = normalize_periods(text)
    if len(t) <= limit:
        return t if t.endswith("。") or not t else t + "。"
    cut = t[: limit - 1]
    if "、" in cut[limit // 2 :]:
        cut = cut[: cut.rfind("、") + 1]
    return cut.rstrip("、") + "…"


def strip_faq_boiler(text: str) -> str:
    out = norm(text)
    for m in FAQ_BOILER:
        out = out.replace(m, "")
    return re.sub(r"\s+", " ", out).strip()


def is_generic_lead(text: str) -> bool:
    t = norm(text)
    if not t:
        return True
    return any(m in t for m in GENERIC_LEAD_MARKERS)


def cell_is_real(text: str) -> bool:
    t = norm(text)
    if len(t) < 10:
        return False
    return not any(m in t for m in PLACEHOLDER_CELL)


def shorten_cell(text: str, max_len: int = 55) -> str:
    t = norm(text).rstrip("。")
    if len(t) <= max_len:
        return t
    return t[: max_len - 1] + "…"


def load_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader.fieldnames or []), list(reader)


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def load_glossary_short_index() -> dict[str, str]:
    out: dict[str, str] = {}
    if not GLOSSARY_CSV.is_file():
        return out
    _, rows = load_csv(GLOSSARY_CSV)
    for row in rows:
        term = norm(row.get("term"))
        short = norm(row.get("short_def"))
        if term and short and not _is_generic_index_snippet(short, term):
            out[term] = short.rstrip("。")
    return out


def hint_for_term(term: str, glossary: dict[str, str]) -> str | None:
    t = norm(term)
    if not t:
        return None
    if t in glossary:
        g = glossary[t]
        return g[len(t) + 1 :].lstrip("は、") if g.startswith(t) else g
    if t in TOPIC_HINTS:
        return TOPIC_HINTS[t]
    if "（" in t:
        base = t.split("（", 1)[0]
        return hint_for_term(base, glossary)
    return None


def parse_title_pair(title: str) -> tuple[str, str] | None:
    t = re.sub(r"\s+S\d+$", "", norm(title))
    t = re.sub(r"（[^）]*）$", "", t).strip()
    for pat in TITLE_PAIR_RES:
        m = pat.match(t)
        if m:
            a, b = m.group(1).strip(), m.group(2).strip()
            if a and b and a != b:
                return a, b
    if "と" in t and "：" not in t:
        a, _, b = t.partition("と")
        a, b = a.strip(), b.strip()
        for sfx in ("の比較", "の整理", "の違い", "の対比", "の使い分け"):
            b = b.replace(sfx, "").strip()
        if a and b and a != b and len(a) >= 2 and len(b) >= 2:
            return a, b
    return None


def pair_from_row(row: dict[str, str]) -> tuple[str, str]:
    parts = [p.strip() for p in (row.get("col_labels") or "").split(";") if p.strip()]
    generic = {"観点A", "観点B", "整理", "確認", "用語A", "用語B"}
    if len(parts) >= 2 and parts[0] not in generic and parts[1] not in generic:
        return parts[0], parts[1]
    parsed = parse_title_pair(row.get("title", ""))
    if parsed:
        return parsed
    title = norm(row.get("title", ""))
    if "：" in title:
        head, tail = title.split("：", 1)
        return head.strip(), tail.strip()
    return title, "関連制度"


def first_exam_points(row: dict[str, str], n: int = 2) -> str:
    pts = [
        p.strip()
        for p in (row.get("exam_points") or "").split(";")
        if p.strip() and len(p.strip()) >= 4
    ]
    if not pts:
        return ""
    joined = "、".join(pts[:n])
    return joined if joined.endswith("。") else joined + "。"


def has_placeholder_compare(row: dict[str, str]) -> bool:
    try:
        axes = json.loads(row.get("compare_rows") or "[]")
    except json.JSONDecodeError:
        return True
    if not axes:
        return True
    for ax in axes:
        for col in ax.get("cols") or []:
            if cell_is_real(norm(col)):
                return False
    return True


def summarize_compare(row: dict[str, str], glossary: dict[str, str]) -> str:
    t1, t2 = pair_from_row(row)
    parts: list[str] = []

    h1, h2 = hint_for_term(t1, glossary), hint_for_term(t2, glossary)
    if h1 and h2:
        parts.append(f"{t1}は{h1}、{t2}は{h2}。")
    elif h1:
        parts.append(f"{t1}は{h1}。{t2}との違いは目的・主体・時点で見分けます。")

    try:
        axes = json.loads(row.get("compare_rows") or "[]")
    except json.JSONDecodeError:
        axes = []

    for key in COMPARE_AXIS_PRIORITY:
        for ax in axes:
            axis_name = norm(ax.get("axis"))
            if key not in axis_name:
                continue
            cols = ax.get("cols") or []
            if len(cols) < 2:
                continue
            c0, c1 = norm(cols[0]), norm(cols[1])
            if cell_is_real(c0) and cell_is_real(c1):
                parts.append(f"{t1}は{shorten_cell(c0)}、{t2}は{shorten_cell(c1)}。")
                break
        else:
            continue
        break

    if not parts or has_placeholder_compare(row):
        lead = strip_faq_boiler(row.get("article_lead", ""))
        for sent in split_sents(lead):
            if not is_generic_lead(sent) and len(sent) >= 20:
                if norm(row.get("summary", "")) not in sent:
                    parts.insert(0, sent)
                    break

    cm_parts = [
        p.strip()
        for p in (row.get("common_mistakes") or "").split(";")
        if p.strip() and p.strip() not in GENERIC_COMMON_MISTAKES
    ]
    if cm_parts:
        parts.append(f"試験では{cm_parts[0].rstrip('。')}。")
    elif norm(row.get("common_mistakes", "")):
        first = norm(row.get("common_mistakes", "")).split(";")[0]
        if len(first) >= 12:
            parts.append(f"誤答では{first.rstrip('。')}。")

    tip = norm(row.get("memory_tip", ""))
    if tip and tip != "「目的→主体→時点」で毎回判定。" and len(tip) >= 10:
        if not tip.startswith("覚え方"):
            tip = f"覚え方：{tip}" if not tip.startswith("「") else f"覚え方は{tip}"
        parts.append(tip if tip.endswith("。") else tip + "。")

    ep = first_exam_points(row, 2)
    if ep:
        ep_plain = ep.rstrip("。")
        generic_ep = ep_plain in (
            "目的・主体・時点を同時確認、比較軸を先に固定",
            "主体と目的を同時に確認、時系列で整理",
            "条件文の主語を下線",
        ) or "比較軸を先に固定" in ep_plain
        if ep_plain not in "".join(parts) and not generic_ep:
            parts.append(f"押さえる点は{ep_plain}。")

    joined = "".join(parts)
    if t1 not in joined or t2 not in joined:
        parts.insert(
            0,
            f"「{t1}」と「{t2}」は目的・主体・実施時点の違いで見分けます。",
        )

    if not parts:
        parts.append(
            f"{t1}と{t2}の目的・主体・手続の違いを、条文と過去問の入れ替え肢とあわせて整理します。"
        )

    return clamp("".join(parts))


def load_number_anchors() -> list[dict[str, str]]:
    if not NUMBERS_CSV.is_file():
        return []
    _, rows = load_csv(NUMBERS_CSV)
    return [r for r in rows if not is_placeholder_number_items(r)]


def load_mistake_anchors() -> list[dict[str, str]]:
    if not MISTAKES_CSV.is_file():
        return []
    _, rows = load_csv(MISTAKES_CSV)
    return [r for r in rows if not is_generic_mistake_patterns(r)]


def _score_related(row: dict[str, str], candidate: dict[str, str]) -> int:
    title = clean_article_title(row.get("title", ""))
    c_title = clean_article_title(candidate.get("title", ""))
    score = 0
    for word in re.findall(r"[\u4e00-\u9fff]{2,}", title):
        if word in c_title:
            score += 2
    row_tags = {t.strip() for t in (row.get("tags") or "").split(";") if t.strip()}
    c_tags = candidate.get("tags") or ""
    for t in row_tags:
        if t and t in c_tags:
            score += 1
    return score


def best_anchor(row: dict[str, str], anchors: list[dict[str, str]]) -> dict[str, str] | None:
    best: dict[str, str] | None = None
    best_score = 0
    for cand in anchors:
        sc = _score_related(row, cand)
        if sc > best_score:
            best_score = sc
            best = cand
    return best if best_score >= 2 else None


def title_angle_sentence(title: str, category: str) -> str:
    t = clean_article_title(title)
    pairs = (
        ("年間運用", "実施から集団分析・結果周知・改善までの年間サイクル"),
        ("閾値", "数値基準と適用条件（誰に・いつ）"),
        ("実施頻度", "実施回数・計画的運用"),
        ("実施率", "実施状況の把握と未実施防止"),
        ("ステップ", "段階的な手順と記録"),
        ("休職", "休業期間の個別判断と情報管理"),
        ("復職", "復職プランと段階的復帰"),
        ("面接", "医師面接・面接指導の要件とタイミング"),
        ("初動", "相談受理後の初動と調査"),
        ("保存", "記録の保管・保密"),
        ("研修", "管理監督者への計画的教育"),
        ("相談窓口", "相談体制と運用件数"),
        ("衛生委員会", "報告・共有のサイクル"),
        ("要項", "受験要項・公式情報の確認タイミング"),
        ("学習", "試験学習の配分と周期"),
        ("合格", "合格基準・配点"),
        ("ハラスメント", "防止措置と相談対応"),
        ("健診", "健康診断とメタボ関連数値"),
    )
    for key, phrase in pairs:
        if key in t:
            return f"{t}では、{phrase}が中心論点です。"
    if category:
        return f"{t}は{category}分野で、数値・期限・主体をセットで確認する論点です。"
    return f"{t}の代表数値と適用条件を整理します。"


def summarize_numbers(row: dict[str, str], anchors: list[dict[str, str]] | None = None) -> str:
    parts: list[str] = []
    title = clean_article_title(row.get("title", ""))
    stub = is_placeholder_number_items(row)

    if stub:
        anchor = best_anchor(row, anchors or load_number_anchors())
        if anchor:
            anchor_sum = summarize_numbers(anchor, anchors)
            angle = title_angle_sentence(title, norm(row.get("category")))
            if angle not in anchor_sum:
                parts.append(angle)
            for sent in split_sents(anchor_sum):
                if sent not in angle and len(sent) >= 16:
                    parts.append(sent)
                    if len(parts) >= 3:
                        break
        else:
            parts.append(title_angle_sentence(title, norm(row.get("category"))))
        if parts:
            return clamp("".join(parts))

    lead = strip_faq_boiler(row.get("article_lead", ""))
    for sent in split_sents(lead):
        if len(sent) >= 18 and NUMBER_SUMMARY_BOILER.search(sent) is None:
            if not is_generic_lead(sent) and norm(row.get("summary", "")) not in sent:
                parts.append(sent)
                break

    try:
        items = json.loads(row.get("item_rows") or "[]")
    except json.JSONDecodeError:
        items = []

    vals: list[str] = []
    for item in items:
        label = norm(item.get("item"))
        value = norm(item.get("value"))
        if not value or any(x in value for x in ("要項", "【", "確認】", "試験要点")):
            continue
        if value in PLACEHOLDER_ITEM_VALUES or len(value) < 4:
            continue
        vals.append(f"{label}は{shorten_cell(value, 40)}" if label else shorten_cell(value, 40))
        if len(vals) >= 2:
            break

    if vals:
        parts.append("代表値は" + "、".join(vals) + "。")

    hl = norm(row.get("highlight", ""))
    if hl and hl not in ("代表値は要項・法令で確認", "要項・法令で確認", "数値は一次情報で最新確認"):
        if not vals or hl[:20] not in "".join(parts):
            parts.append(f"早見の要点：{hl}。")

    faq = first_useful_faq(row)
    if faq and faq not in "".join(parts):
        parts.append(faq if faq.endswith("。") else faq + "。")

    cm = norm(row.get("common_mistakes", ""))
    if cm:
        first = cm.split(";")[0].strip()
        if len(first) >= 10 and first not in GENERIC_COMMON_MISTAKES:
            parts.append(f"誤答では{first.rstrip('。')}。")

    ep = first_exam_points(row, 2)
    if ep:
        ep_plain = ep.rstrip("。")
        generic_ep = ep_plain in (
            "数値と条件を分けて覚えない",
            "数値と条件をセット",
            "主体を確認",
            "年度更新を確認",
        )
        if ep_plain not in "".join(parts) and not generic_ep:
            parts.append(f"試験では{ep_plain}。")

    tip = norm(row.get("memory_tip", ""))
    if tip and tip not in ("「数値・条件・主体」を1行で書く。", "「数値・条件・主体」を1行で書く") and len(tip) >= 8:
        if tip not in "".join(parts):
            parts.append(tip if tip.endswith("。") else tip + "。")

    if not parts and title:
        tags = [t.strip() for t in (row.get("tags") or "").split(";") if t.strip()]
        tag_hint = tags[0] if tags else ""
        if tag_hint:
            parts.append(
                f"{title}では、{tag_hint}に関する数値・期限・主体を、条文と試験要項と照合しながら整理します。"
            )
        else:
            parts.append(f"{title}の数値・期限・主体を、条文・試験要項と照合しながら整理します。")

    return clamp("".join(parts))


def shorten_wrong(wrong: str) -> str:
    w = norm(wrong)
    w = re.sub(r"^「[^」]+」で", "", w)
    w = re.sub(r"^「[^」]+」は、?", "", w)
    return shorten_cell(w, 48)


def summarize_mistake(row: dict[str, str], anchors: list[dict[str, str]] | None = None) -> str:
    parts: list[str] = []
    title = clean_article_title(row.get("title", ""))
    stub = is_generic_mistake_patterns(row)

    if stub:
        anchor = best_anchor(row, anchors or load_mistake_anchors())
        if anchor:
            anchor_sum = summarize_mistake(anchor, anchors)
            cp = norm(row.get("confusion_point", "")).rstrip("。")
            if cp and not summary_is_generic(cp, "mistakes"):
                opener = f"{title}では、{cp}が起きやすい論点です。"
            else:
                opener = f"{title}では、制度名や主体の取り違えが起きやすい論点です。"
            if opener not in anchor_sum:
                parts.append(opener)
            for sent in split_sents(anchor_sum):
                if "典型" in sent or "例：" in sent:
                    parts.append(sent)
                    break
        else:
            parts.append(f"{title}で出やすい誤答の型と正しい整理の仕方を、表と過去問で確認できます。")
        if parts:
            return clamp("".join(parts))

    cp = norm(row.get("confusion_point", ""))
    if cp and cp not in ("手順と主体の混同。", "手順と主体の混同"):
        if not summary_is_generic(cp, "mistakes"):
            parts.append(cp if cp.endswith("。") else cp + "。")

    try:
        patterns = json.loads(row.get("pattern_rows") or "[]")
    except json.JSONDecodeError:
        patterns = []

    if patterns and not is_generic_mistake_patterns(row):
        p0 = patterns[0]
        trap = norm(p0.get("trap"))
        wrong = shorten_wrong(norm(p0.get("wrong")))
        correct = shorten_cell(norm(p0.get("correct")), 52)
        if trap and len(trap) >= 6:
            trap_clean = trap.strip("「」")
            parts.append(
                f"典型は{trap_clean}の形で、{wrong}と捉えがちで、正しくは{correct}。"
            )
        elif wrong and correct:
            parts.append(f"例：{wrong}は誤りで、{correct}。")

    if len(parts) < 2:
        lead = strip_faq_boiler(row.get("article_lead", ""))
        for sent in split_sents(lead):
            if len(sent) >= 20 and MISTAKE_SUMMARY_BOILER.search(sent) is None:
                if not is_generic_lead(sent) and norm(row.get("summary", "")) not in sent:
                    parts.append(sent)
                    break

    faq = first_useful_faq(row)
    if faq and faq not in "".join(parts):
        parts.append(faq if faq.endswith("。") else faq + "。")

    ep = first_exam_points(row, 2)
    if ep:
        ep_plain = ep.rstrip("。")
        generic_ep = ep_plain in (
            "誤答型を分類する",
            "誤答型を分類",
            "原因を1行で記録",
            "同型問題を連続再演習する",
        )
        if ep_plain not in "".join(parts) and not generic_ep:
            parts.append(f"押さえる論点：{ep_plain}。")

    cm = norm(row.get("common_mistakes", ""))
    if cm:
        first = cm.split(";")[0].strip()
        if len(first) >= 10 and first not in GENERIC_COMMON_MISTAKES:
            if first not in "".join(parts):
                parts.append(f"誤答では{first.rstrip('。')}。")

    if not parts and title:
        parts.append(f"{title}で出やすい誤答の型と正しい整理の仕方を、表と過去問で確認できます。")

    return clamp("".join(parts))


def summarize_glossary_short(row: dict[str, str]) -> str:
    term = norm(row.get("term"))
    if not term:
        return norm(row.get("short_def"))

    if term in KNOWN_DEFINITIONS:
        return KNOWN_DEFINITIONS[term].rstrip("。") + "。"

    key_summary = norm(row.get("key_summary"))
    if key_summary:
        m = re.search(r"一言で言うと、(.+?)。", key_summary)
        if m:
            plain = m.group(1).strip()
            if plain and not _is_generic_index_snippet(plain, term):
                if plain.startswith(term):
                    return plain if plain.endswith("。") else plain + "。"
                return f"{term}は、{plain.rstrip('。')}。"

    article_lead = norm(row.get("article_lead"))
    if article_lead:
        first = split_sents(article_lead)
        if first and len(first[0]) >= 12 and not is_generic(first[0]):
            s = first[0]
            if not _is_generic_index_snippet(s, term):
                return s if s.endswith("。") else s + "。"

    body = norm(row.get("term_detail_body"))
    if body:
        first = split_sents(body)
        if first and len(first[0]) >= 12:
            s = first[0]
            if not _is_generic_index_snippet(s, term) and not is_generic(s):
                return s if s.endswith("。") else s + "。"

    src = parse_source(term, norm(row.get("definition")))
    if src.core and not is_generic(src.core):
        return src.core if src.core.endswith("。") else src.core + "。"

    snippet = terms_index_snippet(row)
    if snippet and not _is_generic_index_snippet(snippet, term):
        return snippet if snippet.endswith("。") else snippet + "。"

    ep = first_exam_points(row, 1)
    if ep:
        return clamp(f"{term}は、{ep.rstrip('。')}が試験で問われやすいポイントです。")

    return norm(row.get("short_def")) or f"{term}の意味と試験での出方を解説します。"


def needs_compare_rewrite(summary: str, row: dict[str, str] | None = None) -> bool:
    s = norm(summary)
    if not s or summary_is_generic(s, "compare"):
        return True
    if s.endswith("整理します。") and "違い" in s and len(s) < 55:
        return True
    if row and has_placeholder_compare(row) and "違い" not in s:
        return True
    return False


def needs_mistake_rewrite(summary: str, row: dict[str, str] | None = None) -> bool:
    s = norm(summary)
    if not s or summary_is_generic(s, "mistakes"):
        return True
    if s.endswith("整理します。") and len(s) < 70:
        return True
    if row and is_generic_mistake_patterns(row) and "典型" not in s and "例：" not in s:
        return True
    return False


def needs_number_rewrite(summary: str, row: dict[str, str] | None = None) -> bool:
    s = norm(summary)
    if not s or summary_is_generic(s, "numbers"):
        return True
    if "整理します" in s and len(s) < 55:
        return True
    if row and is_placeholder_number_items(row) and "代表値は" in s:
        return True
    return False


def needs_glossary_rewrite(row: dict[str, str]) -> bool:
    term = norm(row.get("term"))
    short = norm(row.get("short_def"))
    if not short:
        return True
    if _is_generic_index_snippet(short, term):
        return True
    if is_generic(short):
        return True
    defn = norm(row.get("definition"))
    if defn and short in defn[: max(len(short) + 5, 40)]:
        if "に関わる用語です" in defn or "まず「" in defn:
            return True
    return False


def enrich_glossary(dry_run: bool = False, force: bool = False) -> tuple[int, int]:
    fieldnames, rows = load_csv(GLOSSARY_CSV)
    changed = 0
    for row in rows:
        if not force and not needs_glossary_rewrite(row):
            continue
        new = summarize_glossary_short(row)
        old = norm(row.get("short_def"))
        if new != old:
            row["short_def"] = new
            changed += 1
    if changed and not dry_run:
        write_csv(GLOSSARY_CSV, fieldnames, rows)
    return changed, len(rows)


def enrich_compare(
    dry_run: bool = False,
    glossary: dict[str, str] | None = None,
    force: bool = False,
) -> tuple[int, int]:
    glossary = glossary or load_glossary_short_index()
    fieldnames, rows = load_csv(COMPARE_CSV)
    seen: dict[str, int] = {}
    changed = 0
    for row in rows:
        old = norm(row.get("summary"))
        if not force and not needs_compare_rewrite(old, row) and len(old) >= 40 and not is_generic_lead(old):
            seen[old] = seen.get(old, 0) + 1
            continue
        new = summarize_compare(row, glossary)
        if seen.get(old, 0) >= 2 or seen.get(new, 0) >= 1:
            new = summarize_compare(row, glossary)
        if new != old:
            row["summary"] = new
            changed += 1
        seen[new] = seen.get(new, 0) + 1
    if changed and not dry_run:
        write_csv(COMPARE_CSV, fieldnames, rows)
    return changed, len(rows)


def enrich_numbers(dry_run: bool = False, force: bool = False) -> tuple[int, int]:
    fieldnames, rows = load_csv(NUMBERS_CSV)
    anchors = [r for r in rows if not is_placeholder_number_items(r)]
    seen: dict[str, int] = {}
    changed = 0
    for row in rows:
        old = norm(row.get("summary"))
        if not force and not needs_number_rewrite(old, row) and len(old) >= 45:
            seen[old] = seen.get(old, 0) + 1
            continue
        new = summarize_numbers(row, anchors)
        if seen.get(old, 0) >= 2:
            title = clean_article_title(row.get("title", ""))
            if title and title not in new:
                new = clamp(f"{title}。{new}")
        if new != old:
            row["summary"] = new
            changed += 1
        seen[new] = seen.get(new, 0) + 1
    if changed and not dry_run:
        write_csv(NUMBERS_CSV, fieldnames, rows)
    return changed, len(rows)


def enrich_mistakes(dry_run: bool = False, force: bool = False) -> tuple[int, int]:
    fieldnames, rows = load_csv(MISTAKES_CSV)
    anchors = [r for r in rows if not is_generic_mistake_patterns(r)]
    seen: dict[str, int] = {}
    changed = 0
    for row in rows:
        old = norm(row.get("summary"))
        if not force and not needs_mistake_rewrite(old, row) and len(old) >= 50 and "整理します" not in old:
            seen[old] = seen.get(old, 0) + 1
            continue
        new = summarize_mistake(row, anchors)
        if seen.get(old, 0) >= 2:
            title = clean_article_title(row.get("title", ""))
            if title and title not in new:
                new = clamp(f"{title}。{new}")
        if new != old:
            row["summary"] = new
            changed += 1
        seen[new] = seen.get(new, 0) + 1
    if changed and not dry_run:
        write_csv(MISTAKES_CSV, fieldnames, rows)
    return changed, len(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description="一覧用の定義・概要を記事ベースで更新")
    parser.add_argument("--dry-run", action="store_true", help="CSVを書き込まない")
    parser.add_argument(
        "--glossary-force",
        action="store_true",
        help="用語の short_def を記事ベースで全件再生成",
    )
    parser.add_argument(
        "--force-all",
        action="store_true",
        help="比較・数値・誤答の概要も全件再生成",
    )
    args = parser.parse_args()
    dry = args.dry_run
    force_hub = args.force_all

    g_changed, g_total = enrich_glossary(dry, force=args.glossary_force or force_hub)
    glossary = load_glossary_short_index()
    c_changed, c_total = enrich_compare(dry, glossary, force=force_hub)
    n_changed, n_total = enrich_numbers(dry, force=force_hub)
    m_changed, m_total = enrich_mistakes(dry, force=force_hub)

    print(
        f"glossary: {g_changed}/{g_total} updated\n"
        f"compare:  {c_changed}/{c_total} updated\n"
        f"numbers:  {n_changed}/{n_total} updated\n"
        f"mistakes: {m_changed}/{m_total} updated"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
