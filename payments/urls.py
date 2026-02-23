from django.urls import path

from academics.views import stripe_webhook
from .views import CreateCheckoutSessionView, CreateInstallmentSessionView, ProcessInstallmentView

urlpatterns = [
    path('create-checkout-session/<uuid:course_id>/', CreateCheckoutSessionView.as_view(), name='create-checkout-session'),
    path('create-installment-session/<uuid:course_id>/', CreateInstallmentSessionView.as_view(), name='create-installment-session'),
    path('process-installment/<uuid:transaction_id>/', ProcessInstallmentView.as_view(), name='process-installment'),
    path('webhook/', stripe_webhook, name='stripe-webhook'),
]