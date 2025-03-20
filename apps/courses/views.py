from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count
from django.http import HttpResponseForbidden
from .models import Course, CourseEnrollment
from apps.attendance.models import Attendance
from .forms import CourseForm, CourseJoinForm
from django.utils import timezone
from django.db.models import Q


@login_required
def course_list(request):
    """Display list of courses based on user role"""
    
    if request.user.is_teacher:
        # For teachers, show courses they created
        courses = Course.objects.filter(teacher=request.user)
        
        # Add session counts to each course
        for course in courses:
            course.session_count = course.sessions.count()
            course.active_session_count = course.sessions.filter(
                date=timezone.now().date(),
                start_time__lte=timezone.now().time(),
                end_time__gte=timezone.now().time()
            ).count()
        
        template = 'courses/teacher_course_list.html'
    else:
        # For students, show enrolled courses
        enrollments = CourseEnrollment.objects.filter(
            student=request.user,
            is_active=True
        ).select_related('course')
        
        courses = []
        for enrollment in enrollments:
            course = enrollment.course
            
            # Add session counts to each course
            course.session_count = course.sessions.count()
            course.active_session_count = course.sessions.filter(
                date=timezone.now().date(),
                start_time__lte=timezone.now().time(),
                end_time__gte=timezone.now().time()
            ).count()
            
            # Add attendance info
            course.attended_sessions = Attendance.objects.filter(
                student=request.user,
                session__course=course
            ).count()
            
            # Calculate attendance rate
            if course.session_count > 0:
                course.attendance_rate = (course.attended_sessions / course.session_count) * 100
            else:
                course.attendance_rate = 0
                
            courses.append(course)
        
        template = 'courses/student_course_list.html'
    
    context = {
        'courses': courses
    }
    
    return render(request, template, context)


@login_required
def course_detail(request, course_id):
    """Display course details"""
    
    course = get_object_or_404(Course, id=course_id)
    
    # Check permissions
    if request.user.is_teacher:
        if request.user != course.teacher:
            return HttpResponseForbidden("You don't have permission to view this course.")
        
        # Get enrolled students
        enrollments = CourseEnrollment.objects.filter(
            course=course,
            is_active=True
        ).select_related('student')
        
        # Get recent sessions
        recent_sessions = course.sessions.all().order_by('-date', '-start_time')[:5]
        
        context = {
            'course': course,
            'enrollments': enrollments,
            'recent_sessions': recent_sessions,
            'session_count': course.sessions.count(),
        }
        
        return render(request, 'courses/teacher_course_detail.html', context)
    else:
        # Check if student is enrolled
        try:
            enrollment = CourseEnrollment.objects.get(
                course=course,
                student=request.user,
                is_active=True
            )
        except CourseEnrollment.DoesNotExist:
            return HttpResponseForbidden("You are not enrolled in this course.")
        
        # Get recent sessions
        recent_sessions = course.sessions.all().order_by('-date', '-start_time')[:5]
        
        # Get active sessions (happening now)
        active_sessions = course.sessions.filter(
            date=timezone.now().date(),
            start_time__lte=timezone.now().time(),
            end_time__gte=timezone.now().time()
        )
        
        # Get upcoming sessions
        upcoming_sessions = course.sessions.filter(
            Q(date__gt=timezone.now().date()) | 
            Q(date=timezone.now().date(), start_time__gt=timezone.now().time())
        ).order_by('date', 'start_time')[:3]
        
        # Get attendance records for this student in this course
        attendances = Attendance.objects.filter(
            student=request.user,
            session__course=course
        ).select_related('session')
        
        # Calculate attendance statistics
        session_count = course.sessions.count()
        attended_count = attendances.count()
        
        if session_count > 0:
            attendance_rate = (attended_count / session_count) * 100
        else:
            attendance_rate = 0
        
        context = {
            'course': course,
            'enrollment': enrollment,
            'recent_sessions': recent_sessions,
            'active_sessions': active_sessions,
            'upcoming_sessions': upcoming_sessions,
            'attendances': attendances,
            'session_count': session_count,
            'attended_count': attended_count,
            'attendance_rate': attendance_rate,
        }
        
        return render(request, 'courses/student_course_detail.html', context)


