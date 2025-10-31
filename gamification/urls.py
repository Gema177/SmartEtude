from django.urls import path
from . import views

app_name = 'gamification'

urlpatterns = [
    path('dashboard/', views.gamification_dashboard_view, name='dashboard'),
    path('badges/', views.badges_view, name='badges'),
    path('achievements/', views.achievements_view, name='achievements'),
    path('challenges/', views.challenges_view, name='challenges'),
    path('challenges/<uuid:challenge_id>/', views.challenge_detail_view, name='challenge_detail'),
    path('leaderboard/', views.leaderboard_view, name='leaderboard'),
    path('rewards/', views.rewards_view, name='rewards'),
    path('profile/<int:user_id>/', views.user_gamification_view, name='user_profile'),
]
