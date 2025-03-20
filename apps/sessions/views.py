from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden, JsonResponse
from django.urls import reverse
from django.utils import timezone
from django.db.models import Q
from datetime import timedelta, datetime, date
from .models import Session, CourseSchedule
from .forms import SessionForm, QRCodeRefreshForm, CourseScheduleForm
from apps.courses.models import Course
from utils.qr_generator import generate_qr_code_url, generate_qr_code_image


@login_required
def session_list(request, course_id):
    """Display list of sessions for a course"""
    
    course = get_object_or_404(Course, id=course_id)
    
    # Check permissions
    if request.user.is_teacher:
        if request.user != course.teacher:
            return HttpResponseForbidden("You don't have permission to view sessions for this course.")
    else:
        # Check if student is enrolled
        if not course.enrollments.filter(student=request.user, is_active=True).exists():
            return HttpResponseForbidden("You are not enrolled in this course.")
    
    # Get sessions
    sessions = Session.objects.filter(course=course)
    
    # Group sessions by status
    upcoming_sessions = [s for s in sessions if s.is_upcoming]
    active_sessions = [s for s in sessions if s.is_active]
    past_sessions = [s for s in sessions if s.is_past]
    
    context = {
        'course': course,
        'upcoming_sessions': upcoming_sessions,
        'active_sessions': active_sessions,
        'past_sessions': past_sessions,
    }
    
    if request.user.is_teacher:
        return render(request, 'sessions/teacher_session_list.html', context)
    else:
        return render(request, 'sessions/student_session_list.html', context)


@login_required
def create_session(request, course_id):
    """Create a new session for a course"""
    
    course = get_object_or_404(Course, id=course_id)
    
    # Check permissions
    if not request.user.is_teacher or request.user != course.teacher:
        return HttpResponseForbidden("You don't have permission to create sessions for this course.")
    
    if request.method == 'POST':
        form = SessionForm(request.POST, course=course)
        if form.is_valid():
            session = form.save()
            messages.success(request, f'Session "{session.title}" has been created successfully!')
            return redirect('session_detail', course_id=course.id, session_id=session.id)
    else:
        form = SessionForm(course=course)
    
    context = {
        'form': form,
        'course': course,
        'title': 'Create Session'
    }
    
    return render(request, 'sessions/session_form.html', context)


@login_required
def session_detail(request, course_id, session_id):
    """Display session details"""
    
    course = get_object_or_404(Course, id=course_id)
    session = get_object_or_404(Session, id=session_id, course=course)
    
    # Check permissions
    if request.user.is_teacher:
        if request.user != course.teacher:
            return HttpResponseForbidden("You don't have permission to view this session.")
        
        # For teachers, show QR code and attendance list
        qr_refresh_form = QRCodeRefreshForm()
        
        # Generate QR code URL and image
        qr_url = generate_qr_code_url(session.id, session.qr_code_token)
        qr_image = generate_qr_code_image(qr_url)
        
        # Get attendance records
        attendances = session.attendances.all().select_related('student')
        
        context = {
            'course': course,
            'session': session,
            'qr_url': qr_url,
            'qr_image': qr_image,
            'qr_refresh_form': qr_refresh_form,
            'attendances': attendances,
        }
        
        return render(request, 'sessions/teacher_session_detail.html', context)
    else:
        # Check if student is enrolled
        if not course.enrollments.filter(student=request.user, is_active=True).exists():
            return HttpResponseForbidden("You are not enrolled in this course.")
        
        # For students, show session details and attendance status
        try:
            attendance = session.attendances.get(student=request.user)
            has_attended = True
        except:
            has_attended = False
        
        context = {
            'course': course,
            'session': session,
            'has_attended': has_attended,
        }
        
        return render(request, 'sessions/student_session_detail.html', context)


@login_required
def edit_session(request, course_id, session_id):
    """Edit an existing session"""
    
    course = get_object_or_404(Course, id=course_id)
    session = get_object_or_404(Session, id=session_id, course=course)
    
    # Check permissions
    if not request.user.is_teacher or request.user != course.teacher:
        return HttpResponseForbidden("You don't have permission to edit this session.")
    
    if request.method == 'POST':
        form = SessionForm(request.POST, instance=session, course=course)
        if form.is_valid():
            form.save()
            messages.success(request, f'Session "{session.title}" has been updated successfully!')
            return redirect('session_detail', course_id=course.id, session_id=session.id)
    else:
        form = SessionForm(instance=session, course=course)
    
    context = {
        'form': form,
        'course': course,
        'session': session,
        'title': 'Edit Session'
    }
    
    return render(request, 'sessions/session_form.html', context)


