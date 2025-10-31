from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from core.models import Course, Quiz, Question
import uuid


class UserActivity(models.Model):
    """Suivi détaillé des activités utilisateur"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    
    # Type d'activité
    ACTIVITY_TYPES = [
        ('course_view', 'Visualisation de cours'),
        ('course_upload', 'Upload de cours'),
        ('quiz_start', 'Démarrage de quiz'),
        ('quiz_complete', 'Fin de quiz'),
        ('quiz_pass', 'Quiz réussi'),
        ('quiz_fail', 'Quiz échoué'),
        ('profile_update', 'Mise à jour de profil'),
        ('login', 'Connexion'),
        ('logout', 'Déconnexion'),
        ('search', 'Recherche'),
        ('download', 'Téléchargement'),
        ('share', 'Partage'),
        ('like', 'Like'),
        ('comment', 'Commentaire'),
    ]
    
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES)
    
    # Contexte de l'activité
    course = models.ForeignKey(Course, on_delete=models.CASCADE, null=True, blank=True, related_name='user_activities')
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, null=True, blank=True, related_name='user_activities')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, null=True, blank=True, related_name='user_activities')
    
    # Métadonnées
    timestamp = models.DateTimeField(auto_now_add=True)
    session_id = models.CharField(max_length=100, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    device_type = models.CharField(max_length=20, blank=True)  # mobile, desktop, tablet
    
    # Données contextuelles
    duration = models.DurationField(null=True, blank=True)  # Durée de l'activité
    metadata = models.JSONField(default=dict, blank=True)  # Données supplémentaires
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'activity_type', 'timestamp']),
            models.Index(fields=['activity_type', 'timestamp']),
            models.Index(fields=['course', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.get_activity_type_display()} - {self.timestamp}"


class CourseAnalytics(models.Model):
    """Analytics détaillés pour chaque cours"""
    course = models.OneToOneField(Course, on_delete=models.CASCADE, related_name='analytics')
    
    # Statistiques de base
    total_views = models.PositiveIntegerField(default=0)
    unique_visitors = models.PositiveIntegerField(default=0)
    total_time_spent = models.DurationField(default=timezone.timedelta)
    average_session_duration = models.DurationField(default=timezone.timedelta)
    
    # Engagement
    bounce_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)  # Pourcentage
    return_visitor_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    
    # Performance des quiz
    total_quiz_attempts = models.PositiveIntegerField(default=0)
    successful_attempts = models.PositiveIntegerField(default=0)
    average_quiz_score = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    completion_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    
    # Métadonnées
    last_updated = models.DateTimeField(auto_now=True)
    analytics_version = models.CharField(max_length=10, default='1.0')
    
    class Meta:
        verbose_name_plural = "Course Analytics"
    
    def __str__(self):
        return f"Analytics - {self.course.title}"
    
    def update_statistics(self):
        """Met à jour toutes les statistiques du cours"""
        # Calculer les vues totales
        self.total_views = UserActivity.objects.filter(
            course=self.course,
            activity_type='course_view'
        ).count()
        
        # Calculer les visiteurs uniques
        self.unique_visitors = UserActivity.objects.filter(
            course=self.course,
            activity_type='course_view'
        ).values('user').distinct().count()
        
        # Calculer le temps total passé
        activities = UserActivity.objects.filter(
            course=self.course,
            duration__isnull=False
        )
        total_duration = sum(
            (activity.duration for activity in activities),
            timezone.timedelta()
        )
        self.total_time_spent = total_duration
        
        # Calculer la durée moyenne des sessions
        if self.total_views > 0:
            self.average_session_duration = total_duration / self.total_views
        
        # Calculer les statistiques des quiz
        self.total_quiz_attempts = self.course.total_attempts
        self.successful_attempts = QuizAttempt.objects.filter(
            quiz__course=self.course,
            passed=True
        ).count()
        
        if self.total_quiz_attempts > 0:
            self.completion_rate = (self.successful_attempts / self.total_quiz_attempts) * 100
            self.average_quiz_score = self.course.quizzes.aggregate(
                avg=models.Avg('average_score')
            )['avg'] or 0
        
        self.save()


class QuizAnalytics(models.Model):
    """Analytics détaillés pour chaque quiz"""
    quiz = models.OneToOneField(Quiz, on_delete=models.CASCADE, related_name='analytics')
    
    # Statistiques de base
    total_attempts = models.PositiveIntegerField(default=0)
    unique_attempters = models.PositiveIntegerField(default=0)
    average_completion_time = models.DurationField(default=timezone.timedelta)
    
    # Performance
    success_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    average_score = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    score_distribution = models.JSONField(default=dict)  # Distribution des scores
    
    # Analyse des questions
    question_difficulty_analysis = models.JSONField(default=dict)  # Difficulté par question
    time_analysis = models.JSONField(default=dict)  # Temps par question
    
    # Métadonnées
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Quiz Analytics"
    
    def __str__(self):
        return f"Analytics - {self.quiz.title}"
    
    def update_statistics(self):
        """Met à jour toutes les statistiques du quiz"""
        attempts = self.quiz.attempts.all()
        
        if attempts.exists():
            self.total_attempts = attempts.count()
            self.unique_attempters = attempts.values('user').distinct().count()
            
            # Calculer le taux de succès
            successful = attempts.filter(passed=True).count()
            self.success_rate = (successful / self.total_attempts) * 100 if self.total_attempts > 0 else 0
            
            # Calculer le score moyen
            self.average_score = attempts.aggregate(avg=models.Avg('score_percentage'))['avg'] or 0
            
            # Analyser la distribution des scores
            score_ranges = {
                '0-20': 0, '21-40': 0, '41-60': 0, '61-80': 0, '81-100': 0
            }
            
            for attempt in attempts:
                score = attempt.score_percentage
                if score <= 20:
                    score_ranges['0-20'] += 1
                elif score <= 40:
                    score_ranges['21-40'] += 1
                elif score <= 60:
                    score_ranges['41-60'] += 1
                elif score <= 80:
                    score_ranges['61-80'] += 1
                else:
                    score_ranges['81-100'] += 1
            
            self.score_distribution = score_ranges
            
            # Analyser le temps de completion
            completed_attempts = attempts.filter(time_taken__isnull=False)
            if completed_attempts.exists():
                total_time = sum(
                    (attempt.time_taken for attempt in completed_attempts),
                    timezone.timedelta()
                )
                self.average_completion_time = total_time / completed_attempts.count()
        
        self.save()


class UserAnalytics(models.Model):
    """Analytics détaillés pour chaque utilisateur"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='analytics')
    
    # Statistiques d'apprentissage
    total_study_time = models.DurationField(default=timezone.timedelta)
    average_session_duration = models.DurationField(default=timezone.timedelta)
    total_sessions = models.PositiveIntegerField(default=0)
    
    # Performance
    courses_completed = models.PositiveIntegerField(default=0)
    quizzes_passed = models.PositiveIntegerField(default=0)
    average_quiz_score = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    
    # Engagement
    last_activity = models.DateTimeField(null=True, blank=True)
    activity_streak = models.PositiveIntegerField(default=0)  # Jours consécutifs
    total_activities = models.PositiveIntegerField(default=0)
    
    # Préférences d'apprentissage
    preferred_categories = models.JSONField(default=list)
    preferred_difficulty = models.CharField(max_length=20, default='intermediate')
    learning_patterns = models.JSONField(default=dict)  # Patterns d'apprentissage
    
    # Métadonnées
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "User Analytics"
    
    def __str__(self):
        return f"Analytics - {self.user.username}"
    
    def update_statistics(self):
        """Met à jour toutes les statistiques de l'utilisateur"""
        # Calculer le temps total d'étude
        sessions = self.user.study_sessions.all()
        if sessions.exists():
            self.total_study_time = sum(
                (session.duration for session in sessions if session.duration),
                timezone.timedelta()
            )
            self.total_sessions = sessions.count()
            
            if self.total_sessions > 0:
                self.average_session_duration = self.total_study_time / self.total_sessions
        
        # Calculer les performances
        self.courses_completed = self.user.courses.filter(status='published').count()
        self.quizzes_passed = self.user.quiz_attempts.filter(passed=True).count()
        
        # Calculer le score moyen
        attempts = self.user.quiz_attempts.all()
        if attempts.exists():
            self.average_quiz_score = attempts.aggregate(
                avg=models.Avg('score_percentage')
            )['avg'] or 0
        
        # Calculer l'activité récente
        recent_activity = UserActivity.objects.filter(
            user=self.user
        ).order_by('-timestamp').first()
        
        if recent_activity:
            self.last_activity = recent_activity.timestamp
        
        # Calculer le streak d'activité
        self.activity_streak = self._calculate_activity_streak()
        
        # Calculer le total d'activités
        self.total_activities = UserActivity.objects.filter(user=self.user).count()
        
        # Analyser les préférences
        self._analyze_preferences()
        
        self.save()
    
    def _calculate_activity_streak(self):
        """Calcule le nombre de jours consécutifs d'activité"""
        if not self.last_activity:
            return 0
        
        streak = 0
        current_date = timezone.now().date()
        check_date = self.last_activity.date()
        
        while check_date <= current_date:
            if UserActivity.objects.filter(
                user=self.user,
                timestamp__date=check_date
            ).exists():
                streak += 1
                check_date += timezone.timedelta(days=1)
            else:
                break
        
        return streak
    
    def _analyze_preferences(self):
        """Analyse les préférences d'apprentissage de l'utilisateur"""
        # Catégories préférées
        category_counts = {}
        for course in self.user.courses.all():
            if course.category:
                category_counts[course.category.name] = category_counts.get(course.category.name, 0) + 1
        
        self.preferred_categories = sorted(
            category_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        # Difficulté préférée
        difficulty_counts = {}
        for course in self.user.courses.all():
            difficulty_counts[course.difficulty] = difficulty_counts.get(course.difficulty, 0) + 1
        
        if difficulty_counts:
            self.preferred_difficulty = max(difficulty_counts, key=difficulty_counts.get)


class SystemAnalytics(models.Model):
    """Analytics système global"""
    date = models.DateField(unique=True)
    
    # Statistiques globales
    total_users = models.PositiveIntegerField(default=0)
    active_users = models.PositiveIntegerField(default=0)
    new_users = models.PositiveIntegerField(default=0)
    
    # Contenu
    total_courses = models.PositiveIntegerField(default=0)
    total_quizzes = models.PositiveIntegerField(default=0)
    total_quiz_attempts = models.PositiveIntegerField(default=0)
    
    # Performance système
    average_response_time = models.FloatField(default=0.0)  # en millisecondes
    error_rate = models.DecimalField(max_digits=5, decimal_places=4, default=0.0000)
    server_load = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-date']
        verbose_name_plural = "System Analytics"
    
    def __str__(self):
        return f"System Analytics - {self.date}"
    
    @classmethod
    def get_or_create_today(cls):
        """Récupère ou crée les analytics pour aujourd'hui"""
        today = timezone.now().date()
        analytics, created = cls.objects.get_or_create(date=today)
        
        if created:
            analytics.update_statistics()
        
        return analytics
    
    def update_statistics(self):
        """Met à jour toutes les statistiques système"""
        today = self.date
        
        # Statistiques utilisateurs
        self.total_users = User.objects.count()
        self.active_users = UserActivity.objects.filter(
            timestamp__date=today
        ).values('user').distinct().count()
        
        # Nouveaux utilisateurs aujourd'hui
        self.new_users = User.objects.filter(
            date_joined__date=today
        ).count()
        
        # Contenu
        self.total_courses = Course.objects.count()
        self.total_quizzes = Quiz.objects.count()
        self.total_quiz_attempts = QuizAttempt.objects.count()
        
        # TODO: Implémenter la collecte des métriques de performance système
        
        self.save()


class LearningPathAnalytics(models.Model):
    """Analytics pour les parcours d'apprentissage"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='learning_paths')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='learning_paths')
    
    # Progression
    progress_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    time_spent = models.DurationField(default=timezone.timedelta)
    quizzes_completed = models.PositiveIntegerField(default=0)
    
    # Difficulté perçue
    difficulty_rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True, blank=True
    )
    
    # Recommandations
    next_recommended_course = models.ForeignKey(
        Course, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='recommended_from'
    )
    
    # Métadonnées
    started_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['user', 'course']
        ordering = ['-last_activity']
    
    def __str__(self):
        return f"{self.user.username} - {self.course.title} ({self.progress_percentage}%)"
    
    def update_progress(self):
        """Met à jour la progression du parcours d'apprentissage"""
        # Calculer le pourcentage de progression
        total_quizzes = self.course.quizzes.count()
        if total_quizzes > 0:
            self.progress_percentage = (self.quizzes_completed / total_quizzes) * 100
        
        # Marquer comme terminé si 100%
        if self.progress_percentage >= 100 and not self.completed_at:
            self.completed_at = timezone.now()
        
        self.save()
