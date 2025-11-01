"""
Vues pour les fonctionnalités IA avec Phi-3 pour SmartEtude
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.conf import settings
from django.contrib import messages
from django.core.cache import cache
import json
import re
from .models import Course, Quiz, Question
from .decorators import subscription_required
from .phi3_ai import phi3_ai

import markdown
from django.utils.safestring import mark_safe


import re

def parse_ai_quiz_text(quiz_text):
    """
    Fonction de parsing complètement réécrite pour gérer le format généré par l'IA
    """
    questions = []
    
    print(f"DEBUG: Parsing quiz text of length: {len(quiz_text)}")
    print(f"DEBUG: Quiz text preview: {quiz_text[:500]}...")

    # Diviser le texte en lignes pour un parsing plus simple
    lines = quiz_text.split('\n')
    current_question = None
    current_options = []
    in_options = False
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Détecter le début d'une nouvelle question
        question_match = re.match(r'^(\d+)\.\s*(.+)$', line)
        if question_match:
            # Sauvegarder la question précédente si elle existe
            if current_question:
                questions.append(current_question)
            
            # Commencer une nouvelle question
            question_num = question_match.group(1)
            question_text = question_match.group(2).strip()
            
            # Détecter le type de question
            question_type = "multiple_choice"
            
            print(f"DEBUG: Analyzing question {question_num}: '{question_text[:100]}...'")
            
            # Détection FORCÉE des questions Vrai/Faux
            tf_indicators = [
                'vrai ou faux', 'true or false', 'est-ce vrai', 'est-ce faux',
                'cette affirmation est', 'cette déclaration est', 'ceci est vrai',
                'ceci est faux', 'correct ou incorrect', 'right or wrong',
                'principalement adopté', 'principalement accéléré', 'uniquement',
                'seulement', 'exclusivement', 'a été principalement', 'est principalement',
                'a été adopté', 'a été accéléré', 'ne présente que', 'n\'a que',
                'principalement', 'uniquement', 'seulement', 'exclusivement'
            ]
            
            # Vérifier chaque indicateur
            for indicator in tf_indicators:
                if indicator in question_text.lower():
                    question_type = "true_false"
                    print(f"DEBUG: Question {question_num} detected as True/False (found '{indicator}')")
                    break
            
            # Détection basée sur la structure de la phrase
            if question_type == "multiple_choice":
                # Phrases qui commencent par "Le/La/Les" + verbe + "principalement"
                if (question_text.lower().startswith(('le ', 'la ', 'les ')) and 
                    'principalement' in question_text.lower()):
                    question_type = "true_false"
                    print(f"DEBUG: Question {question_num} detected as True/False (structure match)")
                # Phrases affirmatives courtes
                elif len(question_text) < 100 and not '?' in question_text:
                    question_type = "true_false"
                    print(f"DEBUG: Question {question_num} detected as True/False (short affirmative)")
            
            current_question = {
                'question': f"{question_num}. {question_text}",
                'options': [],
                'correct_answer': '',
                'type': question_type
            }
            current_options = []
            in_options = False
            continue
        
        # Détecter les options A, B, C, D (seulement pour les QCM)
        option_match = re.match(r'^([A-D])[\.\)]\s*(.+)$', line)
        if option_match and current_question and current_question['type'] != 'true_false':
            letter = option_match.group(1)
            text = option_match.group(2).strip()
            current_options.append(text)
            in_options = True
            print(f"DEBUG: Found option {letter}: {text}")
            continue
        
        # Détecter les options Vrai/Faux
        if line.lower() in ['vrai', 'faux', 'true', 'false'] and current_question and current_question['type'] == 'true_false':
            current_options.append(line)
            in_options = True
            print(f"DEBUG: Found TF option: {line}")
            continue
        
        # Détecter la réponse correcte
        answer_match = re.match(r'(?:Réponse correcte|Réponse|Correct|Answer):\s*(.+)$', line, re.IGNORECASE)
        if answer_match and current_question:
            answer = answer_match.group(1).strip()
            
            if current_question['type'] == 'true_false':
                # Pour Vrai/Faux
                if answer.lower() in ['vrai', 'true']:
                    current_question['correct_answer'] = 0
                else:
                    current_question['correct_answer'] = 1
                print(f"DEBUG: Found TF answer: {answer}")
            else:
                # Pour QCM
                if answer.upper() in ['A', 'B', 'C', 'D']:
                    current_question['correct_answer'] = ord(answer.upper()) - ord('A')
                    print(f"DEBUG: Found QCM answer: {answer}")
                else:
                    # Fallback si la réponse n'est pas trouvée
                    current_question['correct_answer'] = 0
                    print(f"DEBUG: QCM answer not found, defaulting to 0")
            
            # Finaliser la question
            if current_question['type'] == 'true_false':
                current_question['options'] = ['Vrai', 'Faux']
                # Pour Vrai/Faux, ne pas stocker les options A, B, C, D
                current_question['options'] = ['Vrai', 'Faux']
            else:
                current_question['options'] = current_options if current_options else ['Option A', 'Option B', 'Option C', 'Option D']
            
            questions.append(current_question)
            current_question = None
            current_options = []
            in_options = False
    
    # Ajouter la dernière question si elle existe
    if current_question:
        if current_question['type'] == 'true_false':
            current_question['options'] = ['Vrai', 'Faux']
        else:
            current_question['options'] = current_options if current_options else ['Option A', 'Option B', 'Option C', 'Option D']
        questions.append(current_question)
    
    print(f"DEBUG: Successfully parsed {len(questions)} questions")
    
    # Fallback si aucune question n'a été trouvée
    if not questions:
        print("DEBUG: Using fallback - no questions found")
        fallback_type = "true_false" if any(word in quiz_text.lower() for word in ['vrai', 'faux', 'true', 'false']) else "multiple_choice"
        fallback_options = ['Vrai', 'Faux'] if fallback_type == "true_false" else ['Option A', 'Option B', 'Option C', 'Option D']
        
        questions.append({
            'question': quiz_text[:500],
            'options': fallback_options,
            'correct_answer': 0,
            'type': fallback_type
        })
    
    return questions


@login_required
def ai_dashboard(request):
    """Tableau de bord IA avec toutes les fonctionnalités"""
    # QuerySet complet pour les statistiques
    user_courses_all = Course.objects.filter(user=request.user)
    
    # QuerySet limité pour l'affichage
    user_courses = user_courses_all.order_by('-created_at')[:10]
    
    # Statistiques IA
    ai_stats = {
        'total_courses': user_courses_all.count(),
        'courses_with_ai_summary': user_courses_all.filter(ai_summary__isnull=False).count(),
        'total_ai_quizzes': Quiz.objects.filter(course__user=request.user, title__icontains='IA').count(),
        'recent_ai_activity': []
    }
    
    return render(request, 'ai_dashboard.html', {
        'courses': user_courses,
        'ai_stats': ai_stats,
        'model_info': phi3_ai.get_model_info()
    })


@login_required
def ai_settings(request):
    """Paramètres IA de l'utilisateur"""
    return render(request, 'ai_settings.html', {
        'phi3_info': phi3_ai.get_model_info()
    })