@login_required
def delete_session(request, course_id, session_id):
    """Delete a session"""
    
    course = get_object_or_404(Course, id=course_id)
    session = get_object_or_404(Session, id=session_id, course=course)
    
    # Check permissions
    if not request.user.is_teacher or request.user != course.teacher:
        return HttpResponseForbidden("You don't have permission to delete this session.")
    
    if request.method == 'POST':
        session_title = session.title
        session.delete()
        messages.success(request, f'Session "{session_title}" has been deleted successfully!')
        return redirect('session_list', course_id=course.id)
    
    context = {
        'course': course,
        'session': session
    }
    
    return render(request, 'sessions/session_confirm_delete.html', context)


@login_required
def refresh_qr_code(request, course_id, session_id):
    """Refresh the QR code for a session"""
    
    course = get_object_or_404(Course, id=course_id)
    session = get_object_or_404(Session, id=session_id, course=course)
    
    # Check permissions
    if not request.user.is_teacher or request.user != course.teacher:
        return HttpResponseForbidden("You don't have permission to refresh the QR code for this session.")
    
    if request.method == 'POST':
        form = QRCodeRefreshForm(request.POST)
        if form.is_valid():
            duration = form.cleaned_data['duration']
            session.refresh_qr_code(duration_seconds=duration)
            
            # Generate new QR code URL and image
            qr_url = generate_qr_code_url(session.id, session.qr_code_token)
            qr_image = generate_qr_code_image(qr_url)
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'qr_image': qr_image,
                    'qr_url': qr_url,
                    'expiry_time': session.qr_expiry_time.strftime('%Y-%m-%d %H:%M:%S')
                })
            
            messages.success(request, f'QR code has been refreshed and is valid for {duration} seconds.')
            return redirect('session_detail', course_id=course.id, session_id=session.id)
    
    return redirect('session_detail', course_id=course.id, session_id=session.id)


@login_required
def qr_code_display(request, course_id, session_id):
    """Display QR code in fullscreen for easy scanning"""
    
    course = get_object_or_404(Course, id=course_id)
    session = get_object_or_404(Session, id=session_id, course=course)
    
    # Check permissions
    if not request.user.is_teacher or request.user != course.teacher:
        return HttpResponseForbidden("You don't have permission to view the QR code for this session.")
    
    # Generate QR code URL and image
    qr_url = generate_qr_code_url(session.id, session.qr_code_token)
    qr_image = generate_qr_code_image(qr_url, size=20)
    
    context = {
        'course': course,
        'session': session,
        'qr_image': qr_image,
    }
    
    return render(request, 'sessions/qr_code_display.html', context)


@login_required
def close_session(request, course_id, session_id):
    """Close a session to prevent further attendance marking"""
    
    course = get_object_or_404(Course, id=course_id)
    session = get_object_or_404(Session, id=session_id, course=course)
    
    # Check permissions
    if not request.user.is_teacher or request.user != course.teacher:
        return HttpResponseForbidden("You don't have permission to close this session.")
    
    if request.method == 'POST':
        session.is_closed = True
        session.save()
        
        messages.success(request, f'Session "{session.title}" has been closed. No further attendance can be marked.')
        
        # If AJAX request, return JSON response
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': f'Session "{session.title}" has been closed.'
            })
            
        return redirect('session_detail', course_id=course.id, session_id=session.id)
    
    # If not POST, redirect to session detail
    return redirect('session_detail', course_id=course.id, session_id=session.id)


@login_required
def reopen_session(request, course_id, session_id):
    """Reopen a closed session to allow attendance marking again"""
    
    course = get_object_or_404(Course, id=course_id)
    session = get_object_or_404(Session, id=session_id, course=course)
    
    # Check permissions
    if not request.user.is_teacher or request.user != course.teacher:
        return HttpResponseForbidden("You don't have permission to reopen this session.")
    
    if request.method == 'POST':
        session.is_closed = False
        session.save()
        
        # Refresh QR code with default duration
        session.refresh_qr_code(duration_seconds=10)
        
        messages.success(request, f'Session "{session.title}" has been reopened. Students can now mark attendance.')
        
        # If AJAX request, return JSON response
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': f'Session "{session.title}" has been reopened.'
            })
            
        return redirect('session_detail', course_id=course.id, session_id=session.id)
    
    # If not POST, redirect to session detail
    return redirect('session_detail', course_id=course.id, session_id=session.id)


