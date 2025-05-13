import datetime

from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.utils import timezone
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from .async_executor import execute_test_suite_async
from .models import (
    Project, Environment, TestCase, TestSuite,
    TestSuiteCase, TestRun, TestResult, EmailConfig, TestSuiteGroup, TestCaseGroup
)
from .forms import (
    ProjectForm, EnvironmentForm, TestCaseForm, TestSuiteForm,
    TestRunForm, EmailConfigForm, TestEmailForm, TestSuiteGroupForm, TestCaseGroupForm
)
from .httprunner_executor import execute_test_case, execute_test_suite


def paginate_queryset(request, queryset, per_page=10):
    page = request.GET.get('page', 1)
    paginator = Paginator(queryset, per_page)

    try:
        paginated_queryset = paginator.page(page)
    except PageNotAnInteger:
        paginated_queryset = paginator.page(1)
    except EmptyPage:
        paginated_queryset = paginator.page(paginator.num_pages)

    return paginated_queryset


@login_required
def dashboard(request):
    # Get counts for dashboard
    projects_count = Project.objects.count()
    test_cases_count = TestCase.objects.count()
    test_suites_count = TestSuite.objects.count()
    test_runs_count = TestRun.objects.count()

    # Get recent test runs with pagination
    all_test_runs = TestRun.objects.order_by('-created_at')
    recent_test_runs = paginate_queryset(request, all_test_runs, 5)

    # Get test run statistics
    test_run_stats = {
        'total': test_runs_count,
        'passed': TestRun.objects.filter(status='completed').count(),
        'failed': TestRun.objects.filter(status='failed').count(),
        'pending': TestRun.objects.filter(status='pending').count(),
        'running': TestRun.objects.filter(status='running').count(),
    }

    # Get test result statistics
    test_result_stats = {
        'total': TestResult.objects.count(),
        'passed': TestResult.objects.filter(status='passed').count(),
        'failed': TestResult.objects.filter(status='failed').count(),
        'error': TestResult.objects.filter(status='error').count(),
        'skipped': TestResult.objects.filter(status='skipped').count(),
    }

    # 模拟最近活动数据
    recent_activities = [
        {
            'action': 'Test run completed',
            'timestamp': timezone.now() - datetime.timedelta(hours=2),
            'description': 'API Integration Test Suite completed successfully'
        },
        {
            'action': 'Test case created',
            'timestamp': timezone.now() - datetime.timedelta(hours=5),
            'description': 'New test case "Login Authentication" added to Auth Project'
        },
        {
            'action': 'Project updated',
            'timestamp': timezone.now() - datetime.timedelta(days=1),
            'description': 'Project "Payment Gateway" description and settings updated'
        },
        {
            'action': 'Test run failed',
            'timestamp': timezone.now() - datetime.timedelta(days=1, hours=6),
            'description': 'Checkout Process Test Suite failed with 3 errors'
        },
        {
            'action': 'Environment created',
            'timestamp': timezone.now() - datetime.timedelta(days=2),
            'description': 'New staging environment created for E-commerce Project'
        },
    ]

    context = {
        'projects_count': projects_count,
        'test_cases_count': test_cases_count,
        'test_suites_count': test_suites_count,
        'test_runs_count': test_runs_count,
        'recent_test_runs': recent_test_runs,
        'test_run_stats': test_run_stats,
        'test_result_stats': test_result_stats,
        'recent_activities': recent_activities,
    }

    return render(request, 'test_manager/dashboard.html', context)


# Project views
@login_required
def project_list(request):
    all_projects = Project.objects.all().order_by('-created_at')

    # 获取每页显示的记录数
    per_page = request.GET.get('per_page', 10)
    try:
        per_page = int(per_page)
    except ValueError:
        per_page = 10

    projects = paginate_queryset(request, all_projects, per_page)

    return render(request, 'test_manager/project_list.html', {
        'projects': projects,
        'per_page': per_page
    })


@login_required
def project_create(request):
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.created_by = request.user
            project.save()
            messages.success(request, 'Project created successfully.')
            return redirect('project_detail', pk=project.pk)
    else:
        form = ProjectForm()

    return render(request, 'test_manager/project_form.html', {'form': form, 'title': 'Create Project'})


