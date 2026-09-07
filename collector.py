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

# 权威且高频更新的公开 RSS 订阅源（经过深度扩充与实测验证）
RSS_SOURCES = {
    "economy": [
        # 1. 谷歌新闻顶级宏观财经聚合（自动汇集彭博 Bloomberg、路透社 Reuters、金融时报 FT 等）
        {
            "name": "Bloomberg/Reuters/FT 聚合 (Google News)",
            "url": "https://news.google.com/rss/search?q=US+economy+Fed+inflation+when:24h&hl=en-US&gl=US&ceid=US:en"
        },
        # 2. 华尔街日报 (WSJ)
        {
            "name": "华尔街日报市场版 (WSJ Markets)",
            "url": "https://feeds.a.dj.com/rss/RSSMarketsMain.xml"
        },
        {
            "name": "华尔街日报商业版 (WSJ Business)",
            "url": "https://feeds.a.dj.com/rss/WSJcomUSBusiness.xml"
        },
        # 3. CNBC 财经与宏观
        {
            "name": "CNBC 宏观经济 (CNBC Economy)",
            "url": "https://www.cnbc.com/id/20910258/device/rss/rss.html"
        },
        {
            "name": "CNBC 金融市场 (CNBC Finance)",
            "url": "https://www.cnbc.com/id/10000664/device/rss/rss.html"
        },
        # 4. 雅虎全球财经
        {
            "name": "雅虎全球财经 (Yahoo Finance)",
            "url": "https://finance.yahoo.com/news/rssindex"
        },
        # 5. MarketWatch 市场实时速递
        {
            "name": "MarketWatch 实时热点",
            "url": "https://feeds.content.dowjones.io/public/rss/mw_realtimeheadlines"
        },
        # 6. 美联储官方新闻发布
        {
            "name": "美联储官方发布 (Federal Reserve)",
            "url": "https://www.federalreserve.gov/feeds/press_all.xml"
        }
    ],
    "politics": [
        # 1. 谷歌政治聚合（自动汇集美联社 AP、华盛顿邮报 WaPo、Axios、CNN 等）
        {
            "name": "AP/WaPo/Axios 政治聚合 (Google News)",
            "url": "https://news.google.com/rss/search?q=US+politics+White+House+Congress+when:24h&hl=en-US&gl=US&ceid=US:en"
        },
        # 2. 纽约时报 (NYT)
        {
            "name": "纽约时报政治专栏 (NYT Politics)",
            "url": "https://rss.nytimes.com/services/xml/rss/nyt/Politics.xml"
        },
        # 3. Politico 政治前沿
        {
            "name": "Politico 全美政治",
            "url": "https://rss.politico.com/politics-news.xml"
        },
        # 4. 国会山报 (The Hill)
        {
            "name": "国会山报 (The Hill)",
            "url": "https://thehill.com/feed/"
        },
        # 5. 美国国家公共电台 (NPR)
        {
            "name": "NPR 深度政治观察",
            "url": "https://feeds.npr.org/1014/rss.xml"
        }
    ],
    "military": [
        # 1. 谷歌防务聚合（自动汇集五角大楼、战略智库、印太与中东一线行动）
        {
            "name": "五角大楼与全球军情聚合 (Google News)",
            "url": "https://news.google.com/rss/search?q=Pentagon+US+military+defense+when:24h&hl=en-US&gl=US&ceid=US:en"
        },
        # 2. 美国国防部官方动态 (DoD News)
        {
            "name": "美国国防部 (DoD News)",
            "url": "https://www.defense.gov/DesktopModules/ArticleCS/RSS.ashx?ContentType=1&Site=945&max=20"
        },
        # 3. 美国国防部重大军费与采办合同 (DoD Contracts)
        {
            "name": "国防部重大采办 (DoD Contracts)",
            "url": "https://www.defense.gov/DesktopModules/ArticleCS/RSS.ashx?ContentType=400&Site=945&max=20"
        },
        # 4. 防务一号 (Defense One)
        {
            "name": "防务一号 (Defense One)",
            "url": "https://www.defenseone.com/rss/all/"
        },
        # 5. 军事时报 (Military Times)
        {
            "name": "军事时报 (Military Times)",
            "url": "https://www.militarytimes.com/arc/outboundfeeds/rss/category/news/pentagon-congress/?outputType=xml"
        },
        # 6. C4ISRNET 军事智能与网络战
        {
            "name": "C4ISRNET 军事科技",
            "url": "https://www.c4isrnet.com/arc/outboundfeeds/rss/?outputType=xml"
        },
        # 7. 任务与目的 (Task & Purpose)
        {
            "name": "前线防务 (Task & Purpose)",
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
