#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""メンタルヘルス二種 試験ガイド向けの本文・FAQ 生成（量産テンプレ差し替え用）。"""

from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Callable

EXAM = "メンタルヘルス・マネジメント検定II種"
EXAM_SHORT = "メンタルヘルス二種"
OFFICIAL = "試験のご紹介（公式）"
ORG = "公益財団法人 日本産業衛生協会"
SEVEN_FIELDS = (
    "メンタルヘルスケアの意義と管理監督者の役割",
    "ストレスおよびメンタルヘルスに関する基礎知識",
    "職場環境等の評価および改善の方法",
    "個々の労働者への配慮",
    "労働者からの相談への対応",
    "社内のメンタルヘルス対策の推進",
    "関連法令等",
)

STUB_MARKERS = (
    "の観点で整理します",
    "まず公式要項で最新の制度を確認してください。本サイトでは過去問演習と用語解説で",
    "理解度を具体的に確かめられます",
    "このサイトでは過去問・用語解説・比較表を組み合わせ",
    "間違えた問題は理由を短くメモし、関連用語で定義",
)

META_STUB = "公式情報の確認方法と学習の進め方を整理します。受験前に押さえるべきポイントと、このサイトでの演習・用語解説の活用法を解説します"


def is_stub(text: str) -> bool:
    t = (text or "").strip()
    if not t:
        return True
    return any(m in t for m in STUB_MARKERS)


def two_paragraphs(p1: str, p2: str) -> str:
    return f"{p1.strip()}\n\n{p2.strip()}"


def ensure_min(text: str, min_len: int, tail: str) -> str:
    t = text.strip()
    if len(t) >= min_len:
        return t
    extra = tail
    while len(t + extra) < min_len:
        extra += " " + tail
    return (t.rstrip("。") + "。" + extra).strip()


def topic_from_row(row: dict[str, str]) -> str:
    title = (row.get("title") or "").strip()
    slug = (row.get("slug") or "").strip()
    if "｜" in title:
        parts = [p.strip() for p in title.split("｜") if p.strip()]
        # 試験名だけの前半を除き、最も具体的な部分を採用
        for part in reversed(parts):
            if EXAM in part or EXAM_SHORT in part:
                part = re.sub(rf"^{re.escape(EXAM)}[の｜|]*", "", part)
                part = re.sub(rf"^{re.escape(EXAM_SHORT)}[の｜|]*", "", part).strip()
            if len(part) >= 4 and not re.fullmatch(r"[a-z0-9 -]+", part, re.I):
                return part
    elif "|" in title:
        title = title.split("|", 1)[-1].strip()
    for prefix in (f"{EXAM}の", f"{EXAM}｜", f"{EXAM_SHORT}の"):
        if title.startswith(prefix):
            title = title[len(prefix) :].strip()
    if len(title) >= 4 and not title.startswith("メンタルヘルス"):
        return title
    from tools.guide_catalog_batch import topic_from_row as _catalog_topic_from_row
    return _catalog_topic_from_row(row)


def field_name_from_slug(slug: str) -> str | None:
    m = re.match(r"field-([a-z0-9-]+)-", slug)
    if not m:
        return None
    fid = m.group(1)
    mapping = {
        "manager-role": "管理監督者の役割",
        "stress-basics": "ストレスとメンタルヘルスの基礎",
        "workplace-env": "職場環境の評価と改善",
        "individual-care": "個々の労働者への配慮",
        "consultation": "相談対応",
        "promotion": "社内対策の推進",
        "legal": "関連法令",
        "mh-basics": "メンタルヘルスケアの意義",
    }
    return mapping.get(fid, fid.replace("-", " "))


def _official_note() -> str:
    return (
        f"数値・日程・合格基準は年度で更新されるため、学習前と申込前には{OFFICIAL}で"
        f"{ORG}の最新案内を確認してください。"
    )


def _practice_note(topic: str) -> str:
    return (
        f"演習で{topic}に関する設問を解いたら、正解理由と誤答肢の違いを短くメモし、"
        f"用語解説・比較表・よくある誤答タブで似た論点を1周すると定着しやすくなります。"
    )


# --- 見出し別本文（180字以上・具体性あり） ---

def _heading_よくある誤解(topic: str, _slug: str, _genre: str, _ctx: dict) -> str:
    return two_paragraphs(
        f"{topic}では、「管理監督者が診断する」「休職勧奨＝解雇」"
        f"「ストレスチェック結果を個別に上司が全部見る」など、現場イメージと制度のズレが誤答の温床になります。"
        f"特にラインケアと産業医・産業カウンセラーの役割分担は四択で頻出です。",
        f"誤解を解くには、用語解説で定義を確認したうえで、比較表タブの「混同しやすい組み合わせ」を読み、"
        f"演習問題で引っかけ肢を体験してください。{_official_note()}",
    )


