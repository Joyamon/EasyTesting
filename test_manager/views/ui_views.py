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
from test_manager.utils.notification import create_ui_test_notification, create_ui_test_run_notification
import json
import asyncio
import logging

logger = logging.getLogger(__name__)

try:
    from test_manager.automation.executors.ui_executor import UIExecutor
except ImportError:
    UIExecutor = None




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


from test_manager.automation.executors.ui_executors import UITestExecutor

@login_required
def ui_test_run(request, test_case_id):
    """执行 UI 测试用例
    
    支持 POST 请求执行测试，返回 JSON 结果。
    支持 GET 请求返回 HTML 执行页面。
    """
    test_case = get_object_or_404(TestCase, pk=test_case_id)

    if request.method == 'POST':
        try:
            # 检查 UITestExecutor 是否可用
            if not UIExecutor:
                logger.error("UITestExecutor not available")
                return JsonResponse({
                    'success': False,
                    'error': 'UI 自动化框架未配置'
                }, status=400)
            
            # 获取测试配置参数
            data = json.loads(request.body) if request.body else {}
            headless = data.get('headless', True)
            slow_mo = data.get('slow_mo', 0)
            environment_id = data.get('environment_id')
            
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
            
            logger.info(f"Starting UI test run {test_run.id} for test case {test_case.id}")
            
            try:
                # 执行 UI 测试（同步包装异步执行）
                executor = UIExecutor(
                    test_case=test_case,
                    environment=environment,
                    headless=headless,
                    slow_mo=slow_mo
                )
                
                # 运行异步执行方法
                result = asyncio.run(executor.execute())
                
            except Exception as e:
                logger.exception(f"Test execution failed: {e}")
                result = {
                    'status': 'error',
                    'error_message': str(e),
                    'duration': 0,
                    'steps_executed': 0,
                    'steps_passed': 0,
                    'steps_failed': 0,
                    'screenshots': [],
                    'step_details': []
                }
            
            # 保存详细的测试结果
            test_result = UITestResult.objects.create(
                test_run=test_run,
                status=result.get('status', 'error'),
                steps_executed=result.get('steps_executed', 0),
                steps_passed=result.get('steps_passed', 0),
                steps_failed=result.get('steps_failed', 0),
                duration=result.get('duration', 0),
                error_message=result.get('error_message', ''),
                screenshots=json.dumps(result.get('screenshots', [])),
                step_details=json.dumps(result.get('step_details', [])),
                page_metrics=json.dumps(result.get('page_metrics', {}))
            )
            
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
            if result.get('steps_executed', 0) > 0:
                success_rate = round(
                    (result.get('steps_passed', 0) / result.get('steps_executed', 0)) * 100, 
                    2
                )
            
            logger.info(f"Test run {test_run.id} completed with status {result.get('status')}")
            
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
                }
            })
            
        except json.JSONDecodeError:
            logger.error("Invalid JSON in request body")
            return JsonResponse({
                'success': False, 
                'error': '无效的请求格式'
            }, status=400)
        except Exception as e:
            logger.exception(f"Unexpected error in ui_test_run: {e}")
            return JsonResponse({
                'success': False, 
                'error': f'测试执行失败: {str(e)}'
            }, status=500)

    # GET 请求：返回测试执行页面
    context = {'test_case': test_case}
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
