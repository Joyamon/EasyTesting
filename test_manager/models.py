import uuid
from django.urls import reverse
from django.db import models
from django.contrib.auth.models import User
import json


class Project(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_projects')

    def __str__(self):
        return self.name


class Environment(models.Model):
    name = models.CharField(max_length=100)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='environments')
    base_url = models.URLField()
    variables = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.project.name} - {self.name}"


# 测试用例分组
class TestCaseGroup(models.Model):
    name = models.CharField(max_length=100)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='test_case_groups')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_test_case_groups')

    def __str__(self):
        if self.parent:
            return f"{self.parent} / {self.name}"
        return self.name

    class Meta:
        unique_together = ('name', 'project', 'parent')
        ordering = ['name']


class TestCase(models.Model):
    REQUEST_BODY_FORMAT_CHOICES = [
        ('json', 'JSON'),
        ('form-data', 'Form Data'),
    ]

    name = models.CharField(max_length=100)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='test_cases')
    group = models.ForeignKey(TestCaseGroup, on_delete=models.SET_NULL, null=True, blank=True,
                              related_name='test_cases')
    description = models.TextField(blank=True)
    request_method = models.CharField(max_length=10, choices=[
        ('GET', 'GET'),
        ('POST', 'POST'),
        ('PUT', 'PUT'),
        ('DELETE', 'DELETE'),
        ('PATCH', 'PATCH'),
    ])
    request_url = models.CharField(max_length=500)
    request_headers = models.JSONField(default=dict, blank=True)
    request_body = models.JSONField(default=dict, blank=True, null=True)
    request_body_format = models.CharField(max_length=20, choices=REQUEST_BODY_FORMAT_CHOICES, default='json')
    expected_status_code = models.IntegerField(default=200)
    validation_rules = models.JSONField(default=list, blank=True)
    extract_params = models.JSONField(default=list, blank=True)  # 新增字段，用于存储提取的参数
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_test_cases')

    def __str__(self):
        return self.name


# 新增测试套件分组模型
class TestSuiteGroup(models.Model):
    name = models.CharField(max_length=100)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='test_suite_groups')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_test_suite_groups')

    def __str__(self):
        if self.parent:
            return f"{self.parent} / {self.name}"
        return self.name

    class Meta:
        unique_together = ('name', 'project', 'parent')
        ordering = ['name']


class TestSuite(models.Model):
    name = models.CharField(max_length=100)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='test_suites')
    group = models.ForeignKey(TestSuiteGroup, on_delete=models.SET_NULL, null=True, blank=True,
                              related_name='test_suites')
    description = models.TextField(blank=True)
    test_cases = models.ManyToManyField(TestCase, through='TestSuiteCase')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_test_suites')

    def __str__(self):
        return self.name


class TestSuiteCase(models.Model):
    test_suite = models.ForeignKey(TestSuite, on_delete=models.CASCADE)
    test_case = models.ForeignKey(TestCase, on_delete=models.CASCADE)
    environment = models.ForeignKey(Environment, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='test_suite_cases')
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']


class TestRun(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    name = models.CharField(max_length=100)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='test_runs')
    test_suite = models.ForeignKey(TestSuite, on_delete=models.CASCADE, related_name='test_runs', null=True, blank=True)
    environment = models.ForeignKey(Environment, on_delete=models.CASCADE, related_name='test_runs')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_test_runs')

    def __str__(self):
        return self.name

    @property
    def duration(self):
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None


class TestResult(models.Model):
    STATUS_CHOICES = [
        ('passed', 'Passed'),
        ('failed', 'Failed'),
        ('error', 'Error'),
        ('skipped', 'Skipped'),
    ]

    test_run = models.ForeignKey(TestRun, on_delete=models.CASCADE, related_name='test_results')
    test_case = models.ForeignKey(TestCase, on_delete=models.CASCADE, related_name='test_results')
    environment = models.ForeignKey(Environment, on_delete=models.CASCADE, related_name='test_results')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    response_time = models.FloatField(null=True, blank=True)  # in milliseconds
    response_status_code = models.IntegerField(null=True, blank=True)
    response_headers = models.JSONField(default=dict, blank=True)
    response_body = models.JSONField(default=dict, blank=True, null=True)
    request_headers = models.JSONField(default=dict, blank=True)
    request_body = models.JSONField(default=dict, blank=True, null=True)
    error_message = models.TextField(blank=True)
    extracted_params = models.JSONField(default=dict, blank=True)
    validators = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.test_case.name} - {self.status}"


from django.db import models
from django.conf import settings
from django.core.mail import EmailMessage
from django.core.exceptions import ValidationError
import smtplib
import ssl


