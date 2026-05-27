"""测试 PR #9507 的渲染结果."""

import asyncio
import sys
from pathlib import Path

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.fetcher import GitHubFetcher
from src.renderer import CardRenderer
from src.config import get_config


def main():
    """主函数."""
    config = get_config()
    token = config.settings.github_token

    print("=" * 60)
    print("PR #9507 渲染测试")
    print("=" * 60)

    with GitHubFetcher(token) as fetcher:
        try:
            pr_data = fetcher.fetch_pr_data('amll-dev', 'amll-ttml-db', 9507)

            print(f"\n📋 PR 标题: {pr_data.title}")
            print(f"📝 描述长度: {len(pr_data.body) if pr_data.body else 0} 字符")

            # 渲染卡片
            renderer = CardRenderer()
            html = renderer.render(pr_data, style="github")

            # 查找描述部分的 HTML
            import re

            # 提取 pr-body 部分
            body_match = re.search(
                r'<div class="pr-body markdown-body">(.*?)</div>',
                html,
                re.DOTALL
            )

            if body_match:
                body_html = body_match.group(1).strip()
                print(f"\n🔍 渲染后的描述 HTML (前 2000 字符):")
                print("-" * 60)
                print(body_html[:2000])
                print("-" * 60)

                # 检查是否包含表格标签
                has_table = "<table>" in body_html
                has_td = "<td" in body_html
                has_th = "<th" in body_html

                print(f"\n✅ 检查结果:")
                print(f"  包含 <table>: {has_table}")
                print(f"  包含 <td>: {has_td}")
                print(f"  包含 <th>: {has_th}")

                if not has_table:
                    print("\n⚠️ 警告: 表格没有被正确渲染!")
                    print("\n原始描述内容:")
                    print(pr_data.body[:1000] if pr_data.body else "(空)")
            else:
                print("❌ 未找到 pr-body 部分")

            # 保存完整 HTML 到文件以便查看
            output_file = Path("test_render_output.html")
            output_file.write_text(html, encoding='utf-8')
            print(f"\n💾 完整 HTML 已保存到: {output_file.absolute()}")

            print("\n" + "=" * 60)

        except Exception as e:
            print(f"❌ 错误: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()
