import traceback

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.views.decorators.http import require_POST
from django.contrib import messages
from test_manager.async_executor import logger
from test_manager.forms import ScheduledTaskForm
from test_manager.model.models import TestSuite
from test_manager.model.schedule import ScheduledTask, TaskExecutionLog
from test_manager.scheduler import TaskScheduler


@login_required
def scheduled_task_list(request):
    """定时任务列表"""
    test_suite_id = request.GET.get('test_suite')
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')

    tasks = ScheduledTask.objects.filter(created_by=request.user)

    if test_suite_id:
        tasks = tasks.filter(test_suite_id=test_suite_id)
        test_suite = get_object_or_404(TestSuite, pk=test_suite_id)
    else:
        test_suite = None

    if search_query:
        tasks = tasks.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(test_suite__name__icontains=search_query)
        )

    if status_filter:
        tasks = tasks.filter(status=status_filter)

    # 分页
    paginator = Paginator(tasks, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'test_suite': test_suite,
        'search_query': search_query,
        'status_filter': status_filter,
        'status_choices': ScheduledTask.STATUS_CHOICES,
    }

    return render(request, 'test_manager/scheduled_task_list.html', context)


def create_celery_periodic_task(scheduled_task):
    """创建Celery周期性任务的备用方法"""
    try:
        from django_celery_beat.models import PeriodicTask, CrontabSchedule
        import json

        # 检查必要的属性
        if not hasattr(scheduled_task, 'cron_expression'):
            logger.error("任务缺少cron_expression属性")
            return None

        # 解析cron表达式
        cron_parts = scheduled_task.cron_expression.split()
        if len(cron_parts) != 5:
            logger.error(f"无效的cron表达式: {scheduled_task.cron_expression}")
            return None

        minute, hour, day_of_month, month_of_year, day_of_week = cron_parts

        # 获取或创建CrontabSchedule
        schedule, created = CrontabSchedule.objects.get_or_create(
            minute=minute,
            hour=hour,
            day_of_month=day_of_month,
            month_of_year=month_of_year,
            day_of_week=day_of_week,
            timezone='Asia/Shanghai'  # 根据实际情况调整时区
        )

        # 创建任务名称
        task_name = f"scheduled_task_{scheduled_task.id}"

        # 创建或更新PeriodicTask
        celery_task, created = PeriodicTask.objects.update_or_create(
            name=task_name,
            defaults={
                'task': 'test_manager.tasks.run_scheduled_task',  # 调整为您实际的任务路径
                'crontab': schedule,
                'args': json.dumps([scheduled_task.id]),
                'enabled': True,
                'description': f'Scheduled task: {scheduled_task.name}'
            }
        )

        # 更新任务的celery_task_id
        if hasattr(scheduled_task, 'celery_task_id'):
            scheduled_task.celery_task_id = celery_task.name
            scheduled_task.save()

        logger.info(f"Celery周期性任务创建{'成功' if created else '更新'}: {task_name}")
        return celery_task

    except Exception as e:
        logger.error(f"创建Celery周期性任务失败: {str(e)}")
        return None


