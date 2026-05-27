"""显示 PR #9507 的详细内容."""

import asyncio
import sys
from pathlib import Path

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.fetcher import GitHubFetcher
from src.config import get_config


def main():
    """主函数."""
    config = get_config()
    token = config.settings.github_token

    print("=" * 60)
    print("PR #9507 详细数据")
    print("=" * 60)

    with GitHubFetcher(token) as fetcher:
        try:
            pr_data = fetcher.fetch_pr_data('amll-dev', 'amll-ttml-db', 9507)

            print(f"\n📋 基本信息:")
            print(f"  编号: #{pr_data.number}")
            print(f"  标题: {pr_data.title}")
            print(f"  作者: {pr_data.author}")
            print(f"  状态: {pr_data.state}")
            print(f"  已合并: {pr_data.merged}")
            print(f"  草稿: {pr_data.draft}")

            print(f"\n📊 统计信息:")
            print(f"  添加行数: +{pr_data.additions}")
            print(f"  删除行数: -{pr_data.deletions}")
            print(f"  变更文件: {pr_data.changed_files}")
            print(f"  提交数: {pr_data.commits}")
            print(f"  评论数: {pr_data.comments}")

            print(f"\n🏷️ 标签:")
            if pr_data.labels:
                for label in pr_data.labels:
                    print(f"  - {label}")
            else:
                print("  (无标签)")

            print(f"\n🌿 分支信息:")
            print(f"  源分支: {pr_data.head_branch}")
            print(f"  目标分支: {pr_data.base_branch}")

            print(f"\n📝 描述内容:")
            if pr_data.body:
                body_preview = pr_data.body[:500] + "..." if len(pr_data.body) > 500 else pr_data.body
                print(f"  长度: {len(pr_data.body)} 字符")
                print(f"  内容预览:\n{body_preview}")
            else:
                print("  (无描述)")

            print(f"\n🔗 链接:")
            print(f"  URL: {pr_data.html_url}")
            print(f"  头像: {pr_data.author_avatar}")

            print(f"\n📅 时间:")
            print(f"  创建: {pr_data.created_at}")
            print(f"  更新: {pr_data.updated_at}")
            if pr_data.merged_at:
                print(f"  合并: {pr_data.merged_at}")

            print("\n" + "=" * 60)

        except Exception as e:
            print(f"❌ 错误: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()
