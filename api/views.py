from rest_framework import viewsets, status, filters, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count, Avg
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, OpenApiResponse
from drf_spectacular.types import OpenApiTypes

from .serializers import *
from core.models import *
from .permissions import IsOwnerOrReadOnly, IsCourseOwnerOrReadOnly


class StandardResultsSetPagination(PageNumberPagination):
    """Pagination standard pour l'API"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """API pour les catégories de cours"""
    queryset = Category.objects.annotate(
        course_count=Count('courses', filter=Q(courses__status='published', courses__is_public=True))
    ).filter(course_count__gt=0)
    serializer_class = CategorySerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'course_count', 'created_at']
    ordering = ['name']


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """API pour les tags"""
    queryset = Tag.objects.annotate(
        course_count=Count('courses', filter=Q(courses__status='published', courses__is_public=True))
    ).filter(course_count__gt=0)
    serializer_class = TagSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']
    ordering = ['name']


class CourseViewSet(viewsets.ModelViewSet):
    """API complète pour les cours"""
    queryset = Course.objects.select_related('category', 'user').prefetch_related('tags')
    serializer_class = CourseListSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'difficulty', 'status', 'is_public', 'is_featured']
    search_fields = ['title', 'description', 'short_description', 'tags__name']
    ordering_fields = ['title', 'created_at', 'updated_at', 'rating', 'view_count', 'like_count']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filtre les cours selon les permissions"""
        queryset = super().get_queryset()
        
        # Pour les utilisateurs non connectés, seulement les cours publics publiés
        if not self.request.user.is_authenticated:
            return queryset.filter(status='published', is_public=True)
        
        # Pour les utilisateurs connectés, leurs cours + cours publics
        return queryset.filter(
            Q(status='published', is_public=True) |
            Q(user=self.request.user) |
            Q(collaborators=self.request.user)
        ).distinct()
    
    def get_serializer_class(self):
        """Retourne le bon sérialiseur selon l'action"""
        if self.action == 'create':
            return CourseCreateSerializer
        elif self.action in ['retrieve', 'update', 'partial_update']:
            return CourseDetailSerializer
        return CourseListSerializer
    
    def perform_create(self, serializer):
        """Crée un cours avec l'utilisateur connecté"""
        serializer.save(user=self.request.user)


class QuizViewSet(viewsets.ModelViewSet):
    """API pour les quizzes"""
    queryset = Quiz.objects.select_related('course').prefetch_related('questions')
    serializer_class = QuizListSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsCourseOwnerOrReadOnly]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['course', 'difficulty', 'is_active']
    search_fields = ['title', 'description']
    ordering_fields = ['title', 'created_at', 'average_score', 'success_rate']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filtre les quizzes selon les permissions"""
        queryset = super().get_queryset()
        
        if not self.request.user.is_authenticated:
            return queryset.filter(
                is_active=True,
                course__status='published',
                course__is_public=True
            )
        
        return queryset.filter(
            Q(is_active=True, course__status='published', course__is_public=True) |
            Q(course__user=self.request.user) |
            Q(course__collaborators=self.request.user)
        ).distinct()
    
    def get_serializer_class(self):
        """Retourne le bon sérialiseur selon l'action"""
        if self.action == 'create':
            return QuizCreateSerializer
        elif self.action in ['retrieve', 'update', 'partial_update']:
            return QuizDetailSerializer
        return QuizListSerializer


class QuizAttemptViewSet(viewsets.ModelViewSet):
    """API pour les tentatives de quiz"""
    queryset = QuizAttempt.objects.select_related('quiz', 'user')
    serializer_class = QuizAttemptSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['quiz', 'user', 'passed', 'is_completed']
    ordering_fields = ['started_at', 'completed_at', 'score', 'score_percentage']
    ordering = ['-started_at']
    
    def get_queryset(self):
        """Filtre les tentatives selon les permissions"""
        queryset = super().get_queryset()
        
        if not self.request.user.is_authenticated:
            return queryset.filter(user__isnull=True)
        
        return queryset.filter(
            Q(user=self.request.user) |
            Q(quiz__course__user=self.request.user) |
            Q(quiz__course__collaborators=self.request.user)
        ).distinct()


