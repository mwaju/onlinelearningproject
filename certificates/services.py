import uuid
from datetime import datetime
from django.conf import settings
from django.db import transaction
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph, Spacer
from reportlab.lib.units import inch
import qrcode
from io import BytesIO
from .models import Certificate

class CertificateService:
    @staticmethod
    def generate_certificate_number():
        """Generate a unique certificate number."""
        return f"CERT-{uuid.uuid4().hex[:8].upper()}"

    @staticmethod
    def create_certificate(user, course):
        """Create a new certificate for a completed course."""
        certificate = Certificate.objects.create(
            user=user,
            course=course,
            certificate_number=CertificateService.generate_certificate_number(),
            issue_date=datetime.now(),
            status='active'
        )
        return certificate

    @staticmethod
    def generate_pdf(certificate):
        """Generate PDF certificate with QR code."""
        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter

        # Add certificate header
        p.setFont("Helvetica-Bold", 24)
        p.drawCentredString(width/2, height - 2*inch, "Certificate of Completion")

        # Add course information
        p.setFont("Helvetica", 16)
        p.drawCentredString(width/2, height - 3*inch, f"Course: {certificate.course.title}")

        # Add student information
        p.setFont("Helvetica", 14)
        p.drawCentredString(width/2, height - 4*inch, 
            f"This is to certify that {certificate.user.get_full_name()}")
        p.drawCentredString(width/2, height - 4.5*inch, 
            "has successfully completed the course")

        # Add certificate number and date
        p.setFont("Helvetica", 12)
        p.drawCentredString(width/2, height - 6*inch, 
            f"Certificate Number: {certificate.certificate_number}")
        p.drawCentredString(width/2, height - 6.5*inch, 
            f"Issue Date: {certificate.issue_date.strftime('%B %d, %Y')}")

        # Generate and add QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        verification_url = f"{settings.SITE_URL}/verify/{certificate.certificate_number}"
        qr.add_data(verification_url)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white")
        
        # Save QR code to buffer
        qr_buffer = BytesIO()
        qr_img.save(qr_buffer)
        qr_buffer.seek(0)
        
        # Add QR code to PDF
        p.drawImage(qr_buffer, width/2 - 1*inch, height - 8*inch, 
            width=2*inch, height=2*inch)

        # Add verification text
        p.setFont("Helvetica", 10)
        p.drawCentredString(width/2, height - 9*inch, 
            "Scan QR code to verify this certificate")

        p.save()
        buffer.seek(0)
        return buffer

    @staticmethod
    def verify_certificate(certificate_number):
        """Verify a certificate's authenticity."""
        try:
            certificate = Certificate.objects.get(
                certificate_number=certificate_number,
                status='active'
            )
            return {
                'valid': True,
                'certificate': certificate,
                'message': 'Certificate is valid'
            }
        except Certificate.DoesNotExist:
            return {
                'valid': False,
                'message': 'Invalid or revoked certificate'
            }

class CertificateAnalyticsService:
    @staticmethod
    def get_user_certificates(user):
        """Get all certificates for a user."""
        return Certificate.objects.filter(user=user, status='active')

    @staticmethod
    def get_course_certificates(course):
        """Get all certificates issued for a course."""
        return Certificate.objects.filter(course=course, status='active')

    @staticmethod
    def get_certificate_stats():
        """Get overall certificate statistics."""
        total_certificates = Certificate.objects.count()
        active_certificates = Certificate.objects.filter(status='active').count()
        revoked_certificates = Certificate.objects.filter(status='revoked').count()
        
        return {
            'total_certificates': total_certificates,
            'active_certificates': active_certificates,
            'revoked_certificates': revoked_certificates
        } 