@login_required
def create_course(request):
    """Create a new course (teachers only)"""
    
    if not request.user.is_teacher:
        return HttpResponseForbidden("Only teachers can create courses.")
    
    if request.method == 'POST':
        form = CourseForm(request.POST, teacher=request.user)
        if form.is_valid():
            course = form.save()
            messages.success(request, f'Course "{course.name}" has been created successfully!')
            return redirect('course_detail', course_id=course.id)
    else:
        form = CourseForm(teacher=request.user)
    
    context = {
        'form': form,
        'title': 'Create Course'
    }
    
    return render(request, 'courses/course_form.html', context)


@login_required
def edit_course(request, course_id):
    """Edit an existing course (teachers only)"""
    
    course = get_object_or_404(Course, id=course_id)
    
    # Check permissions
    if not request.user.is_teacher or request.user != course.teacher:
        return HttpResponseForbidden("You don't have permission to edit this course.")
    
    if request.method == 'POST':
        form = CourseForm(request.POST, instance=course, teacher=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, f'Course "{course.name}" has been updated successfully!')
            return redirect('course_detail', course_id=course.id)
    else:
        form = CourseForm(instance=course, teacher=request.user)
    
    context = {
        'form': form,
        'course': course,
        'title': 'Edit Course'
    }
    
    return render(request, 'courses/course_form.html', context)


@login_required
def delete_course(request, course_id):
    """Delete a course (teachers only)"""
    
    course = get_object_or_404(Course, id=course_id)
    
    # Check permissions
    if not request.user.is_teacher or request.user != course.teacher:
        return HttpResponseForbidden("You don't have permission to delete this course.")
    
    if request.method == 'POST':
        course_name = course.name
        course.delete()
        messages.success(request, f'Course "{course_name}" has been deleted successfully!')
        return redirect('course_list')
    
    context = {
        'course': course
    }
    
    return render(request, 'courses/course_confirm_delete.html', context)


@login_required
def join_course(request):
    """Allow students to join a course using a course code"""
    
    if not request.user.is_student:
        return HttpResponseForbidden("Only students can join courses.")
    
    if request.method == 'POST':
        form = CourseJoinForm(request.POST, student=request.user)
        if form.is_valid():
            course_code = form.cleaned_data['course_code']
            
            # Check if the code is in the QR format (course_code-longerqrcode)
            if '-' in course_code:
                # Extract the actual course code from the QR format
                course_code = course_code.split('-')[0]
            
            try:
                course = Course.objects.get(code=course_code, is_active=True)
                
                # Create enrollment
                enrollment = CourseEnrollment(course=course, student=request.user)
                enrollment.save()
                
                messages.success(request, f'You have successfully joined the course "{course.name}"!')
                return redirect('course_detail', course_id=course.id)
            except Course.DoesNotExist:
                messages.error(request, 'Invalid course code. Please check and try again.')
                return redirect('join_course')
    else:
        form = CourseJoinForm(student=request.user)
    
    context = {
        'form': form
    }
    
    return render(request, 'courses/join_course.html', context)


@login_required
def leave_course(request, course_id):
    """Allow students to leave a course"""
    
    if not request.user.is_student:
        return HttpResponseForbidden("Only students can leave courses.")
    
    course = get_object_or_404(Course, id=course_id)
    enrollment = get_object_or_404(CourseEnrollment, course=course, student=request.user)
    
    if request.method == 'POST':
        enrollment.is_active = False
        enrollment.save()
        messages.success(request, f'You have successfully left the course "{course.name}".')
        return redirect('course_list')
    
    context = {
        'course': course
    }
    
    return render(request, 'courses/leave_course_confirm.html', context)
