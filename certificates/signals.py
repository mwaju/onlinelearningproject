from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import Certificate

@receiver(post_save, sender=get_user_model())
def create_welcome_certificate(sender, instance, created, **kwargs):
    """
    Create a welcome certificate for new users
    """
    if created:
        # You can add logic here to create a welcome certificate
        pass

@receiver(post_save, sender=Certificate)
def send_certificate_email(sender, instance, created, **kwargs):
    """
    Send an email notification when a new certificate is issued
    """
    if created:
        # Add email sending logic here
        pass
