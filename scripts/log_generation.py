#!/usr/bin/env python3
"""
記事生成ログのサマリーを出力するスクリプト
GitHub Actionsのサマリーに書き込みます。
"""

import os
import json
from datetime import datetime
from pathlib import Path

LOGS_DIR = Path(__file__).parent.parent / "logs"
LOG_FILE = LOGS_DIR / "generation_log.jsonl"


def main():
    if not LOG_FILE.exists():
        print("[INFO] ログファイルが存在しません。")
        return 0

    # 最新のログエントリを取得
    entries = []
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

    if not entries:
        print("[INFO] ログエントリがありません。")
        return 0

    # 当月の統計
    current_month = datetime.now().strftime("%Y-%m")
    monthly_entries = [e for e in entries if e.get("timestamp", "").startswith(current_month)]
    monthly_cost = sum(e.get("estimated_cost_usd", 0) for e in monthly_entries)
    monthly_articles = len(monthly_entries)

    # GitHub Actions サマリーに書き込み
    summary_file = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_file:
        with open(summary_file, "a", encoding="utf-8") as f:
            f.write("## 📊 記事生成サマリー\n\n")
            f.write(f"| 項目 | 値 |\n")
            f.write(f"|------|----|\n")
            f.write(f"| 当月生成記事数 | {monthly_articles}本 |\n")
            f.write(f"| 当月APIコスト | ${monthly_cost:.4f} |\n")
            f.write(f"| 最新生成記事 | {entries[-1].get('tool_name', 'N/A')} |\n")
            f.write(f"| 使用モデル | {entries[-1].get('model', 'N/A')} |\n")

    print(f"[INFO] 当月: {monthly_articles}本生成, コスト: ${monthly_cost:.4f}")
    return 0


if __name__ == "__main__":
    main()
