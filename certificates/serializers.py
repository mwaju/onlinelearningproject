from rest_framework import serializers
from .models import Certificate
from courses.serializers import CourseSerializer
from users.serializers import UserSerializer

class CertificateSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    course = CourseSerializer(read_only=True)

    class Meta:
        model = Certificate
        fields = '__all__'
        read_only_fields = ('certificate_number', 'issue_date', 'verification_code',
                          'created_at', 'updated_at')

class CertificateCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Certificate
        fields = ('course',)

class CertificateVerificationSerializer(serializers.Serializer):
    verification_code = serializers.CharField(max_length=100) 