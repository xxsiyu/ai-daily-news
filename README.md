# AI 每日简报

每天自动抓取 AI 资讯，发送 HTML 邮件到你的邮箱。

- 仓库地址：https://github.com/xxsiyu/ai-daily-news
- 默认推送时间：**每天 20:00（北京时间）**
- 每次约 **10 条**资讯

---

## 工作原理

```
cron-job.org（定时） → GitHub Actions → daily_ai_news.py → QQ 邮箱
```

1. **cron-job.org** 每天 20:00 调用 GitHub API，触发 Actions
2. **GitHub Actions** 在云端运行脚本，抓取 RSS 并发送邮件
3. 不依赖你的电脑是否开机、是否联网

> **注意：** 本仓库不使用 GitHub 内置 `schedule` 定时（实测对此仓库不会自动触发）。请使用 **cron-job.org** 作为外部定时器。

---

## 一、GitHub Secrets（邮箱配置）

首次部署或更换邮箱时，在仓库中配置 Secrets：

**路径：** 仓库 → **Settings** → **Secrets and variables** → **Actions** → **Repository secrets**

| Secret 名称 | 说明 | 示例 |
|---|---|---|
| `SENDER_EMAIL` | 发件 QQ 邮箱 | `yourname@qq.com` |
| `SMTP_PASSWORD` | QQ 邮箱 **SMTP 授权码**（不是登录密码） | 16 位授权码 |
| `RECEIVER_EMAIL` | 收件邮箱（可与发件相同） | `yourname@qq.com` |

### QQ 邮箱授权码获取

