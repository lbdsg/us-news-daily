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
        for i, item in enumerate(items[:10], 1):  # 每类至多取前10条最具代表性的
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
（精炼列出 2-3 个核心事件，每条格式为：**【核心标题】** + 核心事实简析 + 市场影响，附带原报道源）

---

### 🏛️ 二、 美国政治与外交
（精炼列出 2-3 个核心事件，包含白宫政策、国会立法、选举动态或对外战略）

---

### 🛡️ 三、 防务与军事动态
（精炼列出 2-3 个核心事件，包含五角大楼重大举措、军工军备、印太/中东战略部署等）

---

### 🔍 四、 综合研判与市场展望
（从联动角度深度剖析：以上事件对美股/美债/美元走势、以及全球地缘政治格局可能带来的潜在影响）

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
        print(f"调用大模型 API 异常: {e}")
        return f"⚠️ 晨报生成失败，大模型接口调用出错: {e}"
