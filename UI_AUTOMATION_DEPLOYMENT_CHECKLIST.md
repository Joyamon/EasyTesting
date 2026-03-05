# UI 自动化测试框架 - 部署检查清单

按照此清单逐步部署和配置 UI 自动化测试框架。

## 前置条件检查

- [ ] Python 3.8+ 已安装
- [ ] Django 3.2+ 已安装
- [ ] 现有 EasyTesting 系统正常运行
- [ ] 数据库可用
- [ ] git 已配置（用于版本控制）

## 步骤 1: 环境准备 (15 分钟)

### 1.1 创建虚拟环境
```bash
# Linux/Mac
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```
- [ ] 虚拟环境创建成功
- [ ] 虚拟环境已激活

### 1.2 安装依赖
```bash
pip install playwright==1.40.0
```
- [ ] Playwright 安装成功
- [ ] `pip list` 中能看到 playwright

### 1.3 安装浏览器
```bash
playwright install chromium firefox webkit
```
- [ ] Chromium 浏览器已安装
- [ ] Firefox 浏览器已安装
- [ ] WebKit 浏览器已安装
- [ ] `~/.cache/ms-playwright/` 存在浏览器文件

## 步骤 2: 文件部署 (10 分钟)

### 2.1 验证数据模型文件
```bash
ls -la test_manager/model/ui_models.py
```
- [ ] `test_manager/model/ui_models.py` 存在（199 行）
- [ ] 文件可读

### 2.2 验证自动化模块
```bash
ls -la test_manager/automation/
```
- [ ] `test_manager/automation/` 目录存在
- [ ] `drivers/` 目录存在
- [ ] `locators/` 目录存在
- [ ] `executors/` 目录存在
- [ ] 所有 `__init__.py` 文件存在

### 2.3 验证文件完整性
```bash
# 检查所有关键文件
find test_manager/automation -name "*.py" | wc -l
```
- [ ] 至少 10 个 Python 文件
- [ ] 驱动文件约 300 行
- [ ] 定位器文件约 300 行
- [ ] 执行器文件约 400 行

### 2.4 验证文档文件
```bash
ls -la UI_AUTOMATION_*.md
```
- [ ] `UI_AUTOMATION_README.md` 存在
- [ ] `UI_AUTOMATION_SUMMARY.md` 存在
- [ ] `UI_AUTOMATION_INTEGRATION.md` 存在
- [ ] `UI_AUTOMATION_BEST_PRACTICES.md` 存在
- [ ] `UI_AUTOMATION_ARCHITECTURE.md` 存在

## 步骤 3: 数据库迁移 (10 分钟)

### 3.1 创建迁移文件
```bash
python manage.py makemigrations test_manager
```
- [ ] 迁移文件创建成功
- [ ] 输出显示创建了新的迁移

### 3.2 检查迁移内容
```bash
python manage.py showmigrations test_manager
```
- [ ] 显示所有迁移
- [ ] 包括 `0002_notification` 之后的迁移

### 3.3 执行迁移
```bash
python manage.py migrate test_manager
```
- [ ] 迁移执行成功
- [ ] 数据库表已创建

### 3.4 验证新表
```bash
# 进入数据库 shell
python manage.py shell
```
```python
from test_manager.model.ui_models import UITestStep, UITestResult, UITestSession
print(UITestStep.objects.count())  # 应该返回 0
print(UITestResult.objects.count())  # 应该返回 0
print(UITestSession.objects.count())  # 应该返回 0
```
- [ ] UITestStep 表存在
- [ ] UITestResult 表存在
- [ ] UITestSession 表存在
- [ ] 表可以查询

## 步骤 4: 模块导入验证 (10 分钟)

### 4.1 验证驱动导入
```python
python -c "from test_manager.automation.drivers import PlaywrightBrowserDriver; print('✅ Driver imported')"
```
- [ ] PlaywrightBrowserDriver 导入成功

### 4.2 验证定位器导入
```python
python -c "from test_manager.automation.locators import ElementLocator; print('✅ Locator imported')"
```
- [ ] ElementLocator 导入成功

### 4.3 验证执行器导入
```python
python -c "from test_manager.automation.executors import UITestExecutor; print('✅ Executor imported')"
```
- [ ] UITestExecutor 导入成功

### 4.4 验证模型导入
```python
python -c "from test_manager.model.ui_models import UITestStep, UITestResult; print('✅ Models imported')"
```
- [ ] UITestStep 导入成功
- [ ] UITestResult 导入成功

