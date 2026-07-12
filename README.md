# AI Trend Monitor

AI Trend Monitor は、AI 関連ニュース・研究・ツール情報を毎日収集し、日本語の要約、トレンド集計、GitHub の注目 AI リポジトリ情報を生成するための小規模なモニタリングプロジェクトです。生成された JSON / テキストデータは `index.html` から静的サイトとして閲覧でき、月次では PDF レポートも作成します。

https://masaowatanabe1129.github.io/ai-trend-monitor/
でアクセス

## 主な機能

- RSS フィードから AI 関連の記事・論文・ニュースを収集
- OpenAI API を使った日本語要約と日次サマリー生成
- 記事タイトル・概要からの簡易トレンドワード抽出
- AI 技術トピックのランキングと履歴保存
- GitHub Search API による注目 AI ツール / リポジトリの取得
- 収集結果を表示する静的ダッシュボード
- 月次のトレンド差分分析と PDF レポート生成
- GitHub Actions による日次・月次の自動実行

## プロジェクト構成

```text
.
├── main.py                    # 日次データ収集・要約・トレンド生成スクリプト
├── monthly_report.py          # 月次 PDF レポート生成スクリプト
├── index.html                 # 生成済みデータを表示する静的ダッシュボード
├── requirements.txt           # Python 依存パッケージ
├── data/                      # 日次 JSON、最新データ、ランキング、サマリーなど
├── reports/                   # 月次 PDF レポート出力先
└── .github/workflows/
    ├── daily.yml              # 毎日実行する GitHub Actions
    └── monthly.yml            # 毎月実行する GitHub Actions
```

## データ収集元

`main.py` では、次のような RSS フィードを参照しています。

- arXiv: `cs.AI`, `cs.CL`, `cs.LG`
- Hugging Face Blog
- Google DeepMind Blog
- MarkTechPost
- Artificial Intelligence News
- VentureBeat AI
- GitHub Trending RSS

GitHub の注目ツールは GitHub Search API から `AI agent OR LLM OR AI coding` という条件で取得しています。

## 生成される主なファイル

| ファイル | 内容 |
| --- | --- |
| `data/YYYY-MM-DD.json` | 実行日の記事タイトル、リンク、OpenAI による分析結果 |
| `data/latest.json` | 最新の日次結果。`index.html` のニュース一覧で使用 |
| `data/trends.json` | 記事本文から抽出した頻出語ランキング |
| `data/trend_summary.txt` | 今日の AI 業界サマリー |
| `data/topic_ranking.json` | OpenAI による AI 技術トピックランキング |
| `data/topic_history.json` | 日別トピックランキング履歴 |
| `data/github_ai.json` | GitHub 上の注目 AI リポジトリ |
| `reports/AI_Monthly_Report_YYYY-MM.pdf` | 月次 AI 戦略レポート |

## セットアップ

### 1. Python 環境を用意する

Python 3.11 以上を推奨します。

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. OpenAI API キーを設定する

日次要約と月次分析で OpenAI API を使用します。

```bash
export OPENAI_API_KEY="your-api-key"
```

## 使い方

### 日次データを生成する

```bash
python main.py
```

このコマンドは RSS / GitHub から情報を収集し、`data/` 配下に日次データ、最新データ、サマリー、ランキングを出力します。

### ダッシュボードを表示する

`index.html` は `fetch()` で `data/` 配下のファイルを読み込むため、ローカルファイルとして直接開くよりも簡易 HTTP サーバー経由で開くのがおすすめです。

```bash
python -m http.server 8000
```

ブラウザで <http://localhost:8000/> を開くと、以下を確認できます。

- 今日の AI 業界サマリー
- AI トレンドの前日比
- 注目 AI ツール / GitHub リポジトリ
- 最新 AI ニュース一覧

### 月次レポートを生成する

```bash
python monthly_report.py
```

実行月と前月の `data/YYYY-MM-DD.json` を集計し、`reports/AI_Monthly_Report_YYYY-MM.pdf` を生成します。

## GitHub Actions による自動実行

このリポジトリには 2 つのワークフローがあります。

### 日次更新

`.github/workflows/daily.yml` は毎日 UTC 00:00 に実行されます。

1. Python 3.11 をセットアップ
2. `requirements.txt` をインストール
3. `python main.py` を実行
4. `data/` 配下の更新をコミットして push

### 月次レポート

`.github/workflows/monthly.yml` は毎月 1 日 UTC 01:00 に実行されます。

1. Python 3.11 をセットアップ
2. `requirements.txt` をインストール
3. `python monthly_report.py` を実行
4. `reports/` 配下の更新をコミットして push

GitHub Actions で動かす場合は、リポジトリの Secrets に `OPENAI_API_KEY` を登録してください。

## 注意点

- `main.py` と `monthly_report.py` は OpenAI API キーが必要です。
- RSS フィードや GitHub API のレスポンス内容により、収集件数は日によって変動します。
- `main.py` の記事分析プロンプトは日本語要約を要求していますが、内部では JSON パースを試みる実装になっています。そのため、既存データには `json_parse` エラーと `raw` 要約が保存されている場合があります。
- `monthly_report.py` は記事分析結果の `tech_category` を集計対象にしています。日次データにこのキーが存在しない場合は `unknown` として扱われます。
- GitHub Actions の自動コミットは、更新差分がない場合に `git commit` が失敗する可能性があります。必要に応じてワークフロー側で差分チェックを追加してください。

## ライセンス

このプロジェクトは MIT License です。詳細は `LICENSE` を参照してください。
