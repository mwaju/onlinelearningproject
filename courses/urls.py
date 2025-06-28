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


router = DefaultRouter()
router.register('courses', CourseViewSet)
router.register('modules', ModuleViewSet)
router.register('lessons', LessonViewSet)
router.register('enrollments', EnrollmentViewSet, basename='enrollment')

# API URLs
api_urlpatterns = [
    # Existing course URLs
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

app_name = 'onlinelearning'

# Template URLs
template_urlpatterns = [
    path('', include(api_urlpatterns)),
    
    # Course URLs
    path('', CourseListView.as_view(), name='course_list'),
    path('create/', CourseCreateView.as_view(), name='course_create'),
    path('<slug:slug>/edit/', CourseUpdateView.as_view(), name='course_edit'),
    path('<slug:slug>/', CourseDetailView.as_view(), name='course_detail'),
    path('<slug:slug>/enroll/', enroll_course, name='enroll_course'),
    path('<slug:slug>/learn/', course_learn_view, name='course_learn'),
    path('<slug:slug>/discussions/', course_discussions_view, name='course_discussions'),
    path('<slug:slug>/discussions/<int:discussion_id>/', discussion_detail_view, name='discussion_detail'),
    
    # Student Dashboard
    path('student/dashboard/', StudentDashboardView.as_view(), name='student_dashboard'),
    path('my-courses/', CourseListView.as_view(template_name='courses/my_courses.html'), name='my_courses'),
]

urlpatterns = template_urlpatterns