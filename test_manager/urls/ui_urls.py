"""
UI 自动化测试 URL 配置
"""

from django.urls import path
from test_manager.views.ui_views import (
    ui_test_case_list,
    ui_test_case_create,
    ui_test_case_detail,
    ui_test_case_edit,
    ui_test_case_delete,
    ui_test_step_add,
    ui_test_step_edit,
    ui_test_step_delete,
    ui_test_run,
    ui_test_run_detail,
    ui_test_run_list,
)

urlpatterns = [
    # UI 测试用例
    path('ui-test-cases/', ui_test_case_list, name='ui_test_case_list'),
    path('ui-test-cases/create/', ui_test_case_create, name='ui_test_case_create'),
    path('ui-test-cases/<int:pk>/', ui_test_case_detail, name='ui_test_case_detail'),
    path('ui-test-cases/<int:pk>/edit/', ui_test_case_edit, name='ui_test_case_edit'),
    path('ui-test-cases/<int:pk>/delete/', ui_test_case_delete, name='ui_test_case_delete'),
    path('ui-test-cases/<int:pk>/run/', ui_test_run, name='ui_test_run'),

    # UI 测试步骤
    path('ui-test-cases/<int:test_case_id>/steps/add/', ui_test_step_add, name='ui_test_step_add'),
    path('ui-test-steps/<int:step_id>/edit/', ui_test_step_edit, name='ui_test_step_edit'),
    path('ui-test-steps/<int:step_id>/delete/', ui_test_step_delete, name='ui_test_step_delete'),

    # UI 测试运行
    path('ui-test-runs/', ui_test_run_list, name='ui_test_run_list'),
    path('ui-test-runs/<int:run_id>/', ui_test_run_detail, name='ui_test_run_detail'),
]
