# EasyTesting UI 自动化设计方案

## 一、系统现状分析

### 1.1 现有架构概览
```
当前系统架构：
├── API 测试模块（已完全实现）
│   ├── 数据模型：Project, Environment, TestCase, TestSuite, TestRun, TestResult
│   ├── 执行引擎：httprunner_executor.py（基于 HTTP 请求）
│   ├── REST API：test_manager/api/views.py
│   └── 测试流程：单条/批量执行、结果收集、参数提取
├── 数据库：Django ORM + PostgreSQL
├── 前端：Django Template + Bootstrap
└── 通知系统：Notification 模型 + 实时推送
```

### 1.2 API 测试功能现状
- ✅ 支持多种 HTTP 方法（GET, POST, PUT, DELETE, PATCH）
- ✅ 请求头、请求体、响应验证
- ✅ 参数提取和变量替换
- ✅ 测试套件（批量执行）
- ✅ 结果统计和报告

### 1.3 UI 自动化需求空白
- ❌ 没有 Web UI 测试能力
- ❌ 没有浏览器交互能力
- ❌ 没有页面元素定位机制
- ❌ 没有动态内容验证能力
- ❌ 没有截图和可视化测试

---

## 二、UI 自动化最佳实践方案

### 2.1 核心设计原则

#### 原则一：轻耦合架构
- UI 测试模块独立于 API 测试
- 共享数据模型和执行框架
- 通过公共接口完成集成

#### 原则二：模块化设计
```
UI 自动化模块结构：
test_manager/
├── automation/                    # UI 自动化新模块
│   ├── __init__.py
│   ├── drivers/                   # 浏览器驱动管理
│   │   ├── __init__.py
│   │   ├── playwright_driver.py   # Playwright 驱动实现
│   │   └── browser_factory.py     # 浏览器工厂类
│   ├── executors/                 # 执行器
│   │   ├── __init__.py
│   │   ├── ui_executor.py         # UI 测试执行引擎
│   │   └── action_executor.py     # 动作执行器
│   ├── locators/                  # 元素定位
│   │   ├── __init__.py
│   │   ├── element_locator.py     # 元素定位器
│   │   └── locator_strategies.py  # 定位策略（CSS, XPath, 等）
│   ├── actions/                   # 测试动作
│   │   ├── __init__.py
│   │   ├── base_actions.py        # 基础动作（点击、输入等）
│   │   ├── advanced_actions.py    # 高级动作（等待、滚动等）
│   │   └── validation_actions.py  # 验证动作
│   ├── utils/                     # 工具函数
│   │   ├── __init__.py
│   │   ├── screenshot.py          # 截图管理
│   │   ├── video.py               # 视频录制
│   │   └── performance.py         # 性能指标
│   └── config.py                  # 配置文件
```

#### 原则三：数据驱动
- UI 测试步骤从数据库读取
- 支持参数化测试
- 易于维护和管理

### 2.2 数据模型设计

#### 扩展 TestCase 模型
```python
# 增加 UI 测试特定字段
class TestCase(models.Model):
    # 现有字段...
    
    # UI 测试字段
    test_type = models.CharField(
        max_length=20,
        choices=[('api', 'API'), ('ui', 'UI')],
        default='api'
    )
    target_url = models.URLField(
        null=True, blank=True,  # UI 测试的目标 URL
        help_text="UI 测试的目标 URL"
    )
    browser_type = models.CharField(
        max_length=20,
        choices=[('chromium', 'Chromium'), ('firefox', 'Firefox'), ('webkit', 'WebKit')],
        default='chromium'
    )
    viewport_width = models.IntegerField(default=1280)
    viewport_height = models.IntegerField(default=720)
    headless = models.BooleanField(default=True, help_text="是否无头模式")
```