class UserProfileViewSet(viewsets.ModelViewSet):
    """API pour les profils utilisateur"""
    queryset = UserProfile.objects.select_related('user').prefetch_related('preferred_categories')
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        """Les utilisateurs ne peuvent voir que leur propre profil"""
        return UserProfile.objects.filter(user=self.request.user)


class StudySessionViewSet(viewsets.ModelViewSet):
    """API pour les sessions d'étude"""
    queryset = StudySession.objects.select_related('course', 'user')
    serializer_class = StudySessionSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['course', 'started_at']
    ordering_fields = ['started_at', 'ended_at', 'duration']
    ordering = ['-started_at']
    
    def get_queryset(self):
        """Les utilisateurs ne peuvent voir que leurs propres sessions"""
        return StudySession.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        """Crée une session avec l'utilisateur connecté"""
        serializer.save(user=self.request.user)


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """API pour les notifications"""
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['notification_type', 'is_read']
    ordering_fields = ['created_at', 'read_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Les utilisateurs ne peuvent voir que leurs propres notifications"""
        return Notification.objects.filter(user=self.request.user)


class SearchViewSet(viewsets.ViewSet):
    """API de recherche globale"""
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    @extend_schema(
        responses={200: SearchResultSerializer}
    )
    @action(detail=False, methods=['get'])
    def global_search(self, request):
        """Recherche globale dans les cours et quizzes"""
        query = request.query_params.get('q', '')
        if not query:
            return Response({'error': 'Query parameter required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Recherche dans les cours
        courses = Course.objects.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(short_description__icontains=query) |
            Q(tags__name__icontains=query),
            status='published',
            is_public=True
        ).distinct()[:20]
        
        # Recherche dans les quizzes
        quizzes = Quiz.objects.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query),
            is_active=True,
            course__status='published',
            course__is_public=True
        ).distinct()[:20]
        
        results = {
            'courses': CourseListSerializer(courses, many=True).data,
            'quizzes': QuizListSerializer(quizzes, many=True).data,
            'total_results': courses.count() + quizzes.count(),
        }
        
        serializer = SearchResultSerializer(results)
        return Response(serializer.data)


# Vues d'authentification
class UserRegistrationView(generics.CreateAPIView):
    """Vue pour l'inscription des utilisateurs"""
    serializer_class = UserSerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Créer le profil utilisateur
        UserProfile.objects.create(user=user)
        
        # Générer les tokens JWT
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': UserSerializer(user).data,
            'tokens': {
                'access': str(refresh.access_token),
                'refresh': str(refresh)
            }
        }, status=201)


class UserProfileView(APIView):
    """Vue pour le profil utilisateur connecté"""
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        responses={200: UserProfileSerializer}
    )
    def get(self, request):
        """Récupère le profil de l'utilisateur connecté"""
        profile = getattr(request.user, 'profile', None)
        if not profile:
            profile = UserProfile.objects.create(user=request.user)
        
        serializer = UserProfileSerializer(profile)
        return Response(serializer.data)
    
    @extend_schema(
        request=UserProfileUpdateSerializer,
        responses={200: UserProfileSerializer}
    )
    def put(self, request):
        """Met à jour le profil de l'utilisateur connecté"""
        profile = getattr(request.user, 'profile', None)
        if not profile:
            profile = UserProfile.objects.create(user=request.user)
        
        serializer = UserProfileUpdateSerializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response(UserProfileSerializer(profile).data)