1. 登录 [QQ 邮箱](https://mail.qq.com)
2. **设置** → **账户** → **POP3/IMAP/SMTP/Exchange/CardDAV/CalDAV 服务**
3. 开启 **POP3/SMTP 服务**
4. 按提示生成 **授权码**，填入 `SMTP_PASSWORD`

---

## 二、cron-job.org 定时配置（重要）

当 cron-job.org 账号到期、任务被删、或需要在新设备上重新配置时，按本节操作即可，**无需查看聊天记录**。

### 步骤 1：创建 GitHub Token（推荐 Classic，更稳）

Fine-grained token 在 cron-job.org 上容易报 403，建议直接用 **Classic token**：

1. 打开 https://github.com/settings/tokens
2. 点 **Generate new token (classic)**
3. Note 随便填，例如 `ai-daily-news-cron`
4. Expiration 可选 `90 days` 或 `No expiration`
5. 勾选权限：**`repo`** 和 **`workflow`**
6. 生成后复制 Token（以 `ghp_` 开头）

> 不要把 Token 发给任何人；泄露后立刻 Revoke。

若坚持用 Fine-grained token，至少要：

- Repository access：只选 **ai-daily-news**
- Permissions → **Actions: Read and write**
- Permissions → **Contents: Read and write**

### 步骤 2：注册 / 登录 cron-job.org

1. 打开 https://console.cron-job.org
2. 注册或登录账号

### 步骤 3：创建定时任务

**Cronjobs** → **Create cronjob**，填写以下内容：

#### 基本信息

| 项 | 填写内容 |
|---|---|
| **Title** | `AI Daily News` |
| **URL** | `https://api.github.com/repos/xxsiyu/ai-daily-news/actions/workflows/daily_ai.yml/dispatches` |
| **Schedule** | 每天 **20:00** |
| **Timezone** | **Asia/Shanghai** |

#### ADVANCED（高级设置）

| 项 | 填写内容 |
|---|---|
| **Request method** | `POST` |
| **Requires HTTP authentication** | **不要勾选 / 留空** |

#### Request headers（点 Add header，逐条添加 **5** 条）

| Header 名称 | Header 值 |
|---|---|
| `User-Agent` | `ai-daily-news` |
| `Authorization` | `Bearer 你的Token` |
| `Accept` | `application/vnd.github+json` |
| `X-GitHub-Api-Version` | `2022-11-28` |
| `Content-Type` | `application/json` |

> **必填 `User-Agent`：** 没有它 GitHub 会直接 403。  
> `Authorization` 格式：`Bearer` + 空格 + Token（Classic 是 `ghp_...`，Fine-grained 是 `github_pat_...`）。  
> **Requires HTTP authentication** 不要勾选。

#### Request body

```json
{"ref":"main"}
```

### 步骤 4：测试

1. 保存任务
2. 点击 **Run now**
3. 成功时状态码通常是 **204**
4. 打开 https://github.com/xxsiyu/ai-daily-news/actions 应出现新运行
5. 检查 QQ 邮箱是否收到简报

### 备用方案：改用 repository_dispatch

若上面 URL 仍 Forbidden，把 cron-job 改成：

| 项 | 填写内容 |
|---|---|
| **URL** | `https://api.github.com/repos/xxsiyu/ai-daily-news/dispatches` |
| **Request body** | `{"event_type":"daily-news"}` |

Headers 仍用上面那 5 条不变。

### 本地自检 Token（可选）

在 PowerShell 中运行（把 `粘贴你的Token` 换成真实 Token，测完可关掉窗口）：

```powershell
$token = "粘贴你的Token"
$headers = @{
  "Authorization" = "Bearer $token"
  "Accept" = "application/vnd.github+json"
  "X-GitHub-Api-Version" = "2022-11-28"
  "User-Agent" = "ai-daily-news"
}
Invoke-RestMethod -Method POST `
  -Uri "https://api.github.com/repos/xxsiyu/ai-daily-news/actions/workflows/daily_ai.yml/dispatches" `
  -Headers $headers `
  -ContentType "application/json" `
  -Body '{"ref":"main"}'
```

- 无报错 + Actions 有新运行 → Token 正常，问题在 cron-job.org 配置
- 仍 401/403 → Token 权限不够或已失效，重新生成 Classic token

---

## 三、手动触发（备用）

不依赖 cron-job.org，可随时手动发一封：

1. 打开 https://github.com/xxsiyu/ai-daily-news/actions
2. 左侧选择 **Daily AI News**
3. 点击 **Run workflow** → **Run workflow**

---

## 四、本地运行（可选）

```powershell
cd ai资讯
pip install -r requirements.txt
copy config.example.json config.json
# 编辑 config.json，填写邮箱和授权码
python daily_ai_news.py
```

本地运行会生成本地 HTML 简报（`output/` 目录），并尝试打开浏览器。

---

## 常见问题

### cron-job.org 报 Forbidden / 403？

按下面顺序排查：

1. **换 Classic Token**（最有效）  
   https://github.com/settings/tokens → **Generate new token (classic)** → 勾选 **`repo` + `workflow`**  
   然后把 Header 里的 `Authorization` 改成：`Bearer ghp_你的新Token`

2. **确认有 `User-Agent: ai-daily-news`**

3. **Requires HTTP authentication 不要勾选**

4. **改用备用 URL / Body：**
   - URL：`https://api.github.com/repos/xxsiyu/ai-daily-news/dispatches`
   - Body：`{"event_type":"daily-news"}`

5. **用 README「本地自检 Token」验证**  
   - 本地成功、cron 失败 → 检查 cron 的 Header/Body 是否抄错  
   - 本地也 403 → Token 权限问题

成功时 cron-job.org 通常显示 **204**。

### 没收到邮件？

1. 看 [Actions 运行记录](https://github.com/xxsiyu/ai-daily-news/actions) 是否成功（绿色 ✓）
2. 检查 QQ 邮箱 **垃圾箱**
3. 确认 Secrets 中 `SMTP_PASSWORD` 是 **授权码**，不是 QQ 登录密码
4. 确认 cron-job.org 任务状态为 **启用**，且 **Run now** 能触发 Actions

### cron-job.org 到期后怎么办？

1. 重新注册 / 续期 cron-job.org
2. 按本文 **「二、cron-job.org 定时配置」** 重新创建任务
3. 若 GitHub Token 已过期，在 https://github.com/settings/tokens 重新生成，并更新 Header 中的 `Authorization`

### Token 泄露了怎么办？

1. 立即到 https://github.com/settings/tokens **删除（Revoke）** 该 Token
2. 重新生成新 Token
3. 在 cron-job.org 中更新 `Authorization` Header

### 为什么不用 GitHub 自带 schedule？

本仓库实测 GitHub 内置 `schedule` 定时**从未自动触发**（Actions 里只有手动记录）。因此改用 cron-job.org 外部定时，更稳定可靠。

---

## 资讯来源

- Hacker News (AI)
- 量子位
- Google AI Blog
- OpenAI Blog
- 36氪（AI 相关）
- Solidot（AI 相关）

---

## 文件说明

| 文件 | 说明 |
|---|---|
| `daily_ai_news.py` | 主脚本：抓取 RSS、生成 HTML、发送邮件 |
| `.github/workflows/daily_ai.yml` | GitHub Actions 工作流 |
| `config.example.json` | 本地运行配置模板 |
| `requirements.txt` | Python 依赖 |
