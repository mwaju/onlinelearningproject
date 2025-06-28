from django.db import models
from django.db.models import Avg, Count
from .models import Course, Module, Lesson, Enrollment

class CourseService:
    @staticmethod
    def create_course(instructor, **data):
        """Create a new course with the given details."""
        course = Course.objects.create(instructor=instructor, **data)
        return course

    @staticmethod
    def update_course(course, **data):
        """Update course information."""
        for field, value in data.items():
            if hasattr(course, field):
                setattr(course, field, value)
        course.save()
        return course

    @staticmethod
    def get_course_stats(course):
        """Get statistics for a course."""
        return {
            'total_students': course.enrollments.count(),
            'completion_rate': (course.enrollments.filter(completed=True).count() / 
                              course.enrollments.count() * 100) if course.enrollments.exists() else 0,
            'average_rating': course.ratings.aggregate(Avg('rating'))['rating__avg'] or 0,
            'total_revenue': course.payments.aggregate(models.Sum('amount'))['amount__sum'] or 0
        }

    @staticmethod
    def get_popular_courses(limit=10):
        """Get the most popular courses."""
        return Course.objects.annotate(
            enrollment_count=Count('enrollments'),
            average_rating=Avg('ratings__rating')
        ).order_by('-enrollment_count', '-average_rating')[:limit]

class ModuleService:
    @staticmethod
    def create_module(course, **data):
        """Create a new module for a course."""
        # Get the next order number
        next_order = Module.objects.filter(course=course).count() + 1
        module = Module.objects.create(course=course, order=next_order, **data)
        return module

    @staticmethod
    def reorder_modules(course, module_order):
        """Reorder modules in a course."""
        for order, module_id in enumerate(module_order, 1):
            Module.objects.filter(id=module_id, course=course).update(order=order)

class LessonService:
    @staticmethod
    def create_lesson(module, **data):
        """Create a new lesson for a module."""
        next_order = Lesson.objects.filter(module=module).count() + 1
        lesson = Lesson.objects.create(module=module, order=next_order, **data)
        return lesson

    @staticmethod
    def reorder_lessons(module, lesson_order):
        """Reorder lessons in a module."""
        for order, lesson_id in enumerate(lesson_order, 1):
            Lesson.objects.filter(id=lesson_id, module=module).update(order=order)

class EnrollmentService:
    @staticmethod
    def enroll_student(course, student):
        """Enroll a student in a course."""
        enrollment, created = Enrollment.objects.get_or_create(
            course=course,
            student=student,
            defaults={'progress': 0}
        )
        return enrollment

    @staticmethod
    def update_progress(enrollment, progress):
        """Update student's progress in a course."""
        enrollment.progress = progress
        if progress >= 100:
            enrollment.completed = True
        enrollment.save()
        return enrollment

    @staticmethod
    def get_student_progress(enrollment):
        """Get detailed progress information for a student."""
        total_lessons = Lesson.objects.filter(module__course=enrollment.course).count()
        completed_lessons = enrollment.progress * total_lessons / 100
        return {
            'total_lessons': total_lessons,
            'completed_lessons': int(completed_lessons),
            'progress_percentage': enrollment.progress,
            'is_completed': enrollment.completed
        } 