#!/usr/bin/env python3
"""
generate_x_thread.py - X（Twitter）用5連スレッドを自動生成するスクリプト

記事の内容から5連スレッド形式のテキストを生成する。
1〜4ツイート目は純粋なノウハウ（リンクなし）、
5ツイート目にCTA + 記事リンクを配置する。

実行タイミング: 毎日 AM11:45 JST頃（x-post.ymlワークフロー内）
出力先: data/threads/YYYY-MM-DD.json
"""

import sys
import os
import json
import re
import glob
import requests

from config import (
    GEMINI_API_KEY, GEMINI_MODEL, GEMINI_MAX_OUTPUT_TOKENS_THREAD,
    GEMINI_TEMPERATURE_THREAD, THREAD_SYSTEM_PROMPT,
    TODAY, CONTENT_DIR, THREADS_DIR, SITE_BASE_URL,
    check_cost_limit, add_cost,
    setup_logger, log_json, detect_forbidden_ip_terms,
    reserve_gemini_request
)

logger = setup_logger("generate_x_thread", "generate.log")


def validate_gemini_key():
    """Gemini APIキーが設定されているか確認する。"""
    if not GEMINI_API_KEY:
        logger.error("GEMINI_API_KEY が設定されていません")
        sys.exit(1)


def find_latest_article() -> dict:
    """
    最新の記事ファイルを見つけて内容を読み込む。

    Returns:
        記事情報の辞書（title, summary, url, filepath）
    """
    # 今日の記事を探す
    pattern = str(CONTENT_DIR / f"{TODAY}*.md")
    files = sorted(glob.glob(pattern), reverse=True)

    if not files:
        # 今日の記事がなければ直近の記事を探す
        pattern = str(CONTENT_DIR / "*.md")
        files = sorted(glob.glob(pattern), reverse=True)

    if not files:
        logger.warning("記事ファイルが見つかりません")
        return {}

    filepath = files[0]
    logger.info(f"最新記事: {filepath}")

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # front matterからタイトルを抽出
    title_match = re.search(r'title:\s*["\']?(.+?)["\']?\s*$', content, re.MULTILINE)
    title = title_match.group(1).strip('"').strip("'") if title_match else "最新記事"

    # front matterを除去して本文を取得
    parts = content.split("---", 2)
    body = parts[2] if len(parts) >= 3 else content

    # 本文を要約用に整形（最初の1000文字）
    summary = body.strip()[:1000]

    # 記事URLを構築
    filename = os.path.basename(filepath).replace(".md", "")
    article_url = f"{SITE_BASE_URL}posts/{filename}/"

    return {
        "title": title,
        "summary": summary,
        "url": article_url,
        "filepath": filepath
    }


def parse_thread(raw_text: str) -> list:
    """
    生成されたテキストを5つのツイートに分割する。

    Args:
        raw_text: AIが生成した生テキスト

    Returns:
        5つのツイートテキストのリスト
    """
    # 「---」区切りで分割を試みる
    tweets = [t.strip() for t in raw_text.split("---") if t.strip()]

    # 番号付きパターンでも分割を試みる
    if len(tweets) < 5:
        tweets = re.split(r'\n\s*(?:\d+[\.）\)]\s*|ツイート\s*\d+[:：]\s*)', raw_text)
        tweets = [t.strip() for t in tweets if t.strip()]

    # 5ツイートに調整
    if len(tweets) > 5:
        tweets = tweets[:5]
    elif len(tweets) < 5:
        # 足りない場合は最後のツイートを分割するか、空で埋める
        while len(tweets) < 5:
            tweets.append("")

    # 各ツイートの文字数チェック（140文字以内）
    for i, tweet in enumerate(tweets):
        if len(tweet) > 140:
            tweets[i] = tweet[:137] + "..."
            logger.warning(f"ツイート{i+1}が140文字を超過。切り詰めました。")

    return tweets


def extract_gemini_text(response_json: dict) -> str:
    """Geminiレスポンスからテキストを抽出する。"""
    candidates = response_json.get("candidates", [])
    if not candidates:
        return ""
    parts = candidates[0].get("content", {}).get("parts", [])
    text_parts = [p.get("text", "") for p in parts if p.get("text")]
    return "\n".join(text_parts).strip()


