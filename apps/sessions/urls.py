from django.urls import path
from . import views

urlpatterns = [
    path('all-sessions/', views.all_sessions, name='all_sessions'),
    path('course/<int:course_id>/sessions/', views.session_list, name='session_list'),
    path('course/<int:course_id>/sessions/create/', views.create_session, name='create_session'),
    path('course/<int:course_id>/sessions/<int:session_id>/', views.session_detail, name='session_detail'),
    path('course/<int:course_id>/sessions/<int:session_id>/edit/', views.edit_session, name='edit_session'),
    path('course/<int:course_id>/sessions/<int:session_id>/delete/', views.delete_session, name='delete_session'),
    path('course/<int:course_id>/sessions/<int:session_id>/refresh-qr/', views.refresh_qr_code, name='refresh_qr_code'),
    path('course/<int:course_id>/sessions/<int:session_id>/qr-display/', views.qr_code_display, name='qr_code_display'),
    path('course/<int:course_id>/sessions/<int:session_id>/close/', views.close_session, name='close_session'),
    path('course/<int:course_id>/sessions/<int:session_id>/reopen/', views.reopen_session, name='reopen_session'),
]
