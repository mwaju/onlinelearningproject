from django.contrib import admin
from .models import Payment, Refund

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'student', 'course', 'amount', 'currency', 'status', 'payment_method', 'created_at')
    list_filter = ('status', 'payment_method', 'created_at')
    search_fields = ('student__email', 'course__title', 'stripe_payment_id')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Basic Information', {
            'fields': ('student', 'course', 'amount', 'currency', 'status', 'payment_method')
        }),
        ('Stripe Information', {
            'fields': ('stripe_payment_id', 'stripe_customer_id')
        }),
        ('Metadata', {
            'fields': ('metadata',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )

@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):
    list_display = ('id', 'payment', 'amount', 'currency', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('payment__student__email', 'payment__course__title', 'stripe_refund_id')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Basic Information', {
            'fields': ('payment', 'amount', 'currency', 'status', 'reason')
        }),
        ('Stripe Information', {
            'fields': ('stripe_refund_id',)
        }),
        ('Metadata', {
            'fields': ('metadata',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
