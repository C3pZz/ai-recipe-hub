#!/usr/bin/env python3
"""
collect_trends.py - AI動画生成関連のトレンド情報を収集するスクリプト

Serper API（Google検索API）を使用して、対象ツールの最新ニュース・
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
    SERPER_API_KEY, TOOL_NAMES, TODAY, TRENDS_DIR,
    SERPER_RESULTS_PER_QUERY, SERPER_COUNTRY, SERPER_LANGUAGE,
    DAILY_SERPER_QUERY_LIMIT, check_cost_limit, add_cost,
    setup_logger, log_json
)

logger = setup_logger("collect_trends", "collect.log")


def search_serper(query: str, num_results: int = 5) -> dict:
    """
    Serper APIで検索を実行する。

    Args:
        query: 検索クエリ文字列
        num_results: 取得する結果数

    Returns:
        Serper APIのレスポンスJSON
    """
    if not SERPER_API_KEY:
        logger.error("SERPER_API_KEY が設定されていません")
        return {"organic": []}

    url = "https://google.serper.dev/search"
    headers = {
        "X-API-KEY": SERPER_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "q": query,
        "gl": SERPER_COUNTRY,
        "hl": SERPER_LANGUAGE,
        "num": num_results
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        response.raise_for_status()
        # Serper APIは1クエリあたり約$0.001（無料枠内なら$0）
        add_cost(0.001, "serper")
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Serper API検索エラー: {e}")
        return {"organic": []}


def collect_tool_trends(tool_name: str) -> list:
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
    for query in queries:
        logger.info(f"検索中: {query}")
        response = search_serper(query, SERPER_RESULTS_PER_QUERY)
        organic = response.get("organic", [])

        for item in organic:
            results.append({
                "tool": tool_name,
                "query": query,
                "title": item.get("title", ""),
                "link": item.get("link", ""),
                "snippet": item.get("snippet", ""),
                "date": item.get("date", ""),
                "position": item.get("position", 0),
            })

        # API負荷軽減のため1秒待機
        time.sleep(1)

    return results


def collect_general_trends() -> list:
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
    for query in queries:
        logger.info(f"一般トレンド検索中: {query}")
        response = search_serper(query, SERPER_RESULTS_PER_QUERY)
        organic = response.get("organic", [])

        for item in organic:
            results.append({
                "tool": "general",
                "query": query,
                "title": item.get("title", ""),
                "link": item.get("link", ""),
                "snippet": item.get("snippet", ""),
                "date": item.get("date", ""),
                "position": item.get("position", 0),
            })

        time.sleep(1)

    return results


def main():
    """メイン処理: トレンド情報を収集してJSONに保存する"""
    logger.info("=" * 60)
    logger.info(f"トレンド収集開始: {TODAY}")
    logger.info("=" * 60)

    # コスト上限チェック
    if check_cost_limit():
        logger.warning("月間コスト上限に到達。トレンド収集をスキップします。")
        sys.exit(0)

    all_results = []
    query_count = 0

    # 各ツールのトレンド収集
    for tool_name in TOOL_NAMES:
        if query_count >= DAILY_SERPER_QUERY_LIMIT:
            logger.warning(f"日次クエリ上限 ({DAILY_SERPER_QUERY_LIMIT}) に到達。残りのツールをスキップします。")
            break

        logger.info(f"--- {tool_name} のトレンド収集 ---")
        results = collect_tool_trends(tool_name)
        all_results.extend(results)
        query_count += 2  # ツールあたり2クエリ
        logger.info(f"{tool_name}: {len(results)}件の結果を取得")

    # 一般トレンド収集
    if query_count < DAILY_SERPER_QUERY_LIMIT:
        logger.info("--- 一般トレンド収集 ---")
        general_results = collect_general_trends()
        all_results.extend(general_results)
        query_count += 3
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
            "tools_searched": TOOL_NAMES[:len(all_results)]
        },
        "cost_usd": query_count * 0.001
    })

    return output_data


if __name__ == "__main__":
    main()
