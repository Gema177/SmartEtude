from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Course


class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-input',
            'placeholder': 'votre.email@example.com'
        })
    )

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Personnaliser les widgets pour correspondre à notre design
        self.fields['username'].widget.attrs.update({
            'class': 'form-input',
            'placeholder': 'Choisissez un nom d\'utilisateur'
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'form-input',
            'placeholder': 'Créez un mot de passe sécurisé'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-input',
            'placeholder': 'Confirmez votre mot de passe'
        })

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user


class CourseUploadForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['title', 'description', 'file', 'is_public']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'block w-full rounded-md border border-gray-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Ex: Chapitre 1 - Probabilités'
            }),
            'description': forms.Textarea(attrs={
                'class': 'block w-full rounded-md border border-gray-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500',
                'rows': 3,
                'placeholder': 'Description du cours (optionnel)'
            }),
            'file': forms.ClearableFileInput(attrs={
                'class': 'block w-full text-sm text-gray-700 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100'
            }),
            'is_public': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 text-blue-600 focus:ring-blue-500'
            }),
        }

    def clean_file(self):
        uploaded = self.cleaned_data['file']
        allowed = [
            'application/pdf', 
            'text/plain',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',  # DOCX
            'application/msword'  # DOC
        ]
        if uploaded.content_type not in allowed:
            raise forms.ValidationError('Format autorisé: PDF, TXT, DOCX ou DOC')
        if uploaded.size > 10 * 1024 * 1024:
            raise forms.ValidationError('Fichier trop volumineux (max 10MB)')
        return uploaded


