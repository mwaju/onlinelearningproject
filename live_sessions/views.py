from django.shortcuts import render, get_object_or_404, redirect
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters import rest_framework as filters
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from courses.models import Course
from .models import LiveSession, SessionParticipant, SessionChat
from .serializers import (
    LiveSessionSerializer, LiveSessionCreateSerializer,
    SessionParticipantSerializer, SessionChatSerializer
)
from .services import (
    LiveSessionService, SessionParticipantService,
    SessionChatService, LiveSessionAnalyticsService
)

class LiveSessionFilter(filters.FilterSet):
    class Meta:
        model = LiveSession
        fields = {
            'course': ['exact'],
            'instructor': ['exact'],
            'status': ['exact'],
            'start_time': ['gte', 'lte'],
        }

class LiveSessionViewSet(viewsets.ModelViewSet):
    queryset = LiveSession.objects.all()
    serializer_class = LiveSessionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_class = LiveSessionFilter
    search_fields = ['title', 'description']
    ordering_fields = ['start_time', 'created_at']

    def get_serializer_class(self):
        if self.action == 'create':
            return LiveSessionCreateSerializer
        return LiveSessionSerializer

    def get_queryset(self):
        return LiveSession.objects.select_related('instructor', 'course')

    def perform_create(self, serializer):
        session = LiveSessionService.create_session(
            instructor=self.request.user,
            **serializer.validated_data
        )
        return session

    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        session = self.get_object()
        if session.instructor != request.user:
            return Response(
                {'error': 'Not authorized'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            session = LiveSessionService.start_session(session)
            return Response(LiveSessionSerializer(session).data)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    def end(self, request, pk=None):
        session = self.get_object()
        if session.instructor != request.user:
            return Response(
                {'error': 'Not authorized'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            session = LiveSessionService.end_session(session)
            return Response(LiveSessionSerializer(session).data)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        session = self.get_object()
        if session.instructor != request.user:
            return Response(
                {'error': 'Not authorized'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        reason = request.data.get('reason', '')
        try:
            session = LiveSessionService.cancel_session(session, reason)
            return Response(LiveSessionSerializer(session).data)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

class SessionParticipantViewSet(viewsets.ModelViewSet):
    queryset = SessionParticipant.objects.all()
    serializer_class = SessionParticipantSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return SessionParticipant.objects.select_related('user', 'session')

    @action(detail=False, methods=['post'])
    def join(self, request):
        session_id = request.data.get('session')
        session = LiveSession.objects.get(id=session_id)
        
        try:
            participant = SessionParticipantService.join_session(request.user, session)
            return Response(
                SessionParticipantSerializer(participant).data,
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    def leave(self, request, pk=None):
        participant = self.get_object()
        if participant.user != request.user:
            return Response(
                {'error': 'Not authorized'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            participant = SessionParticipantService.leave_session(participant)
            return Response(SessionParticipantSerializer(participant).data)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

class SessionChatViewSet(viewsets.ModelViewSet):
    queryset = SessionChat.objects.all()
    serializer_class = SessionChatSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return SessionChat.objects.select_related('user', 'session')

    def perform_create(self, serializer):
        chat_message = SessionChatService.send_message(
            user=self.request.user,
            **serializer.validated_data
        )
        return chat_message

class LiveSessionAnalyticsViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['get'])
    def instructor_sessions(self, request):
        if not request.user.is_instructor:
            return Response(
                {'error': 'Not authorized'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        sessions = LiveSessionAnalyticsService.get_instructor_sessions(request.user)
        serializer = LiveSessionSerializer(sessions, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def course_sessions(self, request, pk=None):
        course = Course.objects.get(id=pk)
        sessions = LiveSessionAnalyticsService.get_course_sessions(course)
        serializer = LiveSessionSerializer(sessions, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def user_sessions(self, request):
        sessions = LiveSessionAnalyticsService.get_user_sessions(request.user)
        serializer = LiveSessionSerializer(sessions, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def session_stats(self, request, pk=None):
        session = LiveSession.objects.get(id=pk)
        stats = LiveSessionAnalyticsService.get_session_stats(session)
        return Response(stats)

    @action(detail=False, methods=['get'])
    def upcoming_sessions(self, request):
        course_id = request.query_params.get('course')
        course = Course.objects.get(id=course_id) if course_id else None
        
        sessions = LiveSessionAnalyticsService.get_upcoming_sessions(course)
        serializer = LiveSessionSerializer(sessions, many=True)
        return Response(serializer.data)

# API Views
class JoinSessionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, session_id):
        session = get_object_or_404(LiveSession, id=session_id)
        try:
            participant = SessionParticipantService.join_session(request.user, session)
            return Response(
                SessionParticipantSerializer(participant).data,
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

class LeaveSessionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, session_id):
        session = get_object_or_404(LiveSession, id=session_id)
        participant = get_object_or_404(
            SessionParticipant,
            session=session,
            user=request.user
        )
        try:
            participant = SessionParticipantService.leave_session(participant)
            return Response(SessionParticipantSerializer(participant).data)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

# Frontend Views
class SessionListView(LoginRequiredMixin, ListView):
    model = LiveSession
    template_name = 'live_sessions/session_list.html'
    context_object_name = 'sessions'
    paginate_by = 10

    def get_queryset(self):
        return LiveSession.objects.filter(
            course__enrollments__student=self.request.user
        ).order_by('-start_time')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user'] = self.request.user
        return context

class SessionDetailView(LoginRequiredMixin, DetailView):
    model = LiveSession
    template_name = 'live_sessions/session_detail.html'
    context_object_name = 'session'

    def get_queryset(self):
        return LiveSession.objects.filter(
            course__enrollments__student=self.request.user
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['participants'] = self.object.participants.all()
        context['chat_messages'] = self.object.chat_messages.all().order_by('created_at')
        context['user'] = self.request.user
        return context
