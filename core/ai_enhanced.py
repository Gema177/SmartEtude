"""
Module d'IA amélioré pour SmartEtude
Fournit des fonctions d'interface pour les fonctionnalités d'IA
"""

from typing import Dict, Any
from .phi3_ai import phi3_ai


def get_ai_summary(text: str, level: str = 'intermediate') -> Dict[str, Any]:
    """
    Génère un résumé IA du texte fourni

    Args:
        text: Le texte à résumer
        level: Niveau de détail ('beginner', 'intermediate', 'advanced')

    Returns:
        Dictionnaire avec 'success', 'summary' et 'summary_data' ou 'error'
    """
    try:
        result = phi3_ai.generate_summary(text, level=level, language='french')

        if result.get('success'):
            return {
                'success': True,
                'summary': result['summary'],
                'summary_data': {
                    'model': result.get('model', 'gpt-4o-mini'),
                    'level': level,
                    'language': 'french'
                }
            }
        else:
            return {
                'success': False,
                'error': result.get('error', 'Erreur inconnue lors de la génération du résumé')
            }
    except Exception as e:
        return {
            'success': False,
            'error': f'Erreur lors de la génération du résumé: {str(e)}'
        }


def get_ai_quiz(text: str, num_questions: int = 5, difficulty: str = 'medium') -> Dict[str, Any]:
    """
    Génère un quiz IA basé sur le texte fourni

    Args:
        text: Le texte sur lequel baser le quiz
        num_questions: Nombre de questions à générer
        difficulty: Difficulté ('easy', 'medium', 'hard')

    Returns:
        Dictionnaire avec 'success', 'questions' et métadonnées ou 'error'
    """
    try:
        result = phi3_ai.generate_quiz(
            text,
            num_questions=num_questions,
            difficulty=difficulty,
            language='french'
        )

        if result.get('success'):
            return {
                'success': True,
                'questions': result['quiz'],
                'quiz_data': {
                    'model': result.get('model', 'gpt-4o-mini'),
                    'num_questions': num_questions,
                    'difficulty': difficulty,
                    'language': 'french'
                }
            }
        else:
            return {
                'success': False,
                'error': result.get('error', 'Erreur inconnue lors de la génération du quiz')
            }
    except Exception as e:
        return {
            'success': False,
            'error': f'Erreur lors de la génération du quiz: {str(e)}'
        }
