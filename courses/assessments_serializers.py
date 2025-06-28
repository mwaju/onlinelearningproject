from rest_framework import serializers
from .models import (
    Assignment, Quiz, Question, Choice, 
    AssignmentSubmission, QuizSubmission, QuizAnswer
)

class ChoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Choice
        fields = ['id', 'choice_text', 'is_correct', 'order']
        read_only_fields = ['is_correct']  # Don't expose correct answers by default

class QuestionSerializer(serializers.ModelSerializer):
    choices = ChoiceSerializer(many=True, required=False)
    
    class Meta:
        model = Question
        fields = [
            'id', 'question_type', 'question_text', 'question_format',
            'points', 'order', 'choices', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

class AssignmentSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, required=False)
    is_past_due = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Assignment
        fields = [
            'id', 'title', 'description', 'course', 'module', 'due_date',
            'total_points', 'questions', 'is_past_due', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
        extra_kwargs = {
            'course': {'required': True},
            'due_date': {'required': True}
        }

class QuizSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, required=False)
    is_available = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Quiz
        fields = [
            'id', 'title', 'description', 'course', 'module', 'time_limit',
            'passing_score', 'is_published', 'available_from', 'available_until',
            'questions', 'is_available', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
        extra_kwargs = {
            'course': {'required': True},
            'available_from': {'required': True},
            'available_until': {'required': True}
        }

class QuizAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizAnswer
        fields = ['id', 'question', 'answer_text', 'selected_choices', 'is_correct', 'points_earned', 'feedback']
        read_only_fields = ['is_correct', 'points_earned', 'feedback']
        extra_kwargs = {
            'selected_choices': {'required': False}
        }

class QuizSubmissionSerializer(serializers.ModelSerializer):
    answers = QuizAnswerSerializer(many=True, required=False)
    time_remaining = serializers.SerializerMethodField()
    
    class Meta:
        model = QuizSubmission
        fields = [
            'id', 'quiz', 'student', 'start_time', 'end_time', 'score',
            'is_completed', 'time_spent', 'time_remaining', 'answers'
        ]
        read_only_fields = ['student', 'start_time', 'end_time', 'score', 'is_completed', 'time_spent']
    
    def get_time_remaining(self, obj):
        if not obj.end_time:
            return None
        return (obj.end_time - obj.start_time).total_seconds() - obj.time_spent
    
    def create(self, validated_data):
        answers_data = validated_data.pop('answers', [])
        submission = QuizSubmission.objects.create(**validated_data)
        
        for answer_data in answers_data:
            selected_choices = answer_data.pop('selected_choices', [])
            answer = QuizAnswer.objects.create(submission=submission, **answer_data)
            answer.selected_choices.set(selected_choices)
            answer.check_answer()  # Auto-grade the answer if possible
        
        # Calculate total score
        submission.score = submission.calculate_score()
        submission.save()
        return submission

class AssignmentSubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssignmentSubmission
        fields = [
            'id', 'assignment', 'student', 'submission_text', 'submission_file',
            'submitted_at', 'grade', 'feedback', 'graded_at', 'graded_by'
        ]
        read_only_fields = ['student', 'submitted_at', 'graded_at', 'graded_by', 'grade']
        extra_kwargs = {
            'submission_text': {'required': False},
            'submission_file': {'required': False}
        }
    
    def validate(self, data):
        # At least one of submission_text or submission_file must be provided
        if not data.get('submission_text') and not data.get('submission_file'):
            raise serializers.ValidationError("Either submission_text or submission_file must be provided.")
        return data

class AssignmentGradingSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssignmentSubmission
        fields = ['grade', 'feedback']
        extra_kwargs = {
            'grade': {'required': True},
            'feedback': {'required': False}
        }

class QuizGradingSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizAnswer
        fields = ['points_earned', 'feedback']
        extra_kwargs = {
            'points_earned': {'required': True},
            'feedback': {'required': False}
        }
