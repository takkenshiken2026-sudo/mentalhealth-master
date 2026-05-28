# -*- coding: utf-8 -*-
"""メンタルヘルスII種 知識ハブ S40 追加分（各10件）."""

from tools.write_mentalhealth_hub_s30 import _OFFICIAL, cmp, mis, num

B = "基礎・役割"
W = "職場環境・配慮"
R = "相談・連携・復職"

def _related(cat: str) -> str:
    if cat == B:
        return "管理監督者への教育研修・情報提供;メンタルヘルス不調の定義;保健師"
    if cat == W:
        return "職場環境の改善;過重労働防止;ストレスチェック"
    return "就業上の配慮;復職;再発予防"

COMPARISON_TOPICS = [
    ("s40-saihatsu-keikaku-cmp", "再発防止計画の比較", R),
    ("s40-kyufukki-shien-diff", "休復職支援の違い", R),
    ("s40-saihatsu-keikaku-matome", "再発防止計画の整理", R),
    ("s40-kyufukki-shien-point", "休復職支援の要点", R),
    ("s40-saihatsu-keikaku-taihi", "再発防止計画の対比", R),
    ("s40-kyufukki-shien-kubun", "休復職支援の区分", R),
    ("s40-saihatsu-keikaku-tejun", "再発防止計画の手順", R),
    ("s40-kyufukki-shien-seido", "休復職支援の制度", R),
    ("s40-saihatsu-keikaku-unyo", "再発防止計画の運用", R),
    ("s40-kyufukki-shien-hantei", "休復職支援の判定", R),
]

NUMBER_TOPICS = [
    ("s40-saihatsu-keikaku-num", "再発防止計画の数値", R),
    ("s40-kyufukki-shien-cycle", "休復職支援の周期", R),
    ("s40-saihatsu-keikaku-meyasu", "再発防止計画の目安", R),
    ("s40-kyufukki-shien-freq", "休復職支援の頻度", R),
    ("s40-saihatsu-keikaku-ratio", "再発防止計画の比率", R),
    ("s40-kyufukki-shien-time", "休復職支援の時間", R),
    ("s40-saihatsu-keikaku-count", "再発防止計画の回数", R),
    ("s40-kyufukki-shien-kijun", "休復職支援の基準", R),
    ("s40-saihatsu-keikaku-haibun", "再発防止計画の配分", R),
    ("s40-kyufukki-shien-check", "休復職支援の確認", R),
]

MISTAKE_TOPICS = [
    ("s40-kon-saihatsu-keikaku-kon", "再発防止計画の混同", R),
    ("s40-kon-kyufukki-shien-gokai", "休復職支援の誤認", R),
    ("s40-kon-saihatsu-keikaku-reverse", "再発防止計画の逆転", R),
    ("s40-kon-kyufukki-shien-omit", "休復職支援の省略", R),
    ("s40-kon-saihatsu-keikaku-blind", "再発防止計画の盲信", R),
    ("s40-kon-kyufukki-shien-over", "休復職支援の過剰", R),
    ("s40-kon-saihatsu-keikaku-noconf", "再発防止計画の未確認", R),
    ("s40-kon-kyufukki-shien-nouse", "休復職支援の未使用", R),
    ("s40-kon-saihatsu-keikaku-skip", "再発防止計画の放置", R),
    ("s40-kon-kyufukki-shien-zero", "休復職支援のゼロ", R),
]

