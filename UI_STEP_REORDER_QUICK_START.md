# UI 测试步骤排序 - 快速开始指南

## 5 分钟快速上手

### 修改的文件清单

| 文件 | 行数 | 说明 |
|------|------|------|
| `templates/test_manager/ui_test/ui_test_case_detail.html` | +130 | 拖拽 UI 和 JavaScript |
| `test_manager/views/ui_views.py` | +64 | 步骤排序视图和删除改进 |
| `test_manager/urls/ui_urls.py` | +2 | 新增 URL 路由 |
| **总计** | **+196** | **完整实现** |

### 安装步骤

#### 1. 代码部署
```bash
# 确保所有文件都已更新
- templates/test_manager/ui_test/ui_test_case_detail.html
- test_manager/views/ui_views.py
- test_manager/urls/ui_urls.py
```

#### 2. 重启应用
```bash
# Django
python manage.py runserver

# 或生产环境
supervisorctl restart all
```

#### 3. 验证功能
访问任何 UI 测试用例详情页面:
```
http://localhost:8000/ui-test-cases/<id>/
```

应该看到:
- "调整顺序" 按钮（绿色）
- 测试步骤列表
- 每个步骤右侧的编辑/删除按钮

### 使用流程

#### 步骤 1: 点击"调整顺序"
![image](https://img.shields.io/badge/状态-可拖拽-brightgreen)

```
"调整顺序" 按钮变为隐藏
"完成排序" 按钮显示
拖拽手柄变为可见 (六点图标)
```

#### 步骤 2: 拖拽重新排列
```
1. 将鼠标悬停在步骤左侧的 "⋮⋮" 图标
2. 点击并按住不放
3. 拖动到目标位置
4. 释放鼠标
```

#### 步骤 3: 完成排序
```
点击 "完成排序" 按钮
- 系统自动保存
- 页面刷新显示新顺序
- 步骤号自动更新
```

### 核心 API

#### 前端 API

```javascript
// 切换排序模式
toggleSortMode()

// 更新步骤顺序 (自动调用)
updateStepOrder()

// 删除步骤
confirmDeleteStep(stepId)

// 显示提示
showToast(message, type)
```

#### 后端 API

```
POST /ui-test-cases/<pk>/reorder-steps/

请求体:
{
    "steps": [
        {"id": 1, "step_number": 1},
        {"id": 2, "step_number": 2},
        ...
    ]
}

响应:
{
    "success": true,
    "message": "步骤顺序更新成功"
}
```

### 常见问题

#### Q1: 如何取消排序?
```
点击 "调整顺序" 按钮切换回去
注意: 必须点击 "完成排序" 才会保存
```

#### Q2: 删除步骤后会怎样?
```
系统自动重新编号后续步骤
例如: 删除步骤 2 后, 步骤 3→2, 步骤 4→3
```

#### Q3: 支持哪些浏览器?
```
✅ Chrome 60+
✅ Firefox 55+
✅ Safari 12+
✅ Edge 79+
```

#### Q4: 如果网络中断会怎样?
```
会显示错误提示，步骤顺序不会改变
点击 "完成排序" 重试即可
```

### 故障排除

#### 问题: 拖拽手柄不显示
```
1. 清除浏览器缓存 (Ctrl+Shift+Delete)
2. 刷新页面 (F5)
3. 检查浏览器控制台是否有错误
```

#### 问题: 排序后页面没有刷新
```
1. 等待 1-2 秒
2. 手动刷新页面 (F5)
3. 检查网络请求是否成功 (F12 → Network)
```

#### 问题: 提示"网络错误"
```
1. 检查网络连接
2. 确保 CSRF token 正确
3. 检查服务器日志
```

### 功能检查清单

- [ ] "调整顺序" 按钮可见
- [ ] 点击按钮后拖拽手柄显示
- [ ] 可以拖拽步骤
- [ ] 拖拽后步骤号更新
- [ ] 点击 "完成排序" 保存成功
- [ ] 删除步骤后编号正确
- [ ] 刷新页面数据持久化

### 监控指标

监控以下指标确保功能正常:

```python
# 后端日志
- INFO: Test case {pk} steps reordered successfully
- ERROR: Error reordering steps

# 数据库
- UITestStep.step_number 值唯一性
- unique_together ('test_case', 'step_number') 约束
```

### 性能指标

| 指标 | 目标 | 实际 |
|------|------|------|
| 拖拽响应时间 | <100ms | - |
| 保存延迟 | <500ms | - |
| 页面加载 | <2s | - |
| 脚本体积 | <50KB | ~45KB (Sortable.js) |

### 下一步

1. ✅ 部署代码
2. ✅ 验证功能
3. 📊 收集用户反馈
4. 🔄 迭代改进

### 支持和反馈

遇到问题? 查看完整文档:
- `UI_STEP_REORDER_FEATURE.md` - 完整实现细节
- `UI_TEST_STEP_REORDER_TESTS.md` - 测试指南
