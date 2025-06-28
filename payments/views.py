from django.shortcuts import render, redirect, get_object_or_404
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.views.generic import TemplateView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.http import Http404, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import stripe
import json

from .models import Payment
from courses.models import Course
from .serializers import PaymentSerializer, PaymentCreateSerializer
from .services import PaymentService

stripe.api_key = settings.STRIPE_SECRET_KEY

class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Payment.objects.filter(student=self.request.user)

    def get_serializer_class(self):
        if self.action == 'create':
            return PaymentCreateSerializer
        return PaymentSerializer

    def perform_create(self, serializer):
        course = serializer.validated_data['course']
        payment_method = serializer.validated_data['payment_method']
        
        payment = PaymentService.create_payment(
            student=self.request.user,
            course=course,
            payment_method=payment_method
        )
        
        if payment_method == 'card':
            try:
                payment = PaymentService.process_stripe_payment(payment)
                return Response(
                    PaymentSerializer(payment).data,
                    status=status.HTTP_201_CREATED
                )
            except stripe.error.CardError as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
        return Response(
            PaymentSerializer(payment).data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['post'])
    def refund(self, request, pk=None):
        payment = self.get_object()
        try:
            payment = PaymentService.process_refund(payment)
            return Response(
                PaymentSerializer(payment).data,
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

class PaymentTemplateView(LoginRequiredMixin, TemplateView):
    template_name = 'payments/payment.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['stripe_public_key'] = settings.STRIPE_PUBLIC_KEY
        course_id = self.request.GET.get('course_id')
        if course_id:
            try:
                course = Course.objects.get(id=course_id)
                context['course'] = course
            except Course.DoesNotExist:
                raise Http404("Course not found")
        return context

    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            course_id = data.get('course_id')
            payment_method_id = data.get('payment_method_id')

            if not course_id or not payment_method_id:
                return JsonResponse({'error': 'Missing required fields'}, status=400)

            course = get_object_or_404(Course, id=course_id)
            payment = PaymentService.create_payment(
                student=request.user,
                course=course,
                payment_method='card'
            )
            payment.stripe_payment_id = payment_method_id
            payment.save()

            payment = PaymentService.process_stripe_payment(payment)
            return JsonResponse(PaymentSerializer(payment).data)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

class PaymentSuccessView(LoginRequiredMixin, TemplateView):
    template_name = 'payments/payment_success.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course_id = self.request.GET.get('course_id')
        if course_id:
            try:
                course = Course.objects.get(id=course_id)
                context['course'] = course
            except Course.DoesNotExist:
                raise Http404("Course not found")
        return context

class PaymentCancelView(LoginRequiredMixin, TemplateView):
    template_name = 'payments/payment_cancel.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course_id = self.request.GET.get('course_id')
        if course_id:
            try:
                course = Course.objects.get(id=course_id)
                context['course'] = course
            except Course.DoesNotExist:
                raise Http404("Course not found")
        return context

class PaymentHistoryView(LoginRequiredMixin, ListView):
    model = Payment
    template_name = 'payments/payment_history.html'
    context_object_name = 'payments'
    paginate_by = 10

    def get_queryset(self):
        return Payment.objects.filter(student=self.request.user).order_by('-created_at')

@method_decorator(csrf_exempt, name='dispatch')
class StripeWebhookView(APIView):
    def post(self, request, *args, **kwargs):
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
        except ValueError as e:
            return Response({'error': 'Invalid payload'}, status=400)
        except stripe.error.SignatureVerificationError as e:
            return Response({'error': 'Invalid signature'}, status=400)

        if event['type'] == 'payment_intent.succeeded':
            payment_intent = event['data']['object']
            try:
                payment = Payment.objects.get(stripe_payment_id=payment_intent['id'])
                payment.status = 'completed'
                payment.save()
                # Enroll student in course
                CourseService.enroll_student(payment.course, payment.student)
            except Payment.DoesNotExist:
                pass

        return Response({'status': 'success'})

class ProcessPaymentView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = PaymentCreateSerializer(data=request.data)
        if serializer.is_valid():
            course = serializer.validated_data['course']
            payment_method = serializer.validated_data['payment_method']
            
            payment = PaymentService.create_payment(
                student=request.user,
                course=course,
                payment_method=payment_method
            )
            
            if payment_method == 'card':
                try:
                    payment = PaymentService.process_stripe_payment(payment)
                    return Response(
                        PaymentSerializer(payment).data,
                        status=status.HTTP_201_CREATED
                    )
                except stripe.error.CardError as e:
                    return Response(
                        {'error': str(e)},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            return Response(
                PaymentSerializer(payment).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class RefundPaymentView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        payment_id = request.data.get('payment_id')
        try:
            payment = Payment.objects.get(id=payment_id, student=request.user)
            payment = PaymentService.process_refund(payment)
            return Response(
                PaymentSerializer(payment).data,
                status=status.HTTP_200_OK
            )
        except Payment.DoesNotExist:
            return Response(
                {'error': 'Payment not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            ) 