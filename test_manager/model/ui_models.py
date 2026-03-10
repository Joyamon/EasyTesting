from django.db import models
from django.contrib.auth.models import User
from django.utils.safestring import mark_safe

from .models import TestCase, TestRun, Environment


class UITestStep(models.Model):
    """UI 测试步骤模型

    用于定义 UI 自动化测试的每个操作步骤
    """
    ACTION_TYPES = [
        ('navigate', '导航到页面'),
        ('click', '点击元素'),
        ('fill', '输入文本'),
        ('select', '选择选项'),
        ('hover', '鼠标悬停'),
        ('wait', '等待元素'),
        ('assert_visible', '验证可见'),
        ('assert_text', '验证文本'),
        ('assert_url', '验证 URL'),
        ('screenshot', '截图'),
        ('scroll', '滚动'),
        ('keyboard', '键盘操作'),
        ('upload_file', '上传文件'),
        ('double_click', '双击'),
        ('right_click', '右击'),
    ]

    SELECTOR_TYPES = [
        ('css', 'CSS Selector'),
        ('xpath', 'XPath'),
        ('id', 'Element ID'),
        ('text', 'Text Content'),
    ]

    test_case = models.ForeignKey(TestCase, on_delete=models.CASCADE, related_name='ui_steps',
                                  verbose_name="测试用例", db_comment="所属测试用例")
    step_number = models.IntegerField(verbose_name="步骤序号", db_comment="步骤执行序号")
    action_type = models.CharField(max_length=20, choices=ACTION_TYPES,
                                   verbose_name="动作类型", db_comment="动作类型")
    action_value = models.TextField(null=True, blank=True, verbose_name="动作值",
                                    db_comment="动作值（如输入的文本、导航的 URL）")
    element_selector = models.CharField(max_length=500, verbose_name="元素",
                                        db_comment="元素选择器（CSS/XPath 等）", blank=True)
    selector_type = models.CharField(max_length=10, choices=SELECTOR_TYPES, default='css',
                                     verbose_name="选择器类型", db_comment="选择器类型")

    expected_result = models.TextField(null=True, blank=True, verbose_name="预期结果",
                                       db_comment="预期结果（用于断言）")
    timeout = models.IntegerField(default=10, verbose_name="超时时间（秒）",
                                  db_comment="超时时间（秒），默认 10 秒")
    description = models.TextField(blank=True, verbose_name="步骤描述",
                                   db_comment="步骤描述，用于理解步骤作用")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间",
                                      db_comment="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间",
                                      db_comment="更新时间")

    class Meta:
        ordering = ['test_case', 'step_number']
        unique_together = ('test_case', 'step_number')
        verbose_name = "UI 测试步骤"
        verbose_name_plural = "UI 测试步骤"
        indexes = [
            models.Index(fields=['test_case', 'step_number']),
        ]

    def __str__(self):
        return f"{self.test_case.name} - Step {self.step_number}: {self.get_action_type_display()}"


