"""命令行入口模块.

提供 PR 卡片生成器的命令行界面.
"""

import argparse
import asyncio
import sys
from pathlib import Path
from typing import Optional, Tuple

from src.config import get_config, reset_config
from src.fetcher import GitHubFetcher, PRData, fetch_pr, fetch_pr_from_url
from src.renderer import CardRenderer, render_card
from src.screenshot import capture_html, ScreenshotManager
from src.utils import (
    parse_repo_string,
    is_valid_pr_url,
    generate_output_filename,
    get_logger,
)


def parse_arguments() -> argparse.Namespace:
    """解析命令行参数.

    Returns:
        解析后的参数命名空间.
    """
    parser = argparse.ArgumentParser(
        prog="pr-card",
        description="GitHub PR 卡片生成器 - 将 Pull Request 转换为精美的卡片图片",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s --pr 123                          # 使用默认仓库生成 PR #123 的卡片
  %(prog)s --repo owner/repo --pr 456        # 指定仓库生成卡片
  %(prog)s --url https://github.com/...      # 从 URL 生成卡片
  %(prog)s --pr 123 --style dark             # 使用深色主题
  %(prog)s --pr 123 --output ./my_card.png   # 指定输出路径
  %(prog)s --pr 123 --use-system-chrome      # 使用系统 Chrome(无需安装 Playwright 浏览器)
        """,
    )

    # PR 来源参数(互斥)
    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument(
        "--pr", "-p",
        type=int,
        help="PR 编号",
    )
    source_group.add_argument(
        "--url", "-u",
        type=str,
        help="PR 的完整 URL",
    )

    # 仓库参数
    parser.add_argument(
        "--repo", "-r",
        type=str,
        help="仓库名称 (格式: owner/repo),覆盖默认仓库配置",
    )

    # 样式参数
    parser.add_argument(
        "--style", "-s",
        type=str,
        choices=["light", "dark", "github"],
        help="卡片样式主题",
    )

    # 输出参数
    parser.add_argument(
        "--output", "-o",
        type=str,
        help="输出文件路径",
    )

    # 尺寸参数
    parser.add_argument(
        "--width", "-w",
        type=int,
        help="卡片宽度 (像素)",
    )

    # 代理参数
    parser.add_argument(
        "--proxy",
        type=str,
        help="网络代理地址 (如: http://127.0.0.1:7890)",
    )

    # Token 参数
    parser.add_argument(
        "--token", "-t",
        type=str,
        help="GitHub Personal Access Token",
    )

    # 浏览器参数
    parser.add_argument(
        "--headless",
        action="store_true",
        default=None,
        help="使用无头模式运行浏览器(默认)",
    )
    parser.add_argument(
        "--no-headless",
        action="store_true",
        help="显示浏览器窗口(调试用)",
    )
    parser.add_argument(
        "--keep-open",
        action="store_true",
        help="截图后保持浏览器窗口打开(调试用,按 Ctrl+C 退出)",
    )
    parser.add_argument(
        "--use-system-chrome",
        action="store_true",
        help="使用系统安装的 Chrome 浏览器(无需下载 Playwright 浏览器)",
    )
    parser.add_argument(
        "--chrome-path",
        type=str,
        help="手动指定 Chrome 可执行文件路径",
    )



    # 其他参数
    parser.add_argument(
        "--version", "-v",
        action="version",
        version="%(prog)s 1.0.0",
    )

    return parser.parse_args()


def resolve_repo(args: argparse.Namespace) -> Tuple[str, str]:
    """解析仓库信息.

    Args:
        args: 命令行参数.

    Returns:
        (owner, repo) 元组.

    Raises:
        SystemExit: 当无法确定仓库时.
    """
    config = get_config()

    # 如果指定了 --repo 参数
    if args.repo:
        return parse_repo_string(args.repo)["owner"], parse_repo_string(args.repo)["repo"]

    # 如果指定了 --url 参数
    if args.url:
        if not is_valid_pr_url(args.url):
            print(f"错误: 无效的 PR URL: {args.url}", file=sys.stderr)
            sys.exit(1)

        # 从 URL 解析
        import re
        match = re.search(r"github\.com/([^/]+)/([^/]+)/pull/", args.url)
        if match:
            return match.group(1), match.group(2)

    # 使用默认仓库
    if config.settings.default_repo:
        parts = parse_repo_string(config.settings.default_repo)
        return parts["owner"], parts["repo"]

    print(
        "错误: 无法确定仓库.请使用 --repo 指定仓库,或在配置文件中设置 DEFAULT_REPO",
        file=sys.stderr,
    )
    sys.exit(1)


def setup_config(args: argparse.Namespace) -> None:
    """根据命令行参数设置配置.

    Args:
        args: 命令行参数.
    """
    config = get_config()

    # 构建 CLI 覆盖配置
    cli_overrides = {}

    if args.style:
        cli_overrides["default_style"] = args.style

    if args.width:
        cli_overrides["card_width"] = args.width

    if args.proxy:
        cli_overrides["http_proxy"] = args.proxy
        cli_overrides["https_proxy"] = args.proxy
        cli_overrides["playwright_proxy"] = args.proxy

    if args.token:
        cli_overrides["github_token"] = args.token

    if args.no_headless:
        cli_overrides["headless"] = False
    elif args.headless:
        cli_overrides["headless"] = True

    if args.use_system_chrome:
        cli_overrides["use_system_chrome"] = True

    if args.chrome_path:
        cli_overrides["chrome_path"] = args.chrome_path

    if args.keep_open:
        cli_overrides["keep_open"] = True

    config.update_from_cli(**cli_overrides)

    # 应用代理到环境变量
    config.apply_proxy_to_env()


async def generate_card(
    owner: str,
    repo: str,
    pr_number: int,
    style: str,
    output_path: Optional[Path],
    token: Optional[str],
    keep_open: bool = False,
) -> Path:
    """生成 PR 卡片.

    Args:
        owner: 仓库所有者.
        repo: 仓库名称.
        pr_number: PR 编号.
        style: 卡片样式(已废弃，保留参数兼容性).
        output_path: 输出路径.
        token: GitHub Token.
        keep_open: 截图后是否保持浏览器打开.

    Returns:
        生成的图片路径.
    """
    logger = get_logger()

    # 1. 获取 PR 数据、评论、提交记录和事件
    logger.info(f"正在获取 PR #{pr_number} 的数据...")
    with GitHubFetcher(token) as fetcher:
        pr_data = fetcher.fetch_pr_data(owner, repo, pr_number)
        logger.info("正在获取 PR 评论...")
        comments = fetcher.fetch_pr_comments(owner, repo, pr_number)
        logger.info(f"✓ 获取到 {len(comments)} 条评论")
        logger.info("正在获取 PR 提交记录...")
        commits = fetcher.fetch_pr_commits(owner, repo, pr_number)
        logger.info(f"✓ 获取到 {len(commits)} 个提交")
        logger.info("正在获取 PR 事件记录...")
        events = fetcher.fetch_pr_events(owner, repo, pr_number)
        label_events = [e for e in events if e.get('event') in ['labeled', 'unlabeled']]
        logger.info(f"✓ 获取到 {len(label_events)} 条标签事件")

    logger.info(f"✓ 获取成功: {pr_data.title}")

    # 2. 渲染 HTML (默认使用 Vue 模板)
    logger.info("正在渲染 Vue 现代化卡片...")
    renderer = CardRenderer()
    html_content = renderer.render(pr_data, use_vue_template=True, comments=comments, commits=commits, events=events)
    logger.info("✓ 渲染完成")

    # 3. 生成截图
    logger.info("正在生成截图...")
    config = get_config()
    config.settings.ensure_output_dir()

    if output_path is None:
        output_path = config.settings.output_path / generate_output_filename(
            f"{owner}/{repo}",
            pr_number,
            "vue",
        )

    manager = ScreenshotManager()
    # 使用 Vue 模板选择器
    result_path = await manager.capture(html_content, output_path, "vue", keep_open=keep_open, selector="#app")

    if not keep_open:
        logger.info(f"✓ 截图已保存: {result_path}")

    return result_path


async def generate_card_from_url(
    url: str,
    style: str,
    output_path: Optional[Path],
    token: Optional[str],
    keep_open: bool = False,
) -> Path:
    """从 URL 生成 PR 卡片.

    Args:
        url: PR URL.
        style: 卡片样式(已废弃，保留参数兼容性).
        output_path: 输出路径.
        token: GitHub Token.
        keep_open: 截图后是否保持浏览器打开.

    Returns:
        生成的图片路径.
    """
    logger = get_logger()

    # 1. 获取 PR 数据、评论、提交记录和事件
    logger.info(f"正在从 URL 获取 PR 数据...")
    with GitHubFetcher(token) as fetcher:
        pr_data = fetcher.fetch_pr_by_url(url)
        # 解析 URL 获取评论
        import re
        match = re.search(r"github\.com/([^/]+)/([^/]+)/pull/(\d+)", url)
        if match:
            owner, repo_name, pr_number = match.group(1), match.group(2), int(match.group(3))
            logger.info("正在获取 PR 评论...")
            comments = fetcher.fetch_pr_comments(owner, repo_name, pr_number)
            logger.info(f"✓ 获取到 {len(comments)} 条评论")
            logger.info("正在获取 PR 提交记录...")
            commits = fetcher.fetch_pr_commits(owner, repo_name, pr_number)
            logger.info(f"✓ 获取到 {len(commits)} 个提交")
            logger.info("正在获取 PR 事件记录...")
            events = fetcher.fetch_pr_events(owner, repo_name, pr_number)
            label_events = [e for e in events if e.get('event') in ['labeled', 'unlabeled']]
            logger.info(f"✓ 获取到 {len(label_events)} 条标签事件")
        else:
            comments = []
            commits = []
            events = []
    logger.info(f"✓ 获取成功: {pr_data.title}")

    # 2. 渲染 HTML (使用 Vue 模板)
    logger.info("正在渲染 Vue 现代化卡片...")
    renderer = CardRenderer()
    html_content = renderer.render(pr_data, use_vue_template=True, comments=comments, commits=commits, events=events)
    logger.info("✓ 渲染完成")

    # 3. 生成截图
    logger.info("正在生成截图...")
    config = get_config()
    config.settings.ensure_output_dir()

    if output_path is None:
        # 从 URL 解析仓库信息
        if match:
            repo = f"{match.group(1)}/{match.group(2)}"
            pr_number = int(match.group(3))
            output_path = config.settings.output_path / generate_output_filename(repo, pr_number, "vue")
        else:
            output_path = config.settings.output_path / "pr_card_vue.png"

    manager = ScreenshotManager()
    result_path = await manager.capture(html_content, output_path, "vue", keep_open=keep_open, selector="#app")

    if not keep_open:
        logger.info(f"✓ 截图已保存: {result_path}")

    return result_path


async def main_async() -> int:
    """异步主函数.

    Returns:
        退出码.
    """
    args = parse_arguments()

    # 设置配置
    setup_config(args)
    config = get_config()

    # 确定 Token
    token = args.token or config.settings.github_token

    # 确定样式(已废弃，保留兼容性)
    style = args.style or config.settings.default_style

    # 确定输出路径
    output_path = Path(args.output) if args.output else None

    # 确定是否保持浏览器打开
    keep_open = args.keep_open or config.settings.keep_open

    try:
        if args.url:
            # 从 URL 生成
            result = await generate_card_from_url(
                url=args.url,
                style=style,
                output_path=output_path,
                token=token,
                keep_open=keep_open,
            )
        else:
            # 解析仓库信息
            owner, repo = resolve_repo(args)

            # 生成卡片(默认使用 Vue 模板)
            result = await generate_card(
                owner=owner,
                repo=repo,
                pr_number=args.pr,
                style=style,
                output_path=output_path,
                token=token,
                keep_open=keep_open,
            )

        if not keep_open:
            print(f"\n✅ 卡片生成成功!")
            print(f"📄 文件路径: {result}")
        return 0

    except Exception as e:
        print(f"\n❌ 错误: {e}", file=sys.stderr)
        return 1


def main() -> int:
    """主入口函数.

    Returns:
        退出码.
    """
    try:
        return asyncio.run(main_async())
    except KeyboardInterrupt:
        print("\n\n操作已取消", file=sys.stderr)
        return 130


if __name__ == "__main__":
    sys.exit(main())
