from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.http import JsonResponse
from django.db.models import Count, Q
from django.utils import timezone

from .models import AIProcessingJob, AIConfiguration, AIPromptTemplate


@login_required
def ai_dashboard_view(request):
    """Vue du tableau de bord IA"""
    return render(request, 'ai_engine/dashboard.html')


@login_required
def job_management_view(request):
    """Vue de gestion des jobs IA"""
    return render(request, 'ai_engine/job_management.html')


@login_required
def configurations_view(request):
    """Vue des configurations IA"""
    return render(request, 'ai_engine/configurations.html')


@login_required
def prompts_view(request):
    """Vue des templates de prompts"""
    return render(request, 'ai_engine/prompts.html')


@login_required
def usage_logs_view(request):
    """Vue des logs d'utilisation IA"""
    return render(request, 'ai_engine/usage_logs.html')


@login_required
def training_data_view(request):
    """Vue des données d'entraînement"""
    return render(request, 'ai_engine/training_data.html')


@login_required
def recommendations_view(request):
    """Vue des recommandations IA"""
    return render(request, 'ai_engine/recommendations.html')


class AIDashboardView(LoginRequiredMixin, TemplateView):
    """Vue du tableau de bord IA avec classe"""
    template_name = 'ai_engine/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Statistiques IA
        context['total_jobs'] = AIProcessingJob.objects.filter(user=user).count()
        context['completed_jobs'] = AIProcessingJob.objects.filter(
            user=user, 
            status='completed'
        ).count()
        context['pending_jobs'] = AIProcessingJob.objects.filter(
            user=user, 
            status='pending'
        ).count()
        
        return context


def ai_api_data(request):
    """API pour récupérer les données IA"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    data = {
        'jobs_count': AIProcessingJob.objects.filter(user=request.user).count(),
        'configurations_count': AIConfiguration.objects.filter(is_active=True).count(),
        'prompts_count': AIPromptTemplate.objects.filter(is_active=True).count(),
    }
    
    return JsonResponse(data)


@login_required
def jobs_list_view(request):
    """Vue de liste des jobs IA"""
    return render(request, 'ai_engine/jobs_list.html')


@login_required
def job_detail_view(request, job_id):
    """Vue de détail d'un job IA"""
    return render(request, 'ai_engine/job_detail.html')


@login_required
def configurations_list_view(request):
    """Vue de liste des configurations IA"""
    return render(request, 'ai_engine/configurations_list.html')


@login_required
def configuration_detail_view(request, config_id):
    """Vue de détail d'une configuration IA"""
    return render(request, 'ai_engine/configuration_detail.html')


@login_required
def prompts_list_view(request):
    """Vue de liste des prompts IA"""
    return render(request, 'ai_engine/prompts_list.html')


@login_required
def prompt_detail_view(request, prompt_id):
    """Vue de détail d'un prompt IA"""
    return render(request, 'ai_engine/prompt_detail.html')


@login_required
def usage_logs_list_view(request):
    """Vue de liste des logs d'utilisation IA"""
    return render(request, 'ai_engine/usage_logs_list.html')


@login_required
def training_data_list_view(request):
    """Vue de liste des données d'entraînement IA"""
    return render(request, 'ai_engine/training_data_list.html')


@login_required
def recommendations_list_view(request):
    """Vue de liste des recommandations IA"""
    return render(request, 'ai_engine/recommendations_list.html')
