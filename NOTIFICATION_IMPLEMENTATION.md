# 通知中心实现总结

## 概述

为 EasyTesting 项目实现了完整的通知中心系统，包括数据库模型、REST API、前端 UI 和通知管理工具。

## 实现内容

### 1. 数据库模型 (`test_manager/model/models.py`)

添加了 `Notification` 模型，包含以下字段：

```python
class Notification(models.Model):
    user = models.ForeignKey(User, ...)  # 通知所属用户
    notification_type = models.CharField(...)  # 通知类型
    title = models.CharField(max_length=255)  # 通知标题
    message = models.TextField()  # 通知内容
    is_read = models.BooleanField(default=False)  # 是否已读
    related_url = models.URLField(blank=True, null=True)  # 相关链接
    created_at = models.DateTimeField(auto_now_add=True)  # 创建时间
    read_at = models.DateTimeField(null=True, blank=True)  # 已读时间
```

支持的通知类型：
- `test_run` - 测试运行
- `test_suite_run` - 测试套件运行
- `task` - 定时任务
- `system` - 系统通知
- `other` - 其他

### 2. REST API (`test_manager/api/`)

#### 序列化器 (`serializers.py`)

添加了 `NotificationSerializer`，用于序列化/反序列化通知对象。

#### 视图 (`views.py`)

添加了 `NotificationViewSet`，提供以下端点：

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/notifications/` | 获取用户的所有通知 |
| GET | `/api/notifications/unread_count/` | 获取未读通知数 |
| GET | `/api/notifications/unread_notifications/` | 获取未读通知列表 |
| POST | `/api/notifications/{id}/mark_as_read/` | 标记单个通知为已读 |
| POST | `/api/notifications/mark_all_as_read/` | 标记所有通知为已读 |
| DELETE | `/api/notifications/{id}/` | 删除单个通知 |
| DELETE | `/api/notifications/delete_all_read/` | 删除所有已读通知 |

#### URL 配置 (`urls.py`)

注册了 `NotificationViewSet` 路由：
```python
router.register(r'notifications', NotificationViewSet, basename='notification')
```

### 3. 前端实现 (`templates/base.html`)

#### HTML 结构

在导航栏添加通知中心 UI：
- 通知铃铛图标，显示未读通知数量徽章
- 通知下拉菜单，显示最近未读通知
- 快速操作按钮（标记全部已读、删除已读）

#### JavaScript (`NotificationManager` 类)

完整的客户端通知管理系统：

**主要功能：**
- 自动加载和更新通知列表（每 10 秒）
- 实时显示未读通知数
- 点击通知标记为已读
- 删除单个或批量通知
- 时间格式化显示（刚刚、几分钟前等）
- CSRF 令牌处理

**核心方法：**
```javascript
loadNotifications()       // 加载通知
updateUnreadCount()      // 更新未读计数
renderNotifications()    // 渲染通知列表
markAsRead()            // 标记为已读
markAllAsRead()         // 标记全部为已读
deleteNotification()    // 删除通知
deleteAllRead()         // 删除已读通知
```

#### CSS 样式

添加了通知中心的样式：
- 通知下拉菜单样式
- 已读/未读状态视觉区分
- 响应式设计
- 悬停效果
- 徽章样式

### 4. 通知工具函数 (`test_manager/utils/notification.py`)

提供了便捷的通知创建和管理函数：

```python
# 创建通知
create_notification()
create_test_run_notification()
create_test_suite_run_notification()
create_scheduled_task_notification()
create_system_notification()

# 查询通知
get_user_unread_count()
get_user_notifications()

# 清理通知
delete_old_read_notifications()
```

### 5. Django Admin 集成 (`test_manager/admin.py`)

添加了 `NotificationAdmin` 类：
- 列表视图显示用户、标题、类型、已读状态等
- 搜索功能（用户名、标题、消息）
- 过滤功能（类型、已读状态、日期）
- 日期层级导航
- 只读字段保护

### 6. 数据库迁移 (`test_manager/migrations/0002_notification.py`)

创建了数据库迁移脚本，包含：
- `Notification` 表创建
- 索引创建（用户-日期、用户-已读状态）

### 7. 管理命令 (`test_manager/management/commands/create_sample_notification.py`)

创建了示例通知命令：
```bash
python manage.py create_sample_notification
python manage.py create_sample_notification --user admin
python manage.py create_sample_notification --type test_run
```

### 8. 文档

#### `NOTIFICATION_USAGE.md`
完整的通知系统使用指南，包含：
- 系统架构说明
- API 接口文档
- 前端功能说明
- 后端集成示例
- 最佳实践
- 故障排除

#### `NOTIFICATION_IMPLEMENTATION.md`
本文档，实现总结

## 快速开始

### 1. 运行数据库迁移

```bash
python manage.py migrate test_manager
```

### 2. 创建示例通知（可选）

```bash
python manage.py create_sample_notification
```

### 3. 启动开发服务器

```bash
python manage.py runserver
```

### 4. 访问通知 API

- 通知列表：`http://localhost:8000/api/notifications/`
- 未读通知数：`http://localhost:8000/api/notifications/unread_count/`

