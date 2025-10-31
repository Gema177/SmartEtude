from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken
from django.shortcuts import get_object_or_404

from .serializers import UserSerializer, UserProfileSerializer, UserProfileUpdateSerializer
from core.models import UserProfile


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
    
    def get(self, request):
        """Récupère le profil de l'utilisateur connecté"""
        profile = getattr(request.user, 'profile', None)
        if not profile:
            profile = UserProfile.objects.create(user=request.user)
        
        serializer = UserProfileSerializer(profile)
        return Response(serializer.data)
    
    def put(self, request):
        """Met à jour le profil de l'utilisateur connecté"""
        profile = getattr(request.user, 'profile', None)
        if not profile:
            profile = UserProfile.objects.create(user=request.user)
        
        serializer = UserProfileUpdateSerializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response(UserProfileSerializer(profile).data)
