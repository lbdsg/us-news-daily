from datetime import datetime, timezone, timedelta
from openai import OpenAI
from config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL

def generate_oil_summary(oil_data: dict) -> str:
    """调用大模型 API 对原油化工盘面与三类新闻进行深度提炼与产业链分析"""

    beijing_now = datetime.now(timezone(timedelta(hours=8)))
    beijing_time_str = beijing_now.strftime("%Y年%m月%d日 %H:00")
    hour = beijing_now.hour

    tickers = oil_data.get("tickers", {})
    ticker_lines = []
    for name, info in tickers.items():
        pct = info["pct_change"]
        color = "🟢 +" if pct >= 0 else "🔴 "
        ticker_lines.append(f"* {name}：`{info['price']}` ({color}{pct}%, `{info['change']:+0.2f}`)")

    ticker_board_text = "\n".join(ticker_lines) if ticker_lines else "暂未获取到最新盘面点位"

    # 检查是否配置了 API KEY
    if not LLM_API_KEY or "your_api_key" in LLM_API_KEY.lower():
        return (
            f"# 🛢️ 原油与化工核心快报（{beijing_time_str}）\n\n"
            f"> 📊 **实时大宗盘面看板**\n"
            f"{ticker_board_text}\n\n"
            f"⚠️ 【系统提示】未检测到有效的 LLM_API_KEY，已仅输出实时基准盘面。"
        )

    # 组织原料文本
    raw_content = []
    raw_content.append(f"【实时盘面点位】\n{ticker_board_text}\n")

    category_map = [
        ("crude_oil_global", "【国际原油与宏观地缘资讯】"),
        ("petrochemical_downstream", "【石化与中下游产业链资讯】"),
        ("china_macro_commodity", "【国内原油石化与大宗商品动态】")
    ]

    for cat_key, label in category_map:
        items = oil_data.get(cat_key, [])
        raw_content.append(f"\n{label} 共 {len(items)} 条：")
        for i, item in enumerate(items[:15], 1):
            raw_content.append(
                f"{i}. 标题: {item['title']}\n"
                f"   来源: {item['source']}\n"
                f"   链接: {item['link']}\n"
                f"   摘要: {item['summary']}\n"
            )

    combined_text = "\n".join(raw_content)

    system_prompt = (
        "你是一位供职于顶级大宗商品对冲基金的能源化工首席宏观研究员。"
        "你的读者是专业的原油期货与化工产业链（石脑油、聚酯、聚烯烃、甲醇）交易员与现货决策者。"
        "任务目标：根据提供的实时盘面数据与最新 2 小时资讯，输出一份高信息密度、逻辑硬核、言简意赅的《原油化工双小时内参》。"
        "要求：\n"
        "1. 务必结合开篇给出的实时原油/天然气涨跌点位做归因分析，拒绝假大空的套话；\n"
        "2. 重点关注：OPEC+动向、地缘溢价（中东/红海/俄乌）、EIA/API库存、炼厂裂解价差（Crack Spread）、下游石化品（PTA/MEG/PP/PE/甲醇）开工与现货基差；\n"
        "3. 全文控制在 1200-2000 字，结构清晰，重点数据与支撑阻力结论必须加粗。"
    )

    user_prompt = f"""当前时间：北京时间 {beijing_time_str}
以下是刚抓取到的实时盘面点位与中英文资讯原料：

{combined_text}

请根据以上素材，撰写《原油化工双小时情报 · {hour:02d}:00 档》。严禁口水话，严格遵循以下 Markdown 结构输出：

# 🛢️ 原油与化工核心快报（{beijing_time_str}）

> 📊 **实时大宗盘面看板**
{ticker_board_text}
>
> 📌 **双小时核心导读**：（用2-3句话精准概括过去2小时内最核心的市场驱动力、盘面异动原因与产业链传导）

---

### ⚡ 一、 原油与宏观地缘突发

（从素材中精选 2-3 个最核心事件展开剖析）：
1. **【事件核心大标题】**
   * 📖 **事实脉络**：详细阐述事件细节（当事国/机构、关键量化指标加粗、来龙去脉）。
   * 🎯 **油价驱动**：剖析该事件对 Brent / WTI 的实际供需冲击或风险溢价定价逻辑。
   * 🔗 **信源**：[标注采集源，如 Reuters / Bloomberg / OilPrice / CNBC 等]

---

### 🧪 二、 石化与中下游产业链动态

（重点剖析下游石化品供需、开工与现货裂解）：
1. **【产业链核心标题】**
   * 📖 **产业要点**：石脑油/乙烯/聚酯PTA/聚烯烃PP/甲醇等品种的开工检修、社会库存或现货基差动态。
   * 🎯 **成本传导**：分析原油/天然气价格波动对下游化工品利润空间与定价成本的即时传导。
   * 🔗 **信源**：[标注采集源，如 Chemical Engineering / 期货日报 / 行业资讯等]

---

### 📈 三、 短线交易研判与后市提示

> 💡 **投研量化核心建议**
1. **原油与天然气短线逻辑**：（结合最新盘面点位，分析短线支撑位、阻力位及地缘多空博弈主线，展开 2-3 句）
2. **化工品产业链配置建议**：（提示下游聚酯、烯烃等利润压缩或修复的关注品种与风险点，展开 2-3 句）

直接输出专业排版的 Markdown 内容，严禁客套寒暄。
"""

    try:
        client = OpenAI(api_key=LLM_API_KEY, base_url=LLM_BASE_URL, timeout=90)
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"调用 OpenAI 兼容接口异常: {e}")
        # 谷歌原生 REST 接口兜底
        if "generativelanguage.googleapis.com" in LLM_BASE_URL or LLM_API_KEY.startswith(("AIza", "AQ.")):
            try:
                print("正在通过谷歌原生 REST 接口兜底生成原油化工内参...")
                import requests
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{LLM_MODEL}:generateContent?key={LLM_API_KEY}"
                payload = {
                    "contents": [{"parts": [{"text": f"{system_prompt}\n\n{user_prompt}"}]}],
                    "generationConfig": {"temperature": 0.3}
                }
                res = requests.post(url, json=payload, timeout=90)
                if res.status_code == 200:
                    data = res.json()
                    return data["candidates"][0]["content"]["parts"][0]["text"]
                else:
                    print(f"谷歌原生接口返回错误: {res.status_code} {res.text[:200]}")
            except Exception as err2:
                print(f"谷歌原生接口调用异常: {err2}")

        return f"⚠️ 原油化工快报生成失败，大模型接口调用出错: {e}"

if __name__ == "__main__":
    from collector_oil import collect_oil_news
    news = collect_oil_news()
    summary = generate_oil_summary(news)
    print("\n===== 生成结果预览 =====\n")
    print(summary[:600] + "\n...")
