"""测试公共模块.

提供测试基类和辅助函数.
"""

import tempfile
from datetime import datetime
from typing import Dict, Any, Optional
from unittest import IsolatedAsyncioTestCase
from unittest.mock import MagicMock, patch

from src.fetcher import PRData
from src.config import reset_config


class AsyncTestCase(IsolatedAsyncioTestCase):
    """异步测试基类.

    继承自 IsolatedAsyncioTestCase,提供通用的测试基础设施.
    """

    async def asyncSetUp(self) -> None:
        """异步测试前置设置."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)

        # 重置配置单例
        reset_config()

    async def asyncTearDown(self) -> None:
        """异步测试后置清理."""
        pass

    def create_mock_pr_data(
        self,
        number: int = 1,
        title: str = "Test PR",
        state: str = "open",
        merged: bool = False,
        draft: bool = False,
        author: str = "testuser",
        **kwargs: Any,
    ) -> PRData:
        """创建模拟 PR 数据.

        Args:
            number: PR 编号.
            title: PR 标题.
            state: PR 状态.
            merged: 是否已合并.
            draft: 是否为草稿.
            author: 作者.
            **kwargs: 其他字段覆盖.

        Returns:
            PRData 实例.
        """
        now = datetime.now()
        data = {
            "number": number,
            "title": title,
            "state": state,
            "merged": merged,
            "draft": draft,
            "author": author,
            "author_avatar": f"https://github.com/{author}.png",
            "created_at": now,
            "updated_at": now,
            "merged_at": now if merged else None,
            "closed_at": now if state == "closed" and not merged else None,
            "body": "This is a test PR description.",
            "additions": kwargs.get("additions", 100),
            "deletions": kwargs.get("deletions", 50),
            "changed_files": kwargs.get("changed_files", 5),
            "commits": kwargs.get("commits", 3),
            "comments": kwargs.get("comments", 2),
            "labels": kwargs.get("labels", ["bug", "enhancement"]),
            "html_url": f"https://github.com/owner/repo/pull/{number}",
            "base_branch": "main",
            "head_branch": "feature-branch",
        }
        data.update(kwargs)
        return PRData(**data)

    def create_mock_pr_dict(self, **kwargs: Any) -> Dict[str, Any]:
        """创建模拟 PR 数据字典.

        Args:
            **kwargs: 字段覆盖.

        Returns:
            PR 数据字典.
        """
        now = datetime.now().isoformat()
        data = {
            "number": 1,
            "title": "Test PR",
            "state": "open",
            "merged": False,
            "draft": False,
            "author": "testuser",
            "author_avatar": "https://github.com/testuser.png",
            "created_at": now,
            "updated_at": now,
            "merged_at": None,
            "body": "Test description",
            "additions": 100,
            "deletions": 50,
            "changed_files": 5,
            "commits": 3,
            "comments": 2,
            "labels": ["bug"],
            "html_url": "https://github.com/owner/repo/pull/1",
            "base_branch": "main",
            "head_branch": "feature",
        }
        data.update(kwargs)
        return data


class MockGitHubResponse:
    """模拟 GitHub API 响应对象."""

    def __init__(self, **kwargs: Any) -> None:
        """初始化模拟响应.

        Args:
            **kwargs: 属性值.
        """
        for key, value in kwargs.items():
            setattr(self, key, value)


def mock_github_pr(
    number: int = 1,
    title: str = "Test PR",
    state: str = "open",
    **kwargs: Any,
) -> MagicMock:
    """创建模拟 PR 对象.

    Args:
        number: PR 编号.
        title: 标题.
        state: 状态.
        **kwargs: 其他属性.

    Returns:
        模拟 PR 对象.
    """
    mock = MagicMock()
    mock.number = number
    mock.title = title
    mock.state = state
    mock.merged = kwargs.get("merged", False)
    mock.draft = kwargs.get("draft", False)
    mock.body = kwargs.get("body", "Test body")
    mock.additions = kwargs.get("additions", 100)
    mock.deletions = kwargs.get("deletions", 50)
    mock.changed_files = kwargs.get("changed_files", 5)
    mock.commits = kwargs.get("commits", 3)
    mock.comments = kwargs.get("comments", 2)
    mock.created_at = kwargs.get("created_at", datetime.now())
    mock.updated_at = kwargs.get("updated_at", datetime.now())
    mock.merged_at = kwargs.get("merged_at")
    mock.closed_at = kwargs.get("closed_at", datetime.now() if state == "closed" and not kwargs.get("merged", False) else None)
    mock.html_url = kwargs.get("html_url", f"https://github.com/owner/repo/pull/{number}")
    mock.base.ref = kwargs.get("base_branch", "main")
    mock.head.ref = kwargs.get("head_branch", "feature")

    # 用户对象
    user_mock = MagicMock()
    user_mock.login = kwargs.get("author", "testuser")
    user_mock.avatar_url = kwargs.get("author_avatar", "https://github.com/testuser.png")
    mock.user = user_mock

    # 标签列表
    labels = kwargs.get("labels", [])
    label_mocks = []
    for label_name in labels:
        label_mock = MagicMock()
        label_mock.name = label_name
        label_mocks.append(label_mock)
    mock.labels = label_mocks

    return mock
