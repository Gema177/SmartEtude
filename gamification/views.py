from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.http import JsonResponse
from django.db.models import Count, Q
from django.utils import timezone

from .models import Badge, Achievement, Challenge
from core.models import UserProfile


@login_required
def gamification_dashboard_view(request):
    """Vue du tableau de bord gamification"""
    return render(request, 'gamification/dashboard.html')


@login_required
def badges_view(request):
    """Vue des badges"""
    return render(request, 'gamification/badges.html')


@login_required
def achievements_view(request):
    """Vue des réalisations"""
    return render(request, 'gamification/achievements.html')


@login_required
def challenges_view(request):
    """Vue des défis"""
    return render(request, 'gamification/challenges.html')


@login_required
def leaderboard_view(request):
    """Vue du classement"""
    return render(request, 'gamification/leaderboard.html')


@login_required
def rewards_view(request):
    """Vue des récompenses"""
    return render(request, 'gamification/rewards.html')


@login_required
def user_gamification_view(request, user_id):
    """Vue du profil gamification d'un utilisateur"""
    return render(request, 'gamification/user_profile.html')


class GamificationDashboardView(LoginRequiredMixin, TemplateView):
    """Vue du tableau de bord gamification avec classe"""
    template_name = 'gamification/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Statistiques gamification
        try:
            profile = user.profile
            context['level'] = profile.level
            context['experience_points'] = profile.experience_points
            context['badges_count'] = profile.badges.count()
            context['achievements_count'] = profile.achievements.count()
        except UserProfile.DoesNotExist:
            context['level'] = 1
            context['experience_points'] = 0
            context['badges_count'] = 0
            context['achievements_count'] = 0
        
        return context


def gamification_api_data(request):
    """API pour récupérer les données gamification"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    try:
        profile = request.user.profile
        data = {
            'level': profile.level,
            'experience_points': profile.experience_points,
            'badges_count': profile.badges.count(),
            'achievements_count': profile.achievements.count(),
            'challenges_completed': profile.challenges_completed.count(),
        }
    except UserProfile.DoesNotExist:
        data = {
            'level': 1,
            'experience_points': 0,
            'badges_count': 0,
            'achievements_count': 0,
            'challenges_completed': 0,
        }
    
    return JsonResponse(data)


@login_required
def badge_detail_view(request, badge_id):
    """Vue de détail d'un badge"""
    return render(request, 'gamification/badge_detail.html')


@login_required
def achievement_detail_view(request, achievement_id):
    """Vue de détail d'une réalisation"""
    return render(request, 'gamification/achievement_detail.html')


@login_required
def challenge_detail_view(request, challenge_id):
    """Vue de détail d'un défi"""
    return render(request, 'gamification/challenge_detail.html')


@login_required
def leaderboard_detail_view(request):
    """Vue détaillée du classement"""
    return render(request, 'gamification/leaderboard_detail.html')


@login_required
def reward_detail_view(request, reward_id):
    """Vue de détail d'une récompense"""
    return render(request, 'gamification/reward_detail.html')


@login_required
def user_gamification_detail_view(request, user_id):
    """Vue détaillée du profil gamification d'un utilisateur"""
    return render(request, 'gamification/user_profile_detail.html')
