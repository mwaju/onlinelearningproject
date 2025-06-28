from django.shortcuts import redirect, render, get_object_or_404
from django.http import Http404
from django.utils import timezone
from rest_framework import viewsets, status, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import filters
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import ListView, DetailView, TemplateView, CreateView
from django.views.generic.edit import UpdateView
from django.core.paginator import Paginator
import requests
from django.conf import settings
from django.db.models import Avg
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib.auth import get_user_model

from .models import Course, Module, Lesson, Enrollment, Category
from .serializers import (
    CourseSerializer, CourseCreateSerializer,
    ModuleSerializer, LessonSerializer,
    EnrollmentSerializer
)
from .services import (
    CourseService, ModuleService,
    LessonService, EnrollmentService
)


class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ['title', 'description']
    ordering_fields = ['price', 'created_at']

    def get_queryset(self):
        queryset = super().get_queryset()
        if 'ordering' in self.request.query_params:
            ordering = self.request.query_params['ordering']
            if ordering == 'rating':
                return queryset.annotate(avg_rating=Avg('ratings__rating')).order_by('-avg_rating')
        return queryset

    def get_serializer_class(self):
        if self.action == 'create':
            return CourseCreateSerializer
        return CourseSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return super().get_permissions()

    def perform_create(self, serializer):
        course = CourseService.create_course(
            instructor=self.request.user,
            **serializer.validated_data
        )
        return course

    @action(detail=True, methods=['post'])
    def enroll(self, request, pk=None):
        course = self.get_object()
        enrollment = EnrollmentService.enroll_student(course, request.user)
        return Response(
            EnrollmentSerializer(enrollment).data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        course = self.get_object()
        stats = CourseService.get_course_stats(course)
        return Response(stats)

    @action(detail=False, methods=['get'])
    def popular(self, request):
        courses = CourseService.get_popular_courses()
        serializer = self.get_serializer(courses, many=True)
        return Response(serializer.data)

class ModuleViewSet(viewsets.ModelViewSet):
    queryset = Module.objects.all()
    serializer_class = ModuleSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Module.objects.filter(course__instructor=self.request.user)

    def perform_create(self, serializer):
        course_id = self.request.data.get('course')
        course = Course.objects.get(id=course_id)
        if course.instructor != self.request.user:
            raise permissions.PermissionDenied()
        module = ModuleService.create_module(course, **serializer.validated_data)
        return module

    @action(detail=False, methods=['post'])
    def reorder(self, request):
        course_id = request.data.get('course')
        module_order = request.data.get('module_order', [])
        course = Course.objects.get(id=course_id)
        if course.instructor != request.user:
            raise permissions.PermissionDenied()
        ModuleService.reorder_modules(course, module_order)
        return Response(status=status.HTTP_200_OK)

class LessonViewSet(viewsets.ModelViewSet):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Lesson.objects.filter(module__course__instructor=self.request.user)

    def perform_create(self, serializer):
        module_id = self.request.data.get('module')
        module = Module.objects.get(id=module_id)
        if module.course.instructor != self.request.user:
            raise permissions.PermissionDenied()
        lesson = LessonService.create_lesson(module, **serializer.validated_data)
        return lesson

    @action(detail=False, methods=['post'])
    def reorder(self, request):
        module_id = request.data.get('module')
        lesson_order = request.data.get('lesson_order', [])
        module = Module.objects.get(id=module_id)
        if module.course.instructor != request.user:
            raise permissions.PermissionDenied()
        LessonService.reorder_lessons(module, lesson_order)
        return Response(status=status.HTTP_200_OK)

class EnrollmentViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Enrollment.objects.all()
    serializer_class = EnrollmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Enrollment.objects.filter(student=self.request.user)

    @action(detail=True, methods=['post'])
    def update_progress(self, request, pk=None):
        enrollment = self.get_object()
        progress = request.data.get('progress', 0)
        enrollment = EnrollmentService.update_progress(enrollment, progress)
        return Response(
            EnrollmentSerializer(enrollment).data,
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['get'])
    def progress_details(self, request, pk=None):
        enrollment = self.get_object()
        progress = EnrollmentService.get_student_progress(enrollment)
        return Response(progress)

# Template Rendering Views
class CourseListView(ListView):
    model = Course
    template_name = 'courses/course_list.html'
    context_object_name = 'courses'
    paginate_by = 9

    def get_queryset(self):
        # Get filter parameters
        search = self.request.GET.get('search', '')
        category = self.request.GET.get('category', '')
        level = self.request.GET.get('level', '')
        price = self.request.GET.get('price', '')
        rating = self.request.GET.get('rating', '')
        duration = self.request.GET.getlist('duration', [])

        # Build API URL with filters
        api_url = f"{settings.API_BASE_URL}/courses/"
        params = {
            'search': search,
            'category': category,
            'level': level,
            'price': price,
            'rating': rating,
            'duration': duration,
            'page': self.request.GET.get('page', 1)
        }

        # Make API request
        response = requests.get(api_url, params=params)
        if response.status_code == 200:
            return response.json()
        return []

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get categories for filter
        categories_response = requests.get(f"{settings.API_BASE_URL}/categories/")
        if categories_response.status_code == 200:
            context['categories'] = categories_response.json()
        return context

class CourseDetailView(DetailView):
    model = Course
    template_name = 'courses/course_detail.html'
    context_object_name = 'course'
    slug_url_kwarg = 'slug'
    slug_field = 'slug'

    def get_object(self):
        # Get course from API
        slug = self.kwargs.get('slug')
        if not slug:
            raise Http404("Course not found")
            
        try:
            # First try to get the course by ID or slug directly from the database
            try:
                course = Course.objects.get(slug=slug)
                return course
            except (Course.DoesNotExist, ValueError):
                pass
                
            # If not found in DB, try the API
            headers = {}
            if hasattr(self.request, 'user') and self.request.user.is_authenticated:
                from rest_framework_simplejwt.tokens import AccessToken
                token = AccessToken.for_user(self.request.user)
                headers = {'Authorization': f'Bearer {str(token)}'}
            
            # Try direct course endpoint first
            response = requests.get(
                f"{settings.API_BASE_URL}/courses/{slug}/",
                headers=headers
            )
            
            # If direct endpoint fails, try the list endpoint with filter
            if response.status_code != 200:
                response = requests.get(
                    f"{settings.API_BASE_URL}/courses/?slug={slug}",
                    headers=headers
                )
                if response.status_code == 200 and response.json().get('results'):
                    course_data = response.json()['results'][0]
                else:
                    raise Http404("Course not found")
            else:
                course_data = response.json()
            
            # Ensure we have a valid slug
            if not course_data.get('slug'):
                course_data['slug'] = slug
                
            # Create a Course instance from the API data
            course = Course(
                id=course_data.get('id'),
                title=course_data.get('title', 'Untitled Course'),
                slug=course_data.get('slug', slug),
                description=course_data.get('description', ''),
                price=float(course_data.get('price', 0)),
                duration=course_data.get('duration', '0 hours'),
                level=course_data.get('level', 'beginner'),
                is_published=course_data.get('is_published', False),
                created_at=course_data.get('created_at', timezone.now()),
                updated_at=course_data.get('updated_at', timezone.now())
            )
            
            # Set the instructor if available
            instructor_data = course_data.get('instructor', {}) or {}
            if instructor_data and 'id' in instructor_data:
                try:
                    course.instructor = get_user_model().objects.get(id=instructor_data['id'])
                    # Store instructor data for template
                    course._instructor_data = instructor_data
                except (get_user_model().DoesNotExist, ValueError):
                    course.instructor = None
            
            # Set the category if available
            category_data = course_data.get('category', {}) or {}
            if category_data and 'id' in category_data:
                try:
                    course.category = Category.objects.get(id=category_data['id'])
                except (Category.DoesNotExist, ValueError):
                    course.category = None
            
            # Handle thumbnail
            if course_data.get('thumbnail'):
                course._thumbnail_url = course_data['thumbnail']
            
            # Try to save the course to DB for future lookups
            try:
                course.save()
            except Exception as e:
                print(f"Warning: Could not save course to database: {e}")
                
            return course
            
        except requests.RequestException as e:
            print(f"API request failed: {e}")
            # Try to get from DB as fallback
            try:
                return Course.objects.get(slug=slug)
            except (Course.DoesNotExist, ValueError):
                raise Http404("Course not found")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course = self.object
        
        # Ensure course has a slug
        if not hasattr(course, 'slug') or not course.slug:
            course.slug = self.kwargs.get('slug')
        
        # Get enrollment status for authenticated users
        if self.request.user.is_authenticated:
            enrollment = Enrollment.objects.filter(
                student=self.request.user,
                course=course
            ).first()
            if enrollment:
                context['enrollment'] = enrollment
        
        # Add thumbnail URL to context if available
        if hasattr(course, '_thumbnail_url'):
            context['thumbnail_url'] = course._thumbnail_url
            
        # Add instructor data to context
        if hasattr(course, '_instructor_data'):
            context['instructor_data'] = course._instructor_data
        
        # Get course modules and lessons
        try:
            response = requests.get(
                f"{settings.API_BASE_URL}/courses/{course.id}/modules/"
            )
            if response.status_code == 200:
                modules = response.json()
                # Store modules in context
                context['modules'] = modules
                
                # For the "What You'll Learn" section, use the first few modules
                if modules:
                    context['learning_objectives'] = [module['title'] for module in modules[:4]]
                    
        except Exception as e:
            print(f"Error fetching course modules: {str(e)}")
            context['modules'] = []
            context['learning_objectives'] = []
            
        return context

@login_required
def course_learn_view(request, slug):
    # Get course details
    course_response = requests.get(
        f"{settings.API_BASE_URL}/courses/{slug}/",
        headers={'Authorization': f'Bearer {request.session.get("access_token")}'}
    )
    if course_response.status_code != 200:
        return redirect('courses:course_list')

    course = course_response.json()

    # Get current lesson
    lesson_id = request.GET.get('lesson')
    if not lesson_id:
        # Get first lesson
        modules_response = requests.get(
            f"{settings.API_BASE_URL}/courses/{slug}/modules/",
            headers={'Authorization': f'Bearer {request.session.get("access_token")}'}
        )
        if modules_response.status_code == 200:
            modules = modules_response.json()
            if modules and modules[0]['lessons']:
                lesson_id = modules[0]['lessons'][0]['id']

    # Get lesson details
    lesson_response = requests.get(
        f"{settings.API_BASE_URL}/lessons/{lesson_id}/",
        headers={'Authorization': f'Bearer {request.session.get("access_token")}'}
    )
    if lesson_response.status_code != 200:
        return redirect('courses:course_list')

    lesson = lesson_response.json()

    # Get progress
    progress_response = requests.get(
        f"{settings.API_BASE_URL}/enrollments/progress/",
        params={'course': course['id']},
        headers={'Authorization': f'Bearer {request.session.get("access_token")}'}
    )
    progress = progress_response.json() if progress_response.status_code == 200 else {'percentage': 0}

    context = {
        'course': course,
        'current_lesson': lesson,
        'progress': progress
    }
    return render(request, 'courses/course_learn.html', context)

@login_required
def course_discussions_view(request, slug):
    # Get course details
    course_response = requests.get(
        f"{settings.API_BASE_URL}/courses/{slug}/",
        headers={'Authorization': f'Bearer {request.session.get("access_token")}'}
    )
    if course_response.status_code != 200:
        return redirect('course_list')

    course = course_response.json()

    # Get discussions
    discussions_response = requests.get(
        f"{settings.API_BASE_URL}/discussions/",
        params={'course': course['id']},
        headers={'Authorization': f'Bearer {request.session.get("access_token")}'}
    )
    discussions = discussions_response.json() if discussions_response.status_code == 200 else []

    # Get progress
    progress_response = requests.get(
        f"{settings.API_BASE_URL}/enrollments/progress/",
        params={'course': course['id']},
        headers={'Authorization': f'Bearer {request.session.get("access_token")}'}
    )
    progress = progress_response.json() if progress_response.status_code == 200 else {'percentage': 0}

    context = {
        'course': course,
        'discussions': discussions,
        'progress': progress
    }
    return render(request, 'courses/course_discussions.html', context)

@login_required
def discussion_detail_view(request, slug, discussion_id):
    # Get course details
    course_response = requests.get(
        f"{settings.API_BASE_URL}/courses/{slug}/",
        headers={'Authorization': f'Bearer {request.session.get("access_token")}'}
    )
    if course_response.status_code != 200:
        return redirect('course_list')

    course = course_response.json()

    # Get discussion details
    discussion_response = requests.get(
        f"{settings.API_BASE_URL}/discussions/{discussion_id}/with_comments/",
        headers={'Authorization': f'Bearer {request.session.get("access_token")}'}
    )
    if discussion_response.status_code != 200:
        return redirect('course_discussions', slug=slug)

    discussion = discussion_response.json()

    # Get progress
    progress_response = requests.get(
        f"{settings.API_BASE_URL}/enrollments/progress/",
        params={'course': course['id']},
        headers={'Authorization': f'Bearer {request.session.get("access_token")}'}
    )
    progress = progress_response.json() if progress_response.status_code == 200 else {'percentage': 0}

    context = {
        'course': course,
        'discussion': discussion,
        'progress': progress
    }
    return render(request, 'courses/discussion_detail.html', context)

class StudentDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'courses/student_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get all enrollments for the user with related course data
        enrollments = Enrollment.objects.filter(
            student=user
        ).select_related('course__instructor').prefetch_related(
            'course__modules'
        ).order_by('-enrolled_at')
        
        # Separate into active and completed courses
        active_enrollments = [e for e in enrollments if not e.completed]
        completed_enrollments = [e for e in enrollments if e.completed]
        
        # Prepare course data with progress
        enrolled_courses = []
        completed_courses = []
        course_progress = {}
        
        # Process active enrollments
        for enrollment in active_enrollments:
            course = enrollment.course
            total_modules = course.modules.count()
            completed_modules = int((enrollment.progress / 100) * total_modules) if total_modules > 0 else 0
            
            course_progress[course.id] = {
                'progress': enrollment.progress,
                'completed_modules': completed_modules,
                'total_modules': total_modules
            }
            
            # Add course to enrolled courses if not already added
            if not any(c['course'].id == course.id for c in enrolled_courses):
                enrolled_courses.append({
                    'course': course,
                    'enrollment': enrollment,
                    'progress': enrollment.progress
                })
        
        # Process completed enrollments
        for enrollment in completed_enrollments:
            course = enrollment.course
            if not any(c['course'].id == course.id for c in completed_courses):
                completed_courses.append({
                    'course': course,
                    'completed_at': enrollment.completed_at,
                    'enrollment': enrollment
                })
        
        # Sort enrolled courses by enrollment date (newest first)
        enrolled_courses.sort(key=lambda x: x['enrollment'].enrolled_at, reverse=True)
        
        # Prepare course lists
        enrolled_courses_list = [{
            'course': e['course'],
            'enrollment': e['enrollment'],
            'progress': e['progress']
        } for e in enrolled_courses]
        
        completed_courses_list = [{
            'course': c['course'],
            'enrollment': c['enrollment'],
            'completed_at': c['completed_at']
        } for c in completed_courses]
        
        # Calculate statistics
        total_courses = len(enrolled_courses) + len(completed_courses)
        in_progress_count = len(enrolled_courses)
        completed_count = len(completed_courses)
        
        context.update({
            'enrolled_courses': [e['course'] for e in enrolled_courses],
            'completed_courses': [c['course'] for c in completed_courses],
            'enrollments': enrolled_courses_list + completed_courses_list,
            'course_progress': course_progress,
            'total_courses': total_courses,
            'in_progress_count': in_progress_count,
            'completed_count': completed_count
        })
        return context

class InstructorDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'courses/instructor_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get instructor's courses
        courses = Course.objects.filter(instructor=user).select_related('instructor')
        
        # Get course statistics
        course_stats = {}
        total_revenue = 0
        total_students = 0
        
        for course in courses:
            enrollments = Enrollment.objects.filter(course=course)
            students_count = enrollments.count()
            revenue = sum(enrollment.payment.amount for enrollment in enrollments if hasattr(enrollment, 'payment'))
            
            course_stats[course.id] = {
                'students_count': students_count,
                'revenue': revenue,
                'avg_rating': course.ratings.aggregate(Avg('rating'))['rating__avg'] or 0
            }
            
            total_revenue += revenue
            total_students += students_count
        
        context.update({
            'courses': courses,
            'course_stats': course_stats,
            'total_courses': courses.count(),
            'total_students': total_students,
            'total_revenue': total_revenue
        })
        return context

class CourseCreateView(LoginRequiredMixin, CreateView):
    model = Course
    template_name = 'courses/course_form.html'
    fields = ['title', 'description', 'category', 'level', 'price', 'thumbnail']
    success_url = reverse_lazy('courses:instructor_dashboard')

    def form_valid(self, form):
        form.instance.instructor = self.request.user
        form.instance.is_published = False
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create New Course'
        context['button_text'] = 'Create Course'
        return context


class CourseUpdateView(LoginRequiredMixin, UpdateView):
    model = Course
    template_name = 'courses/course_form.html'
    fields = ['title', 'description', 'category', 'level', 'price', 'thumbnail', 'is_published']
    slug_url_kwarg = 'slug'
    slug_field = 'slug'
    context_object_name = 'course'

    def get_queryset(self):
        # Only allow instructors to edit their own courses
        return Course.objects.filter(instructor=self.request.user)
    
    def get_success_url(self):
        return reverse_lazy('courses:instructor_dashboard')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Edit Course'
        context['button_text'] = 'Update Course'
        return context

def enroll_course(request, slug):
    # Redirect unauthenticated users to registration page with next parameter
    if not request.user.is_authenticated:
        messages.info(request, 'Please register or log in to enroll in this course.')
        register_url = f"{reverse('users:register')}?next={reverse('courses:enroll_course', kwargs={'slug': slug})}"
        return redirect(register_url)
    try:
        # First try to get the course by slug from local database
        course = Course.objects.get(slug=slug)
    except Course.DoesNotExist:
        # Fall back to API if course not found locally
        try:
            response = requests.get(f"{settings.API_BASE_URL}/courses/?slug={slug}")
            response.raise_for_status()
            course_data = response.json().get('results', [None])[0]
            if not course_data:
                raise Course.DoesNotExist
            # Try to get course by title if slug doesn't match
            course = Course.objects.get(title=course_data['title'])
        except (requests.RequestException, (IndexError, KeyError), Course.DoesNotExist) as e:
            messages.error(request, 'Course not found or could not be loaded.')
            return redirect('courses:course_list')
    
    # Ensure user is logged in (redundant check but safe)
    if not request.user.is_authenticated:
        return redirect('users:login')
        
    # Prevent instructors from enrolling in courses
    if request.user.is_instructor:
        messages.warning(request, 'Instructors cannot enroll in courses as students.')
        return redirect('courses:course_detail', slug=course.slug)
    
    # Check if already enrolled (completed or not)
    existing_enrollment = Enrollment.objects.filter(
        student=request.user,
        course=course
    ).first()
    
    if existing_enrollment:
        if not existing_enrollment.completed:
            messages.info(request, 'You are already enrolled in this course.')
            return redirect('courses:course_learn', slug=course.slug)
        else:
            # If completed, allow re-enrolling
            existing_enrollment.completed = False
            existing_enrollment.save()
            messages.info(request, 'Welcome back! You have been re-enrolled in this course.')
            return redirect('courses:course_learn', slug=course.slug)
    
    # Handle enrollment for GET requests (show confirmation page)
    if request.method != 'POST':
        return render(request, 'courses/enroll_confirm.html', {'course': course})
    
    # Process enrollment for POST requests
    try:
        enrollment = EnrollmentService.enroll_student(course, request.user)
        messages.success(request, 'Successfully enrolled in the course!')
        return redirect('courses:student_dashboard')
    except Exception as e:
        messages.error(request, f'Error enrolling in course: {str(e)}')
        return redirect('courses:course_detail', slug=course.slug)
