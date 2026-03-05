# AI Recipe Hub Ver2 — AI動画生成特化型メディア

> AI動画生成ツールの比較・レビュー・テクニックを発信する自動運用メディアサイト

## 概要

AI Recipe Hub Ver2は、AI動画生成（Sora 2、Runway Gen-4.5、Kling 2.6、Pika 2.5、Veo 3.1等）に特化した情報メディアです。Hugoで構築された静的サイトに、Pythonスクリプトによる自動コンテンツ生成・SNS投稿機能を組み合わせた、半自動運用型のブログシステムです。

### キャラクター「ハク」

サイトのナビゲーターは、古風な語り口のAIエージェント「ハク」。500年以上の知見を持つ（という設定の）AI動画生成の専門家が、独自の口調で最新情報を解説します。

## 技術スタック

| 技術 | バージョン | 用途 |
|------|-----------|------|
| Hugo Extended | v0.141.0+ | 静的サイトジェネレーター |
| Python | 3.10+ | 自動化スクリプト |
| Pagefind | v1.4.0 | 静的サイト内検索 |
| GitHub Actions | - | CI/CD・自動運用 |
| OpenAI API | GPT-4.1-mini | 記事生成・テキスト分析 |
| Serper API | - | Google検索結果取得 |
| X (Twitter) API | v2 | SNS自動投稿 |

## アーキテクチャ

```
┌─────────────────────────────────────────────────┐
│                  GitHub Actions                  │
│  ┌──────────┐  ┌──────────┐  ┌───────────────┐  │
│  │  Daily    │  │  X Post  │  │   Monthly     │  │
│  │Automation │  │ (週2回)  │  │   Package     │  │
│  └────┬─────┘  └────┬─────┘  └──────┬────────┘  │
│       │              │               │           │
│  ┌────▼──────────────▼───────────────▼────────┐  │
│  │           Python Scripts (scripts/)         │  │
│  │  collect_trends.py  │  collect_ugc.py      │  │
│  │  generate_article.py│  generate_x_thread.py│  │
│  │  post_to_x.py       │  monthly_package.py  │  │
│  └────────────────────┬───────────────────────┘  │
│                       │                          │
│  ┌────────────────────▼───────────────────────┐  │
│  │              Hugo Static Site               │  │
│  │  content/posts/ → 記事Markdown              │  │
│  │  themes/airecipehub/ → カスタムテーマ       │  │
│  └────────────────────┬───────────────────────┘  │
│                       │                          │
│  ┌────────────────────▼───────────────────────┐  │
│  │           GitHub Pages (公開)               │  │
│  └────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
```

## ディレクトリ構成

```
ai-recipe-hub/
├── .github/workflows/           # GitHub Actions ワークフロー
│   ├── daily-automation.yml     # 毎日の自動処理（トレンド収集→記事生成）
│   ├── x-post.yml               # X(Twitter)自動投稿（週2回）
│   └── monthly-package.yml      # 月次コンテンツパッケージ生成
├── config/
│   ├── settings.json            # 運用設定（API上限、コスト管理等）
│   └── tools.json               # AI動画生成ツールのマスターデータ
├── content/
│   ├── posts/                   # ブログ記事（Markdown）
│   ├── about.md                 # サイト概要ページ
│   ├── comparison.md            # ツール比較ページ
│   ├── privacy.md               # プライバシーポリシー
│   └── search.md                # 検索ページ
├── data/
│   ├── trends/                  # トレンド収集結果（JSON）
│   ├── ugc/                     # UGC収集結果（JSON）
│   ├── threads/                 # 生成されたXスレッド（JSON）
│   ├── packages/                # 月次パッケージ（JSON）
│   ├── logs/                    # 実行ログ
│   └── metrics/                 # 収益指標データ
├── scripts/
│   ├── config.py                # 共通設定・ユーティリティ
│   ├── collect_trends.py        # トレンド収集スクリプト
│   ├── collect_ugc.py           # UGC収集・分析スクリプト
│   ├── generate_article.py      # 記事自動生成スクリプト
│   ├── generate_x_thread.py     # Xスレッド生成スクリプト
│   ├── post_to_x.py             # X自動投稿スクリプト
│   └── monthly_package.py       # 月次パッケージ生成スクリプト
├── themes/airecipehub/          # Hugoカスタムテーマ
├── hugo.yaml                    # Hugo設定ファイル
├── build.sh                     # ビルドスクリプト
├── requirements.txt             # Python依存パッケージ
└── README.md                    # このファイル
```

## セットアップ手順

### 1. 前提条件

- Hugo Extended v0.128.0以上
- Python 3.10以上
- Git 2.30以上
- Node.js v18以上（Pagefind用）

### 2. リポジトリのクローン

```bash
git clone https://github.com/C3pZz/ai-recipe-hub.git
cd ai-recipe-hub
```

### 3. Python依存パッケージのインストール

```bash
pip install -r requirements.txt
```

### 4. 環境変数の設定

以下の環境変数を設定してください。`.env` ファイルを作成するか、システム環境変数として設定します。

