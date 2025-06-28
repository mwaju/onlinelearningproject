from django.shortcuts import render
from django.views.generic import TemplateView
from django.db.models import Count
from courses.models import Course
from users.models import User

# Create your views here.

class HomeView(TemplateView):
    template_name = 'home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get 6 most popular courses by counting enrollments
        context['popular_courses'] = Course.objects.annotate(
            enrollment_count=Count('enrollments')
        ).order_by('-enrollment_count')[:6]
        # Get testimonials (you can add a Testimonial model later)
        context['testimonials'] = []  # Placeholder for testimonials
        return context

class AboutView(TemplateView):
    template_name = 'core/about.html'

class ContactView(TemplateView):
    template_name = 'core/contact.html'

class PrivacyView(TemplateView):
    template_name = 'core/privacy.html'

class TermsView(TemplateView):
    template_name = 'core/terms.html'
