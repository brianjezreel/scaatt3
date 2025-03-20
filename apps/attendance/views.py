from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden, JsonResponse
from django.utils import timezone
from django.db.models import Q
from django.views.decorators.http import require_POST
from .models import Attendance
from .forms import AttendanceForm, BulkAttendanceForm, AttendanceFilterForm
from apps.sessions.models import Session
from apps.courses.models import Course


@login_required
def mark_attendance(request, session_id, token):
    """Mark attendance for a student by scanning a QR code"""
    
    # Get the session and verify the token
    session = get_object_or_404(Session, id=session_id)
    
    # Check if the token is valid
    if session.qr_code_token != token:
        messages.error(request, 'Invalid QR code. Please try again.')
        return redirect('course_detail', course_id=session.course.id)
    
    # Check if the QR code has expired
    if not session.qr_is_valid:
        messages.error(request, 'This QR code has expired. Please ask your teacher for a new one.')
        return redirect('course_detail', course_id=session.course.id)
    
    # Check if the session is closed
    if session.is_closed:
        messages.error(request, 'This session has been closed by the teacher. No further attendance can be marked.')
        return redirect('course_detail', course_id=session.course.id)
    
    # Check if the user is a student
    if not request.user.is_student:
        messages.error(request, 'Only students can mark attendance.')
        return redirect('course_detail', course_id=session.course.id)
    
    # Check if the student is enrolled in the course
    if not session.course.enrollments.filter(student=request.user, is_active=True).exists():
        messages.error(request, 'You are not enrolled in this course.')
        return redirect('course_list')
    
    # Check if the student has already marked attendance for this session
    if Attendance.objects.filter(session=session, student=request.user).exists():
        messages.info(request, 'You have already marked your attendance for this session.')
        return redirect('session_detail', course_id=session.course.id, session_id=session.id)
    
    # Create attendance record
    attendance = Attendance(
        session=session,
        student=request.user,
        ip_address=request.META.get('REMOTE_ADDR', ''),
        device_info=request.META.get('HTTP_USER_AGENT', '')[:255]
    )
    attendance.save()
    
    messages.success(request, 'Your attendance has been recorded successfully!')
    return redirect('session_detail', course_id=session.course.id, session_id=session.id)


@login_required
def attendance_list(request, course_id):
    """Display attendance records for a course"""
    
    course = get_object_or_404(Course, id=course_id)
    
    # Check permissions
    if request.user.is_teacher:
        if request.user != course.teacher:
            return HttpResponseForbidden("You don't have permission to view attendance for this course.")
    else:
        # Check if student is enrolled
        if not course.enrollments.filter(student=request.user, is_active=True).exists():
            return HttpResponseForbidden("You are not enrolled in this course.")
    
    # Get filter form
    filter_form = AttendanceFilterForm(request.GET)
    
    # Get sessions for the course
    sessions = Session.objects.filter(course=course)
    
    # Apply filters
    if filter_form.is_valid():
        date_from = filter_form.cleaned_data.get('date_from')
        date_to = filter_form.cleaned_data.get('date_to')
        status = filter_form.cleaned_data.get('status')
        student_query = filter_form.cleaned_data.get('student')
        
        if date_from:
            sessions = sessions.filter(date__gte=date_from)
        
        if date_to:
            sessions = sessions.filter(date__lte=date_to)
        
        # Get attendance records
        attendances = Attendance.objects.filter(session__in=sessions)
        
        if status:
            attendances = attendances.filter(status=status)
        
        if student_query:
            attendances = attendances.filter(
                Q(student__first_name__icontains=student_query) |
                Q(student__last_name__icontains=student_query) |
                Q(student__email__icontains=student_query)
            )
    else:
        # Get all attendance records for the course
        attendances = Attendance.objects.filter(session__in=sessions)
    
    # For students, only show their own attendance
    if request.user.is_student:
        attendances = attendances.filter(student=request.user)
    
    context = {
        'course': course,
        'attendances': attendances,
        'filter_form': filter_form,
    }
    
    if request.user.is_teacher:
        return render(request, 'attendance/teacher_attendance_list.html', context)
    else:
        return render(request, 'attendance/student_attendance_list.html', context)


