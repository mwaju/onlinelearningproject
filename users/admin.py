from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, InstructorApplication

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'username', 'first_name', 'last_name', 'is_instructor', 'is_staff', 'is_active')
    list_filter = ('is_instructor', 'is_staff', 'is_active', 'groups')
    search_fields = ('email', 'username', 'first_name', 'last_name')
    ordering = ('email',)
    
    fieldsets = (
        (None, {'fields': ('email', 'username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'bio', 'profile_picture',
                                    'date_of_birth', 'phone_number', 'address')}),
        ('Permissions', {'fields': ('is_instructor', 'is_active', 'is_staff', 'is_superuser',
                                  'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2', 'is_instructor',
                      'is_staff', 'is_active')}
        ),
    )

@admin.register(InstructorApplication)
class InstructorApplicationAdmin(admin.ModelAdmin):
    list_display = ('user', 'status', 'applied_at', 'reviewed_at')
    list_filter = ('status', 'applied_at', 'reviewed_at')
    search_fields = ('user__email', 'user__first_name', 'user__last_name')
    readonly_fields = ('applied_at', 'reviewed_at')
    ordering = ('-applied_at',)
    
    fieldsets = (
        ('Application Details', {
            'fields': ('user', 'resume', 'cover_letter', 'status')
        }),
        ('Review Information', {
            'fields': ('admin_notes', 'reviewed_at'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('applied_at',),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['approve_applications', 'reject_applications']
    
    def approve_applications(self, request, queryset):
        for application in queryset.filter(status='pending'):
            application.approve()
        self.message_user(request, f"{queryset.count()} applications approved successfully.")
    approve_applications.short_description = "Approve selected applications"
    
    def reject_applications(self, request, queryset):
        for application in queryset.filter(status='pending'):
            application.reject()
        self.message_user(request, f"{queryset.count()} applications rejected successfully.")
    reject_applications.short_description = "Reject selected applications"
