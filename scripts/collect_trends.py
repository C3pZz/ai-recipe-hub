#!/usr/bin/env python3
"""
collect_trends.py - AI動画生成関連のトレンド情報を収集するスクリプト

Brave Search APIを使用して、対象ツールの最新ニュース・
アップデート情報を収集し、JSON形式で保存する。

実行タイミング: 毎日 AM6:00 JST（GitHub Actions cron）
出力先: data/trends/YYYY-MM-DD.json
"""

import sys
import json
import time
import requests
from datetime import datetime

# 同一ディレクトリのconfigをインポート
from config import (
    BRAVE_SEARCH_API_KEY, TOOL_NAMES, TODAY, TRENDS_DIR,
    BRAVE_RESULTS_PER_QUERY, BRAVE_COUNTRY, BRAVE_SEARCH_LANG, BRAVE_SAFESEARCH,
    DAILY_BRAVE_QUERY_LIMIT, MONTHLY_BRAVE_QUERY_LIMIT,
    check_cost_limit, reserve_usage, get_usage,
    setup_logger, log_json
)

logger = setup_logger("collect_trends", "collect.log")


def search_brave(query: str, num_results: int = 5) -> dict:
    """
    Brave Search APIで検索を実行する。

    Args:
        query: 検索クエリ文字列
        num_results: 取得する結果数

    Returns:
        Brave Search APIのレスポンスJSON
    """
    if not BRAVE_SEARCH_API_KEY:
        logger.error("BRAVE_SEARCH_API_KEY が設定されていません")
        return {"web": {"results": []}}

    url = "https://api.search.brave.com/res/v1/web/search"
    headers = {
        "Accept": "application/json",
        "X-Subscription-Token": BRAVE_SEARCH_API_KEY,
    }
    params = {
        "q": query,
        "country": BRAVE_COUNTRY,
        "search_lang": BRAVE_SEARCH_LANG,
        "safesearch": BRAVE_SAFESEARCH,
        "count": num_results,
    }

    try:
        response = requests.get(url, headers=headers, params=params, timeout=20)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Brave Search API検索エラー: {e}")
        return {"web": {"results": []}}


def collect_tool_trends(tool_name: str) -> tuple:
    """
    特定のツールに関する最新トレンド情報を収集する。

    Args:
        tool_name: ツール名（例: "Kling", "Runway"）

    Returns:
        検索結果のリスト
    """
    queries = [
        f"{tool_name} AI動画生成 最新 アップデート 2026",
        f"{tool_name} AI video generation new feature 2026",
    ]

    results = []
    queries_executed = 0
    limit_reached = False
    for query in queries:
        if not reserve_usage(
            "brave_search_queries",
            units=1,
            daily_limit=DAILY_BRAVE_QUERY_LIMIT,
            monthly_limit=MONTHLY_BRAVE_QUERY_LIMIT,
        ):
            logger.warning("Brave Searchクエリ上限に到達。以降の検索を停止します。")
            limit_reached = True
            break

        logger.info(f"検索中: {query}")
        response = search_brave(query, BRAVE_RESULTS_PER_QUERY)
        web_results = response.get("web", {}).get("results", [])
        queries_executed += 1

        for idx, item in enumerate(web_results):
            results.append({
                "tool": tool_name,
                "query": query,
                "title": item.get("title", ""),
                "link": item.get("url", ""),
                "snippet": item.get("description", ""),
                "date": item.get("age", ""),
                "position": item.get("position", idx + 1),
            })

        # API負荷軽減のため1秒待機
        time.sleep(1)

    return results, queries_executed, limit_reached


def collect_general_trends() -> tuple:
    """
    AI動画生成全般のトレンド情報を収集する。

    Returns:
        検索結果のリスト
    """
    queries = [
        "AI動画生成 最新ニュース 2026",
        "AI video generation trends 2026",
        "テキストから動画 AI 新サービス",
    ]

    results = []
    queries_executed = 0
    limit_reached = False
    for query in queries:
        if not reserve_usage(
            "brave_search_queries",
            units=1,
            daily_limit=DAILY_BRAVE_QUERY_LIMIT,
            monthly_limit=MONTHLY_BRAVE_QUERY_LIMIT,
        ):
            logger.warning("Brave Searchクエリ上限に到達。一般トレンド収集を停止します。")
            limit_reached = True
            break

        logger.info(f"一般トレンド検索中: {query}")
        response = search_brave(query, BRAVE_RESULTS_PER_QUERY)
        web_results = response.get("web", {}).get("results", [])
        queries_executed += 1

        for idx, item in enumerate(web_results):
            results.append({
                "tool": "general",
                "query": query,
                "title": item.get("title", ""),
                "link": item.get("url", ""),
                "snippet": item.get("description", ""),
                "date": item.get("age", ""),
                "position": item.get("position", idx + 1),
            })

        time.sleep(1)

    return results, queries_executed, limit_reached


def main():
    """メイン処理: トレンド情報を収集してJSONに保存する"""
    logger.info("=" * 60)
    logger.info(f"トレンド収集開始: {TODAY}")
    logger.info("=" * 60)

    # コスト上限チェック
    if check_cost_limit():
        logger.warning("月間コスト上限に到達。トレンド収集をスキップします。")
        sys.exit(0)

    if not BRAVE_SEARCH_API_KEY:
        logger.error("BRAVE_SEARCH_API_KEY が設定されていません。トレンド収集を中止します。")
        sys.exit(1)

    all_results = []
    query_count = 0
    limit_reached = False

    # 各ツールのトレンド収集
    for tool_name in TOOL_NAMES:
        if limit_reached:
            logger.warning("Brave Searchクエリ上限のため残りのツール収集をスキップします。")
            break

        logger.info(f"--- {tool_name} のトレンド収集 ---")
        results, executed, hit_limit = collect_tool_trends(tool_name)
        all_results.extend(results)
        query_count += executed
        limit_reached = hit_limit
        logger.info(f"{tool_name}: {len(results)}件の結果を取得")

    # 一般トレンド収集
    if not limit_reached:
        logger.info("--- 一般トレンド収集 ---")
        general_results, executed, hit_limit = collect_general_trends()
        all_results.extend(general_results)
        query_count += executed
        limit_reached = hit_limit
        logger.info(f"一般トレンド: {len(general_results)}件の結果を取得")

    # 結果を保存
    output_data = {
        "date": TODAY,
        "total_results": len(all_results),
        "total_queries": query_count,
        "results": all_results
    }

    output_file = TRENDS_DIR / f"{TODAY}.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    logger.info(f"トレンド収集完了: {len(all_results)}件 → {output_file}")

    # ログ記録
    log_json("collect.json", {
        "phase": "A",
        "action": "collect_trends",
        "status": "success",
        "details": {
            "total_results": len(all_results),
            "total_queries": query_count,
            "tools_searched": TOOL_NAMES,
            "daily_query_limit": DAILY_BRAVE_QUERY_LIMIT,
            "monthly_query_limit": MONTHLY_BRAVE_QUERY_LIMIT,
            "monthly_queries_used": get_usage("brave_search_queries", "monthly"),
        },
        "cost_usd": 0
    })

    return output_data


if __name__ == "__main__":
    main()