### 4.5 完整导入测试
```python
from test_manager.automation import PlaywrightBrowserDriver, ElementLocator, UITestExecutor
from test_manager.model.ui_models import UITestStep, UITestResult, UITestSession
from test_manager.utils.notification import create_ui_test_notification
print("✅ All imports successful")
```
- [ ] 所有导入成功

## 步骤 5: 浏览器测试 (15 分钟)

### 5.1 启动 Python shell
```bash
python manage.py shell
```

### 5.2 测试 Playwright
```python
import asyncio
from test_manager.automation import PlaywrightBrowserDriver

async def test_browser():
    driver = PlaywrightBrowserDriver(headless=True)
    await driver.launch()
    print("✅ Browser launched")
    
    await driver.navigate("https://www.google.com")
    title = await driver.get_title()
    print(f"✅ Page title: {title}")
    
    await driver.screenshot("test_screenshot.png")
    print("✅ Screenshot saved")
    
    await driver.close()
    print("✅ Browser closed")

asyncio.run(test_browser())
```
- [ ] 浏览器成功启动
- [ ] 页面成功导航
- [ ] 标题成功获取
- [ ] 截图成功保存
- [ ] 浏览器成功关闭

### 5.3 检查截图
```bash
ls -la test_screenshot.png
```
- [ ] 截图文件存在
- [ ] 文件大小 > 0

## 步骤 6: 完整功能测试 (30 分钟)

### 6.1 创建测试用例
```python
from django.contrib.auth.models import User
from test_manager.model.models import TestCase, Project, Environment
from test_manager.model.ui_models import UITestStep

# 获取或创建必要的对象
user = User.objects.first()
project = Project.objects.first()
environment = Environment.objects.first()

if not environment:
    print("❌ 请先创建至少一个 Environment")

# 创建 UI 测试用例
test_case = TestCase.objects.create(
    name="Google 搜索测试 - 部署检查",
    test_type="ui",
    target_url="https://www.google.com",
    project=project,
    created_by=user,
    browser_type='chromium',
    viewport_width=1280,
    viewport_height=720
)
print(f"✅ Test case created: {test_case.id}")
```
- [ ] 测试用例创建成功

### 6.2 添加测试步骤
```python
# 导航
UITestStep.objects.create(
    test_case=test_case,
    step_number=1,
    action_type='navigate',
    action_value='https://www.google.com'
)

# 搜索框填充
UITestStep.objects.create(
    test_case=test_case,
    step_number=2,
    action_type='fill',
    element_selector='[name="q"]',
    selector_type='css',
    action_value='Python Playwright'
)

# 点击搜索按钮
UITestStep.objects.create(
    test_case=test_case,
    step_number=3,
    action_type='click',
    element_selector='[aria-label="Google Search"]',
    selector_type='css'
)

# 等待结果加载
UITestStep.objects.create(
    test_case=test_case,
    step_number=4,
    action_type='wait',
    element_selector='.g',
    selector_type='css',
    timeout=10
)

# 验证结果
UITestStep.objects.create(
    test_case=test_case,
    step_number=5,
    action_type='assert_visible',
    element_selector='.g',
    selector_type='css'
)

# 截图
UITestStep.objects.create(
    test_case=test_case,
    step_number=6,
    action_type='screenshot'
)

print(f"✅ {test_case.ui_steps.count()} steps created")
```
- [ ] 所有 6 个步骤创建成功

### 6.3 执行测试
```python
import asyncio
from test_manager.automation import UITestExecutor

executor = UITestExecutor(test_case, environment, headless=True)
result = asyncio.run(executor.execute())

print(f"✅ Test execution completed")
print(f"Status: {result['status']}")
print(f"Steps executed: {result['steps_executed']}")
print(f"Steps passed: {result['steps_passed']}")
print(f"Steps failed: {result['steps_failed']}")
print(f"Duration: {result['duration']:.2f}s")

if result['screenshots']:
    print(f"Screenshots: {result['screenshots']}")
```
- [ ] 测试执行成功
- [ ] 状态为 'passed'
- [ ] 所有 6 步执行
- [ ] 所有 6 步通过
- [ ] 耗时合理（5-30 秒）
- [ ] 截图已保存

### 6.4 验证测试结果
```python
from test_manager.model.ui_models import UITestResult

# 如果使用了 TestRun 和 Result 保存
results = UITestResult.objects.filter(test_case=test_case)
print(f"✅ Found {results.count()} results")

if results.exists():
    latest = results.latest('created_at')
    print(f"Latest result status: {latest.status}")
```
- [ ] 测试结果已保存
- [ ] 结果可以查询

## 步骤 7: API 集成验证 (15 分钟)

