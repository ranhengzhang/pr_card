"""工具模块.

提供各种辅助函数和工具类.
"""

import re
import html
from pathlib import Path
from typing import Optional, Dict, Any
from urllib.parse import urlparse


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

    # 移除代码块 (但保留表格内容)
    # 代码块使用 ``` 包裹，表格使用 | 分隔
    text = re.sub(r"```[\s\S]*?```", "", text)
    # 保留行内代码，但移除反引号
    text = re.sub(r"`([^`]+)`", r"\1", text)

    # 转换表格为纯文本格式 (保留内容，移除格式符号)
    lines = text.split('\n')
    result_lines = []
    for line in lines:
        # 检查是否是表格分隔行 (如 |---|---|)
        if re.match(r'^\s*\|[-:\s|]+\|\s*$', line):
            continue
        # 转换表格行为普通文本
        if '|' in line:
            # 提取表格单元格内容
            cells = [cell.strip() for cell in line.split('|')]
            # 过滤空单元格
            cells = [cell for cell in cells if cell]
            if cells:
                result_lines.append(' | '.join(cells))
        else:
            result_lines.append(line)
    text = '\n'.join(result_lines)

    # 移除标题标记
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)

    # 移除粗体和斜体
    text = re.sub(r"\*\*\*(.+?)\*\*\*", r"\1", text)
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"\*(.+?)\*", r"\1", text)
    text = re.sub(r"___(.+?)___", r"\1", text)
    text = re.sub(r"__(.+?)__", r"\1", text)
    text = re.sub(r"_(.+?)_", r"\1", text)

    # 移除图片 (包括 alt 文本) - 必须在链接处理之前
    text = re.sub(r"!\[[^\]]*\]\([^)]+\)", "", text)

    # 移除链接,保留文本
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"<([^>]+)>", r"\1", text)

    # 移除引用标记
    text = re.sub(r"^>\s*", "", text, flags=re.MULTILINE)

    # 移除列表标记
    text = re.sub(r"^[-*+]\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\d+\.\s+", "", text, flags=re.MULTILINE)

    # 移除水平线
    text = re.sub(r"^---+\s*$", "", text, flags=re.MULTILINE)

    # 移除 HTML 标签
    text = re.sub(r"<[^>]+>", "", text)

    # 解码 HTML 实体
    text = html.unescape(text)

    # 规范化空白字符
    text = re.sub(r"\n\s*\n", "\n\n", text)
    text = text.strip()

    return text


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


def sanitize_filename(filename: str) -> str:
    """清理文件名,移除非法字符.

    Args:
        filename: 原始文件名.

    Returns:
        清理后的文件名.
    """
    # Windows 非法字符: < > : " / \ | ? *
    illegal_chars = '<>:"/\\|?*'

    result = filename
    for char in illegal_chars:
        result = result.replace(char, "_")

    # 移除控制字符
    result = "".join(char for char in result if ord(char) >= 32)

    # 限制长度
    if len(result) > 200:
        result = result[:200]

    # 移除首尾空格和点
    result = result.strip(" .")

    # 确保不为空 (如果只剩 _ 也视为空)
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


def merge_proxy_config(
    http_proxy: Optional[str] = None,
    https_proxy: Optional[str] = None,
    playwright_proxy: Optional[str] = None,
) -> Dict[str, Any]:
    """合并代理配置.

    Args:
        http_proxy: HTTP 代理.
        https_proxy: HTTPS 代理.
        playwright_proxy: Playwright 代理.

    Returns:
        包含 requests 和 playwright 代理配置的字典.
    """
    # 使用 http_proxy 作为默认值
    default_proxy = http_proxy or https_proxy

    requests_proxy = {
        "http": http_proxy or default_proxy,
        "https": https_proxy or default_proxy,
    }

    pw_proxy = playwright_proxy or default_proxy
    playwright_proxy_config = {"server": pw_proxy} if pw_proxy else None

    return {
        "requests": requests_proxy,
        "playwright": playwright_proxy_config,
    }


class PathHelper:
    """路径辅助类.

    提供常用的路径操作功能.
    """

    @staticmethod
    def get_project_root() -> Path:
        """获取项目根目录.

        Returns:
            项目根目录的 Path 对象.
        """
        return Path(__file__).parent.parent

    @staticmethod
    def get_template_dir() -> Path:
        """获取模板目录.

        Returns:
            模板目录的 Path 对象.
        """
        return PathHelper.get_project_root() / "templates"

    @staticmethod
    def get_output_dir() -> Path:
        """获取输出目录.

        Returns:
            输出目录的 Path 对象.
        """
        return PathHelper.get_project_root() / "outputs"

    @staticmethod
    def ensure_dir(path: Path) -> Path:
        """确保目录存在.

        Args:
            path: 目录路径.

        Returns:
            目录的 Path 对象.
        """
        path.mkdir(parents=True, exist_ok=True)
        return path


class Logger:
    """简易日志记录器.

    提供基本的日志输出功能.
    """

    LEVELS = {
        "DEBUG": 0,
        "INFO": 1,
        "WARNING": 2,
        "ERROR": 3,
    }

    def __init__(self, name: str = "pr_card", level: str = "INFO") -> None:
        """初始化日志记录器.

        Args:
            name: 日志器名称.
            level: 日志级别.
        """
        self._name = name
        self._level = self.LEVELS.get(level, 1)

    def _log(self, level: str, message: str) -> None:
        """输出日志.

        Args:
            level: 日志级别.
            message: 日志消息.
        """
        if self.LEVELS.get(level, 1) >= self._level:
            from datetime import datetime

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{timestamp}] [{level}] [{self._name}] {message}")

    def debug(self, message: str) -> None:
        """输出调试日志."""
        self._log("DEBUG", message)

    def info(self, message: str) -> None:
        """输出信息日志."""
        self._log("INFO", message)

    def warning(self, message: str) -> None:
        """输出警告日志."""
        self._log("WARNING", message)

    def error(self, message: str) -> None:
        """输出错误日志."""
        self._log("ERROR", message)


# 全局日志实例
_default_logger: Optional[Logger] = None


def get_logger() -> Logger:
    """获取默认日志记录器.

    Returns:
        Logger 实例.
    """
    global _default_logger
    if _default_logger is None:
        _default_logger = Logger()
    return _default_logger
