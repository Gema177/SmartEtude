from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Permission personnalisée pour permettre aux propriétaires d'éditer leurs objets
    """
    
    def has_object_permission(self, request, view, obj):
        # Les permissions de lecture sont autorisées pour toute requête
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Les permissions d'écriture sont autorisées seulement pour le propriétaire
        return obj.user == request.user


class IsCourseOwnerOrReadOnly(permissions.BasePermission):
    """
    Permission pour les objets liés aux cours (quizzes, questions)
    """
    
    def has_object_permission(self, request, view, obj):
        # Les permissions de lecture sont autorisées pour toute requête
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Vérifier si l'utilisateur est propriétaire du cours ou collaborateur
        if hasattr(obj, 'course'):
            course = obj.course
        elif hasattr(obj, 'quiz') and hasattr(obj.quiz, 'course'):
            course = obj.quiz.course
        else:
            return False
        
        return (
            course.user == request.user or
            request.user in course.collaborators.all()
        )


class IsProfileOwner(permissions.BasePermission):
    """
    Permission pour les profils utilisateur
    """
    
    def has_object_permission(self, request, view, obj):
        # Seul le propriétaire du profil peut le modifier
        return obj.user == request.user


class IsStudySessionOwner(permissions.BasePermission):
    """
    Permission pour les sessions d'étude
    """
    
    def has_object_permission(self, request, view, obj):
        # Seul le propriétaire de la session peut la modifier
        return obj.user == request.user


class IsNotificationOwner(permissions.BasePermission):
    """
    Permission pour les notifications
    """
    
    def has_object_permission(self, request, view, obj):
        # Seul le destinataire de la notification peut la modifier
        return obj.user == request.user


class IsPublicCourseOrOwner(permissions.BasePermission):
    """
    Permission pour les cours publics ou privés
    """
    
    def has_object_permission(self, request, view, obj):
        # Les cours publics sont accessibles en lecture
        if request.method in permissions.SAFE_METHODS:
            return obj.is_public and obj.status == 'published'
        
        # Seul le propriétaire peut modifier
        return obj.user == request.user


class IsActiveQuizOrOwner(permissions.BasePermission):
    """
    Permission pour les quizzes actifs
    """
    
    def has_object_permission(self, request, view, obj):
        # Les quizzes actifs sont accessibles en lecture
        if request.method in permissions.SAFE_METHODS:
            return obj.is_active and obj.course.status == 'published'
        
        # Seul le propriétaire du cours peut modifier
        return (
            obj.course.user == request.user or
            request.user in obj.course.collaborators.all()
        )


class HasQuizAttemptPermission(permissions.BasePermission):
    """
    Permission pour les tentatives de quiz
    """
    
    def has_object_permission(self, request, view, obj):
        # Les utilisateurs peuvent voir leurs propres tentatives
        if obj.user == request.user:
            return True
        
        # Les propriétaires de cours peuvent voir toutes les tentatives
        if obj.quiz.course.user == request.user:
            return True
        
        # Les collaborateurs peuvent voir toutes les tentatives
        if request.user in obj.quiz.course.collaborators.all():
            return True
        
        return False


class CanCreateQuizAttempt(permissions.BasePermission):
    """
    Permission pour créer des tentatives de quiz
    """
    
    def has_permission(self, request, view):
        # Vérifier si l'utilisateur peut tenter le quiz
        quiz_id = request.data.get('quiz')
        if not quiz_id:
            return False
        
        from core.models import Quiz
        try:
            quiz = Quiz.objects.get(id=quiz_id)
            # Le quiz doit être actif et le cours publié
            if not quiz.is_active or quiz.course.status != 'published':
                return False
            
            # Vérifier les tentatives maximum pour les utilisateurs connectés
            if request.user.is_authenticated:
                user_attempts = quiz.attempts.filter(user=request.user).count()
                if user_attempts >= quiz.max_attempts:
                    return False
            
            return True
        except Quiz.DoesNotExist:
            return False


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Permission pour les administrateurs
    """
    
    def has_permission(self, request, view):
        # Les permissions de lecture sont autorisées pour toute requête
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Les permissions d'écriture sont autorisées seulement pour les administrateurs
        return request.user and request.user.is_staff


class IsSuperUserOrReadOnly(permissions.BasePermission):
    """
    Permission pour les super utilisateurs
    """
    
    def has_permission(self, request, view):
        # Les permissions de lecture sont autorisées pour toute requête
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Les permissions d'écriture sont autorisées seulement pour les super utilisateurs
        return request.user and request.user.is_superuser
