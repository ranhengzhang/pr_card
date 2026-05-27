"""调试 Vue 模板渲染."""

import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from src.fetcher import GitHubFetcher
from src.renderer import CardRenderer
from src.config import get_config

# 获取配置
config = get_config()
token = config.settings.github_token

# 获取 PR 数据
with GitHubFetcher(token) as fetcher:
    pr_data = fetcher.fetch_pr_data("Steve-xmh", "amll-ttml-db", 9507)
    comments = fetcher.fetch_pr_comments("Steve-xmh", "amll-ttml-db", 9507)

print(f"PR 标题: {pr_data.title}")
print(f"PR 编号: {pr_data.number}")
print(f"评论数: {len(comments)}")

# 渲染 HTML
renderer = CardRenderer()
html_content = renderer.render(pr_data, use_vue_template=True, comments=comments)

# 保存 HTML 文件以便检查
output_path = Path("test_vue_output.html")
output_path.write_text(html_content, encoding='utf-8')
print(f"HTML 已保存到: {output_path}")

# 检查第 9259 个字符附近的内容
if len(html_content) > 9260:
    print(f"\n位置 9259 附近的字符:")
    print(repr(html_content[9250:9270]))
