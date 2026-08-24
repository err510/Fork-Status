# 🔄 Fork Status Notifier & Auto Sync

基于 GitHub Actions 与 Python 实现的 Fork 仓库状态监控与自动同步工具。每天晚上 19:00（北京时间）自动检查名下的所有 Fork 仓库，比对上游更新，自动拉取同步并推送纯文本汇总通知至企业微信。

---

## ✨ 功能特性

- ⏰ **定时自动化**：每天晚上 19:00 (UTC 11:00) 自动触发，无须人工干预。
- 🔄 **自动同步上游**：检测到上游有新 Commit 时，通过 GitHub API 自动将上游主分支合并至 Fork。
- 📱 **微信无缝通知**：基于企业微信群机器人 Webhook 推送纯文本消息，直接在个人微信内完美展示，无需跳转企业微信。
- 🔕 **双向独立排除名单**（解耦控制）：
  - **免状态通知**：排除特定仓库的微信消息提醒（后台仍正常自动同步）。
  - **免自动同步**：排除特定仓库的自动合并（微信中仅提醒落后提交数，不自动改动代码）。
  - **完全忽略**：同时写入两份名单即可实现既不推送也不同步。

---

## 🛠️ 配置说明

### 1. GitHub Repository Secrets

在 GitHub 仓库 **Settings** -> **Secrets and variables** -> **Actions** 中添加以下密钥：

| Secret 名称 | 必填 | 说明 |
| :--- | :--- | :--- |
| `GH_TOKEN` | **是** | 个人访问令牌 (Personal Access Token - Classic)，需勾选 `repo` 权限 |
| `WECHAT_WEBHOOK` | **是** | 企业微信群机器人的 Webhook 完整地址 |

**如何获得企业微信群机器人的 Webhook 完整地址？** 
1. 在企业微信中新建一个只有你自己的群（或任意内部群）。
2. 点击群右上角 ... > 消息推送 > 添加机器人。
3. 任意命名（如：fork仓库状态通知），点击创建。
复制生成的 Webhook 地址（格式形如 https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxxxxx）。

### 2. Workflow 环境变量配置

在 `.github/workflows/notify.yml` 文件中可配置以下环境变量控制排除规则：

| 环境变量名称 | 格式 | 示例 | 说明 |
| :--- | :--- | :--- | :--- |
| `EXCLUDE_STATUS_REPOS` | 逗号分隔的仓库名 | `'repo-a,repo-b'` | 填入**不需要发送微信提醒**的 Fork 仓库名称 |
| `EXCLUDE_SYNC_REPOS` | 逗号分隔的仓库名 | `'fork-SullyOS,repo-c'` | 填入**不需要自动同步**的 Fork 仓库名称 |

---

## 📂 项目结构

```text
.
├── .github/
│   └── workflows/
│       └── notify.yml    # GitHub Actions 定时任务配置
├── check_forks.py        # 核心检查与同步 Python 脚本
└── README.md             # 项目说明文档

