"""
Configuration de l'administration Django pour l'application core
"""

from django.contrib import admin
from .models import Category, Tag, Course, Quiz, Question, QuizAttempt, StudySession, UserProfile, Notification

# Enregistrement des modèles
admin.site.register(Category)
admin.site.register(Tag)
admin.site.register(Course)
admin.site.register(Quiz)
admin.site.register(Question)
admin.site.register(QuizAttempt)
admin.site.register(StudySession)
admin.site.register(UserProfile)
admin.site.register(Notification)
