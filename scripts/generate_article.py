#!/usr/bin/env python3
"""
AI Recipe Hub - 記事自動生成スクリプト
OpenAI API (gpt-4o-mini) を使用してAIツールのレビュー記事を生成します。

使用方法:
  python3 scripts/generate_article.py --tool-name "ChatGPT" --category "文章生成AI"
  python3 scripts/generate_article.py  # ツール名省略時は自動選択

環境変数:
  OPENAI_API_KEY: OpenAI APIキー (必須)
  OPENAI_MODEL: 使用するモデル (デフォルト: gpt-4o-mini)
"""

import os
import sys
import json
import argparse
import re
from datetime import datetime
from pathlib import Path

try:
    from openai import OpenAI
except ImportError:
    print("ERROR: openai パッケージがインストールされていません。")
    print("  pip install openai")
    sys.exit(1)

# ============================================================
# 設定
# ============================================================
CONTENT_DIR = Path(__file__).parent.parent / "content" / "posts"
LOGS_DIR = Path(__file__).parent.parent / "logs"
TOOLS_DATA_FILE = Path(__file__).parent.parent / "data" / "tools_queue.json"

CATEGORIES = [
    "文章生成AI",
    "画像生成AI",
    "コーディングAI",
    "業務効率化AI",
    "マーケティングAI",
]

# 記事生成プロンプトテンプレート
ARTICLE_PROMPT_TEMPLATE = """
あなたは「AI Recipe Hub」というAIツール専門メディアの編集者です。
以下の情報をもとに、SEOに最適化された高品質な日本語レビュー記事を作成してください。

## 対象ツール
- ツール名: {tool_name}
- カテゴリ: {category}
- 追加情報: {additional_info}

## 記事の要件
1. 文字数: 1500〜2500文字
2. 読者: AIツールの導入を検討しているビジネスパーソン・中小企業
3. 目的: ツールの理解を深め、アフィリエイトリンクへの誘導
4. トーン: 専門的だが分かりやすい。具体的な数値や事例を含める

## 必須セクション
1. ツール概要 (h2)
2. 主な機能と使い方 (h2) - 具体的な手順を含む
3. 料金プラン (h2) - 表形式で比較
4. ユースケース (h2) - 具体的な業務シーン
5. プロンプト例 (h2) - コードブロックで実際のプロンプトを提示
6. まとめ (h2)

## 出力形式
以下のYAMLフロントマターを含むMarkdown形式で出力してください。
他のテキストは含めず、Markdownのみを出力してください。

---
title: "[記事タイトル]"
date: {date}
description: "[SEO最適化されたメタディスクリプション（120文字以内）]"
categories: ["{category}"]
tags: ["[タグ1]", "[タグ2]", "[タグ3]"]
emoji: "[ツールに合った絵文字1文字]"
toolName: "{tool_name}"
toolTagline: "[キャッチーなツールの説明（30文字以内）]"
toolPrice: "[価格帯（例：無料 / $20/月〜）]"
toolFreeplan: "[あり/なし]"
toolCategory: "{category}"
toolLanguage: "[日本語対応状況]"
rating: [3.5〜5.0の評価]
affiliateUrl: "[公式サイトURL]"
officialUrl: "[公式サイトURL]"
featured: false
isNew: true
isPopular: false
draft: false
---

[記事本文]
"""


