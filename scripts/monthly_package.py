#!/usr/bin/env python3
"""
monthly_package.py - 月次コンテンツパッケージ化スクリプト

その月の記事とプロンプトを自動抽出し、note/Brain販売用の
長文Markdownとして整理する。

実行タイミング: 毎月28日 AM8:00 JST（GitHub Actions cron）
出力先: data/packages/YYYY-MM.md
"""

import sys
import os
import json
import re
import glob
from datetime import datetime
from openai import OpenAI

from config import (
    OPENAI_API_KEY, OPENAI_MODEL, TODAY, THIS_MONTH,
    CONTENT_DIR, PACKAGES_DIR, METRICS_DIR,
    check_cost_limit, add_cost,
    setup_logger, log_json, JST
)

logger = setup_logger("monthly_package", "generate.log")


def get_openai_client() -> OpenAI:
    """OpenAIクライアントを初期化して返す"""
    if not OPENAI_API_KEY:
        logger.error("OPENAI_API_KEY が設定されていません")
        sys.exit(1)
    return OpenAI(api_key=OPENAI_API_KEY)


def load_monthly_articles() -> list:
    """
    今月の全記事を読み込む。

    Returns:
        記事データのリスト（タイトル、日付、本文）
    """
    pattern = str(CONTENT_DIR / f"{THIS_MONTH}*.md")
    files = sorted(glob.glob(pattern))

    articles = []
    for filepath in files:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        # front matterからタイトルを抽出
        title_match = re.search(r'title:\s*["\']?(.+?)["\']?\s*$', content, re.MULTILINE)
        title = title_match.group(1).strip('"').strip("'") if title_match else os.path.basename(filepath)

        # カテゴリを抽出
        cat_match = re.search(r'categories:\s*\[?"?(.+?)"?\]?\s*$', content, re.MULTILINE)
        category = cat_match.group(1).strip('"').strip("'").strip("[]") if cat_match else ""

        # front matterを除去して本文を取得
        parts = content.split("---", 2)
        body = parts[2].strip() if len(parts) >= 3 else content

        articles.append({
            "title": title,
            "category": category,
            "filepath": filepath,
            "body": body,
            "body_length": len(body),
            "date": os.path.basename(filepath)[:10]
        })

    logger.info(f"今月の記事: {len(articles)}本")
    return articles


def extract_prompts(articles: list) -> list:
    """
    記事からプロンプト例を抽出する。

    コードブロックやプロンプト関連のセクションからテキストを抽出する。

    Returns:
        プロンプトのリスト
    """
    prompts = []
    prompt_pattern = re.compile(
        r'(?:プロンプト|prompt)[^`]*```[^`]*\n(.*?)```',
        re.IGNORECASE | re.DOTALL
    )

    for article in articles:
        matches = prompt_pattern.findall(article["body"])
        for match in matches:
            prompts.append({
                "prompt": match.strip(),
                "source_article": article["title"],
                "category": article["category"]
            })

    # プロンプトが見つからなかった場合、英語のコードブロックを探す
    if not prompts:
        code_pattern = re.compile(r'```\s*\n(.*?)```', re.DOTALL)
        for article in articles:
            matches = code_pattern.findall(article["body"])
            for match in matches:
                text = match.strip()
                # 英語のプロンプトらしきものを抽出
                if any(kw in text.lower() for kw in ["cinematic", "video", "camera", "scene", "4k"]):
                    prompts.append({
                        "prompt": text,
                        "source_article": article["title"],
                        "category": article["category"]
                    })

    logger.info(f"抽出されたプロンプト: {len(prompts)}個")
    return prompts


