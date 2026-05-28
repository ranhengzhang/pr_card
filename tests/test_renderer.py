"""模板渲染模块测试.

测试 HTML 卡片渲染功能.
"""

from pathlib import Path
from unittest.mock import patch, MagicMock

from tests.common import AsyncTestCase
from src.renderer import CardRenderer, render_card
from src.fetcher import PRData


class TestCardRenderer(AsyncTestCase):
    """CardRenderer 类测试."""

    async def asyncSetUp(self) -> None:
        """测试前置设置."""
        await super().asyncSetUp()
        self.renderer = CardRenderer()
        self.pr_data = self.create_mock_pr_data()

    def test_init_default_template_dir(self) -> None:
        """测试默认模板目录初始化."""
        renderer = CardRenderer()
        expected_dir = Path(__file__).parent.parent / "templates"
        self.assertEqual(renderer._template_dir, expected_dir)

    def test_init_custom_template_dir(self) -> None:
        """测试自定义模板目录初始化."""
        custom_dir = Path("/custom/templates")
        renderer = CardRenderer(template_dir=custom_dir)
        self.assertEqual(renderer._template_dir, custom_dir)

    def test_markdown_filter(self) -> None:
        """测试 Markdown 过滤器."""
        renderer = CardRenderer()

        # 测试普通文本
        result = renderer._markdown_filter("Hello **World**")
        self.assertIn("<strong>World</strong>", result)

        # 测试空值
        self.assertEqual(renderer._markdown_filter(None), "")
        self.assertEqual(renderer._markdown_filter(""), "")

    def test_markdown_filter_table(self) -> None:
        """测试 Markdown 表格转换."""
        renderer = CardRenderer()

        # 测试表格转换
        md_table = """| key | value |
| -: | :- |
| **作曲** | `蔡近翰Zoe` |
| **作词** | `尹纯青Eyn` |"""

        result = renderer._markdown_filter(md_table)

        self.assertIn("<table>", result)
        self.assertIn("</table>", result)
        self.assertIn("<tr>", result)
        self.assertIn("<td ", result)  # td 可能有 style 属性
        self.assertIn("<th ", result)  # th 可能有 style 属性

    def test_truncate_filter(self) -> None:
        """测试截断过滤器."""
        renderer = CardRenderer()

        # 测试需要截断的文本
        long_text = "a" * 300
        result = renderer._truncate_filter(long_text, 100)
        self.assertTrue(result.endswith("..."))
        self.assertLessEqual(len(result), 103)

        # 测试不需要截断的文本
        short_text = "Short text"
        result = renderer._truncate_filter(short_text, 100)
        self.assertEqual(result, short_text)

        # 测试 Markdown 转换
        md_text = "This is **bold** text with more content"
        result = renderer._truncate_filter(md_text, 20)
        self.assertNotIn("**", result)  # Markdown 应该被转换

    def test_format_number_filter(self) -> None:
        """测试数字格式化过滤器."""
        from src.format_utils import format_number

        self.assertEqual(format_number(999), "999")
        self.assertEqual(format_number(1500), "1.5k")
        self.assertEqual(format_number(2500000), "2.5M")

    def test_get_status_info_merged(self) -> None:
        """测试合并状态信息."""
        renderer = CardRenderer()
        pr_data = self.create_mock_pr_data(merged=True, state="closed")

        status = renderer._get_status_info(pr_data)

        self.assertEqual(status["text"], "Merged")
        self.assertEqual(status["class"], "status-merged")

    def test_get_status_info_closed(self) -> None:
        """测试关闭状态信息."""
        renderer = CardRenderer()
        pr_data = self.create_mock_pr_data(merged=False, state="closed")

        status = renderer._get_status_info(pr_data)

        self.assertEqual(status["text"], "Closed")
        self.assertEqual(status["class"], "status-closed")

    def test_get_status_info_draft(self) -> None:
        """测试草稿状态信息."""
        renderer = CardRenderer()
        pr_data = self.create_mock_pr_data(draft=True, state="open")

        status = renderer._get_status_info(pr_data)

        self.assertEqual(status["text"], "Draft")
        self.assertEqual(status["class"], "status-draft")

    def test_get_status_info_open(self) -> None:
        """测试打开状态信息."""
        renderer = CardRenderer()
        pr_data = self.create_mock_pr_data(merged=False, state="open", draft=False)

        status = renderer._get_status_info(pr_data)

        self.assertEqual(status["text"], "Open")
        self.assertEqual(status["class"], "status-open")

    def test_prepare_context(self) -> None:
        """测试上下文准备."""
        renderer = CardRenderer()
        pr_data = self.create_mock_pr_data(
            title="Test Title",
            body="Test Body",
            labels=[{"name": "bug", "color": "d73a4a"}, {"name": "feature", "color": "a2eeef"}],
        )

        context = renderer._prepare_context(pr_data, "dark", 1000)

        self.assertEqual(context["pr"], pr_data)
        self.assertEqual(context["style"], "dark")
        self.assertEqual(context["width"], 1000)
        self.assertTrue(context["has_body"])
        self.assertTrue(context["has_labels"])
        self.assertIn("status", context)
        self.assertIn("created_date", context)

    def test_prepare_context_no_body(self) -> None:
        """测试无描述时的上下文."""
        renderer = CardRenderer()
        pr_data = self.create_mock_pr_data(body=None, labels=[])

        context = renderer._prepare_context(pr_data, "light", 800)

        self.assertFalse(context["has_body"])
        self.assertFalse(context["has_labels"])

    def test_get_available_styles(self) -> None:
        """测试获取可用样式."""
        renderer = CardRenderer()
        styles = renderer.get_available_styles()

        self.assertIn("light", styles)
        self.assertIn("dark", styles)
        self.assertIn("github", styles)

    def test_dict_to_pr_data(self) -> None:
        """测试字典转换为 PRData."""
        renderer = CardRenderer()
        data = self.create_mock_pr_dict(number=42, title="Dict Test")

        result = renderer._dict_to_pr_data(data)

        self.assertIsInstance(result, PRData)
        self.assertEqual(result.number, 42)
        self.assertEqual(result.title, "Dict Test")

    def test_render_from_dict(self) -> None:
        """测试从字典渲染."""
        renderer = CardRenderer()
        data = self.create_mock_pr_dict(title="Render From Dict")

        # 由于模板文件可能不存在,我们 mock 模板
        with patch.object(renderer._env, "get_template") as mock_get_template:
            mock_template = MagicMock()
            mock_template.render.return_value = "<html>Rendered</html>"
            mock_get_template.return_value = mock_template

            result = renderer.render_from_dict(data, style="github")

            self.assertEqual(result, "<html>Rendered</html>")


class TestRenderFunction(AsyncTestCase):
    """render_card 函数测试."""

    @patch("src.renderer.CardRenderer")
    def test_render_card(self, mock_renderer_class: MagicMock) -> None:
        """测试 render_card 函数."""
        mock_renderer = MagicMock()
        mock_renderer.render.return_value = "<html>Test</html>"
        mock_renderer_class.return_value = mock_renderer

        pr_data = self.create_mock_pr_data()
        result = render_card(pr_data, style="dark", width=1000)

        mock_renderer_class.assert_called_once()
        mock_renderer.render.assert_called_once_with(pr_data, "dark", 1000)
        self.assertEqual(result, "<html>Test</html>")
