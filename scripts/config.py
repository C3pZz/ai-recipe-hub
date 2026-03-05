#!/usr/bin/env python3
"""
config.py - AI Recipe Hub 共通設定モジュール

全スクリプトで使用する設定値、パス、APIキーの読み込みを一元管理する。
APIキーはすべて環境変数から読み込み、ハードコーディングは禁止。
"""

import os
import json
import logging
import re
from typing import List, Pattern
from pathlib import Path
from datetime import datetime, timezone, timedelta

# ============================================================
# パス設定
# ============================================================
# プロジェクトルート（scriptsディレクトリの1つ上）
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# 各ディレクトリのパス
CONTENT_DIR = PROJECT_ROOT / "content" / "posts"
CONFIG_DIR = PROJECT_ROOT / "config"
DATA_DIR = PROJECT_ROOT / "data"
TRENDS_DIR = DATA_DIR / "trends"
UGC_DIR = DATA_DIR / "ugc"
THREADS_DIR = DATA_DIR / "threads"
LOGS_DIR = DATA_DIR / "logs"
METRICS_DIR = DATA_DIR / "metrics"
PACKAGES_DIR = DATA_DIR / "packages"

# ディレクトリが存在しなければ作成
for d in [CONTENT_DIR, TRENDS_DIR, UGC_DIR, THREADS_DIR, LOGS_DIR, METRICS_DIR, PACKAGES_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ============================================================
# 日時設定（JST）
# ============================================================
JST = timezone(timedelta(hours=9))
TODAY = datetime.now(JST).strftime("%Y-%m-%d")
THIS_MONTH = datetime.now(JST).strftime("%Y-%m")

# ============================================================
# API キー（環境変数から読み込み）
# ============================================================
SERPER_API_KEY = os.environ.get("SERPER_API_KEY", "")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
X_API_KEY = os.environ.get("X_API_KEY", "")
X_API_SECRET = os.environ.get("X_API_SECRET", "")
X_ACCESS_TOKEN = os.environ.get("X_ACCESS_TOKEN", "")
X_ACCESS_SECRET = os.environ.get("X_ACCESS_SECRET", "")
KLING_API_KEY = os.environ.get("KLING_API_KEY", "")
SLACK_WEBHOOK = os.environ.get("SLACK_WEBHOOK", "")

# ============================================================
# 設定ファイルの読み込み
# ============================================================
def load_json_config(filename: str) -> dict:
    """config/ ディレクトリからJSONファイルを読み込む"""
    filepath = CONFIG_DIR / filename
    if filepath.exists():
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

# 設定値の読み込み
SETTINGS = load_json_config("settings.json")
TOOLS_CONFIG = load_json_config("tools.json")

# ============================================================
# 対象ツールリスト
# ============================================================
TOOL_NAMES = [t["name"] for t in TOOLS_CONFIG.get("tools", [])]
# フォールバック
if not TOOL_NAMES:
    TOOL_NAMES = ["Kling", "Runway", "Sora", "Pika", "Veo"]

# ============================================================
# OpenAI API 設定
# ============================================================
OPENAI_MODEL = SETTINGS.get("api", {}).get("openai_model", "gpt-4o-mini")
OPENAI_MAX_TOKENS_ARTICLE = SETTINGS.get("api", {}).get("openai_max_tokens_article", 4000)
OPENAI_MAX_TOKENS_THREAD = SETTINGS.get("api", {}).get("openai_max_tokens_thread", 1500)
OPENAI_TEMPERATURE_ARTICLE = SETTINGS.get("api", {}).get("openai_temperature_article", 0.7)
OPENAI_TEMPERATURE_THREAD = SETTINGS.get("api", {}).get("openai_temperature_thread", 0.9)

# ============================================================
# Serper API 設定
# ============================================================
SERPER_RESULTS_PER_QUERY = SETTINGS.get("api", {}).get("serper_results_per_query", 5)
SERPER_COUNTRY = SETTINGS.get("api", {}).get("serper_country", "jp")
SERPER_LANGUAGE = SETTINGS.get("api", {}).get("serper_language", "ja")

# ============================================================
# コスト上限設定
# ============================================================
COST_LIMITS = SETTINGS.get("cost_limits", {})
MONTHLY_COST_LIMIT_USD = COST_LIMITS.get("monthly_total_usd", 100)
DAILY_OPENAI_LIMIT_USD = COST_LIMITS.get("daily_openai_usd", 5)
DAILY_SERPER_QUERY_LIMIT = COST_LIMITS.get("daily_serper_queries", 50)
MONTHLY_X_POST_LIMIT = COST_LIMITS.get("monthly_x_posts", 150)

# ============================================================
# X投稿設定
# ============================================================
X_JITTER_MAX = SETTINGS.get("x_posting", {}).get("jitter_max_seconds", 1800)
X_TWEET_INTERVAL_MIN = SETTINGS.get("x_posting", {}).get("tweet_interval_min_seconds", 5)
X_TWEET_INTERVAL_MAX = SETTINGS.get("x_posting", {}).get("tweet_interval_max_seconds", 15)
X_MAX_RETRIES = SETTINGS.get("x_posting", {}).get("max_retries", 3)

# ============================================================
# サイト設定
# ============================================================
SITE_BASE_URL = SETTINGS.get("site", {}).get("base_url", "https://c3pzz.github.io/ai-recipe-hub/")
SITE_AUTHOR = SETTINGS.get("site", {}).get("author", "ハク")
MAX_ARTICLES_PER_DAY = SETTINGS.get("site", {}).get("max_articles_per_day", 2)

# ============================================================
# UGC検索クエリパターン
# ============================================================
UGC_QUERY_PATTERNS = [
    "{tool} 使ってみた",
    "{tool} デメリット",
    "{tool} 退会 解約",
    "{tool} 料金 高い",
    "{tool} 比較 おすすめ",
]

# ============================================================
# 記事生成用システムプロンプト（ハクの口調）
# ============================================================
ARTICLE_SYSTEM_PROMPT = """あなたは「ハク」という名前の自律型AIエージェントです。
古風で知的な語り口で記事を書きます。

【口調ルール】
- 一人称は「儂（わし）」
- 語尾は「〜じゃ」「〜ぞ」「〜であるな」「〜じゃろう」
- 読者への呼びかけは「貴様」「汝」（ただし親しみを込めて）
- 知識を披露する際は「儂の知見によれば」「儂が検証した結果」
- 時折「ふむ」「うむ」などの間投詞を入れる
- 既存作品・既存キャラクター名は出さない
- 「〜風」「〜っぽい」など特定作品を連想させる表現は使わない

【記事品質ルール】
- 具体的な数値データを必ず含める
- 断定的すぎる表現は避け、検証結果に基づく表現を使う
- 読者が実際に試せるプロンプト例やステップを含める
- SEOを意識し、見出しにキーワードを含める
- front matterはYAML形式で出力する
- 記事の最後に「まとめ」セクションを必ず入れる
"""

# ============================================================
# 禁止IP参照の検出ルール
# ============================================================
FORBIDDEN_IP_PATTERNS: List[Pattern] = [
    re.compile(r"\u5fcd\u91ce\s*\u5fcd"),
    re.compile(r"\u7269\u8a9e\s*\u30b7\u30ea\u30fc\u30ba"),
    re.compile(r"Shinobu\s+Oshino", re.IGNORECASE),
    re.compile(r"Oshino\s+Shinobu", re.IGNORECASE),
]


def detect_forbidden_ip_terms(text: str) -> List[str]:
    """テキスト内の禁止IP参照を検出し、マッチしたパターンを返す。"""
    if not text:
        return []

    matched_patterns = []
    for pattern in FORBIDDEN_IP_PATTERNS:
        if pattern.search(text):
            matched_patterns.append(pattern.pattern)
    return matched_patterns

# ============================================================
# Xスレッド生成用システムプロンプト
# ============================================================
THREAD_SYSTEM_PROMPT = """あなたはAI動画生成を実際に使い倒している個人クリエイターです。
以下のルールを厳守してください：

【絶対禁止事項】
- 「〜と言えるでしょう」「〜が期待されます」等のAI特有の堅苦しい表現
- 「画期的な」「革新的な」等の大げさな形容詞
- 箇条書きの羅列

【必須事項】
- 少し泥臭い、個人の実体験のような口調で書く
- 「マジで」「ぶっちゃけ」「正直」等のカジュアルな表現を適度に使う
- 具体的な数字や体験を入れる
- 各ツイートは140文字以内（日本語）

【構成（5ツイート）】
1. フック（驚きや共感を誘う導入）
2. ノウハウ①（具体的なTips）
3. ノウハウ②（比較や数字）
4. まとめ・結論
5. 記事リンク + CTA（ここにのみリンクを配置）

各ツイートは「---」で区切って出力してください。
"""

# ============================================================
# コスト追跡ファイル
# ============================================================
COST_TRACKER_FILE = METRICS_DIR / "cost_tracker.json"

def load_cost_tracker() -> dict:
    """コスト追跡データを読み込む"""
    if COST_TRACKER_FILE.exists():
        with open(COST_TRACKER_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "monthly_total_usd": 0.0,
        "daily_costs": {},
        "last_updated": TODAY
    }

def save_cost_tracker(data: dict):
    """コスト追跡データを保存する"""
    data["last_updated"] = TODAY
    with open(COST_TRACKER_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def add_cost(amount_usd: float, category: str = "general"):
    """APIコストを記録する"""
    tracker = load_cost_tracker()
    # 月が変わったらリセット
    if not tracker.get("last_updated", "").startswith(THIS_MONTH):
        tracker["monthly_total_usd"] = 0.0
        tracker["daily_costs"] = {}
    tracker["monthly_total_usd"] = tracker.get("monthly_total_usd", 0) + amount_usd
    if TODAY not in tracker.get("daily_costs", {}):
        tracker["daily_costs"][TODAY] = {}
    daily = tracker["daily_costs"][TODAY]
    daily[category] = daily.get(category, 0) + amount_usd
    save_cost_tracker(tracker)

def check_cost_limit() -> bool:
    """コスト上限をチェック。Trueなら停止すべき"""
    tracker = load_cost_tracker()
    if tracker.get("monthly_total_usd", 0) >= MONTHLY_COST_LIMIT_USD:
        return True
    return False

# ============================================================
# ロガー設定
# ============================================================
def setup_logger(name: str, log_file: str = None) -> logging.Logger:
    """ロガーを設定して返す"""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # コンソールハンドラ
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    formatter = logging.Formatter(
        "%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # ファイルハンドラ
    if log_file:
        file_handler = logging.FileHandler(
            LOGS_DIR / log_file, encoding="utf-8"
        )
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger

# ============================================================
# JSON ログ記録
# ============================================================
def log_json(log_file: str, entry: dict):
    """JSON形式でログエントリを追記する"""
    filepath = LOGS_DIR / log_file
    entries = []
    if filepath.exists():
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                entries = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            entries = []

    entry["timestamp"] = datetime.now(JST).isoformat()
    entries.append(entry)

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)
