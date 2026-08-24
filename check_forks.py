import os
import requests
from datetime import datetime, timezone, timedelta

# 环境变量读取
GH_TOKEN = os.environ.get('GH_TOKEN')
WECHAT_WEBHOOK = os.environ.get('WECHAT_WEBHOOK')
EXCLUDE_REPOS = [r.strip() for r in os.environ.get('EXCLUDE_REPOS', '').split(',') if r.strip()]

GH_HEADERS = {
    'Authorization': f'token {GH_TOKEN}',
    'Accept': 'application/vnd.github.v3+json'
}

def send_wechat_msg(content):
    if not WECHAT_WEBHOOK:
        print("[错误] 未配置 WECHAT_WEBHOOK 环境变量！")
        return
    # 使用 text 纯文本类型，实现个人微信原生无缝显示
    payload = {
        "msgtype": "text",
        "text": {
            "content": content
        }
    }
    try:
        resp = requests.post(WECHAT_WEBHOOK, json=payload).json()
        print(f"[调试] Webhook 推送结果: {resp}")
    except Exception as e:
        print(f"[异常] 推送消息报错: {e}")

def main():
    # 1. 获取当前用户
    user_info = requests.get('https://api.github.com/user', headers=GH_HEADERS).json()
    username = user_info['login']

    # 2. 获取所有仓库并筛选 Fork
    repos_url = f"https://api.github.com/user/repos?type=owner&per_page=200"
    repos = requests.get(repos_url, headers=GH_HEADERS).json()
    forks = [r for r in repos if r.get('fork')]

    if not forks:
        print("没有找到任何 Fork 的仓库。")
        return

    now_str = datetime.now(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S')
    msg_lines = [
        "【GitHub Forks 状态汇报】",
        f"统计时间: {now_str}",
        "----------------------"
    ]

    # 3. 检查每个 Fork 的状态
    for fork in forks:
        repo_name = fork['name']
        default_branch = fork['default_branch']
        updated_at = fork['updated_at'][:10]
        
        repo_detail = requests.get(fork['url'], headers=GH_HEADERS).json()
        parent = repo_detail.get('parent')
        if not parent:
            continue
            
        parent_owner = parent['owner']['login']
        parent_branch = parent['default_branch']

        # 比对进度
        compare_url = f"https://api.github.com/repos/{username}/{repo_name}/compare/{username}:{default_branch}...{parent_owner}:{parent_branch}"
        compare_res = requests.get(compare_url, headers=GH_HEADERS).json()
        behind_by = compare_res.get('ahead_by', 0)
        
        if behind_by > 0:
            if repo_name in EXCLUDE_REPOS:
                status = f"🔴 落后 {behind_by} 个提交 (免自动同步)"
            else:
                sync_url = f"https://api.github.com/repos/{username}/{repo_name}/merge-upstream"
                sync_payload = {"branch": default_branch}
                sync_res = requests.post(sync_url, headers=GH_HEADERS, json=sync_payload)

                if sync_res.status_code == 200:
                    status = f"🟢 自动同步成功 (原落后 {behind_by} 个提交)"
                elif sync_res.status_code == 409:
                    status = f"❌ 同步失败：存在代码冲突"
                else:
                    status = f"⚠️ 同步请求异常: 状态码 {sync_res.status_code}"
        else:
            status = "🟢 已是最新"

        msg_lines.append(f"• {repo_name}: {status}\n  更新于 {updated_at}\n  链接: {fork['html_url']}")

    # 4. 发送纯文本 Webhook 通知
    send_wechat_msg("\n\n".join(msg_lines))

if __name__ == "__main__":
    main()
