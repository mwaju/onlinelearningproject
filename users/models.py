from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.mail import send_mail
from django.conf import settings

class User(AbstractUser):
    email = models.EmailField(_('email address'), unique=True)
    is_instructor = models.BooleanField(default=False)
    is_email_verified = models.BooleanField(default=False)
    email_verification_token = models.CharField(max_length=100, null=True, blank=True)
    password_reset_token = models.CharField(max_length=100, null=True, blank=True)
    bio = models.TextField(max_length=500, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    phone_number = models.CharField(max_length=15, blank=True)
    address = models.TextField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Override username field to use email as the unique identifier
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.username

    def get_short_name(self):
        return self.first_name or self.username

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')


class InstructorApplication(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='instructor_applications'
    )
    resume = models.FileField(upload_to='instructor_applications/resumes/')
    cover_letter = models.TextField(
        help_text='Tell us why you want to become an instructor and your teaching experience.'
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='pending'
    )
    applied_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    admin_notes = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.user.get_full_name()}'s Application ({self.get_status_display()})"
    
    def approve(self, admin_notes=''):
        self.status = 'approved'
        self.reviewed_at = timezone.now()
        self.admin_notes = admin_notes
        self.user.is_instructor = True
        self.user.save()
        self.save()
        # Send approval email
        self._send_status_update_email()
    
    def reject(self, admin_notes=''):
        self.status = 'rejected'
        self.reviewed_at = timezone.now()
        self.admin_notes = admin_notes
        self.save()
        # Send rejection email
        self._send_status_update_email()
    
    def _send_status_update_email(self):
        subject = f"Instructor Application {self.get_status_display().lower()}"
        message = (
            f"Hello {self.user.get_full_name()},\n\n"
            f"Your instructor application has been {self.get_status_display().lower()}.\n"
        )
        
        if self.status == 'approved':
            message += "\nCongratulations! You are now an instructor. You can now create and manage courses."
        elif self.status == 'rejected':
            message += "\nWe appreciate your interest in becoming an instructor. "
            message += "Unfortunately, we cannot approve your application at this time."
            if self.admin_notes:
                message += f"\n\nNotes: {self.admin_notes}"
        
        message += "\n\nThank you for your interest in teaching with us!"
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [self.user.email],
            fail_silently=True,
        )
    
    class Meta:
        ordering = ['-applied_at']
        verbose_name = 'Instructor Application'
        verbose_name_plural = 'Instructor Applications'
