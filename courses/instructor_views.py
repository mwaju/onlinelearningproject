from django.shortcuts import render, get_object_or_404, redirect, HttpResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Count, Avg, Q, F, Sum, Case, When, Value, IntegerField
from django.utils import timezone
from django.http import JsonResponse, HttpResponseRedirect, Http404
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.urls import reverse
from django.db import transaction
from django.views.decorators.http import require_POST
import csv
from io import StringIO

from users.models import User
from .models import (
    Course, Assignment, Quiz, AssignmentSubmission, 
    QuizSubmission, Question, Choice, Enrollment, QuizAnswer
)
from .forms import (
    AssignmentForm, QuizForm, QuestionForm, ChoiceFormSet,
    GradeAssignmentForm, GradeQuizQuestionForm, BulkGradeForm
)

@login_required
def instructor_dashboard(request):
    if not request.user.is_instructor and not request.user.is_staff:
        return redirect('home')
    
    # Get instructor's courses
    courses = Course.objects.filter(instructor=request.user)
    
    # Get recent assignments and quizzes
    recent_assignments = Assignment.objects.filter(course__in=courses).order_by('-created_at')[:5]
    recent_quizzes = Quiz.objects.filter(course__in=courses).order_by('-created_at')[:5]
    
    # Get grading stats
    grading_stats = {
        'assignments_to_grade': AssignmentSubmission.objects.filter(
            assignment__course__in=courses, 
            graded_at__isnull=True
        ).count(),
        'quizzes_to_grade': QuizAnswer.objects.filter(
            submission__quiz__course__in=courses,
            points_earned__isnull=True,
            question__question_format__in=[Question.SHORT_ANSWER, Question.ESSAY]
        ).count(),
        'average_grades': {
            'assignments': AssignmentSubmission.objects.filter(
                assignment__course__in=courses,
                graded_at__isnull=False
            ).aggregate(avg=Avg('grade'))['avg'] or 0,
            'quizzes': QuizSubmission.objects.filter(
                quiz__course__in=courses,
                is_completed=True
            ).aggregate(avg=Avg('score'))['avg'] or 0
        }
    }
    
    context = {
        'courses': courses,
        'recent_assignments': recent_assignments,
        'recent_quizzes': recent_quizzes,
        'grading_stats': grading_stats,
    }
    
    return render(request, 'instructor/dashboard.html', context)

@login_required
def assignment_list(request, course_id=None):
    if not request.user.is_instructor and not request.user.is_staff:
        return redirect('home')
    
    query = request.GET.get('q', '')
    status_filter = request.GET.get('status', 'all')
    
    assignments = Assignment.objects.filter(course__instructor=request.user)
    
    if course_id:
        course = get_object_or_404(Course, id=course_id, instructor=request.user)
        assignments = assignments.filter(course=course)
    
    if query:
        assignments = assignments.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query)
        )
    
    if status_filter == 'graded':
        assignments = assignments.annotate(
            submissions_count=Count('submissions', filter=Q(submissions__graded_at__isnull=False))
        ).filter(submissions_count__gt=0)
    elif status_filter == 'ungraded':
        assignments = assignments.annotate(
            submissions_count=Count('submissions', filter=Q(submissions__graded_at__isnull=False))
        ).filter(submissions_count=0)
    
    # Add submission counts and grading status
    assignments = assignments.annotate(
        total_submissions=Count('submissions'),
        graded_submissions=Count('submissions', filter=Q(submissions__graded_at__isnull=False))
    )
    
    context = {
        'assignments': assignments,
        'course_id': course_id,
        'query': query,
        'status_filter': status_filter,
    }
    
    return render(request, 'instructor/assignment_list.html', context)

