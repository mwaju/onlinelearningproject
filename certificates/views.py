from django.shortcuts import render
from django.views.generic import ListView
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from courses.models import Course
from .models import Certificate
from .serializers import (
    CertificateSerializer, CertificateCreateSerializer,
    CertificateVerificationSerializer
)
from .services import CertificateService, CertificateAnalyticsService

class CertificateViewSet(viewsets.ModelViewSet):
    queryset = Certificate.objects.all()
    serializer_class = CertificateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return CertificateCreateSerializer
        return CertificateSerializer

    def get_queryset(self):
        return Certificate.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        course_id = serializer.validated_data['course'].id
        course = get_object_or_404(Course, id=course_id)
        
        # Check if user has completed the course
        enrollment = course.enrollments.filter(
            student=request.user,
            completed=True
        ).first()
        
        if not enrollment:
            return Response(
                {'error': 'Course not completed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        certificate = CertificateService.create_certificate(request.user, course)
        return Response(
            CertificateSerializer(certificate).data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        certificate = self.get_object()
        if certificate.user != request.user:
            return Response(
                {'error': 'Not authorized'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        pdf_buffer = CertificateService.generate_pdf(certificate)
        response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="certificate_{certificate.certificate_number}.pdf"'
        return response

    @action(detail=False, methods=['post'])
    def verify(self, request):
        serializer = CertificateVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        result = CertificateService.verify_certificate(
            serializer.validated_data['certificate_number']
        )
        return Response(result)

class MyCertificatesView(LoginRequiredMixin, ListView):
    model = Certificate
    template_name = 'certificates/my_certificates.html'
    context_object_name = 'certificates'
    
    def get_queryset(self):
        return Certificate.objects.filter(user=self.request.user).select_related('course')

class CertificateAnalyticsViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def user_certificates(self, request):
        """Get all certificates for the current user"""
        certificates = Certificate.objects.filter(user=request.user)
        serializer = CertificateSerializer(certificates, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def course_certificates(self, request, pk=None):
        course = get_object_or_404(Course, id=pk)
        if course.instructor != request.user:
            return Response(
                {'error': 'Not authorized'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        certificates = CertificateAnalyticsService.get_course_certificates(course)
        serializer = CertificateSerializer(certificates, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        if not request.user.is_staff:
            return Response(
                {'error': 'Not authorized'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        stats = CertificateAnalyticsService.get_certificate_stats()
        return Response(stats)
