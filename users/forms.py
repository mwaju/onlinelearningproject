from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.utils.translation import gettext_lazy as _
from .models import User, InstructorApplication

class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('email', 'username', 'first_name', 'last_name')

class CustomUserChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = User
        fields = ('email', 'username', 'first_name', 'last_name', 'is_staff', 'is_active', 'is_superuser')

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'bio', 'profile_picture', 'date_of_birth', 'phone_number', 'address']


class InstructorApplicationForm(forms.ModelForm):
    class Meta:
        model = InstructorApplication
        fields = ['resume', 'cover_letter']
        labels = {
            'resume': _('Your Resume/CV'),
            'cover_letter': _('Cover Letter')
        }
        help_texts = {
            'resume': _('Upload your resume or CV (PDF, DOC, DOCX, max 5MB)'),
            'cover_letter': _('Tell us about your teaching experience and why you want to become an instructor')
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['resume'].required = True
        self.fields['cover_letter'].required = True
        self.fields['cover_letter'].widget = forms.Textarea(attrs={
            'rows': 5,
            'placeholder': _('Please include your teaching experience, qualifications, and why you want to teach on our platform...')
        })
    
    def clean_resume(self):
        resume = self.cleaned_data.get('resume')
        if resume:
            # Validate file type
            valid_extensions = ['.pdf', '.doc', '.docx']
            ext = str(resume).lower()
            if not any(ext.endswith(ext) for ext in valid_extensions):
                raise forms.ValidationError(
                    _('Unsupported file format. Please upload a PDF, DOC, or DOCX file.')
                )
            
            # Validate file size (5MB)
            if resume.size > 5 * 1024 * 1024:
                raise forms.ValidationError(
                    _('File size must be no more than 5MB.')
                )
        return resume
