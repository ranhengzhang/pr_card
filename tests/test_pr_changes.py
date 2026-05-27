"""测试 PR 更改内容显示.

测试获取和显示 PR 的 additions/deletions/changed_files 等信息.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
from datetime import datetime
from src.fetcher import GitHubFetcher, PRData
from src.renderer import CardRenderer


def test_display_pr_changes():
    """显示获取到的 PR 更改内容."""
    # 创建模拟 PR 数据，包含更改统计
    pr_data = PRData(
        number=123,
        title="[功能] 添加用户认证模块",
        state="merged",
        merged=True,
        draft=False,
        author="developer1",
        author_avatar="https://github.com/developer1.png",
        created_at=datetime(2024, 1, 15, 10, 30, 0),
        updated_at=datetime(2024, 1, 16, 14, 20, 0),
        merged_at=datetime(2024, 1, 16, 14, 20, 0),
        closed_at=None,
        body="## 更改内容\n\n- 添加了用户登录功能\n- 实现了 JWT 认证\n- 更新了数据库模型",
        additions=1250,
        deletions=320,
        changed_files=15,
        commits=8,
        comments=5,
        labels=[
            {"name": "feature", "color": "a2eeef"},
            {"name": "authentication", "color": "d876e3"},
        ],
        html_url="https://github.com/owner/repo/pull/123",
        base_branch="main",
        head_branch="feature/auth-module",
    )

    print("=" * 60)
    print("PR 更改内容统计")
    print("=" * 60)
    print(f"PR 编号: #{pr_data.number}")
    print(f"标题: {pr_data.title}")
    print(f"作者: {pr_data.author}")
    print(f"状态: {'已合并' if pr_data.merged else pr_data.state}")
    print("-" * 60)
    print("📊 更改统计:")
    print(f"   添加行数 (additions): +{pr_data.additions}")
    print(f"   删除行数 (deletions): -{pr_data.deletions}")
    print(f"   变更文件数 (changed_files): {pr_data.changed_files}")
    print(f"   提交数 (commits): {pr_data.commits}")
    print(f"   评论数 (comments): {pr_data.comments}")
    print("-" * 60)
    print("📁 分支信息:")
    print(f"   源分支: {pr_data.head_branch}")
    print(f"   目标分支: {pr_data.base_branch}")
    print("-" * 60)
    print("🏷️ 标签:")
    for label in pr_data.labels:
        print(f"   - {label['name']} (#{label['color']})")
    print("=" * 60)

    # 模拟提交记录
    commits = [
        {"sha": "abc1234", "message": "添加用户认证基础框架", "author": "developer1", "author_avatar": "https://github.com/developer1.png", "date": "2024-01-15T10:30:00"},
        {"sha": "def5678", "message": "实现 JWT token 生成和验证", "author": "developer1", "author_avatar": "https://github.com/developer1.png", "date": "2024-01-15T11:45:00"},
        {"sha": "ghi9012", "message": "添加数据库用户表迁移", "author": "developer2", "author_avatar": "https://github.com/developer2.png", "date": "2024-01-15T14:20:00"},
        {"sha": "jkl3456", "message": "实现登录 API 接口", "author": "developer1", "author_avatar": "https://github.com/developer1.png", "date": "2024-01-16T09:15:00"},
        {"sha": "mno7890", "message": "添加单元测试", "author": "developer3", "author_avatar": "https://github.com/developer3.png", "date": "2024-01-16T11:30:00"},
    ]

    # 显示提交记录
    print("\n📦 提交记录:")
    print("-" * 60)
    for commit in commits:
        print(f"\n  🔹 {commit['sha']}")
        print(f"     作者: {commit['author']}")
        print(f"     头像: {commit['author_avatar']}")
        print(f"     时间: {commit['date']}")
        print(f"     消息: {commit['message']}")
    print("\n" + "=" * 60)

    # 测试渲染器生成时间线事件
    print("\n📅 时间线事件:")
    print("-" * 60)

    renderer = CardRenderer()
    comments = []
    timeline_events = renderer._generate_timeline_events(pr_data, comments, commits)

    for i, event in enumerate(timeline_events, 1):
        print(f"\n事件 {i}:")
        print(f"  类型: {event['type']}")
        print(f"  标题: {event['title']}")
        print(f"  时间: {event['date']}")
        print(f"  描述: {event['description']}")
        print(f"  图标: {event['icon']}")
        print(f"  样式类: {event['icon_class']}")
        if event.get('author_avatar'):
            print(f"  头像: {event['author_avatar']}")

    print("\n" + "=" * 60)


def test_fetch_real_pr_commits():
    """从网络拉取真实 PR 的提交信息."""
    # 配置：替换为你要测试的 PR
    OWNER = "amll-dev"  # 仓库所有者
    REPO = "amll-ttml-db"      # 仓库名称
    PR_NUMBER = 8754        # PR 编号

    print("\n" + "=" * 60)
    print(f"从网络拉取 PR #{PR_NUMBER} 的实际提交信息")
    print(f"仓库: {OWNER}/{REPO}")
    print("=" * 60)

    try:
        fetcher = GitHubFetcher()

        # 获取 PR 基本信息
        print("\n📋 正在获取 PR 基本信息...")
        pr_data = fetcher.fetch_pr_data(OWNER, REPO, PR_NUMBER)

        print(f"\nPR 编号: #{pr_data.number}")
        print(f"标题: {pr_data.title}")
        print(f"作者: {pr_data.author}")
        print(f"状态: {'已合并' if pr_data.merged else pr_data.state}")
        print(f"提交数: {pr_data.commits}")

        # 获取提交记录
        print(f"\n📦 正在获取提交记录...")
        commits = fetcher.fetch_pr_commits(OWNER, REPO, PR_NUMBER)

        print(f"\n共 {len(commits)} 条提交:")
        print("-" * 60)
        for commit in commits:
            print(f"\n  🔹 {commit['sha']}")
            print(f"     作者: {commit['author']}")
            print(f"     头像: {commit['author_avatar']}")
            print(f"     时间: {commit['date']}")
            print(f"     消息: {commit['message'][:80]}{'...' if len(commit['message']) > 80 else ''}")

        # 获取事件记录
        print(f"\n📋 正在获取事件记录...")
        events = fetcher.fetch_pr_events(OWNER, REPO, PR_NUMBER)

        print(f"\n共 {len(events)} 条事件:")
        print("-" * 60)
        for event in events:
            print(f"\n  📌 {event['event']}")
            print(f"     操作者: {event['actor']}")
            print(f"     头像: {event['actor_avatar']}")
            print(f"     时间: {event['created_at']}")
            if event.get('label'):
                print(f"     标签: {event['label']['name']}")

        # 生成时间线
        print(f"\n📅 生成时间线事件...")
        renderer = CardRenderer()
        comments = fetcher.fetch_pr_comments(OWNER, REPO, PR_NUMBER)
        timeline_events = renderer._generate_timeline_events(pr_data, comments, commits, events)

        print(f"\n共 {len(timeline_events)} 个时间线事件:")
        print("-" * 60)
        for i, event in enumerate(timeline_events, 1):
            print(f"\n  事件 {i}: [{event['type']}] {event['title']}")
            print(f"     时间: {event['date']}")
            if event.get('description'):
                print(f"     描述: {event['description'][:60]}{'...' if len(event['description']) > 60 else ''}")
            if event.get('author_avatar'):
                print(f"     头像: {event['author_avatar']}")

        print("\n" + "=" * 60)

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        print("\n提示: 如果需要访问私有仓库，请设置 GITHUB_TOKEN 环境变量")
        print("      export GITHUB_TOKEN=your_token_here")


def test_closed_pr_changes():
    """测试已关闭但未合并的 PR."""
    pr_data = PRData(
        number=456,
        title="[废弃] 实验性功能",
        state="closed",
        merged=False,
        draft=False,
        author="developer2",
        author_avatar="https://github.com/developer2.png",
        created_at=datetime(2024, 1, 10, 9, 0, 0),
        updated_at=datetime(2024, 1, 12, 16, 30, 0),
        merged_at=None,
        closed_at=datetime(2024, 1, 12, 16, 30, 0),
        body="此 PR 已被废弃，不再继续开发。",
        additions=150,
        deletions=80,
        changed_files=5,
        commits=3,
        comments=2,
        labels=[
            {"name": "wontfix", "color": "ffffff"},
        ],
        html_url="https://github.com/owner/repo/pull/456",
        base_branch="main",
        head_branch="feature/experimental",
    )

    print("\n" + "=" * 60)
    print("已关闭 PR 更改内容统计")
    print("=" * 60)
    print(f"PR 编号: #{pr_data.number}")
    print(f"标题: {pr_data.title}")
    print(f"状态: 已关闭 (未合并)")
    print("-" * 60)
    print("📊 更改统计:")
    print(f"   添加行数: +{pr_data.additions}")
    print(f"   删除行数: -{pr_data.deletions}")
    print(f"   变更文件数: {pr_data.changed_files}")
    print("=" * 60)

    renderer = CardRenderer()
    timeline_events = renderer._generate_timeline_events(pr_data, [])

    print("\n📅 时间线事件:")
    for event in timeline_events:
        print(f"  - [{event['type']}] {event['title']}")


if __name__ == "__main__":
    # 运行模拟数据测试
    # test_display_pr_changes()
    # test_closed_pr_changes()

    # 运行真实网络测试（取消注释以执行）
    test_fetch_real_pr_commits()
