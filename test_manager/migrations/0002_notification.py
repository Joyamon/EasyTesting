# Generated migration for Notification model

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('test_manager', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('notification_type', models.CharField(
                    choices=[('test_run', '测试运行'), ('test_suite_run', '测试套件运行'), ('task', '定时任务'), ('system', '系统通知'), ('other', '其他')],
                    db_comment='通知类型',
                    default='system',
                    max_length=20,
                    verbose_name='通知类型'
                )),
                ('title', models.CharField(db_comment='通知标题', max_length=255, verbose_name='通知标题')),
                ('message', models.TextField(db_comment='通知内容', verbose_name='通知内容')),
                ('is_read', models.BooleanField(db_comment='是否已读', default=False, verbose_name='是否已读')),
                ('related_url', models.URLField(blank=True, db_comment='相关链接', null=True, verbose_name='相关链接')),
                ('created_at', models.DateTimeField(auto_now_add=True, db_comment='创建时间', verbose_name='创建时间')),
                ('read_at', models.DateTimeField(blank=True, db_comment='已读时间', null=True, verbose_name='已读时间')),
                ('user', models.ForeignKey(db_comment='通知所属用户', on_delete=django.db.models.deletion.CASCADE, related_name='notifications', to=settings.AUTH_USER_MODEL, verbose_name='用户')),
            ],
            options={
                'verbose_name': '通知',
                'verbose_name_plural': '通知',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='notification',
            index=models.Index(fields=['user', '-created_at'], name='test_manager_user_id_created_at_idx'),
        ),
        migrations.AddIndex(
            model_name='notification',
            index=models.Index(fields=['user', 'is_read'], name='test_manager_user_id_is_read_idx'),
        ),
    ]
