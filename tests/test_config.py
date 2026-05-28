"""配置模块测试.

测试配置管理功能.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

from tests.common import AsyncTestCase
from src.config import Settings, ConfigManager, get_config, reset_config


class TestSettings(AsyncTestCase):
    """Settings 类测试."""

    async def asyncSetUp(self) -> None:
        """测试前置设置."""
        await super().asyncSetUp()
        # 清除环境变量
        for key in [
            "GITHUB_TOKEN", "DEFAULT_REPO", "DEFAULT_STYLE",
            "HTTP_PROXY", "HTTPS_PROXY", "PLAYWRIGHT_PROXY",
            "OUTPUT_DIR", "CARD_WIDTH", "BROWSER_TYPE",
            "HEADLESS", "CHROME_PATH", "USE_SYSTEM_CHROME", "KEEP_OPEN",
        ]:
            if key in os.environ:
                del os.environ[key]

    def test_default_values(self) -> None:
        """测试默认值."""
        settings = Settings()

        self.assertIsNone(settings.github_token)
        self.assertIsNone(settings.default_repo)
        self.assertEqual(settings.default_style, "github")
        self.assertIsNone(settings.http_proxy)
        self.assertEqual(settings.output_dir, "./outputs")
        self.assertEqual(settings.card_width, 1000)
        self.assertEqual(settings.browser_type, "chromium")
        self.assertTrue(settings.headless)

    def test_output_path_property(self) -> None:
        """测试 output_path 属性."""
        settings = Settings(output_dir="./test_outputs")
        self.assertEqual(settings.output_path, Path("./test_outputs"))

    def test_proxies_property(self) -> None:
        """测试 proxies 属性."""
        settings = Settings(http_proxy="http://proxy:8080", https_proxy="https://proxy:8080")
        proxies = settings.proxies

        self.assertEqual(proxies["http"], "http://proxy:8080")
        self.assertEqual(proxies["https"], "https://proxy:8080")

    def test_playwright_proxy_config(self) -> None:
        """测试 playwright_proxy_config 属性."""
        # 无代理时
        settings = Settings()
        self.assertIsNone(settings.playwright_proxy_config)

        # 有 playwright_proxy 时
        settings = Settings(playwright_proxy="http://proxy:8080")
        self.assertEqual(settings.playwright_proxy_config, {"server": "http://proxy:8080"})

        # 只有 http_proxy 时
        settings = Settings(http_proxy="http://proxy:8080")
        self.assertEqual(settings.playwright_proxy_config, {"server": "http://proxy:8080"})

    def test_validate_style_valid(self) -> None:
        """测试有效的样式验证."""
        for style in ["light", "dark", "github"]:
            settings = Settings(default_style=style)
            self.assertEqual(settings.default_style, style)

    def test_validate_style_invalid(self) -> None:
        """测试无效的样式验证."""
        with self.assertRaises(ValueError) as context:
            Settings(default_style="invalid")
        self.assertIn("无效的样式", str(context.exception))

    def test_validate_browser_valid(self) -> None:
        """测试有效的浏览器类型验证."""
        for browser in ["chromium", "firefox", "webkit"]:
            settings = Settings(browser_type=browser)
            self.assertEqual(settings.browser_type, browser)

    def test_validate_browser_invalid(self) -> None:
        """测试无效的浏览器类型验证."""
        with self.assertRaises(ValueError) as context:
            Settings(browser_type="invalid")
        self.assertIn("无效的浏览器类型", str(context.exception))

    def test_validate_card_width_invalid(self) -> None:
        """测试无效的卡片宽度验证."""
        with self.assertRaises(ValueError) as context:
            Settings(card_width=100)
        self.assertIn("卡片宽度", str(context.exception))

        with self.assertRaises(ValueError):
            Settings(card_width=3000)

    def test_ensure_output_dir(self) -> None:
        """测试 ensure_output_dir 方法."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "nested" / "outputs"
            settings = Settings(output_dir=str(output_path))
            settings.ensure_output_dir()
            self.assertTrue(output_path.exists())


class TestConfigManager(AsyncTestCase):
    """ConfigManager 类测试."""

    async def asyncSetUp(self) -> None:
        """测试前置设置."""
        await super().asyncSetUp()
        reset_config()

    def test_singleton(self) -> None:
        """测试单例模式."""
        config1 = get_config()
        config2 = get_config()
        self.assertIs(config1, config2)

    def test_update_from_cli(self) -> None:
        """测试从 CLI 更新配置."""
        config = get_config()

        config.update_from_cli(default_style="dark", card_width=1000)

        self.assertEqual(config.settings.default_style, "dark")
        self.assertEqual(config.settings.card_width, 1000)

    def test_get_proxy_for_requests(self) -> None:
        """测试获取 requests 代理配置."""
        config = get_config()
        config.update_from_cli(http_proxy="http://proxy:8080")

        proxies = config.get_proxy_for_requests()
        self.assertEqual(proxies["http"], "http://proxy:8080")

    def test_get_proxy_for_playwright(self) -> None:
        """测试获取 Playwright 代理配置."""
        config = get_config()
        config.update_from_cli(playwright_proxy="http://proxy:8080")

        proxy_config = config.get_proxy_for_playwright()
        self.assertEqual(proxy_config, {"server": "http://proxy:8080"})

    def test_apply_proxy_to_env(self) -> None:
        """测试应用代理到环境变量."""
        config = get_config()
        config.update_from_cli(http_proxy="http://proxy:8080", https_proxy="https://proxy:8080")

        config.apply_proxy_to_env()

        self.assertEqual(os.environ.get("HTTP_PROXY"), "http://proxy:8080")
        self.assertEqual(os.environ.get("HTTPS_PROXY"), "https://proxy:8080")


class TestConfigFromEnvFile(AsyncTestCase):
    """从环境文件加载配置测试."""

    def test_load_from_env_file(self) -> None:
        """测试从 .env 文件加载配置."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
            f.write("GITHUB_TOKEN=test_token_123\n")
            f.write("DEFAULT_REPO=testowner/testrepo\n")
            f.write("DEFAULT_STYLE=dark\n")
            f.write("CARD_WIDTH=1000\n")
            env_file = f.name

        try:
            with patch.dict(os.environ, {}, clear=True):
                settings = Settings(_env_file=env_file)
                self.assertEqual(settings.github_token, "test_token_123")
                self.assertEqual(settings.default_repo, "testowner/testrepo")
                self.assertEqual(settings.default_style, "dark")
                self.assertEqual(settings.card_width, 1000)
        finally:
            os.unlink(env_file)
