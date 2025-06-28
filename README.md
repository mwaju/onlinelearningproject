# EduLearn - Online Learning Platform

A comprehensive Django-based online learning platform that enables instructors to create and manage courses, while providing students with a rich learning experience including assignments, quizzes, live sessions, discussions, and certificates.

## 🚀 Features

### Core Platform
- **User Management**: Student and instructor registration with role-based access
- **Course Management**: Create, edit, and publish courses with modules and lessons
- **Enrollment System**: Student enrollment with progress tracking
- **Rating & Reviews**: Course rating and review system
- **Payment Processing**: Integrated payment system with Stripe
- **Modern UI**: Responsive design with Bootstrap 5 and custom styling

### Learning Features
- **Assignment System**: Complete assignment workflow with submission and grading
- **Quiz System**: Interactive quizzes with multiple question types
- **Live Sessions**: Real-time video sessions with chat functionality
- **Discussion Forums**: Course-specific discussion boards
- **Certificate Generation**: Automated certificate creation upon completion
- **Progress Tracking**: Student progress monitoring across courses

### Instructor Tools
- **Dashboard**: Comprehensive instructor dashboard with analytics
- **Assignment Management**: Create, grade, and manage assignments
- **Quiz Creation**: Build quizzes with various question formats
- **Bulk Grading**: Efficient bulk grading tools for assignments and quizzes
- **Student Management**: View and manage enrolled students
- **Content Management**: Upload and organize course materials

### Student Experience
- **Learning Dashboard**: Personalized student dashboard
- **Assignment Submission**: Submit assignments with file uploads
- **Grade Tracking**: View grades and feedback across all courses
- **Discussion Participation**: Engage in course discussions
- **Live Session Participation**: Join live sessions and interact
- **Certificate Access**: Download completion certificates

## 🛠️ Quick Start Guide

### Prerequisites
- Python 3.12 or higher
- VS Code (recommended)
- Redis (for background tasks)
- Git

### Step-by-Step Setup

1. **Clone and Open Project**
   ```bash
   git clone <repository-url>
   cd onlinelearningproject
   ```

2. **Set Up Virtual Environment**
   ```bash
   # Create virtual environment
   python -m venv env

   # Activate virtual environment
   # Windows:
   env\Scripts\activate
   # Linux/Mac:
   source env/bin/activate
   ```

3. **Install Dependencies**
   ```bash
   # Upgrade pip
   python -m pip install --upgrade pip

   # Install requirements
   pip install -r requirements.txt
   ```

4. **Configure Environment**
   Create `.env` file in project root:
   ```env
   DEBUG=True
   SECRET_KEY=your-secret-key-here
   EMAIL_HOST_USER=your-email@gmail.com
   EMAIL_HOST_PASSWORD=your-email-password
   STRIPE_PUBLIC_KEY=your-stripe-public-key
   STRIPE_SECRET_KEY=your-stripe-secret-key
   STRIPE_WEBHOOK_SECRET=your-stripe-webhook-secret
   ```

5. **Install Redis**
   - **Windows**: Download from https://github.com/microsoftarchive/redis/releases
   - **Linux**: `sudo apt-get install redis-server`
   - **Mac**: `brew install redis`

6. **Start Redis Server**
   ```bash
   # Windows
   redis-server

   # Linux/Mac
   sudo service redis-server start
   ```

7. **Set Up Database**
   ```bash
   # Create database tables
   python manage.py makemigrations
   python manage.py migrate

   # Create admin user
   python manage.py createsuperuser
   ```

8. **Start Services**
   Open three separate terminals:
   
   **Terminal 1 (Redis):**
   ```bash
   redis-server
   ```

   **Terminal 2 (Celery):**
   ```bash
   # Windows
   celery -A onlinelearning worker -l info -P eventlet
   
   # Linux/Mac
   celery -A onlinelearning worker -l info
   ```

   **Terminal 3 (Django):**
   ```bash
   python manage.py runserver
   ```

9. **Seed Demo Data**
   ```bash
   # Populate database with comprehensive demo data
   python manage.py seed_data
   ```

10. **Access the Application**
    - Main site: http://127.0.0.1:8000/
    - Admin interface: http://127.0.0.1:8000/admin/

## 👥 Demo Accounts

After seeding the database, you can log in with these accounts:

