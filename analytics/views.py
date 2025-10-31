from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.http import JsonResponse
from django.db.models import Count, Avg, Q
from django.utils import timezone
from datetime import timedelta

from core.models import Course, Quiz, QuizAttempt, UserProfile


@login_required
def dashboard_view(request):
    """Vue du tableau de bord analytics"""
    return render(request, 'analytics/dashboard.html')


@login_required
def course_analytics_view(request, course_id):
    """Vue des analytics d'un cours"""
    return render(request, 'analytics/course_analytics.html')


@login_required
def user_analytics_view(request, user_id):
    """Vue des analytics d'un utilisateur"""
    return render(request, 'analytics/user_analytics.html')


@login_required
def system_analytics_view(request):
    """Vue des analytics système"""
    return render(request, 'analytics/system_analytics.html')


@login_required
def reports_view(request):
    """Vue des rapports"""
    return render(request, 'analytics/reports.html')


class AnalyticsDashboardView(LoginRequiredMixin, TemplateView):
    """Vue du tableau de bord analytics avec classe"""
    template_name = 'analytics/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Statistiques de base
        context['total_courses'] = Course.objects.filter(user=user).count()
        context['total_quizzes'] = Quiz.objects.filter(course__user=user).count()
        context['total_attempts'] = QuizAttempt.objects.filter(quiz__course__user=user).count()
        
        # Statistiques des 30 derniers jours
        thirty_days_ago = timezone.now() - timedelta(days=30)
        context['recent_attempts'] = QuizAttempt.objects.filter(
            quiz__course__user=user,
            created_at__gte=thirty_days_ago
        ).count()
        
        return context


def analytics_api_data(request):
    """API pour récupérer les données analytics"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    # Données pour les graphiques
    data = {
        'courses_created': Course.objects.filter(user=request.user).count(),
        'quizzes_taken': QuizAttempt.objects.filter(user=request.user).count(),
        'average_score': QuizAttempt.objects.filter(
            user=request.user, 
            is_completed=True
        ).aggregate(avg=Avg('score_percentage'))['avg'] or 0,
    }
    
    return JsonResponse(data)


@login_required
def export_report(request, report_type):
    """Vue d'export des rapports"""
    # TODO: Implémenter l'export des rapports
    return JsonResponse({'message': f'Export {report_type} not implemented yet'})
