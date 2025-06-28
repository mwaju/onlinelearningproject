from django.urls import path
from .instructor_views import (
    instructor_dashboard, assignment_list, assignment_detail, grade_assignment,
    quiz_list, quiz_detail, grade_quiz_question, student_submission_detail,
    create_assignment, create_quiz, add_question, delete_question,
    publish_quiz, duplicate_quiz, download_submissions, regrade_submission,
    delete_submission, bulk_grade_assignments, bulk_grade_quizzes
)

app_name = 'instructor'

urlpatterns = [
    # Dashboard
    path('', instructor_dashboard, name='instructor_dashboard'),
    
    # Assignments
    path('assignments/', assignment_list, name='assignment_list'),
    path('assignments/create/', create_assignment, name='create_assignment'),
    path('assignments/<int:course_id>/create/', create_assignment, name='create_assignment_for_course'),
    path('assignments/<int:assignment_id>/', assignment_detail, name='assignment_detail'),
    path('assignments/<int:assignment_id>/grade/', grade_assignment, name='grade_assignment'),
    path('assignments/<int:assignment_id>/grade/<int:submission_id>/', grade_assignment, name='grade_assignment_submission'),
    path('assignments/bulk-grade/', bulk_grade_assignments, name='bulk_grade_assignments'),
    path('assignments/<int:assignment_id>/download/', download_submissions, name='download_submissions'),
    
    # Quizzes
    path('quizzes/', quiz_list, name='quiz_list'),
    path('quizzes/create/', create_quiz, name='create_quiz'),
    path('quizzes/<int:course_id>/create/', create_quiz, name='create_quiz_for_course'),
    path('quizzes/<int:quiz_id>/', quiz_detail, name='quiz_detail'),
    path('quizzes/<int:quiz_id>/publish/', publish_quiz, name='publish_quiz'),
    path('quizzes/<int:quiz_id>/duplicate/', duplicate_quiz, name='duplicate_quiz'),
    
    # Quiz Questions
    path('quizzes/<int:quiz_id>/questions/add/', add_question, name='add_question'),
    path('quizzes/<int:quiz_id>/questions/<int:question_id>/edit/', add_question, name='edit_question'),
    path('quizzes/questions/<int:question_id>/delete/', delete_question, name='delete_question'),
    
    # Grading
    path('quizzes/<int:quiz_id>/grade/', grade_quiz_question, {'question_id': 'all'}, name='grade_quiz'),
    path('quizzes/<int:quiz_id>/grade/ungraded/', grade_quiz_question, {'question_id': 'ungraded'}, name='grade_ungraded_questions'),
    path('quizzes/<int:quiz_id>/grade/<str:question_id>/', grade_quiz_question, name='grade_quiz_question'),
    path('quizzes/<int:quiz_id>/grade/<str:question_id>/<int:submission_id>/', grade_quiz_question, name='grade_quiz_question_submission'),
    path('quizzes/bulk-grade/', bulk_grade_quizzes, name='bulk_grade_quizzes'),
    
    # Submissions
    path('submissions/<int:submission_id>/', student_submission_detail, name='student_submission_detail'),
    path('submissions/<int:submission_id>/regrade/', regrade_submission, name='regrade_submission'),
    path('submissions/<int:submission_id>/delete/', delete_submission, name='delete_submission'),
]