### Admin Account
- **Email**: admin@edulearn.com
- **Password**: admin123

### Instructor Account
- **Email**: john.doe@edulearn.com
- **Password**: password123

### Student Accounts
- **Alice Smith**: alice.smith@edulearn.com / password123
- **Bob Johnson**: bob.johnson@edulearn.com / password123
- **Carol Wilson**: carol.wilson@edulearn.com / password123

## 📊 Demo Data Overview

The comprehensive seed script creates:

### Users
- 1 Admin user
- 1 Instructor with full profile
- 3 Students with complete profiles

### Courses & Content
- 3 fully loaded courses with modules and lessons
- Complete Web Development Bootcamp (40 hours)
- Data Science Masterclass (50 hours)
- UI/UX Design Fundamentals (35 hours)

### Assessments
- 3 assignments per course (9 total)
- 3 quizzes per course (9 total)
- Multiple question types (multiple choice, true/false, short answer, essay)
- Sample submissions and grades

### Learning Features
- Course enrollments with progress tracking
- Live sessions with participants and chat
- Discussion forums with comments
- Course ratings and reviews
- Payment records and refunds
- Completion certificates

## 🏗️ Project Structure

```
onlinelearningproject/
├── core/                     # Core functionality and landing pages
├── users/                    # User management and authentication
├── courses/                  # Course management and learning features
├── payments/                 # Payment processing with Stripe
├── discussions/              # Discussion forums
├── live_sessions/            # Live video sessions
├── certificates/             # Certificate generation
├── templates/                # HTML templates
├── static/                   # CSS, JS, and static assets
├── media/                    # User uploads
├── onlinelearning/           # Django project settings
├── manage.py                 # Django management
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

## 🔧 Assignment Workflow

### Overview
The assignment workflow provides a complete system for creating, submitting, and grading assignments with automatic late submission handling.

### Key Features

#### Instructor Features
- **Assignment Creation**: Create assignments with title, description, due date, and point value
- **Assignment Management**: View and manage all assignments across courses
- **Grading System**: Grade individual submissions with points and feedback
- **Bulk Grading**: Efficiently grade multiple submissions at once
- **Automatic Late Handling**: Late submissions are automatically graded as F (0 points)
- **Submission Downloads**: Download all submissions for an assignment

#### Student Features
- **Assignment Viewing**: View all assignments across enrolled courses
- **Assignment Submission**: Submit text-based assignments and upload files
- **Grade Viewing**: View grades and detailed feedback from instructors
- **Submission Management**: Update or delete submissions before deadline

### Workflow Process

1. **Assignment Creation** (Instructor)
   - Navigate to instructor dashboard
   - Create assignment with details
   - Set due date and point value

2. **Assignment Submission** (Student)
   - View assignments in dashboard
   - Submit text and/or files
   - System checks for late submission

3. **Assignment Grading** (Instructor)
   - View submission list
   - Grade individual submissions
   - Provide feedback and points
   - Navigate between submissions

4. **Grade Review** (Student)
   - View grades dashboard
   - See detailed feedback
   - Track performance

### Technical Implementation

#### Models
- `Assignment`: Assignment details and metadata
- `AssignmentSubmission`: Student submissions with grading data

#### Views
- **Instructor**: Dashboard, assignment management, grading interface
- **Student**: Assignment viewing, submission, grade tracking

#### Security
- Permission checks for instructors
- Enrollment verification for students
- Submission ownership protection

## 🎨 UI/UX Features

### Modern Design
- **Glassmorphism Effects**: Modern backdrop blur and transparency
- **Gradient Branding**: Professional gradient color scheme
- **Responsive Design**: Mobile-first responsive layout
- **Smooth Animations**: CSS transitions and JavaScript animations
- **Modern Typography**: Inter font family for readability

### Navigation
- **Sticky Navigation**: Modern navbar with scroll effects
- **User Menu**: Enhanced dropdown with notifications
- **Breadcrumbs**: Clear navigation hierarchy
- **Search Functionality**: Course and content search

### Interactive Elements
- **Hover Effects**: Smooth hover animations
- **Loading States**: Loading indicators and skeleton screens
- **Form Validation**: Real-time form validation
- **Toast Notifications**: User feedback messages

## 🔌 API Endpoints

### Authentication
- `POST /api/users/register/` - User registration
- `POST /api/users/login/` - User login
- `POST /api/users/token/refresh/` - Token refresh
- `POST /api/users/logout/` - User logout

### Courses
- `GET /api/courses/` - List all courses
- `POST /api/courses/` - Create new course
- `GET /api/courses/{id}/` - Course details
- `PUT /api/courses/{id}/` - Update course
- `DELETE /api/courses/{id}/` - Delete course

### Assignments
- `GET /api/assignments/` - List assignments
- `POST /api/assignments/` - Create assignment
- `GET /api/assignments/{id}/` - Assignment details
- `POST /api/assignment-submissions/` - Submit assignment
- `POST /api/assignment-submissions/{id}/grade/` - Grade submission

### Quizzes
- `GET /api/quizzes/` - List quizzes
- `POST /api/quizzes/` - Create quiz
- `GET /api/quizzes/{id}/` - Quiz details
- `POST /api/quiz-submissions/` - Submit quiz
- `POST /api/quiz-answers/{id}/grade/` - Grade quiz answer

## 🛡️ Security Features

### Authentication & Authorization
- JWT token-based authentication
- Role-based access control (RBAC)
- Session management
- Password validation and hashing

### Data Protection
- CSRF protection
- SQL injection prevention
- XSS protection
- File upload validation

### Privacy
- User data encryption
- GDPR compliance features
- Privacy policy integration
- Data retention policies

## 🚀 Deployment

### Production Setup
1. **Environment Configuration**
   ```bash
   DEBUG=False
   ALLOWED_HOSTS=your-domain.com
   SECRET_KEY=your-production-secret-key
   ```

2. **Database Setup**
   ```bash
   # Use PostgreSQL for production
   DATABASES = {
       'default': {
           'ENGINE': 'django.db.backends.postgresql',
           'NAME': 'your_db_name',
           'USER': 'your_db_user',
           'PASSWORD': 'your_db_password',
           'HOST': 'localhost',
           'PORT': '5432',
       }
   }
   ```

3. **Static Files**
   ```bash
   python manage.py collectstatic
   ```

4. **Web Server**
   - Use Gunicorn or uWSGI
   - Configure Nginx as reverse proxy
   - Set up SSL certificates

### Docker Deployment
```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["gunicorn", "onlinelearning.wsgi:application"]
```

## 🧪 Testing

### Running Tests
```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test courses
python manage.py test users

