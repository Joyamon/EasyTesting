# UI 自动化测试集成指南

快速将 UI 自动化功能集成到 EasyTesting 系统。

## 一、前置条件

- Python 3.8+
- Django 3.2+
- 现有的 EasyTesting API 测试系统

## 二、安装步骤

### 步骤 1: 安装 Playwright

```bash
pip install playwright==1.40.0
playwright install chromium firefox webkit
```

**验证安装：**
```bash
python -c "import playwright; print(playwright.__version__)"
```

### 步骤 2: 注册 Django 应用

编辑 `EasyTesting/settings.py`，确保应用配置正确：

```python
INSTALLED_APPS = [
    # ... 其他应用
    'test_manager',  # 确保已添加
]
```

### 步骤 3: 运行数据库迁移

```bash
python manage.py makemigrations test_manager
python manage.py migrate test_manager
```

**验证迁移：**
```bash
python manage.py showmigrations test_manager
```

### 步骤 4: 在 Django Admin 中注册模型（可选）

编辑 `test_manager/admin.py`，添加：

```python
from test_manager.model.ui_models import UITestStep, UITestResult, UITestSession

@admin.register(UITestStep)
class UITestStepAdmin(admin.ModelAdmin):
    list_display = ('test_case', 'step_number', 'action_type', 'created_at')
    list_filter = ('action_type', 'created_at')
    search_fields = ('test_case__name', 'element_selector')
    ordering = ('test_case', 'step_number')

@admin.register(UITestResult)
class UITestResultAdmin(admin.ModelAdmin):
    list_display = ('test_case', 'status', 'duration', 'steps_executed', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('test_case__name',)
    readonly_fields = ('created_at', 'updated_at')
```

## 三、文件结构

新增文件：
```
test_manager/
├── model/
│   └── ui_models.py              # UI 测试模型
├── automation/                   # UI 自动化模块
│   ├── __init__.py
│   ├── drivers/
│   │   ├── __init__.py
│   │   └── playwright_driver.py  # Playwright 驱动
│   ├── locators/
│   │   ├── __init__.py
│   │   └── element_locator.py    # 元素定位器
│   └── executors/
│       ├── __init__.py
│       └── ui_executor.py        # UI 测试执行器
├── utils/
│   └── notification.py           # 更新：添加 UI 测试通知
```

## 四、API 扩展

### 在 `test_manager/api/views.py` 中添加

```python
from test_manager.automation.executors.ui_executor import UITestExecutor
from test_manager.model.ui_models import UITestResult

class TestCaseViewSet(viewsets.ModelViewSet):
    # ... 现有代码
    
    @action(detail=True, methods=['post'])
    def run(self, request, pk=None):
        """运行测试（支持 API 和 UI）"""
        test_case = self.get_object()
        environment_id = request.data.get('environment_id')
        
        if not environment_id:
            return Response(
                {"error": "Environment ID is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
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
                # 执行 API 测试
                from test_manager.utils.httprunner_executor import execute_test_case
                result = execute_test_case(test_case, environment)
                test_run.status = 'completed' if result['status'] == 'passed' else 'failed'
            else:
                # 执行 UI 测试
                import asyncio
                executor = UITestExecutor(test_case, environment, headless=True)
                result = asyncio.run(executor.execute())
                test_run.status = 'completed' if result['status'] == 'passed' else 'failed'
                
                # 保存 UI 测试结果
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
                    screenshots=result.get('screenshots', []),
                    step_details=result.get('step_details', [])
                )
                
                # 发送通知
                from test_manager.utils.notification import create_ui_test_notification
                create_ui_test_notification(request.user, test_case, result['status'], 
                                           result.get('error_message', ''))
            
            test_run.end_time = timezone.now()
            test_run.save()
            
            return Response({
                'test_run_id': test_run.id,
                'status': test_run.status,
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

### 在 `test_manager/api/serializers.py` 中添加

```python
from test_manager.model.ui_models import UITestStep, UITestResult

class UITestStepSerializer(serializers.ModelSerializer):
    class Meta:
        model = UITestStep
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

class UITestResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = UITestResult
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']
```

### 在 `test_manager/api/urls.py` 中添加（如需独立 API）

```python
from .views import UITestStepViewSet, UITestResultViewSet

router.register(r'ui-test-steps', UITestStepViewSet)
router.register(r'ui-test-results', UITestResultViewSet)
```

## 五、使用示例

### 示例 1：创建简单的 UI 测试

```python
from django.contrib.auth.models import User
from test_manager.model.models import TestCase, Project
from test_manager.model.ui_models import UITestStep

# 创建测试用例
user = User.objects.first()
project = Project.objects.first()

test_case = TestCase.objects.create(
    name="百度搜索测试",
    test_type="ui",
    target_url="https://www.baidu.com",
    project=project,
    created_by=user,
    browser_type='chromium',
    viewport_width=1280,
    viewport_height=720
)

# 添加测试步骤
UITestStep.objects.create(
    test_case=test_case,
    step_number=1,
    action_type='navigate',
    action_value='https://www.baidu.com'
)

UITestStep.objects.create(
    test_case=test_case,
    step_number=2,
    action_type='fill',
    element_selector='#kw',
    selector_type='css',
    action_value='Python'
)

UITestStep.objects.create(
    test_case=test_case,
    step_number=3,
    action_type='click',
    element_selector='#su',
    selector_type='css'
)

UITestStep.objects.create(
    test_case=test_case,
    step_number=4,
    action_type='wait',
    element_selector='.result',
    selector_type='css',
    timeout=10
)

UITestStep.objects.create(
    test_case=test_case,
    step_number=5,
    action_type='screenshot'
)
```

### 示例 2：运行 UI 测试

```python
import asyncio
from test_manager.model.models import TestCase, Environment
from test_manager.automation.executors.ui_executor import UITestExecutor

# 获取测试用例和环境
test_case = TestCase.objects.get(id=1)
environment = Environment.objects.get(id=1)

# 创建执行器并运行
executor = UITestExecutor(test_case, environment, headless=True)
result = asyncio.run(executor.execute())

# 处理结果
print(f"状态: {result['status']}")
print(f"执行步骤: {result['steps_executed']}")
print(f"通过: {result['steps_passed']}")
print(f"失败: {result['steps_failed']}")
print(f"耗时: {result['duration']:.2f}s")

if result['error_message']:
    print(f"错误: {result['error_message']}")

if result['screenshots']:
    print(f"截图: {result['screenshots']}")
```

### 示例 3：批量运行测试

```python
import asyncio
from test_manager.model.models import TestCase, Environment
from test_manager.automation.executors.ui_executor import UITestExecutor

async def run_all_ui_tests():
    # 获取所有 UI 测试
    test_cases = TestCase.objects.filter(test_type='ui')
    environment = Environment.objects.first()
    
    results = {}
    
    for test_case in test_cases:
        executor = UITestExecutor(test_case, environment, headless=True)
        result = await executor.execute()
        results[test_case.name] = result
    
    # 统计总体结果
    total_tests = len(results)
    passed = sum(1 for r in results.values() if r['status'] == 'passed')
    failed = total_tests - passed
    
    print(f"总计: {total_tests} | 通过: {passed} | 失败: {failed}")
    
    return results

# 运行
results = asyncio.run(run_all_ui_tests())
```

## 六、常见配置

### 配置 1: 不同浏览器的测试

```python
# 在 TestCase 中选择浏览器
test_case = TestCase.objects.create(
    # ...
    browser_type='firefox',  # 或 'webkit'
)
```

### 配置 2: 设置代理

```python
# 修改 playwright_driver.py
self.browser = await browser_launcher.launch(
    headless=self.headless,
    slow_mo=self.slow_mo,
    proxy={
        'server': 'http://proxy.example.com:3128',
        'username': 'user',
        'password': 'password'
    }
)
```

### 配置 3: 自定义超时

```python
# 在创建执行器时
executor = UITestExecutor(test_case, timeout=60000)  # 60 秒
```

## 七、性能考虑

### 并发限制
- 单个服务器上建议同时运行不超过 5-10 个浏览器实例
- 根据服务器资源调整

### 资源监控
```bash
# 监控内存使用
top -p $(pgrep -f "python.*manage.py")

# 清理临时文件
rm -rf screenshots/*
rm -rf media/ui_test_videos/*
```

## 八、故障排除

### 问题：Playwright 安装失败

```bash
# 解决方案
pip install --upgrade pip
pip install playwright --no-cache-dir
playwright install --with-deps
```

### 问题：浏览器启动失败

```python
# 启用调试模式
import logging
logging.basicConfig(level=logging.DEBUG)

# 使用非 headless 模式调试
executor = UITestExecutor(test_case, headless=False)
```

### 问题：元素未找到

1. 验证选择器是否正确
2. 增加等待时间
3. 检查页面是否完全加载

## 九、下一步

- 查看 [UI 自动化架构设计](UI_AUTOMATION_ARCHITECTURE.md) 了解详细设计
- 查看 [UI 自动化最佳实践](UI_AUTOMATION_BEST_PRACTICES.md) 学习最佳实践
- 在 Django Admin 中创建更多 UI 测试用例
- 配置持续集成（CI）运行 UI 测试

## 十、支持

有问题或需要帮助？

1. 查看日志：`python manage.py shell` 后查看 `logging`
2. 检查 Django Admin 中的测试结果
3. 查看存储的截图进行调试

祝你使用愉快！