### 5. 在代码中使用通知

```python
from test_manager.utils.notification import create_system_notification

# 创建通知
create_system_notification(
    user=request.user,
    title="测试标题",
    message="测试消息"
)
```

## 文件列表

### 新增文件
- `test_manager/migrations/0002_notification.py` - 数据库迁移
- `test_manager/utils/notification.py` - 通知工具函数
- `test_manager/management/commands/create_sample_notification.py` - 示例通知命令
- `NOTIFICATION_USAGE.md` - 使用文档
- `NOTIFICATION_IMPLEMENTATION.md` - 实现总结（本文件）

### 修改的文件
- `test_manager/model/models.py` - 添加 Notification 模型
- `test_manager/api/serializers.py` - 添加 NotificationSerializer
- `test_manager/api/views.py` - 添加 NotificationViewSet
- `test_manager/api/urls.py` - 注册通知路由
- `test_manager/admin.py` - 添加 NotificationAdmin
- `templates/base.html` - 添加通知 UI 和 JavaScript

## 集成指南

### 在测试运行完成时创建通知

```python
from test_manager.utils.notification import create_test_run_notification

# 在测试运行完成后
test_run.status = 'completed'
test_run.end_time = timezone.now()
test_run.save()

# 创建通知
create_test_run_notification(
    user=test_run.created_by,
    test_run=test_run,
    status=test_run.status
)
```

### 在定时任务中创建通知

```python
from test_manager.utils.notification import create_scheduled_task_notification

try:
    # 执行任务
    execute_task()
    
    # 创建成功通知
    create_scheduled_task_notification(
        user=task.created_by,
        task_name=task.name,
        status='success'
    )
except Exception as e:
    # 创建失败通知
    create_scheduled_task_notification(
        user=task.created_by,
        task_name=task.name,
        status='error',
        error_message=str(e)
    )
```

## API 使用示例

### 获取未读通知数

```bash
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/notifications/unread_count/
```

响应：
```json
{
  "unread_count": 5
}
```

### 获取未读通知列表

```bash
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/notifications/unread_notifications/?page_size=10
```

### 标记通知为已读

```bash
curl -X POST \
  -H "Authorization: Bearer <token>" \
  -H "X-CSRFToken: <csrf_token>" \
  http://localhost:8000/api/notifications/1/mark_as_read/
```

### 标记所有通知为已读

```bash
curl -X POST \
  -H "Authorization: Bearer <token>" \
  -H "X-CSRFToken: <csrf_token>" \
  http://localhost:8000/api/notifications/mark_all_as_read/
```

## 技术栈

- **后端框架**: Django 3.2+
- **REST API**: Django REST Framework
- **数据库**: PostgreSQL（或其他 Django 支持的数据库）
- **前端**: Vanilla JavaScript + Bootstrap 5
- **样式**: Bootstrap CSS + 自定义 CSS

## 性能考虑

1. **数据库索引**
   - 用户-日期索引：加快用户通知列表查询
   - 用户-已读状态索引：加快未读通知查询

2. **分页**
   - API 默认返回 10 条记录
   - 支持自定义 `page_size` 参数

3. **自动清理**
   - 提供 `delete_old_read_notifications()` 用于清理旧通知
   - 建议在 Celery 定时任务中执行

## 扩展建议

1. **WebSocket 支持**
   - 可以添加 WebSocket 支持实现实时通知推送
   - 使用 Django Channels 库

2. **邮件通知**
   - 为重要通知添加邮件发送功能
   - 使用现有的 EmailConfig 模型

3. **通知分类**
   - 添加通知分类功能，用户可订阅特定类型
   - 添加通知优先级

4. **批量操作**
   - 支持通知搜索和高级过滤
   - 批量标记为已读/删除

## 测试

建议添加单元测试：

```python
from django.test import TestCase
from django.contrib.auth.models import User
from test_manager.model.models import Notification
from test_manager.utils.notification import create_notification

class NotificationTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('testuser', 'test@test.com', 'password')
    
    def test_create_notification(self):
        notification = create_notification(
            user=self.user,
            title='Test',
            message='Test message'
        )
        self.assertEqual(notification.user, self.user)
        self.assertFalse(notification.is_read)
```

## 故障排除

### 迁移失败

确保已安装所有依赖，运行：
```bash
pip install django djangorestframework
python manage.py migrate
```

### API 返回 403 Forbidden

确保用户已认证，在请求头中包含正确的授权令牌。

### 通知不显示

1. 检查浏览器控制台是否有错误
2. 验证通知 API 是否可访问
3. 确保数据库中有通知记录

## 版本历史

- v1.0 (2024) - 初始实现
  - 基础通知模型和 API
  - 前端通知中心 UI
  - 通知管理工具函数

## 许可证

与 EasyTesting 项目使用相同的许可证

## 联系方式

如有问题或建议，请提交 issue 或联系项目维护者
