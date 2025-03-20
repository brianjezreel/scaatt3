from django.urls import path
from . import views

urlpatterns = [
    path('mark/<int:session_id>/<str:token>/', views.mark_attendance, name='mark_attendance'),
    path('course/<int:course_id>/attendance/', views.attendance_list, name='attendance_list'),
    path('course/<int:course_id>/session/<int:session_id>/attendance/', views.session_attendance, name='session_attendance'),
    path('course/<int:course_id>/session/<int:session_id>/attendance/bulk/', views.bulk_attendance, name='bulk_attendance'),
    path('course/<int:course_id>/session/<int:session_id>/attendance/<int:attendance_id>/delete/', views.delete_attendance, name='delete_attendance'),
    path('report/', views.student_attendance_report, name='student_attendance_report'),
    path('scanner/', views.scanner, name='scanner'),
    path('manual/', views.manual_attendance, name='manual_attendance'),
]
