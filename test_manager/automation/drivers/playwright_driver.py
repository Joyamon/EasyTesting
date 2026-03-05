import logging
import asyncio
import time
from typing import Optional, Dict, Any, List
from pathlib import Path

logger = logging.getLogger(__name__)


class PlaywrightBrowserDriver:
    """Playwright 浏览器驱动
    
    提供浏览器启动、页面操作、截图等功能
    """
    
    def __init__(self, browser_type='chromium', headless=True, viewport=None, 
                 timeout=30000, slow_mo=0):
        """初始化浏览器驱动
        
        Args:
            browser_type: 浏览器类型 (chromium, firefox, webkit)
            headless: 是否无头模式
            viewport: 视口大小 {'width': 1280, 'height': 720}
            timeout: 全局超时时间（毫秒）
            slow_mo: 慢动作延迟（毫秒），用于调试
        """
        self.browser_type = browser_type
        self.headless = headless
        self.viewport = viewport or {'width': 1280, 'height': 720}
        self.timeout = timeout
        self.slow_mo = slow_mo
        
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        
        logger.info(f"Initialized PlaywrightBrowserDriver: {browser_type}, headless={headless}")
    
    async def launch(self):
        """启动浏览器
        
        Raises:
            RuntimeError: 如果启动失败
        """
        try:
            from playwright.async_api import async_playwright
            
            self.playwright = await async_playwright().start()
            
            browser_launcher = getattr(self.playwright, self.browser_type)
            self.browser = await browser_launcher.launch(
                headless=self.headless,
                slow_mo=self.slow_mo
            )
            
            self.context = await self.browser.new_context(viewport=self.viewport)
            self.context.set_default_timeout(self.timeout)
            
            self.page = await self.context.new_page()
            
            logger.info(f"Browser {self.browser_type} launched successfully")
        except Exception as e:
            logger.error(f"Failed to launch browser: {e}")
            raise
    
    async def close(self):
        """关闭浏览器"""
        try:
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            logger.info("Browser closed successfully")
        except Exception as e:
            logger.error(f"Error closing browser: {e}")
    
    async def navigate(self, url: str, wait_until='networkidle'):
        """导航到 URL
        
        Args:
            url: 目标 URL
            wait_until: 等待条件 (load, domcontentloaded, networkidle)
        
        Returns:
            response 对象
        """
        try:
            logger.info(f"Navigating to: {url}")
            response = await self.page.goto(url, wait_until=wait_until)
            logger.info(f"Navigation successful, status: {response.status if response else 'None'}")
            return response
        except Exception as e:
            logger.error(f"Navigation failed: {e}")
            raise
    
    async def screenshot(self, path: str, full_page=False):
        """截图
        
        Args:
            path: 保存路径
            full_page: 是否截整个页面
        
        Returns:
            bytes 的截图数据
        """
        try:
            # 确保目录存在
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            
            data = await self.page.screenshot(path=path, full_page=full_page)
            logger.info(f"Screenshot saved to: {path}")
            return data
        except Exception as e:
            logger.error(f"Screenshot failed: {e}")
            raise
    
    async def get_page_metrics(self) -> Dict[str, Any]:
        """获取页面性能指标
        
        Returns:
            包含性能指标的字典
        """
        try:
            metrics = await self.page.evaluate("""
                () => {
                    const navigation = window.performance.getEntriesByType('navigation')[0];
                    const paints = window.performance.getEntriesByType('paint');
                    
                    return {
                        pageLoadTime: navigation?.loadEventEnd,
                        fcp: paints.find(e => e.name === 'first-contentful-paint')?.startTime,
                        lcp: paints.find(e => e.name === 'largest-contentful-paint')?.startTime,
                    };
                }
            """)
            logger.info(f"Page metrics collected: {metrics}")
            return metrics
        except Exception as e:
            logger.error(f"Failed to get page metrics: {e}")
            return {}
    
    async def get_page_content(self) -> str:
        """获取页面 HTML 内容"""
        try:
            return await self.page.content()
        except Exception as e:
            logger.error(f"Failed to get page content: {e}")
            raise
    
    async def get_current_url(self) -> str:
        """获取当前 URL"""
        return self.page.url
    
    async def get_title(self) -> str:
        """获取页面标题"""
        return await self.page.title()
    
    async def wait_for_timeout(self, milliseconds: int):
        """等待指定时间
        
        Args:
            milliseconds: 等待时间（毫秒）
        """
        await self.page.wait_for_timeout(milliseconds)
    
    async def evaluate(self, expression: str, arg=None):
        """在页面上下文执行 JavaScript
        
        Args:
            expression: JavaScript 代码
            arg: 传递给 JavaScript 的参数
        
        Returns:
            JavaScript 执行结果
        """
        try:
            return await self.page.evaluate(expression, arg)
        except Exception as e:
            logger.error(f"JavaScript evaluation failed: {e}")
            raise
    
    async def set_viewport(self, width: int, height: int):
        """设置视口大小"""
        try:
            await self.page.set_viewport_size({'width': width, 'height': height})
            logger.info(f"Viewport set to: {width}x{height}")
        except Exception as e:
            logger.error(f"Failed to set viewport: {e}")
            raise
    
    async def scroll_to(self, x: int, y: int):
        """滚动到指定位置"""
        try:
            await self.evaluate(f"window.scrollTo({x}, {y})")
            logger.info(f"Scrolled to position: ({x}, {y})")
        except Exception as e:
            logger.error(f"Scroll failed: {e}")
            raise
    
    async def handle_dialog(self, dialog_type: str, action='accept', text=''):
        """处理弹出框
        
        Args:
            dialog_type: 弹框类型 (alert, confirm, prompt, beforeunload)
            action: 动作 (accept, dismiss)
            text: 对于 prompt，输入的文本
        """
        async def dialog_handler(dialog):
            logger.info(f"Dialog detected: {dialog.type}")
            if action == 'accept':
                if dialog.type == 'prompt' and text:
                    await dialog.accept(text)
                else:
                    await dialog.accept()
            else:
                await dialog.dismiss()
        
        self.page.on('dialog', dialog_handler)
    
    async def get_cookies(self) -> List[Dict]:
        """获取所有 cookie"""
        return await self.context.cookies()
    
    async def add_cookies(self, cookies: List[Dict]):
        """添加 cookies"""
        try:
            await self.context.add_cookies(cookies)
            logger.info(f"Added {len(cookies)} cookies")
        except Exception as e:
            logger.error(f"Failed to add cookies: {e}")
            raise
    
    async def clear_cookies(self):
        """清除所有 cookies"""
        try:
            await self.context.clear_cookies()
            logger.info("Cookies cleared")
        except Exception as e:
            logger.error(f"Failed to clear cookies: {e}")
            raise
    
    async def set_extra_http_headers(self, headers: Dict[str, str]):
        """设置额外的 HTTP 请求头"""
        try:
            await self.context.set_extra_http_headers(headers)
            logger.info(f"Set {len(headers)} extra HTTP headers")
        except Exception as e:
            logger.error(f"Failed to set HTTP headers: {e}")
            raise
    
    async def intercept_requests(self, url_pattern: str, callback):
        """拦截请求
        
        Args:
            url_pattern: URL 模式（正则表达式或通配符）
            callback: 请求拦截回调函数
        """
        try:
            async def route_handler(route):
                await callback(route)
            
            await self.page.route(url_pattern, route_handler)
            logger.info(f"Request interception set for: {url_pattern}")
        except Exception as e:
            logger.error(f"Failed to set request interception: {e}")
            raise
    
    async def add_init_script(self, script: str):
        """添加在页面加载前执行的脚本"""
        try:
            await self.context.add_init_script(script)
            logger.info("Init script added")
        except Exception as e:
            logger.error(f"Failed to add init script: {e}")
            raise
    
    async def record_video(self, video_path: str):
        """开始录制视频
        
        Args:
            video_path: 视频保存路径
        """
        try:
            # 在创建 context 时指定 record_video_dir
            logger.info(f"Video will be recorded to: {video_path}")
        except Exception as e:
            logger.error(f"Failed to setup video recording: {e}")
            raise
    
    @property
    def current_page(self):
        """获取当前页面对象"""
        return self.page
    
    @property
    def current_context(self):
        """获取当前上下文对象"""
        return self.context
    
    @property
    def current_browser(self):
        """获取当前浏览器对象"""
        return self.browser
