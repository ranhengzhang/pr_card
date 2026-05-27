"""模板渲染模块.

提供将 PR 数据渲染为 HTML 卡片的功能.
"""

import re
from pathlib import Path
from typing import Dict, Any, Optional, List

import markdown
from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from src.config import get_config
from src.fetcher import PRData
from src.utils import markdown_to_text


class CardRenderer:
    """卡片渲染器.

    负责将 PR 数据渲染为 HTML 卡片.

    Attributes:
        _env: Jinja2 模板环境.
        _config: 配置管理器.
        _template_dir: 模板目录路径.
    """

    def __init__(self, template_dir: Optional[Path] = None) -> None:
        """初始化卡片渲染器.

        Args:
            template_dir: 模板目录路径.如果为 None,使用默认路径.
        """
        self._config = get_config()

        if template_dir is None:
            self._template_dir = Path(__file__).parent.parent / "templates"
        else:
            self._template_dir = Path(template_dir)

        self._env = Environment(
            loader=FileSystemLoader(str(self._template_dir)),
            autoescape=False,
        )
        # 确保 Jinja2 正确处理 Unicode
        self._env.policies['json.dumps_kwargs'] = {'ensure_ascii': False}

        # 添加自定义过滤器
        self._env.filters["markdown"] = self._markdown_filter
        self._env.filters["truncate"] = self._truncate_filter
        self._env.filters["format_number"] = self._format_number_filter

    def _markdown_filter(self, text: Optional[str]) -> str:
        """将 Markdown 转换为 HTML.

        Args:
            text: Markdown 文本.

        Returns:
            HTML 字符串.
        """
        if not text:
            return ""

        # 预处理：确保表格前面有空行（修复不规范的 Markdown）
        text = self._fix_table_markdown(text)

        return markdown.markdown(
            text,
            extensions=["nl2br", "fenced_code", "tables"]
        )

    def _fix_table_markdown(self, text: str) -> str:
        """修复不规范的 Markdown 表格格式.

        确保表格行前面有空行，使其能被正确解析为表格。

        Args:
            text: 原始 Markdown 文本.

        Returns:
            修复后的 Markdown 文本.
        """
        lines = text.split('\n')
        result = []

        for i, line in enumerate(lines):
            stripped = line.strip()

            # 检查是否是表格行（以 | 开头和结尾）
            if stripped.startswith('|') and stripped.endswith('|'):
                # 检查 result 中的前一行是否为空行（使用 result 而不是 lines）
                if result and result[-1].strip() != '':
                    # 前一行不是空行，添加空行
                    result.append('')

            result.append(line)

        return '\n'.join(result)

    def _truncate_filter(self, text: Optional[str], length: int = 200) -> str:
        """截断文本.

        Args:
            text: 原始文本.
            length: 最大长度.

        Returns:
            截断后的文本.
        """
        if not text:
            return ""
        text = markdown_to_text(text)
        if len(text) <= length:
            return text
        return text[: length - 3].rstrip() + "..."

    def _format_number_filter(self, num: int) -> str:
        """格式化数字.

        Args:
            num: 数字.

        Returns:
            格式化后的字符串(如 1.2k).
        """
        if num >= 1000000:
            return f"{num / 1000000:.1f}M"
        if num >= 1000:
            return f"{num / 1000:.1f}k"
        return str(num)

    def render(
        self,
        pr_data: PRData,
        style: Optional[str] = None,
        width: Optional[int] = None,
        comments: Optional[List[Dict[str, Any]]] = None,
        use_vue_template: bool = False,
        commits: Optional[List[Dict[str, Any]]] = None,
        events: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        """渲染 PR 卡片.

        Args:
            pr_data: PR 数据.
            style: 卡片样式 (light/dark/github).如果为 None,使用配置默认值.
            width: 卡片宽度.如果为 None,使用配置默认值.
            comments: PR 评论列表，用于 Vue 模板.
            use_vue_template: 是否使用 Vue 模板.
            commits: PR 提交记录列表.
            events: PR 事件记录列表（标签操作等）.

        Returns:
            渲染后的 HTML 字符串.

        Raises:
            ValueError: 当模板不存在时.
        """
        card_style = style or self._config.settings.default_style
        card_width = width or self._config.settings.card_width

        if use_vue_template:
            return self._render_vue_template(pr_data, comments or [], commits or [], events or [])
        else:
            # 准备模板上下文
            context = self._prepare_context(pr_data, card_style, card_width)

            try:
                template = self._env.get_template("card.html")
                return template.render(**context)
            except TemplateNotFound as e:
                raise ValueError(f"模板文件不存在: {e}")

    def _render_vue_template(
        self, pr_data: PRData, comments: List[Dict[str, Any]], commits: List[Dict[str, Any]], events: List[Dict[str, Any]]
    ) -> str:
        """渲染 Vue 模板.

        Args:
            pr_data: PR 数据.
            comments: 评论列表.
            commits: 提交记录列表.
            events: 事件记录列表.

        Returns:
            渲染后的 HTML 字符串.
        """
        # 准备 PR 数据字典
        pr_dict = {
            "number": pr_data.number,
            "title": pr_data.title,
            "state": pr_data.state,
            "merged": pr_data.merged,
            "draft": pr_data.draft,
            "author": pr_data.author,
            "author_avatar": pr_data.author_avatar,
            "created_at": pr_data.created_at.isoformat() if pr_data.created_at else "",
            "updated_at": pr_data.updated_at.isoformat() if pr_data.updated_at else "",
            "merged_at": pr_data.merged_at.isoformat() if pr_data.merged_at else "",
            "closed_at": pr_data.closed_at.isoformat() if pr_data.closed_at else "",
            "body": pr_data.body,
            "additions": pr_data.additions,
            "deletions": pr_data.deletions,
            "changed_files": pr_data.changed_files,
            "commits": pr_data.commits,
            "comments_count": pr_data.comments,
            "labels": pr_data.labels,
            "html_url": pr_data.html_url,
            "base_branch": pr_data.base_branch,
            "head_branch": pr_data.head_branch,
        }

        # 生成操作记录时间线
        timeline_events = self._generate_timeline_events(pr_data, comments, commits, events)

        context = {
            "pr": pr_data,
            "pr_data": pr_dict,
            "comments": comments,
            "commits": commits,
            "events": events,
            "timeline_events": timeline_events,
        }

        try:
            template = self._env.get_template("pr_card_vue.html")
            return template.render(**context)
        except TemplateNotFound as e:
            raise ValueError(f"Vue 模板文件不存在: {e}")

    def _generate_timeline_events(
        self, pr_data: PRData, comments: List[Dict[str, Any]], commits: List[Dict[str, Any]] = None, events_data: List[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """生成统一的时间线事件列表.

        包含 PR 创建、提交、标签操作、合并/关闭等记录，按时间排序.
        只有描述和评论显示为卡片，其他操作平铺显示.

        Args:
            pr_data: PR 数据.
            comments: 评论列表.
            commits: 提交记录列表.
            events_data: 事件记录列表（标签操作等）.

        Returns:
            按时间排序的事件列表.
        """
        events = []

        # 1. PR 创建事件
        events.append({
            "type": "created",
            "icon": "fa-plus",
            "icon_class": "event-created",
            "title": f"{pr_data.author} 创建了此 PR",
            "date": pr_data.created_at.isoformat() if pr_data.created_at else "",
            "description": f"从 {pr_data.head_branch} 合并到 {pr_data.base_branch}",
            "is_card": False,
            "author_avatar": pr_data.author_avatar,
        })

        # 2. 提交记录
        if commits:
            for commit in commits:
                events.append({
                    "type": "commit",
                    "icon": "fa-code-commit",
                    "icon_class": "event-commit",
                    "title": f"提交 {commit.get('sha', '')}",
                    "date": commit.get('date', ''),
                    "description": commit.get('message', '').split('\n')[0],
                    "author": commit.get('author', ''),
                    "is_card": False,
                    "author_avatar": commit.get('author_avatar', ''),
                })

        # 3. 标签事件
        if events_data:
            for event in events_data:
                event_type = event.get('event', '')
                if event_type == 'labeled':
                    label = event.get('label', {})
                    label_name = label.get('name', '')
                    label_color = label.get('color', '')
                    actor = event.get('actor', '')
                    events.append({
                        "type": "labeled",
                        "icon": "fa-tag",
                        "icon_class": "event-labeled",
                        "title": f"{actor} 添加了标签",
                        "date": event.get('created_at', ''),
                        "description": "",
                        "is_card": False,
                        "author_avatar": event.get('actor_avatar', ''),
                        "label": {
                            "name": label_name,
                            "color": label_color,
                        },
                    })
                elif event_type == 'unlabeled':
                    label = event.get('label', {})
                    label_name = label.get('name', '')
                    label_color = label.get('color', '')
                    actor = event.get('actor', '')
                    events.append({
                        "type": "unlabeled",
                        "icon": "fa-tag",
                        "icon_class": "event-unlabeled",
                        "title": f"{actor} 移除了标签",
                        "date": event.get('created_at', ''),
                        "description": "",
                        "is_card": False,
                        "author_avatar": event.get('actor_avatar', ''),
                        "label": {
                            "name": label_name,
                            "color": label_color,
                        },
                    })

        # 4. 合并事件
        if pr_data.merged and pr_data.merged_at:
            events.append({
                "type": "merged",
                "icon": "fa-code-merge",
                "icon_class": "event-merged",
                "title": f"{pr_data.author} 合并了此 PR",
                "date": pr_data.merged_at.isoformat(),
                "description": f"合并了 {pr_data.commits} 个提交",
                "is_card": False,
                "author_avatar": pr_data.author_avatar,
            })

        # 5. 关闭事件（未合并的关闭）
        elif pr_data.state == "closed" and pr_data.closed_at and not pr_data.merged:
            events.append({
                "type": "closed",
                "icon": "fa-xmark",
                "icon_class": "event-closed",
                "title": f"{pr_data.author} 关闭了此 PR",
                "date": pr_data.closed_at.isoformat(),
                "description": "此 PR 已被关闭",
                "is_card": False,
                "author_avatar": pr_data.author_avatar,
            })

        # 6. PR 描述（作为卡片事件插入时间线）
        if pr_data.body and pr_data.created_at:
            events.append({
                "type": "description",
                "icon": "fa-align-left",
                "icon_class": "event-description",
                "title": f"{pr_data.author} 添加了描述",
                "date": pr_data.created_at.isoformat(),
                "description": "",
                "is_card": True,
                "card_type": "pr",
                "author": pr_data.author,
                "author_avatar": pr_data.author_avatar,
                "body": pr_data.body,
            })

        # 7. 评论（作为卡片事件插入时间线）
        if comments:
            for comment in comments:
                events.append({
                    "type": "comment",
                    "icon": "fa-comment",
                    "icon_class": "event-comment",
                    "title": f"{comment.get('user', {}).get('login', '')} 发表了评论",
                    "date": comment.get('created_at', ''),
                    "description": "",
                    "is_card": True,
                    "card_type": "comment",
                    "author": comment.get('user', {}).get('login', ''),
                    "author_avatar": comment.get('user', {}).get('avatar_url', ''),
                    "body": comment.get('body', ''),
                    "comment_index": comments.index(comment),
                })

        # 按时间排序
        events.sort(key=lambda x: x["date"])

        return events

    def _prepare_context(
        self, pr_data: PRData, style: str, width: int
    ) -> Dict[str, Any]:
        """准备模板上下文.

        Args:
            pr_data: PR 数据.
            style: 卡片样式.
            width: 卡片宽度.

        Returns:
            模板上下文字典.
        """
        # 确定状态显示
        status_info = self._get_status_info(pr_data)

        # 格式化时间
        created_date = pr_data.created_at.strftime("%Y-%m-%d") if pr_data.created_at else ""

        return {
            "pr": pr_data,
            "style": style,
            "width": width,
            "status": status_info,
            "created_date": created_date,
            "has_body": bool(pr_data.body and pr_data.body.strip()),
            "has_labels": bool(pr_data.labels),
        }

    def _get_status_info(self, pr_data: PRData) -> Dict[str, str]:
        """获取状态信息.

        Args:
            pr_data: PR 数据.

        Returns:
            包含状态文本和 CSS 类的字典.
        """
        if pr_data.merged:
            return {
                "text": "Merged",
                "class": "status-merged",
                "icon": "git-merge",
            }
        elif pr_data.state == "closed":
            return {
                "text": "Closed",
                "class": "status-closed",
                "icon": "git-pull-request-closed",
            }
        elif pr_data.draft:
            return {
                "text": "Draft",
                "class": "status-draft",
                "icon": "git-pull-request-draft",
            }
        else:
            return {
                "text": "Open",
                "class": "status-open",
                "icon": "git-pull-request",
            }

    def get_available_styles(self) -> list:
        """获取可用的样式列表.

        Returns:
            样式名称列表.
        """
        return ["light", "dark", "github"]

    def render_from_dict(
        self,
        data: Dict[str, Any],
        style: Optional[str] = None,
        width: Optional[int] = None,
    ) -> str:
        """从字典渲染 PR 卡片.

        Args:
            data: PR 数据字典.
            style: 卡片样式.
            width: 卡片宽度.

        Returns:
            渲染后的 HTML 字符串.
        """
        # 将字典转换为 PRData 对象
        pr_data = self._dict_to_pr_data(data)
        return self.render(pr_data, style, width)

    def _dict_to_pr_data(self, data: Dict[str, Any]) -> PRData:
        """将字典转换为 PRData 对象.

        Args:
            data: PR 数据字典.

        Returns:
            PRData 对象.
        """
        from datetime import datetime

        def parse_date(date_str: Optional[str]) -> Optional[datetime]:
            if not date_str:
                return None
            try:
                return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                return None

        return PRData(
            number=data.get("number", 0),
            title=data.get("title", "Unknown"),
            state=data.get("state", "open"),
            merged=data.get("merged", False),
            draft=data.get("draft", False),
            author=data.get("author", "Unknown"),
            author_avatar=data.get("author_avatar", ""),
            created_at=parse_date(data.get("created_at")) or datetime.now(),
            updated_at=parse_date(data.get("updated_at")) or datetime.now(),
            merged_at=parse_date(data.get("merged_at")),
            body=data.get("body"),
            additions=data.get("additions", 0),
            deletions=data.get("deletions", 0),
            changed_files=data.get("changed_files", 0),
            commits=data.get("commits", 0),
            comments=data.get("comments", 0),
            labels=data.get("labels", []),
            html_url=data.get("html_url", ""),
            base_branch=data.get("base_branch", ""),
            head_branch=data.get("head_branch", ""),
        )


def render_card(
    pr_data: PRData,
    style: Optional[str] = None,
    width: Optional[int] = None,
) -> str:
    """便捷函数:渲染 PR 卡片.

    Args:
        pr_data: PR 数据.
        style: 卡片样式.
        width: 卡片宽度.

    Returns:
        渲染后的 HTML 字符串.
    """
    renderer = CardRenderer()
    return renderer.render(pr_data, style, width)
