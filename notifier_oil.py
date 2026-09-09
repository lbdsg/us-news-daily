import sys
import time
import re
from datetime import datetime, timezone, timedelta
import requests
from config import NTFY_TOPIC_OIL

# 适配 Windows 终端编码，防止中文输出乱码
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

def chunk_text(text: str, max_bytes: int = 3200) -> list:
    """按段落将长文本切分成不超过指定字节数的片段"""
    paragraphs = text.split("\n\n")
    chunks = []
    current_chunk = []
    current_len = 0
    for p in paragraphs:
        p_len = len(p.encode("utf-8")) + 2
        if current_len + p_len > max_bytes and current_chunk:
            chunks.append("\n\n".join(current_chunk))
            current_chunk = [p]
            current_len = p_len
        else:
            current_chunk.append(p)
            current_len += p_len
    if current_chunk:
        chunks.append("\n\n".join(current_chunk))
    return chunks

def send_ntfy_oil(title: str, content: str) -> bool:
    """推送到 ntfy 专属频道 yuanyou123456，根据时间自动调整夜间静音优先级"""
    topic = NTFY_TOPIC_OIL or "yuanyou123456"
    try:
        url = "https://ntfy.sh"
        beijing_now = datetime.now(timezone(timedelta(hours=8)))
        hour = beijing_now.hour

        # 智能夜间免打扰策略：凌晨 00:00 - 07:00 采用 Low Priority (2) 静音常驻，不打扰睡眠；日间正常提醒 (3)
        is_night = 0 <= hour < 7
        priority = 2 if is_night else 3

        # 智能分卷：若全文在 3800 字节以内，优先作为 1 条完整通知发送（手机端体验最佳，单次弹窗即可阅读全篇）
        custom_chunks = []
        if len(content.encode("utf-8")) < 3800:
            custom_chunks = [
                (title, content, ["oil_drum", "chart_with_upwards_trend", "fuelpump", "test_tube"])
            ]
        else:
            # 超长时尝试根据板块划分（### 一、二、三）切分
            parts = re.split(r'\n(?=### [^\n]*[一二三]、)', content)
            if len(parts) >= 3:
                c1 = parts[0].strip()
                c2 = parts[1].strip()
                c3 = "\n\n".join(parts[2:]).strip()
                if (len(c1.encode("utf-8")) < 3600 and
                    len(c2.encode("utf-8")) < 3600 and
                    len(c3.encode("utf-8")) < 3600):
                    custom_chunks = [
                        (f"{title} | 盘面看板与地缘动态 (1/3)", c1, ["oil_drum", "chart_with_upwards_trend"]),
                        (f"{title} | 石化产业链动态 (2/3)", c2, ["test_tube", "fuelpump"]),
                        (f"{title} | 短线研判与后市策略 (3/3)", c3, ["bulb", "gem"])
                    ]

        if not custom_chunks:
            raw_chunks = chunk_text(content, max_bytes=3200)
            total = len(raw_chunks)
            custom_chunks = [
                (f"{title} ({i}/{total})" if total > 1 else title, c, ["oil_drum", "chart_with_upwards_trend"])
                for i, c in enumerate(raw_chunks, 1)
            ]

        total = len(custom_chunks)
        all_success = True

        for part_title, chunk, tags in custom_chunks:
            payload = {
                "topic": topic,
                "title": part_title,
                "message": chunk,
                "markdown": True,
                "priority": priority,
                "tags": tags
            }
            resp = requests.post(url, json=payload, timeout=15)
            if resp.status_code != 200:
                all_success = False
                print(f"❌ [ntfy-oil] 推送失败: {part_title}，状态码: {resp.status_code}")
            time.sleep(1.2)

        if all_success:
            p_desc = "静音常驻模式(夜间)" if is_night else "正常提醒模式(日间)"
            print(f"✅ [ntfy-oil] 成功推送到频道: {topic} (共 {total} 篇，{p_desc})")
            return True
        return False
    except Exception as e:
        print(f"❌ [ntfy-oil] 推送异常: {e}")
        return False

def dispatch_oil_notification(content: str):
    """统一分发原油化工研报通知并本地留存归档"""
    beijing_now = datetime.now(timezone(timedelta(hours=8)))
    beijing_today = beijing_now.strftime("%Y-%m-%d")
    hour = beijing_now.hour
    title = f"🛢️ 原油化工核心内参 · {hour:02d}:00档 ({beijing_today})"

    # 本地始终备份一份 markdown 文件
    filename = f"oil_report_{beijing_today.replace('-', '')}_{hour:02d}.md"
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"📁 本地原油研报已归档至: {filename}")
    except Exception as e:
        print(f"本地文件保存失败: {e}")

    # 推送到 ntfy 专属频道
    send_ntfy_oil(title, content)
