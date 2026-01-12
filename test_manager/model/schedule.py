from django.contrib.auth.models import User
from django.db import models

from test_manager.model.models import TestSuite, Environment, TestRun


class ScheduledTask(models.Model):
    """定时任务模型"""
    SCHEDULE_TYPE_CHOICES = [
        ('once', '单次执行'),
        ('daily', '每日执行'),
        ('weekly', '每周执行'),
        ('monthly', '每月执行'),
        ('cron', 'Cron表达式'),
    ]

    STATUS_CHOICES = [
        ('active', '激活'),
        ('inactive', '停用'),
        ('paused', '暂停'),
    ]

    name = models.CharField(max_length=200, verbose_name="任务名称", db_comment="任务名称")
    description = models.TextField(blank=True, verbose_name="任务描述", db_comment="任务描述")
    test_suite = models.ForeignKey(TestSuite, on_delete=models.CASCADE, related_name='scheduled_tasks',
                                   verbose_name="测试套件", db_comment="测试套件")
    environment = models.ForeignKey(Environment, on_delete=models.CASCADE, related_name='scheduled_tasks',
                                    verbose_name="执行环境", db_comment="执行环境", null=True, blank=True)

    # 调度配置
    schedule_type = models.CharField(max_length=20, choices=SCHEDULE_TYPE_CHOICES, default='daily',
                                     verbose_name="调度类型", db_comment="调度类型")
    cron_expression = models.CharField(max_length=100, blank=True, verbose_name="Cron表达式",
                                       db_comment="Cron表达式", help_text="仅当调度类型为Cron时使用")

    # 时间配置
    scheduled_time = models.TimeField(null=True, blank=True, verbose_name="执行时间",
                                      db_comment="执行时间", help_text="每日/每周/每月执行的具体时间")
    scheduled_date = models.DateField(null=True, blank=True, verbose_name="执行日期",
                                      db_comment="执行日期", help_text="单次执行的日期")
    weekday = models.IntegerField(null=True, blank=True, verbose_name="星期几",
                                  db_comment="星期几", help_text="每周执行时的星期几(1-7)")
    day_of_month = models.IntegerField(null=True, blank=True, verbose_name="每月第几天",
                                       db_comment="每月第几天", help_text="每月执行时的日期(1-31)")

    # 任务状态
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active',
                              verbose_name="任务状态", db_comment="任务状态")
    is_enabled = models.BooleanField(default=True, verbose_name="是否启用", db_comment="是否启用")

    # 通知配置
    send_email_notification = models.BooleanField(default=True, verbose_name="发送邮件通知",
                                                  db_comment="发送邮件通知")
    notification_emails = models.TextField(blank=True, verbose_name="通知邮箱",
                                           db_comment="通知邮箱", help_text="多个邮箱用逗号分隔")
    notify_on_success = models.BooleanField(default=False, verbose_name="成功时通知",
                                            db_comment="成功时通知")
    notify_on_failure = models.BooleanField(default=True, verbose_name="失败时通知",
                                            db_comment="失败时通知")

    max_retries = models.IntegerField(default=3, verbose_name="最大重试次数", db_comment="最大重试次数")
    retry_delay = models.IntegerField(default=300, verbose_name="重试间隔(秒)", db_comment="重试间隔(秒)")

    # 执行统计
    last_run_time = models.DateTimeField(null=True, blank=True, verbose_name="上次执行时间",
                                         db_comment="上次执行时间")
    next_run_time = models.DateTimeField(null=True, blank=True, verbose_name="下次执行时间",
                                         db_comment="下次执行时间")
    total_runs = models.IntegerField(default=0, verbose_name="总执行次数", db_comment="总执行次数")
    successful_runs = models.IntegerField(default=0, verbose_name="成功次数", db_comment="成功次数")
    failed_runs = models.IntegerField(default=0, verbose_name="失败次数", db_comment="失败次数")

    # Celery任务ID
    celery_task_id = models.CharField(max_length=255, blank=True, verbose_name="Celery任务ID",
                                      db_comment="Celery任务ID")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间", db_comment="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间", db_comment="更新时间")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_scheduled_tasks',
                                   verbose_name="创建人", db_comment="创建人")

    def __str__(self):
        return f"{self.name} - {self.test_suite.name}"

    class Meta:
        verbose_name = "定时任务"
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

    def get_notification_email_list(self):
        """获取通知邮箱列表"""
        if not self.notification_emails:
            return []
        return [email.strip() for email in self.notification_emails.split(',') if email.strip()]

    def calculate_next_run_time(self):
        """计算下次执行时间"""
        from datetime import datetime, timedelta
        import calendar
        from croniter import croniter

        now = datetime.now()

        if self.schedule_type == 'once':
            if self.scheduled_date and self.scheduled_time:
                next_run = datetime.combine(self.scheduled_date, self.scheduled_time)
                return next_run if next_run > now else None

        elif self.schedule_type == 'daily':
            if self.scheduled_time:
                next_run = datetime.combine(now.date(), self.scheduled_time)
                if next_run <= now:
                    next_run += timedelta(days=1)
                return next_run

        elif self.schedule_type == 'weekly':
            if self.weekday and self.scheduled_time:
                days_ahead = self.weekday - now.weekday()
                if days_ahead <= 0:  # Target day already happened this week
                    days_ahead += 7
                next_run = datetime.combine(now.date(), self.scheduled_time) + timedelta(days=days_ahead)
                return next_run

        elif self.schedule_type == 'monthly':
            if self.day_of_month and self.scheduled_time:
                # 计算下个月的执行时间
                if now.day < self.day_of_month:
                    # 本月还没到执行日期
                    try:
                        next_run = datetime.combine(
                            now.replace(day=self.day_of_month).date(),
                            self.scheduled_time
                        )
                        return next_run
                    except ValueError:
                        # 当月没有这一天，跳到下个月
                        pass

                # 计算下个月
                if now.month == 12:
                    next_year = now.year + 1
                    next_month = 1
                else:
                    next_year = now.year
                    next_month = now.month + 1

                # 确保下个月有这一天
                max_day = calendar.monthrange(next_year, next_month)[1]
                target_day = min(self.day_of_month, max_day)

                next_run = datetime.combine(
                    datetime(next_year, next_month, target_day).date(),
                    self.scheduled_time
                )
                return next_run

        elif self.schedule_type == 'cron' and self.cron_expression:
            # 这里需要使用cron解析库，如croniter
            try:

                cron = croniter(self.cron_expression, now)
                return cron.get_next(datetime)
            except ImportError:
                # 如果没有安装croniter，返回None
                pass

        return None

    def update_next_run_time(self):
        """更新下次执行时间"""
        self.next_run_time = self.calculate_next_run_time()
        self.save(update_fields=['next_run_time'])

    @property
    def success_rate(self):
        """成功率"""
        if self.total_runs == 0:
            return 0
        return (self.successful_runs / self.total_runs) * 100