class EmailConfig(models.Model):
    """邮件配置模型"""
    EMAIL_BACKEND_CHOICES = [
        ('smtp', 'SMTP'),
        ('sendgrid', 'SendGrid API'),
        ('mailgun', 'Mailgun API'),
    ]

    name = models.CharField(max_length=100, verbose_name="配置名称")
    is_active = models.BooleanField(default=False, verbose_name="是否激活")
    email_backend = models.CharField(
        max_length=20,
        choices=EMAIL_BACKEND_CHOICES,
        default='smtp',
        verbose_name="邮件后端"
    )

    # SMTP 设置
    smtp_host = models.CharField(max_length=255, blank=True, verbose_name="SMTP 服务器")
    smtp_port = models.IntegerField(default=587, blank=True, null=True, verbose_name="SMTP 端口")
    smtp_username = models.CharField(max_length=255, blank=True, verbose_name="SMTP 用户名")
    smtp_password = models.CharField(max_length=255, blank=True, verbose_name="SMTP 密码")
    smtp_use_tls = models.BooleanField(default=True, verbose_name="使用 TLS")
    smtp_use_ssl = models.BooleanField(default=False, verbose_name="使用 SSL")

    # API 密钥设置
    api_key = models.CharField(max_length=255, blank=True, verbose_name="API 密钥")

    # 通用设置
    default_from_email = models.EmailField(verbose_name="默认发件人邮箱")
    default_from_name = models.CharField(max_length=100, verbose_name="默认发件人名称")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        verbose_name = "邮件配置"
        verbose_name_plural = "邮件配置"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # 如果当前配置被设置为激活，则将其他配置设置为非激活
        if self.is_active:
            EmailConfig.objects.filter(is_active=True).update(is_active=False)
        super().save(*args, **kwargs)

    def clean(self):
        """验证邮件配置"""
        if self.email_backend == 'smtp':
            if not self.smtp_host or not self.smtp_username or not self.smtp_password:
                raise ValidationError("SMTP 配置需要填写服务器、用户名和密码")
        elif self.email_backend in ['sendgrid', 'mailgun']:
            if not self.api_key:
                raise ValidationError(f"{self.get_email_backend_display()} 配置需要填写 API 密钥")

    def test_connection(self):
        """测试邮件连接"""
        if self.email_backend == 'smtp':
            try:
                if self.smtp_use_ssl:
                    server = smtplib.SMTP_SSL(self.smtp_host, self.smtp_port, context=ssl.create_default_context())
                else:
                    server = smtplib.SMTP(self.smtp_host, self.smtp_port)
                    if self.smtp_use_tls:
                        server.starttls(context=ssl.create_default_context())

                server.login(self.smtp_username, self.smtp_password)
                server.quit()
                return True, "SMTP 连接测试成功"
            except Exception as e:
                return False, f"SMTP 连接测试失败: {str(e)}"
        elif self.email_backend == 'sendgrid':
            # 这里可以添加 SendGrid API 测试代码
            return True, "SendGrid API 配置已保存"
        elif self.email_backend == 'mailgun':
            # 这里可以添加 Mailgun API 测试代码
            return True, "Mailgun API 配置已保存"

        return False, "未知的邮件后端"

    def send_test_email(self, to_email):
        """发送测试邮件"""
        global current_backend, current_host, current_port, current_user, current_password, current_tls, current_ssl, current_from
        subject = "EasyTesting - 测试邮件"
        message = "这是一封测试邮件，用于验证 EasyTesting 的邮件发送功能是否正常工作。"
        from_email = f"{self.default_from_name} <{self.default_from_email}>"

        try:
            # 保存当前设置
            current_backend = settings.EMAIL_BACKEND
            current_host = settings.EMAIL_HOST
            current_port = settings.EMAIL_PORT
            current_user = settings.EMAIL_HOST_USER
            current_password = settings.EMAIL_HOST_PASSWORD
            current_tls = settings.EMAIL_USE_TLS
            current_ssl = getattr(settings, 'EMAIL_USE_SSL', False)
            current_from = settings.DEFAULT_FROM_EMAIL

            # 应用临时设置
            if self.email_backend == 'smtp':
                settings.EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
                settings.EMAIL_HOST = self.smtp_host
                settings.EMAIL_PORT = self.smtp_port
                settings.EMAIL_HOST_USER = self.smtp_username
                settings.EMAIL_HOST_PASSWORD = self.smtp_password
                settings.EMAIL_USE_TLS = self.smtp_use_tls
                settings.EMAIL_USE_SSL = self.smtp_use_ssl
            elif self.email_backend == 'sendgrid':
                settings.EMAIL_BACKEND = 'sendgrid_backend.SendgridBackend'
                settings.SENDGRID_API_KEY = self.api_key
            elif self.email_backend == 'mailgun':
                settings.EMAIL_BACKEND = 'django_mailgun.MailgunBackend'
                settings.MAILGUN_ACCESS_KEY = self.api_key
                settings.MAILGUN_SERVER_NAME = self.smtp_host  # 使用 smtp_host 存储 Mailgun 域名

            settings.DEFAULT_FROM_EMAIL = from_email

            # 发送测试邮件
            email = EmailMessage(
                subject=subject,
                body=message,
                from_email=from_email,
                to=[to_email],
                reply_to=[self.default_from_email],
            )
            email.send(fail_silently=False)

            # 恢复原始设置
            settings.EMAIL_BACKEND = current_backend
            settings.EMAIL_HOST = current_host
            settings.EMAIL_PORT = current_port
            settings.EMAIL_HOST_USER = current_user
            settings.EMAIL_HOST_PASSWORD = current_password
            settings.EMAIL_USE_TLS = current_tls
            settings.EMAIL_USE_SSL = current_ssl
            settings.DEFAULT_FROM_EMAIL = current_from

            return True, "测试邮件发送成功"
        except Exception as e:
            # 恢复原始设置
            settings.EMAIL_BACKEND = current_backend
            settings.EMAIL_HOST = current_host
            settings.EMAIL_PORT = current_port
            settings.EMAIL_HOST_USER = current_user
            settings.EMAIL_HOST_PASSWORD = current_password
            settings.EMAIL_USE_TLS = current_tls
            settings.EMAIL_USE_SSL = current_ssl
            settings.DEFAULT_FROM_EMAIL = current_from

            return False, f"测试邮件发送失败: {str(e)}"

    @classmethod
    def get_active_config(cls):
        """获取当前激活的邮件配置"""
        try:
            return cls.objects.get(is_active=True)
        except cls.DoesNotExist:
            return None

    @classmethod
    def apply_active_config(cls):
        """应用当前激活的邮件配置到 Django 设置"""
        config = cls.get_active_config()
        if not config:
            return False

        if config.email_backend == 'smtp':
            settings.EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
            settings.EMAIL_HOST = config.smtp_host
            settings.EMAIL_PORT = config.smtp_port
            settings.EMAIL_HOST_USER = config.smtp_username
            settings.EMAIL_HOST_PASSWORD = config.smtp_password
            settings.EMAIL_USE_TLS = config.smtp_use_tls
            settings.EMAIL_USE_SSL = config.smtp_use_ssl
        elif config.email_backend == 'sendgrid':
            settings.EMAIL_BACKEND = 'sendgrid_backend.SendgridBackend'
            settings.SENDGRID_API_KEY = config.api_key
        elif config.email_backend == 'mailgun':
            settings.EMAIL_BACKEND = 'django_mailgun.MailgunBackend'
            settings.MAILGUN_ACCESS_KEY = config.api_key
            settings.MAILGUN_SERVER_NAME = config.smtp_host  # 使用 smtp_host 存储 Mailgun 域名

        settings.DEFAULT_FROM_EMAIL = f"{config.default_from_name} <{config.default_from_email}>"
        return True


