"""截图模块.

提供使用 Playwright 将 HTML 渲染为图片的功能.
"""

import asyncio
import os
import platform
import shutil
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from PIL import Image
from playwright.async_api import async_playwright, Page, Browser, BrowserContext

from src.config import get_config
from src.utils import get_logger


class ScreenshotTaker:
    """截图器.

    使用 Playwright 将 HTML 内容截取为图片.

    Attributes:
        _config: 配置管理器.
        _browser: Playwright 浏览器实例.
        _context: 浏览器上下文.
        _playwright: Playwright 实例.
    """

    def __init__(self) -> None:
        """初始化截图器."""
        self._config = get_config()
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._playwright: Optional[Any] = None

    async def __aenter__(self) -> "ScreenshotTaker":
        """异步上下文管理器入口."""
        await self.start()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """异步上下文管理器出口."""
        await self.close()

    async def start(self) -> None:
        """启动浏览器.

        根据配置启动指定的浏览器类型.
        如果配置了使用系统 Chrome,则尝试使用系统安装的 Chrome.
        """
        self._playwright = await async_playwright().start()

        browser_type = self._config.settings.browser_type
        headless = self._config.settings.headless
        proxy = self._config.get_proxy_for_playwright()
        use_system_chrome = self._config.settings.use_system_chrome
        chrome_path = self._config.settings.chrome_path

        # 启动浏览器
        browser_launcher = getattr(self._playwright, browser_type)

        launch_options: Dict[str, Any] = {"headless": headless}
        if proxy:
            launch_options["proxy"] = proxy

        # 如果使用系统 Chrome,指定可执行文件路径
        if use_system_chrome and browser_type == "chromium":
            chrome_executable = chrome_path or self._find_system_chrome()
            if chrome_executable:
                launch_options["executable_path"] = chrome_executable
                from src.utils import get_logger
                get_logger().info(f"使用系统 Chrome: {chrome_executable}")
            else:
                from src.utils import get_logger
                get_logger().warning("未找到系统 Chrome,将使用 Playwright 内置浏览器")

        self._browser = await browser_launcher.launch(**launch_options)
        # 创建上下文时不设置device_scale_factor，使用默认缩放
        self._context = await self._browser.new_context()

    def _find_system_chrome(self) -> Optional[str]:
        """查找系统安装的 Chrome 路径.

        Returns:
            Chrome 可执行文件路径,如果未找到则返回 None.
        """
        import platform
        import shutil

        system = platform.system()

        if system == "Windows":
            # Windows 常见 Chrome 安装路径
            possible_paths = [
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                r"C:\Users\{}\AppData\Local\Google\Chrome\Application\chrome.exe".format(os.environ.get("USERNAME", "")),
                r"C:\Users\{}\AppData\Local\Google\Chrome\Bin\chrome.exe".format(os.environ.get("USERNAME", "")),
            ]
            # 也尝试从环境变量 PATH 中查找
            chrome_from_path = shutil.which("chrome")
            if chrome_from_path:
                possible_paths.insert(0, chrome_from_path)

        elif system == "Darwin":  # macOS
            possible_paths = [
                "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                "/Applications/Chrome.app/Contents/MacOS/Google Chrome",
                os.path.expanduser("~/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
            ]

        else:  # Linux
            possible_paths = [
                "/usr/bin/google-chrome",
                "/usr/bin/google-chrome-stable",
                "/usr/bin/chromium",
                "/usr/bin/chromium-browser",
                "/snap/bin/chromium",
            ]
            # 从 PATH 中查找
            for name in ["google-chrome", "google-chrome-stable", "chromium", "chromium-browser"]:
                path = shutil.which(name)
                if path:
                    possible_paths.insert(0, path)

        # 检查路径是否存在
        for path in possible_paths:
            if path and os.path.isfile(path):
                return path

        return None

    def _add_gradient_background(self, img: Image.Image) -> Image.Image:
        """为图片添加倾斜渐变背景 (135度).

        Args:
            img: 原始图片.

        Returns:
            添加背景后的图片.
        """
        from PIL import ImageDraw
        import math

        # 创建渐变背景
        width, height = img.size
        background = Image.new('RGB', (width, height), (255, 255, 255))
        draw = ImageDraw.Draw(background)

        # 135度倾斜渐变: 从左上到右下
        # 计算对角线长度作为渐变距离
        diag = int(math.sqrt(width ** 2 + height ** 2))

        # 绘制倾斜渐变 (135deg: #e3f2fd -> #ffffff -> #bbdefb)
        for i in range(-diag, diag):
            # 计算渐变比例 (0 -> 0.5 -> 1)
            ratio = (i + diag) / (2 * diag)

            if ratio < 0.5:
                # 前半部分: #e3f2fd (227, 242, 253) -> #ffffff (255, 255, 255)
                local_ratio = ratio * 2
                r = int(227 + (255 - 227) * local_ratio)
                g = int(242 + (255 - 242) * local_ratio)
                b = int(253 + (255 - 253) * local_ratio)
            else:
                # 后半部分: #ffffff (255, 255, 255) -> #bbdefb (187, 222, 251)
                local_ratio = (ratio - 0.5) * 2
                r = int(255 + (187 - 255) * local_ratio)
                g = int(255 + (222 - 255) * local_ratio)
                b = int(255 + (251 - 255) * local_ratio)

            # 绘制135度倾斜线 (斜率为 -1)
            # 线条方程: x + y = i + width (调整偏移使渐变覆盖整个图片)
            offset = i + width
            points = []

            # 左边界 (x=0): y = offset
            if 0 <= offset <= height:
                points.append((0, offset))

            # 右边界 (x=width): y = offset - width
            y_right = offset - width
            if 0 <= y_right <= height:
                points.append((width, y_right))

            # 上边界 (y=0): x = offset
            if 0 <= offset <= width:
                points.append((offset, 0))

            # 下边界 (y=height): x = offset - height
            x_bottom = offset - height
            if 0 <= x_bottom <= width:
                points.append((x_bottom, height))

            if len(points) >= 2:
                draw.line(points, fill=(r, g, b), width=2)

        # 将原图粘贴到背景上（处理透明背景）
        if img.mode == 'RGBA':
            background.paste(img, (0, 0), img)
        else:
            # 如果是白色背景的图片，直接混合
            background = Image.blend(background, img.convert('RGB'), alpha=1.0)

        return background

    def _add_gradient_background_to_image(self, image_path: Path) -> None:
        """为图片添加渐变背景.

        Args:
            image_path: 图片文件路径.
        """
        with Image.open(image_path) as img:
            # 添加渐变背景
            img_with_bg = self._add_gradient_background(img)
            img_with_bg.save(image_path, "PNG")

    async def close(self) -> None:
        """关闭浏览器."""
        if self._context:
            await self._context.close()
            self._context = None

        if self._browser:
            await self._browser.close()
            self._browser = None

        if self._playwright:
            await self._playwright.stop()
            self._playwright = None

    async def take_screenshot(
        self,
        html_content: str,
        output_path: Optional[Path] = None,
        selector: str = ".pr-card",
        wait_for_selector: Optional[str] = None,
        timeout: int = 30000,
        keep_page_open: bool = False,
    ) -> Path:
        """截取 HTML 内容为图片.

        Args:
            html_content: HTML 内容字符串.
            output_path: 输出文件路径.如果为 None,自动生成.
            selector: 要截图的 CSS 选择器.
            wait_for_selector: 等待该选择器出现后再截图.
            timeout: 等待超时时间(毫秒).
            keep_page_open: 是否保持页面打开(用于调试).

        Returns:
            输出图片的完整路径.

        Raises:
            RuntimeError: 当浏览器未启动时.
            ValueError: 当截图元素不存在时.
        """
        if not self._browser or not self._context:
            raise RuntimeError("浏览器未启动,请先调用 start() 或作为上下文管理器使用")

        # 确保输出目录存在
        self._config.settings.ensure_output_dir()

        # 生成输出路径
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self._config.settings.output_path / f"pr_card_{timestamp}.png"
        else:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

        # 创建新页面(或复用已有页面)
        if not hasattr(self, '_keep_open_page') or self._keep_open_page is None:
            self._keep_open_page = await self._context.new_page()
        page = self._keep_open_page

        # 监听图片加载
        pending_images = set()

        async def handle_route(route, request):
            if request.resource_type == "image":
                pending_images.add(request.url)
            await route.continue_()

        def handle_response(response):
            if response.request.url in pending_images:
                pending_images.discard(response.request.url)

        await page.route("**/*", handle_route)
        page.on("response", handle_response)

        try:
            # 设置视口大小为 1440 (720*2) 以支持2倍缩放
            await page.set_viewport_size({"width": 1440, "height": 720})

            # 加载 HTML 内容
            await page.set_content(html_content, wait_until="networkidle", timeout=timeout)

            # 等待特定选择器(如果指定)
            if wait_for_selector:
                await page.wait_for_selector(wait_for_selector, timeout=timeout)

            # 等待卡片元素渲染完成
            await page.wait_for_selector(selector, timeout=timeout)

            # 等待所有图片加载完成
            while pending_images:
                await page.wait_for_timeout(100)

            # 等待 Vue 渲染完成标记
            await page.wait_for_selector("body[data-render-complete='true']", timeout=timeout)

            # 截图（使用 device 缩放保持高清）
            await page.screenshot(path=str(output_path), type="png", full_page=True, animations="disabled", scale="device", omit_background=True)

            # 添加渐变背景
            self._add_gradient_background_to_image(output_path)

            return output_path.resolve()

        finally:
            if not keep_page_open:
                await page.close()
                self._keep_open_page = None

    async def take_screenshot_with_retry(
        self,
        html_content: str,
        output_path: Optional[Path] = None,
        selector: str = ".pr-card",
        max_retries: int = 3,
        timeout: int = 30000,
    ) -> Path:
        """带重试机制的截图.

        Args:
            html_content: HTML 内容字符串.
            output_path: 输出文件路径.
            selector: 要截图的 CSS 选择器.
            max_retries: 最大重试次数.
            timeout: 每次尝试的超时时间(毫秒).

        Returns:
            输出图片的完整路径.

        Raises:
            Exception: 当所有重试都失败时.
        """
        last_error: Optional[Exception] = None

        for attempt in range(max_retries):
            try:
                return await self.take_screenshot(
                    html_content=html_content,
                    output_path=output_path,
                    selector=selector,
                    timeout=timeout,
                )
            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    # 等待后重试
                    await asyncio.sleep(1 * (attempt + 1))
                    # 重新启动浏览器
                    await self.close()
                    await self.start()

        raise last_error or Exception("截图失败,已耗尽所有重试次数")


class ScreenshotManager:
    """截图管理器.

    提供高级截图功能,包括批量截图和自动资源管理.

    Attributes:
        _taker: ScreenshotTaker 实例.
    """

    def __init__(self) -> None:
        """初始化截图管理器."""
        self._taker: Optional[ScreenshotTaker] = None

    async def capture(
        self,
        html_content: str,
        output_path: Optional[Path] = None,
        style: Optional[str] = None,
        keep_open: bool = False,
        selector: str = ".pr-card",
    ) -> Path:
        """捕获 HTML 内容为图片.

        这是一个便捷方法,会自动管理浏览器生命周期.

        Args:
            html_content: HTML 内容.
            output_path: 输出路径.
            style: 卡片样式(用于生成文件名).
            keep_open: 截图后是否保持浏览器打开.
            selector: 要截图的 CSS 选择器.

        Returns:
            输出图片路径.
        """
        from src.config import get_config
        config = get_config()

        # 生成输出路径
        if output_path is None:
            config.settings.ensure_output_dir()

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            style_suffix = f"_{style}" if style else ""
            output_path = config.settings.output_path / f"pr_card{style_suffix}_{timestamp}.png"

        if keep_open:
            # 保持浏览器打开模式
            logger = get_logger()
            logger.info("保持浏览器打开模式 - 截图完成后窗口将保持打开")
            logger.info("按 Ctrl+C 退出程序")

            taker = ScreenshotTaker()
            await taker.start()
            try:
                result = await taker.take_screenshot(html_content, output_path, selector=selector, keep_page_open=True)
                logger.info(f"✓ 截图已保存: {result}")
                logger.info("浏览器窗口保持打开,查看完成后按 Ctrl+C 退出")
                # 保持运行直到用户中断
                while True:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                logger.info("收到中断信号,关闭浏览器...")
            finally:
                await taker.close()
            return result
        else:
            # 正常模式:使用上下文管理器自动关闭
            async with ScreenshotTaker() as taker:
                return await taker.take_screenshot(html_content, output_path, selector=selector)

    async def capture_multiple(
        self,
        html_contents: list,
        output_dir: Optional[Path] = None,
    ) -> list:
        """批量捕获多个 HTML 内容为图片.

        Args:
            html_contents: HTML 内容列表.
            output_dir: 输出目录.

        Returns:
            输出图片路径列表.
        """
        config = get_config()

        if output_dir is None:
            output_dir = config.settings.output_path

        output_dir.mkdir(parents=True, exist_ok=True)

        async with ScreenshotTaker() as taker:
            paths = []
            for i, html in enumerate(html_contents):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = output_dir / f"pr_card_{timestamp}_{i}.png"
                path = await taker.take_screenshot(html, output_path)
                paths.append(path)
            return paths


# 便捷函数
async def capture_html(
    html_content: str,
    output_path: Optional[Path] = None,
    style: Optional[str] = None,
) -> Path:
    """便捷函数:捕获 HTML 为图片.

    Args:
        html_content: HTML 内容.
        output_path: 输出路径.
        style: 卡片样式.

    Returns:
        输出图片路径.
    """
    manager = ScreenshotManager()
    return await manager.capture(html_content, output_path, style)


def capture_html_sync(
    html_content: str,
    output_path: Optional[Path] = None,
    style: Optional[str] = None,
) -> Path:
    """同步便捷函数:捕获 HTML 为图片.

    Args:
        html_content: HTML 内容.
        output_path: 输出路径.
        style: 卡片样式.

    Returns:
        输出图片路径.
    """
    return asyncio.run(capture_html(html_content, output_path, style))
