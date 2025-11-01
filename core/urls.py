from django.urls import path
from django.contrib.auth import views as auth_views
from . import views, views_ai, views_billing

urlpatterns = [
    # Pages principales
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(
        template_name='login_professional.html',
        redirect_authenticated_user=True
    ), name='login'),
    path('logout/', views.custom_logout, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('upload/', views.upload_course, name='upload'),
    path('create/', views.create_course, name='create_course'),
    path('accounts/profile/', views.profile, name='profile'),
    
    # Gestion des cours
    path('course/<uuid:course_id>/', views.course_detail, name='course_detail'),
    path('course/<uuid:course_id>/delete/', views.delete_course, name='delete_course'),
    
    # Quiz gaming mode
    path('quiz/<uuid:quiz_id>/', views.quiz_detail, name='quiz_detail'),
    path('quiz/<uuid:quiz_id>/game/', views.game_quiz, name='game_quiz'),
    path('quiz/<uuid:quiz_id>/game/debug/', views.debug_game_quiz, name='debug_game_quiz'),
    path('quiz/attempt/<uuid:attempt_id>/results/', views.quiz_results, name='quiz_results'),
    path('quiz/attempt/<uuid:attempt_id>/correction/', views.quiz_correction, name='quiz_correction'),
    
    # IA avec Phi-3 (modèle local)
    path('ai/dashboard/', views_ai.ai_dashboard, name='ai_dashboard'),
    path('ai/settings/', views_ai.ai_settings, name='ai_settings'),
    path('ai/course/<uuid:course_id>/summary/', views_ai.phi3_summary_view, name='ai_summary'),
    path('ai/course/<uuid:course_id>/quiz/', views_ai.phi3_quiz_view, name='ai_quiz'),
    path('ai/course/<uuid:course_id>/chat/', views_ai.phi3_chat_view, name='ai_chat'),
    path('ai/course/<uuid:course_id>/resume-result/', views_ai.ai_summary_result, name='ai_summary_result'),
    
    # APIs IA rapides
    path('api/ai/course/<uuid:course_id>/quick-summary/', views_ai.ai_quick_summary, name='ai_quick_summary'),
    path('api/ai/course/<uuid:course_id>/quick-quiz/', views_ai.ai_quick_quiz, name='ai_quick_quiz'),
    path('api/ai/test-connection/', views_ai.test_openai_connection, name='test_openai_connection'),
    path('api/ai/debug-config/', views_ai.debug_openai_config, name='debug_openai_config'),

    # Test et debug
    path('ai/test-quiz-parsing/', views_ai.test_quiz_parsing, name='test_quiz_parsing'),

    # Facturation / Abonnements
    path('billing/plans/', views_billing.billing_plans, name='billing_plans'),
    path('billing/checkout/<int:plan_id>/', views_billing.billing_checkout, name='billing_checkout'),
    path('billing/status/<int:payment_id>/', views_billing.billing_status, name='billing_status'),
    path('billing/webhooks/lygos/', views_billing.billing_webhook_lygos, name='billing_webhook_lygos'),
]
