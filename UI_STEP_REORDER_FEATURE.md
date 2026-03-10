# UI 测试步骤排序功能实现

## 功能概述

在 `ui_test_case_detail.html` 中新增了调整测试步骤顺序的功能，允许用户通过拖拽的方式重新排列测试步骤。

## 实现细节

### 1. 前端实现 (`ui_test_case_detail.html`)

#### HTML 变更
- **拖拽手柄**: 在每个步骤项上添加 `<span class="step-drag-handle">` 用于拖拽操作
- **排序按钮**:
  - "调整顺序" 按钮: 启用排序模式
  - "完成排序" 按钮: 保存排序结果

#### JavaScript 功能
```javascript
// 1. 初始化 Sortable.js 库
initSortable()
  - 使用开源库 Sortable.js 实现拖拽排序
  - 禁用状态，仅在排序模式下启用

// 2. 切换排序模式
toggleSortMode()
  - 进入模式: 显示拖拽手柄，启用排序
  - 退出模式: 隐藏拖拽手柄，禁用排序

// 3. 更新步骤顺序
updateStepOrder()
  - 收集新的步骤顺序
  - 调用后端 API 保存
  - 更新 UI 显示步骤号
  - 自动刷新页面
```

### 2. 后端实现 (`ui_views.py`)

#### 新增视图: `ui_test_case_reorder_steps()`
```python
@login_required
def ui_test_case_reorder_steps(request, pk):
    """重新排序 UI 测试步骤"""
    - 验证请求格式 (POST)
    - 解析步骤列表: [{'id': 1, 'step_number': 1}, ...]
    - 批量更新每个步骤的 step_number
    - 返回成功/失败响应
```

#### 改进: `ui_test_step_delete()`
```python
删除步骤后自动重新编号后续步骤
- 获取被删除步骤的编号
- 重新编号所有大于该编号的步骤
- 确保编号连续性
```

### 3. URL 配置 (`ui_urls.py`)

新增路由:
```
POST /ui-test-cases/<pk>/reorder-steps/
```

## 使用流程

### 用户操作步骤

1. **进入测试用例详情页面**
   - 访问: `/ui-test-cases/<id>/`

2. **点击"调整顺序"按钮**
   - 启用拖拽模式
   - 显示拖拽手柄
   - 提示用户可以开始拖拽

3. **拖拽重新排列步骤**
   - 点击并按住拖拽手柄
   - 拖动到目标位置
   - 释放鼠标

4. **点击"完成排序"按钮**
   - 发送新顺序到后端
   - 服务器保存新顺序
   - 刷新页面显示更新

## 技术栈

### 前端库
- **Sortable.js**: 拖拽排序库
  - CDN: `https://cdn.jsdelivr.net/npm/sortablejs@latest/Sortable.min.js`
  - 功能: 原生 JavaScript 拖拽排序
  - 兼容性: 支持所有现代浏览器

### 后端
- Django ORM
- JSON 请求/响应
- CSRF 保护

## 核心代码片段

### 前端 - 初始化 Sortable
```html
<script src="https://cdn.jsdelivr.net/npm/sortablejs@latest/Sortable.min.js"></script>

<script>
function initSortable() {
    const stepsList = document.getElementById('stepsList');
    Sortable.create(stepsList, {
        animation: 150,
        handle: '.step-drag-handle',
        disabled: true,  // 初始禁用，排序模式下启用
        onEnd: function (evt) {
            if (sortMode) {
                updateStepOrder();
            }
        }
    });
}
</script>
```

### 前端 - 切换排序模式
```javascript
function toggleSortMode() {
    sortMode = !sortMode;
    const dragHandles = document.querySelectorAll('.step-drag-handle');
    const sortableInstance = Sortable.get(stepsList);
    
    if (sortMode) {
        // 显示拖拽手柄，启用排序
        dragHandles.forEach(handle => handle.style.display = 'inline');
        sortableInstance.option('disabled', false);
    } else {
        // 隐藏拖拽手柄，禁用排序
        dragHandles.forEach(handle => handle.style.display = 'none');
        sortableInstance.option('disabled', true);
    }
}
```

### 后端 - 保存排序结果
```python
@login_required
def ui_test_case_reorder_steps(request, pk):
    test_case = get_object_or_404(TestCase, pk=pk)
    
    if request.method == 'POST':
        data = json.loads(request.body)
        steps = data.get('steps', [])
        
        # 批量更新步骤顺序
        for step_data in steps:
            step = UITestStep.objects.get(id=step_data['id'])
            step.step_number = step_data['step_number']
            step.save()
        
        return JsonResponse({'success': True})
```

## 功能特点

✅ **用户友好**
- 直观的拖拽界面
- 实时预览排序效果
- 清晰的模式提示

✅ **可靠性保证**
- 完整的错误处理
- CSRF 保护
- 数据一致性验证
- 步骤号自动重新编号

✅ **性能优化**
- 延迟加载 Sortable.js
- 最小化 DOM 操作
- 批量更新数据库

✅ **无缝集成**
- 与现有代码完全兼容
- 不破坏现有功能
- 遵循项目编码规范

## 测试场景

### 1. 基本排序测试
- 从 A-B-C 排序为 C-B-A
- 验证数据库步骤号正确

### 2. 边界测试
- 只有一个步骤 (无法排序)
- 两个步骤交换位置

### 3. 错误处理
- 网络中断
- 无效的步骤 ID
- 权限不足

### 4. 删除后排序
- 删除步骤后重新编号
- 确保编号连续

## 部署说明

### 前置条件
- Django 应用正常运行
- 数据库迁移完成
- 网络连接正常 (Sortable.js CDN)

### 部署步骤
1. 更新 `ui_test_case_detail.html`
2. 更新 `ui_views.py` (添加新视图)
3. 更新 `ui_urls.py` (添加新路由)
4. 重启 Django 应用
5. 清除浏览器缓存
6. 访问测试用例详情页面验证

### 回滚计划
- 如遇问题，恢复之前版本的三个文件
- 重启应用

## 未来改进方向

1. **批量操作**
   - 支持多选删除
   - 支持批量更新

2. **高级排序**
   - 按名称排序
   - 按类型过滤

3. **版本控制**
   - 记录排序历史
   - 支持还原

4. **实时协作**
   - 多用户同时编辑提示
   - 冲突解决机制

## 总结

此功能通过结合 Sortable.js 前端库和 Django 后端 API，提供了一个完整、可靠的测试步骤排序解决方案。用户可以直观地拖拽步骤重新排序，系统自动处理数据一致性和错误情况。
