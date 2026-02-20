from django.db import models
import uuid
from django.conf import settings

from cloudinary.models import CloudinaryField


# Create your models here.

class Course_category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    
    def __str__(self):
        return self.name

class Course_level(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name
class Course(models.Model):
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField()
    instructor = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='instructors_courses'
    )
    thumbnail = models.ImageField(upload_to='course_thumbnails/', null=True, blank=True)
    category = models.ForeignKey(Course_category, on_delete=models.SET_NULL, null=True)
    duration = models.CharField(max_length=50)
    level = models.ForeignKey(Course_level, on_delete=models.SET_NULL, null=True) 
    enrolled = models.IntegerField(default=0)
    rating = models.IntegerField(default=0)
    total_lessons = models.IntegerField(default=0)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_free = models.BooleanField(default=False)

    # NEW: Payment options
    allows_installments = models.BooleanField(
        default=False,
        help_text="Can students pay in installments?"
    )
    installment_count = models.PositiveIntegerField(
        default=1,
        help_text="How many installments are allowed"
    )
    installment_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Amount per installment (auto-calculated if blank)"
    )
    organization = models.ForeignKey(
        'users.Organization', 
        on_delete=models.CASCADE, 
        related_name='courses',
        null=True,
        blank=True
    )

    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        # Auto-calculate installment amount if allows_installments is True
        if self.allows_installments and not self.installment_amount:
            if self.installment_count > 0:
                self.installment_amount = self.price / self.installment_count
        
        # If free, set price to 0
        if self.is_free:
            self.price = 0
            self.allows_installments = False
            
        super().save(*args, **kwargs)
    

class Module(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='modules')
    title = models.CharField(max_length=255)
    order = models.PositiveIntegerField(default=0)
    class Meta:
        ordering = ['order']


class Lesson(models.Model):
    LESSON_TYPES = [('video', 'Video'), ('text', 'Text'), ('quiz', 'Quiz')]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField(max_length=255)
    content = models.TextField(blank=True)
    lesson_type = models.CharField(max_length=20, choices=LESSON_TYPES, default='video')
    video_url = models.URLField(null=True, blank=True)
    video_file = CloudinaryField(
        'video', 
        resource_type='video', 
        null=True, 
        blank=True,
        folder='lessons/videos/'
    )
    order = models.PositiveIntegerField(default=0)
    summary = models.TextField(blank=True, null=True)
    transcript = models.TextField(blank=True, null=True)
    is_preview = models.BooleanField(default=False) # Allow students to see some lessons for free
    class Meta:
        ordering = ['order']

class LessonStatus(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'lesson')
class Enrollment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    progress = models.IntegerField(default=0)
    completed_lessons = models.IntegerField(default=0)
    is_completed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} enrolled in {self.course.title}"



class Assignment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='assignments')
    title = models.CharField(max_length=255)
    description = models.TextField()
    due_date = models.DateTimeField()
    points = models.IntegerField(default=100)
    status = models.CharField(max_length=50, default="pending")

    def __str__(self):
        return f"{self.title} ({self.course.title})"

class Submission(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField()
    grade = models.IntegerField(null=True, blank=True)
    feedback = models.TextField(null=True, blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}'s work for {self.assignment.title}"