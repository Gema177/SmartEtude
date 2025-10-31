from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from core.models import Course, Quiz, Question
import uuid


class Badge(models.Model):
    """Badges pour récompenser les utilisateurs"""
    BADGE_TYPES = [
        ('achievement', 'Réalisation'),
        ('milestone', 'Étape'),
        ('special', 'Spécial'),
        ('seasonal', 'Saisonnier'),
        ('challenge', 'Défi'),
    ]
    
    DIFFICULTY_LEVELS = [
        ('bronze', 'Bronze'),
        ('silver', 'Argent'),
        ('gold', 'Or'),
        ('platinum', 'Platine'),
        ('diamond', 'Diamant'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    badge_type = models.CharField(max_length=20, choices=BADGE_TYPES)
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_LEVELS)
    
    # Visuel
    icon = models.CharField(max_length=100, help_text="Classe CSS ou nom d'icône")
    color = models.CharField(max_length=7, default="#FFD700")  # Couleur hexadécimale
    image = models.ImageField(upload_to='badges/', blank=True, null=True)
    
    # Critères d'obtention
    criteria = models.JSONField(default=dict, help_text="Critères pour obtenir le badge")
    points_reward = models.PositiveIntegerField(default=0, help_text="Points d'expérience accordés")
    
    # Métadonnées
    is_active = models.BooleanField(default=True)
    is_hidden = models.BooleanField(default=False, help_text="Badge caché jusqu'à obtention")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['difficulty', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.get_difficulty_display()})"
    
    @property
    def rarity_percentage(self):
        """Calcule la rareté du badge en pourcentage"""
        total_users = User.objects.count()
        if total_users == 0:
            return 0
        
        earned_count = self.user_badges.count()
        return round((earned_count / total_users) * 100, 2)