def load_tools_queue() -> list:
    """ツールキューからツール情報を読み込む"""
    if TOOLS_DATA_FILE.exists():
        with open(TOOLS_DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("queue", [])
    return []


def get_existing_articles() -> set:
    """既存の記事のツール名セットを返す"""
    existing = set()
    if CONTENT_DIR.exists():
        for md_file in CONTENT_DIR.glob("*.md"):
            # ファイル名からツール名を推測
            existing.add(md_file.stem.lower())
    return existing


def select_tool(tool_name: str, category: str) -> tuple:
    """生成するツールを選択する"""
    if tool_name:
        return tool_name, category if category != "自動選択" else "文章生成AI"

    # キューからツールを選択
    queue = load_tools_queue()
    existing = get_existing_articles()

    for tool in queue:
        tool_slug = tool.get("name", "").lower().replace(" ", "-")
        if tool_slug not in existing:
            return tool.get("name"), tool.get("category", "文章生成AI")

    # キューが空の場合はデフォルトのツールリストから選択
    default_tools = [
        ("Gemini 2.0 Flash", "文章生成AI"),
        ("Stable Diffusion 3", "画像生成AI"),
        ("GitHub Copilot", "コーディングAI"),
        ("Otter.ai", "業務効率化AI"),
        ("Surfer SEO", "マーケティングAI"),
    ]

    for tool_name, cat in default_tools:
        slug = tool_name.lower().replace(" ", "-").replace(".", "")
        if slug not in existing:
            return tool_name, cat

    return "Claude 3.5 Haiku", "文章生成AI"


def generate_article(tool_name: str, category: str) -> str:
    """OpenAI APIを使って記事を生成する"""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY 環境変数が設定されていません")

    model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    client = OpenAI(api_key=api_key)

    today = datetime.now().strftime("%Y-%m-%d")

    prompt = ARTICLE_PROMPT_TEMPLATE.format(
        tool_name=tool_name,
        category=category,
        additional_info="最新の公式情報をもとに、正確な情報を提供してください。",
        date=today,
    )

    print(f"[INFO] OpenAI API ({model}) を使って記事を生成中: {tool_name}")

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "あなたはAIツール専門メディアの編集者です。SEOに最適化された高品質な日本語レビュー記事を作成します。",
            },
            {"role": "user", "content": prompt},
        ],
        max_tokens=3000,
        temperature=0.7,
    )

    content = response.choices[0].message.content
    usage = response.usage

    print(f"[INFO] 生成完了: {usage.total_tokens} トークン使用")
    print(f"[INFO] 推定コスト: ${usage.total_tokens * 0.00000015:.6f} (gpt-4o-mini)")

    return content, usage


def save_article(content: str, tool_name: str) -> Path:
    """生成した記事を保存する"""
    # ファイル名を生成
    slug = tool_name.lower()
    slug = re.sub(r'[^\w\s-]', '', slug)
    slug = re.sub(r'[\s_]+', '-', slug)
    slug = slug.strip('-')

    today = datetime.now().strftime("%Y-%m-%d")
    filename = f"{slug}-review.md"
    filepath = CONTENT_DIR / filename

    # 既存ファイルが存在する場合は日付を追加
    if filepath.exists():
        filename = f"{slug}-review-{today}.md"
        filepath = CONTENT_DIR / filename

    CONTENT_DIR.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"[INFO] 記事を保存しました: {filepath}")
    return filepath


def log_result(tool_name: str, category: str, filepath: Path, usage) -> None:
    """生成結果をログに記録する"""
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    log_file = LOGS_DIR / "generation_log.jsonl"
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "tool_name": tool_name,
        "category": category,
        "file": str(filepath),
        "tokens_used": usage.total_tokens if usage else 0,
        "estimated_cost_usd": usage.total_tokens * 0.00000015 if usage else 0,
        "model": os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
        "status": "success",
    }

    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

    print(f"[INFO] ログを記録しました: {log_file}")


def main():
    parser = argparse.ArgumentParser(description="AI Recipe Hub 記事自動生成スクリプト")
    parser.add_argument("--tool-name", type=str, default="", help="生成するAIツール名")
    parser.add_argument("--category", type=str, default="自動選択", help="カテゴリ")
    args = parser.parse_args()

    # ツールを選択
    tool_name, category = select_tool(args.tool_name, args.category)
    print(f"[INFO] 対象ツール: {tool_name} ({category})")

    # 記事を生成
    content, usage = generate_article(tool_name, category)

    # 記事を保存
    filepath = save_article(content, tool_name)

    # ログを記録
    log_result(tool_name, category, filepath, usage)

    print(f"[SUCCESS] 記事生成完了: {tool_name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
