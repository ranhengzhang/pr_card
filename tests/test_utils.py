"""工具模块测试.

测试仓库解析、URL 验证和日志功能.
"""

from tests.common import AsyncTestCase
from src.utils import (
    parse_repo_string,
    is_valid_pr_url,
)
from src.logger import get_logger, logger


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


class TestLogger(AsyncTestCase):
    """日志模块测试."""

    def test_get_logger_returns_logger(self) -> None:
        """测试 get_logger 返回 loguru logger."""
        result = get_logger()
        self.assertIs(result, logger)

    def test_logger_has_methods(self) -> None:
        """测试日志器具有标准方法."""
        self.assertTrue(hasattr(logger, "debug"))
        self.assertTrue(hasattr(logger, "info"))
        self.assertTrue(hasattr(logger, "warning"))
        self.assertTrue(hasattr(logger, "error"))

    def test_get_logger_consistent(self) -> None:
        """测试多次获取返回同一实例."""
        logger1 = get_logger()
        logger2 = get_logger()
        self.assertIs(logger1, logger2)
