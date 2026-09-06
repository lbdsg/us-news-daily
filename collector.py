import sys
import io
import time
from datetime import datetime, timezone, timedelta
import re
import requests
import feedparser
from config import MAX_HOURS_BACK, MAX_ITEMS_PER_FEED

# 适配 Windows 终端编码，防止中文输出乱码
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# 权威且高频更新的公开 RSS 订阅源（经过实测验证）
RSS_SOURCES = {
    "economy": [
        {
            "name": "CNBC Economy",
            "url": "https://www.cnbc.com/id/20910258/device/rss/rss.html"
        },
        {
            "name": "CNBC Finance",
            "url": "https://www.cnbc.com/id/10000664/device/rss/rss.html"
        },
        {
            "name": "WSJ Markets",
            "url": "https://feeds.a.dj.com/rss/RSSMarketsMain.xml"
        },
        {
            "name": "美联储官方发布",
            "url": "https://www.federalreserve.gov/feeds/press_all.xml"
        }
    ],
    "politics": [
        {
            "name": "Politico Politics",
            "url": "https://rss.politico.com/politics-news.xml"
        },
        {
            "name": "The Hill",
            "url": "https://thehill.com/feed/"
        },
        {
            "name": "NPR Politics",
            "url": "https://feeds.npr.org/1014/rss.xml"
        }
    ],
    "military": [
        {
            "name": "美国国防部 (DoD News)",
            "url": "https://www.defense.gov/DesktopModules/ArticleCS/RSS.ashx?ContentType=1&Site=945&max=20"
        },
        {
            "name": "Military Times (Pentagon & Congress)",
            "url": "https://www.militarytimes.com/arc/outboundfeeds/rss/category/news/pentagon-congress/?outputType=xml"
        },
        {
            "name": "Task & Purpose",
            "url": "https://taskandpurpose.com/feed/"
        }
    ]
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/rss+xml, application/xml, text/xml, */*"
}

def clean_html(raw_html: str) -> str:
    """去除 HTML 标签，保留纯文本"""
    if not raw_html:
        return ""
    clean_text = re.sub(r"<.*?>", "", raw_html)
    clean_text = re.sub(r"&[a-zA-Z0-9#]+;", " ", clean_text)
    clean_text = re.sub(r"\s+", " ", clean_text).strip()
    return clean_text

def is_recent(entry_time_struct, max_hours=MAX_HOURS_BACK) -> bool:
    """判断文章是否在最近指定小时内"""
    if not entry_time_struct:
        return True  # 无法获取时间时默认保留，交由去重处理
    try:
        pub_dt = datetime(*entry_time_struct[:6], tzinfo=timezone.utc)
        now_dt = datetime.now(timezone.utc)
        return (now_dt - pub_dt) <= timedelta(hours=max_hours)
    except Exception:
        return True

def fetch_feed(feed_info: dict, max_hours: int = MAX_HOURS_BACK) -> list:
    """抓取单个 RSS 源并提取核心字段"""
    name = feed_info["name"]
    url = feed_info["url"]
    items = []
    try:
        resp = requests.get(url, headers=HEADERS, timeout=12)
        if resp.status_code != 200:
            print(f"[{name}] 请求失败，状态码: {resp.status_code}")
            return items

        feed = feedparser.parse(resp.content)
        for entry in feed.entries[:MAX_ITEMS_PER_FEED]:
            title = entry.get("title", "").strip()
            link = entry.get("link", "").strip()
            summary = clean_html(entry.get("summary", entry.get("description", "")))
            
            # 时间解析与过滤
            time_struct = entry.get("published_parsed") or entry.get("updated_parsed")
            if not is_recent(time_struct, max_hours=max_hours):
                continue
            
            if title and link:
                items.append({
                    "source": name,
                    "title": title,
                    "link": link,
                    "summary": summary[:350]  # 适量截取避免过长
                })
    except Exception as e:
        print(f"[{name}] 抓取异常: {e}")
    return items

def collect_news() -> dict:
    """按分类汇总所有资讯，带有周末/假日自适应防空窗兜底"""
    results = {
        "economy": [],
        "politics": [],
        "military": []
    }
    
    for category, feeds in RSS_SOURCES.items():
        print(f"正在抓取分类: {category}...")
        seen_titles = set()
        for feed in feeds:
            feed_items = fetch_feed(feed, max_hours=MAX_HOURS_BACK)
            for item in feed_items:
                simplified_title = re.sub(r"[^\w]", "", item["title"].lower())
                if simplified_title not in seen_titles:
                    seen_titles.add(simplified_title)
                    results[category].append(item)
                    
        # 兜底保障：若周末或发稿淡季条数偏少（少于3条），适度放宽时间窗口至 48 小时
        if len(results[category]) < 3:
            print(f"分类 [{category}] 过去 24 小时条目较少（{len(results[category])}条），自动扩大时间窗口至 48 小时获取深度资讯...")
            for feed in feeds:
                feed_items = fetch_feed(feed, max_hours=48)
                for item in feed_items:
                    simplified_title = re.sub(r"[^\w]", "", item["title"].lower())
                    if simplified_title not in seen_titles:
                        seen_titles.add(simplified_title)
                        results[category].append(item)

        print(f"分类 [{category}] 采集完成，共 {len(results[category])} 条。")
        
    return results

if __name__ == "__main__":
    news = collect_news()
    for cat, items in news.items():
        print(f"\n===== {cat.upper()} ({len(items)}) =====")
        for idx, item in enumerate(items[:3], 1):
            print(f"{idx}. [{item['source']}] {item['title']}")
            print(f"   摘要: {item['summary'][:120]}...")
