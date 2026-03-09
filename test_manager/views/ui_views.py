from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db import models

from test_manager.model.ui_models import UITestStep, UITestResult
from test_manager.model.models import Project, TestCase, TestRun, Environment
from test_manager.automation.executors.ui_executor import UITestExecutor
from test_manager.utils.notification import create_ui_test_run_notification

import json
import asyncio
import time
import logging

logger = logging.getLogger(__name__)




@login_required
def ui_test_case_list(request):
    """UI 测试用例列表"""
    queryset = TestCase.objects.all().order_by('-created_at').filter(test_type='ui')
    project_id = request.GET.get('project')
    search_query = request.GET.get('search', '')

    if project_id:
        queryset = queryset.filter(project_id=project_id)

    if search_query:
        queryset = queryset.filter(name__icontains=search_query)

    paginator = Paginator(queryset, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    projects = Project.objects.all()
    current_project = None
    if project_id:
        current_project = get_object_or_404(Project, id=project_id)

    context = {
        'page_obj': page_obj,
        'test_cases': page_obj,
        'projects': projects,
        'current_project': current_project,
        'search_query': search_query,
    }
    return render(request, 'test_manager/ui_test_case_list.html', context)


@login_required
def ui_test_case_create(request):
    """创建 UI 测试用例"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            print( data)
            test_case = TestCase.objects.create(
                name=data.get('name'),
                project_id=data.get('project_id'),
                description=data.get('description', ''),
                target_url=data.get('url', ''),
                browser_type=data.get('browser_type', 'chromium'),
                created_by=request.user,
                test_type='ui',
            )

            return JsonResponse({'success': True, 'id': test_case.id})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

    projects = Project.objects.all()
    context = {'projects': projects}
    return render(request, 'test_manager/ui_test_case_form.html', context)


@login_required
def ui_test_case_detail(request, pk):
    """UI 测试用例详情"""
    test_case = get_object_or_404(TestCase, pk=pk)
    steps = test_case.ui_steps.all().order_by('step_number')  # 使用默认反向关系名

    context = {
        'test_case': test_case,
        'steps': steps,
    }
    return render(request, 'test_manager/ui_test_case_detail.html', context)


@login_required
def ui_test_case_edit(request, pk):
    """编辑 UI 测试用例"""
    test_case = get_object_or_404(TestCase, pk=pk)

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            test_case.name = data.get('name', test_case.name)
            test_case.description = data.get('description', test_case.description)
            test_case.target_url = data.get('url', test_case.target_url)
            test_case.browser_type = data.get('browser_type', test_case.browser_type)
            test_case.save()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

    projects = Project.objects.all()
    context = {
        'test_case': test_case,
        'projects': projects,
    }
    return render(request, 'test_manager/ui_test_case_form.html', context)


@login_required
def ui_test_case_delete(request, pk):
    """删除 UI 测试用例"""
    test_case = get_object_or_404(TestCase, pk=pk)
    if request.method == 'POST':
        test_case.delete()
        return redirect('ui_test_case_list')

    context = {'test_case': test_case}
    return render(request, 'test_manager/ui_test_case_confirm_delete.html', context)


@login_required
def ui_test_step_add(request, test_case_id):
    """添加 UI 测试步骤"""
    test_case = get_object_or_404(TestCase, pk=test_case_id)

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            # 获取当前最大的 step_number
            max_order_dict = UITestStep.objects.filter(test_case=test_case).aggregate(
                max_step=models.Max('step_number')
            )
            max_step = max_order_dict.get('max_step')
            next_step_number = (max_step + 1) if max_step is not None else 1

            step = UITestStep.objects.create(
                test_case=test_case,
                step_number=next_step_number,
                action_type=data.get('action'),
                action_value=data.get('value', ''),
                element_selector=data.get('locator_type'),
                selector_type=data.get('locator_value'),
                description=data.get('description', '')
            )
            return JsonResponse({
                'success': True,
                'id': step.id,
                'step_number': step.step_number   # 注意这里也改成了 step_number
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

    context = {
        'test_case': test_case,
        'action_choices': UITestStep.ACTION_TYPES,
        'locator_choices': UITestStep.SELECTOR_TYPES,
    }
    return render(request, 'test_manager/ui_test_step_form.html', context)


@login_required
def ui_test_step_edit(request, step_id):
    """编辑 UI 测试步骤"""
    from django.db import models
    step = get_object_or_404(UITestStep, pk=step_id)

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            step.action_type = data.get('action', step.action_type)
            step.element_selector = data.get('locator_type', step.element_selector)
            step.selector_type = data.get('locator_value', step.selector_type)
            step.action_value = data.get('value', step.action_value)
            step.description = data.get('description', step.description)
            step.save()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

    context = {
        'step': step,
        'action_choices': UITestStep.ACTION_TYPES,
        'locator_choices': UITestStep.SELECTOR_TYPES,
    }
    return render(request, 'test_manager/ui_test_step_form.html', context)


@login_required
def ui_test_step_delete(request, step_id):
    """删除 UI 测试步骤"""
    step = get_object_or_404(UITestStep, pk=step_id)
    test_case_id = step.test_case.id

    if request.method == 'POST':
        step.delete()
        return JsonResponse({'success': True})

    return JsonResponse({'error': 'Method not allowed'}, status=405)


@login_required
def ui_test_run(request, test_case_id):
    """执行 UI 测试用例
    
    支持 POST 请求执行测试，返回 JSON 结果。
    支持 GET 请求返回 HTML 执行页面。
    
    基于 UITestExecutor 的异步执行框架，支持：
    - 多浏览器执行（Chromium, Firefox, WebKit）
    - 自定义超时和延迟
    - 自动截图和性能监控
    - 详细的步骤级别日志
    """
    test_case = get_object_or_404(TestCase, pk=test_case_id)

    if request.method == 'POST':
        try:
            # 解析请求参数
            data = json.loads(request.body) if request.body else {}
            headless = data.get('headless', True)
            slow_mo = data.get('slow_mo', 0)
            environment_id = data.get('environment_id')
            
            logger.info(
                f"UI test request: test_case_id={test_case_id}, headless={headless}, "
                f"slow_mo={slow_mo}ms, environment_id={environment_id}"
            )
            
            # 获取环境配置（如果指定）
            environment = None
            if environment_id:
                try:
                    environment = Environment.objects.get(id=environment_id)
                except Environment.DoesNotExist:
                    logger.warning(f"Environment {environment_id} not found")
            
            # 创建测试运行记录
            test_run = TestRun.objects.create(
                test_case=test_case,
                created_by=request.user,
                status='running'
            )
            
            logger.info(
                f"Created test run {test_run.id} for test case '{test_case.name}'"
            )
            
            # 初始化执行器
            executor = UITestExecutor(
                test_case=test_case,
                environment=environment,
                headless=headless,
                slow_mo=slow_mo
            )
            
            logger.info(f"UITestExecutor initialized with test_case={test_case}, type={type(test_case)}")
            
            # 执行 UI 测试（同步包装异步执行）
            result = None
            try:
                logger.info("Starting async test execution...")
                result = asyncio.run(executor.execute())
                logger.info(f"Test execution completed: {result.get('status')}")
            except Exception as e:
                logger.exception(f"Test execution error: {e}")
                # 如果执行失败，构造错误结果
                duration = time.time() - (executor.start_time or time.time())
                result = {
                    'status': 'error',
                    'error_message': str(e),
                    'duration': duration,
                    'steps_executed': len(executor.step_results) if hasattr(executor, 'step_results') else 0,
                    'steps_passed': sum(1 for r in (executor.step_results or []) if r.get('status') == 'passed'),
                    'steps_failed': sum(1 for r in (executor.step_results or []) if r.get('status') == 'failed'),
                    'screenshots': executor.screenshots if hasattr(executor, 'screenshots') else [],
                    'step_details': executor.step_results if hasattr(executor, 'step_results') else [],
                    'page_metrics': executor.page_metrics if hasattr(executor, 'page_metrics') else {},
                }
            
            # 验证结果结构
            if not result:
                result = {
                    'status': 'error',
                    'error_message': 'Unknown error',
                    'duration': 0,
                    'steps_executed': 0,
                    'steps_passed': 0,
                    'steps_failed': 0,
                    'screenshots': [],
                    'step_details': [],
                    'page_metrics': {},
                }
            
            # 从执行器结果映射到 UITestResult
            logger.info(f"Creating UITestResult with status={result.get('status')}")
            test_result = UITestResult.objects.create(
                test_run=test_run,
                test_case=test_case,
                environment=environment,
                status=result.get('status', 'error'),
                duration=result.get('duration', 0),
                steps_executed=result.get('steps_executed', 0),
                steps_passed=result.get('steps_passed', 0),
                steps_failed=result.get('steps_failed', 0),
                error_message=result.get('error_message', ''),
                screenshots=result.get('screenshots', []),
                step_details=result.get('step_details', []),
                browser_type=getattr(test_case, 'browser_type', 'chromium'),
            )
            
            # 提取和保存性能指标
            page_metrics = result.get('page_metrics', {})
            if page_metrics:
                if 'page_load_time' in page_metrics:
                    test_result.page_load_time = page_metrics['page_load_time']
                if 'first_contentful_paint' in page_metrics:
                    test_result.first_contentful_paint = page_metrics['first_contentful_paint']
                if 'largest_contentful_paint' in page_metrics:
                    test_result.largest_contentful_paint = page_metrics['largest_contentful_paint']
                test_result.save()
            
            # 更新测试运行状态
            test_run.status = result.get('status', 'error')
            test_run.save()
            
            # 发送通知
            try:
                create_ui_test_run_notification(
                    user=request.user,
                    test_run=test_run,
                    ui_result=test_result
                )
                logger.info(f"Notification sent for test run {test_run.id}")
            except Exception as e:
                logger.warning(f"Failed to send notification: {e}")
            
            # 计算成功率
            success_rate = 0
            steps_executed = result.get('steps_executed', 0)
            if steps_executed > 0:
                success_rate = round(
                    (result.get('steps_passed', 0) / steps_executed) * 100, 
                    2
                )
            
            logger.info(
                f"Test run {test_run.id} completed: "
                f"{result.get('steps_passed', 0)}/{steps_executed} steps passed "
                f"({success_rate}%), duration: {result.get('duration', 0):.2f}s"
            )
            
            return JsonResponse({
                'success': True,
                'test_run_id': test_run.id,
                'result': {
                    'status': result.get('status', 'error'),
                    'steps_executed': result.get('steps_executed', 0),
                    'steps_passed': result.get('steps_passed', 0),
                    'steps_failed': result.get('steps_failed', 0),
                    'duration': round(result.get('duration', 0), 2),
                    'success_rate': success_rate,
                    'error_message': result.get('error_message', ''),
                    'screenshots': result.get('screenshots', []),
                }
            })
            
        except json.JSONDecodeError:
            logger.error("Invalid JSON in request body")
            return JsonResponse({
                'success': False, 
                'error': '无效的请求格式'
            }, status=400)
        except TestCase.DoesNotExist:
            logger.error(f"Test case {test_case_id} not found")
            return JsonResponse({
                'success': False, 
                'error': '测试用例不存在'
            }, status=404)
        except Exception as e:
            logger.exception(f"Unexpected error in ui_test_run: {e}")
            return JsonResponse({
                'success': False, 
                'error': f'测试执行失败: {str(e)}'
            }, status=500)

    # GET 请求：返回测试执行页面
    # 获取测试用例的可用环境
    environments = Environment.objects.filter(project=test_case.project)
    
    # 获取 UI 步骤
    ui_steps = test_case.ui_steps.all().order_by('step_number')
    
    context = {
        'test_case': test_case,
        'environments': environments,
        'ui_steps': ui_steps,
    }
    return render(request, 'test_manager/ui_test_run.html', context)


@login_required
def ui_test_run_detail(request, run_id):
    """UI 测试运行详情"""
    test_run = get_object_or_404(TestRun, pk=run_id)
    result = test_run.result

    context = {
        'test_run': test_run,
        'result': result,
    }
    return render(request, 'test_manager/ui_test_run_detail.html', context)


@login_required
def ui_test_run_list(request):
    """UI 测试运行列表"""
    queryset = TestRun.objects.all().order_by('-created_at')
    test_case_id = request.GET.get('test_case')
    status = request.GET.get('status')

    if test_case_id:
        queryset = queryset.filter(test_case_id=test_case_id)

    if status:
        queryset = queryset.filter(status=status)

    paginator = Paginator(queryset, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'test_runs': page_obj,
    }
    return render(request, 'test_manager/ui_test_run_list.html', context)
