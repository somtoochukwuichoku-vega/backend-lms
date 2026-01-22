from django.db import models
import uuid
from django.conf import settings


# Create your models here.
class Course(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField()
    instructor = models.CharField(max_length=255)
    thumbnail = models.TextField(null=True, blank=True) 
    category = models.CharField(max_length=100)
    duration = models.CharField(max_length=50)
    level = models.CharField(max_length=50) 
    enrolled = models.IntegerField(default=0)
    rating = models.IntegerField(default=0)
    total_lessons = models.IntegerField(default=0)

    def __str__(self):
        return self.title
    

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