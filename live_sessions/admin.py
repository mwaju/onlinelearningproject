from django.contrib import admin
from .models import LiveSession, SessionParticipant, SessionChat

class SessionParticipantInline(admin.TabularInline):
    model = SessionParticipant
    extra = 1
    ordering = ('joined_at',)

class SessionChatInline(admin.TabularInline):
    model = SessionChat
    extra = 1
    ordering = ('timestamp',)
    readonly_fields = ('timestamp',)

@admin.register(LiveSession)
class LiveSessionAdmin(admin.ModelAdmin):
    list_display = ('title', 'instructor', 'course', 'start_time', 'end_time', 'status')
    list_filter = ('status', 'course', 'start_time')
    search_fields = ('title', 'description', 'instructor__email', 'course__title')
    ordering = ('-start_time',)
    inlines = [SessionParticipantInline, SessionChatInline]
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('title', 'description', 'instructor', 'course')
        }),
        ('Schedule', {
            'fields': ('start_time', 'end_time')
        }),
        ('Session Details', {
            'fields': ('status', 'meeting_link', 'recording_url')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(SessionParticipant)
class SessionParticipantAdmin(admin.ModelAdmin):
    list_display = ('user', 'session', 'joined_at', 'left_at', 'is_presenter')
    list_filter = ('is_presenter', 'joined_at')
    search_fields = ('user__email', 'session__title')
    ordering = ('-joined_at',)
    readonly_fields = ('joined_at', 'left_at')

@admin.register(SessionChat)
class SessionChatAdmin(admin.ModelAdmin):
    list_display = ('user', 'session', 'message', 'timestamp')
    list_filter = ('session', 'timestamp')
    search_fields = ('message', 'user__email', 'session__title')
    ordering = ('-timestamp',)
    readonly_fields = ('timestamp',)
