from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CourseViewSet, ModuleViewSet,
    LessonViewSet, EnrollmentViewSet,
    CourseListView, CourseDetailView,
    course_learn_view, course_discussions_view,
    discussion_detail_view, enroll_course,
    InstructorDashboardView, StudentDashboardView,
    CourseCreateView, CourseUpdateView
)
from .assessments_views import (
    AssignmentListCreateView, AssignmentDetailView,
    QuizListCreateView, QuizDetailView,
    QuestionListCreateView, QuestionDetailView,
    AssignmentSubmissionListCreateView, AssignmentSubmissionDetailView, AssignmentGradingView,
    QuizSubmissionListCreateView, QuizSubmissionDetailView, QuizAnswerUpdateView,
    QuizSubmissionCompleteView, QuizGradingView
)
from .instructor_views import (
    instructor_dashboard, assignment_list, assignment_detail, grade_assignment,
    quiz_list, quiz_detail, grade_quiz_question, student_submission_detail,
    create_assignment, create_quiz, add_question, delete_question,
    publish_quiz, duplicate_quiz, download_submissions, regrade_submission,
    delete_submission, bulk_grade_assignments, bulk_grade_quizzes, delete_quiz
)
from .student_views import (
    student_assignments_view, assignment_detail_view,
    student_grades_view, submission_detail_view,
    delete_submission_view
)

router = DefaultRouter()
router.register('courses', CourseViewSet)
router.register('modules', ModuleViewSet)
router.register('lessons', LessonViewSet)
router.register('enrollments', EnrollmentViewSet, basename='enrollment')

app_name = 'courses'

# API URLs
api_urlpatterns = [
    path('api/courses/', include(router.urls)),
    path('api/courses/', CourseViewSet.as_view({'get': 'list', 'post': 'create'}), name='api_course_list'),
    path('api/courses/<int:pk>/', CourseViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'patch': 'partial_update',
        'delete': 'destroy'
    }), name='api_course_detail'),
    
    # Assignment URLs
    path('api/assignments/', AssignmentListCreateView.as_view(), name='assignment-list'),
    path('api/assignments/<int:id>/', AssignmentDetailView.as_view(), name='assignment-detail'),
    
    # Quiz URLs
    path('api/quizzes/', QuizListCreateView.as_view(), name='quiz-list'),
    path('api/quizzes/<int:id>/', QuizDetailView.as_view(), name='quiz-detail'),
    
    # Question URLs
    path('api/questions/', QuestionListCreateView.as_view(), name='question-list'),
    path('api/questions/<int:id>/', QuestionDetailView.as_view(), name='question-detail'),
    
    # Assignment Submission URLs
    path('api/assignment-submissions/', AssignmentSubmissionListCreateView.as_view(), name='assignment-submission-list'),
    path('api/assignment-submissions/<int:id>/', AssignmentSubmissionDetailView.as_view(), name='assignment-submission-detail'),
    path('api/assignment-submissions/<int:submission_id>/grade/', AssignmentGradingView.as_view(), name='assignment-submission-grade'),
    
    # Quiz Submission URLs
    path('api/quiz-submissions/', QuizSubmissionListCreateView.as_view(), name='quiz-submission-list'),
    path('api/quiz-submissions/<int:id>/', QuizSubmissionDetailView.as_view(), name='quiz-submission-detail'),
    path('api/quiz-answers/<int:answer_id>/', QuizAnswerUpdateView.as_view(), name='quiz-answer-update'),
    path('api/quiz-submissions/<int:submission_id>/complete/', QuizSubmissionCompleteView.as_view(), name='quiz-submission-complete'),
    path('api/quiz-answers/<int:answer_id>/grade/', QuizGradingView.as_view(), name='quiz-answer-grade'),
]