def generate_thread(article: dict) -> list:
    """
    Gemini APIを使ってX用5連スレッドを生成する。

    Args:
        article: 記事情報

    Returns:
        5つのツイートテキストのリスト
    """
    user_prompt = f"""以下の記事要約を基に、X（Twitter）用の5連スレッドを作成してください。

## 記事タイトル
{article['title']}

## 記事要約
{article['summary']}

## 5ツイート目に入れるリンク
{article['url']}

各ツイートは「---」で区切って出力してください。
1〜4ツイート目にはリンクを入れないでください。
5ツイート目にのみリンクとCTAを入れてください。"""

    if not reserve_gemini_request():
        logger.error("Gemini APIの無料枠上限に到達しました（1分15回または1日1,500回）")
        return []

    endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
    payload = {
        "systemInstruction": {
            "parts": [{"text": THREAD_SYSTEM_PROMPT}]
        },
        "contents": [
            {
                "role": "user",
                "parts": [{"text": user_prompt}]
            }
        ],
        "generationConfig": {
            "temperature": GEMINI_TEMPERATURE_THREAD,
            "maxOutputTokens": GEMINI_MAX_OUTPUT_TOKENS_THREAD,
        }
    }
    headers = {
        "x-goog-api-key": GEMINI_API_KEY,
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(endpoint, headers=headers, json=payload, timeout=90)
        response.raise_for_status()
        response_json = response.json()

        usage = response_json.get("usageMetadata", {})
        prompt_tokens = usage.get("promptTokenCount", 0)
        completion_tokens = usage.get("candidatesTokenCount", 0)
        add_cost(0, "gemini_thread")
        logger.info(
            f"スレッド生成完了: {prompt_tokens} input + {completion_tokens} output tokens (free tier)"
        )

        raw_text = extract_gemini_text(response_json)
        return parse_thread(raw_text)

    except requests.RequestException as e:
        logger.error(f"Gemini API エラー: {e}")
        return []


def save_thread(tweets: list, article: dict) -> str:
    """
    生成されたスレッドをJSONファイルに保存する。

    Args:
        tweets: ツイートテキストのリスト
        article: 記事情報

    Returns:
        保存されたファイルパス
    """
    thread_data = {
        "date": TODAY,
        "article_title": article.get("title", ""),
        "article_url": article.get("url", ""),
        "tweets": tweets,
        "tweet_count": len(tweets),
        "posted": False
    }

    output_file = THREADS_DIR / f"{TODAY}.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(thread_data, f, ensure_ascii=False, indent=2)

    logger.info(f"スレッドを保存: {output_file}")
    return str(output_file)


def fail_on_forbidden_terms(text: str, context: str):
    """禁止IP参照を検出した場合、ログを残して停止する。"""
    matches = detect_forbidden_ip_terms(text)
    if not matches:
        return

    logger.error(f"禁止IP参照を検出: {matches}")
    log_json("generate.json", {
        "phase": "C",
        "action": "generate_x_thread",
        "status": "error",
        "details": {
            "error": "Forbidden IP terms detected",
            "context": context,
            "matched_patterns": matches,
        }
    })
    sys.exit(1)


def main():
    """メイン処理: 最新記事からXスレッドを生成する"""
    logger.info("=" * 60)
    logger.info(f"Xスレッド生成開始: {TODAY}")
    logger.info("=" * 60)

    # コスト上限チェック
    if check_cost_limit():
        logger.warning("月間コスト上限に到達。スレッド生成をスキップします。")
        sys.exit(0)

    # 最新記事を取得
    article = find_latest_article()
    if not article:
        logger.warning("記事が見つかりません。スレッド生成をスキップします。")
        sys.exit(0)

    logger.info(f"対象記事: {article['title']}")

    # Gemini APIキー確認
    validate_gemini_key()

    # スレッド生成
    tweets = generate_thread(article)

    if not tweets or all(not t for t in tweets):
        logger.error("スレッドの生成に失敗しました")
        log_json("generate.json", {
            "phase": "C",
            "action": "generate_x_thread",
            "status": "error",
            "details": {"error": "Empty thread generated"}
        })
        sys.exit(1)

    fail_on_forbidden_terms("\n".join(tweets), "thread_tweets")

    # 保存
    filepath = save_thread(tweets, article)

    # ログ記録
    log_json("generate.json", {
        "phase": "C",
        "action": "generate_x_thread",
        "status": "success",
        "details": {
            "article_title": article["title"],
            "tweet_count": len(tweets),
            "tweet_lengths": [len(t) for t in tweets]
        }
    })

    logger.info("Xスレッド生成完了")

    # 各ツイートの内容をログに出力
    for i, tweet in enumerate(tweets):
        logger.info(f"  ツイート{i+1} ({len(tweet)}文字): {tweet[:50]}...")


if __name__ == "__main__":
    main()
