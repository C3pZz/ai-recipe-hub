#!/usr/bin/env python3
"""
post_to_x.py - X（Twitter）への自動スレッド投稿スクリプト

tweepyを使用してX API v2でスレッド投稿を行う。
投稿前にランダムな揺らぎ（0〜30分のスリープ）を入れ、
各ツイート間に5〜15秒のランダム間隔を設ける。

実行タイミング: 毎日 AM11:45 JST頃（GitHub Actions cron）
入力: data/threads/YYYY-MM-DD.json
"""

import sys
import os
import json
import time
import random
import tweepy

from config import (
    X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_SECRET,
    TODAY, THREADS_DIR,
    X_JITTER_MAX, X_TWEET_INTERVAL_MIN, X_TWEET_INTERVAL_MAX, X_MAX_RETRIES,
    X_CONTENT_CREATE_COST_USD, DAILY_X_CONTENT_CREATE_LIMIT, MONTHLY_X_CONTENT_CREATE_LIMIT,
    check_cost_limit, reserve_usage, get_usage, add_cost,
    setup_logger, log_json
)

logger = setup_logger("post_to_x", "post.log")


def get_x_client() -> tweepy.Client:
    """
    tweepy Clientを初期化して返す。

    環境変数からAPIキーを読み込む。
    """
    if not all([X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_SECRET]):
        logger.error("X APIキーが設定されていません。以下の環境変数を確認してください:")
        logger.error("  X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_SECRET")
        sys.exit(1)

    client = tweepy.Client(
        consumer_key=X_API_KEY,
        consumer_secret=X_API_SECRET,
        access_token=X_ACCESS_TOKEN,
        access_token_secret=X_ACCESS_SECRET,
    )
    return client


