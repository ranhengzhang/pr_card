"""截图模块测试.

测试 Playwright 截图功能.
"""

import asyncio
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock

from tests.common import AsyncTestCase
from src.screenshot import ScreenshotTaker, ScreenshotManager, capture_html


class TestScreenshotTaker(AsyncTestCase):
    """ScreenshotTaker 类测试."""

    async def asyncSetUp(self) -> None:
        """测试前置设置."""
        await super().asyncSetUp()
        self.taker = ScreenshotTaker()

    async def asyncTearDown(self) -> None:
        """测试后置清理."""
        await self.taker.close()

    def test_init(self) -> None:
        """测试初始化."""
        taker = ScreenshotTaker()
        self.assertIsNone(taker._browser)
        self.assertIsNone(taker._context)

    async def test_start_and_close(self) -> None:
        """测试启动和关闭."""
        with patch("src.screenshot.async_playwright") as mock_playwright:
            mock_pw = AsyncMock()
            mock_playwright.return_value.start = AsyncMock(return_value=mock_pw)

            mock_browser = AsyncMock()
            mock_pw.chromium.launch = AsyncMock(return_value=mock_browser)

            mock_context = AsyncMock()
            mock_browser.new_context = AsyncMock(return_value=mock_context)

            taker = ScreenshotTaker()
            await taker.start()

            self.assertIsNotNone(taker._browser)
            self.assertIsNotNone(taker._context)

            await taker.close()

            mock_browser.close.assert_called_once()
            mock_pw.stop.assert_called_once()

    async def test_take_screenshot_not_started(self) -> None:
        """测试未启动时截图应报错."""
        taker = ScreenshotTaker()

        with self.assertRaises(RuntimeError) as context:
            await taker.take_screenshot("<html></html>")

        self.assertIn("浏览器未启动", str(context.exception))

    async def test_take_screenshot_success(self) -> None:
        """测试成功截图."""
        with patch("src.screenshot.async_playwright") as mock_playwright:
            # 设置模拟对象
            mock_pw = AsyncMock()
            mock_playwright.return_value.start = AsyncMock(return_value=mock_pw)

            mock_browser = AsyncMock()
            mock_pw.chromium.launch = AsyncMock(return_value=mock_browser)

            mock_context = AsyncMock()
            mock_browser.new_context = AsyncMock(return_value=mock_context)

            mock_page = AsyncMock()
            mock_context.new_page = AsyncMock(return_value=mock_page)

            mock_element = AsyncMock()
            mock_page.wait_for_selector = AsyncMock(return_value=mock_element)

            taker = ScreenshotTaker()
            await taker.start()

            html = "<html><body><div class='pr-card'>Test</div></body></html>"
            output_path = Path(self.temp_dir.name) / "test.png"

            result = await taker.take_screenshot(html, output_path)

            self.assertEqual(result, output_path.resolve())
            mock_page.set_content.assert_called_once()
            mock_element.screenshot.assert_called_once_with(
                path=str(output_path), type="png"
            )

            await taker.close()

    async def test_take_screenshot_element_not_found(self) -> None:
        """测试元素未找到时."""
        with patch("src.screenshot.async_playwright") as mock_playwright:
            mock_pw = AsyncMock()
            mock_playwright.return_value.start = AsyncMock(return_value=mock_pw)

            mock_browser = AsyncMock()
            mock_pw.chromium.launch = AsyncMock(return_value=mock_browser)

            mock_context = AsyncMock()
            mock_browser.new_context = AsyncMock(return_value=mock_context)

            mock_page = AsyncMock()
            mock_context.new_page = AsyncMock(return_value=mock_page)

            # 元素未找到
            mock_page.wait_for_selector = AsyncMock(return_value=None)

            taker = ScreenshotTaker()
            await taker.start()

            html = "<html></html>"

            with self.assertRaises(ValueError) as context:
                await taker.take_screenshot(html)

            self.assertIn("找不到截图元素", str(context.exception))

            await taker.close()

    async def test_take_screenshot_with_retry_success_first_try(self) -> None:
        """测试带重试的截图(第一次成功)."""
        with patch.object(ScreenshotTaker, "take_screenshot") as mock_take:
            mock_take.return_value = Path("/test/output.png")

            taker = ScreenshotTaker()
            # 手动设置浏览器以避免启动
            taker._browser = MagicMock()
            taker._context = MagicMock()

            result = await taker.take_screenshot_with_retry("<html></html>")

            self.assertEqual(result, Path("/test/output.png"))
            mock_take.assert_called_once()

            await taker.close()

    async def test_take_screenshot_with_retry_eventual_success(self) -> None:
        """测试带重试的截图(最终成功)."""
        with patch.object(ScreenshotTaker, "take_screenshot") as mock_take:
            # 前两次失败,第三次成功
            mock_take.side_effect = [
                Exception("First failure"),
                Exception("Second failure"),
                Path("/test/output.png"),
            ]

            with patch.object(ScreenshotTaker, "start", AsyncMock()):
                with patch.object(ScreenshotTaker, "close", AsyncMock()):
                    taker = ScreenshotTaker()
                    taker._browser = MagicMock()
                    taker._context = MagicMock()

                    result = await taker.take_screenshot_with_retry(
                        "<html></html>", max_retries=3
                    )

                    self.assertEqual(result, Path("/test/output.png"))
                    self.assertEqual(mock_take.call_count, 3)

                    await taker.close()

    async def test_take_screenshot_with_retry_exhausted(self) -> None:
        """测试带重试的截图(重试耗尽)."""
        with patch.object(ScreenshotTaker, "take_screenshot") as mock_take:
            mock_take.side_effect = Exception("Always fails")

            with patch.object(ScreenshotTaker, "start", AsyncMock()):
                with patch.object(ScreenshotTaker, "close", AsyncMock()):
                    taker = ScreenshotTaker()
                    taker._browser = MagicMock()
                    taker._context = MagicMock()

                    with self.assertRaises(Exception) as context:
                        await taker.take_screenshot_with_retry(
                            "<html></html>", max_retries=2
                        )

                    self.assertEqual(str(context.exception), "Always fails")
                    self.assertEqual(mock_take.call_count, 2)

                    await taker.close()


