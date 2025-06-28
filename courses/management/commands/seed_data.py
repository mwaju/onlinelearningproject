import random
import os
import json
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.core.files import File
from django.utils import timezone
from courses.models import Course, Module, Lesson, Category, Enrollment, Rating
from users.models import User, InstructorApplication
from discussions.models import Discussion, Comment
from live_sessions.models import LiveSession, SessionParticipant, SessionChat
from payments.models import Payment, Refund
from faker import Faker

fake = Faker()

class Command(BaseCommand):
    help = 'Seeds the database with demo data for the e-learning platform'

    def handle(self, *args, **options):
        self.stdout.write('Seeding database with demo data...')
        
        # Clear existing data
        self.clear_data()
        
        # Create data
        self.create_categories()
        self.create_users()
        self.create_courses()
        self.create_enrollments()
        self.create_ratings()
        self.create_discussions_and_comments()
        self.create_live_sessions()
        self.create_payments()
        
        self.stdout.write(self.style.SUCCESS('Successfully seeded demo data!'))
    
    def clear_data(self):
        """Clear existing data"""
        self.stdout.write('Clearing existing data...')
        models = [
            Rating, Enrollment, Lesson, Module, Course, Category,
            Discussion, Comment, LiveSession, SessionParticipant, 
            SessionChat, Payment, Refund, InstructorApplication
        ]
        for model in models:
            model.objects.all().delete()
        
        # Clear users except superusers
        User = get_user_model()
        User.objects.filter(is_superuser=False).delete()
    
    def create_categories(self):
        """Create course categories"""
        self.stdout.write('Creating categories...')
        categories = [
            'Web Development', 'Mobile Development', 'Data Science', 
            'Business', 'Design', 'Marketing', 'Photography', 'Music',
            'Language', 'Personal Development', 'IT & Software', 'Health & Fitness',
            'Academics', 'Test Prep', 'Lifestyle', 'Other'
        ]
        self.categories = []
        for name in categories:
            category = Category.objects.create(
                name=name,
                description=fake.paragraph(nb_sentences=3)
            )
            self.categories.append(category)
    
    def create_users(self):
        """Create demo users"""
        self.stdout.write('Creating users...')
        User = get_user_model()
        
        # Create admin user if not exists
        admin_email = 'admin@example.com'
        if not User.objects.filter(email=admin_email).exists():
            admin = User.objects.create_superuser(
                username='admin',
                email=admin_email,
                password='admin123',
                first_name='Admin',
                last_name='User',
                is_staff=True,
                is_superuser=True
            )
            admin.is_email_verified = True
            admin.save()
        
        # Create instructors
        self.instructors = []
        instructor_data = [
            ('john_doe', 'john.doe@example.com', 'John', 'Doe', 'I love teaching web development!'),
            ('jane_smith', 'jane.smith@example.com', 'Jane', 'Smith', 'Data science enthusiast and educator'),
            ('mike_johnson', 'mike.johnson@example.com', 'Mike', 'Johnson', 'Mobile app development expert')
        ]
        
        for username, email, first_name, last_name, bio in instructor_data:
            if not User.objects.filter(email=email).exists():
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password='password123',
                    first_name=first_name,
                    last_name=last_name,
                    is_instructor=True,
                    bio=bio,
                    profile_picture=f'profile_pictures/instructor_{username}.jpg',
                    date_of_birth=fake.date_of_birth(minimum_age=25, maximum_age=60),
                    phone_number=fake.phone_number(),
                    is_email_verified=True
                )
                self.instructors.append(user)
            else:
                self.instructors.append(User.objects.get(email=email))
        
        # Create students
        self.students = []
        for i in range(10):
            first_name = fake.first_name()
            last_name = fake.last_name()
            username = f"student_{first_name.lower()}{i}"  # Remove underscore to avoid potential issues
            email = f"{first_name.lower()}.{last_name.lower()}{i}@example.com"  # More unique email pattern
            
            if not User.objects.filter(email=email).exists():
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password='password123',
                    first_name=first_name,
                    last_name=last_name,
                    is_instructor=False,
                    bio=fake.paragraph(),
                    profile_picture=f'profile_pictures/student_{username}.jpg',
                    date_of_birth=fake.date_of_birth(minimum_age=18, maximum_age=80),
                    phone_number=fake.phone_number(),
                    address=fake.address(),
                    is_email_verified=random.choice([True, False])
                )
                self.students.append(user)
            else:
                # If user exists, use existing user
                user = User.objects.get(email=email)
                if not user.is_instructor:  # Only add if not an instructor
                    self.students.append(user)
                
            # Ensure we have enough unique students
            if len(self.students) >= 10:
                break
    
    def parse_duration(self, duration_str):
        """Convert duration string to timedelta"""
        duration_parts = duration_str.split()
        duration_value = int(duration_parts[0])
        duration_unit = duration_parts[1].lower()
        
        if 'hour' in duration_unit:
            return timedelta(hours=duration_value)
        elif 'min' in duration_unit:
            return timedelta(minutes=duration_value)
        return timedelta(days=duration_value)
    
    def create_courses(self):
        """Create demo courses with modules and lessons"""
        self.stdout.write('Creating courses...')
        
        course_data = [
            {
                'title': 'Introduction to Python',
                'description': 'Learn Python from scratch',
                'price': 99.99,
                'level': 'beginner',
                'duration': '30 hours',
                'modules': [
                    {
                        'title': 'Python Basics',
                        'description': 'Learn the basics of Python',
                        'order': 1,
                        'lessons': [
                            {'title': 'Variables and Data Types', 'duration': '30 min', 'order': 1, 'content': 'Introduction to variables'},
                             {'title': 'Control Flow', 'duration': '45 min', 'order': 2, 'content': 'If statements and loops'}
                        ]
                    },
                    {
                        'title': 'Functions and Modules',
                        'description': 'Learn about functions and modules',
                        'order': 2,
                        'lessons': [
                            {'title': 'Defining Functions', 'duration': '40 min', 'order': 1, 'content': 'How to define and use functions'},
                             {'title': 'Working with Modules', 'duration': '35 min', 'order': 2, 'content': 'Importing and using modules'}
                        ]
                    }
                ]
            },
            {
                'title': 'Web Development with Django',
                'description': 'Build web applications with Django',
                'price': 199.99,
                'level': 'intermediate',
                'duration': '50 hours',
                'modules': [
                    {
                        'title': 'Django Basics',
                        'description': 'Introduction to Django framework',
                        'order': 1,
                        'lessons': [
                            {'title': 'Django Overview', 'duration': '30 min', 'order': 1, 'content': 'Introduction to Django'},
                             {'title': 'Models and Migrations', 'duration': '60 min', 'order': 2, 'content': 'Working with database models'}
                        ]
                    }
                ]
            },
            {
                'title': 'Data Science with Python',
                'description': 'Master data analysis and visualization',
                'price': 299.99,
                'level': 'advanced',
                'duration': '40 hours',
                'modules': [
                    {
                        'title': 'Pandas Fundamentals',
                        'description': 'Data manipulation with Pandas',
                        'order': 1,
                        'lessons': [
                            {'title': 'Introduction to Pandas', 'duration': '45 min', 'order': 1, 'content': 'Pandas basics'},
                             {'title': 'Data Cleaning', 'duration': '60 min', 'order': 2, 'content': 'Cleaning and preparing data'}
                        ]
                    }
                ]
            }
        ]
        
        self.courses = []
        
        # List of placeholder image URLs for courses
        placeholder_images = [
            'https://images.unsplash.com/photo-1501504905252-473c47e087f8?w=800&auto=format&fit=crop',  # Python
            'https://images.unsplash.com/photo-1551434678-e076c223a692?w=800&auto=format&fit=crop',  # Web Dev
            'https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=800&auto=format&fit=crop',  # Data Science
            'https://images.unsplash.com/photo-1461749280684-dccba630e2f6?w=800&auto=format&fit=crop',  # Coding
            'https://images.unsplash.com/photo-1617791168926-4a0c8daa4b3a?w=800&auto=format&fit=crop'   # Programming
        ]
        
        for i, course_info in enumerate(course_data):
            instructor = random.choice(self.instructors)
            category = random.choice(self.categories)
            
            # Create course with a thumbnail URL
            course = Course(
                title=course_info['title'],
                slug=f"{course_info['title'].lower().replace(' ', '-')}-{i+1}",
                description=course_info['description'],
                price=course_info['price'],
                level=course_info['level'],
                duration=self.parse_duration(course_info['duration']),
                instructor=instructor,
                category=category,
                is_published=True,
                thumbnail=placeholder_images[i % len(placeholder_images)]
            )
            course.save()
            
            # Create modules and lessons
            for module_info in course_info['modules']:
                module = Module.objects.create(
                    course=course,
                    title=module_info['title'],
                    description=module_info['description'],
                    order=module_info['order']
                )
                
                for lesson_info in module_info['lessons']:
                    Lesson.objects.create(
                        module=module,
                        title=lesson_info['title'],
                        duration=self.parse_duration(lesson_info['duration']),
                        content=lesson_info['content'],
                        order=lesson_info['order']
                    )
            
            self.courses.append(course)
    
    def create_ratings(self):
        """Create demo ratings for courses"""
        self.stdout.write('Creating ratings...')
        
        for course in self.courses:
            # Get students enrolled in this course
            enrolled_students = [e.student for e in course.enrollments.all()]
            
            # 30-80% of enrolled students will rate the course
            num_ratings = random.randint(
                int(len(enrolled_students) * 0.3),
                int(len(enrolled_students) * 0.8)
            )
            
            if num_ratings > 0:
                rating_students = random.sample(enrolled_students, num_ratings)
                
                for student in rating_students:
                    Rating.objects.create(
                        course=course,
                        user=student,
                        rating=random.choices(
                            [1, 2, 3, 4, 5],
                            weights=[0.05, 0.1, 0.15, 0.3, 0.4]  # More likely to get higher ratings
                        )[0],
                        comment=fake.paragraph(nb_sentences=3) if random.random() > 0.3 else ''
                    )
    
    def create_discussions_and_comments(self):
        """Create demo discussions and comments"""
        self.stdout.write('Creating discussions and comments...')
        
        for course in self.courses:
            # Create 3-10 discussions per course
            num_discussions = random.randint(3, 10)
            
            for _ in range(num_discussions):
                # Randomly select a lesson from the course for some discussions
                lesson = None
                if course.modules.exists() and random.random() > 0.5:
                    module = random.choice(course.modules.all())
                    if module.lessons.exists():
                        lesson = random.choice(module.lessons.all())
                
                discussion = Discussion.objects.create(
                    title=fake.sentence(),
                    content=fake.paragraph(nb_sentences=5),
                    course=course,
                    lesson=lesson,
                    author=random.choice(self.students + self.instructors),
                    is_pinned=random.random() > 0.8,  # 20% chance of being pinned
                    is_closed=random.random() > 0.9    # 10% chance of being closed
                )
                
                # Create 1-10 comments per discussion
                num_comments = random.randint(1, 10)
                for _ in range(num_comments):
                    Comment.objects.create(
                        discussion=discussion,
                        author=random.choice(self.students + self.instructors),
                        content=fake.paragraph(nb_sentences=3),
                        is_solution=random.random() > 0.9  # 10% chance of being marked as solution
                    )
    
    def create_live_sessions(self):
        """Create demo live sessions"""
        self.stdout.write('Creating live sessions...')
        
        status_weights = {
            'scheduled': 0.6,
            'live': 0.1,
            'ended': 0.3,
            'cancelled': 0.0
        }
        
        for course in self.courses:
            if not course.instructor:
                continue
                
            # Create 1-3 live sessions per course
            num_sessions = random.randint(1, 3)
            
            for i in range(num_sessions):
                start_time = timezone.now() + timedelta(days=random.randint(-30, 30))
                end_time = start_time + timedelta(hours=random.randint(1, 3))
                
                session = LiveSession.objects.create(
                    title=f"Live Session {i+1}: {fake.sentence(4)[:-1]}",
                    description=fake.paragraph(nb_sentences=3),
                    course=course,
                    instructor=course.instructor,
                    start_time=start_time,
                    end_time=end_time,
                    status=random.choices(
                        list(status_weights.keys()),
                        weights=list(status_weights.values())
                    )[0],
                    meeting_link=f"https://meet.example.com/{fake.uuid4()}",
                    recording_url=f"https://recordings.example.com/{fake.uuid4()}" if random.random() > 0.7 else ''
                )
                
                # Add participants
                enrolled_students = [e.student for e in course.enrollments.all()]
                if enrolled_students:
                    # 30-100% of enrolled students join the session
                    num_participants = random.randint(
                        max(1, int(len(enrolled_students) * 0.3)),
                        len(enrolled_students)
                    )
                    participants = random.sample(enrolled_students, num_participants)
                    
                    for student in participants:
                        joined_at = start_time + timedelta(minutes=random.randint(-5, 30))
                        left_at = (
                            joined_at + timedelta(minutes=random.randint(30, 120))
                            if joined_at < end_time else None
                        )
                        
                        SessionParticipant.objects.create(
                            session=session,
                            user=student,
                            joined_at=joined_at,
                            left_at=left_at,
                            is_presenter=student == course.instructor
                        )
                        
                        # Add some chat messages
                        if left_at:
                            current_time = joined_at
                            while current_time < (left_at or end_time):
                                if random.random() > 0.7:  # 30% chance of a message per minute
                                    SessionChat.objects.create(
                                        session=session,
                                        user=student,
                                        message=fake.sentence(),
                                        timestamp=current_time
                                    )
                                current_time += timedelta(minutes=1)
    
    def create_payments(self):
        """Create demo payments"""
        self.stdout.write('Creating payments...')
        
        payment_methods = ['card', 'bank_transfer', 'paypal']
        
        for enrollment in Enrollment.objects.all():
            if random.random() > 0.8:  # 80% chance of having a payment
                payment = Payment.objects.create(
                    student=enrollment.student,
                    course=enrollment.course,
                    amount=enrollment.course.price,
                    currency='USD',
                    status=random.choices(
                        ['pending', 'completed', 'failed', 'refunded'],
                        weights=[0.1, 0.8, 0.05, 0.05]
                    )[0],
                    payment_method=random.choice(payment_methods),
                    stripe_payment_id=f'pi_{fake.uuid4().replace("-", "")}',
                    stripe_customer_id=f'cus_{fake.uuid4().replace("-", "")}',
                    created_at=enrollment.enrolled_at,
                    metadata={
                        'enrollment_id': str(enrollment.id),
                        'course_title': enrollment.course.title
                    }
                )
                
                # Create a refund for some completed payments
                if payment.status == 'completed' and random.random() > 0.9:  # 10% chance of refund
                    from decimal import Decimal
                    refund_percentage = Decimal(str(random.uniform(0.5, 1.0)))
                    Refund.objects.create(
                        payment=payment,
                        amount=payment.amount * refund_percentage,  # 50-100% refund
                        currency=payment.currency,
                        status=random.choice(['pending', 'completed', 'failed']),
                        reason=random.choice([
                            'Changed my mind',
                            'Course not as described',
                            'Technical issues',
                            'Other'
                        ]),
                        stripe_refund_id=f're_{fake.uuid4().replace("-", "")}',
                        created_at=payment.created_at + timedelta(days=random.randint(1, 30)),
                        metadata={
                            'original_payment_id': str(payment.id),
                            'refund_reason': 'Customer request'
                        }
                    )
    
    def create_enrollments(self):
        """Create demo enrollments"""
        self.stdout.write('Creating enrollments...')
        
        for student in self.students:
            # Each student enrolls in some courses
            num_courses = random.randint(1, len(self.courses))
            enrolled_courses = random.sample(self.courses, num_courses)
            
            for course in enrolled_courses:
                # Random completion status (20% chance of completed)
                is_completed = random.random() < 0.2
                progress = 100 if is_completed else random.randint(0, 99)
                enrolled_at = timezone.now() - timedelta(days=random.randint(1, 180))
                
                enrollment = Enrollment.objects.create(
                    student=student,
                    course=course,
                    progress=progress,
                    completed=is_completed,
                    enrolled_at=enrolled_at
                )
                
                if is_completed:
                    enrollment.completed_at = enrolled_at + timedelta(days=random.randint(1, 30))
                    enrollment.save()
