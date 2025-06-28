from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'live_sessions'

router = DefaultRouter()
router.register('sessions', views.LiveSessionViewSet)
router.register('participants', views.SessionParticipantViewSet)
router.register('chat', views.SessionChatViewSet)
router.register('analytics', views.LiveSessionAnalyticsViewSet, basename='analytics')

# API URLs
api_urlpatterns = [
    path('api/live_sessions/', include(router.urls)),
    path('api/live_sessions/join/<int:session_id>/', views.JoinSessionView.as_view(), name='api_join'),
    path('api/live_sessions/leave/<int:session_id>/', views.LeaveSessionView.as_view(), name='api_leave'),
] 

# Frontend URLs
frontend_urlpatterns = [
    path('live_sessions/', views.SessionListView.as_view(), name='session_list'),
    path('live_sessions/<int:pk>/', views.SessionDetailView.as_view(), name='session_detail'),
    path('live_sessions/join/<int:session_id>/', views.JoinSessionView.as_view(), name='join'),
    path('live_sessions/leave/<int:session_id>/', views.LeaveSessionView.as_view(), name='leave'),
]

urlpatterns = api_urlpatterns + frontend_urlpatterns 