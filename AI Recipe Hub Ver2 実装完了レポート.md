# AI Recipe Hub Ver2 実装完了レポート

## 1. 結論

AI Recipe Hub Ver2（AI動画生成特化型）の全コード実装が完了しました。既存リポジトリ `C3pZz/ai-recipe-hub` をベースに、AI動画生成に特化したメディアサイトへの全面改修を行いました。

## 2. 実装内容サマリー

### push済み（GitHub: `C3pZz/ai-recipe-hub` mainブランチ）

| カテゴリ | ファイル数 | 内容 |
|----------|-----------|------|
| Hugo設定 | 1 | `hugo.yaml` - サイトタイトル・カテゴリ・メニュー全面改修 |
| コンテンツページ | 4 | about.md, comparison.md, privacy.md, search.md |
| 初期記事 | 10 | AI動画生成特化の記事（ハクの口調で執筆） |
| Pythonスクリプト | 7 | config.py, collect_trends.py, collect_ugc.py, generate_article.py, generate_x_thread.py, post_to_x.py, monthly_package.py |
| 設定ファイル | 3 | config/settings.json, config/tools.json, .env.example |
| ドキュメント | 2 | README.md, requirements.txt |
| その他 | 2 | .gitignore更新, data/ディレクトリ構造 |

### 未push（workflows権限不足 → 手動追加が必要）

| ファイル | 内容 |
|----------|------|
| `.github/workflows/daily-automation.yml` | 日次自動処理（トレンド収集→記事生成→デプロイ） |
| `.github/workflows/x-post.yml` | X自動投稿（週2回） |
| `.github/workflows/monthly-package.yml` | 月次コンテンツパッケージ生成 |

## 3. 初期記事一覧

| # | タイトル | カテゴリ | 文字数 |
|---|---------|----------|--------|
| 1 | 【2026年最新】AI動画生成ツール5選をハクが本気で比較してみた | tool-comparison | ~3,500 |
| 2 | Kling 2.6 vs Runway Gen-4.5 — 無料枠で始めるならどっち？徹底検証レポート | tool-comparison | ~3,000 |
| 3 | Soraだけじゃない！2026年に注目すべきAI動画生成の新星たち | tool-comparison | ~2,500 |
| 4 | スマホだけで完結！初心者のためのAI動画作成入門 | beginner-guide | ~3,500 |
| 5 | 商用利用はどこまでOK？主要AI動画生成ツールのライセンスを徹底調査 | monetize | ~3,300 |
| 6 | noteで発見！すごいAI動画クリエイターたちのレビュー記事まとめ＆分析 | ugc-analysis | ~3,200 |
| 7 | 儂が検証！『テキスト→動画』の精度が低いときの5つの改善テクニック | technique | ~3,500 |
| 8 | AI動画生成で月5万円は稼げるか？マネタイズ方法7選を本気で考察 | monetize | ~3,900 |
| 9 | 【失敗談】儂がAI動画生成でやらかした珍妙なアウトプット集 | beginner-guide | ~3,500 |
| 10 | 1週間で学ぶ！AI動画制作スキル習得ロードマップ【スクール情報付き】 | beginner-guide | ~3,400 |

## 4. Pythonスクリプト構成

| スクリプト | 機能 | 使用API |
|-----------|------|---------|
| `config.py` | 共通設定・ログ・ユーティリティ | - |
| `collect_trends.py` | AI動画生成トレンド収集 | Brave Search API |
| `collect_ugc.py` | UGC（ユーザーレビュー）収集・分析 | Brave Search API |
| `generate_article.py` | 記事自動生成 | Gemini API |
| `generate_x_thread.py` | Xスレッド生成 | Gemini API |
| `post_to_x.py` | X自動投稿 | X API v2 (tweepy) |
| `monthly_package.py` | 月次コンテンツパッケージ生成 | Gemini API |

## 5. 環境変数一覧（すべて未設定 → 後から差し込み）

| 変数名 | 用途 | 取得先 |
|--------|------|--------|
| `BRAVE_SEARCH_API_KEY` | Web検索結果取得 | api.search.brave.com |
| `GEMINI_API_KEY` | 記事生成・テキスト分析 | aistudio.google.com |
| `X_API_KEY` | X投稿 | developer.x.com |
| `X_API_SECRET` | X投稿 | developer.x.com |
| `X_ACCESS_TOKEN` | X投稿 | developer.x.com |
| `X_ACCESS_TOKEN_SECRET` | X投稿 | developer.x.com |
| `X_BEARER_TOKEN` | X投稿 | developer.x.com |

## 6. コスト見積もり

| 項目 | 月額推定 |
|------|---------|
| Brave Search API | 無料枠内（2,000回/月、ハード上限で超過防止） |
| Gemini API | 無料枠内（15 req/分、1,500 req/日） |
| X API | 約$0.40/月（週2回×5ポスト想定、$0.01/作成） |
| Hugo/GitHub Pages | 無料 |
| **合計** | **約$0.40〜$2.00/月（約60〜300円）** |

## 7. 収益仮説

| 収益源 | 3ヶ月後目標 | 6ヶ月後目標 |
|--------|-----------|-----------|
| AdSense | ¥1,000〜3,000/月 | ¥5,000〜15,000/月 |
| アフィリエイト | ¥2,000〜5,000/月 | ¥10,000〜30,000/月 |
| note有料記事 | ¥0〜1,000/月 | ¥3,000〜10,000/月 |
| **合計** | **¥3,000〜9,000/月** | **¥18,000〜55,000/月** |

損益分岐点: 月間PV 3,000〜5,000（AdSense RPM ¥300想定）

## 8. リスク

| リスク | 対策 |
|--------|------|
| API規約違反 | 各APIの利用規約を遵守、レート制限設定済み |
| コンテンツ品質低下 | Gemini出力を人間がレビュー可能な設計 |
| API費用超過 | config/settings.jsonで日次上限を設定 |
| GitHub Actions障害 | 手動実行も可能な設計 |
| X凍結リスク | 投稿頻度を週2回に制限、スパム判定回避 |

## 9. 次のアクション

1. **ワークフローファイルの手動追加**: 添付の3ファイルをGitHub Web UIから追加
2. **APIキーの取得・設定**: GitHub Secretsに各APIキーを登録
3. **GitHub Pages有効化**: Settings → Pages → Source を「GitHub Actions」に設定
4. **初回動作確認**: ワークフローの手動実行でテスト
5. **AdSense/アフィリエイト申請**: PV蓄積後に申請
