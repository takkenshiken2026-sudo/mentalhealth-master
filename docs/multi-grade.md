# マルチ種対応（II種ルート + /self + /master）

メンタルヘルス・マネジメント検定の複数の種（grade）を**1リポジトリ・1ドメイン**で運用する仕組み。
II種（ラインケア）は従来どおりルート（`/`）で配信し、新種は basePath 配下に生成する。

| 種 | id | 公開パス | ルート | データ | 状態 |
|----|----|----------|--------|--------|------|
| II種（ラインケア） | `line` | `/` | リポジトリ直下 | `data/` | **公開中** |
| III種（セルフケア） | `self` | `/self` | `grades/self/` | `grades/self/data/` | 準備中（未公開） |
| I種（マスター） | `master` | `/master` | `grades/master/` | `grades/master/data/`（論述 `essays.csv` 含む） | 準備中（未公開） |

レジストリは `grades.json`。`published` が公開可否のフラグ。

## 仕組み（なぜ staging か）

既存ビルドツールは出力先を「リポジトリルート」に固定しているため、設定だけ差し替えても
出力はII種側に書かれてしまう。そこで新種は**使い捨てディレクトリにリポジトリを複製**し、
その中で種の設定・データに差し替えてから `build_all.py` を回し、生成物を `public_site/<種>` に
配置する（II種のファイル・生成物は一切変更されない）。

- `tools/grades.py` … `grades.json` の読み取り（`published_grades()` / `published_secondary_grades()` 等）
- `tools/build_grade.py <id>` … 1種を staging ビルドして `public_site/<id>` に配置（**公開可否に関係なくビルド可**。プレビュー用）
- `tools/rekey_grade.py` … II種固有語（ブランド名・試験名・コース名・級）を種側へ置換
- `tools/build_essays_pages.py` … 論述ハブ `essays/index.html`（`essays.csv` がある種のみ）
- `tools/build_site.py` … 全種一括。**`published=true` の種だけ**を `public_site/` に出す（本番用）

空データ（CSVヘッダのみ）でも壊れないよう、新種ビルドは環境変数 `EXAM_SKELETON=1` で
一部バリデーション/生成を骨組みモードにする（II種の通常ビルドでは未設定なので影響なし）。

## ローカルでのプレビュー（公開しない）

```bash
# 1種だけビルドして public_site/self を確認（published に関係なく作れる）
python3 tools/build_grade.py self
python3 -m http.server -d public_site 8000   # http://localhost:8000/self/ を開く

# 本番と同じ組み立て（公開対象のみ）を再現
python3 tools/build_site.py
```

`build_grade.py` は未公開の種もビルドできる（確認用）。`build_site.py` は未公開の種を
`public_site/` に出さない（本番で露出しない）。

## 本番公開のしくみ

- デプロイは `.github/workflows/deploy-pages.yml`：`main`/`master` への push（または手動実行）で発火。
- CI は `tools/ci_deploy_build.sh` → `python3 tools/build_site.py` を実行し `public_site/` を Pages へ。
- **`feature/*` ブランチへの push では本番公開は起きない。**

したがって `published=false` の間は、`main` にマージしても新種は本番に出ない（II種のみ公開）。

## 新種を本番公開する手順（go-live）

1. 中身を投入：`grades/<種>/data/*.csv`（過去問・用語・ガイド等）を拡充。
2. ローカル確認：`python3 tools/build_grade.py <種>` → `public_site/<種>/` を目視・リンク確認。
3. 公開フラグを立てる：`grades.json` の対象種 `"published": true`。
4. 全体ビルド確認：`python3 tools/build_site.py`（公開一覧に対象種が出ること、`sitemap-index.xml`・`robots.txt` に反映されること）。
5. `main` にマージ → GitHub Actions が `/<種>` を公開。

公開を取り下げるときは `published` を `false` に戻して再デプロイすれば `public_site/` から外れる。

## 検証の要点

- II種がバイト不変であること（`sitemap.xml` の日付、公開種追加に伴う `robots.txt` を除く）。
  ```bash
  cp -R public_site /tmp/ref && python3 tools/build_site.py
  diff -r /tmp/ref public_site -x sitemap.xml -x sitemap-index.xml
  ```
- 新種の basePath 整合：`public_site/<種>/index.html` の canonical/og が `…/<種>/`、
  過去問ハブのタブが `/<種>/q/…`。
- 他種語の混入が無いこと：`grep -rn '二種\|ラインケア' public_site/<種>`（`III種` は `II種` を含むので
  単独の `II種` は `grep -P '(?<!I)II種'` で確認）。

## 既知事項・今後

- 用語集一覧（`terms/index.html`）の検索プレースホルダ例に「ラインケア」が残る（II種共有の定数・汎用語。
  種別化は今後の小改修）。
- `exam-dates`（試験日程ページ）は本文がII種固定のため、新種では生成しない（`EXAM_SKELETON` でスキップ）。
  マルチ種対応は別途。
- 論述（I種）は現状ハブ `essays/index.html` のみ。個別テーマページの生成は今後。
- 各種の本文プロセ（about / privacy / related）はII種からの機械置換のため、公開前に人手レビュー推奨。
