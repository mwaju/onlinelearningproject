import stripe
from django.conf import settings
from .models import Payment, Refund
from courses.models import Course
from courses.services import CourseService

stripe.api_key = settings.STRIPE_SECRET_KEY

class PaymentService:
    @staticmethod
    def create_payment(student, course, payment_method):
        """Create a new payment record."""
        payment = Payment.objects.create(
            student=student,
            course=course,
            amount=course.price,
            currency='USD',
            payment_method=payment_method,
            status='pending'
        )
        return payment

    @staticmethod
    def process_stripe_payment(payment):
        """Process payment through Stripe."""
        try:
            # Create or get Stripe customer
            if not payment.stripe_customer_id:
                customer = stripe.Customer.create(
                    email=payment.student.email,
                    metadata={'user_id': payment.student.id}
                )
                payment.stripe_customer_id = customer.id
                payment.save()

            # Create payment intent
            intent = stripe.PaymentIntent.create(
                amount=int(payment.amount * 100),  # Convert to cents
                currency=payment.currency.lower(),
                customer=payment.stripe_customer_id,
                payment_method=payment.stripe_payment_id,
                confirm=True,
                metadata={
                    'payment_id': payment.id,
                    'course_id': payment.course.id
                }
            )

            # Update payment record
            payment.stripe_payment_id = intent.id
            payment.status = 'completed'
            payment.save()

            return payment
        except stripe.error.StripeError as e:
            payment.status = 'failed'
            payment.metadata['error'] = str(e)
            payment.save()
            raise e

    @staticmethod
    def process_refund(payment, reason=None):
        """Process refund for a payment."""
        try:
            # Create refund record
            refund = Refund.objects.create(
                payment=payment,
                amount=payment.amount,
                currency=payment.currency,
                reason=reason or 'Refund requested',
                status='pending'
            )

            # Process refund through Stripe
            if payment.stripe_payment_id:
                stripe_refund = stripe.Refund.create(
                    payment_intent=payment.stripe_payment_id,
                    reason='requested_by_customer'
                )
                refund.stripe_refund_id = stripe_refund.id
                refund.status = 'completed'
                refund.save()

                # Update payment status
                payment.status = 'refunded'
                payment.save()

            return refund
        except stripe.error.StripeError as e:
            refund.status = 'failed'
            refund.metadata['error'] = str(e)
            refund.save()
            raise e

    @staticmethod
    def get_payment_history(student):
        """Get payment history for a student."""
        return Payment.objects.filter(student=student).order_by('-created_at')

    @staticmethod
    def get_refund_history(payment):
        """Get refund history for a payment."""
        return Refund.objects.filter(payment=payment).order_by('-created_at') 