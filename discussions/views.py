from django.shortcuts import render, get_object_or_404
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters import rest_framework as filters
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from courses.models import Course
from .models import Discussion, Comment
from .serializers import (
    DiscussionSerializer, DiscussionCreateSerializer,
    CommentSerializer, CommentCreateSerializer
)
from .services import (
    DiscussionService, CommentService,
    DiscussionAnalyticsService
)


class DiscussionViewSet(viewsets.ModelViewSet):
    queryset = Discussion.objects.all()
    serializer_class = DiscussionSerializer
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ['title', 'content']
    ordering_fields = ['created_at', 'updated_at']

    def get_serializer_class(self):
        if self.action == 'create':
            return DiscussionCreateSerializer
        return DiscussionSerializer

    def get_queryset(self):
        return Discussion.objects.filter(course__enrollments__student=self.request.user)

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=True, methods=['post'])
    def close(self, request, pk=None):
        discussion = self.get_object()
        if discussion.user != request.user and not request.user.is_staff:
            return Response(
                {'error': 'Not authorized'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        discussion = DiscussionService.close_discussion(discussion)
        return Response(DiscussionSerializer(discussion).data)

    @action(detail=True, methods=['get'])
    def with_comments(self, request, pk=None):
        discussion = DiscussionService.get_discussion_with_comments(pk)
        if not discussion:
            return Response(
                {'error': 'Discussion not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        return Response(DiscussionSerializer(discussion).data)

class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return CommentCreateSerializer
        return CommentSerializer

    def get_queryset(self):
        return Comment.objects.filter(discussion__course__enrollments__student=self.request.user)

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

class DiscussionAnalyticsViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=True, methods=['get'])
    def course_discussions(self, request, pk=None):
        course = Course.objects.get(id=pk)
        discussions = DiscussionAnalyticsService.get_course_discussions(course)
        serializer = DiscussionSerializer(discussions, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def user_discussions(self, request):
        discussions = DiscussionAnalyticsService.get_user_discussions(request.user)
        serializer = DiscussionSerializer(discussions, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def user_comments(self, request):
        comments = DiscussionAnalyticsService.get_user_comments(request.user)
        serializer = CommentSerializer(comments, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def discussion_stats(self, request, pk=None):
        course = Course.objects.get(id=pk)
        stats = DiscussionAnalyticsService.get_discussion_stats(course)
        return Response(stats)

    @action(detail=False, methods=['get'])
    def search(self, request):
        query = request.query_params.get('q', '')
        course_id = request.query_params.get('course')
        course = Course.objects.get(id=course_id) if course_id else None
        
        discussions = DiscussionAnalyticsService.search_discussions(query, course)
        serializer = DiscussionSerializer(discussions, many=True)
        return Response(serializer.data)

# Frontend Views
class DiscussionListView(LoginRequiredMixin, ListView):
    model = Discussion
    template_name = 'discussions/discussion_list.html'
    context_object_name = 'discussions'
    paginate_by = 10

    def get_queryset(self):
        return Discussion.objects.filter(
            course__enrollments__student=self.request.user
        ).order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user'] = self.request.user
        return context

class DiscussionDetailView(LoginRequiredMixin, DetailView):
    model = Discussion
    template_name = 'discussions/discussion_detail.html'
    context_object_name = 'discussion'

    def get_queryset(self):
        return Discussion.objects.filter(
            course__enrollments__student=self.request.user
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['comments'] = self.object.comments.all().order_by('created_at')
        context['user'] = self.request.user
        return context
