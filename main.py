import sys
import io
from datetime import datetime, timezone, timedelta

# 适配 Windows 终端编码，防止中文输出乱码
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from collector import collect_news
from summarizer import generate_summary
from notifier import dispatch_notification

def main():
    beijing_now = datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M:%S")
    print(f"==================================================")
    print(f"🚀 开始执行美国资讯自动汇总内参任务 - 北京时间: {beijing_now}")
    print(f"==================================================")

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
