from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from courses.models import Course, Module, Assignment, AssignmentSubmission, Enrollment, Category
from datetime import timedelta
from django.core.files.uploadedfile import SimpleUploadedFile
import os

User = get_user_model()

class Command(BaseCommand):
    help = 'Test the assignment workflow by creating sample data'

    def handle(self, *args, **options):
        self.stdout.write('Creating test assignment workflow data...')
        
        # Create test users if they don't exist
        instructor, created = User.objects.get_or_create(
            email='instructor@test.com',
            defaults={
                'username': 'instructor',
                'first_name': 'Test',
                'last_name': 'Instructor',
                'is_instructor': True,
                'is_staff': True,
            }
        )
        
        student, created = User.objects.get_or_create(
            email='student@test.com',
            defaults={
                'username': 'student',
                'first_name': 'Test',
                'last_name': 'Student',
                'is_instructor': False,
            }
        )
        
        if created:
            self.stdout.write(f'Created {instructor.email} as instructor')
            self.stdout.write(f'Created {student.email} as student')
        
        # Create test category
        category, created = Category.objects.get_or_create(
            name='Test Category',
            defaults={'description': 'A test category for assignment workflow testing'}
        )
        
        # Create a simple thumbnail file for the course
        # Create a simple text file as a placeholder thumbnail
        thumbnail_content = b'fake image content'
        thumbnail_file = SimpleUploadedFile(
            "test_thumbnail.jpg",
            thumbnail_content,
            content_type="image/jpeg"
        )
        
        # Create test course
        course, created = Course.objects.get_or_create(
            title='Test Course for Assignment Workflow',
            defaults={
                'description': 'This is a test course to verify the assignment workflow',
                'instructor': instructor,
                'category': category,
                'price': 0.00,
                'level': 'beginner',
                'duration': timedelta(hours=10),  # 10 hours duration
                'thumbnail': thumbnail_file,
                'is_published': True,
            }
        )
        
        if created:
            self.stdout.write(f'Created test course: {course.title}')
        
        # Create test module
        module, created = Module.objects.get_or_create(
            title='Test Module',
            course=course,
            defaults={
                'description': 'A test module for assignments',
                'order': 1,
            }
        )
        
        if created:
            self.stdout.write(f'Created test module: {module.title}')
        
        # Create test assignments with different due dates
        now = timezone.now()
        
        # Assignment 1: Due in the future (pending)
        assignment1, created = Assignment.objects.get_or_create(
            title='Future Assignment',
            course=course,
            defaults={
                'description': 'This assignment is due in the future',
                'module': module,
                'due_date': now + timedelta(days=7),
                'total_points': 100,
            }
        )
        
        # Assignment 2: Due in the past (overdue)
        assignment2, created = Assignment.objects.get_or_create(
            title='Overdue Assignment',
            course=course,
            defaults={
                'description': 'This assignment is overdue',
                'module': module,
                'due_date': now - timedelta(days=3),
                'total_points': 50,
            }
        )
        
        # Assignment 3: Due recently (submitted on time)
        assignment3, created = Assignment.objects.get_or_create(
            title='On-Time Assignment',
            course=course,
            defaults={
                'description': 'This assignment was submitted on time',
                'module': module,
                'due_date': now - timedelta(hours=2),
                'total_points': 75,
            }
        )
        
        # Assignment 4: Due recently (submitted late)
        assignment4, created = Assignment.objects.get_or_create(
            title='Late Assignment',
            course=course,
            defaults={
                'description': 'This assignment was submitted late',
                'module': module,
                'due_date': now - timedelta(hours=4),
                'total_points': 60,
            }
        )
        
        if created:
            self.stdout.write(f'Created test assignments')
        
        # Enroll student in the course
        enrollment, created = Enrollment.objects.get_or_create(
            student=student,
            course=course,
            defaults={'progress': 25}
        )
        
        if created:
            self.stdout.write(f'Enrolled {student.email} in {course.title}')
        
        # Create submissions for assignments 3 and 4
        submission3, created = AssignmentSubmission.objects.get_or_create(
            assignment=assignment3,
            student=student,
            defaults={
                'submission_text': 'This is my on-time submission for the assignment.',
                'submitted_at': now - timedelta(hours=3),  # Submitted 1 hour before deadline
            }
        )
        
        submission4, created = AssignmentSubmission.objects.get_or_create(
            assignment=assignment4,
            student=student,
            defaults={
                'submission_text': 'This is my late submission for the assignment.',
                'submitted_at': now - timedelta(hours=2),  # Submitted 2 hours after deadline
            }
        )
        
        # Auto-grade the late submission
        if submission4.submitted_at > assignment4.due_date and not submission4.graded_at:
            submission4.grade = 0
            submission4.feedback = "Assignment submitted after the deadline. Automatic grade: F"
            submission4.graded_at = now
            submission4.graded_by = instructor
            submission4.save()
            self.stdout.write('Auto-graded late submission as F')
        
        # Grade the on-time submission
        if not submission3.graded_at:
            submission3.grade = 85
            submission3.feedback = "Good work! Well-structured response with clear explanations."
            submission3.graded_at = now
            submission3.graded_by = instructor
            submission3.save()
            self.stdout.write('Graded on-time submission as 85/75')
        
        self.stdout.write(self.style.SUCCESS('Successfully created test assignment workflow data!'))
        self.stdout.write('\nTest Data Summary:')
        self.stdout.write(f'- Instructor: {instructor.email}')
        self.stdout.write(f'- courses: {student.email}')
        self.stdout.write(f'- Course: {course.title}')
        self.stdout.write(f'- Assignments: {Assignment.objects.filter(course=course).count()}')
        self.stdout.write(f'- Submissions: {AssignmentSubmission.objects.filter(assignment__course=course).count()}')
        self.stdout.write('\nYou can now test the workflow:')
        self.stdout.write('1. Login as instructor to grade assignments')
        self.stdout.write('2. Login as student to view assignments and grades')
        self.stdout.write('3. Test late submission auto-grading') 