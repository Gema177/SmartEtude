"""
Signals pour la gamification
Déclenche automatiquement la progression basée sur les scores de quiz
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from core.models import QuizAttempt, UserProfile
from .models import Badge, Achievement, UserBadge, UserAchievement
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=QuizAttempt)
def update_gamification_on_quiz_completion(sender, instance, created, **kwargs):
    """
    Met à jour la gamification lorsqu'un quiz est complété
    """
    # Ne traiter que les quiz complétés
    if not instance.is_completed or not instance.user:
        return
    
    try:
        profile, _ = UserProfile.objects.get_or_create(user=instance.user)
        
        # Calculer les points d'expérience basés sur le score
        experience_points = calculate_experience_from_score(
            instance.score_percentage,
            instance.quiz.difficulty,
            instance.passed
        )
        
        # Ajouter les points d'expérience
        level_up = profile.add_experience(experience_points)
        
        # Mettre à jour les statistiques du profil
        update_user_statistics(profile, instance)
        
        # Vérifier et attribuer les badges
        check_and_award_badges(profile, instance)
        
        # Vérifier et attribuer les achievements
        check_and_award_achievements(profile, instance)
        
        # Si niveau gagné, créer une notification
        if level_up:
            create_level_up_notification(instance.user, profile.level)
            
    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour de la gamification: {e}")


def calculate_experience_from_score(score_percentage, difficulty, passed):
    """
    Calcule les points d'expérience basés sur le score du quiz
    
    Formule:
    - Base: 10 points pour avoir complété le quiz
    - Bonus score: (score_percentage / 100) * 50 points
    - Bonus difficulté: easy=1x, medium=1.5x, hard=2x
    - Bonus réussite: +20 points si passé
    """
    base_points = 10
    score_bonus = (float(score_percentage) / 100) * 50
    
    # Multiplicateur de difficulté
    difficulty_multiplier = {
        'easy': 1.0,
        'medium': 1.5,
        'hard': 2.0
    }.get(difficulty, 1.0)
    
    # Bonus de réussite
    success_bonus = 20 if passed else 0
    
    # Calcul total
    total_points = (base_points + score_bonus) * difficulty_multiplier + success_bonus
    
    return int(total_points)


def update_user_statistics(profile, quiz_attempt):
    """
    Met à jour les statistiques de l'utilisateur
    """
    # Mettre à jour le nombre de quiz réussis
    if quiz_attempt.passed:
        profile.total_quizzes_passed += 1
    
    # Recalculer le score moyen
    all_attempts = QuizAttempt.objects.filter(
        user=profile.user,
        is_completed=True
    )
    
    if all_attempts.exists():
        total_score = sum(float(attempt.score_percentage) for attempt in all_attempts)
        profile.average_quiz_score = total_score / all_attempts.count()
    
    # Mettre à jour la date de dernière étude
    profile.last_study_date = timezone.now().date()
    
    # Mettre à jour le streak
    update_streak(profile)
    
    profile.save()


def update_streak(profile):
    """
    Met à jour le streak de jours consécutifs
    """
    today = timezone.now().date()
    
    if profile.last_study_date:
        # Si la dernière étude était hier, incrémenter le streak
        if profile.last_study_date == today - timezone.timedelta(days=1):
            profile.streak_days += 1
        # Si c'était aujourd'hui, ne rien faire
        elif profile.last_study_date == today:
            pass
        # Sinon, réinitialiser le streak
        else:
            profile.streak_days = 1
    else:
        profile.streak_days = 1


def check_and_award_badges(profile, quiz_attempt):
    """
    Vérifie et attribue les badges basés sur les performances
    """
    # Badge: Premier quiz complété
    if profile.total_quizzes_passed == 1:
        award_badge_by_name(profile.user, "Premier Pas")
    
    # Badge: Score parfait (100%)
    if float(quiz_attempt.score_percentage) == 100:
        award_badge_by_name(profile.user, "Score Parfait")
    
    # Badge: Score excellent (90%+)
    if float(quiz_attempt.score_percentage) >= 90:
        award_badge_by_name(profile.user, "Excellent")
    
    # Badge: 10 quiz réussis
    if profile.total_quizzes_passed == 10:
        award_badge_by_name(profile.user, "Débutant Confirmé")
    
    # Badge: 50 quiz réussis
    if profile.total_quizzes_passed == 50:
        award_badge_by_name(profile.user, "Expert")
    
    # Badge: 100 quiz réussis
    if profile.total_quizzes_passed == 100:
        award_badge_by_name(profile.user, "Maître")
    
    # Badge: Streak de 7 jours
    if profile.streak_days == 7:
        award_badge_by_name(profile.user, "Sérieux")
    
    # Badge: Streak de 30 jours
    if profile.streak_days == 30:
        award_badge_by_name(profile.user, "Déterminé")
    
    # Badge: Score moyen excellent (85%+)
    if profile.average_quiz_score >= 85:
        award_badge_by_name(profile.user, "Consistant")


def award_badge_by_name(user, badge_name):
    """
    Attribue un badge par son nom
    """
    try:
        badge = Badge.objects.get(name=badge_name, is_active=True)
        UserBadge.objects.get_or_create(
            user=user,
            badge=badge,
            defaults={'earned_in_context': f'Quiz completion'}
        )
    except Badge.DoesNotExist:
        # Le badge n'existe pas encore, on le créera via la migration
        pass


def check_and_award_achievements(profile, quiz_attempt):
    """
    Vérifie et attribue les achievements basés sur les performances
    """
    # Achievement: Performance aux quiz
    achievements = Achievement.objects.filter(
        achievement_type='quiz_performance',
        is_active=True
    )
    
    for achievement in achievements:
        # Vérifier si l'utilisateur a atteint le seuil
        if profile.total_quizzes_passed >= achievement.threshold:
            user_achievement, created = UserAchievement.objects.get_or_create(
                user=profile.user,
                achievement=achievement
            )
            
            if created:
                # Mettre à jour la progression
                user_achievement.progress = profile.total_quizzes_passed
                user_achievement.save()
            else:
                # Mettre à jour la progression
                user_achievement.update_progress(profile.total_quizzes_passed)
    
    # Achievement: Maîtrise (score moyen)
    mastery_achievements = Achievement.objects.filter(
        achievement_type='mastery',
        is_active=True
    )
    
    for achievement in mastery_achievements:
        if profile.average_quiz_score >= achievement.threshold:
            user_achievement, created = UserAchievement.objects.get_or_create(
                user=profile.user,
                achievement=achievement
            )
            
            if created:
                user_achievement.progress = int(profile.average_quiz_score)
                user_achievement.save()
            else:
                user_achievement.update_progress(int(profile.average_quiz_score))
    
    # Achievement: Streak
    streak_achievements = Achievement.objects.filter(
        achievement_type='streak',
        is_active=True
    )
    
    for achievement in streak_achievements:
        if profile.streak_days >= achievement.threshold:
            user_achievement, created = UserAchievement.objects.get_or_create(
                user=profile.user,
                achievement=achievement
            )
            
            if created:
                user_achievement.progress = profile.streak_days
                user_achievement.save()
            else:
                user_achievement.update_progress(profile.streak_days)


def create_level_up_notification(user, new_level):
    """
    Crée une notification pour un gain de niveau
    """
    try:
        from core.models import Notification
        Notification.objects.create(
            user=user,
            notification_type='level_up',
            title=f'Niveau {new_level} atteint!',
            message=f'Félicitations! Vous avez atteint le niveau {new_level}.',
            is_read=False
        )
    except Exception as e:
        logger.error(f"Erreur lors de la création de la notification: {e}")

