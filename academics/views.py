from django.http import Http404
from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from rest_framework import mixins, generics

from academics.models import Course
from academics.serializers import CourseSerializer

# Create your views here.
class CourseListView (APIView):
    def get(self, request):
        course = Course.objects.all()
        serializer = CourseSerializer(course, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        serializer = CourseSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        print(serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)





class CourseDetailView (APIView):
    def get_object(self, pk):
        try: 
            return Course.objects.get(pk=pk)
        except Course.DoesNotExist:
            raise Http404
        
    def get(self,request, pk):
        course = self.get_object(pk=pk)
        serializer = CourseSerializer(course)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def put(self,request, pk):
        course = self.get_object(pk=pk)
        serializer = CourseSerializer(course, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self,request,pk):
       course = self.get_object(pk=pk) 
       course.delete()
       return Response(status=status.HTTP_204_NO_CONTENT)
        



#MIXINS AND GENERICS

class GradeListView (mixins.CreateModelMixin):
   print('hi')



# class GradeDetailView (APIView):
#    print('hi')


# class GradeDetailView (APIView):
#     print('hi')