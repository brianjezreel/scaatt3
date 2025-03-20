from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .forms import UserLoginForm

urlpatterns = [
    # Authentication
    path('login/', auth_views.LoginView.as_view(
        template_name='accounts/login.html',
        authentication_form=UserLoginForm
    ), name='login'),
    path('logout/', auth_views.LogoutView.as_view(
        template_name='accounts/logged_out.html',
        next_page='home',
        http_method_names=['get', 'post']  # Allow both GET and POST methods
    ), name='logout'),
    
    # Registration
    path('register/teacher/', views.TeacherRegistrationView.as_view(), name='register_teacher'),
    path('register/student/', views.StudentRegistrationView.as_view(), name='register_student'),
    
    # Password reset
    path('password-reset/', auth_views.PasswordResetView.as_view(
        template_name='accounts/password_reset.html'
    ), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='accounts/password_reset_done.html'
    ), name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='accounts/password_reset_confirm.html'
    ), name='password_reset_confirm'),
    path('password-reset-complete/', auth_views.PasswordResetCompleteView.as_view(
        template_name='accounts/password_reset_complete.html'
    ), name='password_reset_complete'),
    
    # User profile
    path('profile/', views.profile, name='profile'),
    path('dashboard/', views.dashboard, name='dashboard'),
]
