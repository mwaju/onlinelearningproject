import random
import os
import json
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.core.files import File
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from django.db import transaction

# Import all models from all apps
from courses.models import (
    Course, Module, Lesson, Category, Enrollment, Rating, 
    Assignment, AssignmentSubmission, Quiz, Question, Choice,
    QuizSubmission, QuizAnswer
)
from users.models import User, InstructorApplication
from discussions.models import Discussion, Comment
from live_sessions.models import LiveSession, SessionParticipant, SessionChat
from payments.models import Payment, Refund
from certificates.models import Certificate
from faker import Faker

fake = Faker()

class Command(BaseCommand):
    help = 'Seeds the database with comprehensive demo data for the entire e-learning platform'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear all existing data before seeding',
        )

    def handle(self, *args, **options):
        self.stdout.write('🌱 Seeding database with comprehensive demo data...')
        
        if options['clear']:
            self.clear_data()
        
        # Create data in proper order
        with transaction.atomic():
            self.create_categories()
            self.create_users()
            self.create_courses_with_content()
            self.create_assignments_and_quizzes()
            self.create_enrollments()
            self.create_assignments_and_submissions()
            self.create_quiz_submissions()
            self.create_ratings()
            self.create_discussions_and_comments()
            self.create_live_sessions()
            self.create_payments()
            self.create_certificates()
            self.create_instructor_applications()
        
        self.stdout.write(self.style.SUCCESS('✅ Successfully seeded comprehensive demo data!'))
        self.print_summary()
    
    def clear_data(self):
        """Clear existing data"""
        self.stdout.write('🧹 Clearing existing data...')
        
        # Clear in reverse dependency order
        models_to_clear = [
            QuizAnswer, QuizSubmission, Choice, Question, Quiz,
            AssignmentSubmission, Assignment,
            SessionChat, SessionParticipant, LiveSession,
            Comment, Discussion,
            Certificate,
            Refund, Payment,
            Rating, Enrollment, 
            Lesson, Module, Course, Category,
            InstructorApplication
        ]
        
        for model in models_to_clear:
            count = model.objects.count()
            model.objects.all().delete()
            if count > 0:
                self.stdout.write(f'   Cleared {count} {model.__name__} objects')
        
        # Clear users except superusers
        User = get_user_model()
        user_count = User.objects.filter(is_superuser=False).count()
        User.objects.filter(is_superuser=False).delete()
        if user_count > 0:
            self.stdout.write(f'   Cleared {user_count} regular users')
    
    def create_categories(self):
        """Create course categories"""
        self.stdout.write('📚 Creating categories...')
        categories_data = [
            ('Web Development', 'Learn modern web development technologies'),
            ('Mobile Development', 'Build mobile apps for iOS and Android'),
            ('Data Science', 'Master data analysis and machine learning'),
            ('Business', 'Business and entrepreneurship courses'),
            ('Design', 'Graphic design and UI/UX courses'),
            ('Marketing', 'Digital marketing and SEO strategies'),
            ('Photography', 'Photography and videography skills'),
            ('Music', 'Music production and theory'),
            ('Language', 'Learn new languages'),
            ('Personal Development', 'Self-improvement and life skills'),
            ('IT & Software', 'IT certifications and software skills'),
            ('Health & Fitness', 'Health, fitness, and wellness'),
            ('Academics', 'Academic subjects and test prep'),
            ('Lifestyle', 'Lifestyle and hobby courses'),
        ]
        
        self.categories = []
        for name, description in categories_data:
            category = Category.objects.create(
                name=name,
                description=description
            )
            self.categories.append(category)
            self.stdout.write(f'   Created category: {name}')
    
    def create_users(self):
        """Create demo users"""
        self.stdout.write('👥 Creating users...')
        User = get_user_model()
        
        # Create admin user
        admin_email = 'admin@edulearn.com'
        if not User.objects.filter(email=admin_email).exists():
            admin = User.objects.create_superuser(
                username='admin',
                email=admin_email,
                password='admin123',
                first_name='Admin',
                last_name='User',
                is_staff=True,
                is_superuser=True,
                is_email_verified=True
            )
            self.stdout.write(f'   Created admin: {admin_email}')
        
        # Create 1 instructor
        self.instructors = []
        instructor_data = [
            ('john_doe', 'john.doe@edulearn.com', 'John', 'Doe', 
             'Experienced web developer and educator with 10+ years of experience teaching modern web technologies. Passionate about helping students master full-stack development.', 
             'Web Development Expert')
        ]
        
        for username, email, first_name, last_name, bio, expertise in instructor_data:
            if not User.objects.filter(email=email).exists():
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password='password123',
                    first_name=first_name,
                    last_name=last_name,
                    is_instructor=True,
                    bio=bio,
                    expertise=expertise,
                    date_of_birth=fake.date_of_birth(minimum_age=30, maximum_age=50),
                    phone_number=fake.phone_number(),
                    address=fake.address(),
                    is_email_verified=True
                )
                self.instructors.append(user)
                self.stdout.write(f'   Created instructor: {email}')
            else:
                self.instructors.append(User.objects.get(email=email))
        
        # Create 3 students
        self.students = []
        student_data = [
            ('alice_smith', 'alice.smith@edulearn.com', 'Alice', 'Smith', 'Computer Science student'),
            ('bob_johnson', 'bob.johnson@edulearn.com', 'Bob', 'Johnson', 'Aspiring web developer'),
            ('carol_wilson', 'carol.wilson@edulearn.com', 'Carol', 'Wilson', 'Design enthusiast')
        ]
        
        for username, email, first_name, last_name, bio in student_data:
            if not User.objects.filter(email=email).exists():
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password='password123',
                    first_name=first_name,
                    last_name=last_name,
                    is_instructor=False,
                    bio=bio,
                    date_of_birth=fake.date_of_birth(minimum_age=18, maximum_age=35),
                    phone_number=fake.phone_number(),
                    address=fake.address(),
                    is_email_verified=True
                )
                self.students.append(user)
                self.stdout.write(f'   Created student: {email}')
            else:
                self.students.append(User.objects.get(email=email))
    
    def create_courses_with_content(self):
        """Create 3 fully loaded courses with modules and lessons"""
        self.stdout.write('📖 Creating courses with content...')
        
        course_data = [
            {
                'title': 'Complete Web Development Bootcamp',
                'description': 'Learn HTML, CSS, JavaScript, React, Node.js, and MongoDB to build modern web applications from scratch.',
                'price': 199.99,
                'level': 'beginner',
                'duration': timedelta(hours=40),
                'category': 'Web Development',
                'modules': [
                    {
                        'title': 'HTML & CSS Fundamentals',
                        'description': 'Learn the basics of HTML and CSS',
                        'order': 1,
                        'lessons': [
                            {'title': 'Introduction to HTML', 'duration': timedelta(minutes=45), 'order': 1, 'content': fake.text(max_nb_chars=2000)},
                            {'title': 'CSS Styling Basics', 'duration': timedelta(minutes=60), 'order': 2, 'content': fake.text(max_nb_chars=2000)},
                            {'title': 'Responsive Design', 'duration': timedelta(minutes=75), 'order': 3, 'content': fake.text(max_nb_chars=2000)}
                        ]
                    },
                    {
                        'title': 'JavaScript Programming',
                        'description': 'Master JavaScript fundamentals',
                        'order': 2,
                        'lessons': [
                            {'title': 'JavaScript Basics', 'duration': timedelta(minutes=60), 'order': 1, 'content': fake.text(max_nb_chars=2000)},
                            {'title': 'DOM Manipulation', 'duration': timedelta(minutes=75), 'order': 2, 'content': fake.text(max_nb_chars=2000)},
                            {'title': 'ES6+ Features', 'duration': timedelta(minutes=90), 'order': 3, 'content': fake.text(max_nb_chars=2000)}
                        ]
                    },
                    {
                        'title': 'React Development',
                        'description': 'Build modern UIs with React',
                        'order': 3,
                        'lessons': [
                            {'title': 'React Fundamentals', 'duration': timedelta(minutes=90), 'order': 1, 'content': fake.text(max_nb_chars=2000)},
                            {'title': 'State Management', 'duration': timedelta(minutes=105), 'order': 2, 'content': fake.text(max_nb_chars=2000)},
                            {'title': 'Advanced React Patterns', 'duration': timedelta(minutes=120), 'order': 3, 'content': fake.text(max_nb_chars=2000)}
                        ]
                    }
                ]
            },
            {
                'title': 'Data Science Masterclass',
                'description': 'Master Python, pandas, numpy, matplotlib, and machine learning algorithms for data analysis and visualization.',
                'price': 299.99,
                'level': 'intermediate',
                'duration': timedelta(hours=50),
                'category': 'Data Science',
                'modules': [
                    {
                        'title': 'Python for Data Science',
                        'description': 'Learn Python programming for data analysis',
                        'order': 1,
                        'lessons': [
                            {'title': 'Python Basics Review', 'duration': timedelta(minutes=60), 'order': 1, 'content': fake.text(max_nb_chars=2000)},
                            {'title': 'Working with Data Structures', 'duration': timedelta(minutes=75), 'order': 2, 'content': fake.text(max_nb_chars=2000)},
                            {'title': 'File I/O and Data Processing', 'duration': timedelta(minutes=90), 'order': 3, 'content': fake.text(max_nb_chars=2000)}
                        ]
                    },
                    {
                        'title': 'Data Analysis with Pandas',
                        'description': 'Master pandas for data manipulation',
                        'order': 2,
                        'lessons': [
                            {'title': 'Pandas Introduction', 'duration': timedelta(minutes=75), 'order': 1, 'content': fake.text(max_nb_chars=2000)},
                            {'title': 'Data Cleaning and Preprocessing', 'duration': timedelta(minutes=90), 'order': 2, 'content': fake.text(max_nb_chars=2000)},
                            {'title': 'Advanced Pandas Operations', 'duration': timedelta(minutes=105), 'order': 3, 'content': fake.text(max_nb_chars=2000)}
                        ]
                    },
                    {
                        'title': 'Data Visualization',
                        'description': 'Create compelling visualizations',
                        'order': 3,
                        'lessons': [
                            {'title': 'Matplotlib Basics', 'duration': timedelta(minutes=60), 'order': 1, 'content': fake.text(max_nb_chars=2000)},
                            {'title': 'Seaborn for Statistical Plots', 'duration': timedelta(minutes=75), 'order': 2, 'content': fake.text(max_nb_chars=2000)},
                            {'title': 'Interactive Visualizations', 'duration': timedelta(minutes=90), 'order': 3, 'content': fake.text(max_nb_chars=2000)}
                        ]
                    }
                ]
            },
            {
                'title': 'UI/UX Design Fundamentals',
                'description': 'Learn design principles, user research, wireframing, and prototyping to create beautiful and functional user interfaces.',
                'price': 149.99,
                'level': 'beginner',
                'duration': timedelta(hours=35),
                'category': 'Design',
                'modules': [
                    {
                        'title': 'Design Principles',
                        'description': 'Learn fundamental design principles',
                        'order': 1,
                        'lessons': [
                            {'title': 'Color Theory', 'duration': timedelta(minutes=45), 'order': 1, 'content': fake.text(max_nb_chars=2000)},
                            {'title': 'Typography Basics', 'duration': timedelta(minutes=60), 'order': 2, 'content': fake.text(max_nb_chars=2000)},
                            {'title': 'Layout and Composition', 'duration': timedelta(minutes=75), 'order': 3, 'content': fake.text(max_nb_chars=2000)}
                        ]
                    },
                    {
                        'title': 'User Research',
                        'description': 'Understand user needs and behaviors',
                        'order': 2,
                        'lessons': [
                            {'title': 'User Personas', 'duration': timedelta(minutes=60), 'order': 1, 'content': fake.text(max_nb_chars=2000)},
                            {'title': 'User Journey Mapping', 'duration': timedelta(minutes=75), 'order': 2, 'content': fake.text(max_nb_chars=2000)},
                            {'title': 'Usability Testing', 'duration': timedelta(minutes=90), 'order': 3, 'content': fake.text(max_nb_chars=2000)}
                        ]
                    },
                    {
                        'title': 'Wireframing and Prototyping',
                        'description': 'Create wireframes and interactive prototypes',
                        'order': 3,
                        'lessons': [
                            {'title': 'Low-Fidelity Wireframes', 'duration': timedelta(minutes=60), 'order': 1, 'content': fake.text(max_nb_chars=2000)},
                            {'title': 'High-Fidelity Mockups', 'duration': timedelta(minutes=75), 'order': 2, 'content': fake.text(max_nb_chars=2000)},
                            {'title': 'Interactive Prototypes', 'duration': timedelta(minutes=90), 'order': 3, 'content': fake.text(max_nb_chars=2000)}
                        ]
                    }
                ]
            }
        ]
        
        self.courses = []
        for course_info in course_data:
            # Create thumbnail
            thumbnail_content = b'fake image content'
            thumbnail_file = SimpleUploadedFile(
                f"{course_info['title'].lower().replace(' ', '_')}_thumbnail.jpg",
                thumbnail_content,
                content_type="image/jpeg"
            )
            
            # Get category
            category = Category.objects.get(name=course_info['category'])
            
            # Create course
            course = Course.objects.create(
                title=course_info['title'],
                description=course_info['description'],
                instructor=self.instructors[0],  # Use the first instructor
                category=category,
                price=course_info['price'],
                level=course_info['level'],
                duration=course_info['duration'],
                thumbnail=thumbnail_file,
                is_published=True
            )
            self.courses.append(course)
            self.stdout.write(f'   Created course: {course.title}')
            
            # Create modules and lessons
            for module_info in course_info['modules']:
                module = Module.objects.create(
                    course=course,
                    title=module_info['title'],
                    description=module_info['description'],
                    order=module_info['order']
                )
                
                for lesson_info in module_info['lessons']:
                    lesson = Lesson.objects.create(
                        module=module,
                        title=lesson_info['title'],
                        content=lesson_info['content'],
                        duration=lesson_info['duration'],
                        order=lesson_info['order'],
                        video_url=f"https://www.youtube.com/watch?v={fake.uuid4()}"
                    )
    
    def create_assignments_and_quizzes(self):
        """Create assignments and quizzes for each course"""
        self.stdout.write('📝 Creating assignments and quizzes...')
        
        for course in self.courses:
            # Create assignments
            assignment_data = [
                {
                    'title': f'{course.title} - Assignment 1',
                    'description': 'Complete the following tasks based on what you learned in the first module.',
                    'total_points': 100,
                    'due_date': timezone.now() + timedelta(days=7)
                },
                {
                    'title': f'{course.title} - Assignment 2',
                    'description': 'Apply your knowledge to create a practical project.',
                    'total_points': 150,
                    'due_date': timezone.now() + timedelta(days=14)
                },
                {
                    'title': f'{course.title} - Final Project',
                    'description': 'Comprehensive project that demonstrates all learned concepts.',
                    'total_points': 200,
                    'due_date': timezone.now() + timedelta(days=30)
                }
            ]
            
            for i, assignment_info in enumerate(assignment_data):
                module = course.modules.first()  # Assign to first module
                assignment = Assignment.objects.create(
                    title=assignment_info['title'],
                    description=assignment_info['description'],
                    course=course,
                    module=module,
                    due_date=assignment_info['due_date'],
                    total_points=assignment_info['total_points']
                )
                self.stdout.write(f'   Created assignment: {assignment.title}')
            
            # Create quizzes
            quiz_data = [
                {
                    'title': f'{course.title} - Module 1 Quiz',
                    'description': 'Test your knowledge of the first module.',
                    'time_limit': 30,
                    'passing_score': 70,
                    'available_from': timezone.now() - timedelta(days=1),
                    'available_until': timezone.now() + timedelta(days=30)
                },
                {
                    'title': f'{course.title} - Module 2 Quiz',
                    'description': 'Assessment for the second module content.',
                    'time_limit': 45,
                    'passing_score': 75,
                    'available_from': timezone.now() - timedelta(days=1),
                    'available_until': timezone.now() + timedelta(days=30)
                },
                {
                    'title': f'{course.title} - Final Exam',
                    'description': 'Comprehensive final examination.',
                    'time_limit': 60,
                    'passing_score': 80,
                    'available_from': timezone.now() - timedelta(days=1),
                    'available_until': timezone.now() + timedelta(days=30)
                }
            ]
            
            for quiz_info in quiz_data:
                quiz = Quiz.objects.create(
                    title=quiz_info['title'],
                    description=quiz_info['description'],
                    course=course,
                    module=course.modules.first(),
                    time_limit=quiz_info['time_limit'],
                    passing_score=quiz_info['passing_score'],
                    available_from=quiz_info['available_from'],
                    available_until=quiz_info['available_until'],
                    is_published=True
                )
                self.stdout.write(f'   Created quiz: {quiz.title}')
                
                # Create questions for each quiz
                question_types = ['multiple_choice', 'true_false', 'short_answer', 'essay']
                for i in range(5):  # 5 questions per quiz
                    question_type = random.choice(question_types)
                    question = Question.objects.create(
                        question_type='quiz',
                        quiz=quiz,
                        question_text=fake.sentence(nb_words=10) + '?',
                        question_format=question_type,
                        points=20,
                        order=i + 1
                    )
                    
                    # Create choices for multiple choice questions
                    if question_type == 'multiple_choice':
                        for j in range(4):
                            Choice.objects.create(
                                question=question,
                                choice_text=fake.sentence(nb_words=5),
                                is_correct=(j == 0),  # First choice is correct
                                order=j + 1
                            )
    
    def create_enrollments(self):
        """Create enrollments for students in courses"""
        self.stdout.write('🎓 Creating enrollments...')
        
        for student in self.students:
            for course in self.courses:
                enrollment = Enrollment.objects.create(
                    student=student,
                    course=course,
                    progress=random.randint(10, 90),
                    completed=random.choice([True, False])
                )
                if enrollment.completed:
                    enrollment.completed_at = timezone.now() - timedelta(days=random.randint(1, 30))
                    enrollment.save()
                self.stdout.write(f'   Enrolled {student.first_name} in {course.title}')
    
    def create_assignments_and_submissions(self):
        """Create assignment submissions"""
        self.stdout.write('📄 Creating assignment submissions...')
        
        for student in self.students:
            for course in self.courses:
                assignments = Assignment.objects.filter(course=course)
                for assignment in assignments:
                    # Randomly create submissions
                    if random.choice([True, False]):
                        submission_text = fake.paragraph(nb_sentences=5)
                        submitted_at = assignment.due_date - timedelta(hours=random.randint(1, 24))
                        
                        submission = AssignmentSubmission.objects.create(
                            assignment=assignment,
                            student=student,
                            submission_text=submission_text,
                            submitted_at=submitted_at
                        )
                        
                        # Randomly grade some submissions
                        if random.choice([True, False]):
                            grade = random.randint(60, 100)
                            submission.grade = grade
                            submission.feedback = fake.paragraph(nb_sentences=3)
                            submission.graded_at = timezone.now()
                            submission.graded_by = self.instructors[0]
                            submission.save()
                        
                        self.stdout.write(f'   Created submission for {student.first_name} - {assignment.title}')
    
    def create_quiz_submissions(self):
        """Create quiz submissions"""
        self.stdout.write('📊 Creating quiz submissions...')
        
        for student in self.students:
            for course in self.courses:
                quizzes = Quiz.objects.filter(course=course)
                for quiz in quizzes:
                    # Randomly create quiz submissions
                    if random.choice([True, False]):
                        submission = QuizSubmission.objects.create(
                            quiz=quiz,
                            student=student,
                            start_time=timezone.now() - timedelta(hours=random.randint(1, 24)),
                            end_time=timezone.now() - timedelta(hours=random.randint(1, 24)),
                            score=random.randint(60, 100),
                            is_completed=True,
                            time_spent=random.randint(300, 1800)  # 5-30 minutes
                        )
                        
                        # Create quiz answers
                        questions = Question.objects.filter(quiz=quiz)
                        for question in questions:
                            answer = QuizAnswer.objects.create(
                                submission=submission,
                                question=question,
                                answer_text=fake.sentence(nb_words=10),
                                is_correct=random.choice([True, False]),
                                points_earned=random.randint(0, question.points)
                            )
                            
                            # Add selected choices for multiple choice questions
                            if question.question_format == 'multiple_choice':
                                choices = Choice.objects.filter(question=question)
                                if choices.exists():
                                    answer.selected_choices.add(random.choice(choices))
                        
                        self.stdout.write(f'   Created quiz submission for {student.first_name} - {quiz.title}')
    
    def create_ratings(self):
        """Create course ratings"""
        self.stdout.write('⭐ Creating ratings...')
        
        for course in self.courses:
            for student in self.students:
                if random.choice([True, False]):  # 50% chance to rate
                    rating = Rating.objects.create(
                        course=course,
                        user=student,
                        rating=random.randint(3, 5),
                        comment=fake.paragraph(nb_sentences=2)
                    )
                    self.stdout.write(f'   Created rating: {student.first_name} rated {course.title}')
    
    def create_discussions_and_comments(self):
        """Create discussions and comments"""
        self.stdout.write('💬 Creating discussions...')
        
        discussion_topics = [
            'General Discussion',
            'Questions & Answers',
            'Project Showcase',
            'Study Group',
            'Tips & Tricks'
        ]
        
        for course in self.courses:
            for topic in discussion_topics:
                discussion = Discussion.objects.create(
                    title=f'{course.title} - {topic}',
                    content=fake.paragraph(nb_sentences=3),
                    course=course,
                    author=random.choice(self.students + self.instructors),
                    is_pinned=random.choice([True, False])
                )
                
                # Create comments
                for _ in range(random.randint(2, 5)):
                    comment = Comment.objects.create(
                        discussion=discussion,
                        author=random.choice(self.students + self.instructors),
                        content=fake.paragraph(nb_sentences=2)
                    )
                
                self.stdout.write(f'   Created discussion: {discussion.title}')
    
    def create_live_sessions(self):
        """Create live sessions"""
        self.stdout.write('🎥 Creating live sessions...')
        
        session_types = ['Lecture', 'Q&A Session', 'Workshop', 'Review Session', 'Office Hours']
        
        for course in self.courses:
            for i in range(3):  # 3 sessions per course
                session_type = random.choice(session_types)
                start_time = timezone.now() + timedelta(days=random.randint(1, 30))
                
                session = LiveSession.objects.create(
                    title=f'{course.title} - {session_type}',
                    description=fake.paragraph(nb_sentences=2),
                    course=course,
                    instructor=self.instructors[0],
                    session_type=session_type,
                    start_time=start_time,
                    end_time=start_time + timedelta(hours=1),
                    max_participants=random.randint(20, 100),
                    is_active=True
                )
                
                # Create participants
                for student in random.sample(self.students, min(3, len(self.students))):
                    SessionParticipant.objects.create(
                        session=session,
                        student=student,
                        joined_at=start_time - timedelta(minutes=random.randint(5, 15))
                    )
                
                # Create chat messages
                for _ in range(random.randint(5, 15)):
                    SessionChat.objects.create(
                        session=session,
                        sender=random.choice(self.students + self.instructors),
                        message=fake.sentence(nb_words=10),
                        timestamp=start_time + timedelta(minutes=random.randint(0, 60))
                    )
                
                self.stdout.write(f'   Created live session: {session.title}')
    
    def create_payments(self):
        """Create payments and refunds"""
        self.stdout.write('💳 Creating payments...')
        
        payment_methods = ['credit_card', 'paypal', 'stripe']
        payment_statuses = ['completed', 'pending', 'failed']
        
        for student in self.students:
            for course in self.courses:
                if random.choice([True, False]):  # 50% chance to have payment
                    payment = Payment.objects.create(
                        student=student,
                        course=course,
                        amount=course.price,
                        payment_method=random.choice(payment_methods),
                        status=random.choice(payment_statuses),
                        transaction_id=fake.uuid4(),
                        payment_date=timezone.now() - timedelta(days=random.randint(1, 365))
                    )
                    
                    # Create refund for some payments
                    if payment.status == 'completed' and random.choice([True, False]):
                        refund = Refund.objects.create(
                            payment=payment,
                            amount=payment.amount * 0.8,  # 80% refund
                            reason=random.choice(['Student request', 'Technical issue', 'Course cancellation']),
                            status='completed',
                            refund_date=payment.payment_date + timedelta(days=random.randint(1, 30))
                        )
                        self.stdout.write(f'   Created refund for {student.first_name} - {course.title}')
                    
                    self.stdout.write(f'   Created payment: {student.first_name} - {course.title}')
    
    def create_certificates(self):
        """Create certificates and templates"""
        self.stdout.write('🏆 Creating certificates...')
        
        # Create certificate templates
        template_data = [
            {
                'name': 'Standard Certificate',
                'description': 'Standard course completion certificate',
                'template_html': '<div class="certificate">...</div>'
            },
            {
                'name': 'Premium Certificate',
                'description': 'Premium certificate with gold border',
                'template_html': '<div class="certificate premium">...</div>'
            },
            {
                'name': 'Achievement Certificate',
                'description': 'Certificate for outstanding achievement',
                'template_html': '<div class="certificate achievement">...</div>'
            }
        ]
        
        self.templates = []
        for template_info in template_data:
            template = Certificate.objects.create(
                name=template_info['name'],
                description=template_info['description'],
                template_html=template_info['template_html']
            )
            self.templates.append(template)
            self.stdout.write(f'   Created template: {template.name}')
        
        # Create certificates for completed enrollments
        for enrollment in Enrollment.objects.filter(completed=True):
            certificate = Certificate.objects.create(
                student=enrollment.student,
                course=enrollment.course,
                template=random.choice(self.templates),
                issued_date=enrollment.completed_at,
                certificate_number=fake.uuid4(),
                is_valid=True
            )
            self.stdout.write(f'   Created certificate for {enrollment.student.first_name} - {enrollment.course.title}')
    
    def create_instructor_applications(self):
        """Create instructor applications"""
        self.stdout.write('📋 Creating instructor applications...')
        
        application_statuses = ['pending', 'approved', 'rejected']
        
        for student in self.students:
            if random.choice([True, False]):  # 50% chance to apply
                application = InstructorApplication.objects.create(
                    applicant=student,
                    bio=fake.paragraph(nb_sentences=3),
                    expertise=random.choice(['Web Development', 'Data Science', 'Design', 'Marketing']),
                    experience_years=random.randint(1, 10),
                    education=fake.sentence(nb_words=8),
                    portfolio_url=f"https://{fake.domain_name()}",
                    status=random.choice(application_statuses),
                    submitted_at=timezone.now() - timedelta(days=random.randint(1, 90))
                )
                
                if application.status != 'pending':
                    application.reviewed_at = application.submitted_at + timedelta(days=random.randint(1, 14))
                    application.reviewer_notes = fake.paragraph(nb_sentences=2)
                    application.save()
                
                self.stdout.write(f'   Created application: {student.first_name} - {application.expertise}')
    
    def print_summary(self):
        """Print a summary of created data"""
        self.stdout.write('\n📊 SEED DATA SUMMARY:')
        self.stdout.write('=' * 50)
        
        # Count objects by model
        models_to_count = [
            (User, 'Users'),
            (Category, 'Categories'),
            (Course, 'Courses'),
            (Module, 'Modules'),
            (Lesson, 'Lessons'),
            (Assignment, 'Assignments'),
            (AssignmentSubmission, 'Assignment Submissions'),
            (Quiz, 'Quizzes'),
            (Question, 'Questions'),
            (QuizSubmission, 'Quiz Submissions'),
            (Enrollment, 'Enrollments'),
            (Rating, 'Ratings'),
            (Discussion, 'Discussions'),
            (Comment, 'Comments'),
            (LiveSession, 'Live Sessions'),
            (Payment, 'Payments'),
            (Certificate, 'Certificates'),
            (InstructorApplication, 'Instructor Applications'),
        ]
        
        for model, name in models_to_count:
            count = model.objects.count()
            self.stdout.write(f'{name}: {count}')
        
        self.stdout.write('\n🔑 TEST ACCOUNTS:')
        self.stdout.write('=' * 30)
        self.stdout.write('Admin: admin@edulearn.com / admin123')
        self.stdout.write('Instructor: john.doe@edulearn.com / password123')
        self.stdout.write('Students:')
        for student in self.students:
            self.stdout.write(f'  {student.email} / password123')
        
        self.stdout.write('\n🚀 Ready to test the platform!')
        self.stdout.write('Visit: http://127.0.0.1:8000/')