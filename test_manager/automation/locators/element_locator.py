import logging
from typing import Optional, List
from playwright.async_api import Locator

logger = logging.getLogger(__name__)


class ElementNotFoundError(Exception):
    """元素未找到异常"""
    pass


class ElementLocator:
    """元素定位器
    
    提供元素定位、查找、验证等功能
    """
    
    def __init__(self, page):
        """初始化元素定位器
        
        Args:
            page: Playwright 页面对象
        """
        self.page = page
    
    def _build_selector(self, selector: str, selector_type: str) -> str:
        """构建 Playwright 选择器
        
        Args:
            selector: 选择器字符串
            selector_type: 选择器类型 (css, xpath, id, text)
        
        Returns:
            Playwright 格式的选择器
        """
        if selector_type == 'css':
            return selector
        elif selector_type == 'xpath':
            return f'xpath={selector}'
        elif selector_type == 'id':
            return f'#{selector}'
        elif selector_type == 'text':
            return f'text={selector}'
        else:
            raise ValueError(f"Unsupported selector type: {selector_type}")
    
    async def find_element(self, selector: str, selector_type: str = 'css', 
                          timeout: int = 10000) -> Locator:
        """查找单个元素
        
        Args:
            selector: 选择器字符串
            selector_type: 选择器类型
            timeout: 超时时间（毫秒）
        
        Returns:
            元素 Locator 对象
        
        Raises:
            ElementNotFoundError: 如果元素未找到
        """
        try:
            locator_str = self._build_selector(selector, selector_type)
            locator = self.page.locator(locator_str)
            
            # 等待元素出现
            await locator.wait_for(timeout=timeout)
            logger.info(f"Element found: {selector_type}={selector}")
            return locator
        except Exception as e:
            logger.error(f"Element not found: {selector_type}={selector}, error: {e}")
            raise ElementNotFoundError(f"Element not found: {selector}")
    
    async def find_elements(self, selector: str, selector_type: str = 'css') -> Locator:
        """查找多个元素
        
        Args:
            selector: 选择器字符串
            selector_type: 选择器类型
        
        Returns:
            元素 Locator 对象（代表多个匹配的元素）
        """
        try:
            locator_str = self._build_selector(selector, selector_type)
            locator = self.page.locator(locator_str)
            count = await locator.count()
            logger.info(f"Found {count} elements: {selector_type}={selector}")
            return locator
        except Exception as e:
            logger.error(f"Error finding elements: {selector_type}={selector}, error: {e}")
            raise
    
    async def is_visible(self, selector: str, selector_type: str = 'css', 
                        timeout: int = 10000) -> bool:
        """检查元素是否可见
        
        Args:
            selector: 选择器字符串
            selector_type: 选择器类型
            timeout: 超时时间（毫秒）
        
        Returns:
            是否可见
        """
        try:
            locator = await self.find_element(selector, selector_type, timeout)
            is_visible = await locator.is_visible()
            logger.info(f"Element visibility: {selector} = {is_visible}")
            return is_visible
        except ElementNotFoundError:
            return False
    
    async def is_hidden(self, selector: str, selector_type: str = 'css') -> bool:
        """检查元素是否隐藏"""
        try:
            locator = await self.find_element(selector, selector_type, timeout=5000)
            return await locator.is_hidden()
        except ElementNotFoundError:
            return True
    
    async def is_enabled(self, selector: str, selector_type: str = 'css') -> bool:
        """检查元素是否启用"""
        try:
            locator = await self.find_element(selector, selector_type)
            return await locator.is_enabled()
        except ElementNotFoundError:
            return False
    
    async def is_checked(self, selector: str, selector_type: str = 'css') -> bool:
        """检查复选框/单选框是否选中"""
        try:
            locator = await self.find_element(selector, selector_type)
            return await locator.is_checked()
        except ElementNotFoundError:
            return False
    
    async def get_text(self, selector: str, selector_type: str = 'css') -> str:
        """获取元素文本内容
        
        Args:
            selector: 选择器字符串
            selector_type: 选择器类型
        
        Returns:
            元素文本
        """
        try:
            locator = await self.find_element(selector, selector_type)
            text = await locator.inner_text()
            logger.info(f"Element text: {selector} = {text}")
            return text
        except Exception as e:
            logger.error(f"Error getting element text: {e}")
            raise
    
    async def get_attribute(self, selector: str, attr_name: str, 
                           selector_type: str = 'css') -> Optional[str]:
        """获取元素属性
        
        Args:
            selector: 选择器字符串
            attr_name: 属性名
            selector_type: 选择器类型
        
        Returns:
            属性值，如果不存在返回 None
        """
        try:
            locator = await self.find_element(selector, selector_type)
            value = await locator.get_attribute(attr_name)
            logger.info(f"Element attribute: {selector}@{attr_name} = {value}")
            return value
        except Exception as e:
            logger.error(f"Error getting element attribute: {e}")
            raise
    
    async def get_value(self, selector: str, selector_type: str = 'css') -> str:
        """获取输入框的值"""
        try:
            locator = await self.find_element(selector, selector_type)
            value = await locator.input_value()
            logger.info(f"Input value: {selector} = {value}")
            return value
        except Exception as e:
            logger.error(f"Error getting input value: {e}")
            raise
    
    async def contains_text(self, selector: str, text: str, 
                           selector_type: str = 'css') -> bool:
        """检查元素是否包含文本"""
        try:
            element_text = await self.get_text(selector, selector_type)
            return text in element_text
        except Exception as e:
            logger.error(f"Error checking text content: {e}")
            return False
    
    async def get_element_count(self, selector: str, selector_type: str = 'css') -> int:
        """获取匹配元素的数量"""
        try:
            locator = await self.find_elements(selector, selector_type)
            count = await locator.count()
            logger.info(f"Element count: {selector} = {count}")
            return count
        except Exception as e:
            logger.error(f"Error getting element count: {e}")
            raise
    
    async def get_element_by_index(self, selector: str, index: int, 
                                   selector_type: str = 'css') -> Locator:
        """获取指定索引的元素"""
        try:
            locator = self.page.locator(self._build_selector(selector, selector_type))
            return locator.nth(index)
        except Exception as e:
            logger.error(f"Error getting element by index: {e}")
            raise
    
    async def get_bounding_box(self, selector: str, selector_type: str = 'css') -> dict:
        """获取元素的边界框"""
        try:
            locator = await self.find_element(selector, selector_type)
            box = await locator.bounding_box()
            logger.info(f"Element bounding box: {selector} = {box}")
            return box
        except Exception as e:
            logger.error(f"Error getting bounding box: {e}")
            raise
    
    async def wait_for_visible(self, selector: str, selector_type: str = 'css', 
                               timeout: int = 10000):
        """等待元素可见"""
        try:
            locator = self.page.locator(self._build_selector(selector, selector_type))
            await locator.wait_for(state='visible', timeout=timeout)
            logger.info(f"Element visible: {selector}")
        except Exception as e:
            logger.error(f"Element not visible: {selector}, error: {e}")
            raise
    
    async def wait_for_hidden(self, selector: str, selector_type: str = 'css', 
                              timeout: int = 10000):
        """等待元素隐藏"""
        try:
            locator = self.page.locator(self._build_selector(selector, selector_type))
            await locator.wait_for(state='hidden', timeout=timeout)
            logger.info(f"Element hidden: {selector}")
        except Exception as e:
            logger.error(f"Element visibility timeout: {selector}, error: {e}")
            raise
    
    async def wait_for_enabled(self, selector: str, selector_type: str = 'css', 
                               timeout: int = 10000):
        """等待元素启用"""
        try:
            locator = self.page.locator(self._build_selector(selector, selector_type))
            await locator.wait_for(state='enabled', timeout=timeout)
            logger.info(f"Element enabled: {selector}")
        except Exception as e:
            logger.error(f"Element enable timeout: {selector}, error: {e}")
            raise
    
    async def wait_for_disabled(self, selector: str, selector_type: str = 'css', 
                                timeout: int = 10000):
        """等待元素禁用"""
        try:
            locator = self.page.locator(self._build_selector(selector, selector_type))
            # 使用 JavaScript 等待禁用状态
            await self.page.wait_for_function(
                f"() => document.querySelector('{selector}').disabled === true",
                timeout=timeout
            )
            logger.info(f"Element disabled: {selector}")
        except Exception as e:
            logger.error(f"Element disable timeout: {selector}, error: {e}")
            raise
    
    async def scroll_into_view(self, selector: str, selector_type: str = 'css'):
        """滚动元素到可见区域"""
        try:
            locator = await self.find_element(selector, selector_type)
            await locator.scroll_into_view_if_needed()
            logger.info(f"Element scrolled into view: {selector}")
        except Exception as e:
            logger.error(f"Error scrolling element: {e}")
            raise
    
    async def highlight_element(self, selector: str, selector_type: str = 'css'):
        """高亮显示元素（用于调试）"""
        try:
            await self.page.evaluate(f"""
                () => {{
                    const element = document.querySelector('{selector}');
                    if (element) {{
                        element.style.border = '3px solid red';
                    }}
                }}
            """)
            logger.info(f"Element highlighted: {selector}")
        except Exception as e:
            logger.error(f"Error highlighting element: {e}")
