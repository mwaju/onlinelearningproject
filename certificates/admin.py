from django.contrib import admin
from .models import Certificate

@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ('user', 'course', 'certificate_number', 'issue_date', 'is_verified')
    list_filter = ('is_verified', 'issue_date')
    search_fields = ('user__email', 'course__title', 'certificate_number', 'verification_code')
    ordering = ('-issue_date',)
    readonly_fields = ('certificate_number', 'issue_date', 'verification_code', 'created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('user', 'course')
        }),
        ('Certificate Details', {
            'fields': ('certificate_number', 'verification_code', 'pdf_file')
        }),
        ('Verification', {
            'fields': ('is_verified',)
        }),
        ('Timestamps', {
            'fields': ('issue_date', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
