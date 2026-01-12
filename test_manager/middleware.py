import logging
from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger('test_manager.visitor')


class VisitorTrackingMiddleware(MiddlewareMixin):
    """
    访客追踪中间件
    记录所有HTTP请求的访客信息，包括IP地址、访问时间、访问路径等
    """

    # 排除不需要记录的路径
    EXCLUDED_PATHS = [
        '/static/',
        '/media/',
        '/favicon.ico',
        '/admin/jsi18n/',
    ]

    def process_request(self, request):
        """处理请求，记录访客信息"""
        try:
            # 检查是否需要排除此路径
            if self._should_exclude_path(request.path):
                return None

            # 获取访客IP地址
            ip_address = self._get_client_ip(request)

            # 获取用户代理
            user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]

            # 获取访问路径
            path = request.path
            method = request.method

            # 获取来源页面
            referer = request.META.get('HTTP_REFERER', '')[:500]
            platform = request.META.get('HTTP_SEC_CH_UA_PLATFORM', '')
            browser = request.META.get('HTTP_SEC_CH_UA', '')

            # 获取用户（如果已登录）
            user = request.user if request.user.is_authenticated else None

            # 延迟导入模型，避免循环导入
            from .models import VisitorLog

            # 创建访客记录
            VisitorLog.objects.create(
                user=user,
                ip_address=ip_address,
                user_agent=user_agent,
                path=path,
                method=method,
                referer=referer,
                session_key=request.session.session_key or '',
                platform=platform,
                browser_type=browser
            )

            logger.info(f"访客记录: {ip_address} - {method} {path}")

        except Exception as e:
            # 记录错误但不影响正常请求
            logger.error(f"记录访客信息失败: {str(e)}")

        return None

    def _get_client_ip(self, request):
        """获取客户端真实IP地址"""
        # 尝试从代理头获取真实IP
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '')
        return ip

    def _should_exclude_path(self, path):
        """判断是否应该排除此路径"""
        for excluded_path in self.EXCLUDED_PATHS:
            if path.startswith(excluded_path):
                return True
        return False