@login_required
def phi3_summary_view(request, course_id):
    """Vue pour générer un résumé avec Phi-3"""
    course = get_object_or_404(Course, id=course_id)

    # Vérifier les permissions d'accès
    if not course.is_public and (not request.user.is_authenticated or course.user != request.user):
        from django.http import Http404
        raise Http404("Cours non trouvé ou accès non autorisé")

    if request.method == 'POST':
        try:
            data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
            
            level = data.get('level', 'intermediate')
            language = data.get('language', 'french')
            
            # Vérifier le cache
            cache_key = f"phi3_summary_{course_id}_{level}_{language}"
            cached_result = cache.get(cache_key)
            
            if cached_result:
                result = cached_result
            else:
                # Générer avec Phi-3
                result = phi3_ai.generate_summary(
                    course.extracted_text,
                    level=level,
                    language=language
                )
                
                # Mettre en cache pour 2 heures
                if result.get('success'):
                    cache.set(cache_key, result, 7200)
            
            if result.get('success'):
                course.ai_summary = result['summary']
                course.save()
                return JsonResponse({
                    'success': True,
                    'summary': result['summary'],
                    'model': result.get('model', getattr(settings, 'AI_MODEL', 'gpt-4o-mini'))
                })
            else:
                # Fallback local: créer un résumé simple si l'IA échoue et le renvoyer en JSON
                from django.utils.text import Truncator
                source_text = (course.extracted_text or '')
                fallback = Truncator(source_text).chars(800) or "Résumé indisponible. Le contenu source est vide."
                course.ai_summary = {
                    'summary': fallback,
                    'error': result.get('error', 'IA indisponible'),
                    'source': 'local_fallback'
                }
                course.save()
                return JsonResponse({
                    'success': True,
                    'summary': fallback,
                    'fallback': True
                })
                
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Erreur: {str(e)}'
            })
    
    return render(request, 'phi3_summary.html', {
        'course': course,
        'model_info': phi3_ai.get_model_info()
    })


