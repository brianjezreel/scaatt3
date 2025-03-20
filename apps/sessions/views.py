from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden, JsonResponse
from django.utils import timezone
from .models import Session
from .forms import SessionForm, QRCodeRefreshForm
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
