# Online Learning Platform

A Django-based online learning platform that allows instructors to create courses and students to enroll and learn.

## Quick Start Guide

### Prerequisites
- Python 3.12 or higher
- VS Code (recommended)
- Redis (for background tasks)

### Step-by-Step Setup

1. **Extract and Open Project**
   - Extract the zip file
   - Open VS Code
   - Open the extracted folder in VS Code

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
   - Create `.env` file in project root
   - Add the following (replace with your values):
   ```
   DEBUG=True
   SECRET_KEY=your-secret-key-here
   EMAIL_HOST_USER=your-email@gmail.com
   EMAIL_HOST_PASSWORD=your-email-password
   STRIPE_PUBLIC_KEY=your-stripe-public-key
   STRIPE_SECRET_KEY=your-stripe-secret-key
   STRIPE_WEBHOOK_SECRET=your-stripe-webhook-secret
   ```

5. **Install Redis**
   - Windows: Download from https://github.com/microsoftarchive/redis/releases
   - Linux: `sudo apt-get install redis-server`
   - Mac: `brew install redis`

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
   - Open three separate terminals in VS Code
   
   Terminal 1 (Redis):
   ```bash
   redis-server
   ```

   Terminal 2 (Celery):
   ```bash
   # Windows
   celery -A onlinelearning worker -l info -P eventlet
   
   # Linux/Mac
   celery -A onlinelearning worker -l info
   ```

   Terminal 3 (Django):
   ```bash
   python manage.py runserver
   ```

9. **Seed Demo Data**
   ```bash
   # Populate database with demo users, courses, and content
   python manage.py seed_data
   ```

10. **Access the Application**
    - Main site: http://127.0.0.1:8000/
    - Admin interface: http://127.0.0.1:8000/admin/
    
### Testing Accounts

After seeding the database, you can log in with these demo accounts:

**Admin Account:**
- Email: admin@example.com
- Password: admin123

**Instructor Accounts:**
- Email: john.doe@example.com
- Password: password123

- Email: jane.smith@example.com
- Password: password123

**Student Accounts:**
- Multiple student accounts are created with email patterns like: firstname.lastname1@example.com, firstname2.lastname2@example.com, etc.
- All student passwords: password123

### Demo Data

The seed script creates:
- 3 demo courses with modules and lessons
- 3 instructor accounts
- 10 student accounts
- Course enrollments
- Ratings and reviews
- Discussion forums
- Live sessions
- Sample payments and refunds
   - Admin panel: http://127.0.0.1:8000/admin/

## Project Structure
```
onlinelearning/
├── core/                 # Core functionality
├── courses/             # Course management
├── users/               # User management
├── payments/            # Payment processing
├── certificates/        # Certificate generation
├── discussions/         # Discussion forums
├── live_sessions/       # Live sessions
├── templates/           # HTML templates
├── static/             # Static files
├── media/              # User uploads
└── manage.py           # Django management
```

## Common Issues & Solutions

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

## VS Code Extensions
- Python (Microsoft)
- Django
- SQLite
- GitLens
- Python Docstring Generator
- Python Test Explorer

## API Endpoints

### Authentication
- POST `/api/users/register/` - Register
- POST `/api/users/login/` - Login
- POST `/api/users/token/refresh/` - Refresh token
- POST `/api/users/logout/` - Logout

### Courses
- GET `/api/courses/` - List courses
- POST `/api/courses/` - Create course
- GET `/api/courses/<id>/` - Course details
- PUT `/api/courses/<id>/` - Update course
- DELETE `/api/courses/<id>/` - Delete course

### Enrollments
- POST `/api/courses/<id>/enroll/` - Enroll
- GET `/api/enrollments/` - List enrollments

## Development

### Running Tests
```bash
python manage.py test
```

### Code Style
The project follows PEP 8 style guide. To check code style:
```bash
flake8
```

### Database Backup
```bash
python manage.py dumpdata > backup.json
```

### Database Restore
```bash
python manage.py loaddata backup.json
```



