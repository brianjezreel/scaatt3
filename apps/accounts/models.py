from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from .managers import UserManager


class User(AbstractUser):
    """Custom User model with role-based authentication"""
    
    class Role(models.TextChoices):
        TEACHER = 'TEACHER', _('Teacher')
        STUDENT = 'STUDENT', _('Student')
    
    email = models.EmailField(_('email address'), unique=True)
    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.STUDENT,
    )
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']
    
    objects = UserManager()
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"
    
    @property
    def is_teacher(self):
        return self.role == self.Role.TEACHER
    
    @property
    def is_student(self):
        return self.role == self.Role.STUDENT


class Profile(models.Model):
    """Extended profile information for users"""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    bio = models.TextField(blank=True)
    phone_number = models.CharField(max_length=15, blank=True)
    
    def __str__(self):
        return f"Profile for {self.user.get_full_name()}"
