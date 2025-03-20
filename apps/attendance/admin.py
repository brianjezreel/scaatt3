from django.contrib import admin
from .models import Attendance


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('student', 'session', 'check_in_time', 'status')
    list_filter = ('status', 'check_in_time', 'session__course')
    search_fields = ('student__email', 'student__first_name', 'student__last_name', 'session__title', 'session__course__name')
    date_hierarchy = 'check_in_time'
    
    fieldsets = (
        (None, {
            'fields': ('session', 'student', 'status')
        }),
        ('Check-in Details', {
            'fields': ('check_in_time', 'notes')
        }),
        ('Technical Information', {
            'fields': ('ip_address', 'device_info'),
            'classes': ('collapse',)
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # Editing an existing object
            return ('session', 'student', 'check_in_time', 'ip_address', 'device_info')
        return ()
