from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator
from django.views.generic import ListView, DetailView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin

from .models import (
    Course, Assignment, AssignmentSubmission, 
    Enrollment, Quiz, QuizSubmission
)
from .forms import AssignmentSubmissionForm


@login_required
def student_assignments_view(request):
    """View for students to see all their assignments across enrolled courses"""
    
    # Get all enrollments for the student
    enrollments = Enrollment.objects.filter(
        student=request.user,
        completed_at__isnull=True  # Only active enrollments
    ).select_related('course')
    
    # Get all assignments from enrolled courses
    assignments = Assignment.objects.filter(
        course__in=[enrollment.course for enrollment in enrollments]
    ).select_related('course', 'module').prefetch_related('submissions')
    
    # Add submission status for each assignment
    for assignment in assignments:
        submission = assignment.submissions.filter(student=request.user).first()
        assignment.student_submission = submission
        assignment.is_submitted = submission is not None
        assignment.is_graded = submission and submission.graded_at is not None
        assignment.is_late = assignment.due_date < timezone.now()
        if submission:
            assignment.submission_is_late = submission.submitted_at > assignment.due_date
    
    # Filter by status
    status_filter = request.GET.get('status', 'all')
    if status_filter == 'pending':
        assignments = [a for a in assignments if not a.is_submitted]
    elif status_filter == 'submitted':
        assignments = [a for a in assignments if a.is_submitted and not a.is_graded]
    elif status_filter == 'graded':
        assignments = [a for a in assignments if a.is_graded]
    elif status_filter == 'late':
        assignments = [a for a in assignments if a.is_late and not a.is_submitted]
    
    # Filter by course
    course_filter = request.GET.get('course', '')
    if course_filter:
        assignments = [a for a in assignments if str(a.course.id) == course_filter]
    
    # Sort assignments
    sort_by = request.GET.get('sort', 'due_date')
    if sort_by == 'due_date':
        assignments = sorted(assignments, key=lambda x: x.due_date)
    elif sort_by == 'course':
        assignments = sorted(assignments, key=lambda x: x.course.title)
    elif sort_by == 'status':
        assignments = sorted(assignments, key=lambda x: (x.is_submitted, x.is_graded))
    
    # Pagination
    paginator = Paginator(assignments, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'assignments': page_obj,
        'enrollments': enrollments,
        'status_filter': status_filter,
        'course_filter': course_filter,
        'sort_by': sort_by,
    }
    
    return render(request, 'courses/student_assignments.html', context)


@login_required
def assignment_detail_view(request, assignment_id):
    """View for students to see assignment details and submit their work"""
    
    assignment = get_object_or_404(
        Assignment.objects.select_related('course', 'module'),
        id=assignment_id
    )
    
    # Check if student is enrolled in the course
    enrollment = get_object_or_404(
        Enrollment,
        student=request.user,
        course=assignment.course,
        completed_at__isnull=True
    )
    
    # Get or create submission
    submission, created = AssignmentSubmission.objects.get_or_create(
        assignment=assignment,
        student=request.user,
        defaults={
            'submission_text': '',
            'submission_file': None
        }
    )
    
    # Check if assignment is past due
    is_past_due = assignment.due_date < timezone.now()
    submission_is_late = submission.submitted_at and submission.submitted_at > assignment.due_date
    
    if request.method == 'POST':
        form = AssignmentSubmissionForm(request.POST, request.FILES, instance=submission)
        if form.is_valid():
            submission = form.save(commit=False)
            
            # If this is a new submission (not just updating)
            if not submission.submitted_at:
                submission.submitted_at = timezone.now()
                
                # Check if submission is late
                if submission.submitted_at > assignment.due_date:
                    # Automatically grade as F for late submission
                    submission.grade = 0
                    submission.feedback = "Assignment submitted after the deadline. Automatic grade: F"
                    submission.graded_at = timezone.now()
                    messages.warning(request, 'Assignment submitted late. Automatic grade: F')
                else:
                    messages.success(request, 'Assignment submitted successfully!')
            
            submission.save()
            return redirect('courses:assignment_detail', assignment_id=assignment.id)
    else:
        form = AssignmentSubmissionForm(instance=submission)
    
    context = {
        'assignment': assignment,
        'submission': submission,
        'form': form,
        'is_past_due': is_past_due,
        'submission_is_late': submission_is_late,
        'enrollment': enrollment,
    }
    
    return render(request, 'courses/student_assignment_detail.html', context)