@login_required
def assignment_detail(request, assignment_id):
    assignment = get_object_or_404(
        Assignment.objects.select_related('course'), 
        id=assignment_id, 
        course__instructor=request.user
    )
    
    submissions = AssignmentSubmission.objects.filter(
        assignment=assignment
    ).select_related('student')
    
    # Get grading statistics
    stats = {
        'total': submissions.count(),
        'graded': submissions.filter(graded_at__isnull=False).count(),
        'average': submissions.filter(graded_at__isnull=False).aggregate(avg=Avg('grade'))['avg'] or 0,
        'highest': submissions.filter(graded_at__isnull=False).order_by('-grade').first(),
        'lowest': submissions.filter(graded_at__isnull=False).order_by('grade').first(),
    }
    
    context = {
        'assignment': assignment,
        'submissions': submissions,
        'stats': stats,
    }
    
    return render(request, 'instructor/assignment_detail.html', context)

@login_required
def grade_assignment(request, assignment_id, submission_id=None):
    assignment = get_object_or_404(
        Assignment.objects.select_related('course'),
        id=assignment_id,
        course__instructor=request.user
    )
    
    # Get the specific submission or the first ungraded one
    if submission_id:
        submission = get_object_or_404(
            AssignmentSubmission.objects.select_related('student', 'assignment__course'),
            id=submission_id,
            assignment=assignment
        )
    else:
        submission = AssignmentSubmission.objects.filter(
            assignment=assignment,
            graded_at__isnull=True
        ).select_related('student').first()
        
        if not submission:
            messages.info(request, 'No ungraded submissions found.')
            return redirect('instructor:assignment_detail', assignment_id=assignment.id)
    
    # Check if submission is late and automatically graded
    is_late_submission = submission.submitted_at and submission.submitted_at > assignment.due_date
    is_auto_graded = submission.graded_at and submission.feedback and "Automatic grade: F" in submission.feedback
    
    # Get all submissions for this student and assignment
    previous_submissions = AssignmentSubmission.objects.filter(
        assignment=assignment,
        student=submission.student
    ).exclude(id=submission.id).order_by('-submitted_at')
    
    if request.method == 'POST':
        form = GradeAssignmentForm(request.POST, instance=submission)
        if form.is_valid():
            submission = form.save(commit=False)
            
            # If this is a late submission that was auto-graded, allow instructor to override
            if is_auto_graded and 'override_auto_grade' in request.POST:
                # Remove the automatic grading feedback and allow manual grading
                submission.feedback = submission.feedback.replace("Assignment submitted after the deadline. Automatic grade: F", "")
                submission.graded_at = None
                submission.graded_by = None
                submission.save()
                messages.info(request, 'Automatic grade removed. You can now provide a manual grade.')
                return redirect('instructor:grade_assignment', assignment_id=assignment.id, submission_id=submission.id)
            
            # Normal grading process
            submission.graded_at = timezone.now()
            submission.graded_by = request.user
            
            # If this is a late submission and not already auto-graded, add a note
            if is_late_submission and not is_auto_graded:
                if not submission.feedback:
                    submission.feedback = ""
                submission.feedback += f"\n\nNote: This assignment was submitted {submission.submitted_at - assignment.due_date} after the deadline."
            
            submission.save()
            
            messages.success(request, 'Assignment graded successfully.')
            
            # Check if we should go to the next ungraded submission
            if 'save_and_next' in request.POST:
                next_submission = AssignmentSubmission.objects.filter(
                    assignment=assignment,
                    graded_at__isnull=True
                ).exclude(id=submission.id).first()
                
                if next_submission:
                    return redirect('instructor:grade_assignment', 
                                 assignment_id=assignment.id, 
                                 submission_id=next_submission.id)
                else:
                    messages.info(request, 'No more ungraded submissions.')
                    return redirect('instructor:assignment_detail', assignment_id=assignment.id)
            
            return redirect('instructor:assignment_detail', assignment_id=assignment.id)
    else:
        form = GradeAssignmentForm(instance=submission)
    
    # Calculate grading progress
    total_submissions = assignment.submissions.count()
    graded_submissions = assignment.submissions.filter(graded_at__isnull=False).count()
    progress = (graded_submissions / total_submissions * 100) if total_submissions > 0 else 0
    
    context = {
        'assignment': assignment,
        'submission': submission,
        'form': form,
        'previous_submissions': previous_submissions,
        'grading_progress': {
            'total': total_submissions,
            'graded': graded_submissions,
            'percent': round(progress, 1)
        },
        'next_submission': AssignmentSubmission.objects.filter(
            assignment=assignment,
            graded_at__isnull=True
        ).exclude(id=submission.id).exists(),
        'is_late_submission': is_late_submission,
        'is_auto_graded': is_auto_graded,
        'late_duration': submission.submitted_at - assignment.due_date if is_late_submission else None,
    }
    
    return render(request, 'instructor/grade_assignment.html', context)

