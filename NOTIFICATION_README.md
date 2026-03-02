# EasyTesting 通知中心系统

## 快速概览

为 EasyTesting 项目实现了完整的**通知中心系统**，允许用户实时接收和管理来自测试运行、定时任务等各种事件的通知。

## 核心特性

✨ **实时通知**
- 自动更新通知列表（每 10 秒）
- 显示未读通知数
- 实时徽章更新

📌 **通知管理**
- 单个或批量标记为已读
- 删除单个或批量通知
- 清理旧的已读通知

🎯 **分类系统**
- 测试运行通知
- 测试套件运行通知
- 定时任务通知
- 系统通知
- 自定义通知

🔌 **完整的 API**
- RESTful API 接口
- 分页支持
- 权限控制
- Django REST Framework

🛠️ **开发友好**
- 便捷的通知创建函数
- 管理命令工具
- Django Admin 集成
- 详细的文档

## 文件结构

```
test_manager/
├── model/
│   └── models.py                 # 添加 Notification 模型
├── api/
│   ├── serializers.py            # 添加 NotificationSerializer
│   ├── views.py                  # 添加 NotificationViewSet
│   └── urls.py                   # 注册通知路由
├── utils/
│   └── notification.py           # 通知工具函数（新建）
├── management/commands/
│   └── create_sample_notification.py  # 示例通知命令（新建）
├── migrations/
│   └── 0002_notification.py      # 数据库迁移（新建）
├── admin.py                      # 添加 NotificationAdmin
└── templates/base.html           # 添加通知 UI 和 JavaScript
```

## 快速开始

### 1. 运行数据库迁移

```bash
python manage.py migrate test_manager
```

### 2. 创建示例通知（可选）

```bash
python manage.py create_sample_notification
```

### 3. 在代码中创建通知

```python
from test_manager.utils.notification import create_system_notification

create_system_notification(
    user=request.user,
    title="测试完成",
    message="您的测试运行已完成"
)
```

### 4. 访问 API

```
GET /api/notifications/
GET /api/notifications/unread_count/
POST /api/notifications/{id}/mark_as_read/
DELETE /api/notifications/{id}/
```

## 使用场景

### 通知类型

| 类型 | 说明 | 场景 |
|------|------|------|
| `test_run` | 测试运行 | 单个测试用例或测试运行完成 |
| `test_suite_run` | 测试套件运行 | 测试套件运行完成 |
| `task` | 定时任务 | 定时任务执行成功/失败 |
| `system` | 系统通知 | 系统维护、公告等 |
| `other` | 其他 | 其他通知 |

### 集成示例

**在测试运行完成时创建通知：**

```python
from test_manager.utils.notification import create_test_run_notification

test_run.status = 'completed'
test_run.end_time = timezone.now()
test_run.save()

create_test_run_notification(
    user=test_run.created_by,
    test_run=test_run,
    status='completed'
)
```

**在定时任务中创建通知：**

```python
from test_manager.utils.notification import create_scheduled_task_notification

try:
    # 执行任务
    execute_task()
    
    create_scheduled_task_notification(
        user=task.created_by,
        task_name=task.name,
        status='success'
    )
except Exception as e:
    create_scheduled_task_notification(
        user=task.created_by,
        task_name=task.name,
        status='error',
        error_message=str(e)
    )
```

## API 接口

### 获取未读通知数

```
GET /api/notifications/unread_count/
```

**响应：**
```json
{
  "unread_count": 5
}
```

### 获取未读通知列表

```
GET /api/notifications/unread_notifications/?page_size=10
```

### 标记通知为已读

```
POST /api/notifications/{id}/mark_as_read/
```

### 标记全部通知为已读

```
POST /api/notifications/mark_all_as_read/
```

### 删除通知

```
DELETE /api/notifications/{id}/
```

### 删除所有已读通知

```
DELETE /api/notifications/delete_all_read/
```

## 前端功能

### 通知中心 UI

