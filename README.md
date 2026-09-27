# place-list-builder

名称とエリアのリストに、Google Places API で電話番号を付けてCSV出力するPythonツールです。
Webサイトの一覧ページから名称・エリアを収集する機能もあります。

営業リストや架電リストの作成を、手作業から自動化する目的で作成しました。

## できること

1. 一覧ページから「名称・エリア・詳細URL」を収集（任意）
2. 名称とエリアが重複する行や、名称が空の行を除外
3. Google Places API で電話番号を取得
4. 結果をCSVで出力（Excelで文字化けしない UTF-8 BOM 付き）

## 工夫した点

- **途中再開**：処理済みの行を出力CSVから読み取ってスキップするため、途中で止まっても続きから再開できます
- **誤取得の防止**：検索結果の住所に指定エリアが含まれない場合は採用しません（同名の別店舗を拾うのを防ぎます）
- **リトライ処理**：通信エラーやAPIエラーの際は自動で再試行します
- **APIキーの安全な管理**：キーはコードに書かず、`.env`（環境変数）から読み込みます
- **サイトへの配慮**：robots.txt の確認と、リクエストごとの待機時間を入れています

## 使用技術

Python / requests / BeautifulSoup / Google Places API (Text Search) / CSV

## 使い方

```bash
pip install -r requirements.txt
```

`.env.example` をコピーして `.env` を作成し、APIキーを設定します。

```bash
# 既存のリストに電話番号を付ける
python main.py --input sample_input.csv --output output.csv

# 一覧ページから収集して電話番号を付ける（scraper.py の設定を対象サイトに合わせて変更）
python main.py --scrape --max-pages 5
```

## 入出力の形式

| 入力（sample_input.csv） | 出力（output.csv） |
|---|---|
| 名称, エリア, URL, カテゴリ | 名称, エリア, URL, カテゴリ, 電話番号 |

## 注意事項

- スクレイピングを行う場合は、対象サイトの利用規約でデータ収集が禁止されていないことを事前に確認してください
- Google Places API は従量課金です。Google Cloud Console で利用上限や予算アラートの設定をおすすめします
- `sample_input.csv` は架空のダミーデータです
