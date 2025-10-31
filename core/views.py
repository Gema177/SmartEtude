from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Avg
from django.http import JsonResponse
from django.utils import timezone
from .models import Course, Quiz, QuizAttempt
from .forms import CourseUploadForm, CustomUserCreationForm

try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

try:
    from docx import Document
except ImportError:
    Document = None


def extract_text_from_file(uploaded_file):
    """
    Extrait le texte d'un fichier uploadé selon son type MIME
    Supporte: TXT, PDF, DOCX
    """
    content_type = uploaded_file.content_type
    text = ''
    
    try:
        if content_type == 'text/plain':
            # Fichier TXT
            uploaded_file.seek(0)  # Remettre le curseur au début
            text = uploaded_file.read().decode('utf-8', errors='ignore')
            
        elif content_type == 'application/pdf':
            # Fichier PDF
            if not PyPDF2:
                raise Exception('PyPDF2 n\'est pas installé. Installez-le avec: pip install PyPDF2')
            
            uploaded_file.seek(0)
            
            try:
                reader = PyPDF2.PdfReader(uploaded_file)
                pages_text = []
                
                for page_num in range(len(reader.pages)):
                    try:
                        page = reader.pages[page_num]
                        page_text = page.extract_text()
                        if page_text and page_text.strip():
                            pages_text.append(page_text.strip())
                    except Exception as page_error:
                        print(f"⚠️ Erreur page {page_num + 1}: {str(page_error)}")
                        continue
                
                text = '\n\n'.join(pages_text)
                
                if not text.strip():
                    raise Exception('Aucun texte lisible trouvé dans le PDF. Le fichier peut être corrompu, protégé par mot de passe, ou contenir uniquement des images.')
                    
            except PyPDF2.errors.PdfReadError as pdf_error:
                raise Exception(f'Erreur de lecture PDF: {str(pdf_error)}. Le fichier peut être corrompu ou protégé.')
            except Exception as pdf_error:
                if 'EOF marker not found' in str(pdf_error):
                    raise Exception('Le fichier PDF est corrompu ou incomplet. Veuillez vérifier que le fichier a été correctement téléchargé.')
                else:
                    raise Exception(f'Erreur lors de l\'extraction PDF: {str(pdf_error)}')
            
        elif content_type in ['application/vnd.openxmlformats-officedocument.wordprocessingml.document', 
                             'application/msword']:
            # Fichier DOCX ou DOC
            if not Document:
                raise Exception('python-docx n\'est pas installé. Installez-le avec: pip install python-docx')
            
            uploaded_file.seek(0)
            doc = Document(uploaded_file)
            paragraphs = []
            
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    paragraphs.append(paragraph.text.strip())
            
            text = '\n\n'.join(paragraphs)
            
        else:
            raise Exception(f'Format de fichier non supporté: {content_type}')
            
    except Exception as e:
        raise Exception(f'Erreur lors de l\'extraction du texte: {str(e)}')
    
    return text.strip()


def home(request):
    # Si l'utilisateur est connecté, l'accueillir directement sur le tableau de bord
    if request.user.is_authenticated:
        return redirect('dashboard')

    # Statistiques pour la page d'accueil
    stats = {
        'total_courses': Course.objects.filter(is_public=True).count(),
        'total_quizzes': Quiz.objects.filter(course__is_public=True).count(),
        'total_attempts': QuizAttempt.objects.count(),
    }
    
    # Cours publics récents
    recent_courses = Course.objects.filter(is_public=True)[:6]
    
    return render(request, 'home_professional.html', {
        'stats': stats,
        'recent_courses': recent_courses
    })


def test_view(request):
    """Vue de test simple pour vérifier que l'application fonctionne"""
    return JsonResponse({
        'status': 'success',
        'message': 'SmartEtude fonctionne correctement !',
        'version': '1.0.0',
        'features': [
            'Gestion des cours',
            'Système de quiz',
            'Intelligence artificielle',
            'Analytics avancés',
            'Gamification'
        ]
    })


def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=password)
            login(request, user)
            messages.success(request, f'Compte créé avec succès pour {username}!')
            return redirect('dashboard')
    else:
        form = CustomUserCreationForm()
    return render(request, 'register_professional.html', {'form': form})


