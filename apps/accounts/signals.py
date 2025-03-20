from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, Profile

# This file will contain signal handlers for the accounts app
# We'll add actual signal handlers when we implement the User model 

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create a Profile instance when a new User is created"""
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Save the Profile instance when the User is saved"""
    instance.profile.save() 