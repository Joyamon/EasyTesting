"""
通知工具函数

提供创建和管理通知的功能
"""

from django.contrib.auth.models import User
from test_manager.model.models import Notification


def create_notification(user, title, message, notification_type='system', related_url=None):
    """
    创建一个通知

    Args:
        user: 用户对象或用户ID
        title: 通知标题
        message: 通知内容
        notification_type: 通知类型 ('test_run', 'test_suite_run', 'task', 'system', 'other')
        related_url: 相关链接 (可选)

    Returns:
        创建的 Notification 对象
    """
    if isinstance(user, int):
        user = User.objects.get(id=user)
    
    notification = Notification.objects.create(
        user=user,
        title=title,
        message=message,
        notification_type=notification_type,
        related_url=related_url
    )
    return notification


def create_test_run_notification(user, test_run, status):
    """
    创建测试运行通知

    Args:
        user: 用户对象或用户ID
        test_run: TestRun 对象
        status: 运行状态 ('completed', 'failed', 等)

    Returns:
        创建的 Notification 对象
    """
    status_text = {
        'completed': '已完成',
        'failed': '失败',
        'running': '运行中',
        'pending': '待运行',
    }.get(status, status)

    title = f"测试运行 - {test_run.name}"
    message = f"测试运行 '{test_run.name}' 已{status_text}"
    
    return create_notification(
        user=user,
        title=title,
        message=message,
        notification_type='test_run',
        related_url=f'/test-runs/{test_run.id}/'
    )


def create_test_suite_run_notification(user, test_suite_run, status):
    """
    创建测试套件运行通知

    Args:
        user: 用户对象或用户ID
        test_suite_run: TestSuiteRun 对象
        status: 运行状态

    Returns:
        创建的 Notification 对象
    """
    status_text = {
        'completed': '已完成',
        'failed': '失败',
        'running': '运行中',
        'pending': '待运行',
    }.get(status, status)

    title = f"测试套件运行 - {test_suite_run.name}"
    message = f"测试套件运行 '{test_suite_run.name}' 已{status_text}"
    
    return create_notification(
        user=user,
        title=title,
        message=message,
        notification_type='test_suite_run',
        related_url=f'/test-suite-runs/{test_suite_run.id}/'
    )


def create_scheduled_task_notification(user, task_name, status, error_message=None):
    """
    创建定时任务通知

    Args:
        user: 用户对象或用户ID
        task_name: 任务名称
        status: 任务状态 ('success', 'failed', 'error')
        error_message: 错误信息 (如果有的话)

    Returns:
        创建的 Notification 对象
    """
    status_text = {
        'success': '成功完成',
        'failed': '执行失败',
        'error': '发生错误',
    }.get(status, status)

    title = f"定时任务 - {task_name}"
    message = f"定时任务 '{task_name}' {status_text}"
    
    if error_message:
        message += f": {error_message[:100]}"

    return create_notification(
        user=user,
        title=title,
        message=message,
        notification_type='task'
    )


def create_system_notification(user, title, message, related_url=None):
    """
    创建系统通知

    Args:
        user: 用户对象或用户ID
        title: 通知标题
        message: 通知内容
        related_url: 相关链接 (可选)

    Returns:
        创建的 Notification 对象
    """
    return create_notification(
        user=user,
        title=title,
        message=message,
        notification_type='system',
        related_url=related_url
    )


def get_user_unread_count(user):
    """
    获取用户的未读通知数

    Args:
        user: 用户对象

    Returns:
        未读通知数
    """
    return Notification.objects.filter(user=user, is_read=False).count()


def get_user_notifications(user, limit=10, unread_only=False):
    """
    获取用户的通知列表

    Args:
        user: 用户对象
        limit: 返回的通知数量限制
        unread_only: 是否仅返回未读通知

    Returns:
        通知 QuerySet
    """
    queryset = Notification.objects.filter(user=user)
    
    if unread_only:
        queryset = queryset.filter(is_read=False)
    
    return queryset.order_by('-created_at')[:limit]


def delete_old_read_notifications(user, days=30):
    """
    删除用户的旧的已读通知

    Args:
        user: 用户对象
        days: 保留多少天内的通知

    Returns:
        被删除的通知数量
    """
    from django.utils import timezone
    from datetime import timedelta
    
    cutoff_date = timezone.now() - timedelta(days=days)
    deleted_count, _ = Notification.objects.filter(
        user=user,
        is_read=True,
        created_at__lt=cutoff_date
    ).delete()
    
    return deleted_count
