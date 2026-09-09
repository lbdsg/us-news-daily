# 🌍 全自动资讯内参推送系统

本系统包含两个完全独立、并行的全自动资讯内参推送模块，均通过 GitHub Actions 免费云端调度，全程 0 成本运行：

---

## 🛢️ 模块一：原油化工 24 小时双小时核心情报 (全天 12 次 / 专属频道：`yuanyou123456`)

全天 24 小时逢偶数整点（08:00、10:00、12:00、14:00、16:00、18:00、20:00、22:00、00:00、02:00、04:00、06:00）自动抓取：
- 📈 **实时盘面数据**：毫秒级提取国际 WTI 原油、布伦特原油、美天然气、汽油期货最新现价、日内涨跌幅（%）与振幅；
- ⚡ **权威多源情报**：路透/彭博能源动态、OilPrice 全球能源、CNBC Energy、化工工程在线、国内大宗商品/聚酯/聚烯烃开工；
- 🤖 **专业深度研判**：大模型深入剖析地缘溢价（中东/红海）、OPEC+决议、EIA库存、中下游石化裂解利润与短线支撑阻力；
- 🌙 **夜间智能免打扰**：凌晨 00:00~07:00 自动开启静音常驻（`Low Priority`），不吵醒睡眠；早晨醒来通知栏翻看夜盘战报。

### 接收方式：
* **手机端**：在 ntfy App 中添加订阅频道：**`yuanyou123456`**；
* **网页端**：直接在浏览器中打开：[https://ntfy.sh/yuanyou123456](https://ntfy.sh/yuanyou123456)；
* **本地运行测试**：
  ```bash
  python main_oil.py --force
  ```

---

## 🇺🇸 模块二：每日 3 次美国核心内参自动推送系统 (06:00 / 12:00 / 18:00 / 频道：`amenews123138`)

每天在北京时间 **06:00（早间内参）**、**12:00（午间速递）**、**18:00（晚间盘点）** 自动抓取美国最新**宏观经济、政治外交、军事防务**权威资讯，通过谷歌大模型进行深度提炼分析，自动推送到你的专属频道：**`amenews123138`**。

### 接收方式：
* **手机端**：在 ntfy App 中订阅频道：**`amenews123138`**；
* **网页端**：随时在浏览器中打开：[https://ntfy.sh/amenews123138](https://ntfy.sh/amenews123138)；
* **本地运行测试**：
  ```bash
  python main.py --force
  ```

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
