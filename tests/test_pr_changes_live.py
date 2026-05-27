"""在线获取并显示 PR 更改内容.

通过 GitHub API 获取真实的 PR 数据并显示更改统计.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
from src.fetcher import GitHubFetcher
from src.config import get_config


def display_pr_changes(owner: str, repo: str, pr_number: int, token: str = None):
    """获取并显示 PR 更改内容.

    Args:
        owner: 仓库所有者
        repo: 仓库名称
        pr_number: PR 编号
        token: GitHub Token (可选)
    """
    print(f"\n{'=' * 70}")
    print(f"正在获取 PR #{pr_number} 的数据...")
    print(f"{'=' * 70}")

    with GitHubFetcher(token) as fetcher:
        # 获取 PR 数据
        pr_data = fetcher.fetch_pr_data(owner, repo, pr_number)

        # 获取评论
        comments = fetcher.fetch_pr_comments(owner, repo, pr_number)

        # 获取提交记录
        commits = fetcher.fetch_pr_commits(owner, repo, pr_number)

        # 获取事件记录（标签添加等）
        events = fetcher.fetch_pr_events(owner, repo, pr_number)

        print(f"\n📋 PR 基本信息:")
        print(f"   编号: #{pr_data.number}")
        print(f"   标题: {pr_data.title}")
        print(f"   作者: {pr_data.author}")
        print(f"   状态: {'已合并' if pr_data.merged else pr_data.state}")

        print(f"\n📊 更改统计:")
        print(f"   ➕ 添加行数: +{pr_data.additions}")
        print(f"   ➖ 删除行数: -{pr_data.deletions}")
        print(f"   📁 变更文件数: {pr_data.changed_files}")
        print(f"   📝 提交数: {pr_data.commits}")
        print(f"   💬 评论数: {pr_data.comments}")

        print(f"\n📁 分支信息:")
        print(f"   源分支: {pr_data.head_branch}")
        print(f"   目标分支: {pr_data.base_branch}")

        if pr_data.labels:
            print(f"\n🏷️ 当前标签:")
            for label in pr_data.labels:
                print(f"   - {label['name']} (#{label['color']})")

        print(f"\n⏰ 时间信息:")
        print(f"   创建时间: {pr_data.created_at}")
        print(f"   更新时间: {pr_data.updated_at}")
        if pr_data.merged_at:
            print(f"   合并时间: {pr_data.merged_at}")
        if pr_data.closed_at:
            print(f"   关闭时间: {pr_data.closed_at}")

        # 显示提交记录
        print(f"\n📝 提交记录 ({len(commits)} 个):")
        print(f"{'-' * 70}")
        for i, commit in enumerate(commits, 1):
            sha = commit.get('sha', '')
            message = commit.get('message', '').split('\n')[0]  # 只显示第一行
            author = commit.get('author', 'Unknown')
            date = commit.get('date', 'N/A')
            print(f"   {i}. [{sha}] {message}")
            print(f"      作者: {author} | 时间: {date}")
        print(f"{'-' * 70}")

        # 显示标签事件
        label_events = [e for e in events if e.get('event') in ['labeled', 'unlabeled']]
        if label_events:
            print(f"\n🏷️ 标签操作记录 ({len(label_events)} 条):")
            print(f"{'-' * 70}")
            for event in label_events:
                event_type = "添加" if event.get('event') == 'labeled' else "移除"
                label_name = event.get('label', {}).get('name', 'Unknown')
                actor = event.get('actor', 'Unknown')
                created_at = event.get('created_at', 'N/A')
                print(f"   [{event_type}] {label_name}")
                print(f"      操作人: {actor} | 时间: {created_at}")
            print(f"{'-' * 70}")

        # 显示其他重要事件
        other_events = [e for e in events if e.get('event') not in ['labeled', 'unlabeled', 'mentioned', 'subscribed']]
        if other_events:
            print(f"\n📌 其他事件 ({len(other_events)} 条):")
            print(f"{'-' * 70}")
            for event in other_events[:10]:  # 只显示前10条
                event_name = event.get('event', 'Unknown')
                actor = event.get('actor', 'Unknown')
                created_at = event.get('created_at', 'N/A')
                print(f"   [{event_name}] 操作人: {actor} | 时间: {created_at}")
            if len(other_events) > 10:
                print(f"   ... 还有 {len(other_events) - 10} 条事件")
            print(f"{'-' * 70}")

        print(f"\n💬 评论列表 ({len(comments)} 条):")
        for i, comment in enumerate(comments, 1):
            user = comment.get('user', {}).get('login', 'Unknown')
            created_at = comment.get('created_at', 'N/A')
            body_preview = comment.get('body', '')[:100]
            if len(comment.get('body', '')) > 100:
                body_preview += "..."
            print(f"\n   评论 {i}:")
            print(f"     作者: {user}")
            print(f"     时间: {created_at}")
            print(f"     内容: {body_preview}")

        print(f"\n{'=' * 70}")


def main():
    """主函数 - 可以通过命令行参数指定 PR."""
    import argparse

    parser = argparse.ArgumentParser(description='获取并显示 PR 更改内容')
    parser.add_argument('--owner', help='仓库所有者 (默认从配置读取)')
    parser.add_argument('--repo', help='仓库名称 (默认从配置读取)')
    parser.add_argument('--pr', type=int, required=True, help='PR 编号')
    parser.add_argument('--token', help='GitHub Token')

    args = parser.parse_args()

    # 获取配置
    config = get_config()

    # 如果没有提供 token，从配置读取
    token = args.token or config.settings.github_token

    # 如果没有提供 owner/repo，从配置的 default_repo 解析
    owner = args.owner
    repo = args.repo

    if not owner or not repo:
        default_repo = config.settings.default_repo
        if default_repo and '/' in default_repo:
            parts = default_repo.split('/')
            owner = owner or parts[0]
            repo = repo or parts[1]
        else:
            print("错误: 请提供 --owner 和 --repo 参数，或在配置中设置 default_repo")
            return

    display_pr_changes(owner, repo, args.pr, token)


if __name__ == "__main__":
    main()