#### 新增 UITestStep 模型
```python
class UITestStep(models.Model):
    """UI 测试步骤模型"""
    ACTION_TYPES = [
        ('navigate', '导航到页面'),
        ('click', '点击元素'),
        ('fill', '输入文本'),
        ('select', '选择选项'),
        ('hover', '鼠标悬停'),
        ('wait', '等待元素'),
        ('assert_visible', '验证可见'),
        ('assert_text', '验证文本'),
        ('assert_url', '验证 URL'),
        ('screenshot', '截图'),
        ('scroll', '滚动'),
        ('keyboard', '键盘操作'),
    ]
    
    test_case = models.ForeignKey(TestCase, on_delete=models.CASCADE, related_name='ui_steps')
    step_number = models.IntegerField(help_text="步骤序号")
    action_type = models.CharField(max_length=20, choices=ACTION_TYPES)
    element_selector = models.CharField(max_length=500, help_text="CSS/XPath 选择器")
    selector_type = models.CharField(
        max_length=10,
        choices=[('css', 'CSS'), ('xpath', 'XPath'), ('id', 'ID'), ('text', 'Text')],
        default='css'
    )
    action_value = models.TextField(null=True, blank=True, help_text="动作值（如输入的文本）")
    expected_result = models.TextField(null=True, blank=True, help_text="预期结果")
    timeout = models.IntegerField(default=10, help_text="超时时间（秒）")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

#### 新增 UITestResult 模型
```python
class UITestResult(models.Model):
    """UI 测试结果模型"""
    test_run = models.ForeignKey(TestRun, on_delete=models.CASCADE, related_name='ui_results')
    test_case = models.ForeignKey(TestCase, on_delete=models.CASCADE)
    environment = models.ForeignKey(Environment, on_delete=models.SET_NULL, null=True)
    
    status = models.CharField(max_length=20, choices=[('passed', '通过'), ('failed', '失败'), ('error', '错误')])
    duration = models.FloatField(help_text="执行时间（秒）")
    error_message = models.TextField(blank=True)
    
    # 执行详情
    steps_executed = models.IntegerField(default=0)
    steps_passed = models.IntegerField(default=0)
    steps_failed = models.IntegerField(default=0)
    
    # 截图和视频
    screenshots = models.JSONField(default=list, help_text="截图路径列表")
    video_path = models.FileField(upload_to='ui_test_videos/', null=True, blank=True)
    
    # 性能指标
    page_load_time = models.FloatField(null=True, blank=True)
    first_contentful_paint = models.FloatField(null=True, blank=True)
    largest_contentful_paint = models.FloatField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
```

---

## 三、核心模块实现

### 3.1 浏览器驱动管理

```python
# test_manager/automation/drivers/playwright_driver.py

class PlaywrightBrowserDriver:
    """Playwright 浏览器驱动"""
    
    def __init__(self, browser_type='chromium', headless=True, viewport=None):
        self.browser_type = browser_type
        self.headless = headless
        self.viewport = viewport or {'width': 1280, 'height': 720}
        self.browser = None
        self.context = None
        self.page = None
    
    async def launch(self):
        """启动浏览器"""
        from playwright.async_api import async_playwright
        
        self.playwright = await async_playwright().start()
        
        browser_launcher = getattr(self.playwright, self.browser_type)
        self.browser = await browser_launcher.launch(headless=self.headless)
        self.context = await self.browser.new_context(viewport=self.viewport)
        self.page = await self.context.new_page()
    
    async def close(self):
        """关闭浏览器"""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
    
    async def navigate(self, url):
        """导航到 URL"""
        return await self.page.goto(url, wait_until='networkidle')
    
    async def screenshot(self, path):
        """截图"""
        return await self.page.screenshot(path=path)
    
    async def get_page_metrics(self):
        """获取页面性能指标"""
        metrics = await self.page.evaluate("""
            () => {
                const paint = window.performance.getEntriesByType('paint');
                const navigation = window.performance.getEntriesByType('navigation')[0];
                return {
                    pageLoadTime: navigation?.loadEventEnd,
                    FCP: paint.find(e => e.name === 'first-contentful-paint')?.startTime,
                    LCP: paint.find(e => e.name === 'largest-contentful-paint')?.startTime,
                }
            }
        """)
        return metrics
```

### 3.2 元素定位和操作

```python
# test_manager/automation/locators/element_locator.py

