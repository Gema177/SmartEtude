from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from core.models import Course, Quiz, Question
import uuid


class AIProcessingJob(models.Model):
    """Tâches de traitement IA"""
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('processing', 'En cours'),
        ('completed', 'Terminé'),
        ('failed', 'Échoué'),
        ('cancelled', 'Annulé'),
    ]
    
    JOB_TYPES = [
        ('text_extraction', 'Extraction de texte'),
        ('summarization', 'Résumé automatique'),
        ('quiz_generation', 'Génération de quiz'),
        ('concept_extraction', 'Extraction de concepts'),
        ('difficulty_analysis', 'Analyse de difficulté'),
        ('recommendation', 'Recommandations'),
        ('translation', 'Traduction'),
        ('sentiment_analysis', 'Analyse de sentiment'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job_type = models.CharField(max_length=30, choices=JOB_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Contexte du job
    course = models.ForeignKey(Course, on_delete=models.CASCADE, null=True, blank=True, related_name='ai_jobs')
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, null=True, blank=True, related_name='ai_jobs')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ai_jobs')
    
    # Paramètres et résultats
    input_data = models.JSONField(default=dict)  # Données d'entrée
    output_data = models.JSONField(default=dict)  # Résultats du traitement
    error_message = models.TextField(blank=True)
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    processing_time = models.DurationField(null=True, blank=True)
    
    # Configuration IA
    ai_model = models.CharField(max_length=100, default='gpt-3.5-turbo')
    ai_provider = models.CharField(max_length=50, default='openai')
    cost = models.DecimalField(max_digits=10, decimal_places=6, default=0.000000)  # Coût en USD
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'job_type']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['course', 'status']),
        ]
    
    def __str__(self):
        return f"{self.get_job_type_display()} - {self.status} - {self.created_at}"
    
    def start_processing(self):
        """Démarre le traitement du job"""
        self.status = 'processing'
        self.started_at = timezone.now()
        self.save()
    
    def complete_job(self, output_data, cost=0.0):
        """Marque le job comme terminé"""
        self.status = 'completed'
        self.output_data = output_data
        self.completed_at = timezone.now()
        self.cost = cost
        
        if self.started_at:
            self.processing_time = self.completed_at - self.started_at
        
        self.save()
    
    def fail_job(self, error_message):
        """Marque le job comme échoué"""
        self.status = 'failed'
        self.error_message = error_message
        self.completed_at = timezone.now()
        
        if self.started_at:
            self.processing_time = self.completed_at - self.started_at
        
        self.save()


class AIConfiguration(models.Model):
    """Configuration des modèles IA"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    
    # Configuration du modèle
    provider = models.CharField(max_length=50)  # openai, anthropic, local, etc.
    model_name = models.CharField(max_length=100)
    api_key = models.CharField(max_length=255, blank=True)
    api_endpoint = models.URLField(blank=True)
    
    # Paramètres
    max_tokens = models.PositiveIntegerField(default=2000)
    temperature = models.DecimalField(max_digits=3, decimal_places=2, default=0.70)
    top_p = models.DecimalField(max_digits=3, decimal_places=2, default=1.00)
    frequency_penalty = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    presence_penalty = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    
    # Limites et coûts
    rate_limit_per_minute = models.PositiveIntegerField(default=60)
    cost_per_1k_tokens = models.DecimalField(max_digits=10, decimal_places=6, default=0.002000)
    
    # Statut
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.provider})"
    
    def save(self, *args, **kwargs):
        # S'assurer qu'il n'y a qu'un seul modèle par défaut
        if self.is_default:
            AIConfiguration.objects.filter(is_default=True).update(is_default=False)
        super().save(*args, **kwargs)


class AIPromptTemplate(models.Model):
    """Templates de prompts pour l'IA"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    
    # Type de prompt
    PROMPT_TYPES = [
        ('summarization', 'Résumé'),
        ('quiz_generation', 'Génération de quiz'),
        ('concept_extraction', 'Extraction de concepts'),
        ('difficulty_analysis', 'Analyse de difficulté'),
        ('translation', 'Traduction'),
        ('explanation', 'Explication'),
        ('question_answering', 'Réponse à des questions'),
    ]
    
    prompt_type = models.CharField(max_length=30, choices=PROMPT_TYPES)
    
    # Contenu du prompt
    system_prompt = models.TextField(help_text="Prompt système (rôle de l'IA)")
    user_prompt_template = models.TextField(help_text="Template du prompt utilisateur avec variables {variable}")
    
    # Variables disponibles
    available_variables = models.JSONField(default=list, help_text="Liste des variables disponibles")
    
    # Configuration
    ai_configuration = models.ForeignKey(AIConfiguration, on_delete=models.SET_NULL, null=True, blank=True)
    max_tokens_override = models.PositiveIntegerField(null=True, blank=True)
    temperature_override = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.get_prompt_type_display()})"
    
    def render_prompt(self, **kwargs):
        """Rend le prompt avec les variables fournies"""
        try:
            return self.user_prompt_template.format(**kwargs)
        except KeyError as e:
            raise ValueError(f"Variable manquante dans le template: {e}")