@login_required
def dashboard(request):
    user = request.user
    
    # Statistiques de l'utilisateur
    user_courses_count = user.courses.count()
    user_quizzes_count = Quiz.objects.filter(course__user=user).count()
    user_attempts_count = user.quiz_attempts.count()
    user_average_score = int(user.quiz_attempts.aggregate(avg=Avg('score'))['avg'] or 75)
    
    # Cours récents de l'utilisateur
    user_courses = user.courses.all()[:6]
    
    # Quiz récents de l'utilisateur
    user_quizzes = Quiz.objects.filter(course__user=user)[:6]
    
    return render(request, 'dashboard_professional.html', {
        'user_courses': user_courses,
        'user_quizzes': user_quizzes,
        'user_courses_count': user_courses_count,
        'user_quizzes_count': user_quizzes_count,
        'user_attempts_count': user_attempts_count,
        'user_average_score': user_average_score,
    })


@login_required
def upload_course(request):
    """Redirige vers le dashboard - l'upload est maintenant intégré dans la page de détail"""
    return redirect('dashboard')


@login_required
def create_course(request):
    """Créer un nouveau cours avec upload de fichier et sélection du type de résumé"""
    if request.method == 'POST':
        form = CourseUploadForm(request.POST, request.FILES)
        if form.is_valid():
            course: Course = form.save(commit=False)
            course.user = request.user
            
            try:
                # Extraire le texte du fichier uploadé
                uploaded_file = request.FILES['file']
                extracted_text = extract_text_from_file(uploaded_file)
                course.extracted_text = extracted_text
                course.save()
                
                if course.extracted_text.strip():
                    messages.success(request, f'Cours créé avec succès ! {len(extracted_text)} caractères extraits.')
                    return redirect('course_detail', course_id=course.id)
                else:
                    messages.warning(request, 'Cours créé mais aucun texte n\'a pu être extrait.')
                    return redirect('course_detail', course_id=course.id)
                
            except Exception as e:
                messages.error(request, f'Erreur lors de l\'extraction du texte: {str(e)}')
                return render(request, 'create_course.html', {'form': form})
    else:
        form = CourseUploadForm()
    return render(request, 'create_course.html', {'form': form})


def course_detail(request, course_id: str):
    course = get_object_or_404(Course, id=course_id)

    # Vérifier les permissions d'accès
    if not course.is_public:
        # Si le cours n'est pas public, vérifier que l'utilisateur est le propriétaire
        if not request.user.is_authenticated or course.user != request.user:
            from django.http import Http404
            raise Http404("Cours non trouvé ou accès non autorisé")

    # Récupérer tous les quiz existants pour ce cours
    existing_quizzes = Quiz.objects.filter(course=course).order_by('-created_at')

    # Si c'est un nouveau cours sans résumé, afficher les options de résumé
    show_summary_options = not course.summary or course.summary.strip() == ""

    return render(request, 'course_detail.html', {
        'course': course,
        'existing_quizzes': existing_quizzes,
        'show_summary_options': show_summary_options
    })


def quiz_detail(request, quiz_id: str):
    quiz = get_object_or_404(Quiz, id=quiz_id)

    # Vérifier les permissions d'accès
    if not quiz.course.is_public and (not request.user.is_authenticated or quiz.course.user != request.user):
        from django.http import Http404
        raise Http404("Quiz non trouvé ou accès non autorisé")

    questions = quiz.questions.all()
    return render(request, 'quiz_detail.html', {'quiz': quiz, 'questions': questions})


