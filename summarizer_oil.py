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
        "2. 详细事实与具体内容部分：必须直接用详实的文字展开叙述事实细节（包括当事国/港口/炼厂/精准量化指标/来龙去脉），【严禁输出任何外部网页超链接或 URL】！文字要讲透彻；\n"
        "3. 字体层级与无障碍阅读优化：\n"
        "   - 顶部的【10秒核心总结】和【核心大标题】保持大字号/加粗，让读者3秒一眼抓牢结论；\n"
        "   - 下方的【具体事实与深度分析】必须使用 `<small>具体文字内容...</small>` 标签包裹，使字号明显小一号，形成鲜明的视觉主次，便于快速扫读与精读分离；\n"
        "4. 全文控制在 900-1300 字，短句断行，重点数据加粗，排版呼吸感强。"
    )

    user_prompt = f"""当前时间：北京时间 {beijing_time_str}
以下是刚抓取到的实时盘面点位与中英文资讯原料：

{combined_text}

请根据以上素材，撰写《原油化工核心情报 · {hour:02d}:00 档》。严禁口水话，严禁输出任何外部链接，严格遵循以下视觉分层排版输出：

# 🛢️ 原油与化工核心快报（{beijing_time_str}）

> 💡 **【10秒核心总结】**
> * 📌 **总论**：（用1-2句大白话，直接提炼过去2小时最核心的地缘/宏观驱动力与方向判断）
> * 📈 **盘面**：（用1句大白话概括原油、天然气与下游化工品的涨跌联动现状）

---

### 📊 实时大宗盘面（红跌绿涨）
{ticker_board_text}

---

### ⚡ 一、 原油与宏观地缘深度事实

（从素材中精选 2 个最核心事件，详细叙述事实，严禁输出链接，具体内容必须用 <small> 标签包裹使字号小一号）：
1. **【事件核心大标题】**
<small>
* 📍 **具体事实经过**：详细讲透事件发生的原委、涉及的国家、机构、部队或油轮港口动态，不可一笔带过（3-4 句话完整阐述，加粗关键主体）。
* 📊 **量化指标与库存**：详细列出官方数据、EIA/API 去库增库桶数、现货溢价具体点位（关键数字**加粗**）。
* 🎯 **油价驱动逻辑**：阐明华尔街机构交易台（如高盛/摩根大通）对风险溢价与供需缺口的最新测算与推演。
</small>

---

### 🧪 二、 石化与中下游产业链深度事实

（重点剖析下游石脑油、聚酯PTA、聚烯烃PP/PE、甲醇等开工检修与利润，严禁输出链接，具体内容用 <small> 标签包裹）：
1. **【产业链核心大标题】**
<small>
* 📍 **产业链具体动态**：详细叙述具体化工品种的装置开工率变化、计划外停产检修、港口社会库存升降的文字详情。
* 🎯 **成本传导与利润**：深入分析原油/天然气价格波动对下游加工企业利润（裂解价差）的直接挤压或修复效应。
</small>

---

### 📈 三、 短线交易研判与后市提示

> 🎯 **投研量化核心建议**
<small>
* 🛢️ **原油短线策略**：明确给出布伦特与 WTI 的核心支撑位、阻力位及多空止损参考区间。
* 🧪 **化工配置建议**：指出当前高成本环境下，下游哪些品种抵抗力强（如甲醇），哪些品种面临开工下调与空配压力。
</small>

直接输出排版完成的 Markdown 内容，严禁客套寒暄。
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
