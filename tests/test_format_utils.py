"""格式化工具模块测试.

测试数字格式化、文本截断、文件名清理和输出文件名生成等功能.
"""

from tests.common import AsyncTestCase
from src.format_utils import truncate_text, format_number, sanitize_filename, generate_output_filename


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
