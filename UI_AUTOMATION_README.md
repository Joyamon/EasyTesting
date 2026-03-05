# EasyTesting UI 自动化测试框架

基于 Playwright 的企业级 UI 自动化测试框架，完全集成于 EasyTesting 系统。

## 快速导航

| 文档 | 用途 |
|------|------|
| 📋 [实现总结](UI_AUTOMATION_SUMMARY.md) | **开始这里** - 了解整体实现 |
| 🚀 [集成指南](UI_AUTOMATION_INTEGRATION.md) | 部署和配置步骤 |
| 📖 [最佳实践](UI_AUTOMATION_BEST_PRACTICES.md) | 使用建议和常见问题 |
| 🏗️ [架构设计](UI_AUTOMATION_ARCHITECTURE.md) | 深入的技术细节 |

## 🎯 核心特性

- ✅ **完整的 UI 测试框架** - 数据驱动的测试定义
- ✅ **Playwright 核心** - 快速、可靠、跨浏览器
- ✅ **无缝集成** - 与现有 API 测试框架兼容
- ✅ **15+ 操作类型** - 覆盖大多数 UI 操作
- ✅ **企业级功能** - 性能监控、截图、日志
- ✅ **异步执行** - 支持并发测试
- ✅ **详细文档** - 1700+ 行文档和示例

## 📦 新增内容

### 数据模型
```python
# UI 测试步骤
UITestStep
├── test_case, step_number, action_type
├── element_selector, selector_type
├── action_value, expected_result, timeout
└── ...

# UI 测试结果
UITestResult
├── test_run, test_case, environment
├── status, duration, error_message
├── steps_executed, steps_passed, steps_failed
├── screenshots, video_path
└── page_metrics (FCP, LCP, 等)

# 浏览器会话
UITestSession
├── session_id, browser_type, status
├── user, project
└── process tracking
```

### 自动化模块
```
test_manager/automation/
├── drivers/
│   └── PlaywrightBrowserDriver    # 浏览器驱动
├── locators/
│   └── ElementLocator             # 元素定位
└── executors/
    └── UITestExecutor             # 测试执行
```

## 🚀 开始使用

### 1. 安装（5 分钟）
```bash
# 安装 Playwright
pip install playwright
playwright install chromium firefox webkit

# 运行数据库迁移
python manage.py migrate test_manager
```

### 2. 创建第一个测试（10 分钟）
```python
from test_manager.model.models import TestCase
from test_manager.model.ui_models import UITestStep

# 创建测试
test = TestCase.objects.create(
    name="Google 搜索测试",
    test_type="ui",
    target_url="https://www.google.com",
    project=my_project,
    created_by=user
)

# 添加步骤
UITestStep.objects.create(
    test_case=test, step_number=1,
    action_type='navigate',
    action_value='https://www.google.com'
)

UITestStep.objects.create(
    test_case=test, step_number=2,
    action_type='fill',
    element_selector='[name="q"]',
    selector_type='css',
    action_value='Playwright Python'
)

UITestStep.objects.create(
    test_case=test, step_number=3,
    action_type='click',
    element_selector='text=Google Search',
    selector_type='text'
)

UITestStep.objects.create(
    test_case=test, step_number=4,
    action_type='screenshot'
)
```

### 3. 运行测试（2 分钟）
```python
import asyncio
from test_manager.automation import UITestExecutor

executor = UITestExecutor(test, environment, headless=True)
result = asyncio.run(executor.execute())

print(f"✅ Status: {result['status']}")
print(f"⏱️  Duration: {result['duration']:.2f}s")
```

## 📚 支持的操作类型

| 操作 | 说明 | 示例 |
|------|------|------|
| `navigate` | 导航到 URL | `https://example.com` |
| `click` | 点击元素 | `.button-class` |
| `fill` | 输入文本 | `#username` → `'user'` |
| `select` | 选择选项 | `select[name='country']` → `'US'` |
| `hover` | 鼠标悬停 | `.menu-item` |
| `wait` | 等待元素 | `.loading-complete` |
| `assert_visible` | 验证可见 | `.success-message` |
| `assert_text` | 验证文本 | `'Successfully logged in'` |
| `assert_url` | 验证 URL | `'/dashboard'` |
| `screenshot` | 截图 | （自动保存） |
| `scroll` | 滚动 | `{'x': 0, 'y': 500}` |
| `keyboard` | 键盘操作 | `'Enter'`, `'Tab'` |
| `upload_file` | 上传文件 | `/path/to/file.txt` |
| `double_click` | 双击 | `.item` |
| `right_click` | 右击 | `.context-menu` |

## 🎨 与 API 测试的集成

同一个 `TestCase` 模型支持两种测试类型：

```python
# API 测试
api_test = TestCase.objects.create(
    test_type='api',
    request_method='GET',
    request_url='/api/users',
    ...
)

# UI 测试
ui_test = TestCase.objects.create(
    test_type='ui',
    target_url='https://example.com/login',
    browser_type='chromium',
    ...
)

# 通过相同的 API 运行两种测试
POST /api/test-cases/{id}/run/
```

