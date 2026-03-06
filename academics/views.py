from django.utils import timezone
from django.conf import settings
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes, parser_classes , renderer_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import filters
import stripe

from academics.permissions import IsCourseOwnerOrOrgAdmin, IsOrgInstructor, IsOrgInstructorOrReadOnly, IsOrgMember
from academics.tasks import generate_lesson_summary_task
from academics.utils import generate_lesson_summary
from payments.models import Transaction
from users.models import Delegation, Membership, Organization

from rest_framework.renderers import JSONRenderer, BrowsableAPIRenderer

from academics.models import Assignment, Course, Course_category, Course_level, Enrollment, Lesson, Module
from academics.serializers import AssignmentSerializer, CategorySerializer, CourseSerializer, EnrollmentSerializer, LessonSerializer, LevelSerializer, ModuleSerializer
from rest_framework.pagination import PageNumberPagination

from django.views.decorators.csrf import csrf_exempt
from django.db import connection, transaction
from django.contrib.auth import get_user_model

from django.db.models import Q


class CategoryListCreateView(generics.ListCreateAPIView):
    queryset = Course_category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated] # I want to Ensure only logged-in users (admins) can do this

class LevelListCreateView(generics.ListCreateAPIView):
    queryset = Course_level.objects.all()
    serializer_class = LevelSerializer
    permission_classes = [IsAuthenticated]

#COURSES
class CourseListCreateView(generics.ListCreateAPIView):
    """
    Public course list scoped to an org.
    Any verified org member (student, instructor, admin) can list courses.
    Search by title, description, or instructor username.
    """
    # queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [IsOrgInstructorOrReadOnly]
    parser_classes = (MultiPartParser, FormParser)

    filter_backends = [filters.SearchFilter]
    search_fields = ['title', 'description', 'instructor__username']

    def get_queryset(self):
       org_id = self.kwargs.get('org_id')
       return Course.objects.filter(organization_id=org_id)
    
    def perform_create(self, serializer):
        serializer.save(
            instructor=self.request.user,
            organization_id=self.kwargs.get('org_id')
        )


class CourseDetailView(generics.RetrieveUpdateDestroyAPIView):
    # queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [IsCourseOwnerOrOrgAdmin]
    lookup_field = 'pk'
    parser_classes = (MultiPartParser, FormParser)

    def get_queryset(self):
        return Course.objects.filter(organization_id=self.kwargs.get('org_id'))



class CourseListWithEnrollmentView(generics.ListAPIView):
    """
    Returns courses with enrollment status attached.
    Scoped to the authenticated user's org memberships.
    Any authenticated user can access this.
    """
    # queryset = Course.objects.all()

    serializer_class = CourseSerializer # This line enables the HTML form
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    def get_queryset(self):
        # Return only courses from orgs the user belongs to
        user_org_ids = Membership.objects.filter(
            user=self.request.user,
            is_verified=True
        ).values_list('organization_id', flat=True)
        
        return Course.objects.filter(organization_id__in=user_org_ids)

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

            # tx = Transaction.objects.get(stripe_checkout_id=session['id'])

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


#MODULES
class ModuleListCreateView(generics.ListCreateAPIView):
    serializer_class = ModuleSerializer
    permission_classes = [IsOrgInstructorOrReadOnly]

    def get_queryset(self):
        # Only show modules belonging to the specific course in the URL
        return Module.objects.filter(course_id=self.kwargs.get('course_id'))

    def perform_create(self, serializer):
        course_id = self.kwargs.get('course_id')
        course = get_object_or_404(Course, id=course_id)

        last_module = Module.objects.filter(course=course).order_by('-order').first()
        # 2. If one exists, add 1. If not, start at 1.
        next_order = (last_module.order + 1) if last_module else 1

        serializer.save(course=course, order=next_order)


class ModuleDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Module.objects.all()
    serializer_class = ModuleSerializer
    # Use the IsOrgInstructor or a custom IsCourseOwner permission
    permission_classes = [IsCourseOwnerOrOrgAdmin]

    def get_queryset(self):
        return Module.objects.filter(
            course__organization_id=self.kwargs.get('org_id')
        ).select_related('course')


#LESSON
class LessonListCreateView(generics.ListCreateAPIView):
    serializer_class = LessonSerializer
    permission_classes = [IsOrgInstructorOrReadOnly]
    parser_classes = (MultiPartParser, FormParser)

    def get_queryset(self):
        # Only show lessons belonging to the specific module in the URL
        return Lesson.objects.filter(module_id=self.kwargs.get('module_id'))

    def perform_create(self, serializer):
        module_id = self.kwargs.get('module_id')
        module = get_object_or_404(Module, id=module_id)

        last_lesson = Lesson.objects.filter(module=module).order_by('-order').first()
        # Calculate the next order number
        next_order = (last_lesson.order + 1) if last_lesson else 1  
        serializer.save(module=module, order=next_order)


class LessonDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    # Use the IsOrgInstructor or a custom IsCourseOwner permission
    permission_classes = [IsCourseOwnerOrOrgAdmin]
    parser_classes = (MultiPartParser, FormParser)

    
    def get_queryset(self):
        return Lesson.objects.filter(
            module__course__organization_id=self.kwargs.get('org_id')
        ).select_related('module__course')

class GenerateLessonSummaryView(APIView):
    permission_classes = [IsAuthenticated, IsOrgInstructor]

    def post(self, request,org_id, lesson_id):
        lesson = get_object_or_404(Lesson, id=lesson_id, module__course__organization_id=org_id)

        # connection.close()

        #Add checks and validation
        #Good practice is creating a queue
        try:
            # Call the AssemblyAI + Groq utility
           
            # # Saving both results to DB
            # lesson.transcript = ai_results['transcript']
            # lesson.summary = ai_results['summary']
            # lesson.save()

            if lesson.summary and not request.data.get('overwrite'):
                return Response({
                "message": "A summary already exists for this lesson. Use 'overwrite': true to reprocess.",
                "transcript": lesson.transcript,
                "summary": lesson.summary
            }, status=status.HTTP_200_OK)

            if not lesson.video_file and not lesson.video_url:
                return Response(
                {"error": "This lesson has no video file or URL to process."}, 
                status=status.HTTP_400_BAD_REQUEST
            )

            generate_lesson_summary_task.enqueue(str(lesson.id))
            return Response({
                "message": "AI Processing Complete",
                "transcript": lesson.transcript,
                "summary": lesson.summary
            })
       
        except Exception as e:
            return Response({"error": str(e)}, status=500)


#ASSIGNMENT
class AssignmentListCreateView(generics.ListCreateAPIView):
    serializer_class = AssignmentSerializer
    permission_classes = [IsAuthenticated]

    filter_backends = [filters.SearchFilter]
    search_fields = ['title', 'description', 'course__title']

    def get_queryset(self):
        from academics.permissions import get_effective_role
        user = self.request.user

         # Superusers see everything
        if user.is_superuser:
            return Assignment.objects.all().select_related('course__organization')
        
        # Find all orgs where user has instructor or admin access (permanent or delegated)
        # Orgs via permanent membership
        instructor_org_ids = set(
            Membership.objects.filter(
                user=user,
                role__in=['admin', 'instructor'],
                is_verified=True
            ).values_list('organization_id', flat=True)
        )

        # Orgs via active delegation
        delegated_org_ids = set(
            Delegation.objects.filter(
                granted_to=user,
                temp_role__in=['admin', 'instructor'],
                is_active=True
            ).filter(
                Q(expires_at__isnull=True) | Q(expires_at__gt=timezone.now())
            ).values_list('organization_id', flat=True)
        )

        elevated_org_ids = instructor_org_ids | delegated_org_ids

        if elevated_org_ids:
            return Assignment.objects.filter(
                course__organization_id__in=elevated_org_ids
            ).select_related('course__organization')

        # Students: only assignments for enrolled courses
        enrolled_course_ids = Enrollment.objects.filter(
            user=user
        ).values_list('course_id', flat=True)
        return Assignment.objects.filter(
            course_id__in=enrolled_course_ids
        ).select_related('course__organization')

# View for Retrieving, Updating, and Deleting a specific Assignment
class AssignmentDetailView(generics.RetrieveUpdateDestroyAPIView): 
    queryset = Assignment.objects.all()
    serializer_class = AssignmentSerializer
    permission_classes = [IsCourseOwnerOrOrgAdmin]
    lookup_field = 'pk'

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Assignment.objects.all().select_related('course__organization')

        instructor_org_ids = set(
            Membership.objects.filter(
                user=user,
                role__in=['admin', 'instructor'],
                is_verified=True
            ).values_list('organization_id', flat=True)
        )
        delegated_org_ids = set(
            Delegation.objects.filter(
                granted_to=user,
                temp_role__in=['admin', 'instructor'],
                is_active=True
            ).filter(
                Q(expires_at__isnull=True) | Q(expires_at__gt=timezone.now())
            ).values_list('organization_id', flat=True)
        )

        elevated_org_ids = instructor_org_ids | delegated_org_ids

        if elevated_org_ids:
            return Assignment.objects.filter(
                course__organization_id__in=elevated_org_ids
            ).select_related('course__organization')

        enrolled_course_ids = Enrollment.objects.filter(
            user=user
        ).values_list('course_id', flat=True)
        return Assignment.objects.filter(
            course_id__in=enrolled_course_ids
        ).select_related('course__organization')
    
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


    
