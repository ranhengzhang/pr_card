"""格式化工具模块.

提供数字格式化、文本截断、文件名清理和输出文件名生成等功能.
"""

from __future__ import annotations

from typing import Optional


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """截断文本到指定长度.

    Args:
        text: 原始文本.
        max_length: 最大长度.
        suffix: 截断后添加的后缀.

    Returns:
        截断后的文本.
    """
    if not text or len(text) <= max_length:
        return text

    truncated = text[: max_length - len(suffix)].rstrip()
    return truncated + suffix


def format_number(num: int) -> str:
    """格式化数字为人类可读形式.

    Args:
        num: 数字.

    Returns:
        格式化后的字符串(如 1.2k, 3.4M).
    """
    if num >= 1_000_000_000:
        return f"{num / 1_000_000_000:.1f}B"
    if num >= 1_000_000:
        return f"{num / 1_000_000:.1f}M"
    if num >= 1_000:
        return f"{num / 1_000:.1f}k"
    return str(num)


def sanitize_filename(filename: str) -> str:
    """清理文件名,移除非法字符.

    Args:
        filename: 原始文件名.

    Returns:
        清理后的文件名.
    """
    illegal_chars = '<>:"/\\|?*'

    result = filename
    for char in illegal_chars:
        result = result.replace(char, "_")

    result = "".join(char for char in result if ord(char) >= 32)

    if len(result) > 200:
        result = result[:200]

    result = result.strip(" .")

    if not result or result.replace("_", "") == "":
        result = "unnamed"

    return result


def generate_output_filename(
    repo: str,
    pr_number: int,
    style: Optional[str] = None,
    extension: str = "png",
) -> str:
    """生成输出文件名.

    Args:
        repo: 仓库名称.
        pr_number: PR 编号.
        style: 卡片样式.
        extension: 文件扩展名.

    Returns:
        生成的文件名.
    """
    safe_repo = sanitize_filename(repo.replace("/", "_"))
    style_suffix = f"_{style}" if style else ""

    return f"{safe_repo}_PR{pr_number}{style_suffix}.{extension}"
