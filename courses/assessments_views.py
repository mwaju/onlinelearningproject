from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.generics import (
    ListCreateAPIView, RetrieveUpdateDestroyAPIView,
    get_object_or_404, ListAPIView, RetrieveAPIView
)
from django.utils import timezone
from django.db import transaction

from .models import (
    Assignment, Quiz, Question, Choice,
    AssignmentSubmission, QuizSubmission, QuizAnswer, Course, Enrollment
)
from .assessments_serializers import (
    AssignmentSerializer, QuizSerializer, QuestionSerializer,
    ChoiceSerializer, QuizSubmissionSerializer, AssignmentSubmissionSerializer,
    AssignmentGradingSerializer, QuizGradingSerializer, QuizAnswerSerializer
)

# Assignment Views
class AssignmentListCreateView(ListCreateAPIView):
    serializer_class = AssignmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        course_id = self.request.query_params.get('course_id')
        if course_id:
            return Assignment.objects.filter(course_id=course_id)
        return Assignment.objects.filter(course__instructor=self.request.user)

    def perform_create(self, serializer):
        course_id = self.request.data.get('course')
        course = get_object_or_404(Course, id=course_id)
        if course.instructor != self.request.user:
            self.permission_denied(self.request)
        serializer.save()

class AssignmentDetailView(RetrieveUpdateDestroyAPIView):
    queryset = Assignment.objects.all()
    serializer_class = AssignmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'

    def get_queryset(self):
        if self.request.user.is_staff:
            return Assignment.objects.all()
        return Assignment.objects.filter(course__instructor=self.request.user)

# Quiz Views
class QuizListCreateView(ListCreateAPIView):
    serializer_class = QuizSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        course_id = self.request.query_params.get('course_id')
        if course_id:
            return Quiz.objects.filter(course_id=course_id, is_published=True)
        return Quiz.objects.filter(course__instructor=self.request.user)

    def perform_create(self, serializer):
        course_id = self.request.data.get('course')
        course = get_object_or_404(Course, id=course_id)
        if course.instructor != self.request.user:
            self.permission_denied(self.request)
        serializer.save()

class QuizDetailView(RetrieveUpdateDestroyAPIView):
    queryset = Quiz.objects.all()
    serializer_class = QuizSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'

    def get_queryset(self):
        if self.request.user.is_staff:
            return Quiz.objects.all()
        return Quiz.objects.filter(course__instructor=self.request.user)

# Question and Choice Views
class QuestionListCreateView(ListCreateAPIView):
    serializer_class = QuestionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        quiz_id = self.request.query_params.get('quiz_id')
        assignment_id = self.request.query_params.get('assignment_id')
        
        if quiz_id:
            return Question.objects.filter(quiz_id=quiz_id)
        elif assignment_id:
            return Question.objects.filter(assignment_id=assignment_id)
        return Question.objects.none()

    def perform_create(self, serializer):
        quiz_id = self.request.data.get('quiz')
        assignment_id = self.request.data.get('assignment')
        
        if quiz_id:
            quiz = get_object_or_404(Quiz, id=quiz_id)
            if quiz.course.instructor != self.request.user:
                self.permission_denied(self.request)
            serializer.save(question_type='quiz')
        elif assignment_id:
            assignment = get_object_or_404(Assignment, id=assignment_id)
            if assignment.course.instructor != self.request.user:
                self.permission_denied(self.request)
            serializer.save(question_type='assignment')
        else:
            self.permission_denied(self.request)

class QuestionDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = QuestionSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'

    def get_queryset(self):
        if self.request.user.is_staff:
            return Question.objects.all()
        return Question.objects.filter(
            models.Q(quiz__course__instructor=self.request.user) |
            models.Q(assignment__course__instructor=self.request.user)
        )

# Assignment Submission Views
class AssignmentSubmissionListCreateView(ListCreateAPIView):
    serializer_class = AssignmentSubmissionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        assignment_id = self.request.query_params.get('assignment_id')
        if assignment_id:
            return AssignmentSubmission.objects.filter(assignment_id=assignment_id)
        return AssignmentSubmission.objects.filter(student=self.request.user)

    def perform_create(self, serializer):
        assignment_id = self.request.data.get('assignment')
        assignment = get_object_or_404(Assignment, id=assignment_id)
        
        # Check if student is enrolled in the course
        if not Enrollment.objects.filter(
            student=self.request.user,
            course=assignment.course,
            completed_at__isnull=True
        ).exists():
            self.permission_denied(self.request, message="You are not enrolled in this course.")
        
        # Check for existing submission
        existing_submission = AssignmentSubmission.objects.filter(
            assignment=assignment,
            student=self.request.user
        ).first()
        
        if existing_submission:
            # Update existing submission
            for attr, value in serializer.validated_data.items():
                setattr(existing_submission, attr, value)
            existing_submission.save()
            self.instance = existing_submission
        else:
            # Create new submission
            serializer.save(student=self.request.user)