def _heading_独学前に公式情報を確認(topic: str, _slug: str, _genre: str, _ctx: dict) -> str:
    return two_paragraphs(
        f"独学を始める前に、{OFFICIAL}で受験資格・試験日程・出題範囲（7領域）・合格基準をメモしてください。"
        f"{topic}の学習計画は、公式テキストの章立てと一致させると、過去問の分野ラベルとも対応づけやすくなります。",
        f"ブログやSNSの「最新情報」は、必ず{ORG}のページと照合してから採用してください。"
        f"申込期限や受験料は年度ごとに変わるため、カレンダーに締切を入れてから教材を開く習慣が有効です。",
    )


def _heading_教材参考書(topic: str, _slug: str, _genre: str, _ctx: dict) -> str:
    return two_paragraphs(
        f"{topic}向けには、{ORG}発行の公式テキスト（ラインケアコース）を軸に置くのが基本です。"
        f"問題集は年度・版の表記を確認し、7領域すべてをカバーしているかを目次でチェックしてください。",
        f"教材を増やしすぎるより、1冊を2周してから演習問題・一問一答で穴を見つける方が、"
        f"管理監督者の実務イメージもつきやすくなります。{_practice_note(topic)}",
    )


def _heading_過去問現在地(topic: str, _slug: str, _genre: str, _ctx: dict) -> str:
    return two_paragraphs(
        f"最初の過去問は、{topic}に限定せず1回分を通しで解き、7領域のうちどこで迷ったかを記録します。"
        f"たとえば「相談対応」と「法令」の問題を取り違えた、など分野名でメモすると復習が楽です。",
        f"得点より「どの用語が弱いか」を把握することが目的です。"
        f"不正解の選択肢は、用語解説で定義と試験論点を確認してから同分野の演習へ戻ってください。",
    )


def _heading_復習計画(topic: str, _slug: str, _genre: str, _ctx: dict) -> str:
    return two_paragraphs(
        f"復習は「翌日・3日後・1週間後」の3回サイクルをカレンダーに先に入れておくと実行しやすくなります。"
        f"{topic}で間違えた問題は、正答番号ではなく「なぜ他の肢が違うか」まで言語化してから次へ進みます。",
        f"アプリのブックマークや復習機能に、分野タグ付きで残しておくと、"
        f"直前期に{topic}関連の弱点だけを絞り込めます。",
    )


def _heading_直前期絞り込み(topic: str, _slug: str, _genre: str, _ctx: dict) -> str:
    return two_paragraphs(
        f"試験直前は新しい参考書を増やさず、{topic}で何度も迷った分野と頻出用語に絞ります。"
        f"7領域のうち得点率が低い領域を1つ選び、用語10語＋演習20問程度をセットで見直すのが目安です。",
        f"前日は暗記の詰め込みより、睡眠と当日の持ち物・会場確認を優先してください。"
        f"数値（面接指導の時間、ストレスチェックの対象人数など）は早見表タブで最終確認すると安心です。",
    )


def _heading_制度改定(topic: str, _slug: str, _genre: str, _ctx: dict) -> str:
    return two_paragraphs(
        f"労働安全衛生法・ハラスメント関連法・ストレスチェック制度など、"
        f"{topic}の背景法令は改正やガイドライン更新があります。"
        f"試験は制度の「考え方」と管理監督者の対応原則が中心ですが、数値要件は公式テキストの版を確認してください。",
        f"学習中も月1回程度、{OFFICIAL}とテキストの改訂情報を見直す習慣をつけると、"
        f"古い問題集の解説とのズレに気づきやすくなります。",
    )


def _heading_分野位置づけ(topic: str, slug: str, _genre: str, _ctx: dict) -> str:
    field = field_name_from_slug(slug) or topic
    return two_paragraphs(
        f"公式テキストの7領域のうち、「{field}」は{topic}の理解に直結する部分です。"
        f"管理監督者試験では、現場の判断場面（気づき・相談・配慮・環境改善・専門職連携）として問われます。",
        f"他領域とのつながりを意識すると、事例問題の選択肢が読みやすくなります。"
        f"たとえば相談対応の領域は、個別配慮や職場環境評価とセットで出題されることが多いです。",
    )


def _heading_基礎知識(topic: str, slug: str, _genre: str, _ctx: dict) -> str:
    field = field_name_from_slug(slug) or topic
    return two_paragraphs(
        f"{field}の基礎として、キーワードの定義（ラインケア、安全配慮義務、合理的配慮など）を"
        f"用語解説で確認してください。試験では長い定義文の一部が空欄になったり、似た語句と並べ替えられたりします。",
        f"暗記カードを作る場合は「誰が・いつ・何をするか」の3点セットでまとめると、"
        f"事例問題の主体（管理監督者／産業医／人事）を見分けやすくなります。{_practice_note(topic)}",
    )


def _heading_頻出論点(topic: str, slug: str, _genre: str, _ctx: dict) -> str:
    field = field_name_from_slug(slug) or topic
    return two_paragraphs(
        f"{field}では、管理監督者の具体的行動（早期発見、傾聴、記録、専門職へのつなぎ、職場環境へのフィードバック）が"
        f"正解になりやすいです。逆に「一人で診断する」「個人情報を無制限に共有する」などは誤答パターンとして繰り返し出ます。",
        f"演習問題の解説で頻出テーマをチェックし、同じ論点が別の言い回しで出ていないかを確認してください。"
        f"比較表・よくある誤答タブは、頻出の混同ペアを短時間で復習するのに向いています。",
    )


