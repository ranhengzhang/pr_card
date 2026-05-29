"""Markdown 处理模块.

提供 Markdown 文本转换为纯文本的功能.
"""

from __future__ import annotations

import re
import html
from typing import Optional


def markdown_to_text(markdown_content: Optional[str]) -> str:
    """将 Markdown 转换为纯文本.

    移除 Markdown 标记,保留纯文本内容.

    Args:
        markdown_content: Markdown 格式的文本.

    Returns:
        纯文本内容.
    """
    if not markdown_content:
        return ""

    text = markdown_content

    text = re.sub(r"```[\s\S]*?```", "", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)

    lines = text.split('\n')
    result_lines = []
    for line in lines:
        if re.match(r'^\s*\|[-:\s|]+\|\s*$', line):
            continue
        if '|' in line:
            cells = [cell.strip() for cell in line.split('|')]
            cells = [cell for cell in cells if cell]
            if cells:
                result_lines.append(' | '.join(cells))
        else:
            result_lines.append(line)
    text = '\n'.join(result_lines)

    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)

    text = re.sub(r"\*\*\*(.+?)\*\*\*", r"\1", text)
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"\*(.+?)\*", r"\1", text)
    text = re.sub(r"___(.+?)___", r"\1", text)
    text = re.sub(r"__(.+?)__", r"\1", text)
    text = re.sub(r"_(.+?)_", r"\1", text)

    text = re.sub(r"!\[[^\]]*\]\([^)]+\)", "", text)

    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"<([^>]+)>", r"\1", text)

    text = re.sub(r"^>\s*\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]\s*\n?", "", text, flags=re.MULTILINE)

    text = re.sub(r"^>\s*", "", text, flags=re.MULTILINE)

    text = re.sub(r"^[-*+]\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\d+\.\s+", "", text, flags=re.MULTILINE)

    text = re.sub(r"^---+\s*$", "", text, flags=re.MULTILINE)

    text = re.sub(r"<[^>]+>", "", text)

    text = html.unescape(text)

    text = re.sub(r"\n\s*\n", "\n\n", text)
    text = text.strip()

    return text