class UITestResult(models.Model):
    """UI 测试结果模型

    记录 UI 自动化测试的执行结果
    """
    STATUS_CHOICES = [
        ('passed', '通过'),
        ('failed', '失败'),
        ('error', '错误'),
    ]

    test_run = models.ForeignKey(TestRun, on_delete=models.CASCADE, related_name='ui_results',
                                 verbose_name="测试运行", db_comment="所属测试运行")
    test_case = models.ForeignKey(TestCase, on_delete=models.CASCADE, related_name='ui_results',
                                  verbose_name="测试用例", db_comment="测试用例")
    environment = models.ForeignKey(Environment, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='ui_results', verbose_name="执行环境",
                                    db_comment="执行环境")

    # 基本信息
    status = models.CharField(max_length=20, choices=STATUS_CHOICES,
                              verbose_name="执行状态", db_comment="执行状态")
    duration = models.FloatField(verbose_name="执行时间（秒）",
                                 db_comment="执行时间（秒）", null=True, blank=True)
    error_message = models.TextField(blank=True, verbose_name="错误信息",
                                     db_comment="执行失败时的错误信息")

    # 步骤统计
    steps_executed = models.IntegerField(default=0, verbose_name="执行步骤数",
                                         db_comment="执行的步骤总数")
    steps_passed = models.IntegerField(default=0, verbose_name="通过步骤数",
                                       db_comment="通过的步骤数")
    steps_failed = models.IntegerField(default=0, verbose_name="失败步骤数",
                                       db_comment="失败的步骤数")

    # 截图和视频
    screenshots = models.JSONField(default=list, verbose_name="截图列表",db_comment="执行过程中的截图路径列表")

    video_path = models.FileField(upload_to='ui_test_videos/', null=True, blank=True,
                                  verbose_name="视频录制", db_comment="测试执行视频录制文件")

    # 性能指标
    page_load_time = models.FloatField(null=True, blank=True, verbose_name="页面加载时间（ms）",
                                       db_comment="页面完全加载时间（毫秒）")
    first_contentful_paint = models.FloatField(null=True, blank=True, verbose_name="FCP（ms）",
                                               db_comment="首次内容绘制时间（毫秒）")
    largest_contentful_paint = models.FloatField(null=True, blank=True, verbose_name="LCP（ms）",
                                                 db_comment="最大内容绘制时间（毫秒）")

    # 执行详情
    browser_type = models.CharField(max_length=20, default='chromium',
                                    verbose_name="浏览器类型", db_comment="使用的浏览器类型")
    browser_version = models.CharField(max_length=50, blank=True,
                                       verbose_name="浏览器版本", db_comment="浏览器版本")

    # 步骤详情（JSON 格式，用于详细日志）
    step_details = models.JSONField(default=list, verbose_name="步骤详情",
                                    db_comment="每个步骤的详细执行日志")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间",
                                      db_comment="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间",
                                      db_comment="更新时间")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='executed_test_runs',
                                   verbose_name="执行人", db_comment="执行人")

    class Meta:
        ordering = ['-created_at']
        verbose_name = "UI 测试结果"
        verbose_name_plural = "UI 测试结果"
        indexes = [
            models.Index(fields=['test_run', '-created_at']),
            models.Index(fields=['test_case', '-created_at']),
            models.Index(fields=['status', '-created_at']),
        ]

    def __str__(self):
        return f"{self.test_case.name} - {self.get_status_display()}"


class UITestSession(models.Model):
    """UI 测试会话模型

    用于跟踪长期的 UI 测试会话，支持会话重用和并发测试
    """
    STATUS_CHOICES = [
        ('active', '活跃'),
        ('idle', '空闲'),
        ('closed', '已关闭'),
    ]

    session_id = models.CharField(max_length=100, unique=True,
                                  verbose_name="会话 ID", db_comment="唯一的会话标识符")
    browser_type = models.CharField(max_length=20, default='chromium',
                                    verbose_name="浏览器类型", db_comment="浏览器类型")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active',
                              verbose_name="会话状态", db_comment="会话状态")

    # 会话信息
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True,
                             related_name='ui_sessions', verbose_name="用户",
                             db_comment="创建此会话的用户")
    project = models.ForeignKey('test_manager.Project', on_delete=models.CASCADE, null=True, blank=True,
                                related_name='ui_sessions', verbose_name="项目",
                                db_comment="所属项目")

    # 浏览器进程信息
    process_id = models.IntegerField(null=True, blank=True,
                                     verbose_name="浏览器进程 ID", db_comment="浏览器进程 ID")

    # 时间跟踪
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间",
                                      db_comment="会话创建时间")
    last_activity_at = models.DateTimeField(auto_now=True, verbose_name="最后活动时间",
                                            db_comment="最后一次活动时间")
    closed_at = models.DateTimeField(null=True, blank=True, verbose_name="关闭时间",
                                     db_comment="会话关闭时间")

    class Meta:
        ordering = ['-created_at']
        verbose_name = "UI 测试会话"
        verbose_name_plural = "UI 测试会话"
        indexes = [
            models.Index(fields=['session_id']),
            models.Index(fields=['status', '-last_activity_at']),
        ]

    def __str__(self):
        return f"Session {self.session_id[:8]}... ({self.get_status_display()})"