@login_required
def project_detail(request, pk):
    project = get_object_or_404(Project, pk=pk)

    # 获取每页显示的记录数
    per_page = request.GET.get('per_page', 5)
    try:
        per_page = int(per_page)
    except ValueError:
        per_page = 5

    # 分页获取环境、测试用例、测试套件和测试运行
    all_environments = Environment.objects.filter(project=project)
    all_test_cases = TestCase.objects.filter(project=project)
    all_test_suites = TestSuite.objects.filter(project=project)
    all_test_runs = TestRun.objects.filter(project=project).order_by('-created_at')

    environments = paginate_queryset(request, all_environments, per_page)
    test_cases = paginate_queryset(request, all_test_cases, per_page)
    test_suites = paginate_queryset(request, all_test_suites, per_page)
    test_runs = paginate_queryset(request, all_test_runs, per_page)

    context = {
        'project': project,
        'environments': environments,
        'test_cases': test_cases,
        'test_suites': test_suites,
        'test_runs': test_runs,
        'per_page': per_page,
        'all_environments_count': all_environments.count(),
        'all_test_cases_count': all_test_cases.count(),
        'all_test_suites_count': all_test_suites.count(),
        'all_test_runs_count': all_test_runs.count(),
    }

    return render(request, 'test_manager/project_detail.html', context)


@login_required
def project_edit(request, pk):
    project = get_object_or_404(Project, pk=pk)

    if request.method == 'POST':
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            form.save()
            messages.success(request, 'Project updated successfully.')
            return redirect('project_detail', pk=project.pk)
    else:
        form = ProjectForm(instance=project)

    return render(request, 'test_manager/project_form.html', {'form': form, 'title': 'Edit Project'})


@login_required
def project_delete(request, pk):
    # 删除项目时，检查该项目是否存在关联的测试用例、测试套件或测试运行
    project = get_object_or_404(Project, pk=pk)
    if project.test_runs.exists() or project.test_suites.exists() or project.test_cases.exists():
        messages.warning(request, 'Cannot delete project with associated test cases, test suites, or test runs.')
    else:
        project.delete()
        messages.success(request, 'Project deleted successfully.')
    return redirect('project_list')


# Environment views
@login_required
def environment_list(request):
    project_id = request.GET.get('project')

    # 获取每页显示的记录数
    per_page = request.GET.get('per_page', 10)
    try:
        per_page = int(per_page)
    except ValueError:
        per_page = 10

    if project_id:
        all_environments = Environment.objects.filter(project_id=project_id).order_by('-created_at')
        project = get_object_or_404(Project, pk=project_id)
        environments = paginate_queryset(request, all_environments, per_page)
        context = {
            'environments': environments,
            'project': project,
            'per_page': per_page,
            'total_count': all_environments.count()
        }
    else:
        all_environments = Environment.objects.all().order_by('-created_at')
        environments = paginate_queryset(request, all_environments, per_page)
        context = {
            'environments': environments,
            'per_page': per_page,
            'total_count': all_environments.count()
        }

    return render(request, 'test_manager/environment_list.html', context)


@login_required
def environment_create(request):
    project_id = request.GET.get('project')

    if request.method == 'POST':
        form = EnvironmentForm(request.POST)
        if form.is_valid():
            environment = form.save()
            messages.success(request, 'Environment created successfully.')
            return redirect('environment_detail', pk=environment.pk)
    else:
        initial = {}
        if project_id:
            initial['project'] = project_id
        form = EnvironmentForm(initial=initial)

    return render(request, 'test_manager/environment_form.html', {'form': form, 'title': 'Create Environment'})


@login_required
def environment_detail(request, pk):
    environment = get_object_or_404(Environment, pk=pk)

    # 获取每页显示的记录数
    per_page = request.GET.get('per_page', 5)
    try:
        per_page = int(per_page)
    except ValueError:
        per_page = 5

    # 分页获取测试运行
    all_test_runs = environment.test_runs.all().order_by('-created_at')
    test_runs = paginate_queryset(request, all_test_runs, per_page)

    context = {
        'environment': environment,
        'test_runs': test_runs,
        'per_page': per_page,
        'total_test_runs': all_test_runs.count()
    }

    return render(request, 'test_manager/environment_detail.html', context)


@login_required
def environment_edit(request, pk):
    environment = get_object_or_404(Environment, pk=pk)

    if request.method == 'POST':
        form = EnvironmentForm(request.POST, instance=environment)
        if form.is_valid():
            form.save()
            messages.success(request, 'Environment updated successfully.')
            return redirect('environment_detail', pk=environment.pk)
    else:
        form = EnvironmentForm(instance=environment)

    return render(request, 'test_manager/environment_form.html', {'form': form, 'title': 'Edit Environment'})


