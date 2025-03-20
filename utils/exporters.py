import csv
import xlsxwriter # type: ignore
import io
from datetime import datetime
from django.http import HttpResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet


def export_attendance_to_csv(attendances, course_name):
    """Export attendance records to CSV format"""
    
    # Create a response object with CSV content type
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="attendance_{course_name}_{datetime.now().strftime("%Y%m%d")}.csv"'
    
    # Create CSV writer
    writer = csv.writer(response)
    
    # Write header row
    writer.writerow(['Student', 'Email', 'Session', 'Date', 'Check-in Time', 'Status', 'Notes'])
    
    # Write data rows
    for attendance in attendances:
        writer.writerow([
            attendance.student.get_full_name(),
            attendance.student.email,
            attendance.session.title,
            attendance.session.date.strftime('%Y-%m-%d'),
            attendance.check_in_time.strftime('%Y-%m-%d %H:%M:%S'),
            attendance.get_status_display(),
            attendance.notes
        ])
    
    return response


def export_attendance_to_excel(attendances, course_name):
    """Export attendance records to Excel format"""
    
    # Create an in-memory output file
    output = io.BytesIO()
    
    # Create a workbook and add a worksheet
    workbook = xlsxwriter.Workbook(output)
    worksheet = workbook.add_worksheet('Attendance')
    
    # Add formats
    header_format = workbook.add_format({
        'bold': True,
        'bg_color': '#4472C4',
        'color': 'white',
        'border': 1
    })
    
    date_format = workbook.add_format({'num_format': 'yyyy-mm-dd'})
    datetime_format = workbook.add_format({'num_format': 'yyyy-mm-dd hh:mm:ss'})
    
    # Write header row
    headers = ['Student', 'Email', 'Session', 'Date', 'Check-in Time', 'Status', 'Notes']
    for col, header in enumerate(headers):
        worksheet.write(0, col, header, header_format)
    
    # Write data rows
    for row, attendance in enumerate(attendances, start=1):
        worksheet.write(row, 0, attendance.student.get_full_name())
        worksheet.write(row, 1, attendance.student.email)
        worksheet.write(row, 2, attendance.session.title)
        worksheet.write_datetime(row, 3, attendance.session.date, date_format)
        worksheet.write_datetime(row, 4, attendance.check_in_time, datetime_format)
        worksheet.write(row, 5, attendance.get_status_display())
        worksheet.write(row, 6, attendance.notes)
    
    # Auto-fit columns
    for col in range(len(headers)):
        worksheet.set_column(col, col, 15)
    
    # Close the workbook
    workbook.close()
    
    # Create the response
    output.seek(0)
    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="attendance_{course_name}_{datetime.now().strftime("%Y%m%d")}.xlsx"'
    
    return response


def export_attendance_to_pdf(attendances, course_name):
    """Export attendance records to PDF format"""
    
    # Create an in-memory output file
    buffer = io.BytesIO()
    
    # Create the PDF object using the buffer as its "file"
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(letter),
        title=f"Attendance Report - {course_name}"
    )
    
    # Get styles
    styles = getSampleStyleSheet()
    title_style = styles['Heading1']
    subtitle_style = styles['Heading2']
    
    # Create the content
    elements = []
    
    # Add title
    elements.append(Paragraph(f"Attendance Report - {course_name}", title_style))
    elements.append(Paragraph(f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}", subtitle_style))
    elements.append(Spacer(1, 20))
    
    # Create table data
    data = [['Student', 'Email', 'Session', 'Date', 'Check-in Time', 'Status', 'Notes']]
    
    for attendance in attendances:
        data.append([
            attendance.student.get_full_name(),
            attendance.student.email,
            attendance.session.title,
            attendance.session.date.strftime('%Y-%m-%d'),
            attendance.check_in_time.strftime('%Y-%m-%d %H:%M'),
            attendance.get_status_display(),
            attendance.notes
        ])
    
    # Create table
    table = Table(data)
    
    # Add style to table
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.blue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
    ]))
    
    # Add table to elements
    elements.append(table)
    
    # Build the PDF
    doc.build(elements)
    
    # Get the value of the buffer
    pdf = buffer.getvalue()
    buffer.close()
    
    # Create the response
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="attendance_{course_name}_{datetime.now().strftime("%Y%m%d")}.pdf"'
    response.write(pdf)
    
    return response


