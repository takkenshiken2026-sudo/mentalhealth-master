#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""試験ガイド本文生成用のサイト別コンテキスト（site-config から構築）。"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class GuideSiteContext:
    exam: str
    brand: str
    exam_short: str
    official: str
    org: str
    scope_fields: tuple[str, ...]
    field_slug_map: dict[str, str]
    textbook_hint: str
    role_label: str
    misconception_line: str
    numeric_hint: str
    faq_subject_hint: str
    basics_terms: str
    cross_field_example: str
    hub_slug_map: dict[str, str] = field(default_factory=dict)
    exam_aliases: tuple[str, ...] = ()

    @property
    def scope_label(self) -> str:
        n = len(self.scope_fields)
        return f"{n}分野" if n <= 9 else "出題分野"

    def strip_exam_from_title(self, part: str) -> str:
        text = part.strip()
        for alias in sorted(self.exam_aliases, key=len, reverse=True):
            for prefix in (f"{alias}の", f"{alias}｜", f"{alias}|"):
                if text.startswith(prefix):
                    text = text[len(prefix) :].strip()
        return text


_CTX: GuideSiteContext | None = None


def get_context() -> GuideSiteContext:
    if _CTX is None:
        raise RuntimeError("guide content context not initialized; call init_guide_content(root) first")
    return _CTX


