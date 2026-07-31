# este_analystics

[エステ魂（estama.jp）](https://estama.jp/) の公開情報を、**客目線**で再整理した非公式分析サイトです。

- 公開URL: https://jim-auto.github.io/este_analystics/
- 対象エリア: **東京（関東）・名古屋（中部）・大阪（関西）**

## 収集・公開している情報

| カテゴリ | 内容 |
|---------|------|
| 料金相場 | 90分料金の最低・最高・中央値・平均（店舗リストサンプルから集計） |
| ランキング | おもてなし / お店 / セラピスト TOP5 と順位変動 |
| クーポン | エステ魂限定クーポンのタイトル・条件・対象店舗 |
| 店舗属性 | 店舗型（マンション/出張など）、サブエリア分布 |

## 免責事項

- 本リポジトリは **エステ魂の非公式** プロジェクトです
- 予約・最新の空き状況は [公式サイト](https://estama.jp/) で必ずご確認ください
- 画像・口コミ本文の転載は行いません（集計・リンクのみ）

## ローカル実行

```bash
pip install -r requirements.txt
python -m scraper.run
```

生成物:

- `data/processed/*.json` — 加工済みデータ
- `docs/data/*.json` — GitHub Pages 用データ

ローカルプレビュー:

```bash
python -m http.server 8080 --directory docs
```

## GitHub Pages 設定

Repository → Settings → Pages → **Deploy from branch**

- Branch: `main`
- Folder: `/docs`

## データ更新

- 手動: Actions → "Update analytics data" → Run workflow
- 自動: 毎週月曜 00:00 JST（UTC 15:00 日曜）

## 技術構成

- 収集: Python + BeautifulSoup（urllib、2.5秒間隔）
- 公開: 静的 HTML + JSON（GitHub Pages）
- CI: GitHub Actions

## ライセンス

分析コードは MIT を想定。エステ魂のコンテンツ・商標は運営会社に帰属します。
