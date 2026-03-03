#!/usr/bin/env python3
"""
generate_article.py - Hugo用Markdown記事を自動生成するスクリプト

収集したトレンド情報とUGCデータを元に、OpenAI API (gpt-4o-mini) を使って
Hugo用のMarkdown記事を生成する。記事は「ハク」の口調（忍野忍風）で書かれる。

実行タイミング: 毎日 AM7:00 JST（情報収集の後に実行）
出力先: content/posts/YYYY-MM-DD-{slug}.md
"""

import sys
import os
import json
import re
import unicodedata
from datetime import datetime
from openai import OpenAI

from config import (
    OPENAI_API_KEY, OPENAI_MODEL, OPENAI_MAX_TOKENS_ARTICLE,
    OPENAI_TEMPERATURE_ARTICLE, ARTICLE_SYSTEM_PROMPT,
    TODAY, CONTENT_DIR, TRENDS_DIR, UGC_DIR, TOOL_NAMES,
    MAX_ARTICLES_PER_DAY, check_cost_limit, add_cost,
    setup_logger, log_json, JST
)

logger = setup_logger("generate_article", "generate.log")


def get_openai_client() -> OpenAI:
    """OpenAIクライアントを初期化して返す"""
    if not OPENAI_API_KEY:
        logger.error("OPENAI_API_KEY が設定されていません")
        sys.exit(1)
    return OpenAI(api_key=OPENAI_API_KEY)


def load_today_trends() -> dict:
    """本日のトレンドデータを読み込む"""
    trends_file = TRENDS_DIR / f"{TODAY}.json"
    if trends_file.exists():
        with open(trends_file, "r", encoding="utf-8") as f:
            return json.load(f)
    logger.warning(f"トレンドデータが見つかりません: {trends_file}")
    return {"results": []}


def load_today_ugc() -> dict:
    """本日のUGCデータを読み込む"""
    ugc_file = UGC_DIR / f"{TODAY}.json"
    if ugc_file.exists():
        with open(ugc_file, "r", encoding="utf-8") as f:
            return json.load(f)
    logger.warning(f"UGCデータが見つかりません: {ugc_file}")
    return {"articles": []}


def select_article_topic(trends: dict, ugc: dict) -> dict:
    """
    トレンドとUGCデータから、記事のトピックを選定する。

    最もデータが豊富なツールを優先的に選ぶ。

    Returns:
        トピック情報の辞書
    """
    # ツールごとのデータ量をカウント
    tool_scores = {}
    for tool in TOOL_NAMES:
        trend_count = len([r for r in trends.get("results", []) if r.get("tool") == tool])
        ugc_count = len([a for a in ugc.get("articles", []) if a.get("tool") == tool])
        tool_scores[tool] = trend_count + ugc_count * 2  # UGCを重み付け

    # スコアが最も高いツールを選択
    if tool_scores:
        best_tool = max(tool_scores, key=tool_scores.get)
    else:
        best_tool = TOOL_NAMES[0] if TOOL_NAMES else "AI動画生成"

    # 該当ツールのデータを抽出
    tool_trends = [r for r in trends.get("results", []) if r.get("tool") == best_tool]
    tool_ugc = [a for a in ugc.get("articles", []) if a.get("tool") == best_tool]

    return {
        "tool": best_tool,
        "trends": tool_trends[:5],  # 上位5件
        "ugc": tool_ugc[:3],  # 上位3件
        "score": tool_scores.get(best_tool, 0)
    }


def slugify(text: str) -> str:
    """日本語テキストをURL用のスラッグに変換する"""
    # ASCII文字以外を除去してスラッグ化
    text = text.lower().strip()
    text = re.sub(r'[【】「」『』（）\(\)\[\]]+', '', text)
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    text = re.sub(r'-+', '-', text)
    text = text.strip('-')
    # 日本語が残っている場合はハッシュで短縮
    if any(ord(c) > 127 for c in text):
        import hashlib
        text = hashlib.md5(text.encode()).hexdigest()[:12]
    return text or "article"


