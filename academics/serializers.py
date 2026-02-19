from rest_framework import serializers
from academics.models import Assignment, Course, Course_category, Course_level, Enrollment, Lesson, Module
from users.models import Membership


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Course_category
        fields = '__all__'


class LevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course_level
        fields = '__all__'

class LessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = '__all__'
    
    def to_representation(self, instance):
        #Custom logic to hide video URLs from non-enrolled students#
        data = super().to_representation(instance)
        request = self.context.get('request')
        
        # If there is no authenticated user, or the lesson isn't a preview, 
        if not instance.is_preview:
            hide_video = True  # default: hide

            if request and request.user and request.user.is_authenticated:
                is_enrolled = Enrollment.objects.filter(
                    user=request.user,
                    course=instance.module.course
                ).exists()
                if is_enrolled:
                    hide_video = False

            if hide_video:
                data['video_url'] = None
                data['video_file'] = None

        return data

class ModuleSerializer(serializers.ModelSerializer):
    # This nests the lessons inside the module
    lessons = LessonSerializer(many=True, read_only=True)

    class Meta:
        model = Module
        fields = ['id', 'title', 'order', 'lessons']

class CourseSerializer(serializers.ModelSerializer):
    modules = ModuleSerializer(many=True, read_only=True)
    
    level = serializers.SlugRelatedField(
        slug_field='name', 
        queryset=Course_level.objects.all()
    )
    category = serializers.SlugRelatedField(
        slug_field='name', 
        queryset=Course_category.objects.all()
    )
    class Meta:
        model = Course
        fields = '__all__'
        read_only_fields = ['instructor', 'organization', 'enrolled', 'rating']

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

        if not Membership.objects.filter(user=user, organization=course.organization).exists():
            raise serializers.ValidationError(
                {'detail': 'You must be a member of this organization to enroll in its courses.'}
            )
        
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
    instructor = serializers.ReadOnlyField(source='course.instructor')
    categoryName = serializers.ReadOnlyField(source='course.category.name')
    levelName = serializers.ReadOnlyField(source='course.level.name')
    dueDate = serializers.DateTimeField(source='due_date')

    class Meta:
        model = Assignment
        fields = [
            'id', 'course', 'courseId', 'courseName', 'instructor', 
            'categoryName', 'levelName', 'title', 'description', 
            'dueDate', 'points', 'status'
        ]

