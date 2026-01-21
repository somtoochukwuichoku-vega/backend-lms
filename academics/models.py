from django.db import models

from studentsApp.models import Student

# Create your models here.
class Course(models.Model):
    name = models.CharField(max_length=100)
    course_code = models.CharField(max_length=10, unique=True)
    def __str__(self):
        return f"{self.course_code}: {self.name}"
    

class Grade(models.Model):
    # This creates the link: One Student can have many Grades
    student = models.ForeignKey(
        Student, 
        on_delete=models.CASCADE, 
        related_name='grades'
    )
    # This links the grade to a specific course
    course = models.ForeignKey(
        Course, 
        on_delete=models.CASCADE,
        related_name='course_grades'
    )
    marks = models.PositiveIntegerField()
    semester = models.CharField(max_length=20)
    date_recorded = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.name} - {self.course.name}: {self.marks}"