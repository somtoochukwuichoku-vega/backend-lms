from rest_framework import serializers

from academics.models import Course, Grade




class StudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Grade
        fields = "__all__"



class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = "__all__"