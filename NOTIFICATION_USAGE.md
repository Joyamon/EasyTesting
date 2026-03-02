# 通知系统使用指南

## 概述

EasyTesting 通知系统提供了在线实时通知功能，用户可以在导航栏的通知中心查看各种通知，包括测试运行、定时任务等的状态更新。

## 系统架构

### 数据库模型

`Notification` 模型位于 `test_manager/model/models.py`，包含以下字段：

- `user`: 外键，指向用户
- `notification_type`: 通知类型（test_run, test_suite_run, task, system, other）
- `title`: 通知标题
- `message`: 通知内容
- `is_read`: 是否已读
- `related_url`: 相关链接（可选）
- `created_at`: 创建时间
- `read_at`: 已读时间

### API 接口

通知 API 位于 `/api/notifications/`，提供以下端点：

#### 1. 获取通知列表
```
GET /api/notifications/
```
返回当前用户的所有通知列表（已读和未读）

**响应示例：**
```json
{
  "count": 10,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "user": 1,
      "notification_type": "test_run",
      "title": "测试运行 - My Test",
      "message": "测试运行 'My Test' 已完成",
      "is_read": false,
      "related_url": "/test-runs/1/",
      "created_at": "2024-01-01T10:00:00Z",
      "read_at": null
    }
  ]
}
```

#### 2. 获取未读通知数
```
GET /api/notifications/unread_count/
```
返回当前用户的未读通知数

**响应示例：**
```json
{
  "unread_count": 5
}
```

#### 3. 获取未读通知列表
```
GET /api/notifications/unread_notifications/
```
返回当前用户的未读通知列表

#### 4. 标记单个通知为已读
```
POST /api/notifications/{id}/mark_as_read/
```
标记指定通知为已读

#### 5. 标记所有通知为已读
```
POST /api/notifications/mark_all_as_read/
```
将当前用户的所有未读通知标记为已读

#### 6. 删除单个通知
```
DELETE /api/notifications/{id}/
```
删除指定通知

#### 7. 删除所有已读通知
```
DELETE /api/notifications/delete_all_read/
```
删除当前用户的所有已读通知

## 前端功能

### 通知中心 UI

在导航栏右上角显示通知中心，包括：

1. **通知铃铛图标**
   - 显示未读通知数量徽章
   - 点击打开通知下拉菜单

2. **通知列表**
   - 显示最近 10 条未读通知
   - 每条通知包含标题、内容摘要和时间
   - 未读通知显示蓝色"未读"徽章

3. **快速操作按钮**
   - "标记全部为已读"：一键将所有通知标记为已读
   - "删除已读通知"：一键删除所有已读通知

4. **自动更新**
   - 每 10 秒自动检查一次新通知
   - 实时更新未读通知数量和列表

### 使用示例

#### 查看通知
1. 点击导航栏的铃铛图标
2. 通知下拉菜单显示未读通知列表
3. 点击任何通知可将其标记为已读

#### 删除通知
1. 在通知列表中，点击通知右侧的垃圾箱图标
2. 通知将被删除

#### 批量操作
1. 点击"标记全部为已读"按钮标记所有通知
2. 点击"删除已读通知"按钮删除已读通知

## 后端使用

### 创建通知

在代码中使用通知工具函数 (`test_manager/utils/notification.py`) 创建通知：

#### 1. 创建基础通知
```python
from test_manager.utils.notification import create_notification

create_notification(
    user=request.user,
    title="测试标题",
    message="这是一条测试消息",
    notification_type='system'
)
```

#### 2. 创建测试运行通知
```python
from test_manager.utils.notification import create_test_run_notification

# 在测试运行完成后调用
create_test_run_notification(
    user=test_run.created_by,
    test_run=test_run,
    status='completed'  # 或 'failed', 'running', 'pending'
)
```

#### 3. 创建定时任务通知
```python
from test_manager.utils.notification import create_scheduled_task_notification

# 在定时任务执行后调用
create_scheduled_task_notification(
    user=task.created_by,
    task_name="My Scheduled Task",
    status='success',  # 或 'failed', 'error'
    error_message=None  # 可选的错误信息
)
```

#### 4. 创建系统通知
```python
from test_manager.utils.notification import create_system_notification

create_system_notification(
    user=request.user,
    title="系统通知",
    message="系统维护通知",
    related_url="/maintenance/"
)
```

### 获取通知信息

