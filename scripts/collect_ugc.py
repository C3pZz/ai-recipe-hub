#!/usr/bin/env python3
"""
collect_ugc.py - UGC（ユーザー生成コンテンツ）収集・分析スクリプト

Serper APIで「ツール名 + デメリット/退会/使ってみた」等のクエリで検索し、
個人ブログ・note・Zenn・Qiitaの記事URLを取得。
BeautifulSoupで本文テキストをスクレイピングして保存する。

実行タイミング: 毎日 AM6:00 JST（collect_trends.pyの後に実行）
出力先: data/ugc/YYYY-MM-DD.json
"""

import sys
import json
import time
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

from config import (
    SERPER_API_KEY, TOOL_NAMES, UGC_QUERY_PATTERNS, TODAY, UGC_DIR,
    SERPER_RESULTS_PER_QUERY, SERPER_COUNTRY, SERPER_LANGUAGE,
    DAILY_SERPER_QUERY_LIMIT, check_cost_limit, add_cost,
    setup_logger, log_json
)

logger = setup_logger("collect_ugc", "collect.log")

# UGC記事として優先するドメイン（個人の生の声が多いサイト）
PRIORITY_DOMAINS = [
    "note.com",
    "zenn.dev",
    "qiita.com",
    "hateblo.jp",
    "hatenablog.com",
    "hatenablog.jp",
    "livedoor.blog",
    "ameblo.jp",
    "medium.com",
]

# 除外するドメイン（大手メディア・企業サイト）
EXCLUDE_DOMAINS = [
    "wikipedia.org",
    "youtube.com",
    "twitter.com",
    "x.com",
    "facebook.com",
    "instagram.com",
    "amazon.co.jp",
    "amazon.com",
]

# スクレイピング時のHTTPヘッダ
SCRAPE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "ja,en;q=0.9",
}


def search_ugc(tool_name: str, query_pattern: str) -> list:
    """
    Serper APIでUGC記事を検索する。

    Args:
        tool_name: ツール名
        query_pattern: クエリパターン（{tool}がツール名に置換される）

    Returns:
        検索結果のリスト
    """
    if not SERPER_API_KEY:
        logger.error("SERPER_API_KEY が設定されていません")
        return []

    query = query_pattern.format(tool=tool_name)
    url = "https://google.serper.dev/search"
    headers = {
        "X-API-KEY": SERPER_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "q": query,
        "gl": SERPER_COUNTRY,
        "hl": SERPER_LANGUAGE,
        "num": SERPER_RESULTS_PER_QUERY
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        response.raise_for_status()
        add_cost(0.001, "serper")
        return response.json().get("organic", [])
    except requests.RequestException as e:
        logger.error(f"Serper API検索エラー ({query}): {e}")
        return []


def is_ugc_url(url: str) -> bool:
    """
    URLがUGC（個人ブログ等）かどうかを判定する。

    Args:
        url: 判定対象のURL

    Returns:
        UGCと判定された場合True
    """
    parsed = urlparse(url)
    domain = parsed.netloc.lower()

    # 除外ドメインチェック
    for exclude in EXCLUDE_DOMAINS:
        if exclude in domain:
            return False

    # 優先ドメインチェック
    for priority in PRIORITY_DOMAINS:
        if priority in domain:
            return True

    # その他の個人ブログも許可（大手メディアでなければ）
    return True


def scrape_article_text(url: str, max_length: int = 3000) -> str:
    """
    URLから記事本文テキストをスクレイピングする。

    BeautifulSoupで<article>タグや<main>タグの中身を優先的に取得し、
    ナビゲーションやフッターのノイズを除去する。

    Args:
        url: スクレイピング対象のURL
        max_length: 取得する最大文字数

    Returns:
        抽出されたテキスト
    """
    try:
        response = requests.get(url, headers=SCRAPE_HEADERS, timeout=10)
        response.raise_for_status()
        response.encoding = response.apparent_encoding

        soup = BeautifulSoup(response.text, "html.parser")

        # 不要な要素を除去
        for tag in soup.find_all(["nav", "footer", "header", "aside", "script", "style", "noscript"]):
            tag.decompose()

        # 本文を優先的に取得（article > main > body の順）
        content = None
        for selector in ["article", "main", ".entry-content", ".post-content",
                         ".note-common-styles__textnote-body", "#main-content", ".content"]:
            content = soup.select_one(selector)
            if content:
                break

        if not content:
            content = soup.body if soup.body else soup

        # テキスト抽出
        text = content.get_text(separator="\n", strip=True)

        # 空行を整理
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        text = "\n".join(lines)

        # 最大文字数で切り詰め
        if len(text) > max_length:
            text = text[:max_length] + "..."

        return text

    except requests.RequestException as e:
        logger.warning(f"スクレイピングエラー ({url}): {e}")
        return ""
    except Exception as e:
        logger.warning(f"パースエラー ({url}): {e}")
        return ""


def collect_tool_ugc(tool_name: str) -> list:
    """
    特定のツールに関するUGC記事を収集する。

    Args:
        tool_name: ツール名

    Returns:
        UGCデータのリスト
    """
    ugc_data = []

    for pattern in UGC_QUERY_PATTERNS:
        query = pattern.format(tool=tool_name)
        logger.info(f"UGC検索中: {query}")
        results = search_ugc(tool_name, pattern)

        for item in results:
            url = item.get("link", "")
            if not is_ugc_url(url):
                continue

            # 本文をスクレイピング
            logger.info(f"  スクレイピング: {url}")
            text = scrape_article_text(url)

            if text and len(text) > 100:  # 100文字以上の記事のみ保存
                ugc_data.append({
                    "tool": tool_name,
                    "query": query,
                    "title": item.get("title", ""),
                    "url": url,
                    "snippet": item.get("snippet", ""),
                    "domain": urlparse(url).netloc,
                    "text_length": len(text),
                    "text_preview": text[:500],
                    "full_text": text,
                })

            # サーバー負荷軽減のため待機
            time.sleep(2)

        time.sleep(1)

    return ugc_data


def main():
    """メイン処理: UGC記事を収集してJSONに保存する"""
    logger.info("=" * 60)
    logger.info(f"UGC収集開始: {TODAY}")
    logger.info("=" * 60)

    # コスト上限チェック
    if check_cost_limit():
        logger.warning("月間コスト上限に到達。UGC収集をスキップします。")
        sys.exit(0)

    all_ugc = []
    query_count = 0

    for tool_name in TOOL_NAMES:
        if query_count >= DAILY_SERPER_QUERY_LIMIT:
            logger.warning(f"日次クエリ上限に到達。残りのツールをスキップします。")
            break

        logger.info(f"--- {tool_name} のUGC収集 ---")
        ugc_data = collect_tool_ugc(tool_name)
        all_ugc.extend(ugc_data)
        query_count += len(UGC_QUERY_PATTERNS)
        logger.info(f"{tool_name}: {len(ugc_data)}件のUGC記事を取得")

    # 結果を保存
    output_data = {
        "date": TODAY,
        "total_articles": len(all_ugc),
        "total_queries": query_count,
        "articles": all_ugc
    }

    output_file = UGC_DIR / f"{TODAY}.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    logger.info(f"UGC収集完了: {len(all_ugc)}件 → {output_file}")

    # ログ記録
    log_json("collect.json", {
        "phase": "A",
        "action": "collect_ugc",
        "status": "success",
        "details": {
            "total_articles": len(all_ugc),
            "total_queries": query_count,
            "domains": list(set(a["domain"] for a in all_ugc))
        },
        "cost_usd": query_count * 0.001
    })

    return output_data


if __name__ == "__main__":
    main()
