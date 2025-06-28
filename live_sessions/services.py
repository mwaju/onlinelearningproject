from django.db import transaction
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from .models import LiveSession, SessionParticipant, SessionChat

class LiveSessionService:
    @staticmethod
    def create_session(instructor, course, title, description, start_time, duration):
        """Create a new live session."""
        session = LiveSession.objects.create(
            instructor=instructor,
            course=course,
            title=title,
            description=description,
            start_time=start_time,
            duration=duration,
            status='scheduled'
        )
        return session

    @staticmethod
    def update_session(session, title=None, description=None, start_time=None, duration=None):
        """Update an existing live session."""
        if title:
            session.title = title
        if description:
            session.description = description
        if start_time:
            session.start_time = start_time
        if duration:
            session.duration = duration
        session.save()
        return session

    @staticmethod
    def start_session(session):
        """Start a live session."""
        if session.status == 'scheduled':
            session.status = 'live'
            session.actual_start_time = timezone.now()
            session.save()
            return session
        raise Exception("Session cannot be started")

    @staticmethod
    def end_session(session):
        """End a live session."""
        if session.status == 'live':
            session.status = 'completed'
            session.actual_end_time = timezone.now()
            session.save()
            return session
        raise Exception("Session cannot be ended")

    @staticmethod
    def cancel_session(session, reason):
        """Cancel a scheduled session."""
        if session.status == 'scheduled':
            session.status = 'cancelled'
            session.cancellation_reason = reason
            session.save()
            return session
        raise Exception("Session cannot be cancelled")

class SessionParticipantService:
    @staticmethod
    def join_session(user, session):
        """Add a participant to a live session."""
        if session.status == 'live':
            participant, created = SessionParticipant.objects.get_or_create(
                user=user,
                session=session,
                defaults={'joined_at': timezone.now()}
            )
            return participant
        raise Exception("Cannot join session")

    @staticmethod
    def leave_session(participant):
        """Remove a participant from a live session."""
        if participant.session.status == 'live':
            participant.left_at = timezone.now()
            participant.save()
            return participant
        raise Exception("Cannot leave session")

    @staticmethod
    def get_session_participants(session):
        """Get all participants for a session."""
        return SessionParticipant.objects.filter(session=session).select_related('user')

class SessionChatService:
    @staticmethod
    def send_message(user, session, message):
        """Send a message in the session chat."""
        if session.status == 'live':
            chat_message = SessionChat.objects.create(
                user=user,
                session=session,
                message=message
            )
            return chat_message
        raise Exception("Cannot send message in this session")

    @staticmethod
    def get_session_messages(session):
        """Get all messages for a session."""
        return SessionChat.objects.filter(session=session).select_related('user')

class LiveSessionAnalyticsService:
    @staticmethod
    def get_instructor_sessions(instructor):
        """Get all sessions for an instructor."""
        return LiveSession.objects.filter(instructor=instructor).annotate(
            participant_count=Count('participants')
        ).order_by('-start_time')

    @staticmethod
    def get_course_sessions(course):
        """Get all sessions for a course."""
        return LiveSession.objects.filter(course=course).annotate(
            participant_count=Count('participants')
        ).order_by('-start_time')

    @staticmethod
    def get_user_sessions(user):
        """Get all sessions a user has participated in."""
        return LiveSession.objects.filter(
            participants__user=user
        ).annotate(
            participant_count=Count('participants')
        ).order_by('-start_time')

    @staticmethod
    def get_session_stats(session):
        """Get statistics for a specific session."""
        return {
            'total_participants': session.participants.count(),
            'active_participants': session.participants.filter(left_at__isnull=True).count(),
            'total_messages': session.chat_messages.count(),
            'duration': (session.actual_end_time - session.actual_start_time) if session.actual_end_time else None
        }

    @staticmethod
    def get_upcoming_sessions(course=None):
        """Get all upcoming sessions."""
        query = Q(status='scheduled', start_time__gt=timezone.now())
        if course:
            query &= Q(course=course)
        
        return LiveSession.objects.filter(query).annotate(
            participant_count=Count('participants')
        ).order_by('start_time') 