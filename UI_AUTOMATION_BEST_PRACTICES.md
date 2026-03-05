# UI 自动化测试最佳实践指南

## 目录
1. [快速开始](#快速开始)
2. [最佳实践](#最佳实践)
3. [常见问题](#常见问题)
4. [性能优化](#性能优化)
5. [故障排除](#故障排除)

---

## 快速开始

### 1. 安装依赖
```bash
pip install playwright
playwright install chromium firefox webkit
```

### 2. 创建 UI 测试用例

#### 方式一：通过 Django Admin
1. 登录 Django Admin
2. 在 TestCase 中创建新用例
3. 设置 `test_type='ui'`，填写 `target_url`, `browser_type` 等字段
4. 保存

#### 方式二：通过代码
```python
from django.contrib.auth.models import User
from test_manager.model.models import TestCase, Project
from test_manager.model.ui_models import UITestStep

# 获取用户和项目
user = User.objects.get(username='admin')
project = Project.objects.get(id=1)

# 创建测试用例
test_case = TestCase.objects.create(
    name="登录测试",
    test_type="ui",
    target_url="https://example.com/login",
    project=project,
    created_by=user,
    browser_type='chromium',
    viewport_width=1280,
    viewport_height=720,
    headless=True
)

# 添加测试步骤
steps = [
    {
        'step_number': 1,
        'action_type': 'navigate',
        'action_value': 'https://example.com/login',
    },
    {
        'step_number': 2,
        'action_type': 'fill',
        'element_selector': '#username',
        'selector_type': 'css',
        'action_value': 'testuser',
    },
    {
        'step_number': 3,
        'action_type': 'fill',
        'element_selector': '#password',
        'selector_type': 'css',
        'action_value': 'password123',
    },
    {
        'step_number': 4,
        'action_type': 'click',
        'element_selector': '.login-button',
        'selector_type': 'css',
    },
    {
        'step_number': 5,
        'action_type': 'wait',
        'element_selector': '.welcome-message',
        'selector_type': 'css',
        'timeout': 10,
    },
    {
        'step_number': 6,
        'action_type': 'assert_text',
        'element_selector': '.welcome-message',
        'selector_type': 'css',
        'expected_result': 'Welcome',
    },
    {
        'step_number': 7,
        'action_type': 'screenshot',
    },
]

for step in steps:
    UITestStep.objects.create(test_case=test_case, **step)
```

### 3. 运行 UI 测试

#### 通过 REST API
```bash
curl -X POST \
  http://localhost:8000/api/test-cases/{test_case_id}/run/ \
  -H 'Content-Type: application/json' \
  -d '{
    "environment_id": 1
  }'
```

#### 通过 Python 代码
```python
import asyncio
from test_manager.automation.executors.ui_executor import UITestExecutor
from test_manager.model.models import TestCase, Environment

test_case = TestCase.objects.get(id=1)
environment = Environment.objects.get(id=1)

executor = UITestExecutor(test_case, environment, headless=True)
result = asyncio.run(executor.execute())

print(f"Status: {result['status']}")
print(f"Duration: {result['duration']:.2f}s")
print(f"Steps: {result['steps_passed']}/{result['steps_executed']}")
```

---

## 最佳实践

### 1. 元素定位最佳实践

#### ✅ 好的做法
```python
# 使用稳定的 ID
'#login-button'

# 使用 data-testid 属性
'[data-testid="submit-button"]'

# 使用有意义的类名
'.primary-button'

# 使用 ARIA 标签
'[aria-label="Close dialog"]'

# 文本定位（对于不变的文本）
'text=Login'
```

#### ❌ 避免
```python
# 深层 CSS 路径（易破损）
'div > div > div > button'

# 过于通用的选择器
'button'
'div'

# 复杂的 XPath
'/html/body/div[1]/div[2]/div[3]/button[4]'

# 依赖样式的属性
'[style="color: blue"]'
```

### 2. 等待策略

#### ✅ 明确等待
```python
# 等待元素可见
'action_type': 'wait',
'element_selector': '.loading-complete',
'timeout': 10

# 等待 URL 变化
'action_type': 'assert_url',
'expected_result': '/dashboard'

# 等待文本出现
'action_type': 'assert_text',
'element_selector': '.success-message',
'expected_result': 'Success'
```

#### ❌ 避免
```python
# 硬等待（绝不使用）
import time
time.sleep(5)  # ❌ 不要这样做
```

### 3. 测试数据管理

```python
# 使用环境变量存储敏感信息
import os

test_username = os.getenv('TEST_USERNAME', 'testuser')
test_password = os.getenv('TEST_PASSWORD', 'password123')

# 使用 action_value 传递参数
{
    'action_type': 'fill',
    'element_selector': '#username',
    'action_value': test_username
}
```

### 4. 错误处理

```python
# 在 UI 测试步骤中实现重试
{
    'step_number': 1,
    'action_type': 'click',
    'element_selector': '#flaky-button',
    'selector_type': 'css',
    'timeout': 10,  # Playwright 会自动重试 10 秒内的操作
}
```

### 5. 截图和调试

```python
# 在关键步骤后截图
{
    'step_number': 5,
    'action_type': 'screenshot',
},

# 在验证前截图用于调试
{
    'step_number': 4,
    'action_type': 'screenshot',
},
{
    'step_number': 5,
    'action_type': 'assert_text',
    'expected_result': 'Expected content'
}
```

### 6. 测试隔离

```python
# 每个测试应该独立，不依赖其他测试
# 使用 setUp 和 tearDown 清理数据

# 清理 cookie 和 session
{
    'step_number': 1,
    'action_type': 'navigate',
    'action_value': 'about:blank'  # 清空当前会话
},
{
    'step_number': 2,
    'action_type': 'navigate',
    'action_value': 'https://example.com'  # 开始新的干净测试
}
```

---

## 常见问题

### Q1: 测试运行缓慢，如何加快？

**A:** 使用以下策略：

1. 减少不必要的等待
```python
# ❌ 等待太长
'timeout': 60

# ✅ 使用合理的超时
'timeout': 10
```

2. 并行执行多个测试（如果可能）
```python
import asyncio

async def run_tests():
    tasks = [
        executor1.execute(),
        executor2.execute(),
        executor3.execute(),
    ]
    results = await asyncio.gather(*tasks)
    return results

results = asyncio.run(run_tests())
```

3. 使用 headless 模式
```python
# ✅ 推荐
executor = UITestExecutor(test_case, environment, headless=True)

# ❌ 较慢
executor = UITestExecutor(test_case, environment, headless=False)
```

### Q2: 如何处理动态内容和 AJAX 请求？

**A:** 使用显式等待：

```python
# 等待 AJAX 加载完成
{
    'step_number': 2,
    'action_type': 'click',
    'element_selector': 'Load Data',
},
{
    'step_number': 3,
    'action_type': 'wait',
    'element_selector': '.loading-spinner',
    'timeout': 15,
},
{
    'step_number': 4,
    'action_type': 'assert_visible',
    'element_selector': '.data-table',
}
```

### Q3: 如何处理多标签页和弹出窗口？

**A:** Playwright 自动处理弹出窗口：

```python
# Playwright 会自动跟踪弹出窗口
# 如果需要切换标签页，使用导航
{
    'step_number': 1,
    'action_type': 'click',
    'element_selector': '[target="_blank"]',
},
{
    'step_number': 2,
    'action_type': 'navigate',
    'action_value': 'https://example.com/new-page'
}
```

### Q4: 如何处理验证码？

**A:** 对于自动化测试，应该：

1. 在测试环境中禁用验证码
2. 使用 mock 的验证码服务
3. 使用测试账号绕过验证码

```python
# 登录跳过验证码的测试账号
{
    'step_number': 1,
    'action_type': 'fill',
    'element_selector': '#username',
    'action_value': 'test_user_no_captcha'  # 特殊测试账号
}
```

### Q5: 截图尺寸不对，如何调整？

**A:** 在创建测试用例时设置视口：

```python
test_case = TestCase.objects.create(
    # ...其他字段
    viewport_width=1920,  # 设置宽度
    viewport_height=1080,  # 设置高度
)
```

---

## 性能优化

### 1. 浏览器实例重用

```python
# 考虑创建会话以重用浏览器实例
# （适用于执行多个相关测试）

async def run_related_tests(test_cases):
    driver = PlaywrightBrowserDriver()
    await driver.launch()
    
    try:
        for test_case in test_cases:
            # 重用同一浏览器实例
            executor = UITestExecutor(test_case)
            executor.driver = driver  # 重用浏览器
            result = await executor.execute()
    finally:
        await driver.close()
```

### 2. 资源清理

```python
# 定期清理截图和视频
import os
from pathlib import Path

def cleanup_old_artifacts(days=7):
    from datetime import datetime, timedelta
    
    cutoff = datetime.now() - timedelta(days=days)
    
    # 清理截图
    for file_path in Path('screenshots').glob('*'):
        if file_path.stat().st_mtime < cutoff.timestamp():
            file_path.unlink()
```

### 3. 网络优化

```python
# 屏蔽不必要的资源加载（如广告、分析）
# 这可以加快页面加载

# 在执行器中实现：
async def intercept_requests(driver):
    blocked_patterns = [
        '**/analytics**',
        '**/ads/**',
        '**/tracking/**'
    ]
    
    async def route_handler(route):
        if any(pattern in route.request.url for pattern in blocked_patterns):
            await route.abort()
        else:
            await route.continue_()
    
    for pattern in blocked_patterns:
        await driver.page.route(pattern, route_handler)
```

---

## 故障排除

### 问题 1: "元素未找到"

**原因：**
- 选择器不正确
- 元素加载不完全
- 元素在不可见的区域

**解决方案：**
```python
# 1. 验证选择器
# 在浏览器控制台使用：
# document.querySelector('.selector')  // 应该返回元素

# 2. 增加等待时间
'timeout': 15  # 增加超时

# 3. 滚动到元素
{
    'step_number': 1,
    'action_type': 'scroll',
    'action_value': json.dumps({'x': 0, 'y': 500})
}
```

### 问题 2: 间歇性失败（flaky tests）

**原因：**
- 网络延迟
- 动画或过渡
- 异步加载

**解决方案：**
```python
# 1. 增加等待时间
'timeout': 15

# 2. 等待具体条件
{
    'action_type': 'wait',
    'element_selector': '.content-loaded'
}

# 3. 添加隐式延迟
executor = UITestExecutor(test_case, slow_mo=500)  # 每个操作延迟 500ms
```

### 问题 3: 性能测试失败

**调试步骤：**
```python
# 1. 收集性能指标
result = asyncio.run(executor.execute())
metrics = result.get('page_metrics', {})
print(f"Page Load Time: {metrics.get('pageLoadTime', 'N/A')}ms")
print(f"FCP: {metrics.get('fcp', 'N/A')}ms")
print(f"LCP: {metrics.get('lcp', 'N/A')}ms")

# 2. 使用浏览器开发者工具
# 在 headless=False 模式下手动测试
executor = UITestExecutor(test_case, headless=False)
```

### 问题 4: 内存泄漏

**症状：** 运行多个测试后内存占用持续增长

**解决方案：**
```python
# 1. 确保浏览器正确关闭
finally:
    await driver.close()

# 2. 清理大量截图
def cleanup_screenshots():
    import os
    for file in os.listdir('screenshots'):
        os.remove(os.path.join('screenshots', file))

# 3. 定期重启浏览器
# 每 N 个测试后重启一次
if test_count % 100 == 0:
    await driver.close()
    await driver.launch()
```

---

## 日志和调试

### 启用详细日志

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('test_manager.automation')
logger.setLevel(logging.DEBUG)
```

### 保存执行日志

```python
# 自动保存到文件
import logging.handlers

handler = logging.handlers.RotatingFileHandler(
    'ui_tests.log',
    maxBytes=10485760,  # 10MB
    backupCount=5
)
logger.addHandler(handler)
```

---

## 总结

| 特性 | 最佳实践 |
|------|--------|
| **选择器** | 使用稳定的 ID/类名，避免深层路径 |
| **等待** | 使用明确等待，避免硬等待 |
| **性能** | 使用 headless 模式，并行执行 |
| **调试** | 保存截图和日志，启用详细模式 |
| **维护** | 定期更新选择器，清理旧数据 |

遵循这些最佳实践，可以构建高效、稳定、易维护的 UI 自动化测试！
