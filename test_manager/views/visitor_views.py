from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST
from django.utils import timezone
from test_manager.model.visitor import VisitorLog
from test_manager.views.common import paginate_queryset


@login_required
def visitor_log_list(request):
    """访客记录列表"""
    # 获取筛选参数
    ip_filter = request.GET.get('ip', '')
    user_filter = request.GET.get('user', '')
    path_filter = request.GET.get('path', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')

    # 构建查询
    visitor_logs = VisitorLog.objects.all()

    if ip_filter:
        visitor_logs = visitor_logs.filter(ip_address__icontains=ip_filter)

    if user_filter:
        visitor_logs = visitor_logs.filter(
            Q(user__username__icontains=user_filter) |
            Q(user__email__icontains=user_filter)
        )

    if path_filter:
        visitor_logs = visitor_logs.filter(path__icontains=path_filter)

    if date_from:
        try:
            from_date = timezone.datetime.strptime(date_from, '%Y-%m-%d')
            from_date = timezone.make_aware(from_date)
            visitor_logs = visitor_logs.filter(created_at__gte=from_date)
        except ValueError:
            pass

    if date_to:
        try:
            to_date = timezone.datetime.strptime(date_to, '%Y-%m-%d')
            to_date = timezone.make_aware(to_date) + timedelta(days=1)
            visitor_logs = visitor_logs.filter(created_at__lt=to_date)
        except ValueError:
            pass

    # 获取统计数据
    total_visits = visitor_logs.count()
    unique_ips = visitor_logs.values('ip_address').distinct().count()
    authenticated_visits = visitor_logs.filter(user__isnull=False).count()

    # 分页
    visitor_logs_page = paginate_queryset(request, visitor_logs, 10)

    context = {
        'visitor_logs': visitor_logs_page,
        'total_visits': total_visits,
        'unique_ips': unique_ips,
        'authenticated_visits': authenticated_visits,
        'ip_filter': ip_filter,
        'user_filter': user_filter,
        'path_filter': path_filter,
        'date_from': date_from,
        'date_to': date_to,
    }

    return render(request, 'test_manager/visitor_log_list.html', context)


@login_required
def visitor_log_stats(request):
    """访客统计数据API"""
    from django.db.models import Count
    from django.db.models.functions import TruncDate

    # 获取时间范围参数
    days = int(request.GET.get('days', 7))
    start_date = timezone.now() - timedelta(days=days)

    # 按日期统计访问量
    daily_stats = (
        VisitorLog.objects
        .filter(created_at__gte=start_date)
        .annotate(date=TruncDate('created_at'))
        .values('date')
        .annotate(count=Count('id'))
        .order_by('date')
    )

    # 按IP统计TOP访客
    top_ips = (
        VisitorLog.objects
        .filter(created_at__gte=start_date)
        .values('ip_address')
        .annotate(count=Count('id'))
        .order_by('-count')[:10]
    )

    # 按路径统计热门页面
    top_paths = (
        VisitorLog.objects
        .filter(created_at__gte=start_date)
        .values('path')
        .annotate(count=Count('id'))
        .order_by('-count')[:10]
    )

    # 按浏览器统计
    all_logs = VisitorLog.objects.filter(created_at__gte=start_date)
    browser_stats = {}
    for log in all_logs:
        browser = log.browser
        browser_stats[browser] = browser_stats.get(browser, 0) + 1

    # 按操作系统统计
    os_stats = {}
    for log in all_logs:
        os = log.os
        os_stats[os] = os_stats.get(os, 0) + 1

    data = {
        'daily_stats': [
            {'date': item['date'].strftime('%Y-%m-%d'), 'count': item['count']}
            for item in daily_stats
        ],
        'top_ips': [
            {'ip': item['ip_address'], 'count': item['count']}
            for item in top_ips
        ],
        'top_paths': [
            {'path': item['path'], 'count': item['count']}
            for item in top_paths
        ],
        'browser_stats': [
            {'browser': k, 'count': v}
            for k, v in browser_stats.items()
        ],
        'os_stats': [
            {'os': k, 'count': v}
            for k, v in os_stats.items()
        ],
    }

    return JsonResponse(data)


@login_required
@require_POST
def visitor_log_clear(request):
    """清空访客记录"""
    try:
        days = int(request.POST.get('days', 30))
        cutoff_date = timezone.now() - timedelta(days=days)

        deleted_count = VisitorLog.objects.filter(created_at__lt=cutoff_date).delete()[0]

        return JsonResponse({
            'success': True,
            'message': f'成功删除 {deleted_count} 条访客记录',
            'deleted_count': deleted_count
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'删除失败: {str(e)}'
        }, status=400)
