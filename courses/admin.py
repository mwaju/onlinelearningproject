from django.contrib import admin
from .models import Category, Course, Module, Lesson, Enrollment

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'created_at')
    search_fields = ('name', 'description')
    ordering = ('name',)

class ModuleInline(admin.TabularInline):
    model = Module
    extra = 1
    ordering = ('order',)

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title','slug', 'instructor', 'category', 'price', 'level', 'is_published', 'created_at')
    list_filter = ('is_published', 'level', 'category', 'instructor')
    search_fields = ('title', 'description', 'instructor__email')
    ordering = ('-created_at',)
    inlines = [ModuleInline]
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('title', 'slug', 'description', 'instructor', 'category')
        }),
        ('Course Details', {
            'fields': ('price', 'thumbnail', 'duration', 'level')
        }),
        ('Status', {
            'fields': ('is_published',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 1
    ordering = ('order',)

@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'order', 'created_at')
    list_filter = ('course',)
    search_fields = ('title', 'description', 'course__title')
    ordering = ('course', 'order')
    inlines = [LessonInline]

@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'module', 'order', 'duration', 'created_at')
    list_filter = ('module__course', 'module')
    search_fields = ('title', 'content', 'module__title')
    ordering = ('module', 'order')
    readonly_fields = ('created_at',)

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'enrolled_at', 'completed', 'progress')
    list_filter = ('completed', 'course', 'enrolled_at')
    search_fields = ('student__email', 'course__title')
    ordering = ('-enrolled_at',)
    readonly_fields = ('enrolled_at',)
    fieldsets = (
        (None, {
            'fields': ('student', 'course')
        }),
        ('Progress', {
            'fields': ('completed', 'progress')
        }),
        ('Timestamps', {
            'fields': ('enrolled_at',),
            'classes': ('collapse',)
        }),
    )
