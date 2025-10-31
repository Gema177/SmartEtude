"""
Modèles de données pour SmartEtude

Ce module contient tous les modèles Django nécessaires pour :
- Gestion des cours et documents
- Système de quiz et questions
- Suivi des tentatives et performances
- Système de catégories et tags
- Métadonnées et analytics

Auteur: [Votre Nom]
Date: 2024
Version: 1.0.0
"""

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.urls import reverse
import uuid


class Category(models.Model):
    """
    Catégorie de cours pour l'organisation et la navigation
    
    Permet de classer les cours par domaine, matière ou thématique
    avec un système de couleurs et d'icônes pour une meilleure UX.
    """
    
    name = models.CharField(
        max_length=100, 
        unique=True,
        verbose_name="Nom de la catégorie"
    )
    description = models.TextField(
        blank=True,
        verbose_name="Description",
        help_text="Description détaillée de la catégorie"
    )
    color = models.CharField(
        max_length=7, 
        default="#3B82F6",
        verbose_name="Couleur",
        help_text="Couleur hexadécimale pour l'affichage"
    )
    icon = models.CharField(
        max_length=50, 
        default="book",
        verbose_name="Icône",
        help_text="Nom de l'icône FontAwesome"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date de création"
    )
    
    class Meta:
        verbose_name = "Catégorie"
        verbose_name_plural = "Catégories"
        ordering = ['name']
        db_table = 'core_category'
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        """Retourne l'URL de la catégorie"""
        return reverse('category_detail', kwargs={'pk': self.pk})
    
    @property
    def course_count(self):
        """Retourne le nombre de cours dans cette catégorie"""
        return self.courses.count()


class Tag(models.Model):
    """
    Tags pour organiser et rechercher les cours
    
    Système de tags flexibles permettant une classification
    fine et une recherche avancée des contenus.
    """
    
    name = models.CharField(
        max_length=50, 
        unique=True,
        verbose_name="Nom du tag"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date de création"
    )
    
    class Meta:
        verbose_name = "Tag"
        verbose_name_plural = "Tags"
        ordering = ['name']
        db_table = 'core_tag'
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        """Retourne l'URL du tag"""
        return reverse('tag_detail', kwargs={'pk': self.pk})


