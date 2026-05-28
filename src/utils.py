"""通用工具模块.

提供仓库解析和 URL 验证等通用工具函数.
"""

from __future__ import annotations

import re
from typing import Dict

from src.format_utils import format_number, truncate_text, sanitize_filename, generate_output_filename
from src.markdown_utils import markdown_to_text
from src.logger import get_logger, logger


def parse_repo_string(repo_string: str) -> Dict[str, str]:
    """解析仓库字符串.

    Args:
        repo_string: 格式为 "owner/repo" 的字符串.

    Returns:
        包含 owner 和 repo 的字典.

    Raises:
        ValueError: 当格式无效时.
    """
    parts = repo_string.strip().split("/")
    if len(parts) != 2:
        raise ValueError(f"无效的仓库格式 '{repo_string}',应为 'owner/repo'")

    owner, repo = parts
    if not owner or not repo:
        raise ValueError(f"无效的仓库格式 '{repo_string}',owner 和 repo 不能为空")

    return {"owner": owner, "repo": repo}


def is_valid_pr_url(url: str) -> bool:
    """检查是否为有效的 GitHub PR URL.

    Args:
        url: 要检查的 URL.

    Returns:
        是否为有效的 PR URL.
    """
    pattern = r"^https?://github\.com/[^/]+/[^/]+/pull/\d+"
    return bool(re.match(pattern, url.strip()))