@login_required
def scheduled_task_create(request):
    """创建定时任务 - 修复版本，确保立即同步到Celery Beat"""
    import logging
    logger = logging.getLogger(__name__)

    test_suite_id = request.GET.get('test_suite')

    if request.method == 'POST':
        form = ScheduledTaskForm(request.POST, test_suite_id=test_suite_id)
        if form.is_valid():
            try:
                # 保存定时任务
                task = form.save(commit=False)
                task.created_by = request.user
                task.save()

                logger.info(f"定时任务已保存到数据库: {task.name} (ID: {task.id})")

                # 立即同步到Celery Beat - 修复部分
                try:
                    # 检查任务状态 - 使用正确的属性名
                    # 先检查常见的状态属性名
                    task_enabled = True  # 默认启用

                    # 检查常见的状态字段名
                    if hasattr(task, 'enabled'):
                        task_enabled = task.enabled
                    elif hasattr(task, 'is_active'):
                        task_enabled = task.is_active
                    elif hasattr(task, 'status'):
                        # 如果status字段存在，可能需要根据具体值判断
                        task_enabled = getattr(task, 'status', 'active') == 'active'
                    else:
                        logger.info(f"未找到明确的状态字段，默认启用任务")

                    if not task_enabled:
                        logger.warning(f"定时任务被禁用: {task.name}")
                        messages.warning(
                            request,
                            f'定时任务 "{task.name}" 创建成功，但处于禁用状态，不会执行。'
                        )
                        return redirect('scheduled_task_detail', pk=task.pk)

                    # 重新计算下次执行时间
                    if hasattr(task, 'update_next_run_time'):
                        task.update_next_run_time()
                        logger.info(f"下次执行时间已计算: {getattr(task, 'next_run_time', 'N/A')}")
                    else:
                        logger.warning("任务对象没有update_next_run_time方法")

                    # 保存任务以确保时间更新
                    task.save()

                    # 创建或更新Celery Beat任务 - 添加重试机制
                    max_retries = 3
                    celery_task = None

                    for attempt in range(max_retries):
                        try:
                            # 确保TaskScheduler方法存在
                            if hasattr(TaskScheduler, 'create_or_update_celery_task'):
                                celery_task = TaskScheduler.create_or_update_celery_task(task)
                            else:
                                # 如果没有TaskScheduler，直接创建Celery任务
                                celery_task = create_celery_periodic_task(task)

                            if celery_task:
                                logger.info(
                                    f"Celery Beat任务创建成功 (尝试 {attempt + 1}/{max_retries}): {getattr(task, 'celery_task_id', 'N/A')}")
                                break
                            else:
                                logger.warning(f"Celery Beat任务创建返回None (尝试 {attempt + 1}/{max_retries})")
                        except Exception as e:
                            logger.warning(f"Celery Beat任务创建失败 (尝试 {attempt + 1}/{max_retries}): {str(e)}")
                            if attempt == max_retries - 1:
                                raise e
                            import time
                            time.sleep(1)  # 等待1秒后重试

                    if celery_task:
                        # 强制更新调度器
                        try:
                            # 尝试不同的更新方法
                            from django_celery_beat.models import PeriodicTask, PeriodicTasks

                            if hasattr(PeriodicTasks, 'update_changed'):
                                PeriodicTasks.update_changed()
                                logger.info("使用PeriodicTasks.update_changed()更新调度器")
                            elif hasattr(PeriodicTask, 'update_changed'):
                                PeriodicTask.update_changed()
                                logger.info("使用PeriodicTask.update_changed()更新调度器")
                            else:
                                logger.warning("未找到可用的调度器更新方法")
                        except Exception as e:
                            logger.warning(f"调度器更新失败: {str(e)}")

                        # 验证同步结果
                        try:
                            from django_celery_beat.models import PeriodicTask
                            celery_task_id = getattr(task, 'celery_task_id', None)

                            if celery_task_id:
                                celery_task_exists = PeriodicTask.objects.filter(name=celery_task_id).first()
                            else:
                                # 如果没有celery_task_id，尝试通过任务名称查找
                                task_name = f"scheduled_task_{task.id}"
                                celery_task_exists = PeriodicTask.objects.filter(name=task_name).first()

                            if celery_task_exists:
                                logger.info(f"验证成功: Celery Beat任务已存在于数据库")
                                logger.info(
                                    f"Celery任务详情: ID={celery_task_exists.id}, 名称={celery_task_exists.name}, 启用={celery_task_exists.enabled}")

                                if celery_task_exists.enabled:
                                    next_run = getattr(task, 'next_run_time', '未知')
                                    messages.success(
                                        request,
                                        f'定时任务 "{task.name}" 创建成功，已同步到调度器。下次执行时间: {next_run}'
                                    )
                                else:
                                    messages.warning(
                                        request,
                                        f'定时任务 "{task.name}" 创建成功，但Celery任务被禁用，不会执行。'
                                    )
                            else:
                                logger.error(f"验证失败: Celery Beat任务不存在于数据库")
                                # 尝试列出所有任务进行调试
                                all_tasks = PeriodicTask.objects.all().values_list('name', flat=True)
                                logger.info(f"当前所有Celery任务: {list(all_tasks)}")
                                messages.error(
                                    request,
                                    f'调度器同步验证失败，任务可能无法按时执行。请检查Celery Beat服务状态。'
                                )
                        except Exception as e:
                            logger.error(f"验证Celery任务时出错: {str(e)}")
                    else:
                        logger.error(f"Celery Beat任务创建完全失败")
                        messages.error(
                            request,
                            f'定时任务 "{task.name}" 创建成功，但同步到调度器失败。请检查Celery Beat服务状态。'
                        )

                except Exception as sync_error:
                    logger.error(f"同步到Celery Beat失败: {str(sync_error)}")
                    logger.error(f"同步错误详情: {traceback.format_exc()}")
                    messages.error(
                        request,
                        f'定时任务创建成功，但同步到调度器失败: {str(sync_error)}。请检查Celery Beat配置。'
                    )

                return redirect('scheduled_task_detail', pk=task.pk)

            except Exception as e:
                logger.error(f"创建定时任务失败: {str(e)}")
                logger.error(f"创建错误详情: {traceback.format_exc()}")
                messages.error(request, f'创建定时任务失败: {str(e)}')

    else:
        initial = {}
        if test_suite_id:
            initial['test_suite'] = test_suite_id
        form = ScheduledTaskForm(initial=initial, test_suite_id=test_suite_id)

    return render(request, 'test_manager/scheduled_task_form.html', {
        'form': form,
        'title': '创建定时任务'
    })