def export_session_summary_to_excel(course, sessions):
    """Export session summary to Excel format"""
    
    # Create an in-memory output file
    output = io.BytesIO()
    
    # Create a workbook and add worksheets
    workbook = xlsxwriter.Workbook(output)
    summary_sheet = workbook.add_worksheet('Summary')
    sessions_sheet = workbook.add_worksheet('Sessions')
    students_sheet = workbook.add_worksheet('Students')
    
    # Add formats
    header_format = workbook.add_format({
        'bold': True,
        'bg_color': '#4472C4',
        'color': 'white',
        'border': 1
    })
    
    title_format = workbook.add_format({
        'bold': True,
        'font_size': 14
    })
    
    date_format = workbook.add_format({'num_format': 'yyyy-mm-dd'})
    percent_format = workbook.add_format({'num_format': '0.00%'})
    
    # Write course information
    summary_sheet.write(0, 0, 'Course Report', title_format)
    summary_sheet.write(2, 0, 'Course Name:')
    summary_sheet.write(2, 1, course.name)
    summary_sheet.write(3, 0, 'Course Code:')
    summary_sheet.write(3, 1, course.code)
    summary_sheet.write(4, 0, 'Teacher:')
    summary_sheet.write(4, 1, course.teacher.get_full_name())
    
    # Get enrolled students
    enrollments = course.enrollments.filter(is_active=True).select_related('student')
    students = [enrollment.student for enrollment in enrollments]
    
    # Write summary statistics
    summary_sheet.write(6, 0, 'Total Sessions:')
    summary_sheet.write(6, 1, len(sessions))
    summary_sheet.write(7, 0, 'Total Students:')
    summary_sheet.write(7, 1, len(students))
    
    # Write sessions data
    sessions_sheet.write(0, 0, 'Sessions', title_format)
    sessions_sheet.write(2, 0, 'Session Title', header_format)
    sessions_sheet.write(2, 1, 'Date', header_format)
    sessions_sheet.write(2, 2, 'Start Time', header_format)
    sessions_sheet.write(2, 3, 'End Time', header_format)
    sessions_sheet.write(2, 4, 'Attendance Count', header_format)
    sessions_sheet.write(2, 5, 'Attendance Rate', header_format)
    
    for row, session in enumerate(sessions, start=3):
        attendance_count = session.attendances.count()
        attendance_rate = attendance_count / len(students) if students else 0
        
        sessions_sheet.write(row, 0, session.title)
        sessions_sheet.write_datetime(row, 1, session.date, date_format)
        sessions_sheet.write(row, 2, session.start_time.strftime('%H:%M'))
        sessions_sheet.write(row, 3, session.end_time.strftime('%H:%M'))
        sessions_sheet.write(row, 4, attendance_count)
        sessions_sheet.write(row, 5, attendance_rate, percent_format)
    
    # Write student attendance data
    students_sheet.write(0, 0, 'Student Attendance', title_format)
    
    # Write header row with student names
    students_sheet.write(2, 0, 'Session', header_format)
    students_sheet.write(2, 1, 'Date', header_format)
    
    for col, student in enumerate(students, start=2):
        students_sheet.write(2, col, student.get_full_name(), header_format)
    
    # Write attendance data for each session
    for row, session in enumerate(sessions, start=3):
        students_sheet.write(row, 0, session.title)
        students_sheet.write_datetime(row, 1, session.date, date_format)
        
        # Get attendance records for this session
        attendances = session.attendances.all()
        attendance_dict = {a.student.id: a for a in attendances}
        
        # Write attendance status for each student
        for col, student in enumerate(students, start=2):
            attendance = attendance_dict.get(student.id)
            if attendance:
                students_sheet.write(row, col, attendance.get_status_display())
            else:
                students_sheet.write(row, col, 'Absent')
    
    # Auto-fit columns
    for sheet in [summary_sheet, sessions_sheet, students_sheet]:
        for col in range(10):  # Adjust range as needed
            sheet.set_column(col, col, 15)
    
    # Close the workbook
    workbook.close()
    
    # Create the response
    output.seek(0)
    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="course_report_{course.name}_{datetime.now().strftime("%Y%m%d")}.xlsx"'
    
    return response
