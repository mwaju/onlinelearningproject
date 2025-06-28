from django.shortcuts import render
from django.views.generic import TemplateView
from django.db.models import Count
from courses.models import Course
from users.models import User
from live_sessions.models import LiveSession
from discussions.models import Discussion

# Create your views here.

class HomeView(TemplateView):
    template_name = 'core/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get 6 most popular courses by counting enrollments
        context['popular_courses'] = Course.objects.filter(
            is_published=True
        ).annotate(
            enrollment_count=Count('enrollments')
        ).order_by('-enrollment_count')[:6]
        
        # Get testimonials (you can add a Testimonial model later)
        context['testimonials'] = []  # Placeholder for testimonials
        
        # Personalized content for logged-in users
        if self.request.user.is_authenticated:
            user = self.request.user
            
            # Get live sessions for user's enrolled courses
            if user.is_instructor:
                # For instructors, show their own live sessions
                context['live_sessions'] = LiveSession.objects.filter(
                    instructor=user
                ).order_by('-start_time')[:6]
            else:
                # For students, show live sessions from their enrolled courses
                enrolled_course_ids = user.enrollments.values_list('course_id', flat=True)
                context['live_sessions'] = LiveSession.objects.filter(
                    course_id__in=enrolled_course_ids
                ).order_by('-start_time')[:6]
            
            # Get recent discussions
            if user.is_instructor:
                # For instructors, show discussions from their courses
                instructor_course_ids = Course.objects.filter(
                    instructor=user
                ).values_list('id', flat=True)
                context['discussions'] = Discussion.objects.filter(
                    course_id__in=instructor_course_ids
                ).order_by('-created_at')[:6]
            else:
                # For students, show discussions from their enrolled courses
                context['discussions'] = Discussion.objects.filter(
                    course_id__in=enrolled_course_ids
                ).order_by('-created_at')[:6]
        
        return context

class AboutView(TemplateView):
    template_name = 'core/about.html'

class ContactView(TemplateView):
    template_name = 'core/contact.html'

class PrivacyView(TemplateView):
    template_name = 'core/privacy.html'

class TermsView(TemplateView):
    template_name = 'core/terms.html'