@login_required
def scheduled_task_detail(request, pk):
    """定时任务详情"""
    task = get_object_or_404(ScheduledTask, pk=pk, created_by=request.user)

    # 获取执行日志
    logs = TaskExecutionLog.objects.filter(scheduled_task=task).order_by('-start_time')

    # 分页
    paginator = Paginator(logs, 10)
    page_number = request.GET.get('page')
    logs_page = paginator.get_page(page_number)

    context = {
        'task': task,
        'logs_page': logs_page,
    }

    return render(request, 'test_manager/scheduled_task_detail.html', context)


@login_required
def scheduled_task_edit(request, pk):
    """编辑定时任务 - 优化版本，确保立即同步到Celery Beat"""
    import logging
    logger = logging.getLogger(__name__)

    task = get_object_or_404(ScheduledTask, pk=pk, created_by=request.user)

    if request.method == 'POST':
        form = ScheduledTaskForm(request.POST, instance=task, test_suite_id=task.test_suite.id)
        if form.is_valid():
            try:
                # 保存原始的celery_task_id，用于删除旧任务
                old_celery_task_id = task.celery_task_id

                # 保存定时任务
                task = form.save()
                logger.info(f"定时任务已更新到数据库: {task.name} (ID: {task.id})")

                # 立即同步到Celery Beat
                try:
                    # 如果有旧的Celery任务，先删除
                    if old_celery_task_id:
                        try:
                            from django_celery_beat.models import PeriodicTask
                            old_task = PeriodicTask.objects.get(name=old_celery_task_id)
                            old_task.delete()
                            logger.info(f"已删除旧的Celery Beat任务: {old_celery_task_id}")
                        except PeriodicTask.DoesNotExist:
                            logger.warning(f"旧的Celery Beat任务不存在: {old_celery_task_id}")

                    # 计算下次执行时间
                    task.update_next_run_time()
                    logger.info(f"下次执行时间已更新: {task.next_run_time}")

                    # 创建新的Celery Beat任务
                    celery_task = TaskScheduler.create_or_update_celery_task(task)

                    if celery_task:
                        logger.info(f"Celery Beat任务更新成功: {task.celery_task_id}")
                        messages.success(
                            request,
                            f'定时任务 "{task.name}" 更新成功，已同步到调度器。下次执行时间: {task.next_run_time}'
                        )
                    else:
                        logger.warning(f"Celery Beat任务更新失败: {task.name}")
                        messages.warning(
                            request,
                            f'定时任务 "{task.name}" 更新成功，但同步到调度器失败。请检查Celery Beat服务状态。'
                        )

                    # 验证同步结果
                    from django_celery_beat.models import PeriodicTask
                    if task.celery_task_id and PeriodicTask.objects.filter(name=task.celery_task_id).exists():
                        logger.info(f"验证成功: Celery Beat任务已存在于数据库")
                        messages.info(request, f'调度器同步验证成功')
                    else:
                        logger.error(f"验证失败: Celery Beat任务不存在于数据库")
                        messages.error(request, f'调度器同步验证失败，任务可能无法按时执行')

                except Exception as sync_error:
                    logger.error(f"同步到Celery Beat失败: {str(sync_error)}")
                    logger.error(f"同步错误详情: {traceback.format_exc()}")
                    messages.error(
                        request,
                        f'定时任务更新成功，但同步到调度器失败: {str(sync_error)}'
                    )

                return redirect('scheduled_task_detail', pk=task.pk)

            except Exception as e:
                logger.error(f"更新定时任务失败: {str(e)}")
                logger.error(f"更新错误详情: {traceback.format_exc()}")
                messages.error(request, f'更新定时任务失败: {str(e)}')

    else:
        form = ScheduledTaskForm(instance=task, test_suite_id=task.test_suite.id)

    return render(request, 'test_manager/scheduled_task_form.html', {
        'form': form,
        'task': task,
        'title': f'编辑定时任务: {task.name}'
    })


