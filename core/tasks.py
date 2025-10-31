"""
Tâches Celery pour le traitement asynchrone des cours
"""

from celery import shared_task
from django.core.files.base import ContentFile
from django.utils import timezone
from .models import Course, Quiz, Question
from .ai_enhanced import get_ai_summary, get_ai_quiz
from ai_engine.models import AIProcessingJob
import logging

logger = logging.getLogger(__name__)

@shared_task(bind=True)
def process_course_async(self, course_id):
    """
    Tâche asynchrone pour traiter un cours uploadé
    """
    try:
        course = Course.objects.get(id=course_id)
        
        # Créer un job de traitement IA
        job = AIProcessingJob.objects.create(
            job_type='text_extraction',
            course=course,
            user=course.user,
            status='processing'
        )
        job.start_processing()
        
        # 1. Prétraitement du texte
        processed_text = preprocess_text(course.extracted_text)
        course.extracted_text = processed_text
        
        # 2. Génération du résumé
        summary_job = generate_summary_async.delay(course_id)
        
        # 3. Génération des concepts clés
        concepts_job = extract_key_concepts_async.delay(course_id)
        
        # 4. Génération du quiz
        quiz_job = generate_quiz_async.delay(course_id)
        
        # Marquer le cours comme traité
        course.ai_processed = True
        course.processing_status = 'completed'
        course.last_ai_update = timezone.now()
        course.save()
        
        # Marquer le job comme terminé
        job.complete_job({
            'summary_job_id': summary_job.id,
            'concepts_job_id': concepts_job.id,
            'quiz_job_id': quiz_job.id
        })
        
        logger.info(f"Cours {course_id} traité avec succès")
        return f"Cours {course_id} traité avec succès"
        
    except Exception as e:
        logger.error(f"Erreur lors du traitement du cours {course_id}: {str(e)}")
        if 'job' in locals():
            job.fail_job(str(e))
        raise

@shared_task
def preprocess_text(text):
    """
    Prétraitement du texte : nettoyage, segmentation, extraction de phrases clés
    """
    import re
    import nltk
    from nltk.tokenize import sent_tokenize, word_tokenize
    from nltk.corpus import stopwords
    
    try:
        # Télécharger les ressources NLTK si nécessaire
        nltk.download('punkt', quiet=True)
        nltk.download('stopwords', quiet=True)
        
        # Nettoyage du texte
        text = re.sub(r'\s+', ' ', text)  # Normaliser les espaces
        text = re.sub(r'[^\w\s\.\,\!\?]', '', text)  # Supprimer caractères spéciaux
        
        # Segmentation en phrases
        sentences = sent_tokenize(text)
        
        # Extraction des mots clés (mots les plus fréquents)
        words = word_tokenize(text.lower())
        stop_words = set(stopwords.words('french'))
        filtered_words = [word for word in words if word not in stop_words and len(word) > 3]
        
        # Compter les fréquences
        from collections import Counter
        word_freq = Counter(filtered_words)
        key_words = [word for word, freq in word_freq.most_common(20)]
        
        return {
            'cleaned_text': text,
            'sentences': sentences,
            'key_words': key_words,
            'word_count': len(words),
            'sentence_count': len(sentences)
        }
        
    except Exception as e:
        logger.error(f"Erreur lors du prétraitement: {str(e)}")
        return {'cleaned_text': text, 'error': str(e)}

@shared_task
def generate_summary_async(course_id):
    """
    Génération asynchrone du résumé IA
    """
    try:
        course = Course.objects.get(id=course_id)
        
        # Créer un job de traitement IA
        job = AIProcessingJob.objects.create(
            job_type='summarization',
            course=course,
            user=course.user,
            status='processing'
        )
        job.start_processing()
        
        # Générer le résumé avec IA
        result = get_ai_summary(course.extracted_text, level='intermediate')
        
        if result.get('success'):
            course.summary = result['summary']
            course.ai_summary = result.get('summary_data', {})
            course.save()
            
            job.complete_job(result)
            logger.info(f"Résumé généré pour le cours {course_id}")
        else:
            job.fail_job(result.get('error', 'Erreur inconnue'))
            logger.error(f"Erreur lors de la génération du résumé {course_id}: {result.get('error')}")
        
        return f"Résumé généré pour le cours {course_id}"
        
    except Exception as e:
        logger.error(f"Erreur lors de la génération du résumé {course_id}: {str(e)}")
        if 'job' in locals():
            job.fail_job(str(e))
        raise

@shared_task
def extract_key_concepts_async(course_id):
    """
    Extraction asynchrone des concepts clés
    """
    try:
        course = Course.objects.get(id=course_id)
        
        # Créer un job de traitement IA
        job = AIProcessingJob.objects.create(
            job_type='concept_extraction',
            course=course,
            user=course.user,
            status='processing'
        )
        job.start_processing()
        
        # Extraction des concepts clés avec IA
        from .similarity import extract_key_concepts
        
        concepts = extract_key_concepts(course.extracted_text)
        
        course.key_concepts = concepts
        course.save()
        
        job.complete_job({'concepts': concepts})
        logger.info(f"Concepts clés extraits pour le cours {course_id}")
        
        return f"Concepts clés extraits pour le cours {course_id}"
        
    except Exception as e:
        logger.error(f"Erreur lors de l'extraction des concepts {course_id}: {str(e)}")
        if 'job' in locals():
            job.fail_job(str(e))
        raise

