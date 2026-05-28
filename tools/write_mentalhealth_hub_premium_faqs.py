# -*- coding: utf-8 -*-
"""メンタルヘルスII種 知識ハブ：比較スラッグ向けプレミアムFAQ."""

from tools.hub_slug_maps import COMPARE_SLUGS
from tools.write_mentalhealth_hub_s30 import _OFFICIAL


def _qa(slug: str) -> list[tuple[str, str]]:
    label = slug.replace("-", " / ")
    return [
        (
            "このテーマで最初に確認するポイントは？",
            f"{label} の学習では、制度の目的・主体・実施タイミングを最初に固定してください。"
            "II種では似た制度名の入替え肢が多く、用語だけ暗記すると誤答につながるため、比較軸を言語化してから過去問へ進むのが有効です。",
        ),
        (
            "問題文の読み方で注意する点は？",
            "数値だけを見る前に、誰に適用される制度かを確認します。主体と対象規模を誤ると正しい数字でも不正解になるため、"
            "『主語→条件→数値』の順で読む習慣を固定してください。復習時は誤答理由を必ず1行残します。",
        ),
        (
            "実務イメージを持つべきですか？",
            "持つべきです。II種は職場対応の文脈で問われるため、相談受付、面接連携、復職支援の流れを時系列で説明できると得点が安定します。"
            "比較表・数値早見・誤答パターンを往復して、判断の根拠を明確にしてください。",
        ),
        (
            "公式情報はどこで再確認しますか？",
            "受験要項、試験実施団体の公式案内、関連法令の一次情報で確認してください。"
            "特に人数基準・合格基準・実施要件は更新が入りやすいため、直前期だけでなく週次で更新有無を照合する運用が安全です。"
            + _OFFICIAL,
        ),
    ]


PREMIUM_FAQS: dict[str, list[tuple[str, str]]] = {slug: _qa(slug) for slug in COMPARE_SLUGS}


def apply_premium_faqs(row: dict[str, str]) -> dict[str, str]:
    slug = row.get("slug", "")
    if slug not in PREMIUM_FAQS:
        return row
    row = dict(row)
    for i, (q, a) in enumerate(PREMIUM_FAQS[slug], start=1):
        row[f"faq_{i}_question"] = q
        row[f"faq_{i}_answer"] = a
    return row


def apply_all(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [apply_premium_faqs(r) for r in rows]
