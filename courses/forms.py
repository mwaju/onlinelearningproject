from django import forms
from django.forms import inlineformset_factory
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from .models import Course, Module, Lesson, Assignment, Quiz, Question, AssignmentSubmission, QuizSubmission, QuizAnswer, Choice


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['title', 'description', 'thumbnail', 'category', 'level', 'is_published']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }


class ModuleForm(forms.ModelForm):
    class Meta:
        model = Module
        fields = ['title', 'description', 'order', 'course']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'course': forms.HiddenInput(),
            'order': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
        }


class LessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = ['title', 'content', 'video_url', 'duration', 'order']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 5, 'class': 'ckeditor'}),
            'video_url': forms.URLInput(attrs={'class': 'form-control'}),
            'duration': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set appropriate widget attributes
        self.fields['title'].widget.attrs.update({'class': 'form-control'})
        self.fields['order'].widget.attrs.update({'class': 'form-control', 'min': 0})


class AssignmentForm(forms.ModelForm):
    class Meta:
        model = Assignment
        fields = ['title', 'description', 'course', 'module', 'due_date', 'total_points']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'due_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        course = kwargs.pop('course', None)
        super().__init__(*args, **kwargs)
        
        # Filter course choices to only show courses owned by the user
        if user:
            self.fields['course'].queryset = Course.objects.filter(instructor=user)
        
        # If a specific course is provided, set it and make the field read-only
        if course:
            self.fields['course'].initial = course
            self.fields['course'].widget = forms.HiddenInput()
            # Filter modules to only show modules from the specified course
            self.fields['module'].queryset = Module.objects.filter(course=course)
        else:
            # If no specific course, show all modules from user's courses
            if user:
                self.fields['module'].queryset = Module.objects.filter(course__instructor=user)
        
        self.fields['due_date'].input_formats = ('%Y-%m-%dT%H:%M',)
        
        # Add Bootstrap classes
        for field_name, field in self.fields.items():
            if field_name != 'course':  # Don't add classes to hidden course field
                field.widget.attrs.update({'class': 'form-control'})


class QuizForm(forms.ModelForm):
    class Meta:
        model = Quiz
        fields = ['title', 'description', 'course', 'module', 'time_limit', 'passing_score', 
                 'is_published', 'available_from', 'available_until']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'available_from': forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
            'available_until': forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        course = kwargs.pop('course', None)
        super().__init__(*args, **kwargs)
        
        # Filter course choices to only show courses owned by the user
        if user:
            self.fields['course'].queryset = Course.objects.filter(instructor=user)
        
        # If a specific course is provided, set it and make the field read-only
        if course:
            self.fields['course'].initial = course
            self.fields['course'].widget = forms.HiddenInput()
            # Filter modules to only show modules from the specified course
            self.fields['module'].queryset = Module.objects.filter(course=course)
        else:
            # If no specific course, show all modules from user's courses
            if user:
                self.fields['module'].queryset = Module.objects.filter(course__instructor=user)
        
        self.fields['available_from'].input_formats = ('%Y-%m-%dT%H:%M',)
        self.fields['available_until'].input_formats = ('%Y-%m-%dT%H:%M',)
        
        # Add Bootstrap classes
        for field_name, field in self.fields.items():
            if field_name != 'course':  # Don't add classes to hidden course field
                field.widget.attrs.update({'class': 'form-control'})