@login_required
@subscription_required
def phi3_quiz_view(request, course_id):
    """Vue pour générer un quiz avec Phi-3"""
    course = get_object_or_404(Course, id=course_id)

    # Vérifier les permissions d'accès
    if not course.is_public and (not request.user.is_authenticated or course.user != request.user):
        from django.http import Http404
        raise Http404("Cours non trouvé ou accès non autorisé")

    if request.method == 'POST':
        try:
            data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
            
            num_questions = int(data.get('num_questions', 5))
            difficulty = data.get('difficulty', 'medium')
            language = data.get('language', 'french')
            
            # Vérifier le cache
            cache_key = f"phi3_quiz_{course_id}_{num_questions}_{difficulty}_{language}"
            cached_result = cache.get(cache_key)
            
            if cached_result:
                result = cached_result
            else:
                # Générer avec Phi-3
                result = phi3_ai.generate_quiz(
                    course.extracted_text,
                    num_questions=num_questions,
                    difficulty=difficulty,
                    language=language
                )
                
                # Mettre en cache pour 2 heures
                if result.get('success'):
                    cache.set(cache_key, result, 7200)
            
            if result.get('success'):
                print(f"DEBUG: Quiz generation successful, result keys: {result.keys()}")
                print(f"DEBUG: Quiz text length: {len(result.get('quiz_text', ''))}")
                print(f"DEBUG: Quiz text preview: {result.get('quiz_text', '')[:100]}...")

                quiz = Quiz.objects.create(
                    title=f"Quiz IA - {course.title}",
                    description=f"Quiz généré par IA ({difficulty}) pour le cours {course.title}",
                    course=course,
                    difficulty=difficulty
                )

                # Créer les questions
                try:
                    questions = parse_ai_quiz_text(result.get('quiz_text', ''))
                    print(f"DEBUG: Parsed {len(questions)} questions from quiz text")

                    for i, q_data in enumerate(questions):
                        print(f"DEBUG: Creating question {i+1}: {q_data.get('question', '')[:50]}...")
                        
                        # Nettoyer encore plus le texte de la question
                        clean_question = q_data.get('question', '')
                        # Enlever les numéros de question du début
                        clean_question = re.sub(r'^\d+\.\s*', '', clean_question)
                        # Enlever toute réponse ou explication qui pourrait rester
                        clean_question = re.sub(
                            r'\*\*.*?\*\*|Réponse correcte.*?$|Explication.*?$',
                            '',
                            clean_question,
                            flags=re.IGNORECASE | re.DOTALL
                        ).strip()
                        
                        Question.objects.create(
                            quiz=quiz,
                            question_text=clean_question[:500],
                            question_type=q_data.get('type', 'multiple_choice'),
                            correct_answer=q_data.get('correct_answer', ''),
                            options=q_data.get('options', []),
                            order=i + 1
                        )

                    return JsonResponse({
                        'success': True,
                        'quiz_id': str(quiz.id),
                        'redirect_url': f'/quiz/{quiz.id}/game/',
                        'model': result.get('model', getattr(settings, 'AI_MODEL', 'gpt-4o-mini'))
                    })
                except Exception as e:
                    print(f"DEBUG: Error creating questions: {str(e)}")
                    return JsonResponse({
                        'success': False,
                        'error': f'Erreur lors de la création des questions: {str(e)}'
                    })
            else:
                print(f"DEBUG: Quiz generation failed: {result.get('error', 'Unknown error')}")
                return JsonResponse({
                    'success': False,
                    'error': result.get('error', 'Erreur inconnue')
                })
                
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Erreur: {str(e)}'
            })
    
    return render(request, 'phi3_quiz.html', {
        'course': course,
        'model_info': phi3_ai.get_model_info()
    })


@login_required
@subscription_required
def phi3_chat_view(request, course_id):
    """Vue pour chat avec Phi-3"""
    course = get_object_or_404(Course, id=course_id)

    # Vérifier les permissions d'accès
    if not course.is_public and (not request.user.is_authenticated or course.user != request.user):
        from django.http import Http404
        raise Http404("Cours non trouvé ou accès non autorisé")

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            question = data.get('question', '')
            language = data.get('language', 'french')
            
            if not question:
                return JsonResponse({
                    'success': False,
                    'error': 'Question requise'
                })
            
            # Générer avec Phi-3
            result = phi3_ai.chat_with_course(
                course.extracted_text,
                question=question,
                language=language
            )
            
            if result.get('success'):
                return JsonResponse({
                    'success': True,
                    'answer': result['answer'],
                    'model': result.get('model', getattr(settings, 'AI_MODEL', 'gpt-4o-mini'))
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': result.get('error', 'Erreur inconnue')
                })
                
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Erreur: {str(e)}'
            })
    
    return render(request, 'phi3_chat.html', {
        'course': course,
        'model_info': phi3_ai.get_model_info()
    })


