from django import forms
from django.utils import timezone
from .models import Session, CourseSchedule


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


class CourseScheduleForm(forms.ModelForm):
    """Form for defining course schedules"""
    
    # Checkbox fields for each day of the week
    monday = forms.BooleanField(required=False, initial=False, label="Monday")
    tuesday = forms.BooleanField(required=False, initial=False, label="Tuesday")
    wednesday = forms.BooleanField(required=False, initial=False, label="Wednesday")
    thursday = forms.BooleanField(required=False, initial=False, label="Thursday")
    friday = forms.BooleanField(required=False, initial=False, label="Friday")
    saturday = forms.BooleanField(required=False, initial=False, label="Saturday")
    
    class Meta:
        model = CourseSchedule
        fields = ['start_time', 'end_time']
        widgets = {
            'start_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.course = kwargs.pop('course', None)
        super().__init__(*args, **kwargs)
    
    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        
        # Check if end time is after start time
        if start_time and end_time and start_time >= end_time:
            raise forms.ValidationError("End time must be after start time.")
        
        # At least one day must be selected
        days_selected = any([
            cleaned_data.get('monday', False),
            cleaned_data.get('tuesday', False),
            cleaned_data.get('wednesday', False),
            cleaned_data.get('thursday', False),
            cleaned_data.get('friday', False),
            cleaned_data.get('saturday', False),
        ])
        
        if not days_selected:
            raise forms.ValidationError("Please select at least one day of the week.")
        
        return cleaned_data
    
    def save(self, commit=True):
        """
        Save method creates multiple CourseSchedule instances,
        one for each selected day of the week
        """
        schedules = []
        if not self.course:
            return schedules
            
        start_time = self.cleaned_data.get('start_time')
        end_time = self.cleaned_data.get('end_time')
        
        day_mapping = {
            'monday': 0,
            'tuesday': 1,
            'wednesday': 2,
            'thursday': 3,
            'friday': 4,
            'saturday': 5,
        }
        
        # Create a schedule for each selected day
        for day_name, day_value in day_mapping.items():
            if self.cleaned_data.get(day_name, False):
                # Check if a schedule already exists for this day and time
                existing = CourseSchedule.objects.filter(
                    course=self.course,
                    day_of_week=day_value,
                    start_time=start_time,
                    end_time=end_time
                ).first()
                
                if existing:
                    # If it exists but was inactive, reactivate it
                    if not existing.is_active:
                        existing.is_active = True
                        existing.save()
                    schedules.append(existing)
                else:
                    # Create a new schedule
                    schedule = CourseSchedule(
                        course=self.course,
                        day_of_week=day_value,
                        start_time=start_time,
                        end_time=end_time
                    )
                    if commit:
                        schedule.save()
                    schedules.append(schedule)
        
        return schedules


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
