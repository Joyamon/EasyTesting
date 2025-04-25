from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from django.utils import timezone
from test_manager.models import (
    Project, Environment, TestCase, TestSuite,
    TestSuiteCase, TestRun, TestResult
)
from .serializers import (
    ProjectSerializer, EnvironmentSerializer, TestCaseSerializer,
    TestSuiteSerializer, TestSuiteCaseSerializer, TestRunSerializer,
    TestResultSerializer
)
from test_manager.httprunner_executor import execute_test_case, execute_test_suite


# 自定义分页类
class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        return Project.objects.all().order_by('-created_at')


class EnvironmentViewSet(viewsets.ModelViewSet):
    queryset = Environment.objects.all()
    serializer_class = EnvironmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        project_id = self.request.query_params.get('project', None)
        if project_id:
            return Environment.objects.filter(project_id=project_id).order_by('-created_at')
        return Environment.objects.all().order_by('-created_at')


class TestCaseViewSet(viewsets.ModelViewSet):
    queryset = TestCase.objects.all()
    serializer_class = TestCaseSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        project_id = self.request.query_params.get('project', None)
        if project_id:
            return TestCase.objects.filter(project_id=project_id).order_by('-created_at')
        return TestCase.objects.all().order_by('-created_at')

    @action(detail=True, methods=['post'])
    def run(self, request, pk=None):
        test_case = self.get_object()
        environment_id = request.data.get('environment_id')

        if not environment_id:
            return Response({"error": "Environment ID is required"}, status=status.HTTP_400_BAD_REQUEST)

        environment = get_object_or_404(Environment, id=environment_id)

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
            status=result['status'],
            response_time=result.get('response_time'),
            response_status_code=result.get('response_status_code'),
            response_headers=result.get('response_headers', {}),
            response_body=result.get('response_body'),
            error_message=result.get('error_message', '')
        )

        serializer = TestResultSerializer(test_result)
        return Response(serializer.data)


class TestSuiteViewSet(viewsets.ModelViewSet):
    queryset = TestSuite.objects.all()
    serializer_class = TestSuiteSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        project_id = self.request.query_params.get('project', None)
        if project_id:
            return TestSuite.objects.filter(project_id=project_id).order_by('-created_at')
        return TestSuite.objects.all().order_by('-created_at')

    @action(detail=True, methods=['post'])
    def add_test_case(self, request, pk=None):
        test_suite = self.get_object()
        test_case_id = request.data.get('test_case_id')
        order = request.data.get('order', 0)

        if not test_case_id:
            return Response({"error": "Test case ID is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            test_case = TestCase.objects.get(id=test_case_id)
        except TestCase.DoesNotExist:
            return Response({"error": "Test case not found"}, status=status.HTTP_404_NOT_FOUND)

        # 检查测试用例是否已经在套件中
        existing = TestSuiteCase.objects.filter(test_suite=test_suite, test_case=test_case).first()
        if existing:
            # 如果已存在，返回现有记录
            serializer = TestSuiteCaseSerializer(existing)
            return Response(serializer.data)

        # 创建新的关联
        try:
            test_suite_case = TestSuiteCase.objects.create(
                test_suite=test_suite,
                test_case=test_case,
                order=order
            )
            serializer = TestSuiteCaseSerializer(test_suite_case)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def remove_test_case(self, request, pk=None):
        test_suite = self.get_object()
        test_case_id = request.data.get('test_case_id')

        if not test_case_id:
            return Response({"error": "Test case ID is required"}, status=status.HTTP_400_BAD_REQUEST)

        test_suite_case = get_object_or_404(TestSuiteCase, test_suite=test_suite, test_case_id=test_case_id)
        test_suite_case.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'])
    def run(self, request, pk=None):
        test_suite = self.get_object()
        environment_id = request.data.get('environment_id')

        if not environment_id:
            return Response({"error": "Environment ID is required"}, status=status.HTTP_400_BAD_REQUEST)

        environment = get_object_or_404(Environment, id=environment_id)

        # Create a test run
        test_run = TestRun.objects.create(
            name=f"Suite run: {test_suite.name}",
            project=test_suite.project,
            test_suite=test_suite,
            environment=environment,
            status='running',
            start_time=timezone.now(),
            created_by=request.user
        )

        # Execute the test suite
        results = execute_test_suite(test_suite, environment)

        # Create test results
        for result in results:
            TestResult.objects.create(
                test_run=test_run,
                test_case_id=result['test_case_id'],
                status=result['status'],
                response_time=result.get('response_time'),
                response_status_code=result.get('response_status_code'),
                response_headers=result.get('response_headers', {}),
                response_body=result.get('response_body'),
                error_message=result.get('error_message', '')
            )

        # Update test run
        failed_results = [r for r in results if r['status'] != 'passed']
        test_run.status = 'failed' if failed_results else 'completed'
        test_run.end_time = timezone.now()
        test_run.save()

        serializer = TestRunSerializer(test_run)
        return Response(serializer.data)


class TestRunViewSet(viewsets.ModelViewSet):
    queryset = TestRun.objects.all()
    serializer_class = TestRunSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        project_id = self.request.query_params.get('project', None)
        if project_id:
            return TestRun.objects.filter(project_id=project_id).order_by('-created_at')
        return TestRun.objects.all().order_by('-created_at')

    @action(detail=True, methods=['get'])
    def results(self, request, pk=None):
        test_run = self.get_object()
        results = TestResult.objects.filter(test_run=test_run)

        # 使用分页
        paginator = StandardResultsSetPagination()
        paginated_results = paginator.paginate_queryset(results, request)

        serializer = TestResultSerializer(paginated_results, many=True)
        return paginator.get_paginated_response(serializer.data)


class TestResultViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = TestResult.objects.all()
    serializer_class = TestResultSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        test_run_id = self.request.query_params.get('test_run', None)
        if test_run_id:
            return TestResult.objects.filter(test_run_id=test_run_id).order_by('-created_at')
        return TestResult.objects.all().order_by('-created_at')
