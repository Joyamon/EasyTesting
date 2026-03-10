from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from test_manager.automation.executors.ui_executors import UITestExecutor
from test_manager.utils.notification import create_ui_test_run_notification
from django.core.paginator import Paginator
from django.db import models
from test_manager.model.ui_models import UITestStep, UITestResult
from test_manager.model.models import Project, TestCase, TestRun, Environment
import json
import logging
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods
from asgiref.sync import async_to_sync

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
    return render(request, 'test_manager/ui_test/ui_test_case_list.html', context)


@login_required
def ui_test_case_create(request):
    """创建 UI 测试用例"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
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
    return render(request, 'test_manager/ui_test/ui_test_case_form.html', context)


@login_required
def ui_test_case_detail(request, pk):
    """UI 测试用例详情"""
    test_case = get_object_or_404(TestCase, pk=pk)
    steps = test_case.ui_steps.all().order_by('step_number')  # 使用默认反向关系名

    context = {
        'test_case': test_case,
        'steps': steps,
    }
    return render(request, 'test_manager/ui_test/ui_test_case_detail.html', context)


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
    return render(request, 'test_manager/ui_test/ui_test_case_form.html', context)


@login_required
def ui_test_case_delete(request, pk):
    """删除 UI 测试用例"""
    test_case = get_object_or_404(TestCase, pk=pk)
    if request.method == 'POST':
        test_case.delete()
        return redirect('ui_test_case_list')

    context = {'test_case': test_case}
    return render(request, 'test_manager/ui_test/ui_test_case_confirm_delete.html', context)


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
                element_selector=data.get('locator_value'),
                selector_type=data.get('locator_type'),
                description=data.get('description', '')
            )
            return JsonResponse({
                'success': True,
                'id': step.id,
                'step_number': step.step_number
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

    context = {
        'test_case': test_case,
        'action_choices': UITestStep.ACTION_TYPES,
        'locator_choices': UITestStep.SELECTOR_TYPES,
    }
    return render(request, 'test_manager/ui_test/ui_test_step_form.html', context)


@login_required
def ui_test_step_edit(request, step_id):
    """编辑 UI 测试步骤"""
    step = get_object_or_404(UITestStep, pk=step_id)

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            step.action_type = data.get('action', step.action_type)
            step.element_selector = data.get('locator_value', step.element_selector)
            step.selector_type = data.get('locator_type', step.selector_type)
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
    return render(request, 'test_manager/ui_test/ui_test_step_form.html', context)


@login_required
def ui_test_step_delete(request, step_id):
    """删除 UI 测试步骤"""
    step = get_object_or_404(UITestStep, pk=step_id)
    if request.method == 'POST':
        test_case = step.test_case
        step_number = step.step_number
        step.delete()
        
        # 删除后重新编号后续步骤
        subsequent_steps = UITestStep.objects.filter(
            test_case=test_case,
            step_number__gt=step_number
        ).order_by('step_number')
        
        for i, s in enumerate(subsequent_steps, start=step_number):
            s.step_number = i
            s.save()
        
        return JsonResponse({'success': True})

    return JsonResponse({'error': '不支持此请求方法'}, status=405)


@login_required
def ui_test_case_reorder_steps(request, pk):
    """重新排序 UI 测试步骤
    
    使用临时步骤号避免 UNIQUE 约束冲突。
    流程：
    1. 使用负数作为临时步骤号
    2. 最后更新为最终的步骤号
    """
    test_case = get_object_or_404(TestCase, pk=pk)
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            steps = data.get('steps', [])
            
            if not steps:
                return JsonResponse({
                    'success': False,
                    'error': '步骤列表不能为空'
                }, status=400)
            
            logger.info(f"Reordering {len(steps)} steps for test case {pk}")
            
            # 第一步：使用临时步骤号（负数）以避免 UNIQUE 约束冲突
            step_updates = {}
            for idx, step_data in enumerate(steps, start=1):
                step_id = step_data.get('id')
                step_number = step_data.get('step_number')
                step_updates[step_id] = step_number
                
                try:
                    step = UITestStep.objects.get(id=step_id, test_case=test_case)
                    # 使用临时步骤号（负数）
                    step.step_number = -(idx)
                    step.save()
                except UITestStep.DoesNotExist:
                    logger.warning(f"UITestStep {step_id} not found for test case {pk}")
                    return JsonResponse({
                        'success': False,
                        'error': f'步骤 {step_id} 不存在'
                    }, status=404)
            
            # 第二步：使用最终的步骤号（正数）
            for step_id, final_step_number in step_updates.items():
                try:
                    step = UITestStep.objects.get(id=step_id, test_case=test_case)
                    step.step_number = final_step_number
                    step.save()
                except UITestStep.DoesNotExist:
                    logger.warning(f"UITestStep {step_id} not found during final update")
            
            logger.info(f"Test case {pk} steps reordered successfully")
            return JsonResponse({
                'success': True,
                'message': '步骤顺序更新成功'
            })
            
        except json.JSONDecodeError:
            logger.error("Invalid JSON in request body")
            return JsonResponse({
                'success': False,
                'error': '无效的 JSON 格式'
            }, status=400)
        except Exception as e:
            logger.exception(f"Error reordering steps for test case {pk}: {e}")
            return JsonResponse({
                'success': False,
                'error': f'更新步骤顺序失败: {str(e)}'
            }, status=500)
    
    return JsonResponse({
        'error': '不支持此请求方法'
    }, status=405)


@require_http_methods(["GET", "POST"])
@ensure_csrf_cookie
@login_required
def ui_test_run(request, pk):
    """执行 UI 测试用例"""
    from django.utils import timezone
    test_case = get_object_or_404(TestCase, pk=pk)

    if request.method == 'POST':
        try:
            data = json.loads(request.body) if request.body else {}
            headless = data.get('headless', False)
            slow_mo = data.get('slow_mo', 0)
            environment_id = data.get('environment')

            environment = None
            if environment_id:
                environment = get_object_or_404(Environment, id=environment_id)

            # 创建测试运行记录
            test_run = TestRun.objects.create(
                name=test_case.name,
                project=test_case.project,
                environment=environment,
                start_time=timezone.now(),
                # test_suite="",
                created_by=request.user,
                status='running'
            )

            # 异步执行测试（使用 async_to_sync 避免事件循环冲突）
            executor = UITestExecutor(
                test_case=test_case,
                environment=environment,
                headless=headless,
                slow_mo=slow_mo
            )

            # 使用 async_to_sync 包装异步方法
            result = async_to_sync(executor.execute)()
            # 增加执行次数
            test_case.run_count += 1
            test_case.save()
            # 创建测试结果对象
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
                # 如果模型没有 browser_type 字段，请移除下面这行
                # browser_type=getattr(test_case, 'browser_type', 'chromium')
                created_by=request.user
            )

            # 保存性能指标
            page_metrics = result.get('page_metrics', {})
            if page_metrics:
                test_result.page_load_time = page_metrics.get('page_load_time')
                test_result.first_contentful_paint = page_metrics.get('first_contentful_paint')
                test_result.largest_contentful_paint = page_metrics.get('largest_contentful_paint')
                test_result.save()

            # 更新测试运行状态
            test_run.status = result.get('status', 'error')
            test_run.save()

            # 发送通知（确保函数存在）
            try:
                create_ui_test_run_notification(
                    user=request.user,
                    test_run=test_run,
                    ui_result=test_result
                )
            except Exception as e:
                logger.warning(f"发送通知失败: {e}")

            # 计算成功率
            steps_executed = result.get('steps_executed', 0)
            success_rate = round((result.get('steps_passed', 0) / steps_executed) * 100, 2) if steps_executed else 0

            return JsonResponse({
                'success': True,
                'test_run_id': test_run.id,
                'result': {
                    'status': result.get('status'),
                    'steps_executed': steps_executed,
                    'steps_passed': result.get('steps_passed', 0),
                    'steps_failed': result.get('steps_failed', 0),
                    'duration': round(result.get('duration', 0), 2),
                    'success_rate': success_rate,
                    'error_message': result.get('error_message', ''),
                    'screenshots': result.get('screenshots', []),
                }
            })

        except TestCase.DoesNotExist:
            return JsonResponse({'success': False, 'error': '测试用例不存在'}, status=404)
        except Exception as e:
            logger.exception("Unexpected error")
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    # GET 请求：渲染页面
    environments = Environment.objects.filter(project=test_case.project)
    ui_steps = test_case.ui_steps.all().order_by('step_number')
    context = {
        'test_case': test_case,
        'environments': environments,
        'steps': ui_steps,  # 保持与模板一致的变量名
    }

    return render(request, 'test_manager/ui_test/ui_test_run_list.html', context)


@login_required
def ui_test_run_detail(request, run_id):
    """UI 测试运行详情
    
    处理截图数据，确保可以正确显示在模板中。
    截图可能是绝对路径或相对路径，需要分别处理。
    """
    test_run = get_object_or_404(UITestResult, pk=run_id)
    steps = TestCase.objects.filter(id=test_run.test_case_id).first().ui_steps.all().order_by('step_number')
    
    # 处理截图数据
    screenshots = []
    if test_run.screenshots:
        if isinstance(test_run.screenshots, list):
            screenshots = test_run.screenshots
        elif isinstance(test_run.screenshots, str):
            # 如果是字符串，尝试解析为 JSON
            try:
                screenshots = json.loads(test_run.screenshots)
                if not isinstance(screenshots, list):
                    screenshots = [screenshots]
            except (json.JSONDecodeError, TypeError):
                screenshots = [test_run.screenshots] if test_run.screenshots else []
    
    # 处理截图路径，确保模板能正确访问
    processed_screenshots = []
    for screenshot in screenshots:
        if screenshot:
            # 移除开头的 /media/ 或 media/，统一处理
            if isinstance(screenshot, str):
                screenshot = screenshot.lstrip('/')
                if screenshot.startswith('media/'):
                    screenshot = screenshot[6:]  # 移除 'media/' 前缀
                processed_screenshots.append(screenshot)
    
    context = {
        'test_run': test_run,
        'steps': steps,
        'screenshots': processed_screenshots,
        'screenshot_count': len(processed_screenshots),
    }
    return render(request, 'test_manager/ui_test/ui_test_run_detail.html', context)


@login_required
def ui_test_run_delete(request, run_id):
    """删除 UI 测试运行"""
    test_run = get_object_or_404(UITestResult, pk=run_id)
    test_run.delete()
    return redirect('ui_test_run_list')


@login_required
def ui_test_run_list(request):
    """UI 测试运行列表"""
    queryset = UITestResult.objects.all().order_by('-created_at')
    test_case_id = request.GET.get('test_case')
    status = request.GET.get('status')

    if test_case_id:
        queryset = queryset.filter(test_case_id=test_case_id)

    if status:
        queryset = queryset.filter(status=status)

    paginator = Paginator(queryset, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'test_runs': page_obj,
    }
    return render(request, 'test_manager/ui_test/ui_test_run_list.html', context)