@login_required
def session_attendance(request, course_id, session_id):
    """Manage attendance for a specific session"""
    
    course = get_object_or_404(Course, id=course_id)
    session = get_object_or_404(Session, id=session_id, course=course)
    
    # Check permissions
    if not request.user.is_teacher or request.user != course.teacher:
        return HttpResponseForbidden("You don't have permission to manage attendance for this session.")
    
    # Get enrolled students
    enrolled_students = course.enrollments.filter(
        is_active=True
    ).select_related('student')
    
    # Get existing attendance records
    attendances = Attendance.objects.filter(
        session=session
    ).select_related('student')
    
    # Create a dictionary of student IDs to attendance records
    attendance_dict = {a.student.id: a for a in attendances}
    
    # Create a list of students with their attendance status
    students_attendance = []
    for enrollment in enrolled_students:
        student = enrollment.student
        attendance = attendance_dict.get(student.id)
        students_attendance.append({
            'student': student,
            'attendance': attendance,
            'status': attendance.status if attendance else Attendance.Status.ABSENT,
        })
    
    # Handle manual attendance recording
    if request.method == 'POST':
        form = AttendanceForm(request.POST, session=session)
        if form.is_valid():
            # Check if attendance record already exists
            student = form.cleaned_data['student']
            try:
                attendance = Attendance.objects.get(session=session, student=student)
                # Update existing record
                attendance.status = form.cleaned_data['status']
                attendance.notes = form.cleaned_data['notes']
                attendance.save()
                messages.success(request, f'Attendance for {student.get_full_name()} has been updated.')
            except Attendance.DoesNotExist:
                # Create new record
                attendance = form.save()
                messages.success(request, f'Attendance for {student.get_full_name()} has been recorded.')
            
            return redirect('session_attendance', course_id=course.id, session_id=session.id)
    else:
        form = AttendanceForm(session=session)
        # Limit student choices to enrolled students
        form.fields['student'].queryset = course.enrollments.filter(
            is_active=True
        ).select_related('student').values_list('student', flat=True)
    
    # Bulk attendance form
    bulk_form = BulkAttendanceForm(session=session)
    
    context = {
        'course': course,
        'session': session,
        'students_attendance': students_attendance,
        'form': form,
        'bulk_form': bulk_form,
    }
    
    return render(request, 'attendance/session_attendance.html', context)


@login_required
@require_POST
def bulk_attendance(request, course_id, session_id):
    """Update attendance for multiple students at once"""
    
    course = get_object_or_404(Course, id=course_id)
    session = get_object_or_404(Session, id=session_id, course=course)
    
    # Check permissions
    if not request.user.is_teacher or request.user != course.teacher:
        return HttpResponseForbidden("You don't have permission to manage attendance for this session.")
    
    form = BulkAttendanceForm(request.POST, session=session)
    if form.is_valid():
        student_ids = form.cleaned_data['students']
        status = form.cleaned_data['status']
        notes = form.cleaned_data['notes']
        
        # Update or create attendance records for selected students
        for student_id in student_ids:
            try:
                attendance = Attendance.objects.get(session=session, student_id=student_id)
                # Update existing record
                attendance.status = status
                attendance.notes = notes
                attendance.save()
            except Attendance.DoesNotExist:
                # Create new record
                Attendance.objects.create(
                    session=session,
                    student_id=student_id,
                    status=status,
                    notes=notes,
                    ip_address=request.META.get('REMOTE_ADDR', ''),
                    device_info=request.META.get('HTTP_USER_AGENT', '')[:255]
                )
        
        messages.success(request, f'Attendance updated for {len(student_ids)} students.')
    else:
        messages.error(request, 'There was an error processing the form. Please try again.')
    
    return redirect('session_attendance', course_id=course.id, session_id=session.id)


@login_required
def delete_attendance(request, course_id, session_id, attendance_id):
    """Delete an attendance record"""
    
    course = get_object_or_404(Course, id=course_id)
    session = get_object_or_404(Session, id=session_id, course=course)
    attendance = get_object_or_404(Attendance, id=attendance_id, session=session)
    
    # Check permissions
    if not request.user.is_teacher or request.user != course.teacher:
        return HttpResponseForbidden("You don't have permission to delete attendance records for this session.")
    
    if request.method == 'POST':
        student_name = attendance.student.get_full_name()
        attendance.delete()
        messages.success(request, f'Attendance record for {student_name} has been deleted.')
        return redirect('session_attendance', course_id=course.id, session_id=session.id)
    
    context = {
        'course': course,
        'session': session,
        'attendance': attendance,
    }
    
    return render(request, 'attendance/delete_attendance.html', context)


