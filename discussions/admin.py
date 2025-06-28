from django.contrib import admin
from .models import Discussion, Comment

class CommentInline(admin.TabularInline):
    model = Comment
    extra = 1
    ordering = ('created_at',)

@admin.register(Discussion)
class DiscussionAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'course', 'lesson', 'is_pinned', 'is_closed', 'created_at')
    list_filter = ('is_pinned', 'is_closed', 'course', 'created_at')
    search_fields = ('title', 'content', 'author__email', 'course__title')
    ordering = ('-is_pinned', '-created_at')
    inlines = [CommentInline]
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('title', 'content', 'author', 'course', 'lesson')
        }),
        ('Status', {
            'fields': ('is_pinned', 'is_closed')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('author', 'discussion', 'is_solution', 'created_at')
    list_filter = ('is_solution', 'created_at')
    search_fields = ('content', 'author__email', 'discussion__title')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('discussion', 'author', 'content')
        }),
        ('Status', {
            'fields': ('is_solution',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