class ElementLocator:
    """元素定位器"""
    
    def __init__(self, page):
        self.page = page
    
    async def find_element(self, selector, selector_type='css', timeout=10000):
        """查找单个元素"""
        try:
            locator = self._get_locator(selector, selector_type)
            await locator.wait_for(timeout=timeout)
            return locator
        except Exception as e:
            raise ElementNotFoundError(f"Element not found: {selector}")
    
    async def find_elements(self, selector, selector_type='css'):
        """查找多个元素"""
        locator = self._get_locator(selector, selector_type)
        return locator
    
    def _get_locator(self, selector, selector_type):
        """根据类型返回定位器"""
        if selector_type == 'css':
            return self.page.locator(selector)
        elif selector_type == 'xpath':
            return self.page.locator(f'xpath={selector}')
        elif selector_type == 'id':
            return self.page.locator(f'#{selector}')
        elif selector_type == 'text':
            return self.page.locator(f'text={selector}')
        else:
            raise ValueError(f"Unsupported selector type: {selector_type}")
    
    async def is_visible(self, selector, selector_type='css', timeout=10000):
        """检查元素是否可见"""
        try:
            locator = await self.find_element(selector, selector_type, timeout)
            return await locator.is_visible()
        except:
            return False
    
    async def get_text(self, selector, selector_type='css'):
        """获取元素文本"""
        locator = await self.find_element(selector, selector_type)
        return await locator.inner_text()
    
    async def get_attribute(self, selector, attr_name, selector_type='css'):
        """获取元素属性"""
        locator = await self.find_element(selector, selector_type)
        return await locator.get_attribute(attr_name)
```

### 3.3 UI 测试执行器

```python
# test_manager/automation/executors/ui_executor.py

class UITestExecutor:
    """UI 测试执行器"""
    
    def __init__(self, test_case, environment, headless=True):
        self.test_case = test_case
        self.environment = environment
        self.headless = headless
        self.driver = None
        self.results = []
        self.screenshots = []
    
    async def execute(self):
        """执行 UI 测试"""
        try:
            # 初始化浏览器
            await self._setup_browser()
            
            # 执行测试步骤
            start_time = time.time()
            for step in self.test_case.ui_steps.all().order_by('step_number'):
                await self._execute_step(step)
            
            duration = time.time() - start_time
            
            # 收集结果
            return {
                'status': 'passed' if not self._has_failures() else 'failed',
                'duration': duration,
                'steps_executed': len(self.results),
                'steps_passed': sum(1 for r in self.results if r['status'] == 'passed'),
                'steps_failed': sum(1 for r in self.results if r['status'] == 'failed'),
                'error_message': self._get_error_messages(),
                'screenshots': self.screenshots,
                'page_metrics': self._page_metrics
            }
        except Exception as e:
            return {
                'status': 'error',
                'error_message': str(e),
                'screenshots': self.screenshots
            }
        finally:
            await self._teardown_browser()
    
    async def _setup_browser(self):
        """设置浏览器"""
        self.driver = PlaywrightBrowserDriver(
            browser_type=self.test_case.browser_type,
            headless=self.headless,
            viewport={
                'width': self.test_case.viewport_width,
                'height': self.test_case.viewport_height
            }
        )
        await self.driver.launch()
    
    async def _execute_step(self, step):
        """执行单个测试步骤"""
        try:
            if step.action_type == 'navigate':
                await self.driver.navigate(step.action_value)
                self.results.append({'step': step.step_number, 'status': 'passed'})
            
            elif step.action_type == 'click':
                locator = await self._find_element(step)
                await locator.click()
                self.results.append({'step': step.step_number, 'status': 'passed'})
            
            elif step.action_type == 'fill':
                locator = await self._find_element(step)
                await locator.fill(step.action_value)
                self.results.append({'step': step.step_number, 'status': 'passed'})
            
            elif step.action_type == 'wait':
                await self.driver.page.wait_for_selector(step.element_selector, timeout=step.timeout * 1000)
                self.results.append({'step': step.step_number, 'status': 'passed'})
            
            elif step.action_type == 'assert_text':
                locator = await self._find_element(step)
                text = await locator.inner_text()
                if step.expected_result in text:
                    self.results.append({'step': step.step_number, 'status': 'passed'})
                else:
                    self.results.append({'step': step.step_number, 'status': 'failed'})
            
            elif step.action_type == 'screenshot':
                path = f"screenshots/{self.test_case.id}_{step.step_number}.png"
                await self.driver.screenshot(path)
                self.screenshots.append(path)
                self.results.append({'step': step.step_number, 'status': 'passed'})
        
        except Exception as e:
            self.results.append({'step': step.step_number, 'status': 'failed', 'error': str(e)})
    
    async def _find_element(self, step):
        """查找元素"""
        locator = ElementLocator(self.driver.page)
        return await locator.find_element(step.element_selector, step.selector_type, step.timeout * 1000)
    
    async def _teardown_browser(self):
        """关闭浏览器"""
        if self.driver:
            await self.driver.close()
    
    def _has_failures(self):
        """检查是否有失败"""
        return any(r['status'] == 'failed' for r in self.results)
    
    def _get_error_messages(self):
        """获取错误信息"""
        errors = [r.get('error') for r in self.results if r.get('error')]
        return '\n'.join(errors) if errors else ''
