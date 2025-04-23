from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import (
    Project, Environment, TestCase, TestSuite,
    TestSuiteCase, TestRun, TestResult
)


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_by', 'created_at', 'updated_at')
    search_fields = ('name', 'description')
    list_filter = ('created_at', 'updated_at')


@admin.register(Environment)
class EnvironmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'project', 'base_url', 'created_at')
    search_fields = ('name', 'base_url')
    list_filter = ('project', 'created_at')


@admin.register(TestCase)
class TestCaseAdmin(admin.ModelAdmin):
    list_display = ('name', 'project', 'request_method', 'request_url', 'expected_status_code', 'created_by')
    search_fields = ('name', 'description', 'request_url')
    list_filter = ('project', 'request_method', 'expected_status_code', 'created_at')


@admin.register(TestSuite)
class TestSuiteAdmin(admin.ModelAdmin):
    list_display = ('name', 'project', 'created_by', 'created_at')
    search_fields = ('name', 'description')
    list_filter = ('project', 'created_at')


@admin.register(TestSuiteCase)
class TestSuiteCaseAdmin(admin.ModelAdmin):
    list_display = ('test_suite', 'test_case', 'order')
    list_filter = ('test_suite',)


@admin.register(TestRun)
class TestRunAdmin(admin.ModelAdmin):
    list_display = ('name', 'project', 'test_suite', 'environment', 'status', 'start_time', 'end_time', 'created_by')
    search_fields = ('name',)
    list_filter = ('project', 'status', 'created_at')


@admin.register(TestResult)
class TestResultAdmin(admin.ModelAdmin):
    list_display = ('test_run', 'test_case', 'status', 'response_time', 'response_status_code', 'created_at')
    search_fields = ('test_case__name', 'error_message')
    list_filter = ('test_run', 'status', 'created_at')