@login_required
def scheduled_task_delete(request, pk):
    """删除定时任务 - 优化版本，确保同步删除Celery Beat任务"""
    import logging
    logger = logging.getLogger(__name__)

    task = get_object_or_404(ScheduledTask, pk=pk, created_by=request.user)

    if request.method == 'POST':
        task_name = task.name
        celery_task_id = task.celery_task_id

        try:
            logger.info(f"开始删除定时任务: {task_name} (ID: {task.id})")

            # 先删除Celery Beat任务
            if celery_task_id:
                try:
                    from django_celery_beat.models import PeriodicTask
                    celery_task = PeriodicTask.objects.get(name=celery_task_id)
                    celery_task.delete()
                    logger.info(f"成功删除Celery Beat任务: {celery_task_id}")
                    messages.info(request, f'已删除调度器中的任务: {celery_task_id}')
                except PeriodicTask.DoesNotExist:
                    logger.warning(f"Celery Beat任务不存在: {celery_task_id}")
                    messages.warning(request, f'调度器中的任务不存在: {celery_task_id}')
                except Exception as celery_error:
                    logger.error(f"删除Celery Beat任务失败: {str(celery_error)}")
                    logger.error(f"Celery删除错误详情: {traceback.format_exc()}")
                    messages.error(request, f'删除调度器任务失败: {str(celery_error)}')
            else:
                logger.info(f"任务没有关联的Celery Beat任务: {task_name}")

            # 删除数据库中的定时任务
            task.delete()
            logger.info(f"成功删除数据库中的定时任务: {task_name}")

            # 验证删除结果
            try:
                if celery_task_id:
                    from django_celery_beat.models import PeriodicTask
                    if not PeriodicTask.objects.filter(name=celery_task_id).exists():
                        logger.info(f"验证成功: Celery Beat任务已从数据库中删除")
                        messages.success(request, f'定时任务 "{task_name}" 已完全删除（包括调度器任务）')
                    else:
                        logger.error(f"验证失败: Celery Beat任务仍存在于数据库中")
                        messages.warning(request, f'定时任务 "{task_name}" 已删除，但调度器任务可能仍然存在')
                else:
                    messages.success(request, f'定时任务 "{task_name}" 已删除')
            except Exception as verify_error:
                logger.error(f"验证删除结果失败: {str(verify_error)}")
                messages.success(request, f'定时任务 "{task_name}" 已删除')

            return redirect('scheduled_task_list')

        except Exception as e:
            logger.error(f"删除定时任务失败: {str(e)}")
            logger.error(f"删除错误详情: {traceback.format_exc()}")
            messages.error(request, f'删除定时任务失败: {str(e)}')
            return redirect('scheduled_task_detail', pk=pk)

    return render(request, 'test_manager/scheduled_task_confirm_delete.html', {'task': task})


@login_required
@require_POST
def scheduled_task_toggle_status(request, pk):
    """切换定时任务状态 - 优化版本，确保立即同步到Celery Beat"""
    import logging
    logger = logging.getLogger(__name__)

    task = get_object_or_404(ScheduledTask, pk=pk, created_by=request.user)
    old_status = task.status

    try:
        if task.status == 'active':
            task.status = 'paused'
            message = f'定时任务 "{task.name}" 已暂停'
        else:
            task.status = 'active'
            task.update_next_run_time()
            message = f'定时任务 "{task.name}" 已激活'

        task.save()
        logger.info(f"任务状态已更新: {task.name} - {old_status} -> {task.status}")

        # 立即同步到Celery Beat
        try:
            if task.status == 'active':
                # 激活任务 - 创建Celery Beat任务
                celery_task = TaskScheduler.create_or_update_celery_task(task)
                if celery_task:
                    logger.info(f"Celery Beat任务已激活: {task.celery_task_id}")
                    message += f"，下次执行时间: {task.next_run_time}"
                else:
                    logger.warning(f"Celery Beat任务激活失败: {task.name}")
                    message += "，但调度器同步失败"
            else:
                # 暂停任务 - 删除Celery Beat任务
                TaskScheduler.delete_celery_task(task)
                logger.info(f"Celery Beat任务已暂停: {task.name}")

        except Exception as sync_error:
            logger.error(f"状态切换同步失败: {str(sync_error)}")
            message += f"，但调度器同步失败: {str(sync_error)}"

        messages.success(request, message)

        return JsonResponse({
            'success': True,
            'status': task.status,
            'message': message,
            'next_run_time': task.next_run_time.strftime('%Y-%m-%d %H:%M:%S') if task.next_run_time else None
        })

    except Exception as e:
        logger.error(f"切换任务状态失败: {str(e)}")
        logger.error(f"状态切换错误详情: {traceback.format_exc()}")

        return JsonResponse({
            'success': False,
            'message': f'切换任务状态失败: {str(e)}',
            'error': str(e)
        })