@login_required
def quiz_list(request, course_id=None):
    if not request.user.is_instructor and not request.user.is_staff:
        return redirect('home')
    
    query = request.GET.get('q', '')
    status_filter = request.GET.get('status', 'all')
    
    quizzes = Quiz.objects.filter(course__instructor=request.user)
    
    if course_id:
        course = get_object_or_404(Course, id=course_id, instructor=request.user)
        quizzes = quizzes.filter(course=course)
    
    if query:
        quizzes = quizzes.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query)
        )
    
    if status_filter == 'active':
        now = timezone.now()
        quizzes = quizzes.filter(
            available_from__lte=now,
            available_until__gte=now,
            is_published=True
        )
    elif status_filter == 'upcoming':
        quizzes = quizzes.filter(available_from__gt=timezone.now())
    elif status_filter == 'completed':
        quizzes = quizzes.filter(available_until__lt=timezone.now())
    elif status_filter == 'draft':
        quizzes = quizzes.filter(is_published=False)
    
    # Add submission counts
    quizzes = quizzes.annotate(
        total_submissions=Count('submissions'),
        average_score=Avg('submissions__score', filter=Q(submissions__is_completed=True))
    )
    
    context = {
        'quizzes': quizzes,
        'course_id': course_id,
        'query': query,
        'status_filter': status_filter,
    }
    
    return render(request, 'instructor/quiz_list.html', context)

@login_required
def quiz_detail(request, quiz_id):
    quiz = get_object_or_404(
        Quiz.objects.select_related('course'), 
        id=quiz_id, 
        course__instructor=request.user
    )
    
    submissions = QuizSubmission.objects.filter(
        quiz=quiz
    ).select_related('student')
    
    # Get grading statistics
    stats = {
        'total': submissions.count(),
        'completed': submissions.filter(is_completed=True).count(),
        'in_progress': submissions.filter(is_completed=False).count(),
        'average': submissions.filter(is_completed=True).aggregate(avg=Avg('score'))['avg'] or 0,
        'passing': submissions.filter(is_completed=True, score__gte=quiz.passing_score).count(),
    }
    
    # Get questions that need manual grading
    questions_needing_grading = Question.objects.filter(
        quiz=quiz,
        question_format__in=[Question.SHORT_ANSWER, Question.ESSAY]
    ).annotate(
        ungraded_answers=Count(
            'quizanswer', 
            filter=Q(quizanswer__submission__quiz=quiz, quizanswer__points_earned__isnull=True)
        )
    ).filter(ungraded_answers__gt=0)
    
    context = {
        'quiz': quiz,
        'submissions': submissions,
        'stats': stats,
        'questions_needing_grading': questions_needing_grading,
    }
    
    return render(request, 'instructor/quiz_detail.html', context)