@login_required
def all_sessions(request):
    """Display all sessions across all courses for a teacher"""
    
    # Only teachers can access this view
    if not request.user.is_teacher:
        return HttpResponseForbidden("You don't have permission to view this page.")
    
    # Get all courses taught by this teacher
    courses = Course.objects.filter(teacher=request.user)
    
    # Get all sessions for these courses
    sessions = Session.objects.filter(course__in=courses).order_by('-date', '-start_time')
    
    # Group sessions by status
    upcoming_sessions = [s for s in sessions if s.is_upcoming]
    active_sessions = [s for s in sessions if s.is_active]
    past_sessions = [s for s in sessions if s.is_past]
    
    context = {
        'upcoming_sessions': upcoming_sessions,
        'active_sessions': active_sessions,
        'past_sessions': past_sessions,
    }
    
    return render(request, 'sessions/all_sessions.html', context)


@login_required
def course_schedule(request, course_id):
    """Manage course schedules"""
    course = get_object_or_404(Course, id=course_id)
    
    # Verify the user is the teacher of the course
    if request.user != course.teacher:
        messages.error(request, 'Only the teacher of the course can manage schedules.')
        return redirect('course_detail', course_id=course.id)
    
    current_schedules = CourseSchedule.objects.filter(course=course, is_active=True)
    
    if request.method == 'POST':
        form = CourseScheduleForm(request.POST, course=course)
        if form.is_valid():
            schedules = form.save()
            if schedules:
                messages.success(request, 'Course schedule has been updated.')
                generate_upcoming_sessions(course)
            return redirect('course_schedule', course_id=course.id)
    else:
        form = CourseScheduleForm(course=course)
    
    return render(request, 'sessions/schedule_form.html', {
        'form': form,
        'course': course,
        'current_schedules': current_schedules,
    })


@login_required
def delete_schedule(request, course_id, schedule_id):
    """Delete a course schedule"""
    course = get_object_or_404(Course, id=course_id)
    schedule = get_object_or_404(CourseSchedule, id=schedule_id, course=course)
    
    # Verify the user is the teacher of the course
    if request.user != course.teacher:
        messages.error(request, 'Only the teacher of the course can delete schedules.')
        return redirect('course_detail', course_id=course.id)
    
    schedule.is_active = False
    schedule.save()
    
    messages.success(request, f'Schedule for {schedule.get_day_of_week_display()} has been deleted.')
    return redirect('course_schedule', course_id=course.id)


def generate_upcoming_sessions(course, weeks_ahead=4):
    """Generate sessions for the upcoming weeks based on course schedules"""
    
    today = timezone.now().date()
    end_date = today + timedelta(days=weeks_ahead * 7)
    
    # Get all active schedules for the course
    schedules = CourseSchedule.objects.filter(course=course, is_active=True)
    
    # If no schedules, return
    if not schedules:
        return []
    
    created_sessions = []
    
    # For each schedule, generate sessions up to weeks_ahead
    for schedule in schedules:
        # Calculate the next occurrence of this schedule's day of the week
        days_ahead = (schedule.day_of_week - today.weekday()) % 7
        if days_ahead == 0 and timezone.now().time() > schedule.end_time:
            # If today is the day but the session time has passed, start from next week
            days_ahead = 7
        
        next_date = today + timedelta(days=days_ahead)
        
        # Generate sessions for the specified number of weeks
        while next_date <= end_date:
            # Check if a session already exists for this date and time range
            existing_session = Session.objects.filter(
                course=course,
                date=next_date,
                start_time=schedule.start_time,
                end_time=schedule.end_time
            ).exists()
            
            if not existing_session:
                # Create a new session
                title = f"{course.name} - {schedule.get_day_of_week_display()}"
                session = Session.objects.create(
                    course=course,
                    schedule=schedule,
                    title=title,
                    date=next_date,
                    start_time=schedule.start_time,
                    end_time=schedule.end_time
                )
                created_sessions.append(session)
            
            # Move to the next week
            next_date += timedelta(days=7)
    
    return created_sessions


@login_required
def generate_qr_redirect(request):
    """
    Redirect teacher to an active session for QR code generation
    If multiple active sessions, show a selection screen
    """
    if not request.user.is_teacher:
        messages.error(request, 'Only teachers can generate QR codes for attendance.')
        return redirect('dashboard')
    
    # Get all courses taught by the teacher
    courses = Course.objects.filter(teacher=request.user)
    
    # Get all currently active sessions for these courses
    now = timezone.now()
    active_sessions = []
    
    for course in courses:
        # Find sessions that should be active (15 min before start to end time)
        for session in Session.objects.filter(course=course, is_closed=False):
            if session.is_active:
                active_sessions.append(session)
    
    if not active_sessions:
        messages.info(request, 'You have no active sessions at this time.')
        return redirect('course_list')
    
    if len(active_sessions) == 1:
        # If only one active session, redirect directly to it
        session = active_sessions[0]
        return redirect('session_detail', course_id=session.course.id, session_id=session.id)
    else:
        # If multiple active sessions, show a selection page
        return render(request, 'sessions/active_sessions.html', {
            'sessions': active_sessions
        })