# @login_required
@require_POST
def scheduled_task_run_now(request, pk):
    """立即执行定时任务"""
    try:
        task = get_object_or_404(ScheduledTask, pk=pk)
        print(f'[DEBUG] scheduled_task_run_now - 找到任务: {task.name} (ID: {task.id})')

        # 检查任务状态
        if not task.is_enabled:
            messages.error(request, f'定时任务 "{task.name}" 已禁用，无法执行')
            return JsonResponse({
                'success': False,
                'message': f'定时任务 "{task.name}" 已禁用，无法执行'
            })

        # 检查Celery是否可用
        try:
            from celery import current_app
            i = current_app.control.inspect()
            active_workers = i.active()

            if not active_workers:
                print('[ERROR] 没有活动的Celery worker')
                messages.error(request, 'Celery服务未运行，无法执行定时任务')
                return JsonResponse({
                    'success': False,
                    'message': 'Celery服务未运行，无法执行定时任务'
                })

            print(f'[DEBUG] 找到活动的Celery worker: {list(active_workers.keys())}')

        except Exception as celery_check_error:
            print(f'[ERROR] Celery状态检查失败: {str(celery_check_error)}')
            # 继续执行，可能是检查方法的问题

        # 尝试异步执行任务
        try:
            from ..tasks import execute_scheduled_test_suite
            print(f'[DEBUG] 准备异步执行任务: {task.id}')
            result = execute_scheduled_test_suite.delay(task.id)
            print(f'[DEBUG] 任务已提交到Celery队列，task_id: {result.id}')

            messages.success(request, f'定时任务 "{task.name}" 已开始执行')

            return JsonResponse({
                'success': True,
                'message': f'定时任务 "{task.name}" 已开始执行',
                'task_id': result.id
            })

        except Exception as celery_error:
            print(f'[ERROR] Celery任务提交失败: {str(celery_error)}')
            print(f'[ERROR] 错误详情: {traceback.format_exc()}')

            # 尝试直接执行任务（同步方式）
            try:
                print(f'[DEBUG] 尝试同步执行任务: {task.id}')
                from ..tasks import execute_scheduled_test_suite

                # 在后台线程中执行，避免阻塞请求
                import threading

                def run_task_sync():
                    try:
                        result = execute_scheduled_test_suite(task.id)
                        print(f'[DEBUG] 同步任务执行完成: {result}')
                    except Exception as sync_error:
                        print(f'[ERROR] 同步任务执行失败: {str(sync_error)}')
                        print(f'[ERROR] 同步任务错误详情: {traceback.format_exc()}')

                thread = threading.Thread(target=run_task_sync)
                thread.daemon = True
                thread.start()

                messages.success(request, f'定时任务 "{task.name}" 已开始执行（同步模式）')

                return JsonResponse({
                    'success': True,
                    'message': f'定时任务 "{task.name}" 已开始执行（同步模式）',
                    'task_id': 'sync_execution'
                })

            except Exception as sync_error:
                print(f'[ERROR] 同步执行也失败: {str(sync_error)}')
                print(f'[ERROR] 同步执行错误详情: {traceback.format_exc()}')

                messages.error(request, f'定时任务 "{task.name}" 执行失败: {str(sync_error)}')

                return JsonResponse({
                    'success': False,
                    'message': f'定时任务 "{task.name}" 执行失败: {str(sync_error)}',
                    'error': str(sync_error)
                })

    except Exception as e:
        print(f'[ERROR] scheduled_task_run_now 视图异常: {str(e)}')
        print(f'[ERROR] 视图异常详情: {traceback.format_exc()}')

        messages.error(request, f'执行定时任务时发生错误: {str(e)}')

        return JsonResponse({
            'success': False,
            'message': f'执行定时任务时发生错误: {str(e)}',
            'error': str(e)
        })


# @login_required
def task_execution_log_detail(request, pk):
    """任务执行日志详情"""
    log = get_object_or_404(TaskExecutionLog, pk=pk)
    print(f'[DEBUG] 找到任务执行日志: ', log)

    context = {
        'log': log,
    }

    return render(request, 'test_manager/task_execution_log_detail.html', context)
