# 知識ハブ執筆 — 正確性チェックログ（mentalhealth）

## パイロット S30 — 完了

| 種別 | 件数 | validate | build | 本番 |
|------|------|----------|-------|------|
| 比較・整理表 | 10 | ✅ | ✅ | ✅ |
| 数値・期限早見表 | 10 | ✅ | ✅ | ✅ |
| よくある誤答 | 10 | ✅ | ✅ | ✅ |

**監修メモ:** 試験合格点（70/100）・2026年度日程は [公式要項](https://www.mental-health.ne.jp/guide/)・[試験のご紹介](https://www.mental-health.ne.jp/about/) に基づく。法令数値は年度・改正で変わるため、公開後も専門家による再確認を推奨。

---

## 本番 URL

- 比較: https://mentalhealth-master.jp/terms/compare/index.html
- 数値: https://mentalhealth-master.jp/terms/numbers/index.html
- 誤答: https://mentalhealth-master.jp/terms/mistakes/index.html

---

## 公開前ゲート（1記事追加時）

1. `related_terms` を glossary で実在確認
2. `validate_csv.py` ERROR 0
3. `build_*` → `prepare_public_site.sh`
4. 数値・試験日程は一次情報で照合
5. commit / push → 本番 curl 確認
