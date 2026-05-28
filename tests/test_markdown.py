"""Markdown 处理模块测试.

测试 markdown_to_text 函数的各种转换场景.
"""

from tests.common import AsyncTestCase
from src.markdown_utils import markdown_to_text


class TestMarkdownToText(AsyncTestCase):
    """markdown_to_text 函数测试."""

    def test_empty_input(self) -> None:
        """测试空输入."""
        self.assertEqual(markdown_to_text(None), "")
        self.assertEqual(markdown_to_text(""), "")

    def test_plain_text(self) -> None:
        """测试纯文本不修改."""
        text = "Hello world"
        self.assertEqual(markdown_to_text(text), "Hello world")

    def test_remove_code_blocks(self) -> None:
        """测试移除代码块."""
        md = "Some text\n```python\nprint('hello')\n```\nMore text"
        result = markdown_to_text(md)
        self.assertNotIn("```", result)
        self.assertNotIn("print", result)
        self.assertIn("Some text", result)
        self.assertIn("More text", result)

    def test_remove_inline_code(self) -> None:
        """测试移除行内代码保留内容."""
        md = "Use `function()` to call"
        result = markdown_to_text(md)
        self.assertEqual(result, "Use function() to call")

    def test_remove_bold_italic(self) -> None:
        """测试移除粗体和斜体标记."""
        md = "**bold** and *italic* and __underline__"
        result = markdown_to_text(md)
        self.assertEqual(result, "bold and italic and underline")

    def test_remove_links(self) -> None:
        """测试移除链接保留文本."""
        md = "Check [this link](http://example.com) here"
        result = markdown_to_text(md)
        self.assertEqual(result, "Check this link here")

    def test_remove_images(self) -> None:
        """测试移除图片."""
        md = "Text ![alt](image.png) more"
        result = markdown_to_text(md)
        self.assertEqual(result, "Text  more")

    def test_remove_html_tags(self) -> None:
        """测试移除 HTML 标签."""
        md = "Text <br/> more <b>bold</b>"
        result = markdown_to_text(md)
        self.assertNotIn("<br/>", result)
        self.assertNotIn("<b>", result)

    def test_table_conversion(self) -> None:
        """测试表格转换为纯文本."""
        md = "| key | value |\n| --- | --- |\n| name | test |"
        result = markdown_to_text(md)
        self.assertNotIn("---", result)
        self.assertIn("key", result)
        self.assertIn("value", result)
        self.assertIn("name", result)
        self.assertIn("test", result)

    def test_heading_removal(self) -> None:
        """测试移除标题标记."""
        md = "## Heading"
        result = markdown_to_text(md)
        self.assertNotIn("##", result)
        self.assertIn("Heading", result)

    def test_list_removal(self) -> None:
        """测试移除列表标记."""
        md = "- item1\n- item2\n1. numbered"
        result = markdown_to_text(md)
        self.assertNotIn("- item", result)
        self.assertNotIn("1. numbered", result)
        self.assertIn("item1", result)
        self.assertIn("item2", result)
        self.assertIn("numbered", result)

    def test_blockquote_removal(self) -> None:
        """测试移除引用标记."""
        md = "> quoted text"
        result = markdown_to_text(md)
        self.assertNotIn(">", result)
        self.assertIn("quoted text", result)

    def test_html_entity_decode(self) -> None:
        """测试 HTML 实体解码."""
        md = "Text &amp; more"
        result = markdown_to_text(md)
        self.assertIn("&", result)

    def test_complex_pr_body(self) -> None:
        """测试复杂 PR 描述."""
        md = """### 歌词议题
#9506

### 歌词作者
@ranhengzhang

| *key* | *value* |
| -: | :- |
| **作曲** | `蔡近翰Zoe` |

```
[00:00.00] 测试歌词
```
"""
        result = markdown_to_text(md)
        self.assertNotIn("```", result)
        self.assertNotIn("---", result)
        self.assertIn("歌词议题", result)
        self.assertIn("作曲", result)
