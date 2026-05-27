"""测试浏览器渲染问题."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.fetcher import GitHubFetcher
from src.renderer import CardRenderer
from src.config import get_config


def main():
    """测试渲染."""
    config = get_config()
    token = config.settings.github_token

    print("=" * 60)
    print("PR #9507 浏览器渲染测试")
    print("=" * 60)

    with GitHubFetcher(token) as fetcher:
        try:
            pr_data = fetcher.fetch_pr_data('amll-dev', 'amll-ttml-db', 9507)

            # 渲染卡片
            renderer = CardRenderer()
            html = renderer.render(pr_data, style="github")

            # 保存 HTML 文件
            output_file = Path("test_browser_render.html")
            output_file.write_text(html, encoding='utf-8')

            print(f"\n✅ HTML 已保存: {output_file.absolute()}")

            # 提取描述部分
            import re
            body_match = re.search(
                r'<div class="pr-body markdown-body" id="pr-description">(.*?)</div>',
                html,
                re.DOTALL
            )

            if body_match:
                raw_md = body_match.group(1)
                # HTML 解码
                import html
                decoded = html.unescape(raw_md)
                print(f"\n🔍 传给浏览器的原始 Markdown (前 500 字符):")
                print("-" * 60)
                print(decoded[:500])
                print("-" * 60)

            print("\n💡 请用浏览器打开 test_browser_render.html 查看实际效果")
            print("=" * 60)

        except Exception as e:
            print(f"❌ 错误: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()
