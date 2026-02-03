import stripe
from rest_framework.views import APIView

from django.shortcuts import get_object_or_404, render, redirect

from django.conf import settings
from django.contrib.auth.decorators import login_required
from academics.models import Course
from rest_framework.response import Response
from rest_framework import status

from payments.models import Transaction

# Create your views here.

stripe.api_key = settings.STRIPE_SECRET_KEY

class CreateCheckoutSessionView(APIView):
    def post(self, request, course_id):
        course = get_object_or_404(Course, id=course_id)
        user = request.user
        try:
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data':{
                        'currency':'usd',
                        'product_data':{'name':course.title},
                        'unit_amount':int(course.price * 100)
                    },
                    'quantity': 1,
                }],
                mode='payment',
                success_url=settings.CLIENT_URL + '/success?session_id={CHECKOUT_SESSION_ID}',
                cancel_url=settings.CLIENT_URL + '/cancel',
                metadata={
                    'course_id': str(course.id),
                    'user_id': str(user.id)
                }

            )
            # Create a pending transaction
            Transaction.objects.create(
                user=user,
                course=course,
                stripe_checkout_id=checkout_session.id,
                amount=int(course.price * 100), # Match the unit_amount above
                status='pending'
            )

            return Response({'url': checkout_session.url})
        except Exception as e:
            return Response({'error':str(e)}, status=status.HTTP_400_BAD_REQUEST)