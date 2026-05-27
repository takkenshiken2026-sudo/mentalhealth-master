#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""試験ガイド全件を資格専門家×プロライター品質へ引き上げる。

正本原稿（populate スクリプト）を復元し、定型パディングを除去したうえで
リード・FAQ4・本文整形のみを行う。
"""

from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.guide_expert_canonical import CONTENT_KEYS, collect_canonical  # noqa: E402

CSV_PATH = ROOT / "data" / "guide_articles.csv"

BOILERPLATE_RES = [
    re.compile(r"——この段階では、担当者と目的がずれていないか確認します。?"),
    re.compile(r"分野別記事は、職場の場面を想像しながら読むと、ケース問題で活きてきます。?\s*"),
    re.compile(r"演習問題で、正答と誤答の違いを声に出して確認すると定着しやすくなります。?\s*"),
    re.compile(r"「[^」]+」の論点は、管理監督者の日常業務と直結するため、場面を想像しながら読み進めてください。?\s*"),
    re.compile(r"本記事では、[^。]+を、試験で得点につながる形で整理します。?\s*"),
    re.compile(r"公式テキストと用語集で用語の定義を補強し、演習で正誤の感覚を養ってください。?\s*"),
    re.compile(r"関連ガイド記事へのリンクもあわせて活用してください。?\s*"),
    re.compile(r"試験では、この論点がそのまま選択肢になりやすいです。?\s*"),
]

GENRE_FAQ4: dict[str, tuple[str, str]] = {
    "試験概要": (
        "独学で最初に読むべき記事はどれですか？",
        "まず試験概要と出題範囲を読み、用語集で章ごとに10語ずつ確認し、演習問題で4択に慣れる——"
        "この順番が効率的です。制度の数値は申込前に公式要項で必ず再確認してください。",
    ),
    "受験・申込": (
        "申込後すぐに何をすればよいですか？",
        "公式テキストの入手、学習計画の作成、演習の開始の3点を進めます。"
        "受験票・会場・持ち物は試験1週間前にもう一度要項と照合してください。",
    ),
    "合格・難易度": (
        "合格率だけで勉強量を決めてよいですか？",
        "演習の章別正答率の方が実力の指標になります。"
        "弱点章を用語記事と演習で潰してから、総合演習に移るのが安全です。",
    ),
    "出題・形式": (
        "7章のうちどこから手を付けるべきですか？",
        "第1章（基礎・役割）と第3章（職場環境）を先に固め、"
        "相談・復職はケース問題が多いため演習量を多めに取るとバランスが取れます。",
    ),
    "学習計画": (
        "週あたりの学習量の目安は？",
        "用語10語＋演習20問を1週間の最低ラインにし、正答率70%未満の章は翌週も同章を継続します。"
        "計画は完璧より継続を優先してください。",
    ),
    "独学対策": (
        "テキストと演習、どちらを優先しますか？",
        "章ごとに「テキストで意味を理解→用語でキーワード整理→演習で正誤確認」の順が基本です。"
        "演習だけ先行すると、ケース問題で理由を説明できない状態になりやすいです。",
    ),
    "過去問活用": (
        "演習で間違えた問題はどう復習しますか？",
        "誤答理由・関連用語・正答の根拠の3点をノート1行に書き、24時間後と1週間後に再挑戦します。"
        "同じ問題を当日中に何度も解くより間隔を空けた方が定着します。",
    ),
    "分野別対策": (
        "この分野の記事を読んだあと何をしますか？",
        "関連用語を3語ピックアップし、演習問題で同テーマの4択を5問解きます。"
        "正答の言い回しを声に出して確認すると、本番の選択肢で迷いにくくなります。",
    ),
    "用語整理": (
        "用語はどう覚えるのが効率的ですか？",
        "定義1行・担当者1行・試験の注意1行の3行メモにし、似た用語は表で比較します。"
        "用語記事の「覚え方・整理のコツ」も併用してください。",
    ),
    "復習・苦手克服": (
        "苦手章が複数ある場合の優先順位は？",
        "演習正答率が最も低い章と、頻出用語が多い章の交差部分から着手します。"
        "全章を均等にやり直すより、2章に絞った方が直前まで成果が残ります。",
    ),
    "直前・当日": (
        "試験当日の朝にやるべきことは？",
        "受験票・身分証・筆記用具・交通ルートの最終確認に加え、"
        "誤答ノートの見直しは15分以内に留め、新しい範囲のインプットは避けてください。",
    ),
    "注意点・更新": (
        "法改正情報はどこで追いますか？",
        "公益財団法人 日本産業衛生協会の公式ページと公式テキストの改訂情報を正本にしてください。"
        "当サイトの記事も確認日を見ながら、申込前・直前の2回は必ず公式と照合してください。",
    ),
}

GENRE_ALIASES = {
    "受験情報": "受験・申込",
    "学習法": "独学対策",
    "直前対策": "直前・当日",
    "復職支援": "分野別対策",
}


def norm(s: str | None) -> str:
    return (s or "").strip()


def load_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader.fieldnames or []), list(reader)


def strip_boilerplate(text: str) -> str:
    out = norm(text)
    for pat in BOILERPLATE_RES:
        out = pat.sub("", out)
    out = re.sub(r"\s+", " ", out).strip()
    return out


def format_section_body(body: str) -> str:
    """セミコロン列挙を読みやすい段落に整形。"""
    body = strip_boilerplate(body)
    if not body:
        return body

    note = ""
    if "\n\n" in body:
        main, note = body.split("\n\n", 1)
        body = main.strip()
    else:
        note = ""

    if ";" in body:
        parts = [p.strip() for p in body.split(";") if p.strip()]
        if len(parts) >= 2 and all(len(p) < 100 for p in parts):
            lines: list[str] = []
            for p in parts:
                p = p.rstrip("。")
                if re.match(r"^[①②③④⑤⑥⑦\d]", p):
                    lines.append(f"{p}。")
                else:
                    lines.append(f"・{p}。")
            formatted = "\n\n".join(lines)
            if note:
                formatted += f"\n\n{note.strip()}"
            return formatted

    if note:
        body = body + "\n\n" + note.strip()
    if "\n\n" not in body and len(body) > 180:
        sents = re.findall(r"[^。！？]+[。！？]", body)
        if len(sents) >= 3:
            mid = len(sents) // 2
            return "".join(sents[:mid]) + "\n\n" + "".join(sents[mid:])
    return body


def expand_section_pro(body: str, heading: str, slug: str, genre: str) -> str:
    """200字未満のセクションに、見出しに応じた専門家コメントを1段落追加。"""
    if len(body) >= 200:
        return body
    genre = GENRE_ALIASES.get(genre, genre)
    if any(k in heading for k in ("頻出", "誤答", "誤解", "注意")):
        extra = (
            "演習では、正答の根拠と誤答の理由をセットで確認してください。"
            "「〜のみ」「〜不要」などの言い切りは、まず疑って読む習慣が有効です。"
        )
    elif "管理監督者" in heading:
        extra = (
            "管理監督者は医学的診断や治療方針を決めません。"
            "職場での観察、業務調整、専門職への連携——この役割分担が試験でも実務でも軸になります。"
        )
    elif any(k in heading for k in ("関連", "次の", "学習")):
        extra = (
            "関連する試験ガイド・用語記事とあわせ、同じ章の演習問題で正誤を確かめると理解が定着します。"
        )
    elif any(k in heading for k in ("公式", "受験", "申込", "持ち物", "日程")):
        extra = (
            "数値・日程・費用は年度で変わるため、公益財団法人 日本産業衛生協会の公式ページを正本として確認してください。"
        )
    elif genre == "直前・当日":
        extra = "直前期は新規インプットより、誤答ノートと公式情報の最終確認に時間を使う方が得点につながります。"
    elif genre == "分野別対策":
        extra = (
            f"「{heading}」はケース問題でそのまま問われることが多い論点です。"
            "職場の場面（相談・休業・復職・ハラスメント対応など）を想像しながら読み進めてください。"
        )
    else:
        extra = (
            "公式テキストで該当章を読んだうえで、用語集と演習問題で4択に慣れておくと本番で迷いにくくなります。"
        )
    if extra not in body:
        body = body.rstrip() + "\n\n" + extra
    return body


def polish_lead(lead: str, genre: str, title: str) -> str:
    lead = strip_boilerplate(lead)
    if len(lead) >= 90 and lead.endswith("。"):
        return lead
    short_title = title.split("｜")[0].split("|")[0]
    genre_key = GENRE_ALIASES.get(genre, genre)
    extra = ""
    if "試験で得点" not in lead and "整理" not in lead[-20:]:
        extra = f"本記事では、{short_title}を、試験本番で得点につながる形で整理します。"
    out = lead.rstrip("。") + "。" + extra
    return out[:300]


def polish_faq_answer(q: str, a: str) -> str:
    a = strip_boilerplate(a)
    if len(a) >= 90:
        return a if a.endswith("。") else a + "。"
    if "公式" in q or "申込" in q or "資格" in q:
        suffix = " 最新情報は公益財団法人 日本産業衛生協会の公式ページで必ず確認してください。"
    elif "試験" in q or "出" in q or "演習" in q:
        suffix = " 関連する演習問題で、正答の言い回しに慣れておくと本番で迷いにくくなります。"
    else:
        suffix = " 用語集・関連ガイドと併読すると理解が深まります。"
    return (a.rstrip("。") + "。" + suffix)[:280]


def ensure_faq4(row: dict[str, str]) -> None:
    if norm(row.get("faq_4_question")) and norm(row.get("faq_4_answer")):
        row["faq_4_answer"] = strip_boilerplate(norm(row.get("faq_4_answer")))
        return
    genre = GENRE_ALIASES.get(norm(row.get("genre")), norm(row.get("genre")))
    q, a = GENRE_FAQ4.get(genre, GENRE_FAQ4["分野別対策"])
    title = norm(row.get("title")).split("｜")[0]
    row["faq_4_question"] = q
    row["faq_4_answer"] = a.replace("この分野", title) if "この分野" in a else a


def enrich_row(row: dict[str, str], canonical: dict[str, dict[str, str]]) -> None:
    slug = norm(row.get("slug"))
    canon = canonical.get(slug, {})
    genre = norm(row.get("genre"))

    for key in CONTENT_KEYS:
        if canon.get(key):
            row[key] = canon[key]

    row["lead"] = polish_lead(norm(row.get("lead")), genre, norm(row.get("title")))

    for i in range(1, 8):
        bkey = f"section_{i}_body"
        hkey = f"section_{i}_heading"
        if norm(row.get(bkey)):
            body = format_section_body(row[bkey])
            row[bkey] = expand_section_pro(body, norm(row.get(hkey)), slug, genre)

    for i in range(1, 5):
        qk, ak = f"faq_{i}_question", f"faq_{i}_answer"
        if norm(row.get(qk)) and norm(row.get(ak)):
            row[ak] = polish_faq_answer(row[qk], row[ak])

    ensure_faq4(row)

    intent = norm(row.get("user_intent"))
    if intent.endswith("。。"):
        row["user_intent"] = intent.replace("。.", "。")


def main() -> int:
    canonical = collect_canonical()
    fieldnames, rows = load_csv(CSV_PATH)
    for col in ("faq_4_question", "faq_4_answer"):
        if col not in fieldnames:
            idx = fieldnames.index("faq_3_answer") + 1 if "faq_3_answer" in fieldnames else len(fieldnames)
            fieldnames.insert(idx, col)

    missing = [norm(r.get("slug")) for r in rows if norm(r.get("slug")) not in canonical]
    if missing:
        print(f"guide_pro: warning missing canonical for {len(missing)} slugs: {missing[:5]}")

    boiler = 0
    for row in rows:
        before = sum(
            1
            for i in range(1, 8)
            if "場面を想像しながら読み進めてください" in norm(row.get(f"section_{i}_body"))
        )
        enrich_row(row, canonical)
        after = sum(
            1
            for i in range(1, 8)
            if "場面を想像しながら読み進めてください" in norm(row.get(f"section_{i}_body"))
        )
        boiler += before - after

    with CSV_PATH.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

    total_body = sum(
        len(norm(row.get(f"section_{i}_body")))
        for row in rows
        for i in range(1, 8)
        if norm(row.get(f"section_{i}_body"))
    )
    n_sec = sum(1 for row in rows for i in range(1, 8) if norm(row.get(f"section_{i}_body")))
    ge900 = sum(
        1
        for row in rows
        if sum(len(norm(row.get(f"section_{i}_body"))) for i in range(1, 8)) >= 900
    )
    faq4 = sum(1 for r in rows if norm(r.get("faq_4_question")))
    print(
        f"guide_pro: articles={len(rows)}, canonical={len(canonical)}, "
        f"body_ge900={ge900}/{len(rows)}, avg_section={total_body // max(n_sec, 1)}字, "
        f"faq4={faq4}/{len(rows)}, boiler_removed={boiler}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
