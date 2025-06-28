from rest_framework import serializers
from .models import Discussion, Comment
from courses.serializers import CourseSerializer
from users.serializers import UserSerializer

class CommentSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = '__all__'
        read_only_fields = ('author', 'created_at', 'updated_at')

class CommentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ('content',)

class DiscussionSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    course = CourseSerializer(read_only=True)
    comments = CommentSerializer(many=True, read_only=True)
    comments_count = serializers.SerializerMethodField()

    class Meta:
        model = Discussion
        fields = '__all__'
        read_only_fields = ('author', 'created_at', 'updated_at')

    def get_comments_count(self, obj):
        return obj.comments.count()

class DiscussionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Discussion
        fields = ('title', 'content', 'course', 'lesson') 