class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['question_type', 'quiz', 'assignment', 'question_text', 'question_format', 'points', 'order']
        widgets = {
            'question_text': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'quiz': forms.HiddenInput(),
            'assignment': forms.HiddenInput(),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make question_type and question_format required
        self.fields['question_type'].required = True
        self.fields['question_format'].required = True
        
        # Set appropriate widget attributes
        self.fields['points'].widget.attrs.update({'class': 'form-control', 'min': 1})
        self.fields['order'].widget.attrs.update({'class': 'form-control', 'min': 0})


class AnswerForm(forms.ModelForm):
    class Meta:
        model = QuizAnswer
        fields = ['answer_text', 'selected_choices', 'is_correct', 'points_earned', 'feedback']
        widgets = {
            'answer_text': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'feedback': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'selected_choices': forms.CheckboxSelectMultiple(),
        }
    
    def __init__(self, *args, **kwargs):
        question = kwargs.pop('question', None)
        super().__init__(*args, **kwargs)
        
        # If this is a multiple choice or true/false question, show checkboxes for choices
        if question and question.question_format in [Question.MULTIPLE_CHOICE, Question.TRUE_FALSE]:
            self.fields['selected_choices'].queryset = question.choices.all()
            self.fields['selected_choices'].required = False
            self.fields['answer_text'].widget = forms.HiddenInput()
        else:
            # For short answer and essay questions, hide the choices field
            if 'selected_choices' in self.fields:
                del self.fields['selected_choices']
        
        # Set appropriate widget attributes
        self.fields['points_earned'].widget.attrs.update({
            'class': 'form-control',
            'min': 0,
            'max': question.points if question else 100,
            'step': 0.5
        })


class AssignmentSubmissionForm(forms.ModelForm):
    class Meta:
        model = AssignmentSubmission
        fields = ['submission_text', 'submission_file']
        widgets = {
            'submission_text': forms.Textarea(attrs={'rows': 5, 'class': 'form-control'}),
            'submission_file': forms.FileInput(attrs={'class': 'form-control'}),
        }


class ChoiceForm(forms.ModelForm):
    class Meta:
        model = Choice
        fields = ['choice_text', 'is_correct', 'order']
        widgets = {
            'choice_text': forms.TextInput(attrs={'class': 'form-control'}),
            'is_correct': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'order': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
        }


# Create formset for choices
ChoiceFormSet = inlineformset_factory(
    Question,
    Choice,
    form=ChoiceForm,
    extra=1,
    can_delete=True,
    min_num=1,
    validate_min=True
)


class GradeAssignmentForm(forms.ModelForm):
    class Meta:
        model = AssignmentSubmission
        fields = ['grade', 'feedback']
        widgets = {
            'feedback': forms.Textarea(attrs={'rows': 5, 'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['grade'].widget.attrs.update({
            'class': 'form-control',
            'min': 0,
            'max': self.instance.assignment.total_points if self.instance and hasattr(self.instance, 'assignment') else 100,
            'step': '0.1',
            'required': True
        })
    
    def clean_grade(self):
        grade = self.cleaned_data.get('grade')
        if grade is not None:
            max_grade = self.instance.assignment.total_points
            if grade < 0 or grade > max_grade:
                raise ValidationError(_(f'Grade must be between 0 and {max_grade}'))
        return grade


class GradeQuizQuestionForm(forms.Form):
    """A dynamic form for grading quiz questions."""
    def __init__(self, question, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.question = question
        self.answers = self._get_answers()
        self._build_form()
    
    def _get_answers(self):
        """Get all answers that need to be graded for this question."""
        if not self.question:
            return QuizAnswer.objects.none()
            
        return QuizAnswer.objects.filter(
            question=self.question,
            points_earned__isnull=True
        ).select_related('submission', 'submission__student')
    
    def _build_form(self):
        """Dynamically add fields for each answer that needs grading."""
        for answer in self.answers:
            field_name = f'points_{answer.id}'
            feedback_name = f'feedback_{answer.id}'
            
            # Points field
            self.fields[field_name] = forms.DecimalField(
                label=f"{answer.submission.student.get_full_name() or answer.submission.student.username}",
                min_value=0,
                max_value=self.question.points,
                decimal_places=1,
                required=False,
                widget=forms.NumberInput(attrs={
                    'class': 'form-control points-input',
                    'step': '0.5',
                    'data-max-points': self.question.points
                })
            )
            
            # Feedback field
            self.fields[feedback_name] = forms.CharField(
                label=_('Feedback'),
                required=False,
                widget=forms.Textarea(attrs={
                    'class': 'form-control',
                    'rows': 2,
                    'placeholder': _('Optional feedback for the student')
                })
            )
    
    def get_answers(self):
        """Get the answers being graded by this form."""
        return self.answers
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Validate that at least one answer has points
        has_points = False
        for answer in self.answers:
            field_name = f'points_{answer.id}'
            if field_name in cleaned_data and cleaned_data[field_name] is not None:
                has_points = True
                break
        
        if not has_points and self.answers.exists():
            raise ValidationError(_('Please enter points for at least one answer.'))
        
        return cleaned_data
    
    def save(self, user):
        """
        Save the grades and feedback for all answers.
        Returns the number of answers that were updated.
        """
        updated_count = 0
        
        for answer in self.answers:
            points_field = f'points_{answer.id}'
            feedback_field = f'feedback_{answer.id}'
            
            if points_field in self.cleaned_data:
                points = self.cleaned_data[points_field]
                feedback = self.cleaned_data.get(feedback_field, '')
                
                if points is not None:
                    answer.points_earned = points
                    answer.feedback = feedback
                    answer.is_correct = (points / self.question.points) >= 0.5
                    answer.graded_at = timezone.now()
                    answer.graded_by = user
                    answer.save()
                    
                    # Update the submission's total score
                    submission = answer.submission
                    submission.score = submission.calculate_score()
                    submission.save()
                    
                    updated_count += 1
        
        return updated_count


class BulkGradeForm(forms.Form):
    """Form for bulk grading of assignments or quizzes."""
    feedback_template = forms.CharField(
        label=_('Feedback Template'),
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': _('Optional feedback that will be applied to all selected submissions. ' 
                           'You can use {student_name} and {max_points} as variables.')
        })
    )
    
    def __init__(self, *args, **kwargs):
        self.submissions = kwargs.pop('submissions', [])
        super().__init__(*args, **kwargs)
    
    def clean(self):
        cleaned_data = super().clean()
        return cleaned_data
    
    def save(self, user):
        """
        Apply the bulk grade to all selected submissions.
        Returns the number of submissions that were updated.
        """
        if not self.cleaned_data:
            return 0
            
        updated_count = 0
        feedback_template = self.cleaned_data.get('feedback_template', '')
        
        for submission in self.submissions:
            # Skip if no grade was provided for this submission
            grade_field = f'grade_{submission.id}'
            if grade_field not in self.cleaned_data:
                continue
            
            grade = self.cleaned_data[grade_field]
            if grade is None:
                continue
                
            # Format feedback with template variables
            feedback = feedback_template.format(
                student_name=submission.student.get_full_name() or submission.student.username,
                max_points=submission.assignment.total_points if hasattr(submission, 'assignment') else submission.quiz.total_points
            )
            
            # Update the submission
            submission.grade = grade
            submission.feedback = feedback
            submission.graded_at = timezone.now()
            submission.graded_by = user
            submission.save()
            
            updated_count += 1
        
        return updated_count