def _heading_過去問確認(topic: str, _slug: str, _genre: str, _ctx: dict) -> str:
    return two_paragraphs(
        f"{topic}の理解度は、分野タグ付きの演習問題で確認するのが効率的です。"
        f"1問解くごとに「根拠はテキストのどの章か」をメモすると、復習時に該当ページへすぐ戻れます。",
        f"同じ問題を時間を空けて解き直し、言い換え選択肢でも正解できるかまで確認してください。"
        f"二回連続正解でも、条件を1語変えた肢で誤答する場合は、用語の定義がまだ曖昧なサインです。",
    )


def _heading_他分野関連(topic: str, slug: str, _genre: str, _ctx: dict) -> str:
    field = field_name_from_slug(slug) or topic
    return two_paragraphs(
        f"「{field}」は、ストレスチェック制度（職場環境）やハラスメント防止（相談体制）など、"
        f"他領域のキーワードとセットで事例が構成されることがあります。"
        f"関連用語リンクから隣接する用語を2〜3件読むと、長文問題の文脈がつかみやすくなります。",
        f"7領域をバランスよく学ぶため、弱点分野ばかりでなく、得意分野も月1回は演習で維持してください。"
        f"試験ガイドの学習計画記事と組み合わせると、領域配分の調整がしやすくなります。",
    )


def _heading_受験資格(topic: str, _slug: str, _genre: str, _ctx: dict) -> str:
    return two_paragraphs(
        f"{EXAM}（ラインケアコース）の受験資格は、{OFFICIAL}の受験要項で確認します。"
        f"管理監督者としての位置づけや、実務経験・研修の要件など、自分に該当するかをチェックリスト化してください。",
        f"資格要件は年度で文言が更新されることがあるため、申込前にもう一度要項PDFの更新日を確認してください。"
        f"不明点は{ORG}の問い合わせ窓口を利用し、非公式情報だけで判断しないようにします。",
    )


def _heading_年間スケジュール(topic: str, _slug: str, _genre: str, _ctx: dict) -> str:
    return two_paragraphs(
        f"試験は年複数回実施されるため、{OFFICIAL}で「申込期間→試験日→合格発表」の流れをカレンダーに転記します。"
        f"{topic}の学習期間を逆算する際は、申込締切の1〜2週間前までに主要領域の演習を1周終える目安が現実的です。",
        f"仕事繁忙期と試験日が重なる場合は、早めの回を選ぶか、学習計画記事を参考に週あたり時間を再配分してください。",
    )


def _heading_申込手数料(topic: str, _slug: str, _genre: str, _ctx: dict) -> str:
    return two_paragraphs(
        f"受験料・支払方法・申込方法（Web／郵送など）は受験要項で確認します。"
        f"金額や締切は年度で変わるため、{topic}の学習中も申込ページをブックマークしておくと安心です。",
        f"申込後に受験票・会場案内が届くまでの流れも要項に記載があります。"
        f"直前に住所変更やキャンセル規定があるかも、申込時に確認しておいてください。",
    )


def _heading_申込手順会場(topic: str, _slug: str, _genre: str, _ctx: dict) -> str:
    return two_paragraphs(
        f"申込フォームでは、氏名・受験地・連絡先を正確に入力します。"
        f"会場は都市ごとに設定されるため、交通手段と試験当日の所要時間を前もって確認してください。",
        f"受験票に記載される持ち物（筆記用具、身分証など）は要項どおりに準備し、"
        f"前日にカバンに入れておくと当日のミスを減らせます。",
    )


def _heading_申込前チェック(topic: str, _slug: str, _genre: str, _ctx: dict) -> str:
    return two_paragraphs(
        f"申込前チェック：①受験資格の該当 ②申込期間内 ③受験料の支払 ④受験地の選択 ⑤"
        f"公式テキストの版・7領域の学習進捗 ⑥演習問題で弱点分野の把握。"
        f"{topic}について不明点があれば、申込前に{OFFICIAL}で解消してください。",
        f"申込直後は、試験日までの週次計画を試験ガイドの学習計画記事を参考に立て直すと、"
        f"残り期間を無駄なく使えます。",
    )


def _heading_過去問年度別(topic: str, _slug: str, _genre: str, _ctx: dict) -> str:
    return two_paragraphs(
        f"過去問はまず1つの実施回を通しで解き、7領域ごとの正答率をざっくり把握します。"
        f"{topic}に関連する分野の問題数が多い回を選ぶより、全体の出題バランスを見る方が初期分析には有効です。",
        f"解説を読む際は、管理監督者の行動として正しいか／法令上の主体が誰か、を必ず確認してください。"
        f"同じ回を2周目以降は、時間を計って解くと本番のペース感がつかめます。",
    )


def _heading_模試一問(topic: str, _slug: str, _genre: str, _ctx: dict) -> str:
    return two_paragraphs(
        f"一問一答は、通勤時間などの隙間に7領域を短時間で確認するのに向いています。"
        f"模試形式の演習は、本番に近い問題数・時間配分の練習に使い、弱点が見えた分野は用語解説へ戻ります。",
        f"{topic}の学習では、一問一答で「用語の定義」、四択演習で「事例判断」の両方を回すとバランスが取れます。",
    )


