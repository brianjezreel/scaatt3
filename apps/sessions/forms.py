from django import forms
from django.utils import timezone
from .models import Session


class SessionForm(forms.ModelForm):
    """Form for creating and updating sessions"""
    
    class Meta:
        model = Session
        fields = ['title', 'description', 'date', 'start_time', 'end_time']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'start_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.course = kwargs.pop('course', None)
        super().__init__(*args, **kwargs)
    
    def clean(self):
        cleaned_data = super().clean()
        date = cleaned_data.get('date')
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        
        # Check if end time is after start time
        if start_time and end_time and start_time >= end_time:
            raise forms.ValidationError("End time must be after start time.")
        
        # Check if date is not in the past
        if date and date < timezone.now().date():
            raise forms.ValidationError("Session date cannot be in the past.")
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.course:
            instance.course = self.course
        if commit:
            instance.save()
        return instance


class QRCodeRefreshForm(forms.Form):
    """Form for refreshing a QR code"""
    
    duration = forms.IntegerField(
        min_value=5,
        max_value=60,
        initial=10,
        label="Duration (seconds)",
        help_text="How long the QR code should be valid for",
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
