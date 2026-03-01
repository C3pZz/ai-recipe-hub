#!/usr/bin/env python3
"""
月間APIコスト上限チェックスクリプト（停止スイッチ）
ログファイルを読み込み、当月のコストが上限を超えていれば終了コード1を返します。
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path

LOGS_DIR = Path(__file__).parent.parent / "logs"
LOG_FILE = LOGS_DIR / "generation_log.jsonl"


def get_monthly_cost() -> float:
    """当月のAPIコストを計算する"""
    if not LOG_FILE.exists():
        return 0.0

    current_month = datetime.now().strftime("%Y-%m")
    total_cost = 0.0

    with open(LOG_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                ts = entry.get("timestamp", "")
                if ts.startswith(current_month):
                    total_cost += entry.get("estimated_cost_usd", 0.0)
            except json.JSONDecodeError:
                continue

    return total_cost


def main():
    cost_limit = float(os.environ.get("COST_LIMIT_USD", "10.0"))
    monthly_cost = get_monthly_cost()

    print(f"[INFO] 当月のAPIコスト: ${monthly_cost:.4f} / 上限: ${cost_limit:.2f}")

    if monthly_cost >= cost_limit:
        print(f"[STOP] 月間コスト上限 (${cost_limit}) に達しました。記事生成を停止します。")
        print("[STOP] 上限を引き上げるには、GitHub Variables の MONTHLY_COST_LIMIT_USD を変更してください。")
        sys.exit(1)

    remaining = cost_limit - monthly_cost
    print(f"[INFO] 残り予算: ${remaining:.4f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