@login_required
def environment_delete(request, pk):
    # 删除环境时，检查该环境是否存在关联的测试运行
    environment = get_object_or_404(Environment, pk=pk)
    if environment.test_runs.exists():
        messages.warning(request, 'Cannot delete environment with associated test runs.')
    else:
        environment.delete()
        messages.success(request, 'Environment deleted successfully.')
    return redirect('environment_list')


# Test Case views
@login_required
def test_case_list(request):
    project_id = request.GET.get('project')
    group_id = request.GET.get('group')
    search_query = request.GET.get('search', '')

    # 获取每页显示的记录数
    per_page = request.GET.get('per_page', 10)
    try:
        per_page = int(per_page)
    except ValueError:
        per_page = 10

    if project_id:
        project = get_object_or_404(Project, pk=project_id)

        # 构建查询条件
        query = Q(project=project)

        # 如果指定了分组，则只显示该分组下的测试用例
        if group_id:
            group = get_object_or_404(TestCaseGroup, pk=group_id)
            query &= Q(group=group)

            # 获取当前分组的所有子分组
            child_groups = TestCaseGroup.objects.filter(project=project, parent=group)
        else:
            # 获取项目的所有顶级分组
            child_groups = TestCaseGroup.objects.filter(project=project, parent=None)

        # 如果有搜索查询，添加搜索条件
        if search_query:
            query &= (Q(name__icontains=search_query) |
                      Q(description__icontains=search_query) |
                      Q(request_url__icontains=search_query))

        all_test_cases = TestCase.objects.filter(query).order_by('-created_at')
        test_cases = paginate_queryset(request, all_test_cases, per_page)

        context = {
            'test_cases': test_cases,
            'project': project,
            'current_group': group if group_id else None,
            'child_groups': child_groups,
            'per_page': per_page,
            'total_count': all_test_cases.count(),
            'search_query': search_query
        }
    else:
        # 构建查询条件
        query = Q()

        # 如果有搜索查询，添加搜索条件
        if search_query:
            query &= (Q(name__icontains=search_query) |
                      Q(description__icontains=search_query) |
                      Q(request_url__icontains=search_query))

        all_test_cases = TestCase.objects.filter(query).order_by('-created_at')
        test_cases = paginate_queryset(request, all_test_cases, per_page)

        context = {
            'test_cases': test_cases,
            'per_page': per_page,
            'total_count': all_test_cases.count(),
            'search_query': search_query
        }

    return render(request, 'test_manager/test_case_list.html', context)


@login_required
def test_case_create(request):
    project_id = request.GET.get('project')

    if request.method == 'POST':
        form = TestCaseForm(request.POST)
        if form.is_valid():
            test_case = form.save(commit=False)
            test_case.created_by = request.user
            test_case.save()
            messages.success(request, 'Test case created successfully.')
            return redirect('test_case_detail', pk=test_case.pk)
    else:
        initial = {}
        if project_id:
            initial['project'] = project_id
        form = TestCaseForm(initial=initial)

    return render(request, 'test_manager/test_case_form.html', {'form': form, 'title': 'Create Test Case'})


@login_required
def test_case_detail(request, pk):
    test_case = get_object_or_404(TestCase, pk=pk)

    # 获取每页显示的记录数
    per_page = request.GET.get('per_page', 10)
    try:
        per_page = int(per_page)
    except ValueError:
        per_page = 10

    # 分页获取测试结果
    all_test_results = TestResult.objects.filter(test_case=test_case).order_by('-created_at')
    test_results = paginate_queryset(request, all_test_results, per_page)

    context = {
        'test_case': test_case,
        'test_results': test_results,
        'per_page': per_page,
        'total_results': all_test_results.count()
    }

    return render(request, 'test_manager/test_case_detail.html', context)


@login_required
def test_case_edit(request, pk):
    test_case = get_object_or_404(TestCase, pk=pk)

    if request.method == 'POST':
        form = TestCaseForm(request.POST, instance=test_case)
        if form.is_valid():
            form.save()
            messages.success(request, 'Test case updated successfully.')
            return redirect('test_case_detail', pk=test_case.pk)
    else:
        form = TestCaseForm(instance=test_case)

    return render(request, 'test_manager/test_case_form.html', {'form': form, 'title': 'Edit Test Case'})


