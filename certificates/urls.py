from django.urls import path, include
from rest_framework.routers import DefaultRouter
from django.contrib.auth.decorators import login_required
from .views import CertificateViewSet, MyCertificatesView

router = DefaultRouter()
router.register('certificates', CertificateViewSet)

app_name = 'certificates'

urlpatterns = [
    path('', include(router.urls)),
    path('my-certificates/', login_required(MyCertificatesView.as_view()), name='my_certificates'),
]

