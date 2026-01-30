from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.core.cache import cache
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

    # 1. 先构建基础查询
    base_query = VisitorLog.objects.all()
    filtered_query = base_query

    # 应用筛选条件
    if ip_filter:
        filtered_query = filtered_query.filter(ip_address__icontains=ip_filter)

    if user_filter:
        filtered_query = filtered_query.filter(
            Q(user__username__icontains=user_filter) |
            Q(user__email__icontains=user_filter)
        )

    if path_filter:
        filtered_query = filtered_query.filter(path__icontains=path_filter)

    if date_from:
        try:
            from_date = timezone.datetime.strptime(date_from, '%Y-%m-%d')
            from_date = timezone.make_aware(from_date)
            filtered_query = filtered_query.filter(created_at__gte=from_date)
        except ValueError:
            pass

    if date_to:
        try:
            to_date = timezone.datetime.strptime(date_to, '%Y-%m-%d')
            to_date = timezone.make_aware(to_date) + timedelta(days=1)
            filtered_query = filtered_query.filter(created_at__lt=to_date)
        except ValueError:
            pass

    # 2. 使用子查询优化统计，避免重复计算
    # 获取分页数据（只查询需要的字段）
    visitor_logs_page = paginate_queryset(
        request,
        filtered_query.select_related('user').only(
            'id', 'ip_address', 'user__username',
            'path', 'method', 'referer', 'created_at'
        ),
        20  # 适当增加每页数量减少查询次数
    )

    # 3. 异步或延迟加载统计数据
    # 只在需要时计算统计数据
    total_visits = None
    unique_ips = None
    authenticated_visits = None

    # 只有在小数据量或明确需要时才计算统计
    if not ip_filter and not user_filter and not path_filter and not date_from and not date_to:
        # 使用缓存获取统计数据
        cache_key = f'visitor_stats_{date_from}_{date_to}'
        stats = cache.get(cache_key)

        if not stats:
            # 批量计算统计
            stats = calculate_visitor_stats(date_from, date_to)
            cache.set(cache_key, stats, 300)  # 缓存5分钟

        total_visits = stats['total_visits']
        unique_ips = stats['unique_ips']
        authenticated_visits = stats['authenticated_visits']
    else:
        # 对于筛选后的数据，只计算必要的统计
        total_visits = filtered_query.count()

        # 使用近似统计，避免distinct count在大数据集上的性能问题
        if filtered_query.count() < 10000:
            unique_ips = filtered_query.values('ip_address').distinct().count()
            authenticated_visits = filtered_query.filter(user__isnull=False).count()
        else:
            # 大数据集使用近似统计或跳过
            unique_ips = "N/A (数据集过大)"
            authenticated_visits = "N/A (数据集过大)"

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


def calculate_visitor_stats(date_from=None, date_to=None):
    """计算访客统计数据 - 可缓存"""
    from django.db.models import Count
    from django.utils import timezone

    base_query = VisitorLog.objects.all()

    if date_from:
        try:
            from_date = timezone.datetime.strptime(date_from, '%Y-%m-%d')
            from_date = timezone.make_aware(from_date)
            base_query = base_query.filter(created_at__gte=from_date)
        except ValueError:
            pass

    if date_to:
        try:
            to_date = timezone.datetime.strptime(date_to, '%Y-%m-%d')
            to_date = timezone.make_aware(to_date) + timedelta(days=1)
            base_query = base_query.filter(created_at__lt=to_date)
        except ValueError:
            pass

    # 使用数据库的聚合函数一次性获取统计
    stats = base_query.aggregate(
        total_visits=Count('id'),
        unique_ips=Count('ip_address', distinct=True),
        authenticated_visits=Count('id', filter=Q(user__isnull=False))
    )

    return stats


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