@login_required
def test_case_run(request, pk):
    test_case = get_object_or_404(TestCase, pk=pk)

    if request.method == 'POST':
        environment_id = request.POST.get('environment')
        if not environment_id:
            messages.error(request, 'Environment is required.')
            return redirect('test_case_detail', pk=test_case.pk)

        environment = get_object_or_404(Environment, pk=environment_id)

        # Create a test run
        test_run = TestRun.objects.create(
            name=f"Single run: {test_case.name}",
            project=test_case.project,
            environment=environment,
            status='running',
            start_time=timezone.now(),
            created_by=request.user
        )

        # Execute the test case
        result = execute_test_case(test_case, environment)

        # Update test run
        test_run.status = 'completed' if result['status'] == 'passed' else 'failed'
        test_run.end_time = timezone.now()
        test_run.save()

        # Create test result
        test_result = TestResult.objects.create(
            test_run=test_run,
            test_case=test_case,
            environment=environment,
            status=result['status'],
            response_time=result.get('response_time'),
            response_status_code=result.get('response_status_code'),
            response_headers=result.get('response_headers', {}),
            response_body=result.get('response_body'),
            error_message=result.get('error_message', ''),
            extracted_params=result.get('extracted_params', {}),
            validators=result.get('validators', [])

        )

        messages.success(request, f'Test case executed. Result: {result["status"]}')
        return redirect('test_run_detail', pk=test_run.pk)

    environments = Environment.objects.filter(project=test_case.project)
    return render(request, 'test_manager/test_case_run.html', {'test_case': test_case, 'environments': environments})


# Test Suite views
@login_required
def test_suite_list(request):
    project_id = request.GET.get('project')
    group_id = request.GET.get('group')
    search_query = request.GET.get('search', '')

    # 获取每页显示的记录数
    per_page = request.GET.get('per_page', 10)
    try:
        per_page = int(per_page)
    except ValueError:
        per_page = 10

    # 初始化查询条件
    query = Q()

    if project_id:
        project = get_object_or_404(Project, pk=project_id)
        # 添加项目条件
        query &= Q(project=project)

        # 如果指定了分组，则只显示该分组下的测试套件
        if group_id:
            group = get_object_or_404(TestSuiteGroup, pk=group_id)
            query &= Q(group=group)

            # 获取当前分组的所有子分组
            child_groups = TestSuiteGroup.objects.filter(project=project, parent=group)
        else:
            # 获取项目的所有顶级分组
            child_groups = TestSuiteGroup.objects.filter(project=project, parent=None)

        # 如果有搜索查询，添加搜索条件
        if search_query:
            query &= (Q(name__icontains=search_query) |
                      Q(description__icontains=search_query))

        # 应用查询条件
        all_test_suites = TestSuite.objects.filter(query).order_by('-created_at')
        test_suites = paginate_queryset(request, all_test_suites, per_page)

        context = {
            'test_suites': test_suites,
            'project': project,
            'current_group': group if group_id else None,
            'child_groups': child_groups,
            'per_page': per_page,
            'total_count': all_test_suites.count(),
            'search_query': search_query
        }
    else:
        # 如果有搜索查询，添加搜索条件
        if search_query:
            query &= (Q(name__icontains=search_query) |
                      Q(description__icontains=search_query))

        all_test_suites = TestSuite.objects.filter(query).order_by('-created_at')
        test_suites = paginate_queryset(request, all_test_suites, per_page)

        context = {
            'test_suites': test_suites,
            'per_page': per_page,
            'total_count': all_test_suites.count(),
            'search_query': search_query
        }

    return render(request, 'test_manager/test_suite_list.html', context)


@login_required
def test_suite_create(request):
    project_id = request.GET.get('project')

    if request.method == 'POST':
        form = TestSuiteForm(request.POST)
        if form.is_valid():
            test_suite = form.save(commit=False)
            test_suite.created_by = request.user
            test_suite.save()
            messages.success(request, 'Test suite created successfully.')
            return redirect('test_suite_detail', pk=test_suite.pk)
    else:
        initial = {}
        if project_id:
            initial['project'] = project_id
        form = TestSuiteForm(initial=initial)

    return render(request, 'test_manager/test_suite_form.html', {'form': form, 'title': 'Create Test Suite'})