@login_required
@subscription_required
def ai_quick_summary(request, course_id):
    """API rapide pour générer un résumé"""
    course = get_object_or_404(Course, id=course_id)

    # Vérifier les permissions d'accès
    if not course.is_public and (not request.user.is_authenticated or course.user != request.user):
        from django.http import Http404
        raise Http404("Cours non trouvé ou accès non autorisé")

    try:
        result = phi3_ai.generate_summary(
            course.extracted_text,
            level='intermediate',
            language='french'
        )
        
        if result.get('success'):
            return JsonResponse({
                'success': True,
                'summary': result['summary']
            })
        else:
            return JsonResponse({
                'success': False,
                'error': result.get('error', 'Erreur inconnue')
            })
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Erreur: {str(e)}'
        })


@login_required
@subscription_required
def ai_quick_quiz(request, course_id):
    """API rapide pour générer un quiz"""
    course = get_object_or_404(Course, id=course_id)

    # Vérifier les permissions d'accès
    if not course.is_public and (not request.user.is_authenticated or course.user != request.user):
        from django.http import Http404
        raise Http404("Cours non trouvé ou accès non autorisé")

    try:
        result = phi3_ai.generate_quiz(
            course.extracted_text,
            num_questions=5,
            difficulty='medium',
            language='french'
        )
        
        if result.get('success'):
            # Créer le quiz dans la base de données
            quiz = Quiz.objects.create(
                title=f"Quiz IA - {course.title}",
                description=f"Quiz généré par IA (medium) pour le cours {course.title}",
                course=course,
                difficulty='medium'
            )

            # Créer les questions
            try:
                questions = parse_ai_quiz_text(result.get('quiz_text', ''))
                for i, q_data in enumerate(questions):
                    # Nettoyer encore plus le texte de la question
                    clean_question = q_data.get('question', '')
                    # Enlever les numéros de question du début
                    clean_question = re.sub(r'^\d+\.\s*', '', clean_question)
                    # Enlever toute réponse ou explication qui pourrait rester
                    clean_question = re.sub(
                        r'\*\*.*?\*\*|Réponse correcte.*?$|Explication.*?$',
                        '',
                        clean_question,
                        flags=re.IGNORECASE | re.DOTALL
                    ).strip()
                    
                    Question.objects.create(
                        quiz=quiz,
                        question_text=clean_question[:500],
                        question_type=q_data.get('type', 'multiple_choice'),
                        correct_answer=q_data.get('correct_answer', ''),
                        options=q_data.get('options', []),
                        order=i + 1
                    )

                return JsonResponse({
                    'success': True,
                    'quiz_id': str(quiz.id),
                    'redirect_url': f'/quiz/{quiz.id}/game/'
                })
            except Exception as e:
                print(f"DEBUG: Error creating questions: {str(e)}")
                return JsonResponse({
                    'success': False,
                    'error': f'Erreur lors de la création des questions: {str(e)}'
                })
        else:
            return JsonResponse({
                'success': False,
                'error': result.get('error', 'Erreur inconnue')
            })
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Erreur: {str(e)}'
        })


