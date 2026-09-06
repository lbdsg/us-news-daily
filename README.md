# 🇺🇸 每日早间 6 点美国资讯内参自动推送系统

每天早上北京时间 **06:00** 自动抓取美国最新**宏观经济、政治外交、军事防务**权威资讯，通过谷歌大模型进行深度提炼分析，自动推送到你的专属频道：**`amenews123138`**。

**核心特色**：
- ☁️ **零运维免开机**：通过 GitHub Actions 免费云端执行，晚上电脑关机睡觉，早上 6 点准时送达。
- 📱 **完全免密码/免注册（ntfy 推送）**：只需订阅频道 `amenews123138`，手机直接弹窗，点击即看完整早报。
- 🤖 **谷歌免费 Gemini 3.5 模型**：已配置你的 Gemini API Key，自动调用最新 `gemini-3.5-flash-lite` 模型，终身免费，分析透彻。
- 📰 **权威多源实时抓取**：覆盖 CNBC、WSJ、美联储官方、Politico、The Hill、美国国防部 (DoD)、Military Times、Task & Purpose 等主流信源。

---

## 手机与电脑端接收方式

### 方式一：手机安装 ntfy App（最推荐，体验如微信消息）
1. 苹果手机在 **App Store**、安卓手机在应用商店或官网搜索下载：**`ntfy`**（完全免费开源）；
2. 打开 App，点击右上角 `+` 号；
3. 输入你的专属频道名：**`amenews123138`**，点击订阅；
4. **完成！** 每天早上 6 点，手机会像收到新微信一样弹窗震动提醒，点开即可阅读图文内参。

### 方式二：网页端直接阅读（无需安装任何软件）
* 随时在浏览器中打开：[https://ntfy.sh/amenews123138](https://ntfy.sh/amenews123138)
* 可以点击页面上的 **Subscribe (订阅通知)**，电脑浏览器也会在早晨弹出通知。

---

## 本地一键测试运行

项目根目录下的 `.env` 文件已自动配置好你的 Gemini Key 与专属频道名：
```ini
LLM_API_KEY=your_gemini_api_key
NTFY_TOPIC=amenews123138
```

直接在当前目录执行：
```bash
python main.py
```
执行完成后，你的手机 App 或网页端 [https://ntfy.sh/amenews123138](https://ntfy.sh/amenews123138) 就会立即收到推送！

---

## 部署到 GitHub Actions（实现每天早晨 6 点自动关机推送）

1. **新建 GitHub 仓库**：
   - 登录你的 GitHub 账号，右上角点击 `+` ➔ **New repository**；
   - 仓库名称填入 `us-news-daily`；
   - 选择 **Private（私有仓库）**，点击 **Create repository**。

2. **将本地代码推送到 GitHub**：
   在当前目录终端下执行：
   ```bash
   git add .
   git commit -m "feat: complete daily us news to ntfy"
   git branch -M main
   git remote add origin https://github.com/<你的用户名>/us-news-daily.git
   git push -u origin main
   ```

3. **在 GitHub 仓库添加 Secret（仅需 1 个！）**：
   - 进入该 GitHub 仓库，点击顶部 **Settings** ➔ 左侧 **Secrets and variables** ➔ **Actions**；
    - 点击 **New repository secret**：
      - `Name`: `LLM_API_KEY`
      - `Secret`: 填入你的 Gemini Key
    - *（注：频道 `amenews123138` 已在代码中作为默认值，无需额外设置）*

4. **手动点击测试一次**：
   - 进入仓库顶部的 **Actions** 标签页；
   - 点击左侧的 **每日早间美国资讯汇总推送**；
   - 点击右侧的 **Run workflow** 绿色按钮手动触发；
   - 稍等约 20 秒，手机就会收到早报推送！

5. **全自动运行**：
   此后每天北京时间 **06:00（国际时间 UTC 22:00）**，GitHub Actions 云端会自动为你抓取最新全球动态、生成研判并推送。你的个人电脑彻底关机也完全不影响。