class TaskExecutionLog(models.Model):
    """任务执行日志"""
    STATUS_CHOICES = [
        ('running', '运行中'),
        ('success', '成功'),
        ('failed', '失败'),
        ('timeout', '超时'),
        ('cancelled', '已取消'),
    ]

    scheduled_task = models.ForeignKey(ScheduledTask, on_delete=models.CASCADE, related_name='execution_logs',
                                       verbose_name="定时任务", db_comment="定时任务")
    test_run = models.ForeignKey(TestRun, on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name='task_execution_logs', verbose_name="测试运行", db_comment="测试运行")

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='running',
                              verbose_name="执行状态", db_comment="执行状态")
    start_time = models.DateTimeField(auto_now_add=True, verbose_name="开始时间", db_comment="开始时间")
    end_time = models.DateTimeField(null=True, blank=True, verbose_name="结束时间", db_comment="结束时间")
    duration = models.FloatField(null=True, blank=True, verbose_name="执行时长(秒)", db_comment="执行时长(秒)")

    # 执行结果统计
    total_test_cases = models.IntegerField(default=0, verbose_name="总测试用例数", db_comment="总测试用例数")
    passed_test_cases = models.IntegerField(default=0, verbose_name="通过用例数", db_comment="通过用例数")
    failed_test_cases = models.IntegerField(default=0, verbose_name="失败用例数", db_comment="失败用例数")
    error_test_cases = models.IntegerField(default=0, verbose_name="错误用例数", db_comment="错误用例数")

    error_message = models.TextField(blank=True, verbose_name="错误信息", db_comment="错误信息")
    retry_count = models.IntegerField(default=0, verbose_name="重试次数", db_comment="重试次数")

    # 通知状态
    email_sent = models.BooleanField(default=False, verbose_name="邮件已发送", db_comment="邮件已发送")
    email_sent_time = models.DateTimeField(null=True, blank=True, verbose_name="邮件发送时间",
                                           db_comment="邮件发送时间")

    def __str__(self):
        return f"{self.scheduled_task.name} - {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}"

    class Meta:
        verbose_name = "任务执行日志"
        verbose_name_plural = verbose_name
        ordering = ['-start_time']

    @property
    def success_rate(self):
        """成功率"""
        if self.total_test_cases == 0:
            return 0
        return (self.passed_test_cases / self.total_test_cases) * 100

    def calculate_duration(self):
        """计算执行时长"""
        if self.start_time and self.end_time:
            self.duration = (self.end_time - self.start_time).total_seconds()
            return self.duration
        return None
