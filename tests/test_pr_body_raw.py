"""显示 PR #9507 的原始 body 内容."""

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
    print("PR #9507 原始 body 内容")
    print("=" * 60)

    with GitHubFetcher(token) as fetcher:
        try:
            pr_data = fetcher.fetch_pr_data('amll-dev', 'amll-ttml-db', 9507)

            if pr_data.body:
                print("\n原始内容 (repr):")
                print(repr(pr_data.body))

                print("\n" + "=" * 60)
                print("\n逐字符分析表格部分:")

                # 查找表格开始位置
                table_start = pr_data.body.find("| *key*")
                if table_start != -1:
                    # 显示表格前后 50 个字符
                    start = max(0, table_start - 50)
                    end = min(len(pr_data.body), table_start + 500)
                    snippet = pr_data.body[start:end]

                    print(f"\n上下文片段 (位置 {start}-{end}):")
                    print(repr(snippet))

                    print("\n逐行显示:")
                    for i, line in enumerate(snippet.split('\n')):
                        print(f"  行{i}: {repr(line)}")
            else:
                print("(无描述)")

            print("\n" + "=" * 60)

        except Exception as e:
            print(f"❌ 错误: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()
