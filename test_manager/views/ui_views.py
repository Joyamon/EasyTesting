"""
UI 自动化测试视图
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db import models
from test_manager.model.ui_models import UITestCase, UITestRun, UITestStep, UITestResult
from test_manager.model.models import Project, TestCase
try:
    from test_manager.automation.executors.ui_executor import UIExecutor
except ImportError:
    UIExecutor = None
import json


@login_required
def ui_test_case_list(request):
    """UI 测试用例列表"""
    queryset = UITestCase.objects.all().order_by('-created_at')
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
            test_case = UITestCase.objects.create(
                name=data.get('name'),
                project_id=data.get('project_id'),
                description=data.get('description', ''),
                url=data.get('url', ''),
                browser_type=data.get('browser_type', 'chromium'),
                created_by=request.user
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
    test_case = get_object_or_404(UITestCase, pk=pk)
    steps = test_case.steps.all().order_by('order')
    
    context = {
        'test_case': test_case,
        'steps': steps,
    }
    return render(request, 'test_manager/ui_test_case_detail.html', context)


@login_required
def ui_test_case_edit(request, pk):
    """编辑 UI 测试用例"""
    test_case = get_object_or_404(UITestCase, pk=pk)
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            test_case.name = data.get('name', test_case.name)
            test_case.description = data.get('description', test_case.description)
            test_case.url = data.get('url', test_case.url)
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
    test_case = get_object_or_404(UITestCase, pk=pk)
    if request.method == 'POST':
        test_case.delete()
        return redirect('ui_test_case_list')
    
    context = {'test_case': test_case}
    return render(request, 'test_manager/ui_test_case_confirm_delete.html', context)


@login_required
def ui_test_step_add(request, test_case_id):
    """添加 UI 测试步骤"""
    test_case = get_object_or_404(UITestCase, pk=test_case_id)
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            # 获取下一个 order 值
            max_order = test_case.steps.aggregate(max_order=models.Max('order'))['max_order'] or 0
            
            step = UITestStep.objects.create(
                test_case=test_case,
                order=max_order + 1,
                action=data.get('action'),
                locator_type=data.get('locator_type'),
                locator_value=data.get('locator_value'),
                value=data.get('value', ''),
                description=data.get('description', '')
            )
            return JsonResponse({
                'success': True,
                'id': step.id,
                'order': step.order
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    
    context = {
        'test_case': test_case,
        'action_choices': UITestStep.ACTION_CHOICES,
        'locator_choices': UITestStep.LOCATOR_TYPE_CHOICES,
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
            step.action = data.get('action', step.action)
            step.locator_type = data.get('locator_type', step.locator_type)
            step.locator_value = data.get('locator_value', step.locator_value)
            step.value = data.get('value', step.value)
            step.description = data.get('description', step.description)
            step.save()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    
    context = {
        'step': step,
        'action_choices': UITestStep.ACTION_CHOICES,
        'locator_choices': UITestStep.LOCATOR_TYPE_CHOICES,
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
    """执行 UI 测试用例"""
    test_case = get_object_or_404(UITestCase, pk=test_case_id)
    
    if request.method == 'POST':
        try:
            # 创建 test run
            test_run = UITestRun.objects.create(
                test_case=test_case,
                created_by=request.user,
                status='running'
            )
            
            # 异步执行测试
            executor = UIExecutor()
            result = executor.execute_test_case(test_case)
            
            # 保存结果
            test_result = UITestResult.objects.create(
                test_run=test_run,
                status=result.get('status'),
                steps_executed=result.get('steps_executed', 0),
                steps_passed=result.get('steps_passed', 0),
                steps_failed=result.get('steps_failed', 0),
                duration=result.get('duration', 0),
                error_message=result.get('error_message', ''),
                screenshots=json.dumps(result.get('screenshots', []))
            )
            
            test_run.status = result.get('status')
            test_run.save()
            
            return JsonResponse({
                'success': True,
                'test_run_id': test_run.id,
                'result': {
                    'status': result.get('status'),
                    'steps_executed': result.get('steps_executed'),
                    'steps_passed': result.get('steps_passed'),
                    'steps_failed': result.get('steps_failed'),
                    'duration': result.get('duration'),
                }
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    
    context = {'test_case': test_case}
    return render(request, 'test_manager/ui_test_run.html', context)


@login_required
def ui_test_run_detail(request, run_id):
    """UI 测试运行详情"""
    test_run = get_object_or_404(UITestRun, pk=run_id)
    result = test_run.result
    
    context = {
        'test_run': test_run,
        'result': result,
    }
    return render(request, 'test_manager/ui_test_run_detail.html', context)


@login_required
def ui_test_run_list(request):
    """UI 测试运行列表"""
    queryset = UITestRun.objects.all().order_by('-created_at')
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