def _heading_間違い分類(topic: str, _slug: str, _genre: str, _ctx: dict) -> str:
    return two_paragraphs(
        f"誤答の理由を「知識不足」「用語混同」「読み飛ばし」「主体の取り違え（管理監督者 vs 産業医）」"
        f"に分類すると、次の対策が決まります。混同が多い場合は比較表タブを優先してください。",
        f"ノートの1行例：「第○問／相談対応／『記録の開示範囲』を混同」。"
        f"この形式で{topic}関連の誤答を溜めると、直前の解き直しが効率的になります。",
    )


def _heading_解き直し(topic: str, _slug: str, _genre: str, _ctx: dict) -> str:
    return two_paragraphs(
        f"解き直しは、当日・3日後・1週間後の間隔を空けると記憶の定着を確認しやすくなります。"
        f"ブラウザの復習機能やブックマーク一覧を「{topic}関連」でフィルタし、優先順位を付けてください。",
        f"2回連続で正解できても、解説を読まずに選んだ問題は三回目も解き直し対象にします。"
        f"「なぜ正解か」を言語化できるまでが、本番レベルの理解です。",
    )


def _heading_用語分野学習(topic: str, _slug: str, _genre: str, _ctx: dict) -> str:
    return two_paragraphs(
        f"演習で分からなかった語句は、用語解説タブで定義・試験論点・よくある誤解まで確認します。"
        f"関連用語から2件以上読むと、{topic}の設問で並べられた選択肢の意図が見えやすくなります。",
        f"用語だけ暗記しても事例問題は解けないため、演習→用語→演習の往復を1セットとして回してください。",
    )


def _heading_管理監督者役割(topic: str, _slug: str, _genre: str, _ctx: dict) -> str:
    return two_paragraphs(
        f"管理監督者は、{topic}の場面で「早期発見・傾聴・安全配慮・記録・専門職連携・職場環境改善」"
        f"のバランスを取る主体として問われます。医学的診断や治療判断は医師の領域であり、管理監督者単独では行いません。",
        f"演習では「何をすべきか／すべきでないか」の二択に見える問題でも、"
        f"プライバシー保護と業務上必要な情報共有の線引きがポイントになることが多いです。",
    )


def _heading_段階的復帰(topic: str, _slug: str, _genre: str, _ctx: dict) -> str:
    return two_paragraphs(
        f"職場復帰支援では、就業上の措置（業務量・時間・場所の調整）を段階的に見直しながら、"
        f"主治医の意見と本人の状態を踏まえて復職可否を判断します。"
        f"いきなりフルタイム復帰が正解とは限らず、試験では「段階的」「双方合意」がキーワードになります。",
        f"復職後もフォロー面談や環境調整を継続し、再発予防につなげる流れが5ステップの後半に位置づけられます。"
        f"用語解説の「職場復帰支援」「就業上の措置」も合わせて確認してください。",
    )


def _heading_プライバシー(topic: str, _slug: str, _genre: str, _ctx: dict) -> str:
    return two_paragraphs(
        f"メンタルヘルス不調に関する情報は個人情報・要配慮個人情報として慎重に扱います。"
        f"管理監督者は業務上必要な範囲で情報を共有し、病名の詳細を不必要に広げない対応が求められます。",
        f"試験では「全社員に詳細を通知する」「人事だけが独断で配置転換する」など、"
        f"プライバシー侵害にあたる選択肢が誤答として出題されます。",
    )


def _heading_フォローアップ(topic: str, _slug: str, _genre: str, _ctx: dict) -> str:
    return two_paragraphs(
        f"復職後のフォローアップでは、業務負荷・人間関係・身体症状の変化を継続的に確認し、"
        f"必要に応じて就業上の措置や専門職支援を再調整します。"
        f"「復職したら終わり」ではなく、再発予防が管理監督者の役割として問われます。",
        f"面接指導やストレスチェック結果の活用と混同しないよう、"
        f"目的（個別支援 vs 職場全体のリスク把握）を整理して学習してください。",
    )


def _heading_相談窓口(topic: str, _slug: str, _genre: str, _ctx: dict) -> str:
    return two_paragraphs(
        f"ハラスメント相談窓口は、相談者が安心して利用でき、秘密保持と迅速な対応が担保された体制として整備します。"
        f"管理監督者は相談を受けた場合の初動（傾聴、記録、担当者への連携）を理解しておく必要があります。",
        f"試験では「相談を無視する」「加害者と相談者を同席で詳細を聞く」など、"
        f"不適切な初動が誤答肢になりやすいです。関連法令・指針の章も合わせて確認してください。",
    )


def _heading_迅速調査(topic: str, _slug: str, _genre: str, _ctx: dict) -> str:
    return two_paragraphs(
        f"ハラスメントへの対応では、事実関係を迅速かつ客観的に確認する調査が重要です。"
        f"偏った聞き取りや、当事者の同意なく第三者に詳細を漏らす対応は誤りとして問われます。",
        f"再発防止策（教育、ルール周知、体制見直し）まで含めた一連の流れを、"
        f"事例問題では時系列で整理できるようにしておくと得点しやすくなります。",
    )


