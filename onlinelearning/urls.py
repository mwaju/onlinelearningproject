"""
URL configuration for onlinelearning project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

# Import the instructor_urls from the courses app
from courses import instructor_urls

# Main URL configuration
urlpatterns = [
    # Core and authentication URLs
    path('', include(('core.urls', 'core'), namespace='core')),
    path('admin/', admin.site.urls),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('', include(('users.urls', 'users'), namespace='users')),
    
    # Instructor URLs - must come before course URLs to avoid slug conflicts
    path('instructor/', include((instructor_urls, 'instructor'))),
    
    # Other app URLs
    path('', include(('payments.urls', 'payments'), namespace='payments')),
    path('', include(('certificates.urls', 'certificates'), namespace='certificates')),
    path('', include(('discussions.urls', 'discussions'), namespace='discussions')),
    path('', include(('live_sessions.urls', 'live_sessions'), namespace='live_sessions')),
    
    # Course URLs - must come after instructor URLs
    path('', include(('courses.urls', 'courses'), namespace='courses')),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

admin.site.site_header = "Online Learning Platform Admin"
admin.site.site_title = "Online Learning Platform Admin"
admin.site.index_title = "Welcome to Online Learning Platform Admin"

