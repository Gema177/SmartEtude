from django.urls import path
from . import views

app_name = 'ai_engine'

urlpatterns = [
    path('dashboard/', views.ai_dashboard_view, name='dashboard'),
    path('jobs/', views.jobs_list_view, name='jobs_list'),
    path('jobs/<uuid:job_id>/', views.job_detail_view, name='job_detail'),
    path('configurations/', views.configurations_view, name='configurations'),
    path('prompts/', views.prompts_view, name='prompts'),
    path('usage/', views.usage_logs_view, name='usage_logs'),
    path('training/', views.training_data_view, name='training_data'),
    path('recommendations/', views.recommendations_view, name='recommendations'),
]