# Instructor URLs (must come before course detail pattern)
instructor_urlpatterns = [
    path('instructor/', instructor_dashboard, name='instructor_dashboard'),
    path('instructor/assignments/', assignment_list, name='instructor_assignment_list'),
    path('instructor/assignments/create/', create_assignment, name='instructor_create_assignment'),
    path('instructor/assignments/<int:course_id>/create/', create_assignment, name='instructor_create_assignment_for_course'),
    path('instructor/assignments/<int:assignment_id>/', assignment_detail, name='instructor_assignment_detail'),
    path('instructor/assignments/<int:assignment_id>/grade/', grade_assignment, name='instructor_grade_assignment'),
    path('instructor/assignments/<int:assignment_id>/grade/<int:submission_id>/', grade_assignment, name='instructor_grade_assignment_submission'),
    path('instructor/assignments/bulk-grade/', bulk_grade_assignments, name='instructor_bulk_grade_assignments'),
    path('instructor/assignments/<int:assignment_id>/download/', download_submissions, name='instructor_download_submissions'),
    
    # Quizzes
    path('instructor/quizzes/', quiz_list, name='instructor_quiz_list'),
    path('instructor/quizzes/create/', create_quiz, name='instructor_create_quiz'),
    path('instructor/quizzes/<int:course_id>/create/', create_quiz, name='instructor_create_quiz_for_course'),
    path('instructor/quizzes/<int:quiz_id>/', quiz_detail, name='instructor_quiz_detail'),
    path('instructor/quizzes/<int:quiz_id>/publish/', publish_quiz, name='instructor_publish_quiz'),
    path('instructor/quizzes/<int:quiz_id>/duplicate/', duplicate_quiz, name='instructor_duplicate_quiz'),
    path('instructor/quizzes/<int:quiz_id>/delete/', delete_quiz, name='instructor_delete_quiz'),
    
    # Quiz Questions
    path('instructor/quizzes/<int:quiz_id>/questions/add/', add_question, name='instructor_add_question'),
    path('instructor/quizzes/<int:quiz_id>/questions/<int:question_id>/edit/', add_question, name='instructor_edit_question'),
    path('instructor/quizzes/questions/<int:question_id>/delete/', delete_question, name='instructor_delete_question'),
    
    # Grading
    path('instructor/quizzes/<int:quiz_id>/grade/', grade_quiz_question, {'question_id': 'all'}, name='instructor_grade_quiz'),
    path('instructor/quizzes/<int:quiz_id>/grade/ungraded/', grade_quiz_question, {'question_id': 'ungraded'}, name='instructor_grade_ungraded_questions'),
    path('instructor/quizzes/<int:quiz_id>/grade/<str:question_id>/', grade_quiz_question, name='instructor_grade_quiz_question'),
    path('instructor/quizzes/<int:quiz_id>/grade/<str:question_id>/<int:submission_id>/', grade_quiz_question, name='instructor_grade_quiz_question_submission'),
    path('instructor/quizzes/bulk-grade/', bulk_grade_quizzes, name='instructor_bulk_grade_quizzes'),
    
    # Submissions
    path('instructor/submissions/<int:submission_id>/', student_submission_detail, name='instructor_student_submission_detail'),
    path('instructor/submissions/<int:submission_id>/regrade/', regrade_submission, name='instructor_regrade_submission'),
    path('instructor/submissions/<int:submission_id>/delete/', delete_submission, name='instructor_delete_submission'),
]

# Student URLs (must come before course detail pattern)
student_urlpatterns = [
    path('student/dashboard/', StudentDashboardView.as_view(), name='student_dashboard'),
    path('student/assignments/', student_assignments_view, name='student_assignments'),
    path('student/assignments/<int:assignment_id>/', assignment_detail_view, name='student_assignment_detail'),
    path('student/assignments/<int:assignment_id>/submission/<int:submission_id>/', submission_detail_view, name='student_submission_detail'),
    path('student/assignments/<int:assignment_id>/submission/<int:submission_id>/delete/', delete_submission_view, name='student_delete_submission'),
    path('student/grades/', student_grades_view, name='student_grades'),
]

# Main Course URLs (must come after specific patterns)
course_urlpatterns = [
    path('', CourseListView.as_view(), name='course_list'),
    path('create/', CourseCreateView.as_view(), name='course_create'),
    path('my-courses/', CourseListView.as_view(template_name='courses/my_courses.html'), name='my_courses'),
    path('<slug:slug>/edit/', CourseUpdateView.as_view(), name='course_edit'),
    path('<slug:slug>/enroll/', enroll_course, name='enroll_course'),
    path('<slug:slug>/learn/', course_learn_view, name='course_learn'),
    path('<slug:slug>/discussions/', course_discussions_view, name='course_discussions'),
    path('<slug:slug>/discussions/<int:discussion_id>/', discussion_detail_view, name='discussion_detail'),
    path('<slug:slug>/', CourseDetailView.as_view(), name='course_detail'),  # This must be last
]

# Combine all URL patterns in the correct order
urlpatterns = api_urlpatterns + instructor_urlpatterns + student_urlpatterns + course_urlpatterns