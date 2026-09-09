import sys
import io
import json
import os
from datetime import datetime, timezone, timedelta
import requests

# 适配 Windows 终端编码，防止中文输出乱码
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from collector_oil import collect_oil_news
from summarizer_oil import generate_oil_summary
from notifier_oil import dispatch_oil_notification
from config import NTFY_TOPIC_OIL

def main():
    beijing_dt = datetime.now(timezone(timedelta(hours=8)))
    beijing_now = beijing_dt.strftime("%Y-%m-%d %H:%M:%S")
    hour = beijing_dt.hour
    today_str = beijing_dt.strftime("%Y-%m-%d")

    print("==================================================")
    print(f"🚀 开始执行【原油化工 24 小时双小时推送任务】")
    print(f"⏰ 当前北京时间: {beijing_now} ({hour:02d}:00 档)")
    print(f"📢 目标频道: {NTFY_TOPIC_OIL}")
    print("==================================================")

    # 智能防重机制：检查当前时段版本是否已推送到频道
    force_run = "--force" in sys.argv or os.getenv("FORCE_RUN", "").lower() in ("true", "1")
    if not force_run and NTFY_TOPIC_OIL:
        try:
            expected_keyword = f"内参 · {hour:02d}:00档 ({today_str})"
            resp = requests.get(f"https://ntfy.sh/{NTFY_TOPIC_OIL}/json?poll=1", timeout=8)
            if resp.status_code == 200:
                for line in resp.text.strip().split("\n"):
                    if not line:
                        continue
                    try:
                        msg_data = json.loads(line)
                        if expected_keyword in msg_data.get("title", ""):
                            print(f"✨ [防重机制] 本时段【{hour:02d}:00档】研报已成功推送过，无需重复抓取。任务优雅结束。")
                            return
                    except Exception:
                        pass
        except Exception as e:
            print(f"防重检测网络波动，将正常执行任务: {e}")

    # 第一步：数据与资讯采集（含实时盘面点位）
    print("\n[Step 1/3] 正在抓取实时国际油价盘面与行业权威信源...")
    oil_data = collect_oil_news()

    total_news = (
        len(oil_data.get("crude_oil_global", [])) +
        len(oil_data.get("petrochemical_downstream", [])) +
        len(oil_data.get("china_macro_commodity", []))
    )
    print(f"采集完成，共获得 {total_news} 条有效资讯，盘面点位获取成功。")

    # 第二步：大模型分析与研报生成
    print("\n[Step 2/3] 正在由 Gemini 大模型提炼产业链逻辑与短线盘面研判...")
    summary = generate_oil_summary(oil_data)

    # 第三步：推送与归档
    print("\n[Step 3/3] 正在推送至专属主题并归档...")
    dispatch_oil_notification(summary)

    print("\n==================================================")
    print("🎉 原油化工双小时情报任务执行完成！")
    print("==================================================")

if __name__ == "__main__":
    main()
