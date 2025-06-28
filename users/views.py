from django.shortcuts import render, redirect, reverse
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.views.generic import FormView, TemplateView, CreateView
from django.contrib import messages
from django.urls import reverse_lazy
from django.core.mail import send_mail
from django.conf import settings
from .forms import CustomUserCreationForm, UserProfileForm, InstructorApplicationForm
from .models import User, InstructorApplication
from .services import UserService

class RegisterView(FormView):
    template_name = 'users/register.html'
    form_class = CustomUserCreationForm
    success_url = '/users/login/'

    def get_success_url(self):
        # Get the 'next' parameter from the URL if it exists
        next_url = self.request.GET.get('next', '')
        # If there's a next parameter, include it in the login URL
        if next_url:
            return f"{reverse('users:login')}?next={next_url}"
        return super().get_success_url()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Pass the next URL to the template
        context['next'] = self.request.GET.get('next', '')
        return context

    def form_valid(self, form):
        user = form.save()
        # Log the user in after registration
        login(self.request, user)
        messages.success(self.request, 'Registration successful! You are now logged in.')
        
        # If there's a next parameter, redirect there after login
        next_url = self.request.POST.get('next') or self.request.GET.get('next')
        if next_url:
            return redirect(next_url)
            
        return super().form_valid(form)

    def get(self, *args, **kwargs):
        if self.request.user.is_authenticated:
            return redirect('core:home')
        return super().get(*args, **kwargs)

class LoginView(FormView):
    template_name = 'users/login.html'
    form_class = AuthenticationForm

    def get_success_url(self):
        # Get the 'next' parameter from the URL if it exists
        next_url = self.request.GET.get('next') or self.request.POST.get('next')
        if next_url:
            return next_url
        # Default redirect based on user type
        if self.request.user.is_instructor:
            return reverse('courses:instructor_dashboard')
        return reverse('courses:student_dashboard')

    def form_valid(self, form):
        user = form.get_user()
        login(self.request, user)
        messages.success(self.request, f'Welcome back, {user.username}!')
        return super().form_valid(form)

    def get(self, *args, **kwargs):
        if self.request.user.is_authenticated:
            return redirect('core:home')
        return super().get(*args, **kwargs)

class LogoutView(View):
    def get(self, request, *args, **kwargs):
        logout(request)
        return redirect('core:home')

class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'users/profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Initialize forms
        context['profile_form'] = UserProfileForm(instance=user)
        
        # Get user statistics based on role
        if user.is_instructor:
            context['stats'] = UserService.get_instructor_stats(user)
        else:
            context['stats'] = UserService.get_student_stats(user)
            
        # Add additional user context
        context.update({
            'user': user,
            'join_date': user.date_joined.strftime('%B %Y'),
            'last_login': user.last_login.strftime('%B %d, %Y') if user.last_login else 'Never',
        })
        
        return context

    def post(self, request, *args, **kwargs):
        user = request.user
        
        if 'update_profile' in request.POST:
            form = UserProfileForm(
                request.POST, 
                request.FILES, 
                instance=user
            )
            
            if form.is_valid():
                form.save()
                messages.success(request, 'Your profile has been updated successfully!')
                return redirect('users:profile')
            else:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"{field}: {error}")
        
        # Handle other form submissions here if needed
        
        return self.render_to_response(self.get_context_data())

class PasswordResetView(TemplateView):
    template_name = 'users/password_reset.html'

class PasswordResetConfirmView(TemplateView):
    template_name = 'users/password_reset_confirm.html'


class BecomeInstructorView(LoginRequiredMixin, CreateView):
    model = InstructorApplication
    form_class = InstructorApplicationForm
    template_name = 'users/become_instructor.html'
    success_url = reverse_lazy('users:profile')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['has_pending_application'] = InstructorApplication.objects.filter(
            user=self.request.user,
            status='pending'
        ).exists()
        return context
    
    def form_valid(self, form):
        if self.request.user.is_instructor:
            messages.warning(self.request, 'You are already an instructor!')
            return redirect('users:profile')
            
        # Check for pending applications
        if InstructorApplication.objects.filter(
            user=self.request.user,
            status='pending'
        ).exists():
            messages.info(self.request, 'You already have a pending application.')
            return redirect('users:profile')
            
        form.instance.user = self.request.user
        response = super().form_valid(form)
        
        # Send notification to admin
        self._send_admin_notification()
        
        messages.success(
            self.request,
            'Your application has been submitted. We will review it and get back to you soon.'
        )
        return response
    
    def _send_admin_notification(self):
        """Send email notification to admin about new instructor application"""
        subject = 'New Instructor Application Received'
        message = (
            f'User {self.request.user.get_full_name()} ({self.request.user.email}) has applied to become an instructor.\n'
            f'Please review their application in the admin panel.'
        )
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [settings.ADMIN_EMAIL],
            fail_silently=True,
        )
    
    def get(self, request, *args, **kwargs):
        if request.user.is_instructor:
            messages.info(request, 'You are already an instructor!')
            return redirect('users:profile')
        return super().get(request, *args, **kwargs)
