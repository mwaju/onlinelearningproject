from rest_framework import serializers
from .models import LiveSession, SessionParticipant, SessionChat
from courses.serializers import CourseSerializer
from users.serializers import UserSerializer

class SessionChatSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = SessionChat
        fields = '__all__'
        read_only_fields = ('user', 'timestamp')

class SessionChatCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = SessionChat
        fields = ('message',)

class SessionParticipantSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = SessionParticipant
        fields = '__all__'
        read_only_fields = ('joined_at', 'left_at')

class LiveSessionSerializer(serializers.ModelSerializer):
    instructor = UserSerializer(read_only=True)
    course = CourseSerializer(read_only=True)
    participants = SessionParticipantSerializer(many=True, read_only=True)
    participants_count = serializers.SerializerMethodField()

    class Meta:
        model = LiveSession
        fields = '__all__'
        read_only_fields = ('instructor', 'created_at', 'updated_at')

    def get_participants_count(self, obj):
        return obj.participants.count()

class LiveSessionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = LiveSession
        fields = ('title', 'description', 'course', 'start_time', 'end_time') 