@login_required
def grade_quiz_question(request, quiz_id, question_id, submission_id=None):
    quiz = get_object_or_404(Quiz, id=quiz_id, course__instructor=request.user)
    
    # Get all questions for this quiz
    questions = quiz.questions.all().order_by('id')
    
    # Handle special cases for question_id
    if question_id == 'all':
        # Show all questions for bulk grading
        question = None
    elif question_id == 'ungraded':
        # Find first ungraded question
        ungraded_question = questions.filter(
            answers__submission__quiz=quiz,
            answers__points_earned__isnull=True
        ).first()
        
        if ungraded_question:
            return redirect('instructor:grade_quiz_question', 
                         quiz_id=quiz.id, 
                         question_id=ungraded_question.id)
        else:
            messages.info(request, 'No ungraded questions found.')
            return redirect('instructor:quiz_detail', quiz_id=quiz.id)
    else:
        # Get the specific question
        question = get_object_or_404(Question, id=question_id, quiz=quiz)
    
    # Get the submission if provided
    submission = None
    if submission_id:
        submission = get_object_or_404(
            QuizSubmission,
            id=submission_id,
            quiz=quiz
        )
    
    # Get all answers for this question or all questions
    if question:
        answers = QuizAnswer.objects.filter(
            question=question,
            submission__quiz=quiz,
            submission__is_completed=True
        )
        
        if submission:
            answers = answers.filter(submission=submission)
        
        answers = answers.select_related('submission', 'submission__student')
        
        # Get next and previous questions for navigation
        question_index = list(questions).index(question)
        next_question = questions[question_index + 1] if question_index + 1 < len(questions) else None
        prev_question = questions[question_index - 1] if question_index > 0 else None
    else:
        # For bulk grading, get all questions with their answers
        answers = None
    
    if request.method == 'POST':
        form = GradeQuizQuestionForm(question, request.POST)
        
        if form.is_valid():
            with transaction.atomic():
                for answer in form.get_answers():
                    points = form.cleaned_data.get(f'points_{answer.id}')
                    feedback = form.cleaned_data.get(f'feedback_{answer.id}', '')
                    
                    if points is not None:
                        answer.points_earned = points
                        answer.feedback = feedback
                        answer.is_correct = (points / answer.question.points) >= 0.5
                        answer.save()
                        
                        # Update submission score
                        submission = answer.submission
                        submission.score = submission.calculate_score()
                        submission.save()
                
                messages.success(request, 'Grades saved successfully.')
                
                # Handle next button
                if 'next' in request.POST and next_question:
                    return redirect('instructor:grade_quiz_question', 
                                 quiz_id=quiz.id, 
                                 question_id=next_question.id)
                
                return redirect('instructor:grade_quiz_question', 
                             quiz_id=quiz.id, 
                             question_id=question.id)
    else:
        form = GradeQuizQuestionForm(question)
    
    # Get grading stats
    if question:
        total_answers = answers.count()
        graded_answers = answers.exclude(points_earned__isnull=True).count()
    else:
        total_answers = QuizAnswer.objects.filter(
            question__quiz=quiz,
            submission__is_completed=True
        ).count()
        
        graded_answers = QuizAnswer.objects.filter(
            question__quiz=quiz,
            submission__is_completed=True,
            points_earned__isnull=False
        ).count()
    
    progress = (graded_answers / total_answers * 100) if total_answers > 0 else 0
    
    context = {
        'quiz': quiz,
        'question': question,
        'questions': questions,
        'answers': answers,
        'form': form,
        'total_questions': questions.count(),
        'question_number': question_index + 1 if question else None,
        'next_question': next_question,
        'previous_question': prev_question,
        'submission': submission,
        'grading_progress': {
            'total': total_answers,
            'graded': graded_answers,
            'percent': round(progress, 1)
        },
    }
    
    return render(request, 'instructor/grade_quiz_question.html', context)

@login_required
def student_submission_detail(request, submission_id):
    submission = get_object_or_404(
        QuizSubmission.objects.select_related('quiz__course', 'student'),
        id=submission_id,
        quiz__course__instructor=request.user
    )
    
    # Get all answers with related questions
    answers = submission.answers.all().select_related('question')
    
    # Calculate time spent if available
    if submission.started_at and submission.submitted_at:
        time_spent = (submission.submitted_at - submission.started_at).total_seconds() / 60  # in minutes
    else:
        time_spent = None
    
    # Get all submissions by this student for this quiz
    all_submissions = QuizSubmission.objects.filter(
        quiz=submission.quiz,
        student=submission.student
    ).order_by('-submitted_at')
    
    # Calculate statistics
    total_questions = submission.quiz.questions.count()
    correct_answers = answers.filter(is_correct=True).count()
    percentage = (correct_answers / total_questions * 100) if total_questions > 0 else 0
    
    context = {
        'submission': submission,
        'answers': answers,
        'time_spent': time_spent,
        'total_questions': total_questions,
        'correct_answers': correct_answers,
        'percentage': round(percentage, 1),
        'all_submissions': all_submissions,
        'passing_score': submission.quiz.passing_score if hasattr(submission.quiz, 'passing_score') else 70,
        'is_passing': percentage >= (submission.quiz.passing_score if hasattr(submission.quiz, 'passing_score') else 70)
    }
    
    return render(request, 'instructor/student_submission_detail.html', context)

