from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'discussions'

router = DefaultRouter()
router.register(r'', views.DiscussionViewSet)

# API URLs
api_urlpatterns = [
    path('api/discussions/', include(router.urls)),
    path('api/discussions/comments/', views.CommentViewSet.as_view({
        'get': 'list',
        'post': 'create'
    }), name='api_comments'),
    path('api/comments/<int:pk>/', views.CommentViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'patch': 'partial_update',
        'delete': 'destroy'
    }), name='api_comment_detail'),
] 

# Frontend URLs
frontend_urlpatterns = [
    path('discussions/', views.DiscussionListView.as_view(), name='discussion_list'),
    path('discussions/<int:pk>/', views.DiscussionDetailView.as_view(), name='discussion_detail'),
]

urlpatterns = api_urlpatterns + frontend_urlpatterns 