# Run with coverage
coverage run --source='.' manage.py test
coverage report
```

### Test Data
```bash
# Create comprehensive test data
python manage.py seed_data

# Create specific test scenarios
python manage.py seed_data --clear
```

## 🔧 Common Issues & Solutions

### Redis Connection Issues
- Ensure Redis server is running
- Check Redis installation
- Restart Redis server

### Celery Worker Issues
- Verify Redis is running
- Check virtual environment activation
- For Windows, try:
  ```bash
  celery -A onlinelearning worker -l info --pool=solo
  ```

### Database Issues
- Delete `db.sqlite3` (if using SQLite)
- Remove migration files (except `__init__.py`)
- Run migrations again:
  ```bash
  python manage.py makemigrations
  python manage.py migrate
  ```

### Static Files Not Loading
```bash
python manage.py collectstatic
```

## 📚 Dependencies

### Core Dependencies
- Django 5.2+
- Django REST Framework
- Django Channels (for live sessions)
- Celery (for background tasks)
- Redis (for caching and message broker)

### Frontend Dependencies
- Bootstrap 5.3
- Font Awesome 6.0
- Inter Font Family
- Custom CSS with modern design

### Payment Dependencies
- Stripe Python SDK
- Django Payments

### Development Dependencies
- Faker (for test data)
- Coverage (for testing)
- Django Debug Toolbar

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new features
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Check the documentation
- Review common issues section

## 🔮 Future Enhancements

- **Mobile App**: Native mobile applications
- **AI Integration**: AI-powered content recommendations
- **Advanced Analytics**: Detailed learning analytics
- **Video Processing**: Built-in video editing tools
- **Social Features**: Student networking and collaboration
- **Gamification**: Points, badges, and leaderboards
- **Multi-language Support**: Internationalization
- **Advanced Assessment**: AI-powered grading assistance

---

**EduLearn** - Empowering education through technology 🎓