# Vues d'analytics
class DashboardAnalyticsView(APIView):
    """Vue pour les analytics du tableau de bord"""
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        responses={200: OpenApiTypes.OBJECT}
    )
    def get(self, request):
        """Récupère les analytics du tableau de bord"""
        user = request.user
        profile = getattr(user, 'profile', None)
        
        # Statistiques de base
        analytics = {
            'total_courses': user.courses.count(),
            'total_quizzes_taken': user.quiz_attempts.count(),
            'average_score': user.quiz_attempts.aggregate(avg=Avg('score_percentage'))['avg'] or 0,
            'streak_days': profile.streak_days if profile else 0,
            'level': profile.level if profile else 1,
            'experience_points': profile.experience_points if profile else 0,
        }
        
        return Response(analytics)


class CourseAnalyticsView(APIView):
    """Vue pour les analytics d'un cours spécifique"""
    permission_classes = [IsAuthenticated, IsCourseOwnerOrReadOnly]
    
    @extend_schema(
        responses={200: OpenApiTypes.OBJECT}
    )
    def get(self, request, course_id):
        """Récupère les analytics d'un cours"""
        course = get_object_or_404(Course, id=course_id)
        
        # Vérifier les permissions
        if not (request.user == course.user or request.user in course.collaborators.all()):
            return Response({'error': 'Permission denied'}, status=403)
        
        analytics = {
            'total_views': course.view_count,
            'total_attempts': course.total_attempts,
            'average_score': course.quizzes.aggregate(avg=Avg('average_score'))['avg'] or 0,
            'completion_rate': course.completion_rate,
        }
        
        return Response(analytics)


class UserAnalyticsView(APIView):
    """Vue pour les analytics d'un utilisateur"""
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        responses={200: OpenApiTypes.OBJECT}
    )
    def get(self, request, user_id):
        """Récupère les analytics d'un utilisateur"""
        # Les utilisateurs ne peuvent voir que leurs propres analytics
        if request.user.id != user_id:
            return Response({'error': 'Permission denied'}, status=403)
        
        profile = getattr(request.user, 'profile', None)
        if not profile:
            profile = UserProfile.objects.create(user=request.user)
        
        analytics = {
            'total_study_time': profile.total_study_time,
            'courses_completed': profile.total_courses_completed,
            'quizzes_passed': profile.total_quizzes_passed,
            'average_score': profile.average_quiz_score,
            'streak_days': profile.streak_days,
            'level_progress': {
                'current_level': profile.level,
                'current_xp': profile.experience_points,
                'next_level_xp': (profile.level + 1) ** 2 * 100
            }
        }
        
        return Response(analytics)


# Vues de recommandations
class CourseRecommendationsView(APIView):
    """Vue pour les recommandations de cours"""
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        responses={200: OpenApiTypes.OBJECT}
    )
    def get(self, request):
        """Récupère les recommandations de cours personnalisées"""
        user = request.user
        profile = getattr(user, 'profile', None)
        
        if profile and profile.preferred_categories.exists():
            recommended = Course.objects.filter(
                category__in=profile.preferred_categories.all(),
                status='published',
                is_public=True
            ).exclude(user=user).order_by('-rating', '-view_count')[:10]
        else:
            recommended = Course.objects.filter(
                status='published',
                is_public=True
            ).order_by('-rating', '-view_count')[:10]
        
        serializer = CourseListSerializer(recommended, many=True)
        return Response({
            'recommended_courses': serializer.data,
            'reason': 'Based on your preferences and popular courses',
            'confidence_score': 0.8
        })


class QuizRecommendationsView(APIView):
    """Vue pour les recommandations de quiz"""
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        responses={200: OpenApiTypes.OBJECT}
    )
    def get(self, request):
        """Récupère les recommandations de quiz personnalisées"""
        user = request.user
        profile = getattr(user, 'profile', None)
        
        if profile and profile.preferred_categories.exists():
            recommended = Quiz.objects.filter(
                course__category__in=profile.preferred_categories.all(),
                is_active=True,
                course__status='published',
                course__is_public=True
            ).order_by('-rating', '-view_count')[:10]
        else:
            recommended = Quiz.objects.filter(
                is_active=True,
                course__status='published',
                course__is_public=True
            ).order_by('-rating', '-view_count')[:10]
        
        serializer = QuizListSerializer(recommended, many=True)
        return Response({
            'recommended_quizzes': serializer.data,
            'reason': 'Based on your preferences and quiz performance',
            'confidence_score': 0.75
        })


