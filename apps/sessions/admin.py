from django.contrib import admin
from .models import Session


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'date', 'start_time', 'end_time', 'is_active', 'is_closed', 'qr_is_valid')
    list_filter = ('date', 'course', 'is_closed')
    search_fields = ('title', 'description', 'course__name')
    readonly_fields = ('created_at', 'updated_at', 'qr_code_token', 'qr_expiry_time')
    date_hierarchy = 'date'
    
    fieldsets = (
        (None, {
            'fields': ('course', 'title', 'description')
        }),
        ('Schedule', {
            'fields': ('date', 'start_time', 'end_time', 'is_closed')
        }),
        ('QR Code', {
            'fields': ('qr_code_token', 'qr_expiry_time')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def is_active(self, obj):
        return obj.is_active
    is_active.boolean = True
    
    def qr_is_valid(self, obj):
        return obj.qr_is_valid
    qr_is_valid.boolean = True
