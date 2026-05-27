"""GitHub 数据获取模块.

提供从 GitHub API 获取 Pull Request 数据的功能.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict, Any

from github import Github, PullRequest, Repository, UnknownObjectException
from github.Auth import Token

from src.config import get_config


@dataclass
class PRData:
    """PR 数据结构.

    存储从 GitHub API 获取的 Pull Request 相关信息.

    Attributes:
        number: PR 编号.
        title: PR 标题.
        state: PR 状态 (open/closed).
        merged: 是否已合并.
        draft: 是否为草稿.
        author: 作者用户名.
        author_avatar: 作者头像 URL.
        created_at: 创建时间.
        updated_at: 更新时间.
        merged_at: 合并时间(如果已合并).
        closed_at: 关闭时间(如果已关闭).
        body: PR 描述内容.
        additions: 添加行数.
        deletions: 删除行数.
        changed_files: 变更文件数.
        commits: 提交数.
        comments: 评论数.
        labels: 标签列表.
        html_url: PR 网页链接.
        base_branch: 目标分支.
        head_branch: 源分支.
    """

    number: int
    title: str
    state: str
    merged: bool
    draft: bool
    author: str
    author_avatar: str
    created_at: datetime
    updated_at: datetime
    merged_at: Optional[datetime]
    closed_at: Optional[datetime]
    body: Optional[str]
    additions: int
    deletions: int
    changed_files: int
    commits: int
    comments: int
    labels: List[Dict[str, str]]  # 包含 name 和 color
    html_url: str
    base_branch: str
    head_branch: str

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式.

        Returns:
            包含所有字段的字典.
        """
        return {
            "number": self.number,
            "title": self.title,
            "state": self.state,
            "merged": self.merged,
            "draft": self.draft,
            "author": self.author,
            "author_avatar": self.author_avatar,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "merged_at": self.merged_at.isoformat() if self.merged_at else None,
            "body": self.body,
            "additions": self.additions,
            "deletions": self.deletions,
            "changed_files": self.changed_files,
            "commits": self.commits,
            "comments": self.comments,
            "labels": self.labels,
            "body": self.body,
            "html_url": self.html_url,
            "base_branch": self.base_branch,
            "head_branch": self.head_branch,
        }


