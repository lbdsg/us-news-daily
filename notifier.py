import sys
import time
import smtplib
from email.header import Header
from email.mime.text import MIMEText
from datetime import datetime, timezone, timedelta

# 适配 Windows 终端编码，防止中文与表情输出乱码
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import requests
from config import (
    NTFY_TOPIC,
    PUSHPLUS_TOKEN,
    SERVERCHAN_KEY,
    FEISHU_WEBHOOK,
    WECOM_WEBHOOK,
    DINGTALK_WEBHOOK,
    MAIL_HOST,
    MAIL_PORT,
    MAIL_USER,
    MAIL_PASS,
    MAIL_TO
)

def send_pushplus(title: str, content: str) -> bool:
    """通过 PushPlus（推送加）推送到微信"""
    if not PUSHPLUS_TOKEN:
        return False
    try:
        url = "http://www.pushplus.plus/send"
        payload = {
            "token": PUSHPLUS_TOKEN,
            "title": title,
            "content": content,
            "template": "markdown"
        }
        resp = requests.post(url, json=payload, timeout=15)
        res_json = resp.json()
        if res_json.get("code") == 200:
            print("✅ [PushPlus] 微信推送成功！")
            return True
        else:
            print(f"❌ [PushPlus] 推送失败: {res_json.get('msg')}")
            return False
    except Exception as e:
        print(f"❌ [PushPlus] 请求异常: {e}")
        return False

def send_serverchan(title: str, content: str) -> bool:
    """通过 Server酱 推送到微信"""
    if not SERVERCHAN_KEY:
        return False
    try:
        url = f"https://sctapi.ftqq.com/{SERVERCHAN_KEY}.send"
        payload = {
            "title": title,
            "desp": content
        }
        resp = requests.post(url, data=payload, timeout=15)
        res_json = resp.json()
        if res_json.get("code") == 0:
            print("✅ [Server酱] 微信推送成功！")
            return True
        else:
            print(f"❌ [Server酱] 推送失败: {res_json.get('message')}")
            return False
    except Exception as e:
        print(f"❌ [Server酱] 请求异常: {e}")
        return False

def send_feishu(title: str, content: str) -> bool:
    """推送到飞书自定义群机器人"""
    if not FEISHU_WEBHOOK:
        return False
    try:
        payload = {
            "msg_type": "interactive",
            "card": {
                "header": {
                    "title": {"tag": "plain_text", "content": title},
                    "template": "blue"
                },
                "elements": [
                    {
                        "tag": "markdown",
                        "content": content
                    }
                ]
            }
        }
        resp = requests.post(FEISHU_WEBHOOK, json=payload, timeout=15)
        if resp.status_code == 200:
            print("✅ [飞书] 推送成功！")
            return True
        else:
            print(f"❌ [飞书] 推送失败，状态码: {resp.status_code}")
            return False
    except Exception as e:
        print(f"❌ [飞书] 请求异常: {e}")
        return False

def send_wecom(title: str, content: str) -> bool:
    """推送到企业微信机器人"""
    if not WECOM_WEBHOOK:
        return False
    try:
        payload = {
            "msgtype": "markdown",
            "markdown": {
                "content": f"### {title}\n\n{content}"
            }
        }
        resp = requests.post(WECOM_WEBHOOK, json=payload, timeout=15)
        if resp.status_code == 200:
            print("✅ [企业微信] 推送成功！")
            return True
        else:
            print(f"❌ [企业微信] 推送失败，状态码: {resp.status_code}")
            return False
    except Exception as e:
        print(f"❌ [企业微信] 请求异常: {e}")
        return False

def send_dingtalk(title: str, content: str) -> bool:
    """推送到钉钉机器人"""
    if not DINGTALK_WEBHOOK:
        return False
    try:
        payload = {
            "msgtype": "markdown",
            "markdown": {
                "title": title,
                "text": f"### {title}\n\n{content}"
            }
        }
        resp = requests.post(DINGTALK_WEBHOOK, json=payload, timeout=15)
        if resp.status_code == 200:
            print("✅ [钉钉] 推送成功！")
            return True
        else:
            print(f"❌ [钉钉] 推送失败，状态码: {resp.status_code}")
            return False
    except Exception as e:
        print(f"❌ [钉钉] 请求异常: {e}")
        return False