![通知中心](# "通知中心位置在导航栏右侧")

**功能：**
- 🔔 通知铃铛：显示未读通知数
- 📋 通知列表：显示最近 10 条未读通知
- ✓ 标记为已读：点击通知或使用快速按钮
- 🗑️ 删除通知：单个删除或批量删除
- ⏱️ 自动更新：每 10 秒更新一次

### 通知样式

- **未读通知**：蓝色背景，带"未读"徽章
- **已读通知**：白色背景
- **时间显示**：自动格式化（刚刚、几分钟前等）

## 数据库模型

```python
class Notification(models.Model):
    user              # 用户（外键）
    notification_type # 通知类型
    title             # 标题
    message           # 内容
    is_read           # 是否已读
    related_url       # 相关链接
    created_at        # 创建时间
    read_at           # 已读时间
```

**索引：**
- 用户-日期：加快用户通知列表查询
- 用户-已读状态：加快未读通知查询

## 工具函数

### 创建通知

```python
from test_manager.utils.notification import (
    create_notification,
    create_test_run_notification,
    create_scheduled_task_notification,
    create_system_notification
)

# 基础通知
create_notification(user, title, message, notification_type)

# 测试运行通知
create_test_run_notification(user, test_run, status)

# 定时任务通知
create_scheduled_task_notification(user, task_name, status, error_message)

# 系统通知
create_system_notification(user, title, message)
```

### 查询通知

```python
from test_manager.utils.notification import (
    get_user_unread_count,
    get_user_notifications
)

# 获取未读通知数
unread_count = get_user_unread_count(user)

# 获取用户通知
notifications = get_user_notifications(user, limit=10, unread_only=False)
```

### 清理通知

```python
from test_manager.utils.notification import delete_old_read_notifications

# 删除 30 天前的已读通知
deleted_count = delete_old_read_notifications(user, days=30)
```

## Django Admin

### 通知管理

在 Django Admin (`/admin/`) 中管理通知：

- **列表视图**：用户、标题、类型、已读状态等
- **搜索**：按用户名、标题、消息搜索
- **过滤**：按类型、已读状态、日期过滤
- **日期层级**：按日期导航

## 管理命令

### 创建示例通知

```bash
# 为当前用户创建示例通知
python manage.py create_sample_notification

# 为指定用户创建通知
python manage.py create_sample_notification --user admin

# 创建特定类型的通知
python manage.py create_sample_notification --type test_run
```

## 配置

### 更新频率

在 `templates/base.html` 中修改：

```javascript
this.updateInterval = 10000; // 10 秒（毫秒）
```

### 通知类型

在 `test_manager/model/models.py` 中修改 `NOTIFICATION_TYPE_CHOICES`

## 文档

- **[NOTIFICATION_USAGE.md](NOTIFICATION_USAGE.md)** - 详细使用文档
- **[NOTIFICATION_IMPLEMENTATION.md](NOTIFICATION_IMPLEMENTATION.md)** - 实现细节
- **[NOTIFICATION_CHECKLIST.md](NOTIFICATION_CHECKLIST.md)** - 检查清单

## 最佳实践

1. **创建有意义的通知**
   - 标题简洁明了
   - 消息内容详细但不过长

2. **使用正确的类型**
   - 与通知内容相匹配
   - 便于用户识别和过滤

3. **提供相关链接**
   - 用户可快速访问相关资源

4. **定期清理**
   - 使用 `delete_old_read_notifications()` 清理旧通知
   - 在 Celery 定时任务中执行

5. **避免通知泛滥**
   - 仅创建重要通知
   - 避免过度提醒

## 性能指标

- **查询性能**：优化索引确保快速查询
- **更新频率**：默认 10 秒，可配置
- **分页支持**：防止大数据集加载
- **自动清理**：避免数据库过度增长

## 故障排除

### 通知不显示

1. 确保已运行迁移：`python manage.py migrate`
2. 检查浏览器控制台错误
3. 验证 API 端点可访问
4. 确保有通知记录

### API 返回 403

1. 检查用户是否认证
2. 验证权限配置

### 通知不更新

1. 检查网络请求
2. 验证 CSRF 令牌
3. 检查浏览器刷新率

## 扩展建议

- **WebSocket 支持**：实时推送通知
- **邮件通知**：重要通知发送邮件
- **通知分类**：用户可订阅特定类型
- **通知优先级**：显示重要通知优先
- **批量操作**：高级搜索和过滤

## 技术栈

- Django 3.2+
- Django REST Framework
- Bootstrap 5
- Vanilla JavaScript

## 依赖

无新增外部依赖，仅使用现有的 Django 和 DRF。

## 版本信息

- 版本：1.0
- 发布日期：2024年
- Python 版本：3.6+
- Django 版本：3.2+

## 问题反馈

如有问题或建议，请：
1. 检查文档
2. 查看故障排除章节
3. 提交 GitHub Issue
4. 联系项目维护者

## 相关文件

### 新增文件
- `test_manager/migrations/0002_notification.py`
- `test_manager/utils/notification.py`
- `test_manager/management/commands/create_sample_notification.py`
- `NOTIFICATION_USAGE.md`
- `NOTIFICATION_IMPLEMENTATION.md`
- `NOTIFICATION_CHECKLIST.md`
- `NOTIFICATION_README.md` (本文件)

### 修改的文件
- `test_manager/model/models.py`
- `test_manager/api/serializers.py`
- `test_manager/api/views.py`
- `test_manager/api/urls.py`
- `test_manager/admin.py`
- `templates/base.html`

## 贡献指南

欢迎贡献！请：
1. Fork 项目
2. 创建特性分支
3. 提交 Pull Request
4. 确保测试通过

## 许可证

与 EasyTesting 项目相同

## 致谢

感谢所有测试和反馈的贡献者！

---

**提示**: 完整的实现细节请查看 [NOTIFICATION_IMPLEMENTATION.md](NOTIFICATION_IMPLEMENTATION.md)，使用指南请查看 [NOTIFICATION_USAGE.md](NOTIFICATION_USAGE.md)
