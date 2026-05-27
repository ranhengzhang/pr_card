"""工具模块测试.

测试辅助函数和工具类.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from tests.common import AsyncTestCase
from src.utils import (
    markdown_to_text,
    truncate_text,
    format_number,
    parse_repo_string,
    is_valid_pr_url,
    sanitize_filename,
    generate_output_filename,
    merge_proxy_config,
    PathHelper,
    Logger,
    get_logger,
)


class TestMarkdownToText(AsyncTestCase):
    """markdown_to_text 函数测试."""

    def test_empty_input(self) -> None:
        """测试空输入."""
        self.assertEqual(markdown_to_text(None), "")
        self.assertEqual(markdown_to_text(""), "")

    def test_remove_code_blocks(self) -> None:
        """测试移除代码块."""
        md = "Some text\n```python\nprint('hello')\n```\nMore text"
        result = markdown_to_text(md)
        self.assertNotIn("```", result)
        self.assertNotIn("print", result)

    def test_remove_inline_code(self) -> None:
        """测试移除行内代码."""
        md = "Use `function()` to call"
        result = markdown_to_text(md)
        self.assertEqual(result, "Use function() to call")

    def test_remove_bold_italic(self) -> None:
        """测试移除粗体和斜体."""
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


class TestTruncateText(AsyncTestCase):
    """truncate_text 函数测试."""

    def test_no_truncate_needed(self) -> None:
        """测试不需要截断."""
        text = "Short text"
        result = truncate_text(text, 100)
        self.assertEqual(result, text)

    def test_truncate_with_suffix(self) -> None:
        """测试带后缀截断."""
        text = "a" * 200
        result = truncate_text(text, 50)
        self.assertTrue(result.endswith("..."))
        self.assertEqual(len(result), 50)

    def test_custom_suffix(self) -> None:
        """测试自定义后缀."""
        text = "a" * 100
        result = truncate_text(text, 50, suffix="[more]")
        self.assertTrue(result.endswith("[more]"))


class TestFormatNumber(AsyncTestCase):
    """format_number 函数测试."""

    def test_small_numbers(self) -> None:
        """测试小数字."""
        self.assertEqual(format_number(0), "0")
        self.assertEqual(format_number(999), "999")

    def test_thousands(self) -> None:
        """测试千位数."""
        self.assertEqual(format_number(1500), "1.5k")
        self.assertEqual(format_number(1000), "1.0k")

    def test_millions(self) -> None:
        """测试百万位数."""
        self.assertEqual(format_number(2500000), "2.5M")
        self.assertEqual(format_number(1000000), "1.0M")

    def test_billions(self) -> None:
        """测试十亿位数."""
        self.assertEqual(format_number(1500000000), "1.5B")


class TestParseRepoString(AsyncTestCase):
    """parse_repo_string 函数测试."""

    def test_valid_repo(self) -> None:
        """测试有效的仓库字符串."""
        result = parse_repo_string("owner/repo")
        self.assertEqual(result, {"owner": "owner", "repo": "repo"})

    def test_valid_repo_with_spaces(self) -> None:
        """测试带空格的仓库字符串."""
        result = parse_repo_string("  owner/repo  ")
        self.assertEqual(result, {"owner": "owner", "repo": "repo"})

    def test_invalid_format(self) -> None:
        """测试无效格式."""
        with self.assertRaises(ValueError) as context:
            parse_repo_string("invalid")
        self.assertIn("无效的仓库格式", str(context.exception))

    def test_empty_parts(self) -> None:
        """测试空部分."""
        with self.assertRaises(ValueError):
            parse_repo_string("/repo")

        with self.assertRaises(ValueError):
            parse_repo_string("owner/")


class TestIsValidPrUrl(AsyncTestCase):
    """is_valid_pr_url 函数测试."""

    def test_valid_urls(self) -> None:
        """测试有效的 URL."""
        valid_urls = [
            "https://github.com/owner/repo/pull/123",
            "http://github.com/owner/repo/pull/456",
            "https://github.com/my-org/my-repo/pull/789",
        ]
        for url in valid_urls:
            self.assertTrue(is_valid_pr_url(url), f"{url} should be valid")

    def test_invalid_urls(self) -> None:
        """测试无效的 URL."""
        invalid_urls = [
            "https://github.com/owner/repo/issues/123",
            "https://gitlab.com/owner/repo/pull/123",
            "not a url",
            "",
        ]
        for url in invalid_urls:
            self.assertFalse(is_valid_pr_url(url), f"{url} should be invalid")


class TestSanitizeFilename(AsyncTestCase):
    """sanitize_filename 函数测试."""

    def test_remove_illegal_chars(self) -> None:
        """测试移除非法字符."""
        filename = 'file<name>:"test"/\\|?*.txt'
        result = sanitize_filename(filename)
        self.assertNotIn("<", result)
        self.assertNotIn(">", result)
        self.assertNotIn(":", result)
        self.assertNotIn('"', result)
        self.assertNotIn("/", result)
        self.assertNotIn("\\", result)
        self.assertNotIn("|", result)
        self.assertNotIn("?", result)
        self.assertNotIn("*", result)

    def test_trim_spaces_and_dots(self) -> None:
        """测试修剪空格和点."""
        self.assertEqual(sanitize_filename("  filename.txt  "), "filename.txt")
        self.assertEqual(sanitize_filename("...filename..."), "filename")

    def test_empty_result(self) -> None:
        """测试空结果处理."""
        result = sanitize_filename("<>:\"/\\|?*")
        self.assertEqual(result, "unnamed")

    def test_length_limit(self) -> None:
        """测试长度限制."""
        long_name = "a" * 300
        result = sanitize_filename(long_name)
        self.assertLessEqual(len(result), 200)


class TestGenerateOutputFilename(AsyncTestCase):
    """generate_output_filename 函数测试."""

    def test_basic(self) -> None:
        """测试基本功能."""
        result = generate_output_filename("owner/repo", 123)
        self.assertEqual(result, "owner_repo_PR123.png")

    def test_with_style(self) -> None:
        """测试带样式."""
        result = generate_output_filename("owner/repo", 456, style="dark")
        self.assertEqual(result, "owner_repo_PR456_dark.png")

    def test_custom_extension(self) -> None:
        """测试自定义扩展名."""
        result = generate_output_filename("owner/repo", 789, extension="jpg")
        self.assertEqual(result, "owner_repo_PR789.jpg")


class TestMergeProxyConfig(AsyncTestCase):
    """merge_proxy_config 函数测试."""

    def test_all_proxies(self) -> None:
        """测试所有代理配置."""
        result = merge_proxy_config(
            http_proxy="http://proxy:8080",
            https_proxy="https://proxy:8080",
            playwright_proxy="http://playwright:8080",
        )

        self.assertEqual(result["requests"]["http"], "http://proxy:8080")
        self.assertEqual(result["requests"]["https"], "https://proxy:8080")
        self.assertEqual(result["playwright"]["server"], "http://playwright:8080")

    def test_no_proxies(self) -> None:
        """测试无代理配置."""
        result = merge_proxy_config()

        self.assertIsNone(result["requests"]["http"])
        self.assertIsNone(result["requests"]["https"])
        self.assertIsNone(result["playwright"])

    def test_default_from_http(self) -> None:
        """测试从 HTTP 代理获取默认值."""
        result = merge_proxy_config(http_proxy="http://proxy:8080")

        self.assertEqual(result["requests"]["https"], "http://proxy:8080")
        self.assertEqual(result["playwright"]["server"], "http://proxy:8080")


class TestPathHelper(AsyncTestCase):
    """PathHelper 类测试."""

    def test_get_project_root(self) -> None:
        """测试获取项目根目录."""
        root = PathHelper.get_project_root()
        self.assertTrue(root.exists())
        self.assertTrue((root / "src").exists())

    def test_get_template_dir(self) -> None:
        """测试获取模板目录."""
        template_dir = PathHelper.get_template_dir()
        self.assertEqual(template_dir.name, "templates")

    def test_get_output_dir(self) -> None:
        """测试获取输出目录."""
        output_dir = PathHelper.get_output_dir()
        self.assertEqual(output_dir.name, "outputs")

    def test_ensure_dir(self) -> None:
        """测试确保目录存在."""
        with tempfile.TemporaryDirectory() as temp:
            test_dir = Path(temp) / "nested" / "dir"
            result = PathHelper.ensure_dir(test_dir)
            self.assertTrue(result.exists())


class TestLogger(AsyncTestCase):
    """Logger 类测试."""

    def test_log_levels(self) -> None:
        """测试日志级别."""
        logger = Logger("test", level="INFO")

        # 测试各级别方法存在
        self.assertTrue(hasattr(logger, "debug"))
        self.assertTrue(hasattr(logger, "info"))
        self.assertTrue(hasattr(logger, "warning"))
        self.assertTrue(hasattr(logger, "error"))

    def test_get_logger_singleton(self) -> None:
        """测试日志单例."""
        logger1 = get_logger()
        logger2 = get_logger()
        self.assertIs(logger1, logger2)

    @patch("builtins.print")
    def test_info_output(self, mock_print: MagicMock) -> None:
        """测试 info 输出."""
        logger = Logger("test", level="INFO")
        logger.info("Test message")
        mock_print.assert_called_once()
        args = mock_print.call_args[0][0]
        self.assertIn("INFO", args)
        self.assertIn("Test message", args)
