from django.contrib import admin
from .models import Course, CourseEnrollment


class CourseEnrollmentInline(admin.TabularInline):
    model = CourseEnrollment
    extra = 1
    readonly_fields = ['enrollment_date']


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'teacher', 'student_count', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'code', 'description', 'teacher__email', 'teacher__first_name', 'teacher__last_name')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [CourseEnrollmentInline]


@admin.register(CourseEnrollment)
class CourseEnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'enrollment_date', 'is_active')
    list_filter = ('is_active', 'enrollment_date')
    search_fields = ('student__email', 'student__first_name', 'student__last_name', 'course__name', 'course__code')
    readonly_fields = ['enrollment_date']
