"""数据获取模块测试.

测试 GitHub API 数据获取功能.
"""

from datetime import datetime
from unittest.mock import MagicMock, patch, PropertyMock

from github import UnknownObjectException

from tests.common import AsyncTestCase, mock_github_pr
from src.fetcher import GitHubFetcher, PRData, fetch_pr, fetch_pr_from_url
from src.config import get_config


class TestPRData(AsyncTestCase):
    """PRData 类测试."""

    def test_to_dict(self) -> None:
        """测试转换为字典."""
        pr_data = self.create_mock_pr_data(
            number=42,
            title="Test Title",
            additions=150,
            deletions=25,
        )

        result = pr_data.to_dict()

        self.assertEqual(result["number"], 42)
        self.assertEqual(result["title"], "Test Title")
        self.assertEqual(result["additions"], 150)
        self.assertEqual(result["deletions"], 25)
        self.assertIsInstance(result["created_at"], str)


class TestGitHubFetcher(AsyncTestCase):
    """GitHubFetcher 类测试."""

    def test_init_without_token(self) -> None:
        """测试无 Token 初始化."""
        with patch("src.fetcher.Github") as mock_github:
            with patch.object(get_config().settings, 'github_token', None):
                fetcher = GitHubFetcher()
                mock_github.assert_called_once_with()
                fetcher.close()

    def test_init_with_token(self) -> None:
        """测试带 Token 初始化."""
        with patch("src.fetcher.Github") as mock_github:
            with patch("src.fetcher.Token") as mock_token:
                fetcher = GitHubFetcher(token="test_token")
                mock_token.assert_called_once_with("test_token")
                mock_github.assert_called_once_with(auth=mock_token.return_value)
                fetcher.close()

    def test_parse_pr_url_valid(self) -> None:
        """测试有效的 PR URL 解析."""
        fetcher = GitHubFetcher()

        test_cases = [
            ("https://github.com/owner/repo/pull/123", {"owner": "owner", "repo": "repo", "number": 123}),
            ("https://github.com/myorg/myrepo/pull/456/files", {"owner": "myorg", "repo": "myrepo", "number": 456}),
        ]

        for url, expected in test_cases:
            result = fetcher._parse_pr_url(url)
            self.assertEqual(result, expected)

        fetcher.close()

    def test_parse_pr_url_invalid(self) -> None:
        """测试无效的 PR URL 解析."""
        fetcher = GitHubFetcher()

        invalid_urls = [
            "https://github.com/owner/repo/issues/123",
            "https://gitlab.com/owner/repo/pull/123",
            "not a url",
        ]

        for url in invalid_urls:
            with self.assertRaises(ValueError) as context:
                fetcher._parse_pr_url(url)
            self.assertIn("无效的 PR URL", str(context.exception))

        fetcher.close()

    @patch("src.fetcher.Github")
    def test_fetch_pr_data_success(self, mock_github_class: MagicMock) -> None:
        """测试成功获取 PR 数据."""
        # 设置模拟对象
        mock_github = MagicMock()
        mock_github_class.return_value = mock_github

        mock_repo = MagicMock()
        mock_github.get_repo.return_value = mock_repo

        mock_pr = mock_github_pr(
            number=123,
            title="Test PR Title",
            additions=100,
            deletions=50,
        )
        mock_repo.get_pull.return_value = mock_pr

        # 执行测试
        with GitHubFetcher() as fetcher:
            result = fetcher.fetch_pr_data("owner", "repo", 123)

        # 验证结果
        self.assertEqual(result.number, 123)
        self.assertEqual(result.title, "Test PR Title")
        self.assertEqual(result.additions, 100)
        self.assertEqual(result.deletions, 50)

    @patch("src.fetcher.Github")
    def test_fetch_pr_data_repo_not_found(self, mock_github_class: MagicMock) -> None:
        """测试仓库不存在的情况."""
        mock_github = MagicMock()
        mock_github_class.return_value = mock_github
        mock_github.get_repo.side_effect = UnknownObjectException(404, "Not Found")

        with GitHubFetcher() as fetcher:
            with self.assertRaises(ValueError) as context:
                fetcher.fetch_pr_data("nonexistent", "repo", 123)
            self.assertIn("不存在", str(context.exception))

    @patch("src.fetcher.Github")
    def test_fetch_pr_data_pr_not_found(self, mock_github_class: MagicMock) -> None:
        """测试 PR 不存在的情况."""
        mock_github = MagicMock()
        mock_github_class.return_value = mock_github

        mock_repo = MagicMock()
        mock_github.get_repo.return_value = mock_repo
        mock_repo.get_pull.side_effect = UnknownObjectException(404, "Not Found")

        with GitHubFetcher() as fetcher:
            with self.assertRaises(ValueError) as context:
                fetcher.fetch_pr_data("owner", "repo", 999)
            self.assertIn("不存在", str(context.exception))

    @patch("src.fetcher.Github")
    def test_fetch_pr_by_url(self, mock_github_class: MagicMock) -> None:
        """测试通过 URL 获取 PR."""
        mock_github = MagicMock()
        mock_github_class.return_value = mock_github

        mock_repo = MagicMock()
        mock_github.get_repo.return_value = mock_repo

        mock_pr = mock_github_pr(number=456, title="URL Test PR")
        mock_repo.get_pull.return_value = mock_pr

        with GitHubFetcher() as fetcher:
            result = fetcher.fetch_pr_by_url("https://github.com/owner/repo/pull/456")

        self.assertEqual(result.number, 456)
        self.assertEqual(result.title, "URL Test PR")


class TestFetchFunctions(AsyncTestCase):
    """便捷函数测试."""

    @patch("src.fetcher.Github")
    def test_fetch_pr(self, mock_github_class: MagicMock) -> None:
        """测试 fetch_pr 函数."""
        mock_github = MagicMock()
        mock_github_class.return_value = mock_github

        mock_repo = MagicMock()
        mock_github.get_repo.return_value = mock_repo

        mock_pr = mock_github_pr(number=1, title="Function Test")
        mock_repo.get_pull.return_value = mock_pr

        result = fetch_pr("owner", "repo", 1)

        self.assertEqual(result.number, 1)
        self.assertEqual(result.title, "Function Test")

    @patch("src.fetcher.Github")
    def test_fetch_pr_from_url(self, mock_github_class: MagicMock) -> None:
        """测试 fetch_pr_from_url 函数."""
        mock_github = MagicMock()
        mock_github_class.return_value = mock_github

        mock_repo = MagicMock()
        mock_github.get_repo.return_value = mock_repo

        mock_pr = mock_github_pr(number=2, title="URL Function Test")
        mock_repo.get_pull.return_value = mock_pr

        result = fetch_pr_from_url("https://github.com/owner/repo/pull/2")

        self.assertEqual(result.number, 2)
