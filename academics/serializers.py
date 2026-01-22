from rest_framework import serializers

from academics.models import Course, Grade




class GradeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Grade
        fields = "__all__"
        read_only_fields = ['grade_letter']



class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = "__all__"