def create_quiz_data(quiz):
    """
    Fonction qui sépare les questions des réponses et prépare les données du quiz
    Avec mélange des options pour rendre le jeu moins prévisible
    """
    import random
    questions = list(quiz.questions.all())
    # Mélanger les questions pour plus de variété
    random.shuffle(questions)

    quiz_data = {
        'quiz': quiz,
        'questions': [],
        'correct_answers': {},  # Réponses correctes comme indices (0, 1, 2, 3)
        'total_questions': len(questions)
    }

    for question in questions:
        question_data = {
            'question': question,
            'options': question.options if question.options else [],
            'correct_answer_index': 0
        }

        if question.question_type == 'multiple_choice' and question.options:
            # Mélanger les options pour rendre le jeu moins prévisible
            options_copy = question.options.copy()
            random.shuffle(options_copy)
            question_data['options'] = options_copy
            
            # Trouver l'index de la bonne réponse dans les options mélangées
            try:
                correct_answer_index = options_copy.index(question.correct_answer)
                question_data['correct_answer_index'] = correct_answer_index
                # Stocker l'index de la réponse correcte
                quiz_data['correct_answers'][str(question.id)] = correct_answer_index
            except ValueError:
                # Si la réponse correcte n'est pas trouvée dans les options
                print(f"DEBUG: Correct answer '{question.correct_answer}' not found in options: {options_copy}")
                # Utiliser la première option comme fallback
                question_data['correct_answer_index'] = 0
                quiz_data['correct_answers'][str(question.id)] = 0
        else:
            # Pour les questions vrai/faux - mélanger l'ordre
            tf_options = ['Vrai', 'Faux']
            random.shuffle(tf_options)
            question_data['options'] = tf_options
            
            # Déterminer l'index correct après mélange
            if question.correct_answer.lower() in ['vrai', 'true', 'a']:
                correct_answer_index = tf_options.index('Vrai')
            else:
                correct_answer_index = tf_options.index('Faux')
            
            question_data['correct_answer_index'] = correct_answer_index
            quiz_data['correct_answers'][str(question.id)] = correct_answer_index

        quiz_data['questions'].append(question_data)

    return quiz_data


def render_quiz_game(request, quiz_data):
    """
    Fonction qui affiche l'interface de jeu du quiz
    """
    return render(request, 'game_quiz.html', {
        'quiz': quiz_data['quiz'],
        'questions_data': quiz_data['questions']
    })


def render_quiz_game_simple(request, quiz_data):
    """
    Version simplifiée pour diagnostiquer les problèmes
    """
    return render(request, 'game_quiz_simple.html', {
        'quiz': quiz_data['quiz'],
        'questions_data': quiz_data['questions']
    })


def render_quiz_game_debug(request, quiz_data):
    """
    Version debug ultra-simple pour diagnostiquer les problèmes
    """
    return render(request, 'game_quiz_debug.html', {
        'quiz': quiz_data['quiz'],
        'questions_data': quiz_data['questions']
    })


def correct_quiz_answers(quiz_data, user_answers):
    """
    Fonction qui corrige les réponses et calcule le score
    """
    correct_answers = quiz_data['correct_answers']
    score = 0
    results = {}

    for question_id, user_answer in user_answers.items():
        if question_id in correct_answers:
            correct_answer = correct_answers[question_id]

            # Trouver la question correspondante
            question_data = None
            for q in quiz_data['questions']:
                if str(q['question'].id) == question_id:
                    question_data = q
                    break

            if question_data:
                is_correct = False

                if question_data['question'].question_type == 'multiple_choice':
                    # L'utilisateur envoie l'index (0, 1, 2, 3), on compare directement les indices
                    try:
                        selected_index = int(user_answer)
                        is_correct = selected_index == correct_answer
                    except (ValueError, IndexError):
                        is_correct = False
                else:
                    # Pour les questions vrai/faux, comparer directement en string (robuste)
                    is_correct = str(user_answer).strip().lower() == str(correct_answer).strip().lower()

                results[question_id] = {
                    'user_answer': user_answer,
                    'correct_answer': correct_answer,
                    'is_correct': is_correct
                }

                if is_correct:
                    score += 1

    return {
        'score': score,
        'total_questions': quiz_data['total_questions'],
        'percentage': round((score / quiz_data['total_questions'] * 100), 2) if quiz_data['total_questions'] > 0 else 0.00,
        'results': results
    }


