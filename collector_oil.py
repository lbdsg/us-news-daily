import sys
import io
import time
from datetime import datetime, timezone, timedelta
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
import feedparser

# 适配 Windows 终端编码，防止中文输出乱码
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/rss+xml, application/xml, text/xml, application/json, */*"
}

def clean_html(raw_html: str) -> str:
    """去除 HTML 标签，保留纯文本"""
    if not raw_html:
        return ""
    clean_text = re.sub(r"<.*?>", "", raw_html)
    clean_text = re.sub(r"&[a-zA-Z0-9#]+;", " ", clean_text)
    clean_text = re.sub(r"\s+", " ", clean_text).strip()
    return clean_text

def fetch_oil_tickers() -> dict:
    """
    毫秒级抓取国际原油、成品油与天然气最新期货盘面数据 (来自 Yahoo Finance 公开行情)
    免 API Key，实时获取最新成交价、昨收价、日内涨跌额及百分比
    """
    tickers = {
        "WTI原油": "CL=F",
        "布伦特原油": "BZ=F",
        "美天然气": "NG=F",
        "RBOB汽油": "RB=F"
    }
    results = {}
    for name, symbol in tickers.items():
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d"
        try:
            resp = requests.get(url, headers=HEADERS, timeout=6)
            if resp.status_code == 200:
                data = resp.json()
                meta = data.get("chart", {}).get("result", [{}])[0].get("meta", {})
                price = meta.get("regularMarketPrice")
                prev_close = meta.get("chartPreviousClose")
                if price is not None and prev_close:
                    change = price - prev_close
                    pct_change = (change / prev_close) * 100
                    sign = "+" if change >= 0 else ""
                    results[name] = {
                        "symbol": symbol,
                        "price": round(price, 2),
                        "change": round(change, 2),
                        "pct_change": round(pct_change, 2),
                        "formatted": f"{price:.2f} ({sign}{change:.2f}, {sign}{pct_change:.2f}%)"
                    }
        except Exception as e:
            print(f"⚠️ [行情获取失败] {name} ({symbol}): {e}")
    return results

# 权威且高频更新的原油与石化专业信源矩阵
RSS_SOURCES_OIL = {
    # 1. 国际原油与宏观地缘能源权威
    "crude_oil_global": [
        {
            "name": "OilPrice 全球能源要闻",
            "url": "https://oilprice.com/rss/main"
        },
        {
            "name": "CNBC 能源板块 (CNBC Energy)",
            "url": "https://www.cnbc.com/id/19836768/device/rss/rss.html"
        },
        {
            "name": "路透/彭博/FT 国际原油聚合 (Google News)",
            "url": "https://news.google.com/rss/search?q=(crude+oil+OR+petroleum+OR+OPEC+OR+Brent+OR+WTI)+when:4h&hl=en-US&gl=US&ceid=US:en"
        },
        {
            "name": "MarketWatch 大宗热点",
            "url": "https://feeds.content.dowjones.io/public/rss/mw_realtimeheadlines"
        }
    ],
    # 2. 中下游石化与化工产业链垂直智库
    "petrochemical_downstream": [
        {
            "name": "化工工程在线 (Chemical Engineering)",
            "url": "https://www.chemengonline.com/feed/"
        },
        {
            "name": "烃加工与石化炼化 (Hydrocarbon Processing)",
            "url": "https://www.hydrocarbonprocessing.com/rss"
        },
        {
            "name": "全球石化与塑料聚合 (Google News)",
            "url": "https://news.google.com/rss/search?q=(petrochemical+OR+plastics+industry+OR+naphtha+OR+ethylene+OR+refinery)+when:12h&hl=en-US&gl=US&ceid=US:en"
        }
    ],
    # 3. 国内原油期货与化工现货动态（聚酯/聚烯烃/甲醇）
    "china_macro_commodity": [
        {
            "name": "国内原油石化与大宗商品前沿 (Google News)",
            "url": "https://news.google.com/rss/search?q=(原油+OR+石化+OR+成品油+OR+聚酯+OR+PTA+OR+聚丙烯+OR+甲醇+OR+欧佩克)+when:6h&hl=zh-CN&gl=CN&ceid=CN:zh-Hans"
        }
    ]
}

def is_recent(entry_time_struct, max_hours=6) -> bool:
    """判断文章是否在最近指定小时内"""
    if not entry_time_struct:
        return True
    try:
        pub_dt = datetime(*entry_time_struct[:6], tzinfo=timezone.utc)
        now_dt = datetime.now(timezone.utc)
        return (now_dt - pub_dt) <= timedelta(hours=max_hours)
    except Exception:
        return True

def fetch_feed(feed_info: dict, max_hours: int = 6) -> tuple:
    """抓取单个原油化工 RSS 源并提取核心字段，故障自动隔离"""
    name = feed_info["name"]
    url = feed_info["url"]
    items = []
    success = False
    try:
        resp = requests.get(url, headers=HEADERS, timeout=8)
        if resp.status_code != 200:
            return items, False

        feed = feedparser.parse(resp.content)
        for entry in feed.entries[:10]:
            title = entry.get("title", "").strip()
            link = entry.get("link", "").strip()
            summary = clean_html(entry.get("summary", entry.get("description", "")))

            time_struct = entry.get("published_parsed") or entry.get("updated_parsed")
            if not is_recent(time_struct, max_hours=max_hours):
                continue

            if title and link:
                items.append({
                    "source": name,
                    "title": title,
                    "link": link,
                    "summary": summary[:300]
                })
        success = True
    except Exception as e:
        print(f"⚠️ [信源故障] {name} 访问失败: {e}，已自动跳过")
        success = False
    return items, success

def collect_oil_news() -> dict:
    """按分类高并发汇总原油与石化资讯，包含盘面数据与新闻资讯"""
    # 1. 抓取实时盘面
    print("📈 正在抓取国际原油期货实时盘面 (WTI/Brent/天然气)...")
    tickers = fetch_oil_tickers()
    for name, info in tickers.items():
        print(f"   - {name}: {info['formatted']}")

    # 2. 并发抓取权威资讯
    results = {
        "tickers": tickers,
        "crude_oil_global": [],
        "petrochemical_downstream": [],
        "china_macro_commodity": []
    }

    print(f"🚀 开始并发抓取原油化工行业权威信源...")
    for category, feeds in RSS_SOURCES_OIL.items():
        seen_titles = set()
        category_items = []

        with ThreadPoolExecutor(max_workers=6) as executor:
            future_to_feed = {
                executor.submit(fetch_feed, feed, 6): feed
                for feed in feeds
            }
            for future in as_completed(future_to_feed):
                try:
                    feed_items, is_ok = future.result()
                    category_items.extend(feed_items)
                except Exception:
                    pass

        # 本地去重聚合
        for item in category_items:
            simplified_title = re.sub(r"[^\w]", "", item["title"].lower())
            if simplified_title not in seen_titles:
                seen_titles.add(simplified_title)
                results[category].append(item)

        # 兜底保障：若最新 6 小时内条目较少，适度放宽至 18 小时以保证情报深度
        if len(results[category]) < 3:
            with ThreadPoolExecutor(max_workers=6) as executor:
                futures = [executor.submit(fetch_feed, feed, 18) for feed in feeds]
                for future in as_completed(futures):
                    try:
                        feed_items, _ = future.result()
                        for item in feed_items:
                            simplified_title = re.sub(r"[^\w]", "", item["title"].lower())
                            if simplified_title not in seen_titles:
                                seen_titles.add(simplified_title)
                                results[category].append(item)
                    except Exception:
                        pass

        print(f"✅ 分类 [{category}] 采集完成，共 {len(results[category])} 条情报。")

    return results

if __name__ == "__main__":
    data = collect_oil_news()
    print("\n--- 盘面数据 ---")
    print(data["tickers"])
    print(f"\n--- 资讯统计 ---")
    print(f"国际原油: {len(data['crude_oil_global'])} 条")
    print(f"石化下游: {len(data['petrochemical_downstream'])} 条")
    print(f"国内大宗: {len(data['china_macro_commodity'])} 条")
