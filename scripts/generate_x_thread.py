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
from openai import OpenAI

from config import (
    OPENAI_API_KEY, OPENAI_MODEL, OPENAI_MAX_TOKENS_THREAD,
    OPENAI_TEMPERATURE_THREAD, THREAD_SYSTEM_PROMPT,
    TODAY, CONTENT_DIR, THREADS_DIR, SITE_BASE_URL,
    check_cost_limit, add_cost,
    setup_logger, log_json
)

logger = setup_logger("generate_x_thread", "generate.log")


def get_openai_client() -> OpenAI:
    """OpenAIクライアントを初期化して返す"""
    if not OPENAI_API_KEY:
        logger.error("OPENAI_API_KEY が設定されていません")
        sys.exit(1)
    return OpenAI(api_key=OPENAI_API_KEY)


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


def generate_thread(client: OpenAI, article: dict) -> list:
    """
    OpenAI APIを使ってX用5連スレッドを生成する。

    Args:
        client: OpenAIクライアント
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

    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": THREAD_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=OPENAI_MAX_TOKENS_THREAD,
            temperature=OPENAI_TEMPERATURE_THREAD,
        )

        # コスト計算
        usage = response.usage
        cost = (usage.prompt_tokens * 0.15 + usage.completion_tokens * 0.60) / 1_000_000
        add_cost(cost, "openai_thread")
        logger.info(f"スレッド生成完了: {usage.prompt_tokens} input + {usage.completion_tokens} output tokens (${cost:.4f})")

        raw_text = response.choices[0].message.content
        return parse_thread(raw_text)

    except Exception as e:
        logger.error(f"OpenAI API エラー: {e}")
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

    # OpenAIクライアント初期化
    client = get_openai_client()

    # スレッド生成
    tweets = generate_thread(client, article)

    if not tweets or all(not t for t in tweets):
        logger.error("スレッドの生成に失敗しました")
        log_json("generate.json", {
            "phase": "C",
            "action": "generate_x_thread",
            "status": "error",
            "details": {"error": "Empty thread generated"}
        })
        sys.exit(1)

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
