from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from django.utils.crypto import get_random_string
from django.db.models import Count, Sum, Avg
from courses.models import Course, Enrollment
import secrets

User = get_user_model()

class UserService:
    @staticmethod
    def create_user(data):
        """Create a new user with the given data."""
        # Generate a unique username if not provided
        if 'username' not in data or not data['username']:
            base_username = data['email'].split('@')[0]
            username = base_username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1
            data['username'] = username

        user = User.objects.create_user(
            username=data['username'],
            email=data['email'],
            password=data['password'],
            first_name=data.get('first_name', ''),
            last_name=data.get('last_name', ''),
            is_instructor=data.get('is_instructor', False)
        )
        return user

    @staticmethod
    def update_user_profile(user, **data):
        """Update user profile information."""
        for field, value in data.items():
            if hasattr(user, field):
                setattr(user, field, value)
        user.save()
        return user

    @staticmethod
    def send_password_reset_email(email):
        """Send a password reset email to the user."""
        try:
            user = User.objects.get(email=email)
            token = UserService.generate_password_reset_token(user)
            # TODO: Send email with reset link
            return True
        except User.DoesNotExist:
            return False

    @staticmethod
    def generate_password_reset_token(user):
        """Generate a password reset token for the user."""
        token = secrets.token_urlsafe(32)
        user.password_reset_token = token
        user.save()
        return token

    @staticmethod
    def verify_email(user):
        user.is_email_verified = True
        user.email_verification_token = None
        user.save()

    @staticmethod
    def get_instructor_stats(user):
        """Get statistics for an instructor user."""
        courses = Course.objects.filter(instructor=user)
        total_courses = courses.count()
        total_students = Enrollment.objects.filter(course__in=courses).count()
        total_revenue = sum(
            enrollment.payment.amount 
            for enrollment in Enrollment.objects.filter(course__in=courses)
            if hasattr(enrollment, 'payment')
        )
        
        # Calculate average rating
        total_rating = sum(
            course.ratings.aggregate(Avg('rating'))['rating__avg'] or 0 
            for course in courses
        )
        avg_rating = total_rating / total_courses if total_courses > 0 else 0
        
        return {
            'total_courses': total_courses,
            'total_students': total_students,
            'total_revenue': total_revenue,
            'average_rating': round(avg_rating, 2)
        }

    @staticmethod
    def get_student_stats(user):
        """Get statistics for a student user."""
        enrollments = Enrollment.objects.filter(student=user)
        total_courses = enrollments.count()
        completed_courses = enrollments.filter(completed=True).count()
        in_progress_courses = enrollments.filter(completed=False).count()
        
        # Calculate average progress
        total_progress = sum(enrollment.progress for enrollment in enrollments)
        avg_progress = total_progress / total_courses if total_courses > 0 else 0
        
        return {
            'total_courses': total_courses,
            'completed_courses': completed_courses,
            'in_progress_courses': in_progress_courses,
            'average_progress': round(avg_progress, 2)
        } 