def generate_package(client: OpenAI, articles: list, prompts: list) -> str:
    """
    OpenAI APIを使って月次パッケージ原稿を生成する。

    Args:
        client: OpenAIクライアント
        articles: 記事データのリスト
        prompts: プロンプトのリスト

    Returns:
        パッケージ原稿のMarkdownテキスト
    """
    # 記事サマリーを作成
    article_summaries = json.dumps(
        [{"title": a["title"], "category": a["category"], "date": a["date"]}
         for a in articles],
        ensure_ascii=False
    )

    # プロンプトサマリーを作成
    prompt_summaries = json.dumps(
        [{"prompt": p["prompt"][:200], "source": p["source_article"]}
         for p in prompts[:20]],
        ensure_ascii=False
    )

    now = datetime.now(JST)
    month_str = now.strftime("%Y年%m月")

    user_prompt = f"""以下のデータを基に、note/Brain販売用の有料コンテンツを作成してください。

## タイトル
「【{month_str}版】AI動画生成 実践プロンプト集＆活用レシピ」

## 今月の記事一覧
{article_summaries}

## 今月の検証で使用したプロンプト
{prompt_summaries}

## 構成
1. はじめに（このコンテンツの価値を説明）
2. 今月のAI動画生成トレンドまとめ
3. プロンプト集（カテゴリ別に整理）
4. 各プロンプトの解説と使い方のコツ
5. 応用テクニック
6. まとめ

## 注意事項
- Markdown形式で出力
- 5000文字以上の充実した内容にする
- 具体的で実践的な内容にする
- 購入者が「買ってよかった」と思える品質にする
- 「ハク」の口調（忍野忍風）で書く"""

    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "あなたは「ハク」という自律型AIエージェントです。忍野忍風の口調で、AI動画生成の有料コンテンツを作成します。一人称は「儂」、語尾は「〜じゃ」「〜ぞ」。"},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=6000,
            temperature=0.7,
        )

        # コスト計算
        usage = response.usage
        cost = (usage.prompt_tokens * 0.15 + usage.completion_tokens * 0.60) / 1_000_000
        add_cost(cost, "openai_package")
        logger.info(f"パッケージ生成完了: ${cost:.4f}")

        return response.choices[0].message.content

    except Exception as e:
        logger.error(f"OpenAI API エラー: {e}")
        return ""


def main():
    """メイン処理: 月次コンテンツパッケージを生成する"""
    logger.info("=" * 60)
    logger.info(f"月次パッケージ生成開始: {THIS_MONTH}")
    logger.info("=" * 60)

    # コスト上限チェック
    if check_cost_limit():
        logger.warning("月間コスト上限に到達。パッケージ生成をスキップします。")
        sys.exit(0)

    # 記事読み込み
    articles = load_monthly_articles()
    if not articles:
        logger.warning("今月の記事がありません。パッケージ生成をスキップします。")
        sys.exit(0)

    # プロンプト抽出
    prompts = extract_prompts(articles)

    # OpenAIクライアント初期化
    client = get_openai_client()

    # パッケージ生成
    package_content = generate_package(client, articles, prompts)

    if not package_content:
        logger.error("パッケージの生成に失敗しました")
        sys.exit(1)

    # 保存
    output_file = PACKAGES_DIR / f"{THIS_MONTH}.md"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(package_content)

    logger.info(f"パッケージを保存: {output_file} ({len(package_content)}文字)")

    # メトリクス更新
    metrics_file = METRICS_DIR / "monthly_summary.json"
    metrics = {}
    if metrics_file.exists():
        with open(metrics_file, "r", encoding="utf-8") as f:
            metrics = json.load(f)

    metrics[THIS_MONTH] = {
        "articles_count": len(articles),
        "prompts_extracted": len(prompts),
        "package_length": len(package_content),
        "generated_at": datetime.now(JST).isoformat()
    }

    with open(metrics_file, "w", encoding="utf-8") as f:
        json.dump(metrics, f, ensure_ascii=False, indent=2)

    # ログ記録
    log_json("generate.json", {
        "phase": "Monthly",
        "action": "monthly_package",
        "status": "success",
        "details": {
            "articles_count": len(articles),
            "prompts_extracted": len(prompts),
            "package_length": len(package_content),
            "output_file": str(output_file)
        }
    })

    logger.info("月次パッケージ生成完了")


if __name__ == "__main__":
    main()