@shared_task
def generate_quiz_async(course_id, num_questions=5, difficulty='medium'):
    """
    Génération asynchrone du quiz
    """
    try:
        course = Course.objects.get(id=course_id)
        
        # Créer un job de traitement IA
        job = AIProcessingJob.objects.create(
            job_type='quiz_generation',
            course=course,
            user=course.user,
            status='processing'
        )
        job.start_processing()
        
        # Générer le quiz avec IA
        result = get_ai_quiz(course.extracted_text, num_questions, difficulty)
        
        if result.get('success'):
            # Créer le quiz dans la base de données
            quiz = Quiz.objects.create(
                title=f"Quiz IA - {course.title}",
                description=f"Quiz généré par IA ({difficulty})",
                course=course,
                difficulty=difficulty
            )
            
            # Créer les questions
            for i, q_data in enumerate(result['questions']):
                question = Question.objects.create(
                    quiz=quiz,
                    question_text=q_data.get('question_text', q_data.get('question', '')),
                    question_type=q_data.get('question_type', 'multiple_choice'),
                    correct_answer=q_data.get('correct_answer', ''),
                    explanation=q_data.get('explanation', ''),
                    options=q_data.get('options', []),
                    order=i + 1
                )
            
            job.complete_job({
                'quiz_id': str(quiz.id),
                'questions_count': len(result['questions'])
            })
            logger.info(f"Quiz généré pour le cours {course_id}: {len(result['questions'])} questions")
            
        else:
            job.fail_job(result.get('error', 'Erreur inconnue'))
            logger.error(f"Erreur lors de la génération du quiz {course_id}: {result.get('error')}")
        
        return f"Quiz généré pour le cours {course_id}"
        
    except Exception as e:
        logger.error(f"Erreur lors de la génération du quiz {course_id}: {str(e)}")
        if 'job' in locals():
            job.fail_job(str(e))
        raise

@shared_task
def evaluate_quiz_answer_async(attempt_id, question_id, user_answer):
    """
    Évaluation asynchrone d'une réponse de quiz avec similarité sémantique
    """
    try:
        from core.models import QuizAttempt
        from .similarity import evaluate_quiz_answer
        
        attempt = QuizAttempt.objects.get(id=attempt_id)
        question = Question.objects.get(id=question_id)
        
        # Évaluer la réponse avec similarité sémantique
        evaluation = evaluate_quiz_answer(user_answer, question.correct_answer)
        
        # Mettre à jour la tentative
        answers = attempt.answers.copy()
        answers[str(question_id)] = {
            'answer': user_answer,
            'is_correct': evaluation['is_correct'],
            'similarity_score': evaluation['similarity_score'],
            'evaluation_method': evaluation['evaluation_method'],
            'confidence': evaluation['confidence']
        }
        attempt.answers = answers
        attempt.save()
        
        logger.info(f"Réponse évaluée pour la tentative {attempt_id}: {evaluation['is_correct']}")
        return evaluation
        
    except Exception as e:
        logger.error(f"Erreur lors de l'évaluation de la réponse {attempt_id}: {str(e)}")
        raise

@shared_task
def update_analytics_async(user_id, activity_type, metadata=None):
    """
    Mise à jour asynchrone des analytics
    """
    try:
        from analytics.models import UserActivity
        from django.contrib.auth.models import User
        
        user = User.objects.get(id=user_id)
        
        # Créer l'activité
        activity = UserActivity.objects.create(
            user=user,
            activity_type=activity_type,
            metadata=metadata or {}
        )
        
        # Mettre à jour les analytics de l'utilisateur
        from analytics.models import UserAnalytics
        analytics, created = UserAnalytics.objects.get_or_create(user=user)
        analytics.update_statistics()
        
        logger.info(f"Analytics mis à jour pour l'utilisateur {user_id}")
        return f"Analytics mis à jour pour l'utilisateur {user_id}"
        
    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour des analytics {user_id}: {str(e)}")
        raise

@shared_task
def update_gamification_async(user_id, points=0, badge_id=None, achievement_id=None):
    """
    Mise à jour asynchrone de la gamification
    """
    try:
        from django.contrib.auth.models import User
        from core.models import UserProfile
        from gamification.models import Badge, UserBadge, Achievement, UserAchievement
        
        user = User.objects.get(id=user_id)
        profile = user.profile
        
        # Ajouter des points d'expérience
        if points > 0:
            level_up = profile.add_experience(points)
            if level_up:
                logger.info(f"Utilisateur {user_id} a gagné un niveau !")
        
        # Accorder un badge
        if badge_id:
            try:
                badge = Badge.objects.get(id=badge_id)
                UserBadge.objects.get_or_create(user=user, badge=badge)
                logger.info(f"Badge {badge_id} accordé à l'utilisateur {user_id}")
            except Badge.DoesNotExist:
                logger.warning(f"Badge {badge_id} non trouvé")
        
        # Accorder une réalisation
        if achievement_id:
            try:
                achievement = Achievement.objects.get(id=achievement_id)
                UserAchievement.objects.get_or_create(user=user, achievement=achievement)
                logger.info(f"Achievement {achievement_id} accordé à l'utilisateur {user_id}")
            except Achievement.DoesNotExist:
                logger.warning(f"Achievement {achievement_id} non trouvé")
        
        return f"Gamification mise à jour pour l'utilisateur {user_id}"
        
    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour de la gamification {user_id}: {str(e)}")
        raise
