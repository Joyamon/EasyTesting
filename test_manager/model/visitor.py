from django.contrib.auth.models import User
from django.db import models


class VisitorLog(models.Model):
    """访客记录模型"""
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='visitor_logs',
        verbose_name="访问用户",
        db_comment="访问用户（如果已登录）"
    )
    ip_address = models.GenericIPAddressField(
        verbose_name="IP地址",
        db_comment="访客IP地址"
    )
    user_agent = models.CharField(
        max_length=500,
        blank=True,
        verbose_name="用户代理",
        db_comment="浏览器用户代理信息"
    )
    path = models.CharField(
        max_length=500,
        verbose_name="访问路径",
        db_comment="访问的URL路径"
    )
    method = models.CharField(
        max_length=10,
        default='GET',
        verbose_name="请求方法",
        db_comment="HTTP请求方法"
    )
    referer = models.CharField(
        max_length=500,
        blank=True,
        verbose_name="来源页面",
        db_comment="来源页面URL"
    )
    session_key = models.CharField(
        max_length=40,
        blank=True,
        verbose_name="会话KEY",
        db_comment="Django会话KEY"
    )
    platform = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="平台",
        db_comment="访问平台"
    )
    browser_type = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="浏览器",
        db_comment="访问浏览器"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="访问时间",
        db_comment="访问时间",
        db_index=True
    )

    def __str__(self):
        user_str = self.user.username if self.user else 'Anonymous'
        return f"{user_str} - {self.ip_address} - {self.path} - {self.created_at.strftime('%Y-%m-%d %H:%M:%S')}"

    @property
    def browser(self):
        """解析浏览器类型"""
        br = self.browser_type.lower()
        if 'chrome' in br:
            return 'Chrome'
        elif 'firefox' in br:
            return 'Firefox'
        elif 'safari' in br:
            return 'Safari'
        elif 'edge' in br:
            return 'Edge'
        elif 'msie' in br or 'trident' in br:
            return 'IE'
        else:
            return 'Unknown'

    @property
    def os(self):
        """解析操作系统"""
        pl = self.platform.lower()
        if 'windows' in pl:
            return 'Windows'
        elif 'mac' in pl:
            return 'MacOS'
        elif 'linux' in pl:
            return 'Linux'
        elif 'android' in pl:
            return 'Android'
        elif 'iphone' in pl or 'ipad' in pl:
            return 'iOS'
        else:
            return 'Unknown'

    class Meta:
        verbose_name = "访客记录"
        verbose_name_plural = verbose_name
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['ip_address']),
            models.Index(fields=['user']),
        ]
