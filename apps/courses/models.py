import uuid
from django.db import models
from django.conf import settings
from django.utils.text import slugify


class Course(models.Model):
    """Course model for managing classes"""
    
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='courses',
        limit_choices_to={'role': 'TEACHER'}
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.code})"
    
    def save(self, *args, **kwargs):
        # Generate a unique course code if not provided
        if not self.code:
            base_code = slugify(self.name)[:10].upper()
            unique_id = str(uuid.uuid4())[:12]
            self.code = f"{base_code}-{unique_id}"
        super().save(*args, **kwargs)
    
    @property
    def student_count(self):
        """Return the number of students enrolled in this course"""
        return self.enrollments.filter(is_active=True).count()


class CourseEnrollment(models.Model):
    """Model for tracking student enrollments in courses"""
    
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='enrollments'
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='enrollments',
        limit_choices_to={'role': 'STUDENT'}
    )
    enrollment_date = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['course', 'student']
        ordering = ['-enrollment_date']
    
    def __str__(self):
        return f"{self.student.get_full_name()} enrolled in {self.course.name}"
