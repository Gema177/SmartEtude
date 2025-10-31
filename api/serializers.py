from rest_framework import serializers
from django.contrib.auth.models import User
from core.models import (
    Course, Quiz, Question, QuizAttempt, UserProfile, 
    Category, Tag, StudySession, Notification
)


class UserSerializer(serializers.ModelSerializer):
    """Sérialiseur pour les utilisateurs"""
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'date_joined']
        read_only_fields = ['id', 'date_joined']


class CategorySerializer(serializers.ModelSerializer):
    """Sérialiseur pour les catégories"""
    course_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = '__all__'
    
    def get_course_count(self, obj):
        return obj.courses.count()


class TagSerializer(serializers.ModelSerializer):
    """Sérialiseur pour les tags"""
    class Meta:
        model = Tag
        fields = '__all__'


class CourseListSerializer(serializers.ModelSerializer):
    """Sérialiseur pour la liste des cours (version courte)"""
    category = CategorySerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    user = UserSerializer(read_only=True)
    rating = serializers.DecimalField(max_digits=3, decimal_places=2, read_only=True)
    
    class Meta:
        model = Course
        fields = [
            'id', 'title', 'slug', 'short_description', 'category', 'tags',
            'difficulty', 'status', 'thumbnail', 'user', 'rating', 'rating_count',
            'view_count', 'like_count', 'quiz_count', 'total_attempts',
            'completion_rate', 'estimated_duration', 'created_at', 'updated_at'
        ]


class CourseDetailSerializer(serializers.ModelSerializer):
    """Sérialiseur pour le détail d'un cours"""
    category = CategorySerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    user = UserSerializer(read_only=True)
    collaborators = UserSerializer(many=True, read_only=True)
    quizzes = serializers.SerializerMethodField()
    related_courses = serializers.SerializerMethodField()
    
    class Meta:
        model = Course
        fields = '__all__'
        read_only_fields = [
            'id', 'slug', 'extracted_text', 'summary', 'key_concepts',
            'view_count', 'like_count', 'share_count', 'rating', 'rating_count',
            'ai_processed', 'processing_status', 'last_ai_update',
            'created_at', 'updated_at', 'published_at'
        ]
    
    def get_quizzes(self, obj):
        """Récupère les quizzes du cours"""
        from .serializers import QuizListSerializer
        return QuizListSerializer(obj.quizzes.filter(is_active=True), many=True).data
    
    def get_related_courses(self, obj):
        """Récupère les cours similaires"""
        if obj.category:
            related = Course.objects.filter(
                category=obj.category,
                status='published',
                is_public=True
            ).exclude(id=obj.id)[:3]
            return CourseListSerializer(related, many=True).data
        return []


class CourseCreateSerializer(serializers.ModelSerializer):
    """Sérialiseur pour la création d'un cours"""
    class Meta:
        model = Course
        fields = [
            'title', 'description', 'short_description', 'category', 'tags',
            'difficulty', 'file', 'thumbnail', 'is_public', 'is_featured'
        ]
    
    def validate_file(self, value):
        """Validation du fichier uploadé"""
        allowed_extensions = ['.pdf', '.docx', '.txt']
        import os
        ext = os.path.splitext(value.name)[1].lower()
        if ext not in allowed_extensions:
            raise serializers.ValidationError(
                f"Type de fichier non supporté. Extensions autorisées: {', '.join(allowed_extensions)}"
            )
        
        # Vérifier la taille du fichier (max 10MB)
        if value.size > 10 * 1024 * 1024:
            raise serializers.ValidationError("Le fichier est trop volumineux (max 10MB)")
        
        return value


class QuestionSerializer(serializers.ModelSerializer):
    """Sérialiseur pour les questions"""
    class Meta:
        model = Question
        fields = [
            'id', 'question_type', 'question_text', 'options', 'points',
            'difficulty', 'order', 'hint'
        ]
        read_only_fields = ['id']


class QuizListSerializer(serializers.ModelSerializer):
    """Sérialiseur pour la liste des quizzes"""
    course = serializers.StringRelatedField()
    question_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Quiz
        fields = [
            'id', 'title', 'description', 'course', 'difficulty',
            'time_limit', 'passing_score', 'max_attempts',
            'total_attempts', 'average_score', 'success_rate',
            'is_active', 'created_at'
        ]
    
    def get_question_count(self, obj):
        return obj.questions.count()


class QuizDetailSerializer(serializers.ModelSerializer):
    """Sérialiseur pour le détail d'un quiz"""
    course = CourseListSerializer(read_only=True)
    questions = QuestionSerializer(many=True, read_only=True)
    
    class Meta:
        model = Quiz
        fields = '__all__'