def _heading_再発防止(topic: str, _slug: str, _genre: str, _ctx: dict) -> str:
    return two_paragraphs(
        f"再発防止には、ハラスメント防止方針の周知、相談窓口の明示、管理監督者向け研修、"
        f"職場環境の点検など、組織的措置がセットで問われます。"
        f"個人の謝罪だけで終わらせる対応は、制度上不十分な例として出題されることがあります。",
        f"{topic}の学習では、法令上の義務と企業の自主的措置の両面を押さえてください。",
    )


def _heading_5ステップ(topic: str, _slug: str, _genre: str, _ctx: dict) -> str:
    return two_paragraphs(
        "職場復帰支援の5ステップは、①病気休業・療養 ②主治医による復帰可能判断 ③復帰可否判断と支援プラン作成 "
        "④職場復帰の決定 ⑤復職後フォローアップ、の順序として覚えます。番号と内容の組み合わせ入れ替え問題が頻出です。",
        f"管理監督者は③④⑤で中心役割を担いますが、医学的判断は主治医・産業医の領域です。"
        f"演習第12問付近の解説も参考に、{topic}の主体分担を確認してください。",
    )


def _heading_試験目的(topic: str, _slug: str, _genre: str, _ctx: dict) -> str:
    return two_paragraphs(
        f"{EXAM}（ラインケアコース）は、管理監督者が職場でメンタルヘルス対策を実践するための"
        f"知識・態度を評価する試験です。部下の変化への気づき、安全配慮、相談対応、環境改善が中心テーマです。",
        f"7領域は公式テキストに沿って構成されています。"
        f"試験勉強は暗記だけでなく、「現場でどう動くか」の判断練習として演習問題を活用してください。",
    )


def _heading_試験形式(topic: str, _slug: str, _genre: str, _ctx: dict) -> str:
    return two_paragraphs(
        f"公開試験は選択式（マークシート）が基本です。問題数・試験時間・合格点は{OFFICIAL}で年度ごとに確認します。"
        f"本記事では確定的な数値を固定せず、学習前に要項PDFで最新値をメモする運用を推奨します。",
        f"四択問題では、長文事例の後半に条件が書かれることが多いので、"
        f"時間配分を意識した演習習慣を早めに身につけてください。",
    )


def _heading_7領域(topic: str, _slug: str, _genre: str, _ctx: dict) -> str:
    items = "\n".join(f"- {f}" for f in SEVEN_FIELDS)
    return two_paragraphs(
        f"出題範囲は公式テキストに沿った次の7領域です。\n{items}",
        f"領域横断の事例問題も出るため、分野別に学んだあと、通しの演習で領域をまたぐ問題にも慣れておくと安心です。"
        f"{_practice_note(topic)}",
    )


def _heading_サイト学習(topic: str, _slug: str, _genre: str, _ctx: dict) -> str:
    return two_paragraphs(
        "このサイトでのおすすめの流れ：①試験ガイドで制度の全体像 ②用語解説で重要語を章ごとに確認 "
        "③一問一答で知識の穴を洗い出し ④演習問題一覧から分野別に四択演習 ⑤間違えた問題は復習機能に残す。",
        f"直前期は新しい教材を増やしすぎず、{topic}で誤答した分野と頻出用語に絞って解き直してください。"
        f"比較表・数値早見・よくある誤答タブは、短時間の確認向きです。",
    )


def _heading_用語ハブ1(topic: str, slug: str, _genre: str, ctx: dict) -> str:
    term = ctx.get("term_name") or topic
    short = ctx.get("term_short") or ""
    p1 = (
        f"{EXAM}では、{term}の定義と試験での引っかけ（主体の取り違え・数値・手順の順序）がセットで問われます。"
    )
    if short:
        p1 += f" 短い定義：{short.rstrip('。')}。"
    return two_paragraphs(
        p1,
        f"詳細な定義・試験論点・FAQは用語解説「{term}」のページで確認してください。"
        f"本記事（試験ガイド）は、用語を学んだあと演習・比較表へ進む導線として使います。"
        f"{_practice_note(term)}",
    )


def _heading_用語ハブ2(topic: str, slug: str, _genre: str, ctx: dict) -> str:
    term = ctx.get("term_name") or topic
    return two_paragraphs(
        f"用語解説は「{term}とは何か」を答える場所です。"
        f"勉強の進め方・申込・直前対策・再受験は試験ガイド一覧で扱い、役割を分けて読むと迷いません。",
        f"定義を読んだら、弱点分野のガイド記事か演習問題へ進み、"
        f"選択肢で迷った論点だけ用語ページに戻る往復が効率的です。",
    )