# Vues de gamification
class LeaderboardView(APIView):
    """Vue pour le classement des utilisateurs"""
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        responses={200: OpenApiTypes.OBJECT}
    )
    def get(self, request):
        """Récupère le classement des utilisateurs"""
        # Classement par points d'expérience
        leaderboard = UserProfile.objects.select_related('user').order_by(
            '-experience_points', '-level'
        )[:20]
        
        data = []
        for i, profile in enumerate(leaderboard, 1):
            data.append({
                'rank': i,
                'username': profile.user.username,
                'level': profile.level,
                'experience_points': profile.experience_points,
                'total_courses_completed': profile.total_courses_completed,
                'total_quizzes_passed': profile.total_quizzes_passed,
            })
        
        return Response(data)


class AchievementsView(APIView):
    """Vue pour les réalisations"""
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        responses={200: OpenApiTypes.OBJECT}
    )
    def get(self, request):
        """Récupère les réalisations de l'utilisateur"""
        profile = getattr(request.user, 'profile', None)
        if not profile:
            return Response({'achievements': []})
        
        return Response({'achievements': profile.achievements})


class BadgesView(APIView):
    """Vue pour les badges"""
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        responses={200: OpenApiTypes.OBJECT}
    )
    def get(self, request):
        """Récupère les badges de l'utilisateur"""
        profile = getattr(request.user, 'profile', None)
        if not profile:
            return Response({'badges': []})
        
        return Response({'badges': profile.badges})


# Vues d'export
class ExportCoursePDFView(APIView):
    """Vue pour l'export PDF d'un cours"""
    permission_classes = [IsAuthenticated, IsCourseOwnerOrReadOnly]
    
    @extend_schema(
        responses={200: OpenApiTypes.OBJECT}
    )
    def get(self, request, course_id):
        """Exporte un cours en PDF"""
        course = get_object_or_404(Course, id=course_id)
        
        # Vérifier les permissions
        if not (request.user == course.user or request.user in course.collaborators.all()):
            return Response({'error': 'Permission denied'}, status=403)
        
        # TODO: Implémenter l'export PDF
        return Response({'message': 'PDF export not implemented yet'})


class ExportQuizResultsPDFView(APIView):
    """Vue pour l'export PDF des résultats de quiz"""
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        responses={200: OpenApiTypes.OBJECT}
    )
    def get(self, request, attempt_id):
        """Exporte les résultats d'un quiz en PDF"""
        attempt = get_object_or_404(QuizAttempt, id=attempt_id)
        
        # Vérifier les permissions
        if not (request.user == attempt.user or 
                request.user == attempt.quiz.course.user or
                request.user in attempt.quiz.course.collaborators.all()):
            return Response({'error': 'Permission denied'}, status=403)
        
        # TODO: Implémenter l'export PDF
        return Response({'message': 'PDF export not implemented yet'})


# Vues de webhooks
class AIProcessingWebhookView(APIView):
    """Webhook pour le traitement IA"""
    permission_classes = []  # Pas d'authentification pour les webhooks
    
    @extend_schema(
        request=OpenApiTypes.OBJECT,
        responses={200: OpenApiTypes.OBJECT}
    )
    def post(self, request):
        """Reçoit les résultats du traitement IA"""
        # TODO: Implémenter le traitement des webhooks IA
        return Response({'status': 'received'})


class AnalyticsWebhookView(APIView):
    """Webhook pour les analytics"""
    permission_classes = []  # Pas d'authentification pour les webhooks
    
    @extend_schema(
        request=OpenApiTypes.OBJECT,
        responses={200: OpenApiTypes.OBJECT}
    )
    def post(self, request):
        """Reçoit les données d'analytics"""
        # TODO: Implémenter le traitement des webhooks analytics
        return Response({'status': 'received'})