class Course(models.Model):
    """
    Modèle de cours amélioré avec IA et analytics
    
    Représente un cours complet avec :
    - Gestion des fichiers multi-format
    - Extraction automatique de texte
    - Traitement IA pour résumés et concepts clés
    - Système de quiz intégré
    - Analytics et métriques d'engagement
    """
    
    # Choix pour les champs à sélection
    DIFFICULTY_CHOICES = [
        ('beginner', 'Débutant'),
        ('intermediate', 'Intermédiaire'),
        ('advanced', 'Avancé'),
        ('expert', 'Expert'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Brouillon'),
        ('published', 'Publié'),
        ('archived', 'Archivé'),
    ]
    
    # =====================================================================
    # INFORMATIONS DE BASE
    # =====================================================================
    
    id = models.UUIDField(
        primary_key=True, 
        default=uuid.uuid4, 
        editable=False
    )
    title = models.CharField(
        max_length=255,
        verbose_name="Titre du cours"
    )
    slug = models.SlugField(
        max_length=255, 
        unique=True, 
        blank=True,
        verbose_name="Slug URL"
    )
    description = models.TextField(
        blank=True, 
        verbose_name="Description",
        help_text="Description détaillée du cours"
    )
    short_description = models.CharField(
        max_length=200, 
        blank=True,
        verbose_name="Description courte"
    )
    
    # =====================================================================
    # MÉTADONNÉES ET CLASSIFICATION
    # =====================================================================
    
    category = models.ForeignKey(
        Category, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='courses',
        verbose_name="Catégorie"
    )
    tags = models.ManyToManyField(
        Tag, 
        blank=True, 
        related_name='courses',
        verbose_name="Tags"
    )
    difficulty = models.CharField(
        max_length=20, 
        choices=DIFFICULTY_CHOICES, 
        default='intermediate',
        verbose_name="Niveau de difficulté"
    )
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='draft',
        verbose_name="Statut"
    )
    
    # =====================================================================
    # FICHIERS ET CONTENU
    # =====================================================================
    
    file = models.FileField(
        upload_to='courses/',
        verbose_name="Document source",
        help_text="Document source (PDF, DOCX, TXT)"
    )
    thumbnail = models.ImageField(
        upload_to='course_thumbnails/', 
        blank=True, 
        null=True,
        verbose_name="Miniature"
    )
    extracted_text = models.TextField(
        blank=True,
        verbose_name="Texte extrait"
    )
    summary = models.TextField(
        blank=True,
        verbose_name="Résumé IA"
    )
    ai_summary = models.JSONField(
        blank=True, 
        null=True,
        verbose_name="Résumé IA structuré",
        help_text="Résumé généré par ChatGPT avec structure et métadonnées"
    )
    key_concepts = models.JSONField(
        default=list, 
        blank=True,
        verbose_name="Concepts clés",
        help_text="Concepts clés extraits par l'IA"
    )
    
    # =====================================================================
    # RELATIONS ET PERMISSIONS
    # =====================================================================
    
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='courses', 
        null=True, 
        blank=True,
        verbose_name="Créateur"
    )
    collaborators = models.ManyToManyField(
        User, 
        blank=True, 
        related_name='collaborated_courses',
        verbose_name="Collaborateurs"
    )
    is_public = models.BooleanField(
        default=False,
        verbose_name="Public",
        help_text="Rendre ce cours public"
    )
    is_featured = models.BooleanField(
        default=False,
        verbose_name="Mis en avant",
        help_text="Cours mis en avant"
    )
    
    # =====================================================================
    # STATISTIQUES ET ENGAGEMENT
    # =====================================================================
    
    view_count = models.PositiveIntegerField(
        default=0,
        verbose_name="Nombre de vues"
    )
    like_count = models.PositiveIntegerField(
        default=0,
        verbose_name="Nombre de likes"
    )
    share_count = models.PositiveIntegerField(
        default=0,
        verbose_name="Nombre de partages"
    )
    rating = models.DecimalField(
        max_digits=3, 
        decimal_places=2, 
        default=0.00, 
        validators=[MinValueValidator(0), MaxValueValidator(5)],
        verbose_name="Note moyenne"
    )
    rating_count = models.PositiveIntegerField(
        default=0,
        verbose_name="Nombre de notes"
    )
    
    # =====================================================================
    # MÉTADONNÉES TEMPORELLES
    # =====================================================================
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date de création"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Date de modification"
    )
    published_at = models.DateTimeField(
        null=True, 
        blank=True,
        verbose_name="Date de publication"
    )
    
    # =====================================================================
    # IA ET ANALYSE
    # =====================================================================
    
    ai_processed = models.BooleanField(
        default=False,
        verbose_name="Traité par l'IA"
    )
    processing_status = models.CharField(
        max_length=20, 
        default='pending',
        verbose_name="Statut du traitement"
    )
    last_ai_update = models.DateTimeField(
        null=True, 
        blank=True,
        verbose_name="Dernière mise à jour IA"
    )
    
    class Meta:
        verbose_name = "Cours"
        verbose_name_plural = "Cours"
        ordering = ['-created_at']
        db_table = 'core_course'
        indexes = [
            models.Index(fields=['status', 'is_public']),
            models.Index(fields=['difficulty', 'category']),
            models.Index(fields=['rating', 'view_count']),
            models.Index(fields=['created_at']),
            models.Index(fields=['user']),
        ]
    
    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        """Retourne l'URL du cours"""
        return reverse('course_detail', kwargs={'pk': self.pk})
    
    def save(self, *args, **kwargs):
        """Logique personnalisée lors de la sauvegarde"""
        if not self.slug:
            self.slug = f"{self.title.lower().replace(' ', '-')}-{self.id}"
        if self.status == 'published' and not self.published_at:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)
    
    @property
    def quiz_count(self):
        """Retourne le nombre de quiz associés au cours"""
        return self.quizzes.count()
    
    @property
    def total_attempts(self):
        """Retourne le nombre total de tentatives de quiz"""
        return QuizAttempt.objects.filter(quiz__course=self).count()
    
    @property
    def completion_rate(self):
        """Calcule le taux de réussite du cours"""
        attempts = self.total_attempts
        if attempts == 0:
            return 0
        successful_attempts = QuizAttempt.objects.filter(
            quiz__course=self, 
            score__gte=models.F('total_questions') * 0.7
        ).count()
        return round((successful_attempts / attempts) * 100, 1)
    
    @property
    def estimated_duration(self):
        """Durée estimée en minutes basée sur la longueur du texte"""
        if not self.extracted_text:
            return 0
        word_count = len(self.extracted_text.split())
        return max(5, word_count // 200)  # 200 mots par minute en moyenne


class Quiz(models.Model):
    """Quiz amélioré avec système de difficulté et timing"""
    DIFFICULTY_CHOICES = [
        ('easy', 'Facile'),
        ('medium', 'Moyen'),
        ('hard', 'Difficile'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='quizzes')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='medium')
    
    # Configuration du quiz
    time_limit = models.PositiveIntegerField(default=0, help_text="Limite de temps en minutes (0 = illimité)")
    passing_score = models.PositiveIntegerField(default=70, help_text="Score minimum pour réussir (%)")
    max_attempts = models.PositiveIntegerField(default=3, help_text="Nombre maximum de tentatives")
    shuffle_questions = models.BooleanField(default=True)
    show_results_immediately = models.BooleanField(default=False)
    
    # Statistiques
    total_attempts = models.PositiveIntegerField(default=0)
    average_score = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    success_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Quizzes"
    
    def __str__(self):
        return f"{self.course.title} - {self.title}"
    
    def update_statistics(self):
        """Met à jour les statistiques du quiz"""
        attempts = self.attempts.all()
        if attempts.exists():
            self.total_attempts = attempts.count()
            self.average_score = attempts.aggregate(avg=models.Avg('score_percentage'))['avg'] or 0
            self.success_rate = attempts.filter(score_percentage__gte=self.passing_score).count() / self.total_attempts * 100
            self.save(update_fields=['total_attempts', 'average_score', 'success_rate'])


class Question(models.Model):
    """Question améliorée avec support multi-format et explications"""
    Q_TYPE_CHOICES = [
        ('true_false', 'Vrai/Faux'),
        ('multiple_choice', 'QCM'),
        ('fill_blank', 'Question à trous'),
        ('matching', 'Association'),
        ('ordering', 'Ordre'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    question_type = models.CharField(max_length=20, choices=Q_TYPE_CHOICES)
    question_text = models.TextField()
    
    # Réponses et options
    correct_answer = models.CharField(max_length=500)
    options = models.JSONField(default=list, blank=True)  # Pour QCM: ['Option A', 'Option B', ...]
    correct_options = models.JSONField(default=list, blank=True)  # Pour questions multi-réponses
    
    # Explications et feedback
    explanation = models.TextField(blank=True, help_text="Explication de la réponse correcte")
    hint = models.CharField(max_length=200, blank=True, help_text="Indice pour l'utilisateur")
    
    # Métadonnées
    points = models.PositiveIntegerField(default=1, help_text="Points attribués pour cette question")
    difficulty = models.CharField(max_length=20, choices=Quiz.DIFFICULTY_CHOICES, default='medium')
    order = models.PositiveIntegerField(default=0, help_text="Ordre d'affichage")
    
    # Statistiques
    times_answered = models.PositiveIntegerField(default=0)
    times_correct = models.PositiveIntegerField(default=0)
    average_time = models.DurationField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order', 'created_at']
    
    def __str__(self):
        return f"{self.quiz.title} - {self.question_text[:50]}..."
    
    @property
    def success_rate(self):
        if self.times_answered == 0:
            return 0
        return round((self.times_correct / self.times_answered) * 100, 1)


class QuizAttempt(models.Model):
    """Tentative de quiz améliorée avec analytics détaillés"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='attempts')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quiz_attempts', null=True, blank=True)
    user_name = models.CharField(max_length=100, default='Anonyme')
    
    # Réponses et scoring
    answers = models.JSONField(default=dict)  # {question_id: answer}
    score = models.IntegerField(default=0)
    total_questions = models.IntegerField(default=0)
    score_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    
    # Timing et performance
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    time_taken = models.DurationField(null=True, blank=True)
    
    # Métadonnées
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    is_completed = models.BooleanField(default=False)
    passed = models.BooleanField(default=False)
    
    # Analytics détaillés
    question_times = models.JSONField(default=dict)  # {question_id: time_spent}
    hints_used = models.JSONField(default=list)  # Liste des indices utilisés
    skipped_questions = models.JSONField(default=list)  # Questions sautées
    
    class Meta:
        ordering = ['-completed_at', '-started_at']
    
    def __str__(self):
        return f"{self.user_name} - {self.quiz.title} ({self.score}/{self.total_questions})"
    
    def save(self, *args, **kwargs):
        if self.total_questions > 0:
            self.score_percentage = round((self.score / self.total_questions) * 100, 2)
            self.passed = self.score_percentage >= self.quiz.passing_score
        super().save(*args, **kwargs)
    
    @property
    def duration_minutes(self):
        if self.time_taken:
            return self.time_taken.total_seconds() / 60
        return 0


class UserProfile(models.Model):
    """Profil utilisateur étendu avec gamification et analytics"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # Informations personnelles
    bio = models.TextField(blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    date_of_birth = models.DateField(null=True, blank=True)
    location = models.CharField(max_length=100, blank=True)
    
    # Préférences d'apprentissage
    preferred_difficulty = models.CharField(max_length=20, choices=Course.DIFFICULTY_CHOICES, default='intermediate')
    preferred_categories = models.ManyToManyField(Category, blank=True)
    learning_goals = models.JSONField(default=list, blank=True)
    
    # Statistiques et progression
    total_courses_completed = models.PositiveIntegerField(default=0)
    total_quizzes_passed = models.PositiveIntegerField(default=0)
    average_quiz_score = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    total_study_time = models.DurationField(default=timezone.timedelta)
    streak_days = models.PositiveIntegerField(default=0)
    last_study_date = models.DateField(null=True, blank=True)
    
    # Gamification
    experience_points = models.PositiveIntegerField(default=0)
    level = models.PositiveIntegerField(default=1)
    badges = models.JSONField(default=list, blank=True)
    achievements = models.JSONField(default=list, blank=True)
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Profil de {self.user.username}"
    
    def calculate_level(self):
        """Calcule le niveau basé sur les points d'expérience"""
        import math
        self.level = max(1, int(math.sqrt(self.experience_points / 100)) + 1)
        return self.level
    
    def add_experience(self, points):
        """Ajoute des points d'expérience et met à jour le niveau"""
        self.experience_points += points
        old_level = self.level
        self.level = self.calculate_level()
        self.save()
        
        # Vérifier si l'utilisateur a gagné un niveau
        if self.level > old_level:
            return True  # Niveau gagné
        return False


class StudySession(models.Model):
    """Session d'étude pour le suivi du temps d'apprentissage"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='study_sessions')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='study_sessions')
    
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    duration = models.DurationField(null=True, blank=True)
    
    # Activités pendant la session
    pages_viewed = models.PositiveIntegerField(default=0)
    quizzes_taken = models.PositiveIntegerField(default=0)
    notes_taken = models.TextField(blank=True)
    
    # Métadonnées
    device_info = models.JSONField(default=dict, blank=True)
    location = models.CharField(max_length=100, blank=True)
    
    class Meta:
        ordering = ['-started_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.course.title} ({self.started_at.date()})"
    
    def end_session(self):
        """Termine la session et calcule la durée"""
        self.ended_at = timezone.now()
        if self.started_at:
            self.duration = self.ended_at - self.started_at
        self.save()
        
        # Mettre à jour le profil utilisateur
        if self.duration:
            profile = self.user.profile
            profile.total_study_time += self.duration
            profile.last_study_date = self.started_at.date()
            profile.save()


class Notification(models.Model):
    """Système de notifications pour l'engagement utilisateur"""
    NOTIFICATION_TYPES = [
        ('achievement', 'Réalisation'),
        ('level_up', 'Niveau gagné'),
        ('quiz_reminder', 'Rappel de quiz'),
        ('course_recommendation', 'Recommandation de cours'),
        ('streak_reminder', 'Rappel de série'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    
    # Métadonnées
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    # Données contextuelles
    related_object_id = models.UUIDField(null=True, blank=True)
    related_object_type = models.CharField(max_length=50, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.title}"
    
    def mark_as_read(self):
        """Marque la notification comme lue"""
        self.is_read = True
        self.read_at = timezone.now()
        self.save()


# =============================================================================
# ABONNEMENTS & PAIEMENTS (LYGOS)
# =============================================================================


class BillingPlan(models.Model):
    """Offre d'abonnement (ex: mensuel, annuel)"""
    INTERVAL_CHOICES = [
        ("month", "Mensuel"),
        ("year", "Annuel"),
    ]

    name = models.CharField(max_length=100, unique=True)
    price = models.PositiveIntegerField(help_text="Montant en XAF")
    currency = models.CharField(max_length=10, default="XAF")
    interval = models.CharField(max_length=10, choices=INTERVAL_CHOICES)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "billing_plan"
        ordering = ["price"]

    def __str__(self):
        return f"{self.name} ({self.price} {self.currency}/{self.interval})"


class Subscription(models.Model):
    """Abonnement utilisateur à un plan"""
    STATUS_CHOICES = [
        ("pending", "En attente"),
        ("active", "Actif"),
        ("cancelled", "Annulé"),
        ("expired", "Expiré"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="subscriptions")
    plan = models.ForeignKey(BillingPlan, on_delete=models.PROTECT, related_name="subscriptions")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    started_at = models.DateTimeField(null=True, blank=True)
    current_period_end = models.DateTimeField(null=True, blank=True)
    cancel_at_period_end = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "subscription"
        indexes = [models.Index(fields=["user", "status"])]

    def __str__(self):
        return f"Subscription({self.user.username}, {self.plan.name}, {self.status})"

    @property
    def is_active(self) -> bool:
        return self.status == "active" and (self.current_period_end is None or self.current_period_end > timezone.now())


class Payment(models.Model):
    """Paiement lié à un abonnement (Mobile Money via Lygos)"""
    STATUS_CHOICES = [
        ("pending", "En attente"),
        ("succeeded", "Réussi"),
        ("failed", "Échoué"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="payments")
    subscription = models.ForeignKey(Subscription, on_delete=models.SET_NULL, null=True, blank=True, related_name="payments")
    provider = models.CharField(max_length=20, default="lygos")
    external_id = models.CharField(max_length=100, unique=True, blank=True, null=True, help_text="ID côté Lygos (payin_id)")
    operator = models.CharField(max_length=50, blank=True, help_text="Ex: MTN, AIRTEL_CONGO")
    amount = models.PositiveIntegerField(help_text="Montant en XAF")
    currency = models.CharField(max_length=10, default="XAF")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    raw = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "payment"
        indexes = [models.Index(fields=["user", "status"])]

    def __str__(self):
        return f"Payment({self.user.username}, {self.amount}{self.currency}, {self.status})"
