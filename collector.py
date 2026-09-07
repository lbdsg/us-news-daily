import sys
import io
import time
from datetime import datetime, timezone, timedelta
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
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
        },
        # 7. 圣路易斯联储 FRED 经济研究中心 (源自 awesome-finance)
        {
            "name": "圣路易斯联储研究 (FRED)",
            "url": "https://news.research.stlouisfed.org/feed/"
        },
        # 8. ZeroHedge 宏观避险与华尔街流动性预警 (源自 awesome-finance)
        {
            "name": "ZeroHedge 宏观风向",
            "url": "https://feeds.feedburner.com/zerohedge/feed"
        },
        # 9. Nick Timiraos 专栏（“新美联储通讯社”利率独家研判）
        {
            "name": "Nick Timiraos 专栏 (新美联储通讯社)",
            "url": "https://news.google.com/rss/search?q=%22Nick+Timiraos%22+when:3d&hl=en-US&gl=US&ceid=US:en"
        },
        # 10. Doomberg 顶流宏观能源与大宗商品观察
        {
            "name": "Doomberg 宏观能源内参",
            "url": "https://doomberg.substack.com/feed"
        }
    ],
    "politics": [
        # 1. 谷歌政治聚合（自动汇集美联社 AP、华盛顿邮报 WaPo、Axios、CNN 等）
        {
            "name": "AP/WaPo/Axios 政治聚合 (Google News)",
            "url": "https://news.google.com/rss/search?q=US+politics+White+House+Congress+when:24h&hl=en-US&gl=US&ceid=US:en"
        },
        # 2. Punchbowl News（Jake Sherman 创办，国会山第一闭门内参）
        {
            "name": "Punchbowl News (Jake Sherman 国会第一内参)",
            "url": "https://punchbowl.news/feed/"
        },
        # 3. 纽约时报 (NYT)
        {
            "name": "纽约时报政治专栏 (NYT Politics)",
            "url": "https://rss.nytimes.com/services/xml/rss/nyt/Politics.xml"
        },
        # 4. Politico 政治前沿
        {
            "name": "Politico 全美政治",
            "url": "https://rss.politico.com/politics-news.xml"
        },
        # 5. 国会山报 (The Hill)
        {
            "name": "国会山报 (The Hill)",
            "url": "https://thehill.com/feed/"
        },
        # 6. 国会点名报 (Roll Call - 源自 awesome-osint)
        {
            "name": "国会点名报 (Roll Call)",
            "url": "https://rollcall.com/feed/"
        },
        # 7. 美国对外关系委员会 / 外交事务期刊 (Foreign Affairs / CFR - 源自 awesome-osint)
        {
            "name": "外交事务期刊 (Foreign Affairs)",
            "url": "https://www.foreignaffairs.com/rss.xml"
        },
        # 8. 美国国家公共电台 (NPR)
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
        # 4. 防务日报武器采办与对外军售 (Defense Daily - 源自 awesome-osint)
        {
            "name": "防务日报军购军售 (Defense Daily)",
            "url": "https://www.defensedaily.com/feed/"
        },
        # 5. 防务新闻主站 (Defense News - 源自 awesome-osint)
        {
            "name": "防务新闻旗舰 (Defense News)",
            "url": "https://www.defensenews.com/arc/outboundfeeds/rss/?outputType=xml"
        },
        # 6. 防务一号 (Defense One)
        {
            "name": "防务一号 (Defense One)",
            "url": "https://www.defenseone.com/rss/all/"
        },
        # 7. 军事时报 (Military Times)
        {
            "name": "军事时报 (Military Times)",
            "url": "https://www.militarytimes.com/arc/outboundfeeds/rss/category/news/pentagon-congress/?outputType=xml"
        },
        # 8. C4ISRNET 军事智能与网络战
        {
            "name": "C4ISRNET 军事科技",
            "url": "https://www.c4isrnet.com/arc/outboundfeeds/rss/?outputType=xml"
        },
        # 9. 岩石战争防务学者智库 (War on the Rocks - 源自 awesome-osint)
        {
            "name": "岩石战争战略智库 (War on the Rocks)",
            "url": "https://warontherocks.com/feed/"
        },
        # 10. Mick Ryan 战略防务专栏（退役陆军少将，专注常规战演变）
        {
            "name": "Mick Ryan 战略防务 (退役少将)",
            "url": "https://mickryan.substack.com/feed"
        },
        # 11. 任务与目的 (Task & Purpose)
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

def fetch_feed(feed_info: dict, max_hours: int = MAX_HOURS_BACK) -> tuple:
    """抓取单个 RSS 源并提取核心字段，故障时自动隔离报错并返回空列表，不影响其他源"""
    name = feed_info["name"]
    url = feed_info["url"]
    items = []
    success = False
    try:
        resp = requests.get(url, headers=HEADERS, timeout=9)
        if resp.status_code != 200:
            print(f"⚠️ [信源异常] {name} 响应码: {resp.status_code}，已自动跳过")
            return items, False

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
        success = True
    except Exception as e:
        print(f"⚠️ [信源故障] {name} 访问失败: {e}，已自动隔离")
        success = False
    return items, success

def collect_news() -> dict:
    """按分类高并发汇总资讯，各个信源完全独立隔离，任意信源故障绝不影响正常信源推送"""
    results = {
        "economy": [],
        "politics": [],
        "military": []
    }
    
    total_sources = sum(len(feeds) for feeds in RSS_SOURCES.values())
    ok_count = 0
    fail_count = 0
    print(f"🚀 开始并发抓取全网 {total_sources} 个权威信源（自动隔离故障信源）...")

    for category, feeds in RSS_SOURCES.items():
        seen_titles = set()
        category_items = []
        
        # 采用多线程独立抓取：每个信源在独立线程中执行，单个信源挂掉或超时绝不阻塞整体进度
        with ThreadPoolExecutor(max_workers=8) as executor:
            future_to_feed = {
                executor.submit(fetch_feed, feed, MAX_HOURS_BACK): feed
                for feed in feeds
            }
            for future in as_completed(future_to_feed):
                feed_info = future_to_feed[future]
                try:
                    feed_items, is_ok = future.result()
                    if is_ok:
                        ok_count += 1
                    else:
                        fail_count += 1
                    category_items.extend(feed_items)
                except Exception as e:
                    fail_count += 1
                    print(f"⚠️ [隔离故障] {feed_info['name']}: {e}")

        # 本地去重聚合
        for item in category_items:
            simplified_title = re.sub(r"[^\w]", "", item["title"].lower())
            if simplified_title not in seen_titles:
                seen_titles.add(simplified_title)
                results[category].append(item)
                    
        # 兜底保障：若发稿淡季条目偏少（少于3条），适度放宽时间窗口至 48 小时
        if len(results[category]) < 3:
            print(f"分类 [{category}] 过去 24 小时条目较少（{len(results[category])}条），自动扩大时间窗口至 48 小时获取深度资讯...")
            with ThreadPoolExecutor(max_workers=8) as executor:
                futures = [executor.submit(fetch_feed, feed, 48) for feed in feeds]
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

        print(f"✅ 分类 [{category}] 采集完成，共 {len(results[category])} 条有效情报。")

    print(f"📊 [信源健康度汇总] 正常响应: {ok_count} 个 | 故障隔离: {fail_count} 个 | 汇聚有效情报: {sum(len(v) for v in results.values())} 条。")
    return results

if __name__ == "__main__":
    news = collect_news()
    for cat, items in news.items():
        print(f"\n===== {cat.upper()} ({len(items)}) =====")
        for idx, item in enumerate(items[:3], 1):
            print(f"{idx}. [{item['source']}] {item['title']}")
            print(f"   摘要: {item['summary'][:120]}...")