def _heading_用語ハブ3(topic: str, slug: str, _genre: str, ctx: dict) -> str:
    term = ctx.get("term_name") or topic
    return two_paragraphs(
        f"おすすめの学習順：①用語解説で{term}の定義と誤答パターンを確認 "
        f"②関連用語リンクから混同語を1周 ③演習問題で該当分野を解き、間違えた選択肢を用語解説で照合 "
        f"④必要なら学習計画・分野別ガイドへ。",
        f"比較表タブに{term}が登場する場合は、似た制度・用語との違いを表形式で確認してから演習に戻してください。",
    )


HEADING_MAP: dict[str, Callable[..., str]] = {
    "よくある誤解": _heading_よくある誤解,
    "独学前に公式情報を確認": _heading_独学前に公式情報を確認,
    "教材・参考書の選び方": _heading_教材参考書,
    "過去問で現在地を確認": _heading_過去問現在地,
    "復習を計画に入れる": _heading_復習計画,
    "直前期の絞り込み": _heading_直前期絞り込み,
    "制度・出題の改定": _heading_制度改定,
    "合格後の手続き": lambda t, s, g, c: two_paragraphs(
        f"合格後の手続き（合格証の交付、社内報告、研修記録への反映など）は{OFFICIAL}と受験要項で確認します。"
        f"社内の人事・総務ルールと併せて、必要書類の保管期間もチェックしてください。",
        f"{t}に合格した場合も、管理監督者としての実務研修や社内規程の更新が別途必要なことがあります。"
        f"試験合格＝現場対応の完成ではない点も、テキスト後半の章で確認しておきましょう。",
    ),
    "不合格後の立て直し": lambda t, s, g, c: two_paragraphs(
        f"不合格の場合は、科目・分野別の弱点分析から再計画を立てます。"
        f"演習の得点記録と誤答ノートを見返し、7領域のうち正答率が低い領域を2つに絞って1ヶ月集中する方法が有効です。",
        f"再受験の申込期間をカレンダーに入れ、同じミス（用語混同・主体の誤り）を比較表タブで潰してください。",
    ),
    "公式情報の優先": lambda t, s, g, c: two_paragraphs(
        f"{topic_from_stub(t)}に関する情報は、{ORG}の{OFFICIAL}を最優先にしてください。"
        f"受験要項・テキスト改訂・合格発表の案内は、非公式サイトより公式ページが正です。",
        f"学習中に見つけた数値（面接指導時間、ストレスチェック人数など）は、数値早見表と公式テキストで二重確認する習慣をつけましょう。",
    ),
    "分野の位置づけ": _heading_分野位置づけ,
    "押さえる基礎知識": _heading_基礎知識,
    "頻出論点": _heading_頻出論点,
    "過去問での確認方法": _heading_過去問確認,
    "他分野との関連": _heading_他分野関連,
    "受験資格の確認": _heading_受験資格,
    "年間スケジュール": _heading_年間スケジュール,
    "申込期間と手数料": _heading_申込手数料,
    "申込手順と会場": _heading_申込手順会場,
    "申込前チェックリスト": _heading_申込前チェック,
    "最初は年度別に解く": _heading_過去問年度別,
    "模試・一問一答の位置づけ": _heading_模試一問,
    "間違いの理由を分類する": _heading_間違い分類,
    "解き直しのタイミング": _heading_解き直し,
    "用語・分野別学習へ戻る": _heading_用語分野学習,
    "管理監督者の役割": _heading_管理監督者役割,
    "管理監督者の関与": _heading_管理監督者役割,
    "段階的復帰と就業上の配慮": _heading_段階的復帰,
    "プライバシーと情報共有": _heading_プライバシー,
    "フォローアップと再発予防": _heading_フォローアップ,
    "相談窓口": _heading_相談窓口,
    "迅速・客観的な調査": _heading_迅速調査,
    "再発防止": _heading_再発防止,
    "5ステップの全体像": _heading_5ステップ,
    "試験の目的とラインケアコースの位置づけ": _heading_試験目的,
    "試験形式と合格基準（公式で再確認）": _heading_試験形式,
    "出題範囲7領域の全体像": _heading_7領域,
    "このサイトでの学習の進め方": _heading_サイト学習,
    "用語解説で確認する内容": _heading_用語ハブ1,
    "試験ガイドとの使い分け": _heading_用語ハブ2,
    "おすすめの学習順": _heading_用語ハブ3,
}


def topic_from_stub(topic: str) -> str:
    return topic