def load_thread() -> dict:
    """
    本日のスレッドデータを読み込む。

    Returns:
        スレッドデータの辞書
    """
    thread_file = THREADS_DIR / f"{TODAY}.json"
    if not thread_file.exists():
        logger.error(f"スレッドファイルが見つかりません: {thread_file}")
        return {}

    with open(thread_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 既に投稿済みかチェック
    if data.get("posted", False):
        logger.info("本日のスレッドは既に投稿済みです。スキップします。")
        return {}

    return data


def post_thread(client: tweepy.Client, tweets: list) -> list:
    """
    X API v2でスレッドを投稿する。

    Args:
        client: tweepy Client
        tweets: ツイートテキストのリスト

    Returns:
        投稿されたツイートIDのリスト
    """
    posted_ids = []
    previous_tweet_id = None

    for i, tweet_text in enumerate(tweets):
        if not tweet_text:
            logger.warning(f"ツイート{i+1}が空です。スキップします。")
            continue

        # 都度課金制に対応: API呼び出し前に上限内であることを予約
        reserved = reserve_usage(
            "x_content_create",
            units=1,
            daily_limit=DAILY_X_CONTENT_CREATE_LIMIT,
            monthly_limit=MONTHLY_X_CONTENT_CREATE_LIMIT,
        )
        if not reserved:
            logger.error(
                "X API作成上限に到達。これ以上投稿しません。"
                f" (daily={DAILY_X_CONTENT_CREATE_LIMIT}, monthly={MONTHLY_X_CONTENT_CREATE_LIMIT})"
            )
            return posted_ids

        success = False
        for retry in range(X_MAX_RETRIES):
            try:
                response = client.create_tweet(
                    text=tweet_text,
                    in_reply_to_tweet_id=previous_tweet_id,
                )
                tweet_id = response.data["id"]
                previous_tweet_id = tweet_id
                posted_ids.append(tweet_id)
                logger.info(f"ツイート {i+1}/5 投稿成功: ID={tweet_id}")
                add_cost(X_CONTENT_CREATE_COST_USD, "x_content_create")
                success = True
                break

            except tweepy.TooManyRequests:
                logger.error("レート制限に到達。本日の投稿を中止します。")
                return posted_ids

            except tweepy.TweepyException as e:
                logger.error(f"ツイート {i+1} 投稿失敗 (リトライ {retry+1}/{X_MAX_RETRIES}): {e}")
                if retry < X_MAX_RETRIES - 1:
                    # 指数バックオフ
                    wait = (2 ** retry) * 30
                    logger.info(f"{wait}秒待機してリトライします...")
                    time.sleep(wait)

        if not success:
            logger.error(f"ツイート {i+1} は{X_MAX_RETRIES}回リトライしても投稿できませんでした。")
            break

        # 次のツイートまでランダム間隔
        if i < len(tweets) - 1:
            interval = random.uniform(X_TWEET_INTERVAL_MIN, X_TWEET_INTERVAL_MAX)
            logger.info(f"次のツイートまで {interval:.1f}秒 待機...")
            time.sleep(interval)

    return posted_ids


def mark_as_posted(posted_ids: list):
    """スレッドデータに投稿済みフラグを立てる"""
    thread_file = THREADS_DIR / f"{TODAY}.json"
    if thread_file.exists():
        with open(thread_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        data["posted"] = True
        data["posted_ids"] = posted_ids
        data["posted_at"] = time.strftime("%Y-%m-%dT%H:%M:%S+09:00")
        with open(thread_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


def main():
    """メイン処理: スレッドをXに投稿する"""
    logger.info("=" * 60)
    logger.info(f"X投稿処理開始: {TODAY}")
    logger.info("=" * 60)

    # コスト上限チェック（全体予算）
    if check_cost_limit():
        logger.warning("月間コスト上限に到達。X投稿をスキップします。")
        sys.exit(0)

    # スレッドデータ読み込み
    thread_data = load_thread()
    if not thread_data:
        logger.info("投稿するスレッドがありません。終了します。")
        sys.exit(0)

    tweets = thread_data.get("tweets", [])
    if not tweets:
        logger.warning("ツイートデータが空です。終了します。")
        sys.exit(0)

    logger.info(f"投稿するスレッド: {len(tweets)}ツイート")
    logger.info(f"記事: {thread_data.get('article_title', 'N/A')}")

    # ランダムな揺らぎ（0〜30分）
    jitter = random.uniform(0, X_JITTER_MAX)
    logger.info(f"投稿前の揺らぎ: {jitter:.0f}秒 ({jitter/60:.1f}分) 待機します...")
    time.sleep(jitter)

    # X クライアント初期化
    client = get_x_client()

    # スレッド投稿
    logger.info("スレッド投稿を開始します...")
    posted_ids = post_thread(client, tweets)

    # 投稿済みフラグを立てる
    if posted_ids:
        mark_as_posted(posted_ids)

    # ログ記録
    log_json("post.json", {
        "phase": "C",
        "action": "post_to_x",
        "status": "success" if posted_ids else "error",
        "details": {
            "article_title": thread_data.get("article_title", ""),
            "tweets_attempted": len(tweets),
            "tweets_posted": len(posted_ids),
            "posted_ids": posted_ids,
            "jitter_seconds": round(jitter),
            "x_content_create_daily_used": get_usage("x_content_create", "daily"),
            "x_content_create_monthly_used": get_usage("x_content_create", "monthly"),
            "x_content_create_daily_limit": DAILY_X_CONTENT_CREATE_LIMIT,
            "x_content_create_monthly_limit": MONTHLY_X_CONTENT_CREATE_LIMIT,
        },
        "cost_usd": round(len(posted_ids) * X_CONTENT_CREATE_COST_USD, 6)
    })

    if posted_ids:
        logger.info(f"X投稿完了: {len(posted_ids)}/{len(tweets)} ツイートを投稿しました")
    else:
        logger.error("X投稿失敗: 1つもツイートを投稿できませんでした")
        sys.exit(1)


if __name__ == "__main__":
    main()