@login_required
def create_assignment(request, course_id=None):
    if course_id:
        course = get_object_or_404(Course, id=course_id, instructor=request.user)
    else:
        course = None
    
    if request.method == 'POST':
        form = AssignmentForm(request.POST, request.FILES, user=request.user, course=course)
        if form.is_valid():
            assignment = form.save(commit=False)
            if course:
                assignment.course = course
            assignment.save()
            messages.success(request, 'Assignment created successfully.')
            return redirect('instructor:assignment_detail', assignment_id=assignment.id)
    else:
        form = AssignmentForm(user=request.user, course=course)
    
    context = {
        'form': form,
        'course': course,
    }
    
    return render(request, 'instructor/assignment_form.html', context)

@login_required
def create_quiz(request, course_id=None):
    if course_id:
        course = get_object_or_404(Course, id=course_id, instructor=request.user)
    else:
        course = None
    
    if request.method == 'POST':
        form = QuizForm(request.POST, user=request.user, course=course)
        if form.is_valid():
            quiz = form.save(commit=False)
            if course:
                quiz.course = course
            quiz.save()
            messages.success(request, 'Quiz created successfully.')
            return redirect('instructor:add_question', quiz_id=quiz.id)
    else:
        form = QuizForm(user=request.user, course=course)
    
    context = {
        'form': form,
        'course': course,
    }
    
    return render(request, 'instructor/quiz_form.html', context)

@login_required
def add_question(request, quiz_id, question_id=None):
    quiz = get_object_or_404(Quiz, id=quiz_id, course__instructor=request.user)
    
    if question_id:
        question = get_object_or_404(Question, id=question_id, quiz=quiz)
    else:
        question = Question(quiz=quiz, question_type='quiz')
    
    if request.method == 'POST':
        form = QuestionForm(request.POST, instance=question)
        formset = ChoiceFormSet(request.POST, instance=question)
        
        if form.is_valid() and formset.is_valid():
            question = form.save(commit=False)
            question.quiz = quiz
            question.save()
            
            formset.save()
            
            # Handle correct answers for multiple choice/true-false
            if question.question_format in [Question.MULTIPLE_CHOICE, Question.TRUE_FALSE]:
                correct_choices = request.POST.getlist('correct_choices')
                question.choices.all().update(is_correct=False)
                question.choices.filter(id__in=correct_choices).update(is_correct=True)
            
            messages.success(request, 'Question saved successfully.')
            
            if 'add_another' in request.POST:
                return redirect('instructor:add_question', quiz_id=quiz.id)
            else:
                return redirect('instructor:quiz_detail', quiz_id=quiz.id)
    else:
        form = QuestionForm(instance=question)
        formset = ChoiceFormSet(instance=question)
    
    context = {
        'form': form,
        'formset': formset,
        'quiz': quiz,
        'question': question,
    }
    
    return render(request, 'instructor/question_form.html', context)

@login_required
def delete_question(request, question_id):
    question = get_object_or_404(Question, id=question_id, quiz__course__instructor=request.user)
    quiz_id = question.quiz.id
    question.delete()
    messages.success(request, 'Question deleted successfully.')
    return redirect('instructor:quiz_detail', quiz_id=quiz_id)

@login_required
def publish_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id, course__instructor=request.user)
    quiz.is_published = True
    quiz.save()
    messages.success(request, 'Quiz published successfully.')
    return redirect('instructor:quiz_detail', quiz_id=quiz_id)