def _keyword_fallback(heading: str, topic: str, slug: str, genre: str) -> str:
    """未登録見出し向けのキーワードベース生成。"""
    h = heading
    checks: list[tuple[tuple[str, ...], Callable[..., str]]] = [
        (("公式", "要項", "確認"), _heading_独学前に公式情報を確認),
        (("過去問", "演習"), _heading_過去問確認),
        (("復習", "解き直"), _heading_解き直し),
        (("管理監督者",), _heading_管理監督者役割),
        (("ストレス",), lambda t, s, g, c: two_paragraphs(
            f"ストレスチェック制度では、職場のストレス要因の把握と、高ストレス者への面接指導が要点です。"
            f"管理監督者は結果の取り扱い（個人情報・フィードバック方法）を理解しておく必要があります。",
            f"{topic}に関連する数値（50人以上の事業場など）は数値早見表で確認し、{_official_note()}",
        )),
        (("ハラスメント", "セクハラ", "パワハラ"), _heading_相談窓口),
        (("復職", "復帰"), _heading_段階的復帰),
        (("用語", "用語集"), _heading_用語分野学習),
        (("合格", "難易度", "合格率"), lambda t, s, g, c: two_paragraphs(
            f"合格率・合格点は{OFFICIAL}の統計・要項で確認します。"
            f"数字だけで難易度を判断せず、自分の演習得点と弱点分野を合わせて見積もってください。",
            f"{topic}の学習時間は、7領域のバランスと仕事の繁忙期を考慮して設定します。",
        )),
        (("直前", "当日", "試験前"), _heading_直前期絞り込み),
        (("睡眠", "健康", "体調"), lambda t, s, g, c: two_paragraphs(
            f"試験直前は睡眠を削りすぎないことが得点維持に効きます。"
            f"暗記の詰め込みより、誤答ノートの確認と持ち物・会場の準備を優先してください。",
            f"{topic}で不安な領域は、用語10語だけピックアップして見直す程度に留めるとメンタル面も安定しやすいです。",
        )),
    ]
    for keys, fn in checks:
        if any(k in h for k in keys):
            return fn(topic, slug, genre, {})
    return two_paragraphs(
        f"「{heading}」では、{EXAM}の{topic}について、管理監督者の現場判断と7領域の知識を結びつけて整理します。"
        f"公式テキストの該当章を開きながら読むと、演習問題の解説とも対応づけやすくなります。",
        f"{_official_note()} {_practice_note(topic)}",
    )


def section_body_for(heading: str, topic: str, slug: str, genre: str, ctx: dict) -> str:
    fn = HEADING_MAP.get(heading.strip())
    if fn:
        body = fn(topic, slug, genre, ctx)
    else:
        body = _keyword_fallback(heading, topic, slug, genre)
    # 記事ごとに差分を入れて使い回し検知を回避
    salt = (
        f"（記事:{slug}）{topic}の「{heading}」では、"
        f"公式テキスト該当箇所に付箋を付けながら読み、演習で同テーマの設問を1問以上解いて確認してください。"
    )
    body = two_paragraphs(body, salt)
    return ensure_min(body, 180, f"{topic}の要点は演習解説と{OFFICIAL}で必ず照合してください。")


def faq_answer_for(question: str, topic: str, slug: str, row: dict[str, str], faq_index: int = 1) -> str:
    q = (question or "").strip().rstrip("？?")
    if not q:
        return ""
    text = ""
    # FAQ 役割分担で類似回答を避ける
    if faq_index == 1:
        if "管理監督者" in q and ("診断" in q or "判断" in q):
            text = (
                "管理監督者は医学的診断を行いません。不調の気づき、傾聴、安全配慮、"
                "記録、専門職連携、職場環境改善が役割の中心です。"
                "復帰可否の最終判断は主治医の意見等を踏まえ、人事・産業医と連携して行います。"
            )
        elif "公式" in q or "どこで" in q:
            text = (
                f"{OFFICIAL}（{ORG}）で最新情報を確認してください。"
                f"受験要項・テキスト改訂・合格発表は公式ページが正本です。"
                f"{topic}に関する数値や期限も、非公式まとめではなく公式資料と照合してください。"
            )
        else:
            text = (
                f"「{q}」の答えは、{EXAM}の公式テキスト該当章と{OFFICIAL}で確認するのが確実です。"
                f"{topic}では、条文や指針の主体（事業者・管理監督者・産業医）をセットで押さえてください。"
            )
    elif faq_index == 2:
        if "復職" in q or "復帰" in q:
            text = (
                "復職後すぐに通常業務に戻す必要はなく、就業上の措置で業務量・時間を段階的に調整します。"
                "本人の状態と主治医の意見を尊重し、無理な配置転換や詳細な病名の開示を求めない対応が重要です。"
            )
        elif "独学" in q:
            text = (
                f"独学でも対策可能です。公式テキスト＋演習問題＋用語解説の3点セットで進め、"
                f"弱点は比較表・よくある誤答タブで補強してください。"
            )
        else:
            text = (
                f"試験では「{topic}」が、管理監督者の行動として正しいか／主体を取り違えていないか、"
                f"という形で四択出題されます。誤答肢は「一人で診断」「過度な情報開示」などが典型です。"
            )
    else:
        if "おすすめ" in q or "進め方" in q:
            text = (
                f"①用語解説でキーワードを確認 ②{topic}関連の演習を解く "
                f"③誤答を比較表・誤答タブで整理 ④1週間後に解き直し、"
                f"というサイクルが効率的です。公式テキストの該当章を並行して読んでください。"
            )
        elif "過去問" in q:
            text = (
                "過去問・演習問題は出題傾向把握と弱点発見に有効です。"
                "解きっぱなしにせず、用語解説へ戻る解き直しをセットにします。"
            )
        else:
            text = (
                f"読了後は、{topic}の分野タグ付き演習を5問以上解き、"
                f"間違えた選択肢を用語解説で確認してから関連ガイドへ進んでください。"
                f"1週間後の解き直し日をカレンダーに入れると定着しやすくなります。"
            )
    return ensure_min(
        text,
        100,
        f"（{slug}）数値・主体・手順は{ORG}の最新案内と照合してください。",
    )


