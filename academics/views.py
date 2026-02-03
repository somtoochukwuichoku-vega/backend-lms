from django.conf import settings
from django.http import Http404, HttpResponse
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes, parser_classes , renderer_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
import stripe

from payments.models import Transaction
from .permissions import IsAdminUserRole

from rest_framework.renderers import JSONRenderer, BrowsableAPIRenderer

from academics.models import Assignment, Course, Course_category, Course_level, Enrollment
from academics.serializers import AssignmentSerializer, CategorySerializer, CourseSerializer, EnrollmentSerializer, LevelSerializer
from rest_framework.pagination import PageNumberPagination

from django.views.decorators.csrf import csrf_exempt



class CategoryListCreateView(generics.ListCreateAPIView):
    queryset = Course_category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated] # Ensure only logged-in users (admins) can do this

class LevelListCreateView(generics.ListCreateAPIView):
    queryset = Course_level.objects.all()
    serializer_class = LevelSerializer
    permission_classes = [IsAuthenticated]
class CourseListView(generics.ListCreateAPIView):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    parser_classes = (MultiPartParser, FormParser)

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
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except Exception as e:
        return HttpResponse(status=400)
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        
        # Fulfill the purchase
        course_id = session['metadata']['course_id']
        user_id = session['metadata']['user_id']
        
        # Update Transaction status
        transaction = Transaction.objects.get(stripe_checkout_id=session['id'])
        transaction.status = 'completed'
        transaction.save()

        # Create Enrollment in academics app
        course = Course.objects.get(id=course_id)
        from users.models import User
        user = User.objects.get(id=user_id)
        Enrollment.objects.get_or_create(user=user, course=course)

    return HttpResponse(status=200)




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
class CourseListWithEnrollmentView(generics.ListCreateAPIView):
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

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Assignment.objects.all()
        
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