class AssignmentSubmissionDetailView(RetrieveAPIView):
    serializer_class = AssignmentSubmissionSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'

    def get_queryset(self):
        if self.request.user.is_staff:
            return AssignmentSubmission.objects.all()
        return AssignmentSubmission.objects.filter(student=self.request.user)

class AssignmentGradingView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, submission_id):
        submission = get_object_or_404(AssignmentSubmission, id=submission_id)
        
        # Check if user is the course instructor
        if submission.assignment.course.instructor != request.user and not request.user.is_staff:
            return Response(
                {"detail": "You don't have permission to grade this assignment."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = AssignmentGradingSerializer(data=request.data)
        if serializer.is_valid():
            submission.grade = serializer.validated_data['grade']
            submission.feedback = serializer.validated_data.get('feedback', '')
            submission.graded_at = timezone.now()
            submission.graded_by = request.user
            submission.save()
            
            return Response(AssignmentSubmissionSerializer(submission).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Quiz Submission Views
class QuizSubmissionListCreateView(ListCreateAPIView):
    serializer_class = QuizSubmissionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        quiz_id = self.request.query_params.get('quiz_id')
        if quiz_id:
            return QuizSubmission.objects.filter(quiz_id=quiz_id)
        return QuizSubmission.objects.filter(student=self.request.user)

    def create(self, request, *args, **kwargs):
        quiz_id = request.data.get('quiz')
        quiz = get_object_or_404(Quiz, id=quiz_id)
        
        # Check if student is enrolled in the course
        if not Enrollment.objects.filter(
            student=request.user,
            course=quiz.course,
            completed_at__isnull=True
        ).exists():
            return Response(
                {"detail": "You are not enrolled in this course."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if quiz is available
        if not quiz.is_available() and not request.user.is_staff:
            return Response(
                {"detail": "This quiz is not currently available."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check for existing submission
        existing_submission = QuizSubmission.objects.filter(
            quiz=quiz,
            student=request.user
        ).first()
        
        if existing_submission and not request.user.is_staff:
            return Response(
                {"detail": "You have already submitted this quiz."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create new submission
        submission = QuizSubmission.objects.create(
            quiz=quiz,
            student=request.user,
            end_time=timezone.now() + timezone.timedelta(minutes=quiz.time_limit)
        )
        
        # Create empty answers for all questions
        for question in quiz.questions.all():
            answer = QuizAnswer.objects.create(
                submission=submission,
                question=question
            )
            if question.question_format in [Question.MULTIPLE_CHOICE, Question.TRUE_FALSE]:
                answer.selected_choices.set(question.choices.filter(is_correct=True))
        
        serializer = self.get_serializer(submission)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class QuizSubmissionDetailView(RetrieveAPIView):
    serializer_class = QuizSubmissionSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'

    def get_queryset(self):
        if self.request.user.is_staff:
            return QuizSubmission.objects.all()
        return QuizSubmission.objects.filter(student=self.request.user)

class QuizAnswerUpdateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request, answer_id):
        answer = get_object_or_404(QuizAnswer, id=answer_id)
        
        # Check if the answer belongs to the user
        if answer.submission.student != request.user:
            return Response(
                {"detail": "You don't have permission to update this answer."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if the quiz submission is still active
        if answer.submission.end_time and timezone.now() > answer.submission.end_time:
            return Response(
                {"detail": "Time's up! You can no longer submit answers for this quiz."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = QuizAnswerSerializer(answer, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            
            # Update time spent
            answer.submission.time_spent = (timezone.now() - answer.submission.start_time).total_seconds()
            answer.submission.save()
            
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class QuizSubmissionCompleteView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, submission_id):
        submission = get_object_or_404(QuizSubmission, id=submission_id)
        
        # Check if the submission belongs to the user
        if submission.student != request.user:
            return Response(
                {"detail": "You don't have permission to complete this submission."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if already completed
        if submission.is_completed:
            return Response(
                {"detail": "This quiz has already been submitted."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Mark as completed
        submission.is_completed = True
        submission.end_time = timezone.now()
        submission.time_spent = (submission.end_time - submission.start_time).total_seconds()
        
        # Calculate score
        submission.score = submission.calculate_score()
        submission.save()
        
        return Response(QuizSubmissionSerializer(submission).data)

class QuizGradingView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, answer_id):
        answer = get_object_or_404(QuizAnswer, id=answer_id)
        
        # Check if user is the course instructor
        if answer.submission.quiz.course.instructor != request.user and not request.user.is_staff:
            return Response(
                {"detail": "You don't have permission to grade this answer."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = QuizGradingSerializer(data=request.data)
        if serializer.is_valid():
            answer.points_earned = serializer.validated_data['points_earned']
            answer.feedback = serializer.validated_data.get('feedback', '')
            answer.is_correct = answer.points_earned >= (answer.question.points * 0.5)  # 50% or more is correct
            answer.save()
            
            # Update submission score
            submission = answer.submission
            submission.score = submission.calculate_score()
            submission.save()
            
            return Response(QuizAnswerSerializer(answer).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
