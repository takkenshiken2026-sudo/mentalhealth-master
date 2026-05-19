# ビルド手順（メンタルヘルス二種マスター）

## 概要

| コマンド | 用途 |
|----------|------|
| `python3 tools/build_foundation.py` | **フェーズ1（推奨）** — CSV 初期化・検証・`site-config.js` / `site-theme.css` 反映のみ |
| `python3 tools/build_all.py` | 上記 + 設定反映（クイズ JS・HTML 再生成は **スキップ**） |
| `EXAM_SITE_FULL_BUILD=1 python3 tools/build_all.py` | CSV からクイズ JS・SEO 記事・用語ページを **一括再生成** |

既存の `eisei1-data-*.js` と手書き HTML は、フルビルドを明示するまで上書きされません。

## 初回セットアップ

```bash
# リポジトリルートで
python3 tools/build_foundation.py
```

実行内容:

1. `tools/bootstrap_data_csv.py` — `data/*.csv` を checklist / 既存記事から生成
2. `tools/validate_csv.py` — CSV スキーマ検証
3. `tools/apply_site_config.py` — `site-config.json` → `site-config.js` / `site-theme.css` 等
4. `tools/build_q_index_from_master.py` — `q/index.html`（演習問題一覧）を生成

## 設定

- `site-config.json` — ブランド名・公式 URL・GA4・分野タグなど
- `data/guide_articles.csv` — SEO 記事（7本）のソース
- `data/glossary_terms.csv` — 用語詳細のソース（`docs/glossary-terms-checklist.csv` 由来）

## フェーズ2（試験ガイド記事）

```bash
# CSV をルール準拠の本文に拡充（初回・更新時）
python3 tools/populate_guide_articles_phase2.py

# HTML 再生成（クイズ JS は触らない）
python3 tools/build_article_pages.py

# 試験ガイドのみ SEO 検証
python3 -c "from pathlib import Path; from tools.validate_generated_seo import GeneratedSeoValidator; v=GeneratedSeoValidator(); [v.validate_page(p) for p in sorted(Path('articles').glob('*/index.html'))]; import sys; sys.exit(1 if any(i.level=='ERROR' for i in v.issues) else 0)"
```

生成される要素: 目次、信頼性表、できること、本文（最大7見出し）、FAQ（`FAQPage`）、`Article` / `BreadcrumbList` 構造化データ。

## フェーズ3以降

1. 用語は `glossary_terms.csv` 拡張後 `build_glossary_pages.py`
2. 過去問静的ページは `data/past_questions.csv` 投入後 `build_past_question_pages.py`
3. 用語ページは `validate_generated_seo.py` で別途検証（現状は旧HTMLのためエラーになり得る）

## 参照

- `docs/seo-article-guidelines.md`
- テンプレートルール: `exam-site-shell` リポジトリの `exam-site-shell-template-rule.md`