def game_quiz(request, quiz_id: str):
    quiz = get_object_or_404(Quiz, id=quiz_id)

    # Vérifier les permissions d'accès
    if not quiz.course.is_public and (not request.user.is_authenticated or quiz.course.user != request.user):
        from django.http import Http404
        raise Http404("Quiz non trouvé ou accès non autorisé")

    quiz_data = create_quiz_data(quiz)

    if request.method == 'POST':
        # Traiter les réponses
        answers = {}
        for i, question_data in enumerate(quiz_data['questions']):
            question = question_data['question']
            answer = request.POST.get(f'question_{question.id}') or request.POST.get(f'answer_{question.id}')

            if answer:
                answers[str(question.id)] = answer

        results = correct_quiz_answers(quiz_data, answers)

        # Créer une tentative avec un temps estimé
        estimated_time = len(quiz_data['questions']) * 30  # 30 secondes par question
        time_taken = timezone.timedelta(seconds=estimated_time)

        # Créer une tentative
        attempt = QuizAttempt.objects.create(
            quiz=quiz,
            user_name=request.POST.get('user_name', 'Anonyme'),
            answers=answers,
            score=results['score'],
            total_questions=quiz_data['total_questions'],
            time_taken=time_taken,
            completed_at=timezone.now(),
            is_completed=True
        )

        return redirect('quiz_results', attempt_id=attempt.id)

    return render_quiz_game(request, quiz_data)


def debug_game_quiz(request, quiz_id: str):
    """Version debug du mode jeu pour diagnostiquer les problèmes"""
    quiz = get_object_or_404(Quiz, id=quiz_id)

    # Vérifier les permissions d'accès
    if not quiz.course.is_public and (not request.user.is_authenticated or quiz.course.user != request.user):
        from django.http import Http404
        raise Http404("Quiz non trouvé ou accès non autorisé")

    quiz_data = create_quiz_data(quiz)

    if request.method == 'POST':
        # Traiter les réponses (même logique que game_quiz)
        answers = {}
        for i, question_data in enumerate(quiz_data['questions']):
            question = question_data['question']
            answer = request.POST.get(f'question_{question.id}') or request.POST.get(f'answer_{question.id}')

            if answer:
                answers[str(question.id)] = answer

        results = correct_quiz_answers(quiz_data, answers)

        # Créer une tentative avec un temps estimé
        estimated_time = len(quiz_data['questions']) * 30  # 30 secondes par question
        time_taken = timezone.timedelta(seconds=estimated_time)

        # Créer une tentative
        attempt = QuizAttempt.objects.create(
            quiz=quiz,
            user_name=request.POST.get('user_name', 'Anonyme'),
            answers=answers,
            score=results['score'],
            total_questions=quiz_data['total_questions'],
            time_taken=time_taken,
            completed_at=timezone.now(),
            is_completed=True
        )

        return redirect('quiz_results', attempt_id=attempt.id)

    return render_quiz_game_debug(request, quiz_data)


def quiz_results(request, attempt_id: str):
    attempt = get_object_or_404(QuizAttempt, id=attempt_id)
    quiz = attempt.quiz
    quiz_data = create_quiz_data(quiz)

    # Récupérer les réponses de l'utilisateur depuis le champ JSON
    user_answers = attempt.answers or {}

    results = correct_quiz_answers(quiz_data, user_answers)

    # Calculer les statistiques (cohérent avec quiz_results)
    correct_count = sum(1 for result in results['results'].values() if result['is_correct'])
    incorrect_count = sum(1 for result in results['results'].values() if not result['is_correct'])
    total_questions = quiz_data['total_questions']
    percentage = results['percentage']

    context = {
        'attempt': attempt,
        'quiz': quiz,
        'question_data': quiz_data['questions'],
        'percentage': percentage,  # Pourcentage du résultat pour l'affichage
        'total_questions': total_questions,
        'correct_count': correct_count,
        'incorrect_count': incorrect_count
    }
    
    return render(request, 'quiz_results.html', context)