def markdown_to_html_email(md_content: str) -> str:
    """将 Markdown 转换为排版精美的 HTML 邮件模板"""
    try:
        import markdown
        html_body = markdown.markdown(md_content, extensions=["extra", "nl2br"])
    except Exception:
        html_body = f"<pre style='white-space: pre-wrap;'>{md_content}</pre>"

    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
            line-height: 1.68;
            color: #1f2328;
            background-color: #f4f6f9;
            margin: 0;
            padding: 20px 10px;
        }}
        .email-card {{
            max-width: 680px;
            margin: 0 auto;
            background: #ffffff;
            padding: 30px 24px;
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.05);
            border: 1px solid #e1e4e8;
        }}
        h1 {{
            color: #0969da;
            font-size: 22px;
            border-bottom: 2px solid #0969da;
            padding-bottom: 12px;
            margin-top: 0;
        }}
        h3 {{
            color: #24292f;
            font-size: 16px;
            margin-top: 24px;
            margin-bottom: 12px;
            border-left: 4px solid #0969da;
            padding-left: 10px;
        }}
        blockquote {{
            margin: 16px 0;
            padding: 12px 16px;
            background-color: #f0f7ff;
            border-left: 4px solid #0969da;
            border-radius: 4px;
            color: #034896;
            font-size: 14px;
        }}
        p, li {{
            font-size: 14.5px;
            color: #333333;
        }}
        strong {{
            color: #111827;
        }}
        a {{
            color: #0969da;
            text-decoration: none;
        }}
        a:hover {{
            text-decoration: underline;
        }}
        hr {{
            border: 0;
            height: 1px;
            background: #e5e7eb;
            margin: 22px 0;
        }}
        .footer {{
            text-align: center;
            margin-top: 25px;
            font-size: 12px;
            color: #8c959f;
        }}
    </style>
</head>
<body>
    <div class="email-card">
        {html_body}
        <div class="footer">
            <hr>
            本内参由自动化系统每日 06:00 自动采集并生成推送
        </div>
    </div>
</body>
</html>"""

def send_email(title: str, content: str) -> bool:
    """通过 SMTP 发送 HTML 邮件至 QQ 邮箱等"""
    if not (MAIL_HOST and MAIL_USER and MAIL_PASS and MAIL_TO):
        return False
    try:
        html_content = markdown_to_html_email(content)
        message = MIMEText(html_content, "html", "utf-8")
        message["From"] = Header(f"早报助手 <{MAIL_USER}>", "utf-8")
        message["To"] = Header(MAIL_TO, "utf-8")
        message["Subject"] = Header(title, "utf-8")

        if MAIL_PORT == 465:
            server = smtplib.SMTP_SSL(MAIL_HOST, MAIL_PORT, timeout=25)
        else:
            server = smtplib.SMTP(MAIL_HOST, MAIL_PORT, timeout=25)
            server.starttls()

        server.login(MAIL_USER, MAIL_PASS)
        server.sendmail(MAIL_USER, [MAIL_TO], message.as_string())
        server.quit()
        print(f"✅ [邮件] 成功发送早报至: {MAIL_TO}")
        return True
    except Exception as e:
        print(f"❌ [邮件] 发送异常: {e}")
        return False

def chunk_text(text: str, max_bytes: int = 3200) -> list:
    """按段落将长文本切分成不超过指定字节数的片段，保证阅读连续性"""
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

def send_ntfy(title: str, content: str) -> bool:
    """通过 ntfy.sh 推送到手机或网页端（自适应分段，免注册/免密码）"""
    if not NTFY_TOPIC:
        return False
    try:
        url = "https://ntfy.sh"
        chunks = chunk_text(content, max_bytes=3200)
        total = len(chunks)
        all_success = True

        for idx, chunk in enumerate(chunks, 1):
            part_title = f"{title} ({idx}/{total})" if total > 1 else title
            payload = {
                "topic": NTFY_TOPIC,
                "title": part_title,
                "message": chunk,
                "markdown": True,
                "tags": ["newspaper", "flag_us"]
            }
            resp = requests.post(url, json=payload, timeout=15)
            if resp.status_code != 200:
                all_success = False
                print(f"❌ [ntfy] 分段 {idx}/{total} 推送失败，状态码: {resp.status_code}")
            time.sleep(0.5)

        if all_success:
            print(f"✅ [ntfy] 成功完整推送到频道: {NTFY_TOPIC} (共 {total} 段)")
            return True
        return False
    except Exception as e:
        print(f"❌ [ntfy] 推送异常: {e}")
        return False

def dispatch_notification(content: str):
    """统一分发通知"""
    beijing_today = datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d")
    title = f"🇺🇸 美国核心动态内参 ({beijing_today})"

    # 本地始终备份一份 markdown 文件
    filename = f"daily_report_{beijing_today.replace('-', '')}.md"
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"📁 本地晨报已归档至: {filename}")
    except Exception as e:
        print(f"本地文件保存失败: {e}")

    sent_any = False
    if send_ntfy(title, content):
        sent_any = True
    if send_pushplus(title, content):
        sent_any = True
    if send_serverchan(title, content):
        sent_any = True
    if send_feishu(title, content):
        sent_any = True
    if send_wecom(title, content):
        sent_any = True
    if send_dingtalk(title, content):
        sent_any = True
    if send_email(title, content):
        sent_any = True

    if not sent_any:
        print("ℹ️ 未配置任何远程推送渠道。仅保存至本地文件。")