class QuizCreateSerializer(serializers.ModelSerializer):
    """Sérialiseur pour la création d'un quiz"""
    class Meta:
        model = Quiz
        fields = [
            'title', 'description', 'difficulty', 'time_limit',
            'passing_score', 'max_attempts', 'shuffle_questions',
            'show_results_immediately'
        ]


class QuizAttemptSerializer(serializers.ModelSerializer):
    """Sérialiseur pour les tentatives de quiz"""
    quiz = QuizListSerializer(read_only=True)
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = QuizAttempt
        fields = [
            'id', 'quiz', 'user', 'user_name', 'score', 'total_questions',
            'score_percentage', 'started_at', 'completed_at', 'time_taken',
            'is_completed', 'passed', 'question_times', 'hints_used',
            'skipped_questions'
        ]
        read_only_fields = [
            'id', 'score_percentage', 'started_at', 'completed_at',
            'is_completed', 'passed'
        ]


class QuizAttemptCreateSerializer(serializers.ModelSerializer):
    """Sérialiseur pour la création d'une tentative"""
    class Meta:
        model = QuizAttempt
        fields = ['user_name', 'answers', 'question_times', 'hints_used', 'skipped_questions']
    
    def validate_answers(self, value):
        """Validation des réponses"""
        if not isinstance(value, dict):
            raise serializers.ValidationError("Les réponses doivent être un dictionnaire")
        return value


class UserProfileSerializer(serializers.ModelSerializer):
    """Sérialiseur pour le profil utilisateur"""
    user = UserSerializer(read_only=True)
    preferred_categories = CategorySerializer(many=True, read_only=True)
    
    class Meta:
        model = UserProfile
        fields = [
            'id', 'user', 'bio', 'avatar', 'date_of_birth', 'location',
            'preferred_difficulty', 'preferred_categories', 'learning_goals',
            'total_courses_completed', 'total_quizzes_passed', 'average_quiz_score',
            'total_study_time', 'streak_days', 'last_study_date',
            'experience_points', 'level', 'badges', 'achievements',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'total_courses_completed', 'total_quizzes_passed',
            'average_quiz_score', 'total_study_time', 'streak_days',
            'experience_points', 'level', 'badges', 'achievements',
            'created_at', 'updated_at'
        ]


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    """Sérialiseur pour la mise à jour du profil"""
    class Meta:
        model = UserProfile
        fields = [
            'bio', 'avatar', 'date_of_birth', 'location',
            'preferred_difficulty', 'preferred_categories', 'learning_goals'
        ]


class StudySessionSerializer(serializers.ModelSerializer):
    """Sérialiseur pour les sessions d'étude"""
    course = CourseListSerializer(read_only=True)
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = StudySession
        fields = [
            'id', 'course', 'user', 'started_at', 'ended_at', 'duration',
            'pages_viewed', 'quizzes_taken', 'notes_taken', 'device_info', 'location'
        ]
        read_only_fields = ['id', 'started_at', 'ended_at', 'duration']


class StudySessionCreateSerializer(serializers.ModelSerializer):
    """Sérialiseur pour la création d'une session"""
    class Meta:
        model = StudySession
        fields = ['course', 'notes_taken', 'device_info', 'location']


class NotificationSerializer(serializers.ModelSerializer):
    """Sérialiseur pour les notifications"""
    class Meta:
        model = Notification
        fields = [
            'id', 'notification_type', 'title', 'message', 'is_read',
            'created_at', 'read_at', 'related_object_id', 'related_object_type'
        ]
        read_only_fields = ['id', 'created_at', 'read_at']


class CourseAnalyticsSerializer(serializers.Serializer):
    """Sérialiseur pour les analytics des cours"""
    total_views = serializers.IntegerField()
    total_attempts = serializers.IntegerField()
    average_score = serializers.DecimalField(max_digits=5, decimal_places=2)
    completion_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    popular_questions = serializers.ListField()
    time_distribution = serializers.DictField()


class UserAnalyticsSerializer(serializers.Serializer):
    """Sérialiseur pour les analytics utilisateur"""
    total_study_time = serializers.DurationField()
    courses_completed = serializers.IntegerField()
    quizzes_passed = serializers.IntegerField()
    average_score = serializers.DecimalField(max_digits=5, decimal_places=2)
    streak_days = serializers.IntegerField()
    level_progress = serializers.DictField()
    weekly_activity = serializers.ListField()


class SearchResultSerializer(serializers.Serializer):
    """Sérialiseur pour les résultats de recherche"""
    courses = CourseListSerializer(many=True)
    quizzes = QuizListSerializer(many=True)
    total_results = serializers.IntegerField()
    search_time = serializers.FloatField()


class RecommendationSerializer(serializers.Serializer):
    """Sérialiseur pour les recommandations"""
    recommended_courses = CourseListSerializer(many=True)
    recommended_quizzes = QuizListSerializer(many=True)
    reason = serializers.CharField()
    confidence_score = serializers.FloatField()