```

### 3.4 API 集成

```python
# test_manager/api/views.py 中新增

from ..automation.executors.ui_executor import UITestExecutor

class TestCaseViewSet(viewsets.ModelViewSet):
    # 现有代码...
    
    @action(detail=True, methods=['post'])
    def run(self, request, pk=None):
        """运行测试（支持 API 和 UI）"""
        test_case = self.get_object()
        environment_id = request.data.get('environment_id')
        
        if not environment_id:
            return Response({"error": "Environment ID is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        environment = get_object_or_404(Environment, id=environment_id)
        
        # 创建测试运行记录
        test_run = TestRun.objects.create(
            name=f"{'UI' if test_case.test_type == 'ui' else 'API'} run: {test_case.name}",
            project=test_case.project,
            environment=environment,
            status='running',
            start_time=timezone.now(),
            created_by=request.user
        )
        
        try:
            if test_case.test_type == 'api':
                # 执行 API 测试（现有逻辑）
                result = execute_test_case(test_case, environment)
                status_code = 'completed' if result['status'] == 'passed' else 'failed'
            else:
                # 执行 UI 测试
                import asyncio
                executor = UITestExecutor(test_case, environment, headless=True)
                result = asyncio.run(executor.execute())
                status_code = 'completed' if result['status'] == 'passed' else 'failed'
                
                # 创建 UI 测试结果
                UITestResult.objects.create(
                    test_run=test_run,
                    test_case=test_case,
                    environment=environment,
                    status=result['status'],
                    duration=result.get('duration', 0),
                    steps_executed=result.get('steps_executed', 0),
                    steps_passed=result.get('steps_passed', 0),
                    steps_failed=result.get('steps_failed', 0),
                    error_message=result.get('error_message', ''),
                    screenshots=result.get('screenshots', [])
                )
            
            test_run.status = status_code
            test_run.end_time = timezone.now()
            test_run.save()
            
            return Response({
                'test_run_id': test_run.id,
                'status': status_code,
                'result': result
            })
        
        except Exception as e:
            test_run.status = 'error'
            test_run.end_time = timezone.now()
            test_run.save()
            
            return Response({
                'error': str(e),
                'test_run_id': test_run.id
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
```

---

## 四、最佳实践

### 4.1 元素定位最佳实践
```python
# ✅ 优先使用稳定的选择器
好的选择器：
- CSS: `.login-button`
- ID: `#submit-btn`
- text: `text=Login`

# ❌ 避免使用不稳定的选择器
坏的选择器：
- `div > div > div > button`
- `/html/body/div[1]/div[2]/div[3]`
```

### 4.2 等待策略
```python
# ✅ 隐式等待
await locator.wait_for(timeout=10000)

# ✅ 显式等待
await page.wait_for_selector('#element', timeout=10000)

# ❌ 避免硬性等待
# time.sleep(5)  # 不要这样做
```

### 4.3 截图和调试
```python
# 自动在失败时截图
if step fails:
    await driver.screenshot(f"failure_{step_id}.png")

# 保存执行日志用于调试
logger.debug(f"Step {step_id}: {action_type} on {selector}")
```

### 4.4 性能考虑
```python
# 并发执行不相关的测试
# 使用异步执行器并行运行多个浏览器实例

# 资源管理
# - 总是关闭浏览器
# - 清理临时文件
# - 定期清理旧截图
```

### 4.5 稳定性提升
```python
# 1. 随机等待：减少时序问题
await asyncio.sleep(random.uniform(0.5, 1.5))

# 2. 重试机制：处理间歇性失败
max_retries = 3
for attempt in range(max_retries):
    try:
        await action()
        break
    except Exception as e:
        if attempt == max_retries - 1:
            raise

# 3. 视觉回归测试：对比截图
# 使用图像对比库检测 UI 变化
```

---

## 五、实现路线图

### 第一阶段：基础设施（优先级：高）
- [ ] 实现 PlaywrightBrowserDriver
- [ ] 实现 ElementLocator
- [ ] 扩展数据模型（UITestStep, UITestResult）
- [ ] 实现基础 UITestExecutor

### 第二阶段：核心功能（优先级：高）
- [ ] 实现所有基础动作（点击、输入、选择）
- [ ] 实现所有断言动作（验证文本、URL）
- [ ] 实现截图和日志
- [ ] REST API 集成

### 第三阶段：高级功能（优先级：中）
- [ ] 视频录制
- [ ] 性能指标收集
- [ ] 并发执行
- [ ] 高级等待策略

### 第四阶段：优化和完善（优先级：中）
- [ ] 视觉回归测试
- [ ] 跨浏览器测试
- [ ] 测试报告增强
- [ ] 前端 UI 完善

---

## 六、集成指南

### 6.1 数据库迁移
```bash
python manage.py makemigrations test_manager
python manage.py migrate test_manager
```

### 6.2 依赖安装
```bash
pip install playwright
playwright install chromium firefox webkit
```

### 6.3 快速开始
```python
# 创建 UI 测试用例
test_case = TestCase.objects.create(
    name="登录测试",
    test_type="ui",
    target_url="https://example.com",
    project=project,
    created_by=user
)

# 创建测试步骤
UITestStep.objects.create(
    test_case=test_case,
    step_number=1,
    action_type="navigate",
    action_value="https://example.com/login"
)

UITestStep.objects.create(
    test_case=test_case,
    step_number=2,
    action_type="fill",
    element_selector="#username",
    selector_type="css",
    action_value="testuser"
)

UITestStep.objects.create(
    test_case=test_case,
    step_number=3,
    action_type="click",
    element_selector=".login-button",
    selector_type="css"
)

UITestStep.objects.create(
    test_case=test_case,
    step_number=4,
    action_type="assert_visible",
    element_selector=".welcome-message",
    selector_type="css",
    expected_result="Welcome"
)
```

---

## 七、技术栈对比

| 特性 | Playwright | Selenium | Puppeteer |
|------|-----------|----------|-----------|
| 语言 | Python, JS, Java | Python, Java | JS |
| 浏览器 | Chromium, Firefox, WebKit | 多种 | Chromium |
| 异步支持 | ✅ | ❌ | ✅ |
| 性能 | 快 | 较慢 | 快 |
| 学习曲线 | 平缓 | 陡峭 | 中等 |
| **我们的选择** | **✅ 推荐** | ❌ | ⚠️ JS Only |

---

## 八、常见问题解答

### Q1: 如何处理动态内容？
A: 使用 wait_for_selector 或 wait_for_function 等待元素加载后再操作。

### Q2: 如何处理跨域问题？
A: Playwright 默认处理跨域，无需额外配置。

### Q3: 如何提高测试稳定性？
A: 
- 使用更稳定的定位器
- 实现智能等待
- 添加重试机制
- 定期更新页面选择器

### Q4: 如何进行调试？
A: 
```python
# 启用调试模式
PLAYWRIGHT_DEBUG = True

# 使用 inspector
playwright inspect ...

# 保存执行日志
logger.info(f"Step {step_id}: {action}")
```

---

## 九、安全考虑

1. **敏感数据保护**
   - 不要将密码存储在代码中
   - 使用环境变量或密钥管理系统
   - 对截图进行脱敏处理

2. **浏览器沙箱**
   - 每个测试独立浏览器实例
   - 定期清理临时数据
   - 防止状态泄漏

3. **资源限制**
   - 设置执行超时
   - 限制并发浏览器数量
   - 定期清理旧结果