def generate_article_content(client: OpenAI, topic: dict) -> str:
    """
    OpenAI APIを使って記事を生成する。

    Args:
        client: OpenAIクライアント
        topic: トピック情報

    Returns:
        生成されたMarkdown記事（front matter付き）
    """
    tool_name = topic["tool"]
    trends_summary = json.dumps(
        [{"title": t["title"], "snippet": t["snippet"]} for t in topic["trends"]],
        ensure_ascii=False
    )
    ugc_summary = json.dumps(
        [{"title": u["title"], "text_preview": u.get("text_preview", "")} for u in topic["ugc"]],
        ensure_ascii=False
    )

    user_prompt = f"""以下のデータを基に、{tool_name}に関する実践的なブログ記事を生成してください。

## 最新トレンド情報
{trends_summary}

## 日本人ユーザーの声（UGC）
{ugc_summary}

## 記事の要件
- Hugo用のMarkdown形式で出力すること
- 最初にYAML front matterを含めること（---で囲む）
- front matterには以下を含める:
  - title: 記事タイトル（SEOを意識、30〜60文字）
  - description: 記事の説明（120文字以内）
  - date: {TODAY}
  - categories: 適切なカテゴリ1つ（tool-comparison, prompt-recipe, monetize, beginner-guide, ugc-analysis, technique のいずれか）
  - tags: 関連タグ3〜5個
  - author: ハク
  - emoji: 記事を象徴する絵文字1つ
- 記事本文は2000〜3000文字程度
- 見出し（h2, h3）を適切に使う
- 具体的な数値やプロンプト例を含める
- 最後に「まとめ」セクションを入れる

記事全体を「ハク」の口調で書いてください。"""

    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": ARTICLE_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=OPENAI_MAX_TOKENS_ARTICLE,
            temperature=OPENAI_TEMPERATURE_ARTICLE,
        )

        # コスト計算（gpt-4o-mini: input $0.15/1M, output $0.60/1M）
        usage = response.usage
        cost = (usage.prompt_tokens * 0.15 + usage.completion_tokens * 0.60) / 1_000_000
        add_cost(cost, "openai_article")
        logger.info(f"記事生成完了: {usage.prompt_tokens} input + {usage.completion_tokens} output tokens (${cost:.4f})")

        return response.choices[0].message.content

    except Exception as e:
        logger.error(f"OpenAI API エラー: {e}")
        return ""


def save_article(content: str) -> str:
    """
    生成された記事をファイルに保存する。

    Args:
        content: Markdown記事の内容

    Returns:
        保存されたファイルパス
    """
    if not content:
        logger.error("記事の内容が空です")
        return ""

    # front matterからタイトルを抽出してスラッグ化
    title_match = re.search(r'title:\s*["\']?(.+?)["\']?\s*$', content, re.MULTILINE)
    if title_match:
        title = title_match.group(1).strip('"').strip("'")
        slug = slugify(title)
    else:
        slug = "article"

    filename = f"{TODAY}-{slug}.md"
    filepath = CONTENT_DIR / filename

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    logger.info(f"記事を保存: {filepath}")
    return str(filepath)


def main():
    """メイン処理: トレンド・UGCデータを元に記事を生成する"""
    logger.info("=" * 60)
    logger.info(f"記事生成開始: {TODAY}")
    logger.info("=" * 60)

    # コスト上限チェック
    if check_cost_limit():
        logger.warning("月間コスト上限に到達。記事生成をスキップします。")
        sys.exit(0)

    # データ読み込み
    trends = load_today_trends()
    ugc = load_today_ugc()

    if not trends.get("results") and not ugc.get("articles"):
        logger.warning("トレンド・UGCデータが空です。記事生成をスキップします。")
        sys.exit(0)

    # OpenAIクライアント初期化
    client = get_openai_client()

    # トピック選定
    topic = select_article_topic(trends, ugc)
    logger.info(f"選定トピック: {topic['tool']} (スコア: {topic['score']})")

    # 記事生成（1日の上限まで）
    articles_generated = 0
    for i in range(min(MAX_ARTICLES_PER_DAY, 1)):  # 通常は1日1記事
        logger.info(f"記事 {i+1} を生成中...")
        content = generate_article_content(client, topic)

        if content:
            filepath = save_article(content)
            if filepath:
                articles_generated += 1
                logger.info(f"記事 {i+1} 生成完了: {filepath}")

    # ログ記録
    log_json("generate.json", {
        "phase": "B",
        "action": "generate_article",
        "status": "success" if articles_generated > 0 else "skipped",
        "details": {
            "articles_generated": articles_generated,
            "topic_tool": topic["tool"],
            "topic_score": topic["score"]
        }
    })

    logger.info(f"記事生成完了: {articles_generated}本")


if __name__ == "__main__":
    main()
