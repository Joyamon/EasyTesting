import logging
import time
import json
from typing import Dict, Any, List
from datetime import datetime

from test_manager.automation.drivers.playwright_driver import PlaywrightBrowserDriver
from test_manager.automation.locators.element_locator import ElementLocator, ElementNotFoundError
from test_manager.utils.notification import create_ui_test_notification

logger = logging.getLogger(__name__)


class UITestExecutor:
    """UI 测试执行器
    
    负责执行 UI 自动化测试，包括页面导航、元素交互、验证等
    """
    
    # 动作处理器映射
    ACTION_HANDLERS = {}
    
    def __init__(self, test_case, environment=None, headless=True, slow_mo=0):
        """初始化 UI 测试执行器
        
        Args:
            test_case: TestCase 对象
            environment: Environment 对象
            headless: 是否无头模式
            slow_mo: 慢动作延迟（毫秒）
        """
        self.test_case = test_case
        self.environment = environment
        self.headless = headless
        self.slow_mo = slow_mo
        
        self.driver = None
        self.locator = None
        self.step_results = []
        self.screenshots = []
        self.start_time = None
        self.end_time = None
        self.page_metrics = {}
    
    async def execute(self) -> Dict[str, Any]:
        """执行 UI 测试
        
        Returns:
            包含测试结果的字典
        """
        self.start_time = time.time()
        
        try:
            # 初始化浏览器
            await self._setup_browser()
            
            # 获取测试步骤
            steps = self.test_case.ui_steps.all().order_by('step_number')
            
            if not steps.exists():
                logger.warning(f"No UI steps found for test case: {self.test_case.name}")
                return self._create_result('failed', error_message='No UI steps defined')
            
            # 执行所有步骤
            for step in steps:
                try:
                    await self._execute_step(step)
                except Exception as e:
                    logger.error(f"Step {step.step_number} failed: {e}")
                    self.step_results.append({
                        'step_number': step.step_number,
                        'action_type': step.action_type,
                        'status': 'failed',
                        'error': str(e)
                    })
            
            # 获取页面性能指标
            try:
                self.page_metrics = await self.driver.get_page_metrics()
            except Exception as e:
                logger.warning(f"Failed to collect page metrics: {e}")
            
            # 判断整体状态
            has_failures = any(r['status'] == 'failed' for r in self.step_results)
            status = 'failed' if has_failures else 'passed'
            
            return self._create_result(status)
        
        except Exception as e:
            logger.exception(f"Test execution error: {e}")
            return self._create_result('error', error_message=str(e))
        
        finally:
            self.end_time = time.time()
            await self._teardown_browser()
    
    async def _setup_browser(self):
        """设置浏览器"""
        try:
            browser_type = getattr(self.test_case, 'browser_type', 'chromium')
            viewport = {
                'width': getattr(self.test_case, 'viewport_width', 1280),
                'height': getattr(self.test_case, 'viewport_height', 720)
            }
            
            self.driver = PlaywrightBrowserDriver(
                browser_type=browser_type,
                headless=self.headless,
                viewport=viewport,
                slow_mo=self.slow_mo
            )
            
            await self.driver.launch()
            self.locator = ElementLocator(self.driver.page)
            logger.info(f"Browser setup completed: {browser_type}")
        
        except Exception as e:
            logger.error(f"Browser setup failed: {e}")
            raise
    
    async def _execute_step(self, step):
        """执行单个步骤"""
        step_start_time = time.time()
        
        try:
            action_type = step.action_type
            
            # 获取对应的处理器
            handler = getattr(self, f'_handle_{action_type}', None)
            if not handler:
                raise ValueError(f"Unsupported action type: {action_type}")
            
            # 执行处理器
            await handler(step)
            
            step_duration = time.time() - step_start_time
            
            # 记录成功的步骤
            self.step_results.append({
                'step_number': step.step_number,
                'action_type': action_type,
                'status': 'passed',
                'duration': step_duration,
                'timestamp': datetime.now().isoformat()
            })
            
            logger.info(f"Step {step.step_number} ({action_type}) passed ({step_duration:.2f}s)")
        
        except Exception as e:
            step_duration = time.time() - step_start_time
            logger.error(f"Step {step.step_number} failed: {e}")
            raise
    
    async def _handle_navigate(self, step):
        """处理导航动作"""
        url = step.action_value
        if not url:
            raise ValueError("URL is required for navigate action")
        
        await self.driver.navigate(url)
    
    async def _handle_click(self, step):
        """处理点击动作"""
        locator = await self.locator.find_element(
            step.element_selector,
            step.selector_type,
            step.timeout * 1000
        )
        await locator.click()
        logger.info(f"Clicked on element: {step.element_selector}")
    
    async def _handle_double_click(self, step):
        """处理双击动作"""
        locator = await self.locator.find_element(
            step.element_selector,
            step.selector_type,
            step.timeout * 1000
        )
        await locator.dblclick()
        logger.info(f"Double clicked on element: {step.element_selector}")
    
    async def _handle_right_click(self, step):
        """处理右击动作"""
        locator = await self.locator.find_element(
            step.element_selector,
            step.selector_type,
            step.timeout * 1000
        )
        await locator.click(button='right')
        logger.info(f"Right clicked on element: {step.element_selector}")
    
    async def _handle_fill(self, step):
        """处理文本输入动作"""
        value = step.action_value
        if value is None:
            raise ValueError("Value is required for fill action")
        
        locator = await self.locator.find_element(
            step.element_selector,
            step.selector_type,
            step.timeout * 1000
        )
        await locator.fill(str(value))
        logger.info(f"Filled text in element: {step.element_selector} = {value}")
    
    async def _handle_select(self, step):
        """处理选择动作"""
        value = step.action_value
        if value is None:
            raise ValueError("Value is required for select action")
        
        locator = await self.locator.find_element(
            step.element_selector,
            step.selector_type,
            step.timeout * 1000
        )
        await locator.select_option(str(value))
        logger.info(f"Selected option in element: {step.element_selector} = {value}")
    
    async def _handle_hover(self, step):
        """处理鼠标悬停动作"""
        locator = await self.locator.find_element(
            step.element_selector,
            step.selector_type,
            step.timeout * 1000
        )
        await locator.hover()
        logger.info(f"Hovered on element: {step.element_selector}")
    
    async def _handle_wait(self, step):
        """处理等待动作"""
        await self.locator.wait_for_visible(
            step.element_selector,
            step.selector_type,
            step.timeout * 1000
        )
        logger.info(f"Waited for element: {step.element_selector}")
    
    async def _handle_assert_visible(self, step):
        """处理可见性验证"""
        is_visible = await self.locator.is_visible(
            step.element_selector,
            step.selector_type,
            step.timeout * 1000
        )
        
        if not is_visible:
            raise AssertionError(f"Element not visible: {step.element_selector}")
        
        logger.info(f"Assertion passed: element visible {step.element_selector}")
    
    async def _handle_assert_text(self, step):
        """处理文本验证"""
        expected_text = step.expected_result
        if expected_text is None:
            raise ValueError("Expected result is required for assert_text action")
        
        try:
            actual_text = await self.locator.get_text(
                step.element_selector,
                step.selector_type
            )
            
            if expected_text not in actual_text:
                raise AssertionError(
                    f"Text assertion failed: expected '{expected_text}' in '{actual_text}'"
                )
            
            logger.info(f"Assertion passed: text contains '{expected_text}'")
        
        except ElementNotFoundError:
            raise AssertionError(f"Element not found: {step.element_selector}")
    
    async def _handle_assert_url(self, step):
        """处理 URL 验证"""
        expected_url = step.expected_result
        if expected_url is None:
            raise ValueError("Expected result is required for assert_url action")
        
        current_url = await self.driver.get_current_url()
        
        if expected_url not in current_url:
            raise AssertionError(
                f"URL assertion failed: expected '{expected_url}' in '{current_url}'"
            )
        
        logger.info(f"Assertion passed: URL contains '{expected_url}'")
    
    async def _handle_screenshot(self, step):
        """处理截图动作"""
        path = f"screenshots/test_{self.test_case.id}_step_{step.step_number}.png"
        try:
            await self.driver.screenshot(path)
            self.screenshots.append(path)
            logger.info(f"Screenshot saved: {path}")
        except Exception as e:
            logger.error(f"Screenshot failed: {e}")
            # 不中断执行，仅记录错误
    
    async def _handle_scroll(self, step):
        """处理滚动动作"""
        value = step.action_value
        if value is None:
            raise ValueError("Value is required for scroll action")
        
        try:
            coords = json.loads(value)
            x = coords.get('x', 0)
            y = coords.get('y', 0)
        except (json.JSONDecodeError, TypeError):
            # 尝试解析为 y 坐标
            try:
                y = int(value)
                x = 0
            except ValueError:
                raise ValueError(f"Invalid scroll value: {value}")
        
        await self.driver.scroll_to(x, y)
        logger.info(f"Scrolled to position: ({x}, {y})")
    
    async def _handle_keyboard(self, step):
        """处理键盘动作"""
        key = step.action_value
        if key is None:
            raise ValueError("Key is required for keyboard action")
        
        await self.driver.page.keyboard.press(key)
        logger.info(f"Pressed key: {key}")
    
    async def _handle_upload_file(self, step):
        """处理文件上传"""
        file_path = step.action_value
        if file_path is None:
            raise ValueError("File path is required for upload_file action")
        
        locator = await self.locator.find_element(
            step.element_selector,
            step.selector_type,
            step.timeout * 1000
        )
        await locator.set_input_files(file_path)
        logger.info(f"File uploaded: {file_path}")
    
    async def _teardown_browser(self):
        """关闭浏览器"""
        try:
            if self.driver:
                await self.driver.close()
            logger.info("Browser closed successfully")
        except Exception as e:
            logger.error(f"Error closing browser: {e}")
    
    def _create_result(self, status: str, error_message: str = '') -> Dict[str, Any]:
        """创建测试结果字典
        
        Args:
            status: 测试状态 (passed, failed, error)
            error_message: 错误信息
        
        Returns:
            结果字典
        """
        duration = (self.end_time - self.start_time) if self.end_time else (time.time() - self.start_time)
        
        result = {
            'status': status,
            'duration': duration,
            'steps_executed': len(self.step_results),
            'steps_passed': sum(1 for r in self.step_results if r['status'] == 'passed'),
            'steps_failed': sum(1 for r in self.step_results if r['status'] == 'failed'),
            'screenshots': self.screenshots,
            'step_details': self.step_results,
            'page_metrics': self.page_metrics,
        }
        
        if error_message:
            result['error_message'] = error_message
        else:
            error_messages = [r.get('error') for r in self.step_results if r.get('error')]
            if error_messages:
                result['error_message'] = '\n'.join(error_messages)
        
        return result
    
    def get_summary(self) -> str:
        """获取测试执行摘要"""
        total_steps = len(self.step_results)
        passed_steps = sum(1 for r in self.step_results if r['status'] == 'passed')
        failed_steps = sum(1 for r in self.step_results if r['status'] == 'failed')
        
        return (
            f"Test: {self.test_case.name}\n"
            f"Total Steps: {total_steps}\n"
            f"Passed: {passed_steps}\n"
            f"Failed: {failed_steps}\n"
            f"Duration: {time.time() - self.start_time:.2f}s"
        )
