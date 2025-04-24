# from django.urls import path
# from . import views, email_views
#
# urlpatterns = [
#     path('dashboard/', views.dashboard, name='dashboard'),
#     path('projects/', views.project_list, name='project_list'),
#     path('projects/create/', views.project_create, name='project_create'),
#     path('projects/<int:pk>/', views.project_detail, name='project_detail'),
#     path('projects/<int:pk>/edit/', views.project_edit, name='project_edit'),
#     path('projects/<int:pk>/delete/', views.project_delete, name='project_delete'),
#
#     # path('environments/edit/', views.project_edit, name='project_edit'),
#
#     path('environments/', views.environment_list, name='environment_list'),
#     path('environments/create/', views.environment_create, name='environment_create'),
#     path('environments/<int:pk>/', views.environment_detail, name='environment_detail'),
#     path('environments/<int:pk>/edit/', views.environment_edit, name='environment_edit'),
#     path('environments/<int:pk>/delete/', views.environment_delete, name='environment_delete'),
#
#     path('test-cases/', views.test_case_list, name='test_case_list'),
#     path('test-cases/create/', views.test_case_create, name='test_case_create'),
#     path('test-cases/<int:pk>/', views.test_case_detail, name='test_case_detail'),
#     path('test-cases/<int:pk>/edit/', views.test_case_edit, name='test_case_edit'),
#     path('test-cases/<int:pk>/run/', views.test_case_run, name='test_case_run'),
#
#     path('test-suites/', views.test_suite_list, name='test_suite_list'),
#     path('test-suites/create/', views.test_suite_create, name='test_suite_create'),
#     path('test-suites/<int:pk>/', views.test_suite_detail, name='test_suite_detail'),
#     path('test-suites/<int:pk>/edit/', views.test_suite_edit, name='test_suite_edit'),
#     path('test-suites/<int:pk>/run/', views.test_suite_run, name='test_suite_run'),
#
#     path('test-runs/', views.test_run_list, name='test_run_list'),
#     path('test-runs/<int:pk>/', views.test_run_detail, name='test_run_detail'),
#     path('test-runs/<int:pk>/delete/', views.test_run_delete, name='test_run_delete')
# ]
