"""日志模块.

提供统一的日志记录功能,基于 loguru.
"""

from __future__ import annotations

import sys

from loguru import logger

logger.remove()
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO",
)


def get_logger():
    """获取日志记录器.

    Returns:
        loguru.Logger 实例.
    """
    return logger
