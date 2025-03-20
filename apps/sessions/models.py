from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from apps.courses.models import Course
from utils.qr_generator import generate_session_token, calculate_expiry_time


class CourseSchedule(models.Model):
    """Model for defining recurring course schedules"""
    
    DAYS_OF_WEEK = [
        (0, _('Monday')),
        (1, _('Tuesday')),
        (2, _('Wednesday')),
        (3, _('Thursday')),
        (4, _('Friday')),
        (5, _('Saturday')),
    ]
    
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='schedules'
    )
    day_of_week = models.IntegerField(choices=DAYS_OF_WEEK)
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['day_of_week', 'start_time']
        unique_together = ['course', 'day_of_week', 'start_time']
    
    def __str__(self):
        return f"{self.course.name} - {self.get_day_of_week_display()} {self.start_time.strftime('%I:%M %p')}"
    
    def clean(self):
        # Check that end time is after start time
        if self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValidationError({"end_time": _("End time must be after start time.")})


class Session(models.Model):
    """Model for course sessions with QR code generation"""
    
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='sessions'
    )
    schedule = models.ForeignKey(
        CourseSchedule,
        on_delete=models.SET_NULL,
        related_name='sessions',
        null=True,
        blank=True
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
        
        # Session starts 15 minutes before scheduled start time
        session_date = timezone.make_aware(
            timezone.datetime.combine(self.date, self.start_time)
        )
        early_start = session_date - timezone.timedelta(minutes=15)
        
        session_end = timezone.make_aware(
            timezone.datetime.combine(self.date, self.end_time)
        )
        
        return early_start <= now <= session_end
    
    @property
    def is_upcoming(self):
        """Check if the session is upcoming"""
        now = timezone.now()
        session_date = timezone.make_aware(
            timezone.datetime.combine(self.date, self.start_time)
        )
        early_start = session_date - timezone.timedelta(minutes=15)
        return now < early_start
    
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