@login_required
def student_attendance_report(request):
    """Display attendance report for a student across all courses"""
    
    # Only students can view their own attendance report
    if not request.user.is_student:
        return HttpResponseForbidden("Only students can view their attendance report.")
    
    # Get all enrollments for the student
    enrollments = request.user.enrollments.filter(is_active=True).select_related('course')
    
    # Get attendance records for each course
    courses_attendance = []
    for enrollment in enrollments:
        course = enrollment.course
        
        # Get all sessions for the course
        sessions = Session.objects.filter(course=course)
        
        # Get attendance records for the student
        attendances = Attendance.objects.filter(
            session__in=sessions,
            student=request.user
        ).select_related('session')
        
        # Calculate attendance statistics
        total_sessions = sessions.count()
        attended_sessions = attendances.count()
        attendance_rate = (attended_sessions / total_sessions * 100) if total_sessions > 0 else 0
        
        courses_attendance.append({
            'course': course,
            'total_sessions': total_sessions,
            'attended_sessions': attended_sessions,
            'attendance_rate': attendance_rate,
            'attendances': attendances,
        })
    
    context = {
        'courses_attendance': courses_attendance,
    }
    
    return render(request, 'attendance/student_report.html', context)


@login_required
def scanner(request):
    """Display QR code scanner for students"""
    
    # Only students can access the scanner
    if not request.user.is_student:
        messages.error(request, 'Only students can access the QR code scanner.')
        return redirect('dashboard')
    
    return render(request, 'attendance/scanner.html')


@login_required
@require_POST
def manual_attendance(request):
    """Mark attendance manually using a code"""
    
    if not request.user.is_student:
        messages.error(request, 'Only students can mark attendance.')
        return redirect('dashboard')
    
    attendance_code = request.POST.get('attendance_code', '').strip()
    
    if not attendance_code:
        messages.error(request, 'Please enter an attendance code.')
        return redirect('scanner')
    
    # Try to parse the attendance code (format: SESSION_ID-TOKEN)
    try:
        parts = attendance_code.split('-')
        if len(parts) != 2:
            raise ValueError("Invalid format")
        
        session_id = int(parts[0])
        token = parts[1]
        
        # Get the session
        session = get_object_or_404(Session, id=session_id)
        
        # Check if the token is valid
        if session.qr_code_token != token:
            messages.error(request, 'Invalid attendance code. Please check and try again.')
            return redirect('scanner')
        
        # Check if the QR code has expired
        if not session.qr_is_valid:
            messages.error(request, 'This attendance code has expired. Please ask your teacher for a new one.')
            return redirect('scanner')
        
        # Check if the session is closed
        if session.is_closed:
            messages.error(request, 'This session has been closed by the teacher. No further attendance can be marked.')
            return redirect('scanner')
        
        # Check if the student is enrolled in the course
        if not session.course.enrollments.filter(student=request.user, is_active=True).exists():
            messages.error(request, 'You are not enrolled in this course.')
            return redirect('course_list')
        
        # Check if the student has already marked attendance for this session
        if Attendance.objects.filter(session=session, student=request.user).exists():
            messages.info(request, 'You have already marked your attendance for this session.')
            return redirect('session_detail', course_id=session.course.id, session_id=session.id)
        
        # Create attendance record
        attendance = Attendance(
            session=session,
            student=request.user,
            ip_address=request.META.get('REMOTE_ADDR', ''),
            device_info=request.META.get('HTTP_USER_AGENT', '')[:255]
        )
        attendance.save()
        
        messages.success(request, 'Your attendance has been recorded successfully!')
        return redirect('session_detail', course_id=session.course.id, session_id=session.id)
        
    except (ValueError, Session.DoesNotExist):
        messages.error(request, 'Invalid attendance code. Please check and try again.')
        return redirect('scanner')
