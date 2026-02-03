from django.urls import path

from academics.views import stripe_webhook
from .views import CreateCheckoutSessionView

urlpatterns = [
    path('create-checkout-session/<uuid:course_id>/', CreateCheckoutSessionView.as_view(), name='create-checkout-session'),
    path('webhook/', stripe_webhook, name='stripe-webhook'),
]