class AIUsageLog(models.Model):
    """Log d'utilisation des services IA"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Contexte
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ai_usage_logs')
    ai_configuration = models.ForeignKey(AIConfiguration, on_delete=models.CASCADE, related_name='usage_logs')
    job = models.ForeignKey(AIProcessingJob, on_delete=models.CASCADE, null=True, blank=True, related_name='usage_logs')
    
    # Détails de l'utilisation
    tokens_used = models.PositiveIntegerField()
    cost = models.DecimalField(max_digits=10, decimal_places=6)
    response_time = models.DurationField()
    
    # Métadonnées
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['ai_configuration', 'timestamp']),
            models.Index(fields=['timestamp']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.ai_configuration.name} - {self.tokens_used} tokens"


class AITrainingData(models.Model):
    """Données d'entraînement pour améliorer les modèles"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Type de données
    DATA_TYPES = [
        ('text_sample', 'Échantillon de texte'),
        ('quiz_question', 'Question de quiz'),
        ('answer_feedback', 'Feedback de réponse'),
        ('user_correction', 'Correction utilisateur'),
        ('translation_pair', 'Paire de traduction'),
    ]
    
    data_type = models.CharField(max_length=30, choices=DATA_TYPES)
    
    # Contenu
    input_text = models.TextField()
    expected_output = models.TextField()
    actual_output = models.TextField(blank=True)
    
    # Métadonnées
    source = models.CharField(max_length=100, blank=True)  # Source des données
    quality_score = models.DecimalField(max_digits=3, decimal_places=2, default=1.00)
    is_verified = models.BooleanField(default=False)
    
    # Contexte
    course = models.ForeignKey(Course, on_delete=models.CASCADE, null=True, blank=True, related_name='ai_training_data')
    language = models.CharField(max_length=10, default='fr')
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_training_data')
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_data_type_display()} - {self.input_text[:50]}..."


class AIRecommendationEngine(models.Model):
    """Moteur de recommandations IA"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    
    # Type de recommandation
    RECOMMENDATION_TYPES = [
        ('course_similarity', 'Similarité de cours'),
        ('user_collaborative', 'Filtrage collaboratif'),
        ('content_based', 'Basé sur le contenu'),
        ('hybrid', 'Hybride'),
        ('learning_path', 'Parcours d\'apprentissage'),
    ]
    
    recommendation_type = models.CharField(max_length=30, choices=RECOMMENDATION_TYPES)
    
    # Configuration
    algorithm = models.CharField(max_length=100)  # Nom de l'algorithme
    parameters = models.JSONField(default=dict)  # Paramètres de l'algorithme
    
    # Performance
    accuracy_score = models.DecimalField(max_digits=5, decimal_places=4, default=0.0000)
    last_training = models.DateTimeField(null=True, blank=True)
    training_samples = models.PositiveIntegerField(default=0)
    
    # Statut
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.get_recommendation_type_display()})"
    
    def get_recommendations(self, user, context=None, limit=10):
        """Génère des recommandations pour un utilisateur"""
        # TODO: Implémenter la logique de recommandation selon le type
        if self.recommendation_type == 'course_similarity':
            return self._get_course_similarity_recommendations(user, context, limit)
        elif self.recommendation_type == 'user_collaborative':
            return self._get_collaborative_recommendations(user, context, limit)
        elif self.recommendation_type == 'content_based':
            return self._get_content_based_recommendations(user, context, limit)
        else:
            return []
    
    def _get_course_similarity_recommendations(self, user, context, limit):
        """Recommandations basées sur la similarité de cours"""
        # Logique de recommandation par similarité
        return []
    
    def _get_collaborative_recommendations(self, user, context, limit):
        """Recommandations basées sur le filtrage collaboratif"""
        # Logique de recommandation collaborative
        return []
    
    def _get_content_based_recommendations(self, user, context, limit):
        """Recommandations basées sur le contenu"""
        # Logique de recommandation basée sur le contenu
        return []
