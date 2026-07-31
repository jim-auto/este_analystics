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
| 口コミ統計 | 平均評価・満点率・注意フラグ率、エリア別サマリー |
| 掲示板 | 爆サイ掲示板（総合＋お店板）の投稿サンプル・キーワード・店名突合 |
| クロス分析 | 公式口コミ × 掲示板のギャップ検出（信号ラベル付き） |
| 店舗索引 | 口コミ・掲示板・ランキング・クーポンに登場した店舗の統合ページ |
| サブエリア | エリア別料金相場・注意信号店・コスパ店のドリルダウン |
| 週次履歴 | 料金中央値・ギャップ数などのスナップショット推移 |
| 今週の注目 | 新規ギャップ店、ランキング UP、掲示板キーワード急増 |

## サイト構成

| ページ | 説明 |
|--------|------|
| `index.html` | 3エリア概要、今週の注目、人気サブエリア、週次推移 |
| `area.html` | エリア別詳細（料金・ランキング・クーポン） |
| `compare.html` | 3エリア横断比較 |
| `reviews.html` | 口コミ統計・注意口コミ一覧 |
| `bbs.html` | 掲示板分析・キーワード |
| `cross.html` | クロス分析詳細 |
| `shops.html` | 店舗索引（検索・エリア・信号フィルタ） |
| `shop.html` | 店舗詳細（口コミ・掲示板・信号） |
| `subareas.html` | サブエリア一覧（検索・並び替え） |
| `subarea.html` | サブエリア詳細 |
| `guide.html` | 初めての方向けガイド |

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
- `data/history/YYYY-MM-DD/metrics.json` — 週次スナップショット
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

収集規模（デフォルト）:

- 店舗リスト: 10ページ（最大1000件/エリア）
- 口コミ: 5ページ
- 掲示板: エリアごとに総合板＋お店板、各5スレッド

## 技術構成

- 収集: Python + BeautifulSoup（urllib、2.5秒間隔、3回リトライ）
- 公開: 静的 HTML + JSON（GitHub Pages）
- CI: GitHub Actions

## ライセンス

分析コードは MIT を想定。エステ魂のコンテンツ・商標は運営会社に帰属します。
