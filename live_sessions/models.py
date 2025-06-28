from django.db import models
from django.conf import settings
from courses.models import Course

class LiveSession(models.Model):
    SESSION_STATUS = (
        ('scheduled', 'Scheduled'),
        ('live', 'Live'),
        ('ended', 'Ended'),
        ('cancelled', 'Cancelled')
    )

    title = models.CharField(max_length=200)
    description = models.TextField()
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='live_sessions')
    instructor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='conducted_sessions')
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    status = models.CharField(max_length=20, choices=SESSION_STATUS, default='scheduled')
    meeting_link = models.URLField(blank=True)
    recording_url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} - {self.course.title}"

    class Meta:
        ordering = ['-start_time']

class SessionParticipant(models.Model):
    session = models.ForeignKey(LiveSession, on_delete=models.CASCADE, related_name='participants')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='attended_sessions')
    joined_at = models.DateTimeField(auto_now_add=True)
    left_at = models.DateTimeField(null=True, blank=True)
    is_presenter = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.email} - {self.session.title}"

    class Meta:
        unique_together = ['session', 'user']

class SessionChat(models.Model):
    session = models.ForeignKey(LiveSession, on_delete=models.CASCADE, related_name='chats')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='session_chats')
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Chat from {self.user.email} in {self.session.title}"

    class Meta:
        ordering = ['timestamp']