### 7.1 验证 REST API
```bash
# 启动开发服务器
python manage.py runserver
```

### 7.2 测试 API 端点
```bash
# 在另一个终端
curl -X GET \
  "http://localhost:8000/api/test-cases/" \
  -H "Authorization: Bearer YOUR_TOKEN"
```
- [ ] API 端点可访问
- [ ] 返回 200 状态码
- [ ] 返回 JSON 数据

### 7.3 测试运行端点
```bash
curl -X POST \
  "http://localhost:8000/api/test-cases/{test_case_id}/run/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"environment_id": 1}'
```
- [ ] POST 请求成功
- [ ] 返回 test_run_id
- [ ] 返回 result 数据

## 步骤 8: Django Admin 集成 (10 分钟)

### 8.1 启动 Django Admin
```bash
python manage.py runserver
# 访问 http://localhost:8000/admin
```

### 8.2 验证 UI 模型显示
- [ ] UITestStep 出现在 Admin 中
- [ ] UITestResult 出现在 Admin 中
- [ ] UITestSession 出现在 Admin 中
- [ ] 可以创建新的 UI 测试步骤
- [ ] 可以查看测试结果

### 8.3 验证搜索和过滤
- [ ] 可以按 action_type 搜索
- [ ] 可以按 status 过滤
- [ ] 可以按日期排序

## 步骤 9: 性能和资源验证 (20 分钟)

### 9.1 监控内存使用
```bash
# 运行测试并监控内存
watch -n 1 'ps aux | grep python'
```
- [ ] 内存占用合理（< 500MB 每个浏览器）
- [ ] 浏览器进程正常创建和销毁

### 9.2 检查文件存储
```bash
ls -la screenshots/
```
- [ ] 截图目录存在
- [ ] 截图文件正确保存
- [ ] 文件数量合理

### 9.3 验证日志输出
```bash
# 查看 Django 日志
tail -f logs/django.log
```
- [ ] UI 测试日志正确记录
- [ ] 没有异常错误
- [ ] 执行时间正常

## 步骤 10: 文档验证 (5 分钟)

- [ ] README 文档可读
- [ ] 集成指南步骤清晰
- [ ] 最佳实践文档完整
- [ ] 架构设计文档详细

## 步骤 11: 备份和版本控制 (5 分钟)

### 11.1 提交代码
```bash
git add .
git commit -m "Add UI automation testing framework"
```
- [ ] 代码已提交到 git
- [ ] commit 消息清晰

### 11.2 备份数据库
```bash
python manage.py dumpdata test_manager > test_manager_backup.json
```
- [ ] 备份文件已创建
- [ ] 文件大小合理

## 最终检查清单

### 系统状态
- [ ] 所有文件已部署
- [ ] 所有依赖已安装
- [ ] 数据库已迁移
- [ ] 模块可以导入

### 功能验证
- [ ] Playwright 浏览器正常启动
- [ ] 可以创建 UI 测试用例
- [ ] 可以执行 UI 测试
- [ ] 可以查看测试结果

### 集成验证
- [ ] REST API 可用
- [ ] Django Admin 显示新模型
- [ ] 通知系统正常工作
- [ ] 与 API 测试框架兼容

### 质量检查
- [ ] 日志正常记录
- [ ] 性能指标正常
- [ ] 资源占用合理
- [ ] 错误处理完善

### 文档完整性
- [ ] README 完整
- [ ] 集成指南清晰
- [ ] 最佳实践可用
- [ ] 架构设计详细

## 部署完成！

恭喜！你已成功部署 EasyTesting UI 自动化测试框架。

### 下一步
1. 📖 阅读 [UI_AUTOMATION_BEST_PRACTICES.md](UI_AUTOMATION_BEST_PRACTICES.md)
2. 🎯 创建实际的 UI 测试用例
3. 🚀 集成到 CI/CD 流程
4. 📊 监控测试执行和结果

### 支持资源
- [快速开始文档](UI_AUTOMATION_README.md)
- [集成指南](UI_AUTOMATION_INTEGRATION.md)
- [最佳实践](UI_AUTOMATION_BEST_PRACTICES.md)
- [架构设计](UI_AUTOMATION_ARCHITECTURE.md)

### 常见问题
- 如有问题，查阅 [UI_AUTOMATION_BEST_PRACTICES.md](UI_AUTOMATION_BEST_PRACTICES.md) 中的常见问题部分
- 检查日志以了解具体错误信息
- 验证所有依赖和配置都正确

---

**部署日期**: _______________  
**部署人员**: _______________  
**验证状态**: ✅ 完成