def init_guide_content(root: Path) -> GuideSiteContext:
    global _CTX
    root = root.resolve()
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from tools.site_config import (  # noqa: WPS433
        brand_name,
        exam_name,
        fields,
        official_organization,
        primary_external_link,
    )

    exam = exam_name().replace("（プレースホルダー）", "").strip()
    brand = brand_name().strip()
    link = primary_external_link()
    official = link.get("label") or "公式情報"
    org = official_organization() or link.get("label") or "試験実施機関"
    field_list = fields()
    field_slug_map = {f["id"]: f["name"] for f in field_list}
    scope = tuple(f["name"] for f in field_list)

    if "ボイラー" in exam or "ボイラー" in brand:
        _CTX = GuideSiteContext(
            exam=exam,
            brand=brand,
            exam_short="2級ボイラー",
            official=official,
            org=org,
            scope_fields=scope
            or (
                "ボイラーの構造に関する知識",
                "ボイラーの取扱いに関する知識",
                "燃料及び燃焼に関する知識",
                "関係法令",
            ),
            field_slug_map=field_slug_map
            or {
                "structure": "ボイラーの構造に関する知識",
                "handling": "ボイラーの取扱いに関する知識",
                "fuel": "燃料及び燃焼に関する知識",
                "law": "関係法令",
            },
            textbook_hint="2級ボイラー技士向けのテキスト・問題集",
            role_label="ボイラー技士・作業者",
            misconception_line=(
                "「構造と取扱いの混同」「燃焼制御と水処理の取り違え」"
                "「安全装置の作動条件の数値ミス」などが誤答の温床になります。"
            ),
            numeric_hint="使用圧力、安全弁、水位、燃焼制御、検査",
            faq_subject_hint="事業者・ボイラー技士・検査機関",
            basics_terms="ボイラー構造、燃焼制御、水処理、安全装置、関係法令",
            cross_field_example="構造の知識が取扱い・燃焼問題の前提になる",
            hub_slug_map={
                "boiler-structure": "ボイラー構造",
                "combustion-control": "燃焼制御",
                "water-treatment": "水処理",
            },
            exam_aliases=(exam, brand, "2級ボイラー", "ボイラー技士", "ボイラー"),
        )
    elif "危険物" in exam or "乙種" in exam or "乙4" in brand:
        _CTX = GuideSiteContext(
            exam=exam,
            brand=brand,
            exam_short="乙4" if "乙4" in brand else "危険物",
            official=official,
            org=org,
            scope_fields=scope or ("法令・制度", "物性・化学", "火災・消火・漏えい"),
            field_slug_map=field_slug_map
            or {"law": "法令・制度", "rights": "物性・化学", "limit": "火災・消火・漏えい"},
            textbook_hint="危険物取扱者（乙4）向けの教本・問題集",
            role_label="危険物取扱者・指定者",
            misconception_line=(
                "「類別の取り違え」「指定数量と最大数量の混同」「消火方法の誤選択」"
                "「保安規程と届出の混同」などが誤答の温床になります。"
            ),
            numeric_hint="指定数量500kg、引火点、類別ごとの消火剤",
            faq_subject_hint="事業者・危険物取扱者・消防法上の主体",
            basics_terms="類別、指定数量、引火点、消火方法、保安規程",
            cross_field_example="物性・化学の知識が火災・消火問題の前提になる",
            hub_slug_map={
                "specified-quantity": "指定数量",
                "flash-point": "引火点",
                "class-category": "類別",
                "fire-extinguishing": "消火方法",
                "safety-regulations": "保安規程",
            },
            exam_aliases=(exam, brand, "危険物取扱者", "乙種第4類", "乙4", "危険物"),
        )
    elif "第二種衛生" in exam or "二衛" in brand:
        _CTX = GuideSiteContext(
            exam=exam,
            brand=brand,
            exam_short="第二種衛生管理者",
            official=official,
            org=org,
            scope_fields=scope or ("関係法令", "労働衛生", "労働生理"),
            field_slug_map=field_slug_map
            or {"law": "関係法令", "rights": "労働衛生", "limit": "労働生理"},
            textbook_hint="第二種衛生管理者向けのテキスト・問題集",
            role_label="衛生管理者・選任者",
            misconception_line=(
                "「第二種の選任要件と第一種の混同」「衛生管理者と産業医の役割取り違え」"
                "「作業環境測定の頻度・対象の数値ミス」などが誤答の温床になります。"
            ),
            numeric_hint="選任数、作業環境測定、健康診断の頻度、温熱基準",
            faq_subject_hint="事業者・衛生管理者・産業医",
            basics_terms="作業環境測定、健康診断、選任・専任、化学物質、温熱",
            cross_field_example="関係法令の知識が労働衛生問題の前提になる",
            hub_slug_map={
                "health-supervisor": "衛生管理者",
                "work-environment-measurement": "作業環境測定",
                "health-examination": "健康診断",
            },
            exam_aliases=(exam, brand, "第二種衛生管理者", "衛生管理者", "二衛", "第二種"),
        )
    elif "第一種衛生" in exam or "一衛" in brand:
        _CTX = GuideSiteContext(
            exam=exam,
            brand=brand,
            exam_short="第一種衛生管理者",
            official=official,
            org=org,
            scope_fields=scope
            or (
                "関係法令（有害業務）",
                "関係法令（有害以外）",
                "労働衛生（有害業務）",
                "労働衛生（有害以外）",
                "労働生理",
            ),
            field_slug_map=field_slug_map
            or {
                "law-harm": "関係法令（有害業務）",
                "law-other": "関係法令（有害以外）",
                "eisei-harm": "労働衛生（有害業務）",
                "eisei-other": "労働衛生（有害以外）",
                "physio": "労働生理",
            },
            textbook_hint="第一種衛生管理者向けのテキスト・問題集",
            role_label="衛生管理者・選任者",
            misconception_line=(
                "「第一種と第二種の混同」「衛生管理者と産業医の役割取り違え」"
                "「作業環境測定の頻度・対象の数値ミス」などが誤答の温床になります。"
            ),
            numeric_hint="選任数50人、作業環境測定6か月、健康診断の頻度、温熱基準",
            faq_subject_hint="事業者・衛生管理者・産業医・安全衛生委員会",
            basics_terms="作業環境測定、健康診断、選任・専任、化学物質、温熱・照明",
            cross_field_example="関係法令の知識が労働衛生問題の前提になる",
            hub_slug_map={
                "health-supervisor": "衛生管理者",
                "work-environment-measurement": "作業環境測定",
                "health-examination": "健康診断",
                "chemical-substance": "化学物質",
                "appointment-requirement": "選任・専任",
            },
            exam_aliases=(exam, brand, "第一種衛生管理者", "衛生管理者", "一衛", "第一種"),
        )
    elif "賃貸不動産経営" in exam or "賃管" in brand:
        _CTX = GuideSiteContext(
            exam=exam,
            brand=brand,
            exam_short="賃貸不動産経営管理士",
            official=official,
            org=org,
            scope_fields=scope or ("賃管法令・制度", "契約・実務", "設備・税務・その他"),
            field_slug_map=field_slug_map
            or {"law": "賃管法令・制度", "rights": "契約・実務", "limit": "設備・税務・その他"},
            textbook_hint="賃管向けのテキスト・過去問",
            role_label="賃貸不動産経営管理士・受験者",
            misconception_line=(
                "「原状回復と通常損耗の混同」「敷金返還と修繕費の取り違え」"
                "「更新と再契約の混同」などが誤答の温床になります。"
            ),
            numeric_hint="敷金、礼金、更新料、原状回復、建物設備",
            faq_subject_hint="貸主・借主・管理業者・登録",
            basics_terms="原状回復、敷金、賃貸借契約、更新、建物設備",
            cross_field_example="法令の知識が契約・実務問題の前提になる",
            hub_slug_map={
                "rental-contract": "賃貸借契約",
                "restoration": "原状回復",
                "deposit": "敷金",
            },
            exam_aliases=(exam, brand, "賃貸不動産経営管理士", "賃管", "賃貸管理"),
        )
    elif "マンション管理士" in exam or "マ管" in brand:
        _CTX = GuideSiteContext(
            exam=exam,
            brand=brand,
            exam_short="マンション管理士",
            official=official,
            org=org,
            scope_fields=scope
            or ("区分所有法・関連法令", "管理組合運営・会計・実務", "建物・設備・維持保全"),
            field_slug_map=field_slug_map
            or {"law": "区分所有法・関連法令", "rights": "管理組合運営・会計・実務", "limit": "建物・設備・維持保全"},
            textbook_hint="マンション管理士向けのテキスト・過去問",
            role_label="マンション管理士・受験者",
            misconception_line=(
                "「管理組合と理事会の混同」「区分所有法と民法の取り違え」"
                "「修繕積立金の計算ミス」などが誤答の温床になります。"
            ),
            numeric_hint="修繕積立金、管理費、総会決議、管理委託契約、登録",
            faq_subject_hint="管理組合・理事会・管理業者・登録",
            basics_terms="区分所有法、管理規約、修繕積立金、管理委託契約、総会",
            cross_field_example="区分所有法の知識が管理組合運営問題の前提になる",
            hub_slug_map={
                "condominium-management": "区分所有法",
                "repair-reserve": "修繕積立金",
                "general-meeting": "総会",
            },
            exam_aliases=(exam, brand, "マンション管理士", "マ管", "マンション管理"),
        )
    elif "運行管理者" in exam or "運管" in brand:
        _CTX = GuideSiteContext(
            exam=exam,
            brand=brand,
            exam_short="運行管理者",
            official=official,
            org=org,
            scope_fields=scope
            or (
                "貨物自動車運送事業法関係",
                "道路運送車両法関係",
                "道路交通法関係",
                "労働基準法関係",
                "実務上の知識及び能力",
            ),
            field_slug_map=field_slug_map
            or {
                "jigyo": "貨物自動車運送事業法関係",
                "vehicle": "道路運送車両法関係",
                "traffic": "道路交通法関係",
                "labor": "労働基準法関係",
                "practice": "実務上の知識及び能力",
            },
            textbook_hint="運行管理者向けのテキスト・過去問",
            role_label="運行管理者・選任者",
            misconception_line=(
                "「一般・貨物・旅客の選任要件の混同」「運行管理者と整備管理者の取り違え」"
                "「運転時間・点呼の数値ミス」などが誤答の温床になります。"
            ),
            numeric_hint="運行管理者選任、運転時間、点呼、整備記録、運行計画",
            faq_subject_hint="事業者・運行管理者・整備管理者・運転者",
            basics_terms="運行管理者選任、点呼、運転時間、整備、運行計画",
            cross_field_example="事業法の知識が道路交通法・実務問題の前提になる",
            hub_slug_map={
                "operation-manager": "運行管理者",
                "roll-call": "点呼",
                "driving-hours": "運転時間",
            },
            exam_aliases=(exam, brand, "運行管理者", "運管", "運送管理"),
        )
    elif "管理業務主任者" in exam or "管業" in brand:
        _CTX = GuideSiteContext(
            exam=exam,
            brand=brand,
            exam_short="管理業務主任者",
            official=official,
            org=org,
            scope_fields=scope
            or (
                "民法・借地借家法",
                "標準管理規約",
                "建築・設備",
                "区分所有法",
                "会計・税務",
                "管理適正化法",
                "品確法・建替円滑化法等",
                "判例・横断総合",
                "標準管理委託契約書・指針",
                "宅建業法",
            ),
            field_slug_map=field_slug_map
            or {
                "civil": "民法・借地借家法",
                "kuhyo": "標準管理規約",
                "building": "建築・設備",
                "condo": "区分所有法",
                "accounting": "会計・税務",
                "tekisei": "管理適正化法",
                "hinkaku": "品確法・建替円滑化法等",
                "cross": "判例・横断総合",
                "itaku": "標準管理委託契約書・指針",
                "takken": "宅建業法",
            },
            textbook_hint="管理業務主任者向けのテキスト・過去問",
            role_label="管理業務主任者・受験者",
            misconception_line=(
                "「管理組合と理事会の混同」「区分所有法と民法の取り違え」"
                "「修繕積立金の計算ミス」などが誤答の温床になります。"
            ),
            numeric_hint="修繕積立金、管理費、総会決議、管理委託契約、登録",
            faq_subject_hint="管理組合・理事会・管理業者・登録",
            basics_terms="区分所有法、管理規約、修繕積立金、管理委託契約、総会・理事会",
            cross_field_example="区分所有法の知識が管理規約・会計問題の前提になる",
            hub_slug_map={
                "condominium-management": "区分所有法",
                "management-contract": "管理委託契約",
                "repair-reserve": "修繕積立金",
                "general-meeting": "総会",
            },
            exam_aliases=(exam, brand, "管理業務主任者", "管業"),
        )
    elif "宅建" in exam or "宅地建物" in exam or "宅建" in brand:
        _CTX = GuideSiteContext(
            exam=exam,
            brand=brand,
            exam_short="宅建",
            official=official,
            org=org,
            scope_fields=scope or ("権利関係", "宅建業法", "法令上の制限", "税・その他"),
            field_slug_map=field_slug_map
            or {
                "rights": "権利関係",
                "law": "宅建業法",
                "limit": "法令上の制限",
                "tax": "税・その他",
            },
            textbook_hint="宅建向けのテキスト・一問一答・過去問",
            role_label="宅地建物取引士・受験者",
            misconception_line=(
                "「35条書面と37条書面の混同」「媒介と代理の取り違え」"
                "「重要事項説明の記載漏れ」などが誤答の温床になります。"
            ),
            numeric_hint="35条書面、37条書面、重要事項説明、媒介手数料、登録免許税",
            faq_subject_hint="宅建業者・取引士・免許行政",
            basics_terms="重要事項説明、35条書面、媒介契約、宅建業免許、都市計画法",
            cross_field_example="権利関係の知識が宅建業法問題の前提になる",
            hub_slug_map={
                "important-matters-explanation": "重要事項説明",
                "article-35-document": "35条書面",
                "article-37-document": "37条書面",
                "mediation-contract": "媒介契約",
                "license": "宅建業免許",
            },
            exam_aliases=(exam, brand, "宅建", "宅地建物取引士"),
        )
    elif "メンタル" in exam or "メンタル" in brand:
        _CTX = GuideSiteContext(
            exam=exam,
            brand=brand,
            exam_short="メンタルヘルス二種",
            official=official,
            org=org,
            scope_fields=scope
            or (
                "メンタルヘルスケアの意義と管理監督者の役割",
                "ストレスおよびメンタルヘルスに関する基礎知識",
                "職場環境等の評価および改善の方法",
                "個々の労働者への配慮",
                "労働者からの相談への対応",
                "社内のメンタルヘルス対策の推進",
                "関連法令等",
            ),
            field_slug_map=field_slug_map,
            textbook_hint="公式テキスト（ラインケアコース）",
            role_label="管理監督者",
            misconception_line=(
                "「管理監督者が診断する」「休職勧奨＝解雇」"
                "「ストレスチェック結果を個別に上司が全部見る」など、現場イメージと制度のズレが誤答の温床になります。"
            ),
            numeric_hint="面接指導の時間、ストレスチェックの対象人数",
            faq_subject_hint="事業者・管理監督者・産業医",
            basics_terms="ラインケア、安全配慮義務、合理的配慮",
            cross_field_example="相談対応の領域は、個別配慮や職場環境評価とセットで出題される",
            hub_slug_map={
                "line-care": "ラインケア",
                "stress-check": "ストレスチェック",
                "power-harassment": "パワーハラスメント",
                "sexual-harassment": "セクシュアルハラスメント",
                "reasonable-accommodation": "合理的配慮",
                "safety-consideration": "安全配慮義務",
                "occupational-physician": "産業医",
                "active-listening": "傾聴",
                "eap-guide": "EAP",
            },
            exam_aliases=(exam, brand, "メンタルヘルス二種", "メンタルヘルス", "II種", "二種"),
        )
    else:
        _CTX = GuideSiteContext(
            exam=exam or brand,
            brand=brand,
            exam_short=brand.replace("マスター", "").strip() or brand,
            official=official,
            org=org,
            scope_fields=scope or ("出題分野1", "出題分野2"),
            field_slug_map=field_slug_map,
            textbook_hint="公式テキスト・問題集",
            role_label="受験者",
            misconception_line="用語の混同や数値の取り違えが誤答の温床になります。",
            numeric_hint="試験要項の数値・期限",
            faq_subject_hint="試験要項上の主体",
            basics_terms="重要用語",
            cross_field_example="分野をまたぐ問題にも慣れておくと安心です",
            exam_aliases=(exam, brand),
        )
    return _CTX


def field_name_from_slug(slug: str) -> str | None:
    ctx = get_context()
    m = re.match(r"field-([a-z0-9-]+)-", slug)
    if not m:
        return None
    fid = m.group(1)
    return ctx.field_slug_map.get(fid, fid.replace("-", " "))


def topic_from_row(row: dict[str, str]) -> str:
    ctx = get_context()
    title = (row.get("title") or "").strip()
    slug = (row.get("slug") or "").strip()
    if "｜" in title:
        parts = [p.strip() for p in title.split("｜") if p.strip()]
        for part in reversed(parts):
            cleaned = ctx.strip_exam_from_title(part)
            if len(cleaned) >= 4 and not re.fullmatch(r"[a-z0-9 -]+", cleaned, re.I):
                return cleaned
    elif "|" in title:
        title = title.split("|", 1)[-1].strip()
    title = ctx.strip_exam_from_title(title)
    if len(title) >= 4:
        return title
    from tools.guide_catalog_batch import topic_from_row as _catalog_topic_from_row
    return _catalog_topic_from_row(row)
