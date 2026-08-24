import os
import requests
from datetime import datetime, timezone, timedelta

# 环境变量读取
GH_TOKEN = os.environ.get('GH_TOKEN')
CORPID = os.environ.get('CORPID')
CORPSECRET = os.environ.get('CORPSECRET')
AGENTID = os.environ.get('AGENTID')
# 解析排除名单（忽略空格）
EXCLUDE_REPOS = [r.strip() for r in os.environ.get('EXCLUDE_REPOS', '').split(',') if r.strip()]

GH_HEADERS = {
    'Authorization': f'token {GH_TOKEN}',
    'Accept': 'application/vnd.github.v3+json'
}

def get_wechat_token():
    url = f"https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={CORPID}&corpsecret={CORPSECRET}"
    resp = requests.get(url).json()
    return resp.get('access_token')

def send_wechat_msg(token, content):
    url = f"https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={token}"
    payload = {
        "touser": "@all",
        "msgtype": "markdown",
        "agentid": int(AGENTID),
        "markdown": {"content": content}
    }
    requests.post(url, json=payload)

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

    msg_lines = ["**GitHub Forks 状态汇报**", f"> 统计时间: {datetime.now(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S')}\n"]

    # 3. 检查每个 Fork 的状态
    for fork in forks:
        repo_name = fork['name']
        default_branch = fork['default_branch']
        updated_at = fork['updated_at'][:10]
        
        # 获取父仓库信息
        repo_detail = requests.get(fork['url'], headers=GH_HEADERS).json()
        parent = repo_detail.get('parent')
        if not parent:
            continue
            
        parent_owner = parent['owner']['login']
        parent_branch = parent['default_branch']

        # 比对进度 (Fork 的主分支 vs 上游的主分支)
        compare_url = f"https://api.github.com/repos/{username}/{repo_name}/compare/{username}:{default_branch}...{parent_owner}:{parent_branch}"
        compare_res = requests.get(compare_url, headers=GH_HEADERS).json()
        
        # ahead_by 表示上游领先 Fork 多少个 commit（即 Fork 落后多少）
        behind_by = compare_res.get('ahead_by', 0)
        
        if behind_by > 0:
            if repo_name in EXCLUDE_REPOS:
                # 在排除名单中，仅提醒
                status = f"<font color=\"warning\">🔴 落后 {behind_by} 个提交 (已设置免同步)</font>"
            else:
                # 不在排除名单中，执行自动同步
                sync_url = f"https://api.github.com/repos/{username}/{repo_name}/merge-upstream"
                sync_payload = {"branch": default_branch}
                sync_res = requests.post(sync_url, headers=GH_HEADERS, json=sync_payload)

            if sync_res.status_code == 200:
                    status = f"<font color=\"info\">🟢 自动同步成功 (原落后 {behind_by} 个提交)</font>"
                elif sync_res.status_code == 409:
                    status = f"<font color=\"warning\">❌ 同步失败：存在代码冲突，需手动解决</font>"
                else:
                    status = f"<font color=\"comment\">⚠️ 同步请求异常: 状态码 {sync_res.status_code}</font>"
        else:
            status = "<font color=\"info\">🟢 已是最新</font>"

        msg_lines.append(f"- [{repo_name}]({fork['html_url']}): 最后更新 `{updated_at}`, {status}")

    # 4. 发送企业微信通知
    wx_token = get_wechat_token()
    if wx_token:
        send_wechat_msg(wx_token, "\n".join(msg_lines))
        print("消息推送成功！")
    else:
        print("获取企业微信 Token 失败！")

if __name__ == "__main__":
    main()
