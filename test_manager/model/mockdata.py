from django.contrib.auth.models import User
import json
from django.db import models


class MockData(models.Model):
    """模拟数据模型"""
    aim = models.CharField(max_length=255, verbose_name="用途", db_comment="用途")
    data = models.TextField(verbose_name="mock数据", db_comment="mock数据")
    description = models.TextField(verbose_name="数据描述", db_comment="数据描述", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间", db_comment="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间", db_comment="更新时间")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_mock_data',
                                   verbose_name="创建人", db_comment="创建人")

    def __str__(self):
        return self.description

    @property
    def count_data(self):
        return len(json.loads(self.data))

    class Meta:
        verbose_name = "模拟数据"
        verbose_name_plural = verbose_name
