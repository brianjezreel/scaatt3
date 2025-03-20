from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.exceptions import ValidationError
from .models import User, Profile


class UserRegistrationForm(UserCreationForm):
    """Form for user registration"""
    
    email = forms.EmailField(max_length=254, help_text='Required. Enter a valid email address.')
    
    class Meta:
        model = User
        fields = ('email', 'username', 'first_name', 'last_name', 'role', 'password1', 'password2')
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("This email is already in use.")
        return email


class TeacherRegistrationForm(UserRegistrationForm):
    """Form specifically for teacher registration"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['role'].initial = User.Role.TEACHER
        self.fields['role'].widget = forms.HiddenInput()


class StudentRegistrationForm(UserRegistrationForm):
    """Form specifically for student registration"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['role'].initial = User.Role.STUDENT
        self.fields['role'].widget = forms.HiddenInput()


class UserLoginForm(AuthenticationForm):
    """Custom login form"""
    
    username = forms.EmailField(label='Email')


class ProfileUpdateForm(forms.ModelForm):
    """Form for updating user profile"""
    
    class Meta:
        model = Profile
        fields = ('profile_picture', 'bio', 'phone_number')


class UserUpdateForm(forms.ModelForm):
    """Form for updating user information"""
    
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'username')
