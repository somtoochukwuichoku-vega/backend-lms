from django.http import Http404
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser

from academics.models import Course, Enrollment
from academics.serializers import CourseSerializer, EnrollmentSerializer

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

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def current_enrollments(request):
    enrollments = Enrollment.objects.filter(user=request.user).select_related('course')
    
    enrolled_courses = []
    for enrollment in enrollments:
        course_data = CourseSerializer(enrollment.course).data
        course_data['progress'] = enrollment.progress
        course_data['completedLessons'] = enrollment.completed_lessons
        course_data['isEnrolled'] = True
        enrolled_courses.append(course_data)
    
    return Response(enrolled_courses, status=status.HTTP_200_OK)

@api_view(['GET'])
def courses_with_enrollment_status(request):
    courses = Course.objects.all()
    courses_data = []
    
    for course in courses:
        course_data = CourseSerializer(course).data
        
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
    
    return Response(courses_data, status=status.HTTP_200_OK)
