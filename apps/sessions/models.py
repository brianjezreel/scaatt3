from django.db import models
from django.conf import settings
from django.utils import timezone
from apps.courses.models import Course
from utils.qr_generator import generate_session_token, calculate_expiry_time


class Session(models.Model):
    """Model for course sessions with QR code generation"""
    
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='sessions'
    )
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    qr_code_token = models.CharField(max_length=100, unique=True, blank=True)
    qr_expiry_time = models.DateTimeField(blank=True, null=True)
    is_closed = models.BooleanField(default=False, help_text="Whether the session has been manually closed by the teacher")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date', '-start_time']
    
    def __str__(self):
        return f"{self.title} - {self.course.name} ({self.date})"
    
    def save(self, *args, **kwargs):
        # Generate a token if not provided
        if not self.qr_code_token:
            self.qr_code_token = generate_session_token()
        
        # Set expiry time if not provided
        if not self.qr_expiry_time:
            self.qr_expiry_time = calculate_expiry_time(duration_seconds=10)
        
        super().save(*args, **kwargs)
    
    @property
    def is_active(self):
        """Check if the session is currently active"""
        if self.is_closed:
            return False
            
        now = timezone.now()
        session_date = timezone.make_aware(
            timezone.datetime.combine(self.date, self.start_time)
        )
        session_end = timezone.make_aware(
            timezone.datetime.combine(self.date, self.end_time)
        )
        return session_date <= now <= session_end
    
    @property
    def is_upcoming(self):
        """Check if the session is upcoming"""
        now = timezone.now()
        session_date = timezone.make_aware(
            timezone.datetime.combine(self.date, self.start_time)
        )
        return now < session_date
    
    @property
    def is_past(self):
        """Check if the session is in the past"""
        now = timezone.now()
        session_end = timezone.make_aware(
            timezone.datetime.combine(self.date, self.end_time)
        )
        return now > session_end
    
    @property
    def qr_is_valid(self):
        """Check if the QR code is still valid"""
        if self.is_closed:
            return False
            
        now = timezone.now()
        return now <= self.qr_expiry_time if self.qr_expiry_time else False
    
    def refresh_qr_code(self, duration_seconds=10):
        """Generate a new QR code token and update expiry time"""
        self.qr_code_token = generate_session_token()
        self.qr_expiry_time = calculate_expiry_time(duration_seconds)
        self.save()
    
    def get_attendance_count(self):
        """Get the number of students who have marked attendance"""
        return self.attendances.count()
    
    def get_enrolled_count(self):
        """Get the number of students enrolled in the course"""
        return self.course.enrollments.filter(is_active=True).count()
    
    def get_attendance_percentage(self):
        """Calculate the attendance percentage"""
        enrolled = self.get_enrolled_count()
        if enrolled == 0:
            return 0
        return (self.get_attendance_count() / enrolled) * 100
    
    @property
    def attendance_code(self):
        """Generate a simple code for manual attendance entry"""
        return f"{self.id}-{self.qr_code_token}"