@login_required
def test_openai_connection(request):
    """Vue de test pour diagnostiquer les problèmes de connexion OpenAI"""
    try:
        # Test de la configuration actuelle
        from django.conf import settings

        api_key = getattr(settings, 'OPENAI_API_KEY', '')
        base_url = getattr(settings, 'OPENAI_BASE_URL', 'https://api.openai.com')
        model = getattr(settings, 'AI_MODEL', 'gpt-4o-mini')

        if not api_key:
            return JsonResponse({
                'error': 'OPENAI_API_KEY non configurée dans les variables d\'environnement',
                'config': {
                    'api_key_configured': False,
                    'base_url': base_url,
                    'model': model
                },
                'solution': 'Ajoutez OPENAI_API_KEY=sk-your-key-here dans votre fichier .env'
            })

        # Test de connexion basique
        import requests

        test_payload = {
            "model": model,
            "messages": [{"role": "user", "content": "Test de connexion"}],
            "max_tokens": 10
        }

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        response = requests.post(
            f"{base_url.rstrip('/')}/v1/chat/completions",
            json=test_payload,
            headers=headers,
            timeout=10
        )

        if response.status_code == 200:
            return JsonResponse({
                'success': True,
                'message': 'Connexion OpenAI réussie',
                'config': {
                    'api_key_configured': True,
                    'base_url': base_url,
                    'model': model
                },
                'next_step': 'Testez maintenant la génération de résumé avec /api/ai/quick-summary/'
            })
        elif response.status_code == 401:
            return JsonResponse({
                'success': False,
                'error': 'Clé API OpenAI invalide',
                'config': {
                    'api_key_configured': True,
                    'base_url': base_url,
                    'model': model,
                    'error_type': 'authentication'
                }
            })
        elif response.status_code == 429:
            return JsonResponse({
                'success': False,
                'error': 'Limite de taux atteinte (rate limit)',
                'config': {
                    'api_key_configured': True,
                    'base_url': base_url,
                    'model': model,
                    'error_type': 'rate_limit'
                }
            })
        else:
            return JsonResponse({
                'success': False,
                'error': f'Erreur API OpenAI: {response.status_code}',
                'config': {
                    'api_key_configured': True,
                    'base_url': base_url,
                    'model': model,
                    'response_text': response.text[:200]
                }
            })

    except requests.exceptions.ConnectionError:
        return JsonResponse({
            'success': False,
            'error': 'Erreur de connexion réseau',
            'config': {
                'error_type': 'network'
            }
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Erreur inattendue: {str(e)}',
            'config': {
                'error_type': 'unexpected'
            }
        })


@login_required
def debug_openai_config(request):
    """Vue de debug pour afficher la configuration OpenAI actuelle"""
    from django.conf import settings

    config_info = {
        'OPENAI_API_KEY_configured': bool(getattr(settings, 'OPENAI_API_KEY', '')),
        'OPENAI_BASE_URL': getattr(settings, 'OPENAI_BASE_URL', 'https://api.openai.com'),
        'AI_MODEL': getattr(settings, 'AI_MODEL', 'gpt-4o-mini'),
        'API_KEY_length': len(getattr(settings, 'OPENAI_API_KEY', '')),
        'settings_module': settings.__class__.__module__,
    }

    # Test rapide sans faire d'appel API
    try:
        api_key = getattr(settings, 'OPENAI_API_KEY', '')
        if not api_key:
            return JsonResponse({
                'error': 'OPENAI_API_KEY non configurée',
                'config': config_info,
                'solution': 'Ajoutez OPENAI_API_KEY=sk-your-key-here dans votre fichier .env'
            })

        return JsonResponse({
            'success': 'Configuration OpenAI détectée',
            'config': config_info,
            'next_step': 'Testez maintenant la connexion avec /api/ai/test-connection/'
        })

    except Exception as e:
        return JsonResponse({
            'error': f'Erreur de configuration: {str(e)}',
            'config': config_info
        })


@login_required
def test_quiz_parsing(request):
    """Vue de test pour diagnostiquer les problèmes de parsing de quiz"""
    if request.method == 'POST':
        quiz_text = request.POST.get('quiz_text', '')

        if not quiz_text:
            messages.error(request, 'Texte du quiz requis')
            return redirect('test_quiz_parsing')

        try:
            questions = parse_ai_quiz_text(quiz_text)

            if questions:
                messages.success(request, f'Succès ! {len(questions)} questions trouvées :')
                for i, q in enumerate(questions, 1):
                    messages.info(request, f'Q{i}: {q.get("question", "")[:50]}...')
                    if q.get('options'):
                        messages.info(request, f'  Options: {", ".join(q["options"])}')
                    messages.info(request, f'  Réponse: {q.get("correct_answer", "N/A")}')
            else:
                messages.warning(request, 'Aucune question trouvée dans le texte fourni')

            return redirect('test_quiz_parsing')

        except Exception as e:
            messages.error(request, f'Erreur de parsing: {str(e)}')
            return redirect('test_quiz_parsing')

    return render(request, 'test_quiz_parsing.html', {})


@login_required
def ai_summary_result(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    # Support à la fois JSONField ou TextField pour le résumé
    ai_data = course.ai_summary if isinstance(course.ai_summary, dict) else {}
    summary_md = ai_data.get('summary') or (course.ai_summary if isinstance(course.ai_summary, str) else '')

    # Conversion Markdown vers HTML professionnel
    summary_html = mark_safe(markdown.markdown(
        summary_md or '',
        extensions=['extra','nl2br','sane_lists']
    ))
    ai_data['summary_html'] = summary_html
    return render(request, 'ai_summary_result.html', {
        'course': course,
        'summary_data': ai_data,
        'success': bool(summary_html.strip())
    })