@login_required
def test_suite_detail(request, pk):
    test_suite = get_object_or_404(TestSuite, pk=pk)

    # 获取每页显示的记录数
    per_page = request.GET.get('per_page', 10)
    try:
        per_page = int(per_page)
    except ValueError:
        per_page = 10

    # 分页获取测试用例和测试运行
    all_test_suite_cases = TestSuiteCase.objects.filter(test_suite=test_suite).order_by('order')
    all_test_runs = TestRun.objects.filter(test_suite=test_suite).order_by('-created_at')

    test_suite_cases = paginate_queryset(request, all_test_suite_cases, per_page)
    test_runs = paginate_queryset(request, all_test_runs, per_page)

    # 获取项目中的所有测试用例，而不仅仅是未添加到套件的测试用例
    project_test_cases = TestCase.objects.filter(project=test_suite.project)

    # 获取项目中的所有测试用例分组
    test_case_groups = TestCaseGroup.objects.filter(project=test_suite.project)

    # 获取每个分组下的测试用例
    grouped_test_cases = {}
    for group in test_case_groups:
        group_test_cases = TestCase.objects.filter(project=test_suite.project, group=group)
        if group_test_cases.exists():
            grouped_test_cases[group.id] = {
                'group': group,
                'test_cases': group_test_cases
            }

    # 获取未分组的测试用例
    ungrouped_test_cases = TestCase.objects.filter(project=test_suite.project, group__isnull=True)

    # 获取已添加到测试套件的测试用例ID列表
    added_test_case_ids = TestSuiteCase.objects.filter(test_suite=test_suite).values_list('test_case_id', flat=True)

    # 获取项目的所有环境
    environments = Environment.objects.filter(project=test_suite.project)

    context = {
        'test_suite': test_suite,
        'test_suite_cases': test_suite_cases,
        'test_runs': test_runs,
        'project_test_cases': project_test_cases,
        'grouped_test_cases': grouped_test_cases,
        'ungrouped_test_cases': ungrouped_test_cases,
        'added_test_case_ids': list(added_test_case_ids),
        'environments': environments,
        'per_page': per_page,
        'total_cases': all_test_suite_cases.count(),
        'total_runs': all_test_runs.count()
    }

    return render(request, 'test_manager/test_suite_detail.html', context)


@login_required
def test_suite_edit(request, pk):
    test_suite = get_object_or_404(TestSuite, pk=pk)

    if request.method == 'POST':
        form = TestSuiteForm(request.POST, instance=test_suite)
        if form.is_valid():
            form.save()
            messages.success(request, 'Test suite updated successfully.')
            return redirect('test_suite_detail', pk=test_suite.pk)
    else:
        form = TestSuiteForm(instance=test_suite)

    return render(request, 'test_manager/test_suite_form.html', {'form': form, 'title': 'Edit Test Suite'})



@login_required
def test_suite_run(request, pk):
    """
    异步执行测试套件
    """
    test_suite = get_object_or_404(TestSuite, pk=pk)

    if request.method == 'POST':
        environment_id = request.POST.get('environment')
        if not environment_id:
            messages.error(request, 'Environment is required.')
            return redirect('test_suite_detail', pk=test_suite.pk)

        environment = get_object_or_404(Environment, pk=environment_id)

        # 获取每个测试用例的环境设置
        case_environments = {}
        for key, value in request.POST.items():
            if key.startswith('case_environment_') and value:
                case_id = key.replace('case_environment_', '')
                case_environments[int(case_id)] = int(value)

        # 创建测试运行记录
        test_run = TestRun.objects.create(
            name=request.POST.get('name', f"Suite run: {test_suite.name}"),
            project=test_suite.project,
            test_suite=test_suite,
            environment=environment,
            status='running',  # 初始状态为运行中
            start_time=timezone.now(),
            created_by=request.user
        )

        # 异步执行测试套件
        execute_test_suite_async(
            test_suite=test_suite,
            environment=environment,
            case_environments=case_environments,
            test_run=test_run,
            user=request.user,
            execute_test_suite_func=execute_test_suite
        )

        messages.success(
            request,
            f'Test suite execution started. You can check the results in the test run details page.'
        )
        return redirect('test_run_detail', pk=test_run.pk)

    environments = Environment.objects.filter(project=test_suite.project)
    test_suite_cases = TestSuiteCase.objects.filter(test_suite=test_suite).order_by('order')

    return render(request, 'test_manager/test_suite_run.html', {
        'test_suite': test_suite,
        'environments': environments,
        'test_suite_cases': test_suite_cases
    })


