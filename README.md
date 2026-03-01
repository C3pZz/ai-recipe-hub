# AI Recipe Hub

**AIツール比較・レビュー専門メディア**

文章生成・画像生成・コーディング・業務効率化など、あらゆるカテゴリのAIツールを徹底比較するメディアサイトです。

## 技術スタック

| 技術 | 用途 |
|------|------|
| **Hugo v0.141.0** | 静的サイトジェネレーター |
| **Pagefind v1.4.0** | 静的サイト向け検索機能 |
| **カスタムテーマ (airecipe)** | モダンテック系デザイン |
| **GitHub Actions** | 自動ビルド・デプロイ・記事生成 |
| **OpenAI API** | 記事自動生成 (gpt-4o-mini) |

## ディレクトリ構成

```
ai-recipe-hub/
├── .github/
│   └── workflows/
│       ├── deploy.yml          # GitHub Pages自動デプロイ
│       └── auto-generate.yml   # 記事自動生成（毎日09:00 JST）
├── content/
│   ├── posts/                  # レビュー記事（Markdown）
│   ├── about.md
│   ├── comparison.md
│   ├── contact.md
│   ├── newsletter.md
│   ├── privacy.md
│   ├── affiliate-disclosure.md
│   └── search.md
├── data/
│   └── tools_queue.json        # 記事生成キュー
├── scripts/
│   ├── generate_article.py     # 記事自動生成スクリプト
│   ├── check_cost_limit.py     # APIコスト上限チェック（停止スイッチ）
│   ├── log_generation.py       # 生成ログ記録
│   └── gen_og_image.py         # OGイメージ生成
├── static/
│   ├── images/
│   │   └── og-image.png
│   ├── favicon.svg
│   └── robots.txt
├── themes/
│   └── airecipe/               # カスタムテーマ
│       ├── layouts/
│       │   ├── _default/
│       │   │   ├── baseof.html  # ベーステンプレート（SEO・OGP・構造化データ）
│       │   │   ├── single.html  # 記事ページ（ツール情報ボックス・アフィリエイトCTA）
│       │   │   └── list.html    # 一覧ページ
│       │   ├── index.html       # トップページ
│       │   ├── index.json       # 検索インデックス用JSON
│       │   ├── page/
│       │   │   └── search.html  # 検索ページ
│       │   ├── partials/
│       │   │   ├── header.html
│       │   │   ├── footer.html
│       │   │   └── search.html
│       │   └── 404.html
│       └── static/
│           ├── css/main.css     # メインCSS（ダークモード・レスポンシブ）
│           └── js/main.js       # メインJS（検索・アフィリエイトトラッキング）
├── logs/                        # 記事生成ログ（自動作成）
├── public/                      # ビルド出力（Gitignore対象）
├── hugo.yaml                    # Hugo設定
├── build.sh                     # ビルドスクリプト
└── README.md
```

## セットアップ

### 必要なツール

- Hugo Extended v0.128.0以上
- Node.js v18以上
- Python 3.9以上

### インストール

```bash
# Hugoのインストール (Ubuntu)
wget https://github.com/gohugoio/hugo/releases/download/v0.141.0/hugo_extended_0.141.0_linux-amd64.deb
sudo dpkg -i hugo_extended_0.141.0_linux-amd64.deb

# Pagefindのインストール
npm install -g pagefind

# Pythonパッケージのインストール
pip install openai
```

### ローカル開発

```bash
# 開発サーバー起動
hugo server

# ビルド
./build.sh

# ビルド + ローカルサーバー起動
./build.sh --serve
```

## 記事の追加方法

### 手動で記事を追加

`content/posts/` ディレクトリに Markdown ファイルを作成します。

```bash
# 新規記事の作成
hugo new posts/tool-name-review.md
```

フロントマターのテンプレート:

```yaml
---
title: "ツール名 レビュー：キャッチーなタイトル"
date: 2026-03-01
description: "SEO最適化されたメタディスクリプション（120文字以内）"
categories: ["文章生成AI"]
tags: ["ツール名", "カテゴリ"]
emoji: "🤖"
toolName: "ツール名"
toolTagline: "キャッチーな説明（30文字以内）"
toolPrice: "無料 / $20/月〜"
toolFreeplan: "あり"
toolCategory: "文章生成AI"
toolLanguage: "対応"
rating: 4.5
affiliateUrl: "https://example.com/?ref=airecipehub"
officialUrl: "https://example.com/"
featured: false
isNew: true
isPopular: false
draft: false
---
```

### 自動生成（OpenAI API）

```bash
# 特定のツールの記事を生成
python3 scripts/generate_article.py --tool-name "Gemini 2.0" --category "文章生成AI"

# キューから自動選択して生成
python3 scripts/generate_article.py
```

環境変数:
- `OPENAI_API_KEY`: OpenAI APIキー（必須）
- `OPENAI_MODEL`: 使用モデル（デフォルト: `gpt-4o-mini`）

## GitHub Pages へのデプロイ

### 初期設定

1. GitHubリポジトリを作成
2. Settings > Pages > Source を「GitHub Actions」に設定
3. Secrets に `OPENAI_API_KEY` を追加（記事自動生成を使う場合）
4. Variables に以下を設定:
   - `HUGO_BASE_URL`: サイトのURL（例: `https://username.github.io/ai-recipe-hub/`）
   - `MONTHLY_COST_LIMIT_USD`: 月間APIコスト上限（デフォルト: `10`）

### デプロイ

```bash
git push origin main
```

`main` ブランチへのプッシュで自動的にビルド・デプロイが実行されます。

## 収益化

### アフィリエイトリンクの設置

各記事のフロントマターに `affiliateUrl` を設定するだけで、自動的にアフィリエイトCTAボタンが表示されます。

```yaml
affiliateUrl: "https://example.com/?ref=airecipehub"
```

### 主要アフィリエイトプログラム

| ツール | プログラム | 報酬 |
|--------|-----------|------|
| Jasper AI | Impact.com | 30% 継続報酬 |
| Copy.ai | PartnerStack | 45% 初回 |
| Writesonic | 直接申込 | 30% 継続報酬 |
| Surfer SEO | PartnerStack | 25% 継続報酬 |

## 自動化の停止スイッチ

記事自動生成を停止するには:

1. **GitHub Actions から無効化**: GitHub > Actions > Auto Generate Articles > Disable workflow
2. **コスト上限による自動停止**: 月間APIコストが `MONTHLY_COST_LIMIT_USD` を超えると自動停止
3. **ログ確認**: `logs/generation_log.jsonl` で生成履歴とコストを確認

## KPI・収益指標

| 指標 | 目標 | 測定方法 |
|------|------|---------|
| 月間PV | 10,000 | Google Analytics |
| 記事数 | 100本/月 | logs/generation_log.jsonl |
| アフィリエイト収益 | $500/月 | 各ASPダッシュボード |
| CVR | 2〜5% | アフィリエイトASP |
| 月間APIコスト | $10以下 | logs/generation_log.jsonl |

## ライセンス

MIT License

---

Built with ❤️ by AI Recipe Hub Team
