# 定时推送设置

GitHub 自带的 `schedule` 对此仓库**不会自动运行**（Actions 里只有手动记录、没有 schedule 记录）。
请用 **cron-job.org**（免费）每天准时触发 workflow。

## 1. 创建 GitHub Token

1. 打开 https://github.com/settings/tokens?type=beta
2. **Generate new token** → Fine-grained token
3. Repository access：只选 **ai-daily-news**
4. Permissions → **Actions: Read and write**
5. 生成后复制 token（只显示一次）

## 2. 注册 cron-job.org

1. 打开 https://console.cron-job.org/signup 注册并登录
2. **Cronjobs** → **Create cronjob**

## 3. 填写定时任务

| 项 | 值 |
|---|---|
| Title | AI Daily News |
| URL | `https://api.github.com/repos/xxsiyu/ai-daily-news/actions/workflows/daily_ai.yml/dispatches` |
| Schedule | 每天 **20:00**，时区 **Asia/Shanghai** |
| Request method | **POST** |

**Request headers**（Add header 各加一条）：

```
Authorization: Bearer 你的GitHub_Token
Accept: application/vnd.github+json
X-GitHub-Api-Version: 2022-11-28
Content-Type: application/json
```

**Request body**：

```json
{"ref":"main"}
```

保存后点 **Run now** 测试。若 GitHub Actions 出现新运行且邮箱收到邮件，即配置成功。

## 4. 手动触发（备用）

仓库 → **Actions** → **Daily AI News** → **Run workflow**
