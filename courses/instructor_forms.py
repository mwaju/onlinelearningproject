from django import forms
from django.forms import inlineformset_factory
from django.utils import timezone

from .models import Assignment, Quiz, Question, Choice

class AssignmentForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.course = kwargs.pop('course', None)
        super().__init__(*args, **kwargs)
        
        if self.user and not self.user.is_staff:
            self.fields['course'].queryset = self.user.instructor_courses.all()
        
        if self.course:
            self.fields['course'].initial = self.course
            self.fields['course'].widget = forms.HiddenInput()
    
    class Meta:
        model = Assignment
        fields = ['title', 'description', 'course', 'module', 'due_date', 'total_points']
        widgets = {
            'due_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
            'description': forms.Textarea(attrs={'rows': 4}),
        }
    
    def clean_due_date(self):
        due_date = self.cleaned_data.get('due_date')
        if due_date and due_date <= timezone.now():
            raise forms.ValidationError("Due date must be in the future.")
        return due_date

class QuizForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.course = kwargs.pop('course', None)
        super().__init__(*args, **kwargs)
        
        if self.user and not self.user.is_staff:
            self.fields['course'].queryset = self.user.instructor_courses.all()
        
        if self.course:
            self.fields['course'].initial = self.course
            self.fields['course'].widget = forms.HiddenInput()
    
    class Meta:
        model = Quiz
        fields = [
            'title', 'description', 'course', 'module', 
            'time_limit', 'passing_score', 'available_from', 
            'available_until'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'available_from': forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
            'available_until': forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        available_from = cleaned_data.get('available_from')
        available_until = cleaned_data.get('available_until')
        
        if available_from and available_until:
            if available_from >= available_until:
                self.add_error('available_until', 'Available until must be after available from.')
            
            if available_until <= timezone.now():
                self.add_error('available_until', 'Available until must be in the future.')
        
        return cleaned_data

class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['question_text', 'question_format', 'points', 'order']
        widgets = {
            'question_text': forms.Textarea(attrs={'rows': 3}),
            'points': forms.NumberInput(attrs={'min': 1, 'max': 100, 'step': 1}),
            'order': forms.NumberInput(attrs={'min': 1, 'step': 1}),
        }

class ChoiceForm(forms.ModelForm):
    class Meta:
        model = Choice
        fields = ['choice_text', 'is_correct', 'order']
        widgets = {
            'choice_text': forms.TextInput(attrs={'class': 'form-control'}),
            'order': forms.NumberInput(attrs={'min': 1, 'step': 1}),
        }

# Formset for choices
ChoiceFormSet = inlineformset_factory(
    Question, Choice, 
    form=ChoiceForm,
    extra=4,
    max_num=10,
    min_num=2,
    can_delete=True
)

class QuestionGradingForm(forms.Form):
    def __init__(self, *args, **kwargs):
        answers = kwargs.pop('answers', [])
        super().__init__(*args, **kwargs)
        
        for answer in answers:
            field_name = f'points_{answer.id}'
            self.fields[field_name] = forms.DecimalField(
                label=f"Points (max {answer.question.points})",
                max_digits=5,
                decimal_places=2,
                min_value=0,
                max_value=answer.question.points,
                required=True,
                initial=answer.points_earned
            )
            
            self.fields[f'feedback_{answer.id}'] = forms.CharField(
                label='Feedback',
                widget=forms.Textarea(attrs={'rows': 2}),
                required=False,
                initial=answer.feedback
            )

class AssignmentGradingForm(forms.ModelForm):
    class Meta:
        model = AssignmentSubmission
        fields = ['grade', 'feedback']
        widgets = {
            'feedback': forms.Textarea(attrs={'rows': 4}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['grade'].required = True
        self.fields['grade'].widget.attrs.update({
            'min': 0,
            'max': self.instance.assignment.total_points if self.instance else 100,
            'step': '0.01'
        })
