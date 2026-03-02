"""
示例管理命令：创建示例通知

用法：
    python manage.py create_sample_notification
    python manage.py create_sample_notification --user <username>
    python manage.py create_sample_notification --type test_run
"""

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from test_manager.utils.notification import (
    create_notification,
    create_test_run_notification,
    create_scheduled_task_notification,
    create_system_notification
)
from test_manager.model.models import TestRun


class Command(BaseCommand):
    help = '创建示例通知用于测试'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user',
            type=str,
            help='指定用户名',
        )
        parser.add_argument(
            '--type',
            type=str,
            choices=['system', 'test_run', 'task'],
            default='system',
            help='通知类型',
        )

    def handle(self, *args, **options):
        # 获取或指定用户
        username = options.get('user')
        
        if username:
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                raise CommandError(f'用户 "{username}" 不存在')
        else:
            # 使用第一个超级用户或第一个用户
            user = User.objects.filter(is_superuser=True).first()
            if not user:
                user = User.objects.first()
            
            if not user:
                raise CommandError('找不到任何用户，请先创建用户')
        
        notification_type = options.get('type')
        
        # 创建示例通知
        if notification_type == 'system':
            notification = create_system_notification(
                user=user,
                title='系统通知示例',
                message='这是一条系统通知的示例消息。您可以在通知中心查看所有通知。'
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f'✓ 已创建系统通知：{notification.title} (ID: {notification.id})'
                )
            )
        
        elif notification_type == 'test_run':
            notification = create_notification(
                user=user,
                title='测试运行通知示例',
                message='示例测试运行已完成。点击查看详细结果。',
                notification_type='test_run',
                related_url='/test-runs/1/'
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f'✓ 已创建测试运行通知：{notification.title} (ID: {notification.id})'
                )
            )
        
        elif notification_type == 'task':
            notification = create_scheduled_task_notification(
                user=user,
                task_name='示例定时任务',
                status='success',
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f'✓ 已创建定时任务通知：{notification.title} (ID: {notification.id})'
                )
            )
        
        # 显示用户信息
        self.stdout.write(f'\n用户: {user.username} (ID: {user.id})')
        self.stdout.write(f'邮箱: {user.email}')
        
        # 显示用户的通知统计
        from test_manager.utils.notification import (
            get_user_unread_count,
            get_user_notifications
        )
        
        unread_count = get_user_unread_count(user)
        total_notifications = user.notifications.count()
        
        self.stdout.write(f'\n通知统计:')
        self.stdout.write(f'  总通知数: {total_notifications}')
        self.stdout.write(f'  未读通知: {unread_count}')
        
        # 显示最近的通知
        recent = get_user_notifications(user, limit=5)
        if recent:
            self.stdout.write(f'\n最近 5 条通知:')
            for i, notif in enumerate(recent, 1):
                status = '✓ 已读' if notif.is_read else '✗ 未读'
                self.stdout.write(
                    f'  {i}. [{status}] {notif.title}'
                )
        
        self.stdout.write(
            self.style.SUCCESS('\n✓ 命令执行成功！')
        )
        self.stdout.write(
            '\n提示: 现在可以访问 /api/notifications/ 来查看通知 API\n'
        )
