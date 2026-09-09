from datetime import datetime, timezone, timedelta
from openai import OpenAI
from config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL

def generate_summary(news_data: dict) -> str:
    """调用大模型 API 对三类新闻进行综合提炼、翻译和深度分析"""
    
    # 检查是否配置了 API KEY
    if not LLM_API_KEY or "your_api_key" in LLM_API_KEY.lower():
        return (
            "⚠️ 【系统提示】未检测到有效的 LLM_API_KEY。\n\n"
            "请在 `.env` 文件或 GitHub Secrets 中配置 `LLM_API_KEY`（支持 DeepSeek / OpenAI / Gemini 等）。\n\n"
            "**今日采集到的原始资讯统计**：\n"
            f"- 经济资讯：{len(news_data.get('economy', []))} 条\n"
            f"- 政治资讯：{len(news_data.get('politics', []))} 条\n"
            f"- 军事防务：{len(news_data.get('military', []))} 条\n"
        )

    # 组织原料文本
    raw_content = []
    
    for category, label in [
        ("economy", "【美国经济与金融】"),
        ("politics", "【美国政治与外交】"),
        ("military", "【美国军事与防务】")
    ]:
        items = news_data.get(category, [])
        raw_content.append(f"\n{label} 共 {len(items)} 条资讯：")
        for i, item in enumerate(items[:20], 1):  # 每类至多取前20条最具代表性的
            raw_content.append(
                f"{i}. 标题: {item['title']}\n"
                f"   来源: {item['source']}\n"
                f"   链接: {item['link']}\n"
                f"   摘要: {item['summary']}\n"
            )

    combined_text = "\n".join(raw_content)

    beijing_now = datetime.now(timezone(timedelta(hours=8)))
    beijing_date = beijing_now.strftime("%Y年%m月%d日")
    hour = beijing_now.hour
    if 4 <= hour < 11:
        edition = "早间内参"
        focus_hint = "重点聚焦昨夜美股收盘动态、五角大楼深夜部署及今日全美战略前瞻。"
    elif 11 <= hour < 16:
        edition = "午间速递"
        focus_hint = "重点聚焦亚太金融联动反应、华盛顿日间政策动向与突发重大热点进展。"
    else:
        edition = "晚间盘点"
        focus_hint = "重点复盘全天大事件脉络、今晚美股开盘前瞻及地缘防务最新演变。"

    system_prompt = (
        "你是一位资深的全球宏观经济、地缘政治与军事防务战略分析专家。"
        f"你的任务是为高净值投资人及战略决策者编写一份高信息密度、深度穿透、论述详实的《美国核心动态内参 · {edition}》。"
        f"时段定位：{focus_hint}\n"
        "分析深度与内容体量要求：\n"
        "1. 拒绝走马观花、过于单薄的碎片式摘要！每个事件必须有扎实的情报厚度，展开充分的事实细节、多方博弈脉络、核心人物与关键数据，全文保持在 2500-3500 字的深度研判体量；\n"
        "2. 专业术语准确（如美联储点阵图、CPI、PCE、非农就业、五角大楼防务预算、印太司令部、USMCA等），关键数据与重要结论必须加粗；\n"
        "3. 排版必须层次分明、极具可读性：每条事件统一采用结构化的小标题与要点列表，段落之间空行清晰，适合移动端精读。"
    )

    user_prompt = f"""以下是当前截至 {beijing_date} 采集到的美国最新权威英文资讯原料：

{combined_text}

请根据以上素材，撰写今日《美国核心动态内参 · {edition}》。严禁偷工减料或过度精简，必须严格遵循以下详实、深度的 Markdown 排版结构输出：

# 🇺🇸 美国核心动态内参 · {edition}（{beijing_date}）

> 📌 **时段要点导读**
> * 💰 **宏观经济**：（用高度凝练且具穿透力的话语，提炼此时段最重磅的宏观金融核心看点）
> * 🏛️ **政治博弈**：（提炼白宫/国会/大国外交最关键的博弈焦点与权力角力）
> * 🛡️ **军情防务**：（提炼五角大楼/一线战局/军工装备供应链的最前沿战略动态）

---

### 💰 一、 美国经济与金融

（从素材中精选 3-4 个最重磅的经济与金融事件，每条事件必须按以下结构深入展开，内容详实丰满）：
1. **【事件核心大标题】**
   * 📖 **核心事实**：详细叙述事件完整脉络，包含具体当事方、关键量化数据（必须加粗）、市场预期差及事件来龙去脉，不可一笔带过（不少于 3-4 句话）。
   * ⚡ **战略洞察**：深入剖析背后的政策动机、美联储与财政部博弈逻辑、华尔街主流机构分歧或宏观周期定位（不少于 3 句话）。
   * 🎯 **市场传导**：具体指出对美股细分板块（如科技/价值/工业/能源等）、美债期限收益率、美元指数及大宗商品的直接与间接传导影响（不少于 2-3 句话）。
   * 🔗 **权威信源**：[标注真实采集源，如 WSJ / Bloomberg / Nick Timiraos / ZeroHedge / CNBC 等]

---

### 🏛️ 二、 美国政治与外交

（从素材中精选 3-4 个最重磅事件，深入剖析白宫行政动向、国会两党角力、选举选情及大国外交博弈）：
1. **【事件核心大标题】**
   * 📖 **核心事实**：清晰详实讲述白宫政令、国会法案辩论、关键议员动向、选举选区民调或重大外交事件的始末细节（不少于 3-4 句话）。
   * ⚡ **政治动因**：深度穿透幕后政治算盘、党派核心利益、利益集团资助背景或大选博弈筹码（不少于 3 句话）。
   * 🎯 **局势影响**：评估该事件对全美立法进程、后续行政权力边界、两党大选胜率或国际大国关系的实质塑造（不少于 2-3 句话）。
   * 🔗 **权威信源**：[标注真实采集源，如 Punchbowl News / NYT / Politico / Foreign Affairs / NPR 等]

---

### 🛡️ 三、 防务与军事动态

（从素材中精选 3-4 个最重磅事件，涵盖五角大楼重大军费采购、一线实战态势演变、全球兵力部署与国防军工供应链）：
1. **【事件核心大标题】**
   * 📖 **军情要点**：详细讲透军购合同金额与厂商、战术武器型号及代际性能、海外前沿基地部署变动或热点冲突进展（不少于 3-4 句话）。
   * ⚡ **深层研判**：剖析装备升级背后的实战教训、美军条令演化、国防工业基础供应链瓶颈或联合作战战略调整（不少于 3 句话）。
   * 🎯 **地缘威慑**：深入评估对相关热点区域（中东/东欧/印太）军力平衡与战略态势带来的冲击和威慑变化（不少于 2-3 句话）。
   * 🔗 **权威信源**：[标注真实采集源，如 Defense Daily / DoD News / Defense News / War on the Rocks 等]

---

### 🔍 四、 综合研判与市场展望

> 💡 **全球大联动核心结论**
1. **宏观与流动性主线**：（综合当前通胀数据、利率路径与美国财政发债节奏，深度研判跨资产全球流动性走向，展开 3-4 句透彻分析）
2. **地缘与大国博弈脉络**：（将政治极化、对外制裁与前线军事态势联动起来，研判对全球大宗供应链及地缘安全溢价的系统性推升，展开 3-4 句分析）
3. **核心资产风险提示**：
   * **美股市场**：（针对不同板块如科技巨头、防务军工、顺周期工业的交易策略与估值风险提示）
   * **固收与外汇**：（美债长短端收益率倒挂/陡峭化预期，美元指数走势与非美货币风险）
   * **大宗与商品**：（国际原油、贵金属及战略农产品的价格波动与避险配置建议）

请直接输出高水准、详实厚重的 Markdown 内容，严禁任何开场白或寒暄客套。
"""

    try:
        client = OpenAI(api_key=LLM_API_KEY, base_url=LLM_BASE_URL, timeout=90)
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.4
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"调用 OpenAI 兼容接口异常: {e}")
        # 双重保险：针对 Gemini API，若兼容端点连接波动，自动通过谷歌原生 REST 接口兜底
        if "generativelanguage.googleapis.com" in LLM_BASE_URL or LLM_API_KEY.startswith(("AIza", "AQ.")):
            try:
                print("正在通过谷歌原生 REST 接口兜底生成内参...")
                import requests
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{LLM_MODEL}:generateContent?key={LLM_API_KEY}"
                payload = {
                    "contents": [{"parts": [{"text": f"{system_prompt}\n\n{user_prompt}"}]}],
                    "generationConfig": {"temperature": 0.4}
                }
                res = requests.post(url, json=payload, timeout=90)
                if res.status_code == 200:
                    data = res.json()
                    return data["candidates"][0]["content"]["parts"][0]["text"]
                else:
                    print(f"谷歌原生接口返回错误: {res.status_code} {res.text[:200]}")
            except Exception as err2:
                print(f"谷歌原生接口调用异常: {err2}")

        return f"⚠️ 晨报生成失败，大模型接口调用出错: {e}"
