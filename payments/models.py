from django.conf import settings
from django.db import models
from academics.models import Course
from django_rest_api.settings import AUTH_USER_MODEL

# Create your models here.
class Transaction(models.Model):
    STATUS_CHOICES = [
    ('pending', 'Pending'),
    ('partially_paid', 'Partially Paid'),
    ('completed', 'Completed'),
    ('refunded', 'Refunded'),
    ('failed', 'Failed'),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    stripe_checkout_id = models.CharField(max_length=255, unique=True)
    stripe_payment_intent_id = models.CharField(max_length=255, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # For Refunds
    refund_id = models.CharField(max_length=255, null=True, blank=True)
    
    # For Installments (Part Payments)
    is_installment = models.BooleanField(default=False)
    total_installments = models.IntegerField(default=1)
    installments_paid = models.IntegerField(default=1)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} - {self.course.title} - {self.status}"
