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

    beijing_time = datetime.now(timezone(timedelta(hours=8))).strftime("%Y年%m月%d日")

    system_prompt = (
        "你是一位资深的全球宏观经济、地缘政治与军事防务战略分析专家。"
        "你的任务是为高净值投资人及战略决策者编写一份《美国每日核心动态内参》。"
        "要求：\n"
        "1. 严谨、专业、去粗取精，剔除低价值碎片信息，聚焦对全球局势或资本市场具有实质影响的大事件；\n"
        "2. 中文表述要地道精炼，专业术语准确（如美联储点阵图、CPI、五角大楼防务预算、印太司令部等）；\n"
        "3. 采用精美整洁的 Markdown 格式输出，排版需适合手机端阅读（多用重点加粗、要点列表，分段清晰）。"
    )

    user_prompt = f"""以下是今天截至 {beijing_time} 采集到的美国最新权威英文资讯原料：

{combined_text}

请根据以上素材，撰写今日《美国核心动态内参早报》，包含以下五个核心板块：

# 🇺🇸 美国核心动态内参（{beijing_time}）

> 📌 **今日导读**（用 3 句话分别总结经济、政治、军事领域今天最重磅的看点）

---

### 💰 一、 美国经济与金融
（深入提炼 3-5 个核心重磅事件，每条格式为：**【核心标题】** + 深度事实简析 + 市场影响，附带原报道源）

---

### 🏛️ 二、 美国政治与外交
（深入提炼 3-5 个核心重大事件，涵盖白宫行政令、国会博弈、重大司法判决、选举动向及大国博弈对外战略）

---

### 🛡️ 三、 防务与军事动态
（深入提炼 3-5 个核心防务事件，涵盖五角大楼重大军购与预算、一线军事交火/战事、全球军事基地部署与前沿国防科技）

---

### 🔍 四、 综合研判与市场展望
（从联动角度深度剖析：以上事件对美股/美债/美元/大宗商品走势、以及全球地缘政治格局可能带来的实质性连锁反应）

请直接输出高质量 Markdown 内容，不要有其他多余的客套话。
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