## 📊 执行结果示例

```python
{
    'status': 'passed',
    'duration': 5.23,
    'steps_executed': 7,
    'steps_passed': 7,
    'steps_failed': 0,
    'screenshots': [
        'screenshots/test_1_step_4.png',
        'screenshots/test_1_step_7.png'
    ],
    'page_metrics': {
        'pageLoadTime': 1200,
        'fcp': 800,
        'lcp': 1500
    },
    'step_details': [
        {'step_number': 1, 'status': 'passed', 'duration': 0.5},
        {'step_number': 2, 'status': 'passed', 'duration': 0.3},
        ...
    ]
}
```

## 💡 最佳实践速览

### ✅ 好的做法
```python
# 使用稳定的选择器
'#login-button'
'[data-testid="submit"]'
'.primary-action'

# 使用明确的等待
wait_for_visible('.success-message', timeout=10000)

# 定期截图用于调试
action_type='screenshot'
```

### ❌ 避免的做法
```python
# 深层 CSS 路径
'div > div > div > button'

# 硬等待
import time; time.sleep(5)

# 过于通用的选择器
'button'
'div'
```

## 🔧 配置选项

### 浏览器配置
```python
test_case.browser_type = 'chromium'      # 默认
# 或
test_case.browser_type = 'firefox'
test_case.browser_type = 'webkit'

test_case.headless = True                 # 无头模式（默认）
test_case.viewport_width = 1280
test_case.viewport_height = 720
```

### 执行配置
```python
executor = UITestExecutor(
    test_case,
    environment,
    headless=True,          # 无头模式
    slow_mo=500            # 慢动作延迟（ms）
)
```

## 📈 性能考虑

| 指标 | 数值 | 说明 |
|------|------|------|
| 浏览器启动 | 2-3s | 初始化时间 |
| 平均步骤 | 200-500ms | 根据操作类型 |
| 单个测试 | 5-30s | 取决于复杂度 |
| 并发限制 | 5-10 个 | 根据服务器资源 |
| 内存占用 | 100-200MB | 单个浏览器 |

## 🐛 常见问题

### Q: 如何处理间歇性失败？
A: 增加等待时间、使用智能等待、添加重试机制。

### Q: 如何调试测试？
A: 使用 `headless=False` 模式、保存截图、启用详细日志。

### Q: 支持多标签页吗？
A: Playwright 自动处理弹出窗口，支持多标签页导航。

### Q: 如何提高执行速度？
A: 使用 `headless=True`、减少等待时间、并行执行测试。

更多问题见 [最佳实践文档](UI_AUTOMATION_BEST_PRACTICES.md)。

## 📖 文档详细说明

### [实现总结](UI_AUTOMATION_SUMMARY.md)
- 项目概述和架构
- 文件清单和文件说明
- 关键性能指标
- 扩展建议

### [集成指南](UI_AUTOMATION_INTEGRATION.md)
- 详细的安装步骤
- API 扩展说明
- 完整的代码示例
- 故障排除

### [最佳实践](UI_AUTOMATION_BEST_PRACTICES.md)
- 元素定位最佳实践
- 等待和同步策略
- 性能优化
- 调试技巧

### [架构设计](UI_AUTOMATION_ARCHITECTURE.md)
- 系统设计原则
- 数据模型详细设计
- 核心模块实现
- 路线图和扩展

## 🎓 学习路径

1. **新手** → 快速开始 → [实现总结](UI_AUTOMATION_SUMMARY.md)
2. **开发者** → 部署 → [集成指南](UI_AUTOMATION_INTEGRATION.md)
3. **高级用户** → 最佳实践 → [最佳实践文档](UI_AUTOMATION_BEST_PRACTICES.md)
4. **架构师** → 深入理解 → [架构设计](UI_AUTOMATION_ARCHITECTURE.md)

## 🤝 支持

- 📚 **文档** - 4 份详细文档，共 2800+ 行
- 💻 **代码** - 完整的实现，共 1400+ 行
- 🔍 **日志** - 详细的执行日志用于调试
- 📸 **截图** - 自动保存失败时的截图

## 📝 版本信息

- **框架**: Playwright 1.40.0+
- **Python**: 3.8+
- **Django**: 3.2+
- **状态**: 生产就绪 ✅

## 🚀 下一步

1. **阅读** [实现总结](UI_AUTOMATION_SUMMARY.md) 了解整体情况
2. **按照** [集成指南](UI_AUTOMATION_INTEGRATION.md) 部署系统
3. **参考** [最佳实践](UI_AUTOMATION_BEST_PRACTICES.md) 创建测试
4. **深入** [架构设计](UI_AUTOMATION_ARCHITECTURE.md) 了解细节

---

## 许可证

遵循 EasyTesting 项目的许可证。

---

**准备好了？开始创建你的第一个 UI 自动化测试吧！** 🎉

> 💡 **提示**: 从简单的测试开始，逐步增加复杂度。使用截图来验证每个步骤。
