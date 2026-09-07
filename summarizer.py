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
        f"你的任务是为高净值投资人及战略决策者编写一份《美国核心动态内参 · {edition}》。"
        f"时段定位：{focus_hint}\n"
        "排版与美学要求（专为手机端优雅阅读定制）：\n"
        "1. 严谨、专业、去粗取精，剔除低价值碎片信息，聚焦对全球局势或资本市场具有实质影响的大事件；\n"
        "2. 中文表述要地道精炼，专业术语准确（如美联储点阵图、CPI、五角大楼防务预算、印太司令部等）；\n"
        "3. 排版必须层次分明、极具可读性：每条事件统一采用结构化的小标题与要点列表，重点数字与核心结论加粗，段落之间空行合理，绝无大块挤压文字。"
    )

    user_prompt = f"""以下是当前截至 {beijing_date} 采集到的美国最新权威英文资讯原料：

{combined_text}

请根据以上素材，撰写今日《美国核心动态内参 · {edition}》。必须严格遵循以下精美的 Markdown 排版结构输出：

# 🇺🇸 美国核心动态内参 · {edition}（{beijing_date}）

> 📌 **时段要点导读**
> * 💰 **宏观经济**：（1句话提炼该领域此时段最重磅的核心看点）
> * 🏛️ **政治博弈**：（1句话提炼白宫/国会/大国外交最关键的博弈焦点）
> * 🛡️ **军情防务**：（1句话提炼五角大楼/一线战局/军工防务的最前沿动态）

---

### 💰 一、 美国经济与金融

（提炼 3-4 个最重磅事件，每条严格按如下优美格式排版）：
1. **【事件核心大标题】**
   * 📖 **核心事实**：用 2 句话清晰讲透核心事实与关键数据（关键数据加粗）。
   * ⚡ **战略洞察**：深入剖析背后的政策意图、联储态度或华尔街博弈逻辑。
   * 🎯 **市场传导**：明确指出对美股、美债收益率、美元或大宗商品的传导影响。
   * 🔗 **权威信源**：[如 WSJ / Bloomberg / Nick Timiraos / ZeroHedge 等]

---

### 🏛️ 二、 美国政治与外交

（提炼 3-4 个最重磅事件，涵盖白宫政策、国会立法、选举与大国对外博弈）：
1. **【事件核心大标题】**
   * 📖 **核心事实**：清晰叙述白宫、国会两党拉锯或对外战略的核心事实。
   * ⚡ **政治动因**：深入分析幕后政治算盘、党派利益纠葛或大国博弈动机。
   * 🎯 **局势影响**：对全美政策走向、大选胜率或国际地缘格局的实质作用。
   * 🔗 **权威信源**：[如 Punchbowl News / NYT / Politico / Foreign Affairs 等]

---

### 🛡️ 三、 防务与军事动态

（提炼 3-4 个最重磅事件，涵盖五角大楼采办、一线战事与全球战略部署）：
1. **【事件核心大标题】**
   * 📖 **军情要点**：五角大楼重大采办/军费预算、海外基地调动或一线冲突态势。
   * ⚡ **深层研判**：防务装备代际演进、军事战略调整或战役级推演。
   * 🎯 **地缘威慑**：对区域军力平衡（如中东/欧洲/印太）带来的战略震慑效应。
   * 🔗 **权威信源**：[如 Defense Daily / DoD News / Defense News / War on the Rocks 等]

---

### 🔍 四、 综合研判与市场展望

> 💡 **全球大联动核心结论**
1. **宏观与流动性主线**：（综合当前通胀、利率与财政政策，研判跨资产流动性预期）
2. **地缘与大国博弈脉络**：（提炼政治与军事事件对全球供应链和地缘安全溢价的影响）
3. **核心资产风险提示**：（针对美股核心板块、美债期限利差、大宗商品的交易风险点）

请直接输出高质量 Markdown，不要有任何开场白或客套话。
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
