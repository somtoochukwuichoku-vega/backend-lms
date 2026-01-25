from rest_framework import serializers
from academics.models import Assignment, Course, Course_category, Course_level, Enrollment


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Course_category
        fields = '__all__'


class LevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course_level
        fields = '__all__'

class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = '__all__'

    def to_representation(self, instance):
        # This handles the output (GET requests)
        data = super().to_representation(instance)
        if instance.thumbnail:
            data['thumbnail'] = instance.thumbnail.url
        return data

class EnrollmentSerializer(serializers.ModelSerializer):
    userId = serializers.ReadOnlyField(source='user.id')
    courseId = serializers.CharField(write_only=True)
    completedLessons = serializers.IntegerField(source='completed_lessons', read_only=True)
    isCompleted = serializers.BooleanField(source='is_completed', read_only=True)

    class Meta:
        model = Enrollment
        fields = ['id', 'userId', 'courseId', 'progress', 'completedLessons', 'isCompleted']
        read_only_fields = ['id', 'userId', 'progress', 'completedLessons', 'isCompleted']

    def create(self, validated_data):
        course_id = validated_data.pop('courseId')
        try:
            course = Course.objects.get(id=course_id)
        except Course.DoesNotExist:
            raise serializers.ValidationError({'courseId': 'Course not found'})

        # Get user from context - don't pass it to create() since perform_create handles it
        user = self.context['request'].user
        if Enrollment.objects.filter(user=user, course=course).exists():
            raise serializers.ValidationError({'courseId': 'Already enrolled in this course'})

        # Don't pass user here - let perform_create handle it
        enrollment = Enrollment.objects.create(
            course=course,
            **validated_data
        )
        return enrollment

class AssignmentSerializer(serializers.ModelSerializer):
    courseName = serializers.ReadOnlyField(source='course.title')
    courseId = serializers.ReadOnlyField(source='course.id')
    dueDate = serializers.DateTimeField(source='due_date')

    class Meta:
        model = Assignment
        fields = ['id', 'courseId', 'courseName', 'title', 'description', 'dueDate', 'points', 'status']
