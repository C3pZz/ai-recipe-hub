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
import time
import math
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
BRAVE_SEARCH_API_KEY = os.environ.get("BRAVE_SEARCH_API_KEY", "") or os.environ.get("SERPER_API_KEY", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
# 互換性維持のため残す（新規利用は非推奨）
SERPER_API_KEY = BRAVE_SEARCH_API_KEY
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
X_API_KEY = os.environ.get("X_API_KEY", "")
X_API_SECRET = os.environ.get("X_API_SECRET", "")
X_ACCESS_TOKEN = os.environ.get("X_ACCESS_TOKEN", "")
X_ACCESS_SECRET = os.environ.get("X_ACCESS_SECRET", "") or os.environ.get("X_ACCESS_TOKEN_SECRET", "")
X_BEARER_TOKEN = os.environ.get("X_BEARER_TOKEN", "")
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
# Gemini API 設定
# ============================================================
GEMINI_MODEL = SETTINGS.get("api", {}).get("gemini_model", SETTINGS.get("api", {}).get("openai_model", "gemini-2.5-flash"))
GEMINI_MAX_OUTPUT_TOKENS_ARTICLE = SETTINGS.get("api", {}).get("gemini_max_output_tokens_article", SETTINGS.get("api", {}).get("openai_max_tokens_article", 4000))
GEMINI_MAX_OUTPUT_TOKENS_THREAD = SETTINGS.get("api", {}).get("gemini_max_output_tokens_thread", SETTINGS.get("api", {}).get("openai_max_tokens_thread", 1500))
GEMINI_MAX_OUTPUT_TOKENS_PACKAGE = SETTINGS.get("api", {}).get("gemini_max_output_tokens_package", 6000)
GEMINI_TEMPERATURE_ARTICLE = SETTINGS.get("api", {}).get("gemini_temperature_article", SETTINGS.get("api", {}).get("openai_temperature_article", 0.7))
GEMINI_TEMPERATURE_THREAD = SETTINGS.get("api", {}).get("gemini_temperature_thread", SETTINGS.get("api", {}).get("openai_temperature_thread", 0.9))
GEMINI_TEMPERATURE_PACKAGE = SETTINGS.get("api", {}).get("gemini_temperature_package", 0.7)

# 互換性維持（既存スクリプト向け）
OPENAI_MODEL = GEMINI_MODEL
OPENAI_MAX_TOKENS_ARTICLE = GEMINI_MAX_OUTPUT_TOKENS_ARTICLE
OPENAI_MAX_TOKENS_THREAD = GEMINI_MAX_OUTPUT_TOKENS_THREAD
OPENAI_TEMPERATURE_ARTICLE = GEMINI_TEMPERATURE_ARTICLE
OPENAI_TEMPERATURE_THREAD = GEMINI_TEMPERATURE_THREAD

# ============================================================
# Brave Search API 設定
# ============================================================
BRAVE_RESULTS_PER_QUERY = SETTINGS.get("api", {}).get("brave_results_per_query", SETTINGS.get("api", {}).get("serper_results_per_query", 5))
BRAVE_COUNTRY = SETTINGS.get("api", {}).get("brave_country", SETTINGS.get("api", {}).get("serper_country", "JP")).upper()
BRAVE_SEARCH_LANG = SETTINGS.get("api", {}).get("brave_search_lang", SETTINGS.get("api", {}).get("serper_language", "ja"))
BRAVE_SAFESEARCH = SETTINGS.get("api", {}).get("brave_safesearch", "moderate")

# 互換性維持（既存スクリプト向け）
SERPER_RESULTS_PER_QUERY = BRAVE_RESULTS_PER_QUERY
SERPER_COUNTRY = BRAVE_COUNTRY
SERPER_LANGUAGE = BRAVE_SEARCH_LANG

# ============================================================
# コスト上限設定
# ============================================================
COST_LIMITS = SETTINGS.get("cost_limits", {})
MONTHLY_COST_LIMIT_USD = COST_LIMITS.get("monthly_total_usd", 100)
DAILY_GEMINI_REQUEST_LIMIT = min(int(COST_LIMITS.get("daily_gemini_requests", 1500)), 1500)
GEMINI_REQUESTS_PER_MINUTE_LIMIT = min(int(COST_LIMITS.get("gemini_requests_per_minute", 15)), 15)
MONTHLY_BRAVE_QUERY_LIMIT = min(int(COST_LIMITS.get("monthly_brave_queries", 2000)), 2000)
DAILY_BRAVE_QUERY_LIMIT = min(int(COST_LIMITS.get("daily_brave_queries", COST_LIMITS.get("daily_serper_queries", 50))), MONTHLY_BRAVE_QUERY_LIMIT)
MONTHLY_X_BUDGET_USD = float(COST_LIMITS.get("monthly_x_budget_usd", 2.0))
X_API_PRICING = SETTINGS.get("x_api_pricing", {})
X_CONTENT_CREATE_COST_USD = float(X_API_PRICING.get("content_create_usd", 0.01))
DAILY_X_CONTENT_CREATE_LIMIT = int(COST_LIMITS.get("daily_x_content_create_limit", 10))
default_monthly_x_create_limit = int(math.floor(MONTHLY_X_BUDGET_USD / X_CONTENT_CREATE_COST_USD)) if X_CONTENT_CREATE_COST_USD > 0 else 0
configured_monthly_x_create_limit = int(COST_LIMITS.get("monthly_x_content_create_limit", default_monthly_x_create_limit))
if default_monthly_x_create_limit > 0:
    MONTHLY_X_CONTENT_CREATE_LIMIT = min(configured_monthly_x_create_limit, default_monthly_x_create_limit)
else:
    MONTHLY_X_CONTENT_CREATE_LIMIT = configured_monthly_x_create_limit

# 互換性維持（既存スクリプト向け）
DAILY_OPENAI_LIMIT_USD = COST_LIMITS.get("daily_openai_usd", 5)
DAILY_SERPER_QUERY_LIMIT = DAILY_BRAVE_QUERY_LIMIT
MONTHLY_X_POST_LIMIT = COST_LIMITS.get("monthly_x_posts", MONTHLY_X_CONTENT_CREATE_LIMIT)

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
            data = json.load(f)
    else:
        data = {
            "monthly_total_usd": 0.0,
            "daily_costs": {},
            "daily_usage": {},
            "monthly_usage": {},
            "gemini_recent_requests_unix": [],
            "last_updated": TODAY
        }

    # 後方互換: 古いフォーマットを補完
    data.setdefault("monthly_total_usd", 0.0)
    data.setdefault("daily_costs", {})
    data.setdefault("daily_usage", {})
    data.setdefault("monthly_usage", {})
    data.setdefault("gemini_recent_requests_unix", [])
    data.setdefault("last_updated", TODAY)
    return data


def new_tracker_data() -> dict:
    """新しいトラッカーデータを返す。"""
    return {
        "monthly_total_usd": 0.0,
        "daily_costs": {},
        "daily_usage": {},
        "monthly_usage": {},
        "gemini_recent_requests_unix": [],
        "last_updated": TODAY
    }


def _prepare_tracker(tracker: dict):
    """日付・月ごとの使用量集計領域を初期化する。"""
    tracker.setdefault("daily_costs", {})
    tracker.setdefault("daily_usage", {})
    tracker.setdefault("monthly_usage", {})
    tracker.setdefault("gemini_recent_requests_unix", [])

    tracker["daily_costs"].setdefault(TODAY, {})
    tracker["daily_usage"].setdefault(TODAY, {})
    tracker["monthly_usage"].setdefault(THIS_MONTH, {})


def save_cost_tracker(data: dict):
    """コスト追跡データを保存する"""
    data["last_updated"] = TODAY
    with open(COST_TRACKER_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _reset_tracker_if_new_month(tracker: dict):
    """月が変わったら月次コストだけリセットする。"""
    if not tracker.get("last_updated", "").startswith(THIS_MONTH):
        tracker["monthly_total_usd"] = 0.0
        tracker["daily_costs"] = {}
        tracker["daily_usage"] = {}
        tracker["gemini_recent_requests_unix"] = []


def add_cost(amount_usd: float, category: str = "general"):
    """APIコストを記録する"""
    tracker = load_cost_tracker()
    _reset_tracker_if_new_month(tracker)
    _prepare_tracker(tracker)
    tracker["monthly_total_usd"] = tracker.get("monthly_total_usd", 0) + amount_usd
    daily = tracker["daily_costs"][TODAY]
    daily[category] = daily.get(category, 0) + amount_usd
    save_cost_tracker(tracker)


def reserve_usage(category: str, units: int = 1, daily_limit: int = None, monthly_limit: int = None) -> bool:
    """
    使用量を先に予約する（上限を超える場合はFalse）。
    失敗時にAPIを呼ばないことで、従量課金の超過を防ぐ。
    """
    if units <= 0:
        return True

    tracker = load_cost_tracker()
    _reset_tracker_if_new_month(tracker)
    _prepare_tracker(tracker)

    daily_usage = tracker["daily_usage"][TODAY].get(category, 0)
    monthly_usage = tracker["monthly_usage"][THIS_MONTH].get(category, 0)

    if daily_limit is not None and daily_usage + units > daily_limit:
        return False
    if monthly_limit is not None and monthly_usage + units > monthly_limit:
        return False

    tracker["daily_usage"][TODAY][category] = daily_usage + units
    tracker["monthly_usage"][THIS_MONTH][category] = monthly_usage + units
    save_cost_tracker(tracker)
    return True


def get_usage(category: str, scope: str = "daily") -> int:
    """使用量を取得する。scopeはdailyまたはmonthly。"""
    tracker = load_cost_tracker()
    _reset_tracker_if_new_month(tracker)
    _prepare_tracker(tracker)

    if scope == "monthly":
        return int(tracker["monthly_usage"][THIS_MONTH].get(category, 0))
    return int(tracker["daily_usage"][TODAY].get(category, 0))


def reserve_gemini_request() -> bool:
    """
    Gemini APIリクエストを予約する。
    - 1日上限（無料枠: 1,500）
    - 1分上限（無料枠: 15）
    """
    tracker = load_cost_tracker()
    _reset_tracker_if_new_month(tracker)
    _prepare_tracker(tracker)

    daily = tracker["daily_usage"][TODAY].get("gemini_requests", 0)
    if daily + 1 > DAILY_GEMINI_REQUEST_LIMIT:
        return False

    now_unix = time.time()
    recent = tracker.get("gemini_recent_requests_unix", [])
    recent = [ts for ts in recent if (now_unix - ts) < 60]
    if len(recent) >= GEMINI_REQUESTS_PER_MINUTE_LIMIT:
        tracker["gemini_recent_requests_unix"] = recent
        save_cost_tracker(tracker)
        return False

    tracker["daily_usage"][TODAY]["gemini_requests"] = daily + 1
    monthly = tracker["monthly_usage"][THIS_MONTH].get("gemini_requests", 0)
    tracker["monthly_usage"][THIS_MONTH]["gemini_requests"] = monthly + 1
    recent.append(now_unix)
    tracker["gemini_recent_requests_unix"] = recent
    save_cost_tracker(tracker)
    return True

def check_cost_limit() -> bool:
    """コスト上限をチェック。Trueなら停止すべき"""
    tracker = load_cost_tracker()
    # 月初は前月コストを無視して新しい月として扱う
    if not tracker.get("last_updated", "").startswith(THIS_MONTH):
        return False
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