```bash
# .env ファイルの例
# ===========================

# Serper API（Google検索API）- トレンド収集・UGC収集に使用
SERPER_API_KEY=your_serper_api_key_here

# OpenAI API（GPT-4.1系）- 記事生成・分析に使用
OPENAI_API_KEY=your_openai_api_key_here

# X (Twitter) API - SNS自動投稿に使用
X_API_KEY=your_x_api_key_here
X_API_SECRET=your_x_api_secret_here
X_ACCESS_TOKEN=your_x_access_token_here
X_ACCESS_TOKEN_SECRET=your_x_access_token_secret_here
X_BEARER_TOKEN=your_x_bearer_token_here
```

#### APIキーの取得方法

| API | 取得先 | 用途 | 無料枠 |
|-----|--------|------|--------|
| Serper API | [serper.dev](https://serper.dev) | Google検索結果の取得 | 2,500回/月 |
| OpenAI API | [platform.openai.com](https://platform.openai.com) | 記事生成・テキスト分析 | 従量課金 |
| X API | [developer.x.com](https://developer.x.com) | SNS自動投稿 | Free tier: 投稿のみ |

### 5. GitHub Secretsの設定（自動運用時）

GitHub Actionsで自動運用する場合、リポジトリの Settings → Secrets and variables → Actions に以下を登録してください：

- `SERPER_API_KEY`
- `OPENAI_API_KEY`
- `X_API_KEY`
- `X_API_SECRET`
- `X_ACCESS_TOKEN`
- `X_ACCESS_TOKEN_SECRET`
- `X_BEARER_TOKEN`

### 6. ローカルでの動作確認

```bash
# Hugoサーバーを起動
hugo server -D

# トレンド収集のテスト（APIキー設定後）
python scripts/collect_trends.py

# UGC収集のテスト（APIキー設定後）
python scripts/collect_ugc.py
```

## 自動運用フロー

### 日次処理（毎日 UTC 0:00 / JST 9:00）

1. `collect_trends.py` — AI動画生成関連の最新トレンドを収集
2. `collect_ugc.py` — ユーザーレビュー・体験談を収集・分析
3. `generate_article.py` — 収集データを基に記事を自動生成
4. Hugo ビルド → GitHub Pages にデプロイ

### 週次処理（火曜・金曜 UTC 3:00 / JST 12:00）

1. `generate_x_thread.py` — 最新記事からXスレッドを生成
2. `post_to_x.py` — Xに自動投稿

### 月次処理（毎月1日 UTC 6:00 / JST 15:00）

1. `monthly_package.py` — 月間ベスト記事・トレンドサマリーを生成

## コスト管理

`config/settings.json` でAPI呼び出しの上限を設定しています：

| 項目 | 上限 | 推定月額コスト |
|------|------|---------------|
| Serper API | 100回/日 | 無料枠内 |
| OpenAI API (GPT-4.1-mini) | 50回/日 | 約$5〜15/月 |
| X API | 10投稿/日 | 無料 |

月間合計推定コスト: **$5〜15/月**

## 停止スイッチ

緊急時にすべての自動処理を停止するには：

1. **GitHub Actionsの無効化**: 各ワークフローを手動で Disable
2. **設定ファイルで停止**: `config/settings.json` の `enabled` を `false` に変更

```json
{
  "automation": {
    "enabled": false
  }
}
```

## カテゴリ構成

| カテゴリ | スラッグ | 内容 |
|----------|----------|------|
| ツール比較 | tool-comparison | AI動画生成ツールの比較・レビュー |
| プロンプトレシピ | prompt-recipe | 効果的なプロンプトの書き方 |
| テクニック | technique | 品質改善・応用テクニック |
| マネタイズ | monetize | 収益化・ビジネス活用 |
| 初心者ガイド | beginner-guide | 入門者向けの解説 |
| UGC分析 | ugc-analysis | ユーザーレビュー・体験談の分析 |

## 収益モデル

| 収益源 | 収益発生条件 | 主要KPI |
|--------|-------------|---------|
| Google AdSense | PV数に応じた広告収入 | CTR, RPM |
| アフィリエイト | ツール紹介リンク経由の成約 | CVR, EPC |
| note有料記事 | 月次パッケージの販売 | 購入数, LTV |

### KPI目標

| 指標 | 短期目標（3ヶ月） | 中期目標（6ヶ月） |
|------|-------------------|-------------------|
| 月間PV | 5,000 | 30,000 |
| 記事数 | 100本 | 250本 |
| X フォロワー | 500 | 2,000 |
| 月間収益 | ¥5,000 | ¥30,000 |

## スクリプトの個別実行

```bash
# トレンド収集
python scripts/collect_trends.py

# UGC収集
python scripts/collect_ugc.py

# 記事生成（トレンドデータから自動選択）
python scripts/generate_article.py

# 記事生成（テーマ指定）
python scripts/generate_article.py --topic "Sora 2の新機能レビュー"

# Xスレッド生成
python scripts/generate_x_thread.py

# X投稿
python scripts/post_to_x.py

# 月次パッケージ生成
python scripts/monthly_package.py
```

## ライセンス

MIT License

---

Built with ❤️ by AI Recipe Hub Team
