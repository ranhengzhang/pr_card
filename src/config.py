"""配置管理模块.

提供统一的配置管理功能,支持环境变量、.env 文件和代码默认值.
配置优先级: 命令行参数 > 环境变量 > .env 文件 > 代码默认值
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置类.

    使用 Pydantic Settings 管理所有配置项,支持从环境变量和 .env 文件加载.

    Attributes:
        github_token: GitHub Personal Access Token,用于 API 认证.
        default_repo: 默认仓库,格式为 "owner/repo".
        default_style: 默认卡片样式,可选值: light, dark, github.
        http_proxy: HTTP 代理地址.
        https_proxy: HTTPS 代理地址.
        playwright_proxy: Playwright 浏览器代理地址.
        output_dir: 输出目录路径.
        card_width: 卡片宽度(像素).
        browser_type: 浏览器类型,可选值: chromium, firefox, webkit.
        headless: 是否使用无头模式运行浏览器.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # GitHub 配置
    github_token: Optional[str] = Field(default=None, description="GitHub Personal Access Token")

    # 默认配置
    default_repo: Optional[str] = Field(default=None, description="默认仓库 (owner/repo)")
    default_style: str = Field(default="github", description="默认卡片样式")

    # 代理配置
    http_proxy: Optional[str] = Field(default=None, alias="HTTP_PROXY")
    https_proxy: Optional[str] = Field(default=None, alias="HTTPS_PROXY")
    playwright_proxy: Optional[str] = Field(default=None, alias="PLAYWRIGHT_PROXY")

    # 输出配置
    output_dir: str = Field(default="./outputs", alias="OUTPUT_DIR")
    card_width: int = Field(default=1000, alias="CARD_WIDTH")

    # 浏览器配置
    browser_type: str = Field(default="chromium", alias="BROWSER_TYPE")
    headless: bool = Field(default=True, alias="HEADLESS")
    chrome_path: Optional[str] = Field(default=None, alias="CHROME_PATH")
    use_system_chrome: bool = Field(default=False, alias="USE_SYSTEM_CHROME")
    keep_open: bool = Field(default=False, alias="KEEP_OPEN")

    @field_validator("default_style")
    @classmethod
    def validate_style(cls, v: str) -> str:
        """验证样式名称是否有效.

        Args:
            v: 样式名称.

        Returns:
            验证通过的样式名称.

        Raises:
            ValueError: 当样式名称无效时.
        """
        valid_styles = ["light", "dark", "github"]
        if v not in valid_styles:
            raise ValueError(f"无效的样式 '{v}',必须是以下之一: {', '.join(valid_styles)}")
        return v

    @field_validator("browser_type")
    @classmethod
    def validate_browser(cls, v: str) -> str:
        """验证浏览器类型是否有效.

        Args:
            v: 浏览器类型.

        Returns:
            验证通过的浏览器类型.

        Raises:
            ValueError: 当浏览器类型无效时.
        """
        valid_browsers = ["chromium", "firefox", "webkit"]
        if v not in valid_browsers:
            raise ValueError(f"无效的浏览器类型 '{v}',必须是以下之一: {', '.join(valid_browsers)}")
        return v

    @field_validator("card_width")
    @classmethod
    def validate_card_width(cls, v: int) -> int:
        """验证卡片宽度是否有效.

        Args:
            v: 卡片宽度值.

        Returns:
            验证通过的卡片宽度.

        Raises:
            ValueError: 当宽度无效时.
        """
        if v < 400 or v > 2000:
            raise ValueError("卡片宽度必须在 400-2000 像素之间")
        return v

    @property
    def output_path(self) -> Path:
        """获取输出目录的 Path 对象.

        Returns:
            输出目录的 Path 对象.
        """
        return Path(self.output_dir)

    @property
    def proxies(self) -> Dict[str, Optional[str]]:
        """获取用于 requests 的代理配置.

        Returns:
            代理配置字典,包含 http 和 https 键.
        """
        return {
            "http": self.http_proxy,
            "https": self.https_proxy,
        }

    @property
    def playwright_proxy_config(self) -> Optional[Dict[str, str]]:
        """获取用于 Playwright 的代理配置.

        Returns:
            Playwright 代理配置字典,如果未配置代理则返回 None.
        """
        proxy = self.playwright_proxy or self.http_proxy
        if proxy:
            return {"server": proxy}
        return None

    def ensure_output_dir(self) -> None:
        """确保输出目录存在.

        如果输出目录不存在,则创建它.
        """
        self.output_path.mkdir(parents=True, exist_ok=True)


class ConfigManager:
    """配置管理器.

    提供对应用配置的集中访问和管理,支持动态更新配置.

    Attributes:
        _settings: 内部 Settings 实例.
        _cli_overrides: 命令行参数覆盖的配置.
    """

    def __init__(self) -> None:
        """初始化配置管理器."""
        self._settings: Settings = Settings()
        self._cli_overrides: Dict[str, Any] = {}

    @property
    def settings(self) -> Settings:
        """获取当前配置设置.

        Returns:
            Settings 实例.
        """
        return self._settings

    def update_from_cli(self, **kwargs: Any) -> None:
        """从命令行参数更新配置.

        Args:
            **kwargs: 命令行参数键值对.
        """
        for key, value in kwargs.items():
            if value is not None:
                self._cli_overrides[key] = value
                if hasattr(self._settings, key):
                    setattr(self._settings, key, value)

    def get_proxy_for_requests(self) -> Dict[str, Optional[str]]:
        """获取用于 requests 库的代理配置.

        Returns:
            代理配置字典.
        """
        return self._settings.proxies

    def get_proxy_for_playwright(self) -> Optional[Dict[str, str]]:
        """获取用于 Playwright 的代理配置.

        Returns:
            Playwright 代理配置字典或 None.
        """
        return self._settings.playwright_proxy_config

    def apply_proxy_to_env(self) -> None:
        """将代理配置应用到环境变量.

        这会影响使用环境变量的库(如 requests).
        """
        if self._settings.http_proxy:
            os.environ["HTTP_PROXY"] = self._settings.http_proxy
        if self._settings.https_proxy:
            os.environ["HTTPS_PROXY"] = self._settings.https_proxy


# 全局配置实例
_config_manager: Optional[ConfigManager] = None


def get_config() -> ConfigManager:
    """获取全局配置管理器实例.

    使用单例模式确保全局只有一个配置管理器.

    Returns:
        ConfigManager 实例.
    """
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


def reset_config() -> None:
    """重置全局配置管理器.

    主要用于测试场景.
    """
    global _config_manager
    _config_manager = None
