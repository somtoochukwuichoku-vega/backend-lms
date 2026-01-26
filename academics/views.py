from django.http import Http404
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes, parser_classes , renderer_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser

from rest_framework.renderers import JSONRenderer, BrowsableAPIRenderer

from academics.models import Course, Course_category, Course_level, Enrollment
from academics.serializers import CategorySerializer, CourseSerializer, EnrollmentSerializer, LevelSerializer



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