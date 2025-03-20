from django import forms
from .models import Course, CourseEnrollment


class CourseForm(forms.ModelForm):
    """Form for creating and updating courses"""
    
    class Meta:
        model = Course
        fields = ['name', 'code', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        help_texts = {
            'code': 'Leave blank to auto-generate a unique code',
        }
    
    def __init__(self, *args, **kwargs):
        self.teacher = kwargs.pop('teacher', None)
        super().__init__(*args, **kwargs)
        
        # Make code field optional
        self.fields['code'].required = False
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.teacher:
            instance.teacher = self.teacher
        if commit:
            instance.save()
        return instance


class CourseEnrollmentForm(forms.ModelForm):
    """Form for enrolling students in courses"""
    
    class Meta:
        model = CourseEnrollment
        fields = ['course', 'is_active']
    
    def __init__(self, *args, **kwargs):
        self.student = kwargs.pop('student', None)
        super().__init__(*args, **kwargs)
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.student:
            instance.student = self.student
        if commit:
            instance.save()
        return instance


class CourseJoinForm(forms.Form):
    """Form for students to join a course using a course code"""
    
    course_code = forms.CharField(
        max_length=40,  # Increased to accommodate longer QR format
        label='Course Code',
        help_text='Enter the full extended code provided by your teacher (includes a hyphen)',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., MATH101-ABC123DEF456'})
    )
    
    def __init__(self, *args, **kwargs):
        self.student = kwargs.pop('student', None)
        super().__init__(*args, **kwargs)
    
    def clean_course_code(self):
        code = self.cleaned_data.get('course_code')
        
        # Require the code to be in the extended format (course_code-longerqrcode)
        if '-' not in code:
            raise forms.ValidationError('Please enter the full extended code. It should contain a hyphen (-).')
        
        # Extract the actual course code from the QR format
        actual_code = code.split('-')[0]
        
        try:
            course = Course.objects.get(code=actual_code, is_active=True)
            
            # Check if student is already enrolled
            if self.student and CourseEnrollment.objects.filter(course=course, student=self.student).exists():
                raise forms.ValidationError('You are already enrolled in this course.')
                
            return code  # Return the original extended code
        except Course.DoesNotExist:
            raise forms.ValidationError('Invalid course code. Please check and try again.')
