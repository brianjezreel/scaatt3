from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.sessions.models import Session, CourseSchedule
from apps.sessions.views import generate_upcoming_sessions
from apps.courses.models import Course
from datetime import timedelta, date
import logging
from django.db.models import Q

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Automatically manages sessions - closes expired ones and generates upcoming sessions'

    def handle(self, *args, **options):
        self.stdout.write('Running automatic session management...')
        
        # Auto-close expired sessions
        self.auto_close_sessions()
        
        # Generate upcoming sessions based on schedules
        self.generate_future_sessions()
        
        self.stdout.write(self.style.SUCCESS('Session management completed successfully'))
        
    def auto_close_sessions(self):
        """Automatically close sessions that have ended"""
        now = timezone.now()
        
        # Find all sessions that:
        # 1. Have not been manually closed
        # 2. End time has passed
        expired_sessions = Session.objects.filter(
            is_closed=False,
            date__lte=now.date()
        ).filter(
            # Only sessions where end time has passed for today's sessions
            # or any past sessions (regardless of time)
            Q(date__lt=now.date()) | Q(date=now.date(), end_time__lt=now.time())
        )
        
        count = expired_sessions.count()
        if count > 0:
            expired_sessions.update(is_closed=True)
            self.stdout.write(f'Auto-closed {count} expired sessions')
        else:
            self.stdout.write('No expired sessions to close')
    
    def generate_future_sessions(self):
        """Generate upcoming sessions based on course schedules"""
        # Get all active courses
        active_courses = Course.objects.filter(is_active=True)
        
        total_generated = 0
        for course in active_courses:
            # Generate sessions for the next 4 weeks
            sessions = generate_upcoming_sessions(course, weeks_ahead=4)
            count = len(sessions)
            total_generated += count
            
            if count > 0:
                self.stdout.write(f'Generated {count} upcoming sessions for {course.name}')
        
        self.stdout.write(f'Total generated sessions: {total_generated}') 