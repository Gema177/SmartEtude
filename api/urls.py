from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from . import views

# Configuration du routeur DRF
router = DefaultRouter()
router.register(r'categories', views.CategoryViewSet)
router.register(r'tags', views.TagViewSet)
router.register(r'courses', views.CourseViewSet, basename='course')
router.register(r'quizzes', views.QuizViewSet, basename='quiz')
router.register(r'quiz-attempts', views.QuizAttemptViewSet, basename='quiz-attempt')
router.register(r'user-profiles', views.UserProfileViewSet, basename='user-profile')
router.register(r'study-sessions', views.StudySessionViewSet, basename='study-session')
router.register(r'notifications', views.NotificationViewSet, basename='notification')
router.register(r'search', views.SearchViewSet, basename='search')

# URLs de l'API
urlpatterns = [
    # Routes du routeur DRF
    path('', include(router.urls)),
    
    # Authentification JWT
    path('auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    # Routes personnalisées
    path('auth/register/', views.UserRegistrationView.as_view(), name='user-register'),
    path('auth/profile/', views.UserProfileView.as_view(), name='user-profile'),
    
    # Routes d'analytics
    path('analytics/dashboard/', views.DashboardAnalyticsView.as_view(), name='dashboard-analytics'),
    path('analytics/courses/<uuid:course_id>/', views.CourseAnalyticsView.as_view(), name='course-analytics'),
    path('analytics/users/<int:user_id>/', views.UserAnalyticsView.as_view(), name='user-analytics'),
    
    # Routes de recommandations
    path('recommendations/courses/', views.CourseRecommendationsView.as_view(), name='course-recommendations'),
    path('recommendations/quizzes/', views.QuizRecommendationsView.as_view(), name='quiz-recommendations'),
    
    # Routes de gamification
    path('gamification/leaderboard/', views.LeaderboardView.as_view(), name='leaderboard'),
    path('gamification/achievements/', views.AchievementsView.as_view(), name='achievements'),
    path('gamification/badges/', views.BadgesView.as_view(), name='badges'),
    
    # Routes d'export
    path('export/courses/<uuid:course_id>/pdf/', views.ExportCoursePDFView.as_view(), name='export-course-pdf'),
    path('export/quiz-results/<uuid:attempt_id>/pdf/', views.ExportQuizResultsPDFView.as_view(), name='export-quiz-pdf'),
    
    # Routes de webhooks
    path('webhooks/ai-processing/', views.AIProcessingWebhookView.as_view(), name='ai-processing-webhook'),
    path('webhooks/analytics/', views.AnalyticsWebhookView.as_view(), name='analytics-webhook'),
]

# Importer les vues depuis le fichier views.py
from . import views