class Achievement(models.Model):
    """Réalisations pour les utilisateurs"""
    ACHIEVEMENT_TYPES = [
        ('course_completion', 'Complétion de cours'),
        ('quiz_performance', 'Performance aux quiz'),
        ('streak', 'Série'),
        ('social', 'Social'),
        ('exploration', 'Exploration'),
        ('mastery', 'Maîtrise'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    achievement_type = models.CharField(max_length=30, choices=ACHIEVEMENT_TYPES)
    
    # Critères
    criteria = models.JSONField(default=dict, help_text="Critères pour obtenir l'achievement")
    threshold = models.PositiveIntegerField(default=1, help_text="Seuil à atteindre")
    
    # Récompenses
    experience_points = models.PositiveIntegerField(default=0)
    badge = models.ForeignKey(Badge, on_delete=models.SET_NULL, null=True, blank=True, related_name='achievements')
    
    # Visuel
    icon = models.CharField(max_length=100)
    color = models.CharField(max_length=7, default="#4CAF50")
    
    # Métadonnées
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['achievement_type', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.get_achievement_type_display()})"
    
    def check_achievement(self, user):
        """Vérifie si l'utilisateur a obtenu cet achievement"""
        from core.models import UserProfile
        
        try:
            profile = user.profile
        except UserProfile.DoesNotExist:
            return False
        
        # Vérifier selon le type d'achievement
        if self.achievement_type == 'course_completion':
            return profile.total_courses_completed >= self.threshold
        elif self.achievement_type == 'quiz_performance':
            return profile.total_quizzes_passed >= self.threshold
        elif self.achievement_type == 'streak':
            return profile.streak_days >= self.threshold
        elif self.achievement_type == 'mastery':
            return profile.average_quiz_score >= self.threshold
        
        return False


class UserBadge(models.Model):
    """Association utilisateur-badge"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_badges')
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE, related_name='user_badges')
    
    # Métadonnées
    earned_at = models.DateTimeField(auto_now_add=True)
    earned_in_context = models.CharField(max_length=100, blank=True, help_text="Contexte d'obtention")
    
    class Meta:
        unique_together = ['user', 'badge']
        ordering = ['-earned_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.badge.name}"
    
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        # Ajouter les points d'expérience si c'est un nouveau badge
        if is_new:
            profile = getattr(self.user, 'profile', None)
            if profile and self.badge.points_reward > 0:
                profile.add_experience(self.badge.points_reward)


class UserAchievement(models.Model):
    """Association utilisateur-achievement"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_achievements')
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE, related_name='user_achievements')
    
    # Métadonnées
    earned_at = models.DateTimeField(auto_now_add=True)
    progress = models.PositiveIntegerField(default=0, help_text="Progression actuelle")
    
    class Meta:
        unique_together = ['user', 'achievement']
        ordering = ['-earned_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.achievement.name}"
    
    def update_progress(self, new_progress):
        """Met à jour la progression et vérifie si l'achievement est obtenu"""
        self.progress = new_progress
        self.save()
        
        # Vérifier si l'achievement est obtenu
        if self.progress >= self.achievement.threshold:
            self._award_achievement()
    
    def _award_achievement(self):
        """Accorde l'achievement à l'utilisateur"""
        from core.models import UserProfile
        
        try:
            profile = self.user.profile
        except UserProfile.DoesNotExist:
            return
        
        # Ajouter les points d'expérience
        if self.achievement.experience_points > 0:
            profile.add_experience(self.achievement.experience_points)
        
        # Accorder le badge associé
        if self.achievement.badge:
            UserBadge.objects.get_or_create(
                user=self.user,
                badge=self.achievement.badge,
                defaults={'earned_in_context': f'Achievement: {self.achievement.name}'}
            )


class Challenge(models.Model):
    """Défis pour les utilisateurs"""
    CHALLENGE_TYPES = [
        ('daily', 'Quotidien'),
        ('weekly', 'Hebdomadaire'),
        ('monthly', 'Mensuel'),
        ('special', 'Spécial'),
        ('seasonal', 'Saisonnier'),
    ]
    
    DIFFICULTY_LEVELS = [
        ('easy', 'Facile'),
        ('medium', 'Moyen'),
        ('hard', 'Difficile'),
        ('expert', 'Expert'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    challenge_type = models.CharField(max_length=20, choices=CHALLENGE_TYPES)
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_LEVELS)
    
    # Critères et objectifs
    objectives = models.JSONField(default=dict, help_text="Objectifs du défi")
    requirements = models.JSONField(default=dict, help_text="Prérequis pour participer")
    
    # Récompenses
    experience_points = models.PositiveIntegerField(default=0)
    badges = models.ManyToManyField(Badge, blank=True, related_name='challenges')
    
    # Timing
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    max_participants = models.PositiveIntegerField(null=True, blank=True)
    
    class Meta:
        ordering = ['-start_date']
    
    def __str__(self):
        return f"{self.name} ({self.get_challenge_type_display()})"
    
    @property
    def is_current(self):
        """Vérifie si le défi est actuellement actif"""
        now = timezone.now()
        return self.start_date <= now <= self.end_date and self.is_active
    
    @property
    def participant_count(self):
        """Compte le nombre de participants"""
        return self.participants.count()
    
    def can_user_join(self, user):
        """Vérifie si un utilisateur peut rejoindre le défi"""
        if not self.is_current:
            return False
        
        if self.max_participants and self.participant_count >= self.max_participants:
            return False
        
        # Vérifier les prérequis
        for requirement_type, requirement_value in self.requirements.items():
            if not self._check_requirement(user, requirement_type, requirement_value):
                return False
        
        return True
    
    def _check_requirement(self, user, requirement_type, requirement_value):
        """Vérifie un prérequis spécifique"""
        from core.models import UserProfile
        
        try:
            profile = user.profile
        except UserProfile.DoesNotExist:
            return False
        
        if requirement_type == 'min_level':
            return profile.level >= requirement_value
        elif requirement_type == 'min_courses':
            return profile.total_courses_completed >= requirement_value
        elif requirement_type == 'min_quizzes':
            return profile.total_quizzes_passed >= requirement_value
        
        return False


class ChallengeParticipant(models.Model):
    """Participants aux défis"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    challenge = models.ForeignKey(Challenge, on_delete=models.CASCADE, related_name='participants')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='challenge_participations')
    
    # Progression
    progress = models.JSONField(default=dict, help_text="Progression dans le défi")
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Métadonnées
    joined_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['challenge', 'user']
        ordering = ['-joined_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.challenge.name}"
    
    def update_progress(self, objective_key, value):
        """Met à jour la progression pour un objectif"""
        if 'progress' not in self.progress:
            self.progress['progress'] = {}
        
        self.progress['progress'][objective_key] = value
        self.last_activity = timezone.now()
        self.save()
        
        # Vérifier si le défi est complété
        self._check_completion()
    
    def _check_completion(self):
        """Vérifie si le défi est complété"""
        if self.is_completed:
            return
        
        objectives = self.challenge.objectives
        progress = self.progress.get('progress', {})
        
        all_completed = True
        for objective_key, objective_value in objectives.items():
            current_progress = progress.get(objective_key, 0)
            if current_progress < objective_value:
                all_completed = False
                break
        
        if all_completed:
            self._complete_challenge()
    
    def _complete_challenge(self):
        """Marque le défi comme complété et accorde les récompenses"""
        self.is_completed = True
        self.completed_at = timezone.now()
        self.save()
        
        # Accorder les points d'expérience
        from core.models import UserProfile
        
        try:
            profile = self.user.profile
        except UserProfile.DoesNotExist:
            return
        
        if self.challenge.experience_points > 0:
            profile.add_experience(self.challenge.experience_points)
        
        # Accorder les badges
        for badge in self.challenge.badges.all():
            UserBadge.objects.get_or_create(
                user=self.user,
                badge=badge,
                defaults={'earned_in_context': f'Challenge: {self.challenge.name}'}
            )


class Leaderboard(models.Model):
    """Classements pour la gamification"""
    LEADERBOARD_TYPES = [
        ('global', 'Global'),
        ('weekly', 'Hebdomadaire'),
        ('monthly', 'Mensuel'),
        ('category', 'Par catégorie'),
        ('challenge', 'Par défi'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    leaderboard_type = models.CharField(max_length=20, choices=LEADERBOARD_TYPES)
    
    # Configuration
    metric = models.CharField(max_length=50, help_text="Métrique pour le classement")
    category = models.ForeignKey('core.Category', on_delete=models.CASCADE, null=True, blank=True)
    challenge = models.ForeignKey(Challenge, on_delete=models.CASCADE, null=True, blank=True)
    
    # Timing
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    max_entries = models.PositiveIntegerField(default=100)
    
    class Meta:
        ordering = ['-start_date']
        unique_together = ['leaderboard_type', 'metric', 'category', 'challenge']
    
    def __str__(self):
        return f"{self.name} ({self.get_leaderboard_type_display()})"
    
    def get_leaderboard_data(self):
        """Récupère les données du classement"""
        if self.leaderboard_type == 'global':
            return self._get_global_leaderboard()
        elif self.leaderboard_type == 'weekly':
            return self._get_weekly_leaderboard()
        elif self.leaderboard_type == 'monthly':
            return self._get_monthly_leaderboard()
        elif self.leaderboard_type == 'category':
            return self._get_category_leaderboard()
        elif self.leaderboard_type == 'challenge':
            return self._get_challenge_leaderboard()
        
        return []
    
    def _get_global_leaderboard(self):
        """Classement global par points d'expérience"""
        from core.models import UserProfile
        
        profiles = UserProfile.objects.select_related('user').order_by(
            '-experience_points', '-level'
        )[:self.max_entries]
        
        leaderboard_data = []
        for i, profile in enumerate(profiles, 1):
            leaderboard_data.append({
                'rank': i,
                'username': profile.user.username,
                'level': profile.level,
                'experience_points': profile.experience_points,
                'total_courses_completed': profile.total_courses_completed,
                'total_quizzes_passed': profile.total_quizzes_passed,
            })
        
        return leaderboard_data
    
    def _get_weekly_leaderboard(self):
        """Classement hebdomadaire"""
        # TODO: Implémenter le classement hebdomadaire
        return []
    
    def _get_monthly_leaderboard(self):
        """Classement mensuel"""
        # TODO: Implémenter le classement mensuel
        return []
    
    def _get_category_leaderboard(self):
        """Classement par catégorie"""
        # TODO: Implémenter le classement par catégorie
        return []
    
    def _get_challenge_leaderboard(self):
        """Classement par défi"""
        # TODO: Implémenter le classement par défi
        return []


class Reward(models.Model):
    """Système de récompenses"""
    REWARD_TYPES = [
        ('experience', 'Points d\'expérience'),
        ('badge', 'Badge'),
        ('achievement', 'Réalisation'),
        ('virtual_currency', 'Monnaie virtuelle'),
        ('unlock', 'Déblocage'),
        ('bonus', 'Bonus'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    reward_type = models.CharField(max_length=20, choices=REWARD_TYPES)
    
    # Valeur de la récompense
    value = models.JSONField(default=dict, help_text="Valeur de la récompense")
    
    # Conditions
    conditions = models.JSONField(default=dict, help_text="Conditions pour obtenir la récompense")
    
    # Métadonnées
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.get_reward_type_display()})"
    
    def can_user_claim(self, user):
        """Vérifie si un utilisateur peut réclamer cette récompense"""
        # TODO: Implémenter la logique de vérification des conditions
        return True
    
    def claim_for_user(self, user):
        """Accorde la récompense à l'utilisateur"""
        if not self.can_user_claim(user):
            return False
        
        # Accorder la récompense selon le type
        if self.reward_type == 'experience':
            return self._grant_experience(user)
        elif self.reward_type == 'badge':
            return self._grant_badge(user)
        elif self.reward_type == 'achievement':
            return self._grant_achievement(user)
        
        return False
    
    def _grant_experience(self, user):
        """Accorde des points d'expérience"""
        from core.models import UserProfile
        
        try:
            profile = user.profile
            experience_points = self.value.get('amount', 0)
            profile.add_experience(experience_points)
            return True
        except UserProfile.DoesNotExist:
            return False
    
    def _grant_badge(self, user):
        """Accorde un badge"""
        badge_id = self.value.get('badge_id')
        if not badge_id:
            return False
        
        try:
            badge = Badge.objects.get(id=badge_id)
            UserBadge.objects.get_or_create(
                user=user,
                badge=badge,
                defaults={'earned_in_context': f'Reward: {self.name}'}
            )
            return True
        except Badge.DoesNotExist:
            return False
    
    def _grant_achievement(self, user):
        """Accorde une réalisation"""
        achievement_id = self.value.get('achievement_id')
        if not achievement_id:
            return False
        
        try:
            achievement = Achievement.objects.get(id=achievement_id)
            UserAchievement.objects.get_or_create(
                user=user,
                achievement=achievement
            )
            return True
        except Achievement.DoesNotExist:
            return False