```python
from test_manager.utils.notification import (
    get_user_unread_count,
    get_user_notifications
)

# 获取未读通知数
unread_count = get_user_unread_count(request.user)

# 获取用户的前 10 条通知
notifications = get_user_notifications(request.user, limit=10)

# 仅获取未读通知
unread_notifications = get_user_notifications(
    request.user, 
    limit=10, 
    unread_only=True
)
```

### 清理旧通知

```python
from test_manager.utils.notification import delete_old_read_notifications

# 删除 30 天前的已读通知
deleted_count = delete_old_read_notifications(request.user, days=30)
print(f"删除了 {deleted_count} 条通知")
```

## 集成示例

### 在测试运行完成后创建通知

在 `test_manager/views/test_views.py` 或相关的测试执行代码中：

```python
from test_manager.utils.notification import create_test_run_notification

def run_test(request, test_id):
    # ... 执行测试代码 ...
    test_run = TestRun.objects.create(...)
    
    # ... 测试运行逻辑 ...
    
    # 测试运行完成后
    test_run.status = 'completed'
    test_run.end_time = timezone.now()
    test_run.save()
    
    # 创建通知
    create_test_run_notification(
        user=test_run.created_by,
        test_run=test_run,
        status=test_run.status
    )
    
    return redirect('test_run_detail', pk=test_run.id)
```

### 在定时任务中创建通知

在 Celery 任务中（如 `test_manager/tasks.py`）：

```python
from celery import shared_task
from test_manager.utils.notification import create_scheduled_task_notification

@shared_task
def execute_scheduled_test(scheduled_task_id):
    scheduled_task = ScheduledTask.objects.get(id=scheduled_task_id)
    
    try:
        # 执行测试
        result = run_tests(scheduled_task)
        
        # 创建成功通知
        create_scheduled_task_notification(
            user=scheduled_task.created_by,
            task_name=scheduled_task.name,
            status='success'
        )
    except Exception as e:
        # 创建失败通知
        create_scheduled_task_notification(
            user=scheduled_task.created_by,
            task_name=scheduled_task.name,
            status='error',
            error_message=str(e)
        )
```

## 管理员功能

### Django Admin 界面

通知可以在 Django 管理后台 (`/admin/`) 中进行管理：

1. 导航到"通知"部分
2. 可以查看、搜索和过滤通知
3. 支持按通知类型、已读状态和日期过滤
4. 可以手动删除通知

## 配置

### 更新检查间隔

在 `templates/base.html` 中的 `NotificationManager` 类中：

```javascript
this.updateInterval = 10000; // 10 秒（单位：毫秒）
```

修改此值可改变通知更新频率。

### 通知类型

在 `test_manager/model/models.py` 中的 `Notification` 模型中定义：

```python
NOTIFICATION_TYPE_CHOICES = [
    ('test_run', '测试运行'),
    ('test_suite_run', '测试套件运行'),
    ('task', '定时任务'),
    ('system', '系统通知'),
    ('other', '其他'),
]
```

可以添加新的通知类型。

## 最佳实践

1. **创建有意义的标题和消息**
   - 标题应该简洁明了
   - 消息应该提供足够的信息，但不要过长

2. **使用正确的通知类型**
   - 使用与内容相匹配的通知类型
   - 这有助于用户过滤和识别通知

3. **提供相关链接**
   - 尽可能提供 `related_url`
   - 用户可以快速导航到相关资源

4. **定期清理旧通知**
   - 使用 `delete_old_read_notifications()` 定期清理
   - 可以在 Celery 定时任务中执行

5. **避免通知泛滥**
   - 仅创建真正重要的通知
   - 避免为每个微小的事件创建通知

## 故障排除

### 通知不显示

1. 确保已运行迁移：`python manage.py migrate`
2. 检查用户是否已认证
3. 查看浏览器控制台是否有错误信息
4. 确保 API 端点可访问

### 通知未更新

1. 检查浏览器网络请求是否成功
2. 验证 CSRF 令牌是否正确传递
3. 检查 Django 日志中的任何错误

### API 错误

确保：
1. 用户已认证
2. 通知 ID 有效
3. 用户有权访问该通知（必须是通知的所有者）

## 相关文件

- **模型**: `test_manager/model/models.py` - `Notification` 类
- **序列化器**: `test_manager/api/serializers.py` - `NotificationSerializer`
- **视图**: `test_manager/api/views.py` - `NotificationViewSet`
- **工具函数**: `test_manager/utils/notification.py` - 通知工具函数
- **前端**: `templates/base.html` - 通知 UI 和 JavaScript
- **Admin**: `test_manager/admin.py` - `NotificationAdmin`

## 版本信息

- 创建日期：2024年
- Django 版本：3.2+
- Python 版本：3.6+
