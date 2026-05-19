#!/usr/bin/env bash
# GitHub Pages 用: SPA（index.html）＋生成済みデータ・静的ページを public_site/ に配置する。
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$ROOT/public_site"
rm -rf "$OUT"
mkdir -p "$OUT"
cd "$ROOT"
for f in \
  index.html \
  about.html \
  privacy.html \
  related-sites.html \
  site-config.json \
  site-config.js \
  site-pages.css \
  site-theme.css \
  site-analytics.js \
  CNAME \
  robots.txt \
  sitemap.xml \
  .nojekyll \
  eisei1-master-data.js \
  eisei1-data-glossary.js \
  eisei1-data-original.js \
  eisei1-data-ichimon.js \
  exam-site-data.js \
  exam-site-data-glossary.js \
  exam-site-data-original.js \
  exam-site-data-ichimon.js
do
  if [[ ! -e "$f" ]]; then
    echo "prepare_public_site.sh: 必須ファイルがありません: $f" >&2
    echo "先に python3 tools/csv_to_exam_site_master.py と各生成スクリプトを実行してください。" >&2
    exit 1
  fi
  cp "$f" "$OUT/"
done
for d in articles q terms; do
  if [[ -d "$ROOT/$d" ]]; then
    cp -R "$ROOT/$d" "$OUT/"
  fi
done
n="$(find "$OUT" -type f | wc -l | tr -d ' ')"
echo "prepare_public_site.sh: $OUT に $n ファイルを配置しました。"
