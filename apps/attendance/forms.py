from django import forms
from .models import Attendance


class AttendanceForm(forms.ModelForm):
    """Form for manually recording attendance"""
    
    class Meta:
        model = Attendance
        fields = ['student', 'status', 'notes']
        widgets = {
            'student': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        self.session = kwargs.pop('session', None)
        super().__init__(*args, **kwargs)
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.session:
            instance.session = self.session
        if commit:
            instance.save()
        return instance


class BulkAttendanceForm(forms.Form):
    """Form for bulk updating attendance status"""
    
    students = forms.MultipleChoiceField(
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=True
    )
    status = forms.ChoiceField(
        choices=Attendance.Status.choices,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    notes = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        required=False
    )
    
    def __init__(self, *args, **kwargs):
        self.session = kwargs.pop('session', None)
        super().__init__(*args, **kwargs)
        
        if self.session:
            # Get all students enrolled in the course
            enrolled_students = self.session.course.enrollments.filter(
                is_active=True
            ).select_related('student')
            
            # Create choices for the students field
            self.fields['students'].choices = [
                (enrollment.student.id, enrollment.student.get_full_name())
                for enrollment in enrolled_students
            ]


class AttendanceFilterForm(forms.Form):
    """Form for filtering attendance records"""
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    status = forms.ChoiceField(
        choices=[('', 'All')] + list(Attendance.Status.choices),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    student = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Search by student name'})
    )
