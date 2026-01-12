"""
author: fishzjp
特别说明：本模块由fishzjp开发。后续由于代码重构，没有显示fishzjp名称。特此说明
gitee：https://gitee.com/jinpeng_zhang
"""
import pytz
from datetime import timedelta
from django.utils import timezone
from test_manager.model.models import Project, TestCase, TestSuite, TestRun, TestReport


def generate_time_series_data(mode, tz):
    now = timezone.now().astimezone(tz)

    if mode == 'daily':
        count = 7
        start_date = now - timedelta(days=count - 1)
        end_date = now
        period = 'day'

    elif mode == 'monthly':
        start_date = now.replace(month=1, day=1)
        end_date = now.replace(month=12, day=31)
        count = 12
        period = 'month'

    elif mode == 'yearly':
        current_year = now.year
        start_date = now.replace(year=current_year - 4, month=1, day=1)
        end_date = now.replace(month=12, day=31)
        count = 5
        period = 'year'

    else:
        raise ValueError("Invalid mode")

    labels = generate_date_labels(start_date, period, count)
    data = {
        'projects': get_model_timeseries(Project, start_date, count, period, tz),
        'test_cases': get_model_timeseries(TestCase, start_date, count, period, tz),
        'test_suites': get_model_timeseries(TestSuite, start_date, count, period, tz),
        'test_runs': get_model_timeseries(TestRun, start_date, count, period, tz),
        'test_reports': get_model_timeseries(TestReport, start_date, count, period, tz),
    }
    return {'labels': labels, 'datasets': data}


def generate_date_labels(start_date, period, count):
    labels = []
    current = start_date

    if period == 'day':
        for _ in range(count):
            labels.append(current.strftime('%b %d').lstrip('0').replace(' 0', ' '))
            current += timedelta(days=1)

    elif period == 'month':
        for i in range(count):
            labels.append(f'{i + 1}月')

    elif period == 'year':
        for i in range(count):
            labels.append(str(start_date.year + i))

    return labels


def get_model_timeseries(model, start_date, count, period, tz):
    now = timezone.now().astimezone(tz)
    end_date = now

    utc_start = start_date.astimezone(pytz.utc)
    utc_end = end_date.astimezone(pytz.utc)

    results = (
        model.objects
        .filter(created_at__range=(utc_start, utc_end))
        .values_list('created_at', flat=True)
    )

    counts = [0] * count

    for dt in results:
        local_dt = dt.astimezone(tz)

        if period == 'day':
            diff = (local_dt.date() - start_date.date()).days
        elif period == 'month':
            diff = local_dt.month - 1
        elif period == 'year':
            diff = local_dt.year - start_date.year
        else:
            continue

        if 0 <= diff < count:
            counts[diff] += 1

    return counts
