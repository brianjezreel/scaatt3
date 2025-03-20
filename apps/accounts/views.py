from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import CreateView, UpdateView
from django.urls import reverse_lazy
from .forms import (
    TeacherRegistrationForm, StudentRegistrationForm, 
    UserLoginForm, ProfileUpdateForm, UserUpdateForm
)
from .models import User


class TeacherRegistrationView(CreateView):
    """View for teacher registration"""
    
    template_name = 'accounts/register.html'
    form_class = TeacherRegistrationForm
    success_url = reverse_lazy('login')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Teacher Registration'
        context['role'] = 'teacher'
        return context
    
    def form_valid(self, form):
        messages.success(self.request, 'Account created successfully. You can now log in.')
        return super().form_valid(form)


class StudentRegistrationView(CreateView):
    """View for student registration"""
    
    template_name = 'accounts/register.html'
    form_class = StudentRegistrationForm
    success_url = reverse_lazy('login')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Student Registration'
        context['role'] = 'student'
        return context
    
    def form_valid(self, form):
        messages.success(self.request, 'Account created successfully. You can now log in.')
        return super().form_valid(form)


@login_required
def dashboard(request):
    """User dashboard view based on role"""
    
    if request.user.is_teacher:
        return redirect('course_list')
    else:
        return redirect('scanner')


@login_required
def profile(request):
    """User profile view"""
    
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = ProfileUpdateForm(
            request.POST, request.FILES, instance=request.user.profile
        )
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Your profile has been updated!')
            return redirect('profile')
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = ProfileUpdateForm(instance=request.user.profile)
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
    }
    
    return render(request, 'accounts/profile.html', context)
