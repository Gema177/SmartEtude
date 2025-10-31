from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('courses/<uuid:course_id>/', views.course_analytics_view, name='course_analytics'),
    path('users/<int:user_id>/', views.user_analytics_view, name='user_analytics'),
    path('system/', views.system_analytics_view, name='system_analytics'),
    path('reports/', views.reports_view, name='reports'),
    path('export/<str:report_type>/', views.export_report, name='export_report'),
]