class TestSuiteRun(models.Model):
    name = models.CharField(max_length=100)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='test_suite_runs')
    test_suite = models.ForeignKey(TestSuite, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='test_suite_runs')
    environment = models.ForeignKey(Environment, on_delete=models.CASCADE, related_name='test_suite_runs')
    status = models.CharField(max_length=20, choices=TestRun.STATUS_CHOICES, default='pending')
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_test_suite_runs')

    def __str__(self):
        return self.name

    @property
    def duration(self):
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None


class TestReport(models.Model):
    """测试报告模型"""
    REPORT_TYPE_CHOICES = [
        ('test_run', 'Test Run'),
        ('test_suite_run', 'Test Suite Run'),
        ('custom', 'Custom'),
    ]

    REPORT_FORMAT_CHOICES = [
        ('html', 'HTML'),
        ('pdf', 'PDF'),
        ('json', 'JSON'),
    ]

    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='test_reports')
    report_type = models.CharField(max_length=20, choices=REPORT_TYPE_CHOICES, default='test_run')
    report_format = models.CharField(max_length=10, choices=REPORT_FORMAT_CHOICES, default='html')
    content = models.TextField()
    test_run = models.ForeignKey(TestRun, on_delete=models.SET_NULL, null=True, blank=True, related_name='reports')
    test_suite_run = models.ForeignKey(TestSuiteRun, on_delete=models.SET_NULL, null=True, blank=True,
                                       related_name='reports')
    is_public = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('test_report_detail', kwargs={'pk': self.pk})

    def get_delete_url(self):
        return reverse('test_report_delete', kwargs={'pk': self.pk})

    def get_summary(self):
        """返回报告的摘要信息"""
        if self.report_format == 'json':
            try:
                data = json.loads(self.content)
                return {
                    'total': data.get('total', 0),
                    'passed': data.get('passed', 0),
                    'failed': data.get('failed', 0),
                    'error': data.get('error', 0),
                    'skipped': data.get('skipped', 0),
                    'success_rate': data.get('success_rate', '0%'),
                }
            except:
                return {}
        return {}
