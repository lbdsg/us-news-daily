import sys
import io
from datetime import datetime, timezone, timedelta

# 适配 Windows 终端编码，防止中文输出乱码
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from collector import collect_news
from summarizer import generate_summary
from notifier import dispatch_notification
from config import NTFY_TOPIC
import json
import os
import requests

def main():
    beijing_dt = datetime.now(timezone(timedelta(hours=8)))
    beijing_now = beijing_dt.strftime("%Y-%m-%d %H:%M:%S")
    print(f"==================================================")
    print(f"🚀 开始执行美国资讯自动汇总内参任务 - 北京时间: {beijing_now}")
    print(f"==================================================")

    # 智能防重机制：若是云端容灾轮询唤醒，且本时段版本今日已成功推送到手机，直接优雅退出
    force_run = "--force" in sys.argv or os.getenv("FORCE_RUN", "").lower() in ("true", "1")
    if not force_run and NTFY_TOPIC:
        try:
            today_str = beijing_dt.strftime("%Y-%m-%d")
            hour = beijing_dt.hour
            edition = "早间版" if 4 <= hour < 11 else ("午间版" if 11 <= hour < 16 else "晚间版")
            expected_keyword = f"内参·{edition} ({today_str})"
            
            resp = requests.get(f"https://ntfy.sh/{NTFY_TOPIC}/json?poll=1", timeout=8)
            if resp.status_code == 200:
                for line in resp.text.strip().split("\n"):
                    if not line: continue
                    try:
                        msg_data = json.loads(line)
                        if expected_keyword in msg_data.get("title", ""):
                            print(f"✨ [智能防重机制] 今日【{edition}】({today_str})已成功送达手机，无需重复抓取。任务优雅结束。")
                            return
                    except Exception:
                        pass
        except Exception as e:
            print(f"防重检测网络波动，将正常执行任务: {e}")

    # 第一步：资讯采集
    print("\n[Step 1/3] 正在从公开权威源抓取经济、政治、军事资讯...")
    news_data = collect_news()
    
    total_count = sum(len(items) for items in news_data.values())
    print(f"抓取完成，共获得 {total_count} 条有效资讯条目。")
    if total_count == 0:
        print("⚠️ 未能获取到过去 24 小时内的最新资讯，请检查网络或 RSS 连通性。")
        # 即使为空也生成一次通知，提示用户
        summary = "⚠️ 今日未能成功采集到最新英文资讯，请检查抓取源网络状态。"
        dispatch_notification(summary)
        return

    # 第二步：大模型分析提炼
    print("\n[Step 2/3] 正在由大模型提炼核心内参与分析研判...")
    summary = generate_summary(news_data)
    
    # 第三步：推送分发
    print("\n[Step 3/3] 正在分发晨报推送...")
    dispatch_notification(summary)

    print("\n==================================================")
    print("🎉 任务执行完成！")
    print("==================================================")

if __name__ == "__main__":
    main()