# Test Run views
@login_required
def test_run_list(request):
    project_id = request.GET.get('project')

    # 获取每页显示的记录数
    per_page = request.GET.get('per_page', 10)
    try:
        per_page = int(per_page)
    except ValueError:
        per_page = 10

    if project_id:
        all_test_runs = TestRun.objects.filter(project_id=project_id).order_by('-created_at')
        project = get_object_or_404(Project, pk=project_id)
        test_runs = paginate_queryset(request, all_test_runs, per_page)
        context = {
            'test_runs': test_runs,
            'project': project,
            'per_page': per_page,
            'total_count': all_test_runs.count()

        }
    else:
        all_test_runs = TestRun.objects.all().order_by('-created_at')
        test_runs = paginate_queryset(request, all_test_runs, per_page)
        context = {
            'test_runs': test_runs,
            'per_page': per_page,
            'total_count': all_test_runs.count()
        }

    return render(request, 'test_manager/test_run_list.html', context)


@login_required
def test_run_detail(request, pk):
    test_run = get_object_or_404(TestRun, pk=pk)

    # 获取每页显示的记录数
    per_page = request.GET.get('per_page', 10)
    try:
        per_page = int(per_page)
    except ValueError:
        per_page = 10

    # 分页获取测试结果
    all_test_results = TestResult.objects.filter(test_run=test_run)
    test_results = paginate_queryset(request, all_test_results, per_page)
    print("test_results:", test_results)

    # Calculate statistics
    total_tests = all_test_results.count()
    passed_tests = all_test_results.filter(status='passed').count()
    failed_tests = all_test_results.filter(status='failed').count()
    error_tests = all_test_results.filter(status='error').count()
    skipped_tests = all_test_results.filter(status='skipped').count()

    context = {
        'test_run': test_run,
        'test_results': test_results,
        'total_tests': total_tests,
        'passed_tests': passed_tests,
        'failed_tests': failed_tests,
        'error_tests': error_tests,
        'skipped_tests': skipped_tests,
        'per_page': per_page,
        'total_results': total_tests
    }

    return render(request, 'test_manager/test_run_detail.html', context)


@login_required
def test_run_delete(request, pk):
    test_run = get_object_or_404(TestRun, pk=pk)
    test_run.delete()
    messages.success(request, 'TestRun deleted successfully.')
    return redirect('test_run_list')


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.urls import reverse


def is_admin(request, user):
    """检查用户是否是管理员"""
    if user.is_superuser:
        return user.is_superuser
    else:
        messages.error(request, '您不是管理员，无法访问此页面。')
    # return user.is_superuser


@login_required
# @user_passes_test(is_admin)
def email_config_list(request):
    """邮件配置列表视图"""
    configs = EmailConfig.objects.all().order_by('-is_active', '-updated_at')
    return render(request, 'admin/email_config_list.html', {'configs': configs})


@login_required
# @user_passes_test(is_admin)
def email_config_create(request):
    """创建邮件配置视图"""
    if request.method == 'POST':
        form = EmailConfigForm(request.POST)
        if form.is_valid():
            config = form.save()
            messages.success(request, f"邮件配置 '{config.name}' 创建成功")
            return redirect('email_config_list')
    else:
        form = EmailConfigForm()

    return render(request, 'admin/email_config_form.html', {
        'form': form,
        'title': '创建邮件配置',
        'submit_text': '创建',
    })


@login_required
# @user_passes_test(is_admin)
def email_config_edit(request, pk):
    """编辑邮件配置视图"""
    config = get_object_or_404(EmailConfig, pk=pk)

    if request.method == 'POST':
        form = EmailConfigForm(request.POST, instance=config)
        if form.is_valid():
            config = form.save()
            messages.success(request, f"邮件配置 '{config.name}' 更新成功")
            return redirect('email_config_list')
    else:
        form = EmailConfigForm(instance=config)

    return render(request, 'admin/email_config_form.html', {
        'form': form,
        'config': config,
        'title': f"编辑邮件配置: {config.name}",
        'submit_text': '保存',
    })


@login_required
# @user_passes_test(is_admin)
def email_config_delete(request, pk):
    """删除邮件配置视图"""
    config = get_object_or_404(EmailConfig, pk=pk)

    if request.method == 'POST':
        name = config.name
        config.delete()
        messages.success(request, f"邮件配置 '{name}' 已删除")
        return redirect('email_config_list')

    return render(request, 'admin/email_config_delete.html', {'config': config})