COMPARISONS_ADD = [
    cmp(
        slug, title, cat,
        "メンタルヘルスII種;S40;比較",
        f"{title}について、試験で混同しやすい観点を5軸で整理します。",
        "観点A;観点B",
        [
            ("定義", ["主語・目的の確認", "手順・対象の確認"]),
            ("頻出", ["類似語の入替", "数値・条件付き出題"]),
            ("運用", ["点検・記録の順序", "異常時の対応"]),
            ("試験", ["名称だけで判断", "旧要項の流用"]),
            ("誤答", ["比較軸を先に固定", "条件文を最後まで読む"]),
        ],
        f"{title}｜メンタルヘルスII種 S40",
        "S40では再発防止計画・休復職支援を中心に整理します。比較表で軸を先に固定してください。" + _OFFICIAL,
        "再発防止計画;休復職支援;条件文の主語確認",
        "名称だけ暗記;旧要項流用;主語の読み飛ばし",
        "「主語→手順→法令→誤答」。",
        _related(cat),
        [
            ("この比較の先に覚える点は？", "主語を一文で言えるようにしてください。その後に手順と法令を広げると正誤判定の再現性が上がります。"),
            ("本番での使い方は？", "問題文のキーワードから比較軸を1つ選び、表の該当行と照合してから選択肢を読みます。"),
            ("S39との違いは？", "S39は基礎整理、S40は再発防止計画・休復職支援の深掘りです。"),
            ("公式確認はどこですか？", "試験要項と関係法令で必ず最新確認してください。" + _OFFICIAL),
        ],
    )
    for slug, title, cat in COMPARISON_TOPICS
]

NUMBERS_ADD = [
    num(
        slug, title, cat,
        "メンタルヘルスII種;S40;数値",
        f"{title}で押さえる代表数値と確認観点を整理します。",
        "代表値は要項・法令で確認",
        [
            ("代表数値", "要項・規則で確認", "年度更新に注意"),
            ("適用条件", "対象・手順を確認", "主語の取り違え防止"),
            ("記録", "運転・学習記録", "異常時は原因を併記"),
            ("試験対策", "数値+条件で暗記", "単独暗記を避ける"),
        ],
        f"{title}｜メンタルヘルスII種 数値S40",
        "S40の数値は再発防止計画・休復職支援と条件のセットで覚えると得点が安定します。" + _OFFICIAL,
        "数値と条件をセット;単位を確認;最新法令で照合",
        "数値のみ暗記;他設備の値を流用;旧要項の使用",
        "「数値・単位・条件・対象」を1行で書く。",
        _related(cat),
        [
            ("数値問題のコツは？", "単位と対象を先に確認し、次に条件文を読みます。"),
            ("復習の進め方は？", "誤答時は読み落とした条件を記録し、型別再演習してください。"),
            ("実務との接続は？", "日常の点検・学習記録と対応づけると定着しやすくなります。"),
            ("公式確認は？", "受験直前に必ず最新版を照合してください。" + _OFFICIAL),
        ],
    )
    for slug, title, cat in NUMBER_TOPICS
]

MISTAKES_ADD = [
    mis(
        slug, title, cat,
        "メンタルヘルスII種;S40;誤答",
        f"{title}で発生しやすい誤答パターンを4ケースで整理します。",
        "再発防止計画・休復職支援は名称が似るため、主語と時点の読み飛ばしが起きやすい。",
        [
            ("用語", "名称だけで判断", "主語・手順をセット確認", "同義語の入替え"),
            ("手順", "順序の逆転", "確認→実施→記録の順", "類似工程の混同"),
            ("数値", "単位未確認", "数値・単位・条件を同時確認", "近似値の誤誘導"),
            ("情報", "旧規則の流用", "最新規則で照合", "非公式情報優先"),
        ],
        f"{title}｜メンタルヘルスII種 誤答S40",
        "S40の誤答は再発防止計画・休復職支援の読み落としが中心です。誤答型を記録し、比較表へ戻って根拠を再確認してください。" + _OFFICIAL,
        "誤答型を分類;主語を固定で読む;比較表と往復",
        "原因を残さない;同型を放置;法令未確認",
        "「誤答原因を1行で書く」を毎回実施。",
        _related(cat),
        [
            ("誤答パターンの使い方は？", "解いた直後に型を選び、同型問題をまとめて再演習します。"),
            ("最優先で直す点は？", "主語確認です。ここが改善すると数値・法令問題の取りこぼしも減ります。"),
            ("過去問との併用は？", "過去問の誤答に型タグを付け、S40比較表で整理し直してください。"),
            ("公式確認は？", "誤答修正後は要項・関係法令の更新有無を必ず確認してください。" + _OFFICIAL),
        ],
    )
    for slug, title, cat in MISTAKE_TOPICS
]