class TestScreenshotManager(AsyncTestCase):
    """ScreenshotManager 类测试."""

    @patch("src.screenshot.ScreenshotTaker")
    async def test_capture(self, mock_taker_class: MagicMock) -> None:
        """测试 capture 方法."""
        mock_taker = AsyncMock()
        mock_taker_class.return_value = mock_taker
        mock_taker.__aenter__ = AsyncMock(return_value=mock_taker)
        mock_taker.__aexit__ = AsyncMock(return_value=None)
        mock_taker.take_screenshot = AsyncMock(return_value=Path("/test/output.png"))

        manager = ScreenshotManager()
        result = await manager.capture("<html></html>")

        self.assertEqual(result, Path("/test/output.png"))
        mock_taker.take_screenshot.assert_called_once()

    @patch("src.screenshot.ScreenshotTaker")
    async def test_capture_multiple(self, mock_taker_class: MagicMock) -> None:
        """测试批量截图."""
        mock_taker = AsyncMock()
        mock_taker_class.return_value = mock_taker
        mock_taker.__aenter__ = AsyncMock(return_value=mock_taker)
        mock_taker.__aexit__ = AsyncMock(return_value=None)

        mock_taker.take_screenshot = AsyncMock(side_effect=[
            Path("/test/1.png"),
            Path("/test/2.png"),
        ])

        manager = ScreenshotManager()
        htmls = ["<html>1</html>", "<html>2</html>"]
        results = await manager.capture_multiple(htmls, Path(self.temp_dir.name))

        self.assertEqual(len(results), 2)
        self.assertEqual(mock_taker.take_screenshot.call_count, 2)


class TestCaptureHtmlFunction(AsyncTestCase):
    """capture_html 函数测试."""

    @patch("src.screenshot.ScreenshotManager")
    async def test_capture_html(self, mock_manager_class: MagicMock) -> None:
        """测试 capture_html 函数."""
        mock_manager = MagicMock()
        mock_manager_class.return_value = mock_manager
        mock_manager.capture = AsyncMock(return_value=Path("/test/result.png"))

        result = await capture_html("<html></html>", style="dark")

        self.assertEqual(result, Path("/test/result.png"))
        mock_manager.capture.assert_called_once_with("<html></html>", None, "dark")
