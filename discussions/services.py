from django.db import transaction
from django.db.models import Count, Q
from django.utils import timezone
from .models import Discussion, Comment

class DiscussionService:
    @staticmethod
    def create_discussion(user, course, title, content):
        """Create a new discussion thread."""
        discussion = Discussion.objects.create(
            user=user,
            course=course,
            title=title,
            content=content,
            status='active'
        )
        return discussion

    @staticmethod
    def update_discussion(discussion, title=None, content=None):
        """Update an existing discussion thread."""
        if title:
            discussion.title = title
        if content:
            discussion.content = content
        discussion.updated_at = timezone.now()
        discussion.save()
        return discussion

    @staticmethod
    def close_discussion(discussion):
        """Close a discussion thread."""
        discussion.status = 'closed'
        discussion.closed_at = timezone.now()
        discussion.save()
        return discussion

    @staticmethod
    def get_discussion_with_comments(discussion_id):
        """Get a discussion with all its comments."""
        try:
            discussion = Discussion.objects.select_related(
                'user', 'course'
            ).prefetch_related(
                'comments__user'
            ).get(id=discussion_id)
            return discussion
        except Discussion.DoesNotExist:
            return None

class CommentService:
    @staticmethod
    def create_comment(user, discussion, content):
        """Create a new comment on a discussion."""
        comment = Comment.objects.create(
            user=user,
            discussion=discussion,
            content=content
        )
        return comment

    @staticmethod
    def update_comment(comment, content):
        """Update an existing comment."""
        comment.content = content
        comment.updated_at = timezone.now()
        comment.save()
        return comment

    @staticmethod
    def delete_comment(comment):
        """Delete a comment."""
        comment.delete()

class DiscussionAnalyticsService:
    @staticmethod
    def get_course_discussions(course):
        """Get all discussions for a course with basic stats."""
        return Discussion.objects.filter(course=course).annotate(
            comment_count=Count('comments'),
            active_participants=Count('comments__user', distinct=True)
        ).order_by('-created_at')

    @staticmethod
    def get_user_discussions(user):
        """Get all discussions created by a user."""
        return Discussion.objects.filter(user=user).annotate(
            comment_count=Count('comments')
        ).order_by('-created_at')

    @staticmethod
    def get_user_comments(user):
        """Get all comments made by a user."""
        return Comment.objects.filter(user=user).select_related(
            'discussion', 'discussion__course'
        ).order_by('-created_at')

    @staticmethod
    def get_discussion_stats(course):
        """Get discussion statistics for a course."""
        discussions = Discussion.objects.filter(course=course)
        return {
            'total_discussions': discussions.count(),
            'active_discussions': discussions.filter(status='active').count(),
            'closed_discussions': discussions.filter(status='closed').count(),
            'total_comments': Comment.objects.filter(discussion__course=course).count(),
            'active_participants': Comment.objects.filter(
                discussion__course=course
            ).values('user').distinct().count()
        }

    @staticmethod
    def search_discussions(query, course=None):
        """Search discussions by title or content."""
        search_query = Q(title__icontains=query) | Q(content__icontains=query)
        if course:
            search_query &= Q(course=course)
        
        return Discussion.objects.filter(search_query).annotate(
            comment_count=Count('comments')
        ).order_by('-created_at') 