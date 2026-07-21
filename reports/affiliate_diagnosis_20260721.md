# 有料模試・有料講座アフィリエイトが売れない原因（診断 2026-07-21）

結論：**有料模試・有料講座は「売り場」も「収益導線」も実質存在していない**。
書籍（テキスト・問題集）以外はページが未公開で、講座リンクは報酬が発生しない素URL。
さらに高集客ページからオファーへの導線がほぼ無い。以下、影響度順。

## 原因1【致命的】有料講座・有料模試のページが未公開（draft）
- アフィリ記事のうち**公開は書籍2本のみ**：`affiliate-textbooks-recommend`（テキスト）/
  `affiliate-problem-books`（問題集）。
- **有料講座・模試系の8本はすべて `content_status: draft`** → ビルドで公開されない
  （`is_published_guide(draft)=False` を確認）。`public_site/` に実体が存在しない。
  - draft: online-course-compare / correspondence-course / cram-school /
    mock-exam-materials / free-vs-paid-study / beginner-material-set /
    retake-short-course / qualification-support-service
- GSCに一部表示が残るのは、過去に公開→draft化した名残（stale index）。**現状は404/不在**。

## 原因2【致命的】有料講座のリンクがアフィリエイト非追跡（報酬ゼロ）
- `affiliate-online-course-compare.yaml` のリンクは
  `https://studying.jp/mental/itempage/course2-2026.html`、
  `https://www.udemy.com/course/mentalhealth-management-exam/` など**素のURL**で
  **トラッキングID／アフィリエイトパラメータが無い**。
- ビルド判定でも `affiliate_brief_has_links = False`（＝ASP追跡リンク無しとして公開対象外）。
- つまり**公開・クリックされても報酬は発生しない**。スタディング/Udemy等のASP
  プログラム未加入、または発行済みリンク未設定の疑いが濃厚。
- 対照的に書籍系はAmazonアソシエイト（`tag=ue083093-22`）が入っており追跡可能。

## 原因3【重大】高集客ページに導線が無い（サイロ化）
- 高集客の実ページ（schedule / exam-fees / exam-difficulty / exam-venue-and-region /
  exam-application-flow）に**アフィリCTAが0**。
  （grepで1件ヒットするのは `seo-editorial.css?v=…fix-affiliate-layout` の
  ファイル名誤検出であり、実リンクではない。）
- アフィリへの内部リンクは `past-questions-study` と `q/index`(過去問ハブ) から
  **書籍2本のみ**。トップページ（SPA）からは0。
- 最も集客・購買意図が高い**個別過去問ページ約300本（q26=3.54位 等）から
  オファーへ一切繋いでいない**（q26のアフィリリンク=0）。
- 講座・模試ページは未公開なので、そこへ向かう内部リンクも当然存在しない。

## 原因4【重大】商品ミスマッチ（「有料模試」の中身が書籍）
- `affiliate-mock-exam-materials` の商品は Amazon の**過去問題集（書籍3冊）**で、
  本物の「有料模試サービス（予想模試・採点付き等）」ではない。
- 「有料模試を受けたい／比較したい」検索意図に、書籍リンクで応えており転換しづらい。

## 原因5【補助】アフィリページ自体の集客・CTRが弱い
- 公開済みの書籍2本も表示は最大11程度、**CTRは0**。
- アフィリ記事はテンプレ由来の比較体裁だが、流入・クリックともほぼ発生していない。

---

## 是正の優先順位（推奨）

まず「売り場」と「収益導線」を成立させることが先決。SEOで集客しても、現状は
受け皿が無いか報酬が出ない状態。

1. **ASP加入と正規リンクの発行を確定**（事業判断・サイト外）
   - スタディング/Udemy/フォーサイト等のアフィリプログラムに加入し、
     **トラッキング付きの正規リンク**を `affiliate-briefs/*.yaml` の `affiliate_url` に設定。
   - リンクが無い/取れないプログラムはページを作っても収益化不可のため優先度を下げる。
2. **講座・模試ページを公開状態にする**（リンク確定後）
   - 正規リンクを入れた記事の `content_status` を `published` にし、`build_all.py` で公開。
   - リンク未確定のまま公開しても報酬ゼロなので、必ず1→2の順。
3. **高集客ページからの導線を作る（サイロ解消）**
   - 個別過去問ページ・過去問ハブ・difficulty/schedule 等の実ページに、
     文脈に合うオファーCTA（例：過去問ページ→「模試・問題集」、
     difficulty→「独学が不安なら講座」）を追加。
   - 特に**個別過去問300本**は集客・意図とも最良の設置面。テンプレ側
     （`build_past_question_pages.py` / `q_page_seo.py`）で一括設置が可能。
4. **「有料模試」の商品定義を見直す**
   - 書籍とは別に、実在する有料模試/予想問題サービスがあればそれを、無ければ
     「模試=過去問題集の回し方」として正直に訴求（現状の書籍リンクを活かす）。
5. **オファーの訴求改善**（CTR対策）
   - 価格・特典・返金・向き不向きを冒頭に、比較表と「あなたはどれ型」の結論を明示。

> 補足：SEO面（別レポート `ranking_strategy_top5_20260721.md`）で過去問の集客は
> 強化中。集客が伸びるほど、上記の導線・収益化の不備が機会損失として拡大する。