@login_required
# @user_passes_test(is_admin)
def email_config_test(request, pk):
    """测试邮件配置视图"""
    config = get_object_or_404(EmailConfig, pk=pk)

    if request.method == 'POST':
        form = TestEmailForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            success, message = config.send_test_email(email)

            if success:
                messages.success(request, message)
            else:
                messages.error(request, message)

            return redirect('email_config_list')
    else:
        form = TestEmailForm()

    return render(request, 'admin/email_config_test.html', {
        'form': form,
        'config': config,
    })


@login_required
# @user_passes_test(is_admin)
def email_config_activate(request, pk):
    """激活邮件配置视图"""
    config = get_object_or_404(EmailConfig, pk=pk)

    # 测试连接
    success, message = config.test_connection()

    if success:
        config.is_active = True
        config.save()  # save 方法会自动将其他配置设置为非激活
        EmailConfig.apply_active_config()  # 应用配置到 Django 设置
        messages.success(request, f"邮件配置 '{config.name}' 已激活: {message}")
    else:
        messages.error(request, f"无法激活邮件配置: {message}")

    return redirect('email_config_list')


# 测试用例分组视图
@login_required
def test_case_group_list(request):
    project_id = request.GET.get('project')

    if project_id:
        project = get_object_or_404(Project, pk=project_id)
        # 获取顶级分组
        root_groups = TestCaseGroup.objects.filter(project=project, parent=None).order_by('name')
        context = {
            'project': project,
            'root_groups': root_groups,
        }
    else:
        # 获取所有项目的顶级分组
        projects = Project.objects.all()
        project_groups = []
        for project in projects:
            root_groups = TestCaseGroup.objects.filter(project=project, parent=None).order_by('name')
            if root_groups.exists():
                project_groups.append({
                    'project': project,
                    'root_groups': root_groups,
                })

        context = {
            'project_groups': project_groups,
        }

    return render(request, 'test_manager/test_case_group_list.html', context)


@login_required
def test_case_group_create(request):
    project_id = request.GET.get('project')
    parent_id = request.GET.get('parent')

    if not project_id:
        messages.error(request, 'Project ID is required.')
        return redirect('project_list')

    project = get_object_or_404(Project, pk=project_id)

    if request.method == 'POST':
        form = TestCaseGroupForm(request.POST, project_id=project_id)
        if form.is_valid():
            group = form.save(commit=False)
            group.created_by = request.user
            group.save()
            messages.success(request, 'Test case group created successfully.')
            return redirect('test_case_list')
    else:
        initial = {'project': project}
        if parent_id:
            parent = get_object_or_404(TestCaseGroup, pk=parent_id)
            initial['parent'] = parent

        form = TestCaseGroupForm(initial=initial, project_id=project_id)

    return render(request, 'test_manager/test_case_group_form.html', {
        'form': form,
        'title': 'Create Test Case Group',
        'project': project,
    })


@login_required
def test_case_group_edit(request, pk):
    group = get_object_or_404(TestCaseGroup, pk=pk)
    project = group.project

    if request.method == 'POST':
        form = TestCaseGroupForm(request.POST, instance=group, project_id=project.id)
        if form.is_valid():
            form.save()
            messages.success(request, 'Test case group updated successfully.')
            return redirect('test_case_list')
    else:
        form = TestCaseGroupForm(instance=group, project_id=project.id)

    return render(request, 'test_manager/test_case_group_form.html', {
        'form': form,
        'title': 'Edit Test Case Group',
        'project': project,
        'group': group,
    })


@login_required
def test_case_group_delete(request, pk):
    group = get_object_or_404(TestCaseGroup, pk=pk)
    project_id = group.project.id

    # 检查是否有子分组或测试用例
    if TestCaseGroup.objects.filter(parent=group).exists() or TestCase.objects.filter(group=group).exists():
        messages.warning(request, 'Cannot delete group with child groups or test cases.')
    else:
        group.delete()
        messages.success(request, 'Test case group deleted successfully.')

    return redirect('test_case_list')


# 测试套件分组视图
@login_required
def test_suite_group_list(request):
    project_id = request.GET.get('project')

    if project_id:
        project = get_object_or_404(Project, pk=project_id)
        # 获取顶级分组
        root_groups = TestSuiteGroup.objects.filter(project=project, parent=None).order_by('name')
        context = {
            'project': project,
            'root_groups': root_groups,
        }
    else:
        # 获取所有项目的顶级分组
        projects = Project.objects.all()
        project_groups = []
        for project in projects:
            root_groups = TestSuiteGroup.objects.filter(project=project, parent=None).order_by('name')
            if root_groups.exists():
                project_groups.append({
                    'project': project,
                    'root_groups': root_groups,
                })

        context = {
            'project_groups': project_groups,
        }

    return render(request, 'test_manager/test_suite_group_list.html', context)


