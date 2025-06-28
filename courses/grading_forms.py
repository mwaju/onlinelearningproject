from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from .models import AssignmentSubmission, QuizAnswer, Question


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
    """
    A dynamic form for grading quiz questions.
    """
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
    
    def save(self):
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
        # Add any additional validation if needed
        return cleaned_data
    
    def save(self):
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
            submission.graded_by = self.user
            submission.save()
            
            updated_count += 1
        
        return updated_count