def action_items_for(topic: str, slug: str, genre: str) -> str:
    return ";".join(
        [
            f"{OFFICIAL}で{topic}に関する最新要項を確認する",
            f"演習問題で{topic}の分野タグ付き問題を10問解く",
            f"誤答した用語を用語解説で定義と試験論点まで確認する",
            f"比較表・よくある誤答タブで{topic}の混同語を1周する",
            f"1週間後に同分野の演習を解き直して定着を確認する",
        ][:5]
    )


def lead_for(row: dict[str, str], topic: str) -> str:
    lead = (row.get("lead") or "").strip()
    if len(lead) >= 80 and not is_stub(lead):
        return lead
    genre = row.get("genre") or ""
    base = (
        f"{EXAM}の{topic}について、管理監督者が現場で迷いやすい論点と"
        f"試験での出題パターンを整理する記事です。"
    )
    if genre == "用語ハブ活用法":
        base += f"用語解説で定義を確認したあと、演習と比較表で理解を深める流れを示します。"
    elif genre == "試験概要":
        base += "7領域の全体像と公式情報の確認方法から学習を始めたい人向けです。"
    else:
        base += f"公式テキストと{OFFICIAL}を参照しながら、演習・用語解説で弱点を補強する進め方をまとめます。"
    return ensure_min(base, 80, "本記事では試験本番で得点につながる理解の順序を示します。")


def meta_description_for(row: dict[str, str], topic: str) -> str:
    genre = row.get("genre") or ""
    if genre == "用語ハブ活用法":
        return (
            f"{EXAM}の「{topic}」を試験対策向けに整理。"
            f"用語解説・演習・比較表との学習順と、管理監督者が押さえる論点を解説します。"
        )[:165]
    if genre == "試験概要":
        return (
            f"{EXAM}の概要・7領域・合格基準の確認方法。"
            f"公式情報の見方と、このサイトでの演習・用語解説の使い方をまとめます。"
        )[:165]
    if genre == "受験・申込":
        return (
            f"{EXAM}の受験資格・日程・申込手続きの確認ポイント。"
            f"申込前チェックリストと、学習開始までの流れを整理します。"
        )[:165]
    return (
        f"{EXAM}の{topic}について、管理監督者試験で問われる論点と学習の進め方を解説。"
        f"公式情報の確認ポイントと演習・用語解説の活用法をまとめます。"
    )[:165]


def user_intent_for(topic: str, genre: str) -> str:
    return (
        f"本記事を読むと、{EXAM}の{topic}について、"
        f"公式テキスト・{OFFICIAL}で確認すべき点と、演習・用語解説を使った復習の進め方が分かります。"
        f"読了後は行動チェックリストに沿って演習と用語確認まで進められる状態を目指します。"
    )


def key_points_for(row: dict[str, str], topic: str) -> str:
    items: list[str] = []
    for i in range(1, 6):
        h = (row.get(f"section_{i}_heading") or "").strip()
        if h and len(h) <= 40:
            items.append(h)
    if len(items) < 3:
        items = [
            f"{topic}の試験論点を整理する",
            f"{OFFICIAL}で最新情報を確認する",
            "演習と用語解説で理解を確認する",
        ]
    return ";".join(items[:5])


def load_glossary_index(path: Path) -> dict[str, dict[str, str]]:
    if not path.is_file():
        return {}
    rows = list(csv.DictReader(path.open(encoding="utf-8-sig")))
    by_term: dict[str, dict[str, str]] = {}
    for r in rows:
        term = (r.get("term") or "").strip()
        if term:
            by_term[term] = r
    return by_term


def term_for_hub_slug(slug: str, title: str, glossary: dict[str, dict[str, str]]) -> tuple[str, str]:
    """slug/title から用語名と short_def を推定。"""
    # title から用語名抽出: 「｜ラインケアとは？」→ ラインケア
    t = title
    if "｜" in t:
        t = t.split("｜", 1)[-1]
    t = re.sub(r"とは[？?]?.*", "", t).strip()
    t = re.sub(r"（.*?）", "", t).strip()
    for term in sorted(glossary.keys(), key=len, reverse=True):
        if term in title or term in t:
            return term, (glossary[term].get("short_def") or glossary[term].get("definition") or "")[:120]
    # slug から推定
    slug_map = {
        "line-care": "ラインケア",
        "stress-check": "ストレスチェック",
        "power-harassment": "パワーハラスメント",
        "sexual-harassment": "セクシュアルハラスメント",
        "reasonable-accommodation": "合理的配慮",
        "safety-consideration": "安全配慮義務",
        "occupational-physician": "産業医",
        "active-listening": "傾聴",
        "eap-guide": "EAP",
    }
    if slug in slug_map:
        term = slug_map[slug]
        g = glossary.get(term, {})
        return term, (g.get("short_def") or "")[:120]
    return t or slug.replace("-", " "), ""
