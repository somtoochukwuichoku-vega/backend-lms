import rest_framework.permissions
import stripe
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from django.shortcuts import get_object_or_404, render, redirect

from django.conf import settings
from django.contrib.auth.decorators import login_required
from academics.models import Course
from rest_framework.response import Response
from rest_framework import status

from payments.models import Transaction
from academics.permissions import IsOrgAdmin

# Create your views here.

stripe.api_key = settings.STRIPE_SECRET_KEY

class CreateCheckoutSessionView(APIView):
    permission_classes = [IsAuthenticated]
    
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
            Transaction.objects.create(
                user=user,
                course=course,
                stripe_checkout_id=checkout_session.id,
                amount=int(course.price * 100),
                status='pending'
            )

            return Response({'url': checkout_session.url})
        except Exception as e:
            return Response({'error':str(e)}, status=status.HTTP_400_BAD_REQUEST)
        



class RefundPaymentView(APIView):
    permission_classes = [IsOrgAdmin]
    def post(self, request, transaction_id):
        transaction = get_object_or_404(Transaction, id=transaction_id)
        if transaction.status != 'completed':
            return Response({'error': 'Only completed transactions can be refunded.'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            refund = stripe.Refund.create(
                payment_intent=transaction.stripe_payment_intent_id,
                amount=int(transaction.amount * 100),
            )
            transaction.status = 'refunded'
            transaction.refund_id = refund.id
            transaction.save()
            return Response({'message': 'Refund successful.'})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        


class CreateInstallmentSessionView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, course_id):
        course = get_object_or_404(Course, id=course_id)
        user = request.user
        
        # Calculate installment amount in cents
        total_amount_cents = int(course.price * 100)
        installment_amount = total_amount_cents // 3
        
        try:
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {'name': f"{course.title} - Installment 1/3"},
                        'unit_amount': installment_amount
                    },
                    'quantity': 1,
                }],
                mode='payment',
                success_url=settings.CLIENT_URL + '/success?session_id={CHECKOUT_SESSION_ID}',
                cancel_url=settings.CLIENT_URL + '/cancel',
                metadata={
                    'course_id': str(course.id),
                    'user_id': str(user.id),
                    'is_installment': "True", # Stripe metadata must be strings
                    'total_installments': "3",
                    'current_installment': "1" 
                }
            )

            Transaction.objects.create(
                user=user,
                course=course,
                stripe_checkout_id=checkout_session.id,
                amount=course.price / 3, # Store as decimal in DB if using DecimalField
                status='pending',
                is_installment=True,
                total_installments=3,
                installments_paid=0 # Webhook will increment this to 1 on success
            )

            return Response({'url': checkout_session.url})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        

class ProcessInstallmentView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, transaction_id):
        tx = get_object_or_404(Transaction, id=transaction_id, user=request.user)

        # 1. I Found the specific transaction record for this user
        tx = get_object_or_404(Transaction, id=transaction_id, user=request.user)
        
        # 2. check first to see if full paymement was made: stop if already paid
        if tx.status == 'completed' or tx.installments_paid >= tx.total_installments:
            return Response({'error': 'This course is already fully paid.'}, status=400)

        # 3. Calculating the NEXT installment number and amount
        next_part = tx.installments_paid + 1
        installment_amount_cents = int((tx.course.price / tx.total_installments) * 100)

        try:
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {'name': f"{tx.course.title} - Installment {next_part}/{tx.total_installments}"},
                        'unit_amount': installment_amount_cents,
                    },
                    'quantity': 1,
                }],
                mode='payment',
                success_url=settings.CLIENT_URL + '/success?session_id={CHECKOUT_SESSION_ID}',
                cancel_url=settings.CLIENT_URL + '/cancel',
                metadata={
                    'transaction_id': str(tx.id), # Crucial for the webhook
                    'is_installment': "True"
                }
            )
            # Update the record with the new session ID so the webhook can find it
            tx.stripe_checkout_id = checkout_session.id
            tx.save()
            return Response({'url': checkout_session.url})
        
        except Exception as e:
            return Response({'error': str(e)}, status=400)