@login_required
def duplicate_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id, course__instructor=request.user)
    
    # Duplicate the quiz
    quiz.pk = None
    quiz.title = f"{quiz.title} (Copy)"
    quiz.is_published = False
    quiz.save()
    
    # Duplicate questions and choices
    for question in Question.objects.filter(quiz_id=quiz_id):
        choices = list(question.choices.all())
        question.pk = None
        question.quiz = quiz
        question.save()
        
        for choice in choices:
            choice.pk = None
            choice.question = question
            choice.save()
    
    messages.success(request, 'Quiz duplicated successfully.')
    return redirect('instructor:quiz_detail', quiz_id=quiz.id)

@login_required
@require_POST
def delete_quiz(request, quiz_id):
    """
    Delete a quiz and all its associated data.
    """
    quiz = get_object_or_404(Quiz, id=quiz_id, course__instructor=request.user)
    
    quiz_title = quiz.title
    quiz.delete()
    
    messages.success(request, f'Quiz "{quiz_title}" deleted successfully.')
    return redirect('instructor:quiz_list')

@login_required
@require_POST
def regrade_submission(request, submission_id):
    """
    Regrade a quiz submission, recalculating scores for auto-graded questions.
    """
    submission = get_object_or_404(
        QuizSubmission.objects.select_related('quiz'),
        id=submission_id,
        quiz__course__instructor=request.user
    )
    
    clear_existing = request.POST.get('clear_existing', 'true').lower() == 'true'
    
    with transaction.atomic():
        # Clear existing grades if requested
        if clear_existing:
            submission.answers.all().update(
                points_earned=None,
                is_correct=None,
                feedback='',
                graded_at=None,
                graded_by=None
            )
        
        # Recalculate scores for auto-graded questions
        updated_count = 0
        for answer in submission.answers.all():
            if answer.question.question_format in [Question.MULTIPLE_CHOICE, Question.TRUE_FALSE]:
                # For auto-gradable questions, recalculate the score
                answer.points_earned = answer.calculate_score()
                answer.is_correct = (answer.points_earned / answer.question.points) >= 0.5
                answer.graded_at = timezone.now()
                answer.graded_by = request.user
                answer.save()
                updated_count += 1
        
        # Update submission score
        submission.score = submission.calculate_score()
        submission.save()
    
    messages.success(request, f'Regraded {updated_count} questions.')
    return redirect('instructor:student_submission_detail', submission_id=submission.id)


@require_POST
def delete_submission(request, submission_id):
    """
    Delete a quiz submission.
    """
    submission = get_object_or_404(
        QuizSubmission,
        id=submission_id,
        quiz__course__instructor=request.user
    )
    
    quiz_id = submission.quiz_id
    submission.delete()
    
    messages.success(request, 'Submission deleted successfully.')
    return redirect('instructor:quiz_detail', quiz_id=quiz_id)


def bulk_grade_assignments(request):
    """
    Bulk grade multiple assignments at once.
    """
    if not request.user.is_instructor and not request.user.is_staff:
        return redirect('home')
    
    course_id = request.GET.get('course_id')
    assignment_id = request.GET.get('assignment_id')
    
    # Get assignments to grade
    assignments = Assignment.objects.filter(
        course__instructor=request.user
    ).select_related('course')
    
    if course_id:
        assignments = assignments.filter(course_id=course_id)
    
    if assignment_id:
        assignments = assignments.filter(id=assignment_id)
    
    # Get submissions that need grading
    submissions = AssignmentSubmission.objects.filter(
        assignment__in=assignments,
        graded_at__isnull=True
    ).select_related('assignment', 'student')
    
    # Apply filters
    if course_id:
        submissions = submissions.filter(assignment__course_id=course_id)
    if assignment_id:
        submissions = submissions.filter(assignment_id=assignment_id)
    
    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(submissions, 25)  # Show 25 submissions per page
    
    try:
        submissions_page = paginator.page(page)
    except PageNotAnInteger:
        submissions_page = paginator.page(1)
    except EmptyPage:
        submissions_page = paginator.page(paginator.num_pages)
    
    # Get courses for filter dropdown
    courses = Course.objects.filter(instructor=request.user)
    
    context = {
        'submissions': submissions_page,
        'courses': courses,
        'selected_course': int(course_id) if course_id else None,
        'selected_assignment': int(assignment_id) if assignment_id else None,
    }
    
    return render(request, 'instructor/bulk_grade_assignments.html', context)


def bulk_grade_quizzes(request):
    """
    Bulk grade multiple quiz questions at once.
    """
    if not request.user.is_instructor and not request.user.is_staff:
        return redirect('home')
    
    course_id = request.GET.get('course_id')
    quiz_id = request.GET.get('quiz_id')
    
    # Get quizzes to grade
    quizzes = Quiz.objects.filter(
        course__instructor=request.user
    ).select_related('course')
    
    if course_id:
        quizzes = quizzes.filter(course_id=course_id)
    if quiz_id:
        quizzes = quizzes.filter(id=quiz_id)
    
    # Get questions that need grading
    questions = Question.objects.filter(
        quiz__in=quizzes,
        quizanswer__points_earned__isnull=True
    ).distinct()
    
    # Apply filters
    if course_id:
        questions = questions.filter(quiz__course_id=course_id)
    if quiz_id:
        questions = questions.filter(quiz_id=quiz_id)
    
    # Get the number of ungraded answers per question
    questions = questions.annotate(
        ungraded_count=Count('quizanswer', filter=Q(quizanswer__points_earned__isnull=True))
    ).filter(ungraded_count__gt=0)
    
    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(questions, 25)  # Show 25 questions per page
    
    try:
        questions_page = paginator.page(page)
    except PageNotAnInteger:
        questions_page = paginator.page(1)
    except EmptyPage:
        questions_page = paginator.page(paginator.num_pages)
    
    # Get courses for filter dropdown
    courses = Course.objects.filter(instructor=request.user)
    
    context = {
        'questions': questions_page,
        'courses': courses,
        'selected_course': int(course_id) if course_id else None,
        'selected_quiz': int(quiz_id) if quiz_id else None,
        'total_ungraded': sum(q.ungraded_count for q in questions_page.object_list)
    }
    
    return render(request, 'instructor/bulk_grade_quizzes.html', context)


def download_submissions(request, assignment_id):
    assignment = get_object_or_404(Assignment, id=assignment_id, course__instructor=request.user)
    
    # Create a CSV file in memory
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="submissions_{assignment_id}_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    # Create the CSV writer with Excel dialect for better compatibility
    writer = csv.writer(response, dialect='excel')
    
    # Write the header row
    headers = [
        'Student ID',
        'Student Name',
        'Email',
        'Submission Date',
        'Status',
        'Grade',
        'Max Grade',
        'Percentage',
        'Feedback',
        'Graded By',
        'Graded At',
        'Late Submission',
        'Submission Notes'
    ]
    
    writer.writerow(headers)
    
    # Get all submissions with related data
    submissions = AssignmentSubmission.objects.filter(
        assignment=assignment
    ).select_related('student', 'graded_by')
    
    # Write submission data
    for submission in submissions:
        is_late = submission.is_late if hasattr(submission, 'is_late') else False
        late_minutes = submission.late_minutes if hasattr(submission, 'late_minutes') else 0
        
        writer.writerow([
            submission.student.id,
            submission.student.get_full_name() or submission.student.username,
            submission.student.email,
            submission.submitted_at.strftime('%Y-%m-%d %H:%M:%S') if submission.submitted_at else 'Not submitted',
            'Graded' if submission.graded_at else 'Pending',
            submission.grade if submission.grade is not None else '',
            assignment.total_points,
            f"{(submission.grade / assignment.total_points * 100):.1f}%" if submission.grade is not None else '',
            submission.feedback or '',
            submission.graded_by.get_full_name() if submission.graded_by else '',
            submission.graded_at.strftime('%Y-%m-%d %H:%M:%S') if submission.graded_at else '',
            'Yes' if is_late else 'No',
            f"{late_minutes} minutes late" if is_late else 'On time',
            submission.notes or ''
        ])
    
    return response
