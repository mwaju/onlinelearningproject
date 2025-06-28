from rest_framework import serializers
from .models import Payment, Refund
from courses.serializers import CourseSerializer
from users.serializers import UserSerializer

class PaymentSerializer(serializers.ModelSerializer):
    student = UserSerializer(read_only=True)
    course = CourseSerializer(read_only=True)

    class Meta:
        model = Payment
        fields = [
            'id', 'student', 'course', 'amount', 'currency',
            'status', 'payment_method', 'stripe_payment_id',
            'stripe_customer_id', 'created_at', 'updated_at',
            'metadata'
        ]
        read_only_fields = [
            'id', 'student', 'stripe_payment_id', 'stripe_customer_id',
            'created_at', 'updated_at', 'metadata'
        ]

class PaymentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ['course', 'payment_method']

class RefundSerializer(serializers.ModelSerializer):
    class Meta:
        model = Refund
        fields = [
            'id', 'payment', 'amount', 'currency', 'status',
            'reason', 'stripe_refund_id', 'created_at',
            'updated_at', 'metadata'
        ]
        read_only_fields = [
            'id', 'stripe_refund_id', 'created_at',
            'updated_at', 'metadata'
        ]

class RefundCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Refund
        fields = ['payment', 'reason'] 