class GitHubFetcher:
    """GitHub 数据获取器.

    负责与 GitHub API 交互,获取 Pull Request 数据.

    Attributes:
        _github: PyGithub 客户端实例.
        _config: 配置管理器.
    """

    def __init__(self, token: Optional[str] = None) -> None:
        """初始化 GitHub 获取器.

        Args:
            token: GitHub Personal Access Token.如果为 None,则从配置读取.
        """
        self._config = get_config()
        self._config.apply_proxy_to_env()

        auth_token = token or self._config.settings.github_token
        if auth_token:
            auth = Token(auth_token)
            self._github = Github(auth=auth)
        else:
            self._github = Github()

    def _get_repo(self, owner: str, name: str) -> Repository.Repository:
        """获取仓库对象.

        Args:
            owner: 仓库所有者.
            name: 仓库名称.

        Returns:
            Repository 对象.

        Raises:
            ValueError: 当仓库不存在时.
        """
        try:
            return self._github.get_repo(f"{owner}/{name}")
        except UnknownObjectException as e:
            raise ValueError(f"仓库 '{owner}/{name}' 不存在或无法访问") from e

    def _get_pr(
        self, repo: Repository.Repository, pr_number: int
    ) -> PullRequest.PullRequest:
        """获取 PR 对象.

        Args:
            repo: 仓库对象.
            pr_number: PR 编号.

        Returns:
            PullRequest 对象.

        Raises:
            ValueError: 当 PR 不存在时.
        """
        try:
            return repo.get_pull(pr_number)
        except UnknownObjectException as e:
            raise ValueError(f"PR #{pr_number} 不存在或无法访问") from e

    def fetch_pr_data(self, owner: str, repo_name: str, pr_number: int) -> PRData:
        """获取 PR 数据.

        Args:
            owner: 仓库所有者.
            repo_name: 仓库名称.
            pr_number: PR 编号.

        Returns:
            PRData 对象.

        Raises:
            ValueError: 当仓库或 PR 不存在时.
        """
        repo = self._get_repo(owner, repo_name)
        pr = self._get_pr(repo, pr_number)

        return self._extract_pr_data(pr)

    def _extract_pr_data(self, pr: PullRequest.PullRequest) -> PRData:
        """从 PR 对象提取数据.

        Args:
            pr: PullRequest 对象.

        Returns:
            PRData 对象.
        """
        labels = [{"name": label.name, "color": label.color} for label in pr.labels]

        return PRData(
            number=pr.number,
            title=pr.title,
            state=pr.state,
            merged=pr.is_merged(),
            draft=pr.draft,
            author=pr.user.login if pr.user else "Unknown",
            author_avatar=pr.user.avatar_url if pr.user else "",
            created_at=pr.created_at,
            updated_at=pr.updated_at,
            merged_at=pr.merged_at,
            closed_at=pr.closed_at if pr.state == "closed" else None,
            body=pr.body,
            additions=pr.additions,
            deletions=pr.deletions,
            changed_files=pr.changed_files,
            commits=pr.commits,
            comments=pr.comments,
            labels=labels,
            html_url=pr.html_url,
            base_branch=pr.base.ref,
            head_branch=pr.head.ref,
        )

    def fetch_pr_comments(
        self, owner: str, repo_name: str, pr_number: int
    ) -> List[Dict[str, Any]]:
        """获取 PR 的评论列表.

        Args:
            owner: 仓库所有者.
            repo_name: 仓库名称.
            pr_number: PR 编号.

        Returns:
            评论列表，每个评论是一个字典.
        """
        repo = self._get_repo(owner, repo_name)
        pr = self._get_pr(repo, pr_number)

        comments = []
        for comment in pr.get_issue_comments():
            comments.append({
                "id": comment.id,
                "body": comment.body,
                "user": {
                    "login": comment.user.login if comment.user else "Unknown",
                    "avatar_url": comment.user.avatar_url if comment.user else "",
                },
                "created_at": comment.created_at.isoformat() if comment.created_at else "",
                "updated_at": comment.updated_at.isoformat() if comment.updated_at else "",
                "html_url": comment.html_url,
            })

        return comments

    def fetch_pr_commits(
        self, owner: str, repo_name: str, pr_number: int
    ) -> List[Dict[str, Any]]:
        """获取 PR 的提交记录.

        Args:
            owner: 仓库所有者.
            repo_name: 仓库名称.
            pr_number: PR 编号.

        Returns:
            提交记录列表，每个提交是一个字典.
        """
        repo = self._get_repo(owner, repo_name)
        pr = self._get_pr(repo, pr_number)

        commits = []
        for commit in pr.get_commits():
            author_name = commit.commit.author.name if commit.commit and commit.commit.author else "Unknown"
            # 优先使用 GitHub API 返回的作者头像，如果没有则尝试构造
            if commit.author and hasattr(commit.author, 'avatar_url') and commit.author.avatar_url:
                author_avatar = commit.author.avatar_url
            else:
                author_avatar = f"https://github.com/{author_name}.png?size=32" if author_name != "Unknown" else ""
            commits.append({
                "sha": commit.sha[:7] if commit.sha else "",
                "message": commit.commit.message if commit.commit else "",
                "author": author_name,
                "author_avatar": author_avatar,
                "date": commit.commit.author.date.isoformat() if commit.commit and commit.commit.author and commit.commit.author.date else "",
                "html_url": commit.html_url if commit.html_url else "",
            })

        return commits

    def fetch_pr_events(
        self, owner: str, repo_name: str, pr_number: int
    ) -> List[Dict[str, Any]]:
        """获取 PR 的事件记录（包括标签添加等）.

        Args:
            owner: 仓库所有者.
            repo_name: 仓库名称.
            pr_number: PR 编号.

        Returns:
            事件记录列表.
        """
        repo = self._get_repo(owner, repo_name)
        pr = self._get_pr(repo, pr_number)

        events = []
        for event in pr.get_issue_events():
            actor = event.actor.login if event.actor else "Unknown"
            # 优先使用 GitHub API 返回的操作者头像，如果没有则尝试构造
            if event.actor and hasattr(event.actor, 'avatar_url') and event.actor.avatar_url:
                actor_avatar = event.actor.avatar_url
            else:
                actor_avatar = f"https://github.com/{actor}.png?size=32" if actor != "Unknown" else ""
            event_data = {
                "id": event.id,
                "event": event.event,
                "actor": actor,
                "actor_avatar": actor_avatar,
                "created_at": event.created_at.isoformat() if event.created_at else "",
            }

            # 标签相关事件
            if event.event in ["labeled", "unlabeled"] and event.label:
                event_data["label"] = {
                    "name": event.label.name,
                    "color": event.label.color,
                }

            events.append(event_data)

        return events

    def fetch_pr_by_url(self, url: str) -> PRData:
        """从 URL 获取 PR 数据.

        支持格式:
        - https://github.com/owner/repo/pull/123
        - https://github.com/owner/repo/pull/123/files

        Args:
            url: PR URL.

        Returns:
            PRData 对象.

        Raises:
            ValueError: 当 URL 格式无效或 PR 不存在时.
        """
        parts = self._parse_pr_url(url)
        return self.fetch_pr_data(parts["owner"], parts["repo"], parts["number"])

    def _parse_pr_url(self, url: str) -> Dict[str, Any]:
        """解析 PR URL.

        Args:
            url: PR URL.

        Returns:
            包含 owner, repo, number 的字典.

        Raises:
            ValueError: 当 URL 格式无效时.
        """
        import re

        pattern = r"github\.com/([^/]+)/([^/]+)/pull/(\d+)"
        match = re.search(pattern, url)

        if not match:
            raise ValueError(f"无效的 PR URL: {url}")

        return {
            "owner": match.group(1),
            "repo": match.group(2),
            "number": int(match.group(3)),
        }

    def close(self) -> None:
        """关闭 GitHub 客户端连接."""
        self._github.close()

    def __enter__(self) -> "GitHubFetcher":
        """上下文管理器入口."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """上下文管理器出口."""
        self.close()


def fetch_pr(
    owner: str, repo: str, pr_number: int, token: Optional[str] = None
) -> PRData:
    """便捷函数:获取 PR 数据.

    Args:
        owner: 仓库所有者.
        repo: 仓库名称.
        pr_number: PR 编号.
        token: 可选的 GitHub Token.

    Returns:
        PRData 对象.
    """
    with GitHubFetcher(token) as fetcher:
        return fetcher.fetch_pr_data(owner, repo, pr_number)


def fetch_pr_from_url(url: str, token: Optional[str] = None) -> PRData:
    """便捷函数:从 URL 获取 PR 数据.

    Args:
        url: PR URL.
        token: 可选的 GitHub Token.

    Returns:
        PRData 对象.
    """
    with GitHubFetcher(token) as fetcher:
        return fetcher.fetch_pr_by_url(url)