def quiz_correction(request, attempt_id):
    """Page de correction détaillée du quiz avec les bonnes réponses"""
    # Récupérer la tentative (plus flexible)
    try:
        attempt = QuizAttempt.objects.get(id=attempt_id)
    except QuizAttempt.DoesNotExist:
        from django.http import Http404
        raise Http404("Tentative de quiz non trouvée")
    
    # Vérifier les permissions d'accès
    if request.user and request.user.is_authenticated:
        # Utilisateur connecté : peut accéder à ses tentatives ou aux tentatives anonymes
        if attempt.user is not None and attempt.user != request.user:
            from django.http import Http404
            raise Http404("Vous n'avez pas accès à cette tentative")
    else:
        # Utilisateur non connecté : peut seulement accéder aux tentatives anonymes
        if attempt.user is not None:
            from django.http import Http404
            raise Http404("Cette tentative nécessite une connexion")
    quiz = attempt.quiz
    quiz_data = create_quiz_data(quiz)
    
    # Récupérer les réponses de l'utilisateur depuis le champ JSON
    user_answers = attempt.answers or {}
    
    # Préparer les données pour chaque question
    question_data = []
    for question_dict in quiz_data['questions']:
        question = question_dict['question']  # L'objet Question réel
        # Utiliser la même clé que dans take_quiz (str(question.id))
        user_answer = user_answers.get(str(question.id), '')
        is_correct = False
        
        # Vérifier si la réponse est correcte (MÊME LOGIQUE QUE take_quiz et quiz_results)
        if question.question_type == 'true_false':
            # Pour Vrai/Faux, comparer directement
            is_correct = user_answer.lower() == question.correct_answer.lower()
        elif question.question_type == 'multiple_choice':
            # Pour QCM mélangé, vérifier l'index après mélange
            try:
                selected_index = int(user_answer)
                if 0 <= selected_index < len(question_dict['options']):
                    selected_option = question_dict['options'][selected_index]
                    is_correct = selected_option == quiz_data['correct_answers'][str(question.id)]
                else:
                    is_correct = False
            except (ValueError, IndexError):
                is_correct = False
        else:
            # Fallback : comparaison directe
            is_correct = user_answer == question.correct_answer
        
        # Déterminer la réponse affichée de l'utilisateur (MÊME LOGIQUE QUE quiz_results)
        display_answer = user_answer
        if question.question_type == 'true_false':
            # Pour Vrai/Faux, convertir en français
            display_answer = "Vrai" if user_answer.lower() == "true" else "Faux"
        elif question.question_type == 'multiple_choice' and question_dict['options']:
            # Pour QCM, afficher l'option sélectionnée
            try:
                selected_index = int(user_answer)
                if 0 <= selected_index < len(question_dict['options']):
                    display_answer = question_dict['options'][selected_index]
                else:
                    display_answer = "Réponse invalide"
            except (ValueError, IndexError):
                display_answer = "Réponse invalide"
        
        question_data.append({
            'question': question,
            'user_answer': display_answer,
            'correct_answer': question.correct_answer,
            'is_correct': is_correct,
            'options': question_dict['options'] if question.question_type == 'multiple_choice' else None
        })
    # Calculer les statistiques (cohérent avec quiz_results)
    correct_count = sum(1 for q in question_data if q['is_correct'])
    incorrect_count = sum(1 for q in question_data if not q['is_correct'])
    total_questions = len(quiz_data['questions'])
    percentage = (correct_count / total_questions * 100) if total_questions > 0 else 0
    
    context = {
        'attempt': attempt,
        'quiz': quiz,
        'question_data': question_data,
        'percentage': percentage,  # Pourcentage du résultat pour l'affichage
        'total_questions': total_questions,
        'correct_count': correct_count,
        'incorrect_count': incorrect_count
    }
    
    return render(request, 'quiz_correction.html', context)


@login_required
def delete_course(request, course_id: str):
    """Vue pour supprimer un cours"""
    course = get_object_or_404(Course, id=course_id, user=request.user)
    
    if request.method == 'POST':
        course_title = course.title
        course.delete()
        messages.success(request, f'Le cours "{course_title}" a été supprimé avec succès.')
        return redirect('dashboard')
    
    # Si c'est une requête GET, afficher une page de confirmation
    return render(request, 'delete_course_confirm.html', {'course': course})


def profile(request):
    """Vue pour la page de profil utilisateur"""
    if not request.user.is_authenticated:
        return redirect('login')
    
    # Calculer les statistiques de l'utilisateur
    user_courses = Course.objects.filter(user=request.user).count()
    user_quizzes = Quiz.objects.filter(course__user=request.user).count()
    
    context = {
        'user': request.user,
        'courses_count': user_courses,
        'quizzes_count': user_quizzes,
    }
    
    return render(request, 'accounts/profile.html', context)


def custom_logout(request):
    """Vue de déconnexion personnalisée qui accepte GET et POST"""
    if request.user.is_authenticated:
        logout(request)
        messages.success(request, 'Vous avez été déconnecté avec succès.')
    return redirect('home')
