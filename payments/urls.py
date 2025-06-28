from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'payments'

router = DefaultRouter()
router.register(r'', views.PaymentViewSet)

# API URLs
api_urlpatterns = [
    path('api/payments/', include(router.urls)),
    path('api/payments/process/', views.ProcessPaymentView.as_view(), name='api_process_payment'),
    path('api/payments/refund/', views.RefundPaymentView.as_view(), name='api_refund'),
] 

# Frontend URLs
frontend_urlpatterns = [
    path('payments/process/', views.PaymentTemplateView.as_view(), name='process_payment'),
    path('payments/success/', views.PaymentSuccessView.as_view(), name='payment_success'),
    path('payments/cancel/', views.PaymentCancelView.as_view(), name='payment_cancel'),
]

urlpatterns = api_urlpatterns + frontend_urlpatterns

# Webhook endpoint
urlpatterns.append(path('webhook/', views.StripeWebhookView.as_view(), name='stripe_webhook')) 