@login_required
def test_suite_group_create(request):
    project_id = request.GET.get('project')
    parent_id = request.GET.get('parent')

    if not project_id:
        messages.error(request, 'Project ID is required.')
        return redirect('project_list')

    project = get_object_or_404(Project, pk=project_id)

    if request.method == 'POST':
        form = TestSuiteGroupForm(request.POST, project_id=project_id)
        if form.is_valid():
            group = form.save(commit=False)
            group.created_by = request.user
            group.save()
            messages.success(request, 'Test suite group created successfully.')
            return redirect('test_suite_list')
    else:
        initial = {'project': project}
        if parent_id:
            parent = get_object_or_404(TestSuiteGroup, pk=parent_id)
            initial['parent'] = parent

        form = TestSuiteGroupForm(initial=initial, project_id=project_id)

    return render(request, 'test_manager/test_suite_group_form.html', {
        'form': form,
        'title': 'Create Test Suite Group',
        'project': project,
    })


@login_required
def test_suite_group_edit(request, pk):
    group = get_object_or_404(TestSuiteGroup, pk=pk)
    project = group.project

    if request.method == 'POST':
        form = TestSuiteGroupForm(request.POST, instance=group, project_id=project.id)
        if form.is_valid():
            form.save()
            messages.success(request, 'Test suite group updated successfully.')
            return redirect('test_suite_list')
    else:
        form = TestSuiteGroupForm(instance=group, project_id=project.id)

    return render(request, 'test_manager/test_suite_group_form.html', {
        'form': form,
        'title': 'Edit Test Suite Group',
        'project': project,
        'group': group,
    })


@login_required
def test_suite_group_delete(request, pk):
    group = get_object_or_404(TestSuiteGroup, pk=pk)
    project_id = group.project.id

    # 检查是否有子分组或测试套件
    if TestSuiteGroup.objects.filter(parent=group).exists() or TestSuite.objects.filter(group=group).exists():
        messages.warning(request, 'Cannot delete group with child groups or test suites.')
    else:
        group.delete()
        messages.success(request, 'Test suite group deleted successfully.')

    return redirect('test_suite_list')


# 获取测试用例分组数据的API
@login_required
def get_test_case_groups_data(request, project_id):
    """获取项目的测试用例分组数据，用于前端展示"""
    project = get_object_or_404(Project, pk=project_id)

    # 获取所有分组
    groups = TestCaseGroup.objects.filter(project=project)

    # 构建分组树
    group_tree = []
    group_dict = {}

    # 先创建所有分组的字典
    for group in groups:
        group_data = {
            'id': group.id,
            'name': group.name,
            'parent_id': group.parent_id,
            'children': [],
            'test_cases': []
        }
        group_dict[group.id] = group_data

    # 构建分组树
    for group_id, group_data in group_dict.items():
        if group_data['parent_id'] is None:
            # 顶级分组
            group_tree.append(group_data)
        else:
            # 子分组
            parent_data = group_dict.get(group_data['parent_id'])
            if parent_data:
                parent_data['children'].append(group_data)

    # 获取每个分组下的测试用例
    for group in groups:
        test_cases = TestCase.objects.filter(project=project, group=group)
        group_data = group_dict.get(group.id)
        if group_data:
            for test_case in test_cases:
                group_data['test_cases'].append({
                    'id': test_case.id,
                    'name': test_case.name,
                    'method': test_case.request_method,
                    'url': test_case.request_url
                })

    # 获取未分组的测试用例
    ungrouped_test_cases = TestCase.objects.filter(project=project, group__isnull=True)
    ungrouped_data = {
        'id': 0,
        'name': 'Ungrouped',
        'parent_id': None,
        'children': [],
        'test_cases': []
    }

    for test_case in ungrouped_test_cases:
        ungrouped_data['test_cases'].append({
            'id': test_case.id,
            'name': test_case.name,
            'method': test_case.request_method,
            'url': test_case.request_url
        })

    # 如果有未分组的测试用例，添加到结果中
    if ungrouped_data['test_cases']:
        group_tree.append(ungrouped_data)

    return JsonResponse({
        'groups': group_tree
    })
