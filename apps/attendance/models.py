from django.db import models
from django.conf import settings
from django.utils import timezone
from apps.sessions.models import Session


class Attendance(models.Model):
    """Model for tracking student attendance in sessions"""
    
    class Status(models.TextChoices):
        PRESENT = 'PRESENT', 'Present'
        LATE = 'LATE', 'Late'
        EXCUSED = 'EXCUSED', 'Excused'
        ABSENT = 'ABSENT', 'Absent'
    
    session = models.ForeignKey(
        Session,
        on_delete=models.CASCADE,
        related_name='attendances'
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='attendances',
        limit_choices_to={'role': 'STUDENT'}
    )
    check_in_time = models.DateTimeField(default=timezone.now)
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PRESENT
    )
    notes = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    device_info = models.CharField(max_length=255, blank=True)
    
    class Meta:
        unique_together = ['session', 'student']
        ordering = ['session', 'check_in_time']
    
    def __str__(self):
        return f"{self.student.get_full_name()} - {self.session.title} ({self.get_status_display()})"
    
    def save(self, *args, **kwargs):
        # Determine if the student is late
        if not self.id and self.status == self.Status.PRESENT:
            session_start = timezone.make_aware(
                timezone.datetime.combine(self.session.date, self.session.start_time)
            )
            # If check-in time is more than 15 minutes after session start, mark as late
            if self.check_in_time > session_start + timezone.timedelta(minutes=15):
                self.status = self.Status.LATE
        
        super().save(*args, **kwargs)
