from django.conf import settings
from django.http import Http404, HttpResponse
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes, parser_classes , renderer_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import filters
import stripe

from payments.models import Transaction
from users.models import Organization
from .permissions import IsAdminUserRole, IsOrgInstructor

from rest_framework.renderers import JSONRenderer, BrowsableAPIRenderer

from academics.models import Assignment, Course, Course_category, Course_level, Enrollment
from academics.serializers import AssignmentSerializer, CategorySerializer, CourseSerializer, EnrollmentSerializer, LevelSerializer
from rest_framework.pagination import PageNumberPagination

from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.contrib.auth import get_user_model


class CategoryListCreateView(generics.ListCreateAPIView):
    queryset = Course_category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated] # I want to Ensure only logged-in users (admins) can do this

class LevelListCreateView(generics.ListCreateAPIView):
    queryset = Course_level.objects.all()
    serializer_class = LevelSerializer
    permission_classes = [IsAuthenticated]
class CourseListView(generics.ListCreateAPIView):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    parser_classes = (MultiPartParser, FormParser)

    filter_backends = [filters.SearchFilter]
    search_fields = ['title', 'description', 'instructor__username']

class CourseDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    lookup_field = 'pk'
    parser_classes = (MultiPartParser, FormParser)

class EnrollmentListView(generics.ListCreateAPIView):
    serializer_class = EnrollmentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Enrollment.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    endpoint_secret = settings.STRIPE_WEBHOOK_SECRET

    try:
        # Verifying to make sure the event came from Stripe
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except Exception as e:
        return HttpResponse(status=400)
    
    # We only care about successful payment completions
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        
        tx_id = session['metadata'].get('transaction_id')
        course_id = session['metadata']['course_id']
        user_id = session['metadata']['user_id']

        with transaction.atomic():

            # Find the local database record for this transaction using either the transaction_id or the Stripe checkout session ID
            if tx_id:
                tx = Transaction.objects.get(id=tx_id)
            else:
                tx = Transaction.objects.get(stripe_checkout_id=session['id'])

            tx = Transaction.objects.get(stripe_checkout_id=session['id'])

            # Save the Payment Intent ID (Needed for future refunds)
            tx.stripe_payment_intent_id = session.get('payment_intent')

            # Check the Payment Type
            is_installment = session['metadata'].get('is_installment') == "True"

            if is_installment:
                # Increment the count of installments paid
                tx.installments_paid += 1
                tx.status = 'completed'
                # Check if this was the final payment required

                if tx.installments_paid >= tx.total_installments:
                    tx.status = 'completed'
                    # Fully unlock the course and create enrollment
                    _enroll_user(user_id, course_id)
                else:
                    # Update status to partially paid to show progress in UI
                    tx.status = 'partially_paid'       
            else:
                # Standard one-time payment logic
                tx.status = 'completed'
                _enroll_user(user_id, course_id)
            
            tx.save()
    return HttpResponse(status=200)

def _enroll_user(user_id, course_id):
    """Helper function to handle user enrollment safely"""
    User = get_user_model()
    user = User.objects.get(id=user_id)
    course = Course.objects.get(id=course_id)
    Enrollment.objects.get_or_create(user=user, course=course)




@api_view(['GET'])
@permission_classes([IsAuthenticated])
def current_enrollments(request):
    enrollments = Enrollment.objects.filter(user=request.user).select_related('course')

    paginator = PageNumberPagination()
    paginated_enrollments = paginator.paginate_queryset(enrollments, request)
    
    enrolled_courses = []
    for enrollment in paginated_enrollments:
        course_data = CourseSerializer(enrollment.course).data
        course_data['progress'] = enrollment.progress
        course_data['completedLessons'] = enrollment.completed_lessons
        course_data['isEnrolled'] = True
        enrolled_courses.append(course_data)
    
    return paginator.get_paginated_response(enrolled_courses)

# @api_view(['GET','POST'])
# @parser_classes([MultiPartParser, FormParser])
# @renderer_classes([JSONRenderer, BrowsableAPIRenderer])
# def courses_with_enrollment_status(request):


#     if request.method == 'POST':
#         serializer = CourseSerializer(data=request.data)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data, status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
#     courses = Course.objects.all()
#     courses_data = []
    
#     for course in courses:
#         course_data = CourseSerializer(course).data
        
#         if request.user.is_authenticated:
#             try:
#                 enrollment = Enrollment.objects.get(user=request.user, course=course)
#                 course_data['isEnrolled'] = True
#                 course_data['progress'] = enrollment.progress
#                 course_data['completedLessons'] = enrollment.completed_lessons
#             except Enrollment.DoesNotExist:
#                 course_data['isEnrolled'] = False
#                 course_data['progress'] = 0
#                 course_data['completedLessons'] = 0
#         else:
#             course_data['isEnrolled'] = False
#             course_data['progress'] = 0
#             course_data['completedLessons'] = 0
            
#         courses_data.append(course_data)
    
#     return Response(courses_data, status=status.HTTP_200_OK)


class CourseCreateView(generics.CreateAPIView):
    serializer_class = CourseSerializer
    permission_classes = [IsOrgInstructor]
    parser_classes = (MultiPartParser, FormParser)

    def perform_create(self, serializer):
        
        org_id = self.kwargs.get('org_id')
        serializer.save(
            instructor=self.request.user,
            organization_id=org_id
        )


class CourseListWithEnrollmentView(generics.ListAPIView):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer # This line enables the HTML form
    permission_classes = [IsAdminUserRole]
    parser_classes = (MultiPartParser, FormParser)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        courses_data = []
        
        for course in queryset:
            course_data = self.get_serializer(course).data
            
            if request.user.is_authenticated:
                try:
                    enrollment = Enrollment.objects.get(user=request.user, course=course)
                    course_data['isEnrolled'] = True
                    course_data['progress'] = enrollment.progress
                    course_data['completedLessons'] = enrollment.completed_lessons
                except Enrollment.DoesNotExist:
                    course_data['isEnrolled'] = False
                    course_data['progress'] = 0
                    course_data['completedLessons'] = 0
            else:
                course_data['isEnrolled'] = False
                course_data['progress'] = 0
                course_data['completedLessons'] = 0
                
            courses_data.append(course_data)
        
        return Response(courses_data)
    

class AssignmentListCreateView(generics.ListCreateAPIView):
    serializer_class = AssignmentSerializer
    permission_classes = [IsAuthenticated]

    filter_backends = [filters.SearchFilter]
    search_fields = ['title', 'description', 'course__title']

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            user_orgs = Organization.objects.filter(members=user)
            return Assignment.objects.filter(course__organization__in=user_orgs)
        
        enrolled_course_ids = Enrollment.objects.filter(user=user).values_list('course_id', flat=True)
        return Assignment.objects.filter(course_id__in=enrolled_course_ids)

# View for Retrieving, Updating, and Deleting a specific Assignment
class AssignmentDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Assignment.objects.all()
    serializer_class = AssignmentSerializer
    # permission_classes = [IsAuthenticated]
    permission_classes = [IsAdminUserRole]
    lookup_field = 'pk'

# Specialized Dashboard View
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def upcoming_assignments(request):
    user = request.user
    enrolled_courses = Enrollment.objects.filter(user=user).values_list('course_id', flat=True)
    
    assignments = Assignment.objects.filter(
        course_id__in=enrolled_courses,
        status="pending"
    ).order_by('due_date')[:5]
    
    serializer = AssignmentSerializer(assignments, many=True)
    return Response(serializer.data)