@login_required
def student_grades_view(request):
    """View for students to see all their grades"""
    
    # Get all graded submissions
    submissions = AssignmentSubmission.objects.filter(
        student=request.user,
        graded_at__isnull=False
    ).select_related('assignment__course', 'assignment__module')
    
    # Get quiz submissions
    quiz_submissions = QuizSubmission.objects.filter(
        student=request.user,
        is_completed=True
    ).select_related('quiz__course')
    
    # Calculate statistics
    total_assignments = submissions.count()
    total_quizzes = quiz_submissions.count()
    
    if total_assignments > 0:
        avg_assignment_grade = sum(s.grade for s in submissions) / total_assignments
    else:
        avg_assignment_grade = 0
    
    if total_quizzes > 0:
        avg_quiz_grade = sum(s.score for s in quiz_submissions) / total_quizzes
    else:
        avg_quiz_grade = 0
    
    # Group by course
    course_grades = {}
    for submission in submissions:
        course = submission.assignment.course
        if course not in course_grades:
            course_grades[course] = {
                'assignments': [],
                'quizzes': [],
                'avg_assignment_grade': 0,
                'avg_quiz_grade': 0
            }
        course_grades[course]['assignments'].append(submission)
    
    for submission in quiz_submissions:
        course = submission.quiz.course
        if course not in course_grades:
            course_grades[course] = {
                'assignments': [],
                'quizzes': [],
                'avg_assignment_grade': 0,
                'avg_quiz_grade': 0
            }
        course_grades[course]['quizzes'].append(submission)
    
    # Calculate averages per course
    for course, data in course_grades.items():
        if data['assignments']:
            data['avg_assignment_grade'] = sum(s.grade for s in data['assignments']) / len(data['assignments'])
        if data['quizzes']:
            data['avg_quiz_grade'] = sum(s.score for s in data['quizzes']) / len(data['quizzes'])
    
    context = {
        'submissions': submissions,
        'quiz_submissions': quiz_submissions,
        'course_grades': course_grades,
        'total_assignments': total_assignments,
        'total_quizzes': total_quizzes,
        'avg_assignment_grade': avg_assignment_grade,
        'avg_quiz_grade': avg_quiz_grade,
    }
    
    return render(request, 'courses/student_grades.html', context)


@login_required
def submission_detail_view(request, submission_id):
    """View for students to see their submission details and feedback"""
    
    submission = get_object_or_404(
        AssignmentSubmission.objects.select_related('assignment__course', 'graded_by'),
        id=submission_id,
        student=request.user
    )
    
    context = {
        'submission': submission,
        'assignment': submission.assignment,
    }
    
    return render(request, 'courses/student_submission_detail.html', context)


@login_required
@require_POST
def delete_submission_view(request, submission_id):
    """Allow students to delete their submission if it's not graded and not past due"""
    
    submission = get_object_or_404(
        AssignmentSubmission,
        id=submission_id,
        student=request.user
    )
    
    # Check if submission can be deleted
    if submission.graded_at:
        messages.error(request, 'Cannot delete a graded submission.')
        return redirect('courses:assignment_detail', assignment_id=submission.assignment.id)
    
    if submission.assignment.due_date < timezone.now():
        messages.error(request, 'Cannot delete submission after the deadline.')
        return redirect('courses:assignment_detail', assignment_id=submission.assignment.id)
    
    # Delete the submission
    submission.delete()
    messages.success(request, 'Submission deleted successfully.')
    
    return redirect('courses:assignment_detail', assignment_id=submission.assignment.id) 