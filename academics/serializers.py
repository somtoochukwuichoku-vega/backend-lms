from rest_framework import serializers

from academics.models import Assignment, Course, Enrollment




# class GradeSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Grade
#         fields = "__all__"
#         read_only_fields = ['grade_letter']



class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = "__all__"



class EnrollmentSerializer(serializers.ModelSerializer):
    # Mapping userId and courseId to match frontend requirements
    userId = serializers.ReadOnlyField(source='user.id')
    courseId = serializers.ReadOnlyField(source='course.id')
    completedLessons = serializers.IntegerField(source='completed_lessons')
    isCompleted = serializers.BooleanField(source='is_completed')

    class Meta:
        model = Enrollment
        fields = ['id', 'userId', 'courseId', 'progress', 'completedLessons', 'isCompleted']

class AssignmentSerializer(serializers.ModelSerializer):
    # Adding courseName which is used in the dashboard UI
    courseName = serializers.ReadOnlyField(source='course.title')
    courseId = serializers.ReadOnlyField(source='course.id')
    dueDate = serializers.DateTimeField(source='due_date')

    class Meta:
        model = Assignment
        fields = ['id', 'courseId', 'courseName', 'title', 'description', 'dueDate', 'points', 'status']