# UI 测试执行错误快速修复清单

## 问题总结
```
Error: 'int' object has no attribute 'ui_steps'
Location: test_manager/automation/executors/ui_executor.py:58
```

## 即时修复步骤

### 步骤 1: 更新 ui_views.py
已完成 ✓

**改进内容**:
- 增强日志记录（18+ 条日志）
- 智能错误恢复
- 结果验证
- 安全的属性访问

### 步骤 2: 验证数据库关系

```bash
# Django shell 中执行
python manage.py shell

from test_manager.model.models import TestCase
from test_manager.model.ui_models import UITestStep

# 检查是否有测试用例
tc = TestCase.objects.filter(ui_steps__isnull=False).first()
if tc:
    print(f"✓ 找到有 UI 步骤的测试用例: {tc.name}")
    print(f"  UI 步骤数: {tc.ui_steps.count()}")
else:
    print("✗ 没有找到有 UI 步骤的测试用例")
    print("  需要先创建 UI 测试步骤")
```

### 步骤 3: 测试执行流程

**在浏览器中测试**:
1. 打开应用
2. 导航到 UI 自动化测试页面
3. 找到一个有 UI 步骤的测试用例
4. 点击"运行"按钮
5. 观察日志输出

**检查日志**:
```bash
# 查看详细日志
tail -f logs/django.log | grep "UITestExecutor\|Test execution"
```

### 步骤 4: 验证修复

查看响应中的以下字段：

```json
{
    "success": true,
    "test_run_id": 1,
    "result": {
        "status": "passed",
        "steps_executed": 5,
        "steps_passed": 5,
        "steps_failed": 0,
        "duration": 12.34,
        "success_rate": 100,
        "error_message": "",
        "screenshots": [...]
    }
}
```

## 故障排除

### 问题: 日志显示 `type(test_case) = <class 'int'>`

**原因**: `get_object_or_404` 可能返回了错误的类型
**解决方案**: 检查 URL 参数传递

```python
# 在 ui_views.py 的开头添加调试
logger.info(f"test_case_id={test_case_id}, type={type(test_case_id)}")
test_case = get_object_or_404(TestCase, pk=test_case_id)
logger.info(f"test_case={test_case}, type={type(test_case)}")
```

### 问题: UITestStep 关联为空

**原因**: 测试用例没有 UI 步骤
**解决方案**: 创建 UI 步骤

```bash
# 在 Django shell 中
from test_manager.model.models import TestCase
from test_manager.model.ui_models import UITestStep

tc = TestCase.objects.get(id=1)  # 替换为实际的 ID
UITestStep.objects.create(
    test_case=tc,
    step_number=1,
    action_type='navigate',
    action_value='https://example.com',
    description='导航到首页'
)
```

### 问题: asyncio.run() 报错

**原因**: 事件循环问题
**解决方案**: 检查是否在异步上下文中

```python
# 改进的异步执行（已在新代码中实现）
try:
    result = asyncio.run(executor.execute())
except RuntimeError as e:
    if "asyncio.run() cannot be called from" in str(e):
        logger.error("已在异步上下文中，需要使用 await")
    raise
```

## 验证命令

运行以下命令验证修复：

```bash
# 1. 检查文件是否已修改
git diff test_manager/views/ui_views.py

# 2. 运行 Python 语法检查
python -m py_compile test_manager/views/ui_views.py

# 3. 运行测试
python manage.py test test_manager.tests

# 4. 启动服务器
python manage.py runserver

# 5. 在另一个终端查看日志
python manage.py shell < <(cat << 'EOF'
from test_manager.model.models import TestCase
from test_manager.model.ui_models import UITestStep

# 检查是否有测试用例
tc = TestCase.objects.filter(ui_steps__isnull=False).first()
if tc:
    print(f"✓ TestCase: {tc.name} (ID: {tc.id})")
    print(f"  UI Steps: {tc.ui_steps.count()}")
    for step in tc.ui_steps.all():
        print(f"    - Step {step.step_number}: {step.get_action_type_display()}")
else:
    print("✗ No TestCase with UI steps found")
EOF
)
```

## 预期测试结果

### 成功场景 ✓
- 日志显示正确的对象类型
- UITestExecutor 初始化成功
- 异步执行启动
- 收集所有步骤结果
- 返回成功的 JSON 响应

### 失败处理 ✓
- 异常被捕获并记录
- 返回有意义的错误信息
- 保留已执行的部分信息

## 部署检查清单

- [ ] 代码已修改：`test_manager/views/ui_views.py`
- [ ] 没有导入错误
- [ ] 日志配置正确
- [ ] 数据库关系正确
- [ ] 浏览器驱动程序已安装
- [ ] 测试用例已准备
- [ ] 环境配置完整

## 回滚计划（如果需要）

```bash
# 如果需要回滚
git checkout test_manager/views/ui_views.py

# 重启服务
supervisorctl restart all
```

---

**修复日期**: 2026-03-09
**修复状态**: 已完成并就绪测试
**优先级**: 高
**估计测试时间**: 15-30 分钟
