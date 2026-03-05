"""
UI 自动化测试模块

这个模块提供 UI 自动化测试的核心功能，包括：
- Playwright 浏览器驱动
- 元素定位和交互
- UI 测试执行引擎
- 性能监控和截图
"""

from .drivers.playwright_driver import PlaywrightBrowserDriver
from .locators.element_locator import ElementLocator, ElementNotFoundError
from .executors.ui_executor import UITestExecutor

__all__ = [
    'PlaywrightBrowserDriver',
    'ElementLocator',
    'ElementNotFoundError',
    'UITestExecutor',
]
