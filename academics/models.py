from django.db import models
from django.core.validators import MaxValueValidator
from django.core.exceptions import ValidationError

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
    marks = models.PositiveIntegerField(validators=[MaxValueValidator(100)])
    grade_letter = models.CharField(max_length=2, blank=True, null=True)
    semester = models.CharField(max_length=20)
    date_recorded = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'course', 'semester')
    
    def calculate_grade(self):
        if self.marks > 100:
            return "Invalid"
        elif self.marks >= 70:
            self.grade_letter = 'A'
        elif self.marks >= 60:
            self.grade_letter = 'B'
        elif self.marks >= 50:
            self.grade_letter = 'C'
        elif self.marks >= 45:
            self.grade_letter = 'D'
        else:
            self.grade_letter = 'F'
            

    def clean(self):
        # """Model validation to catch edge cases before saving."""
            if self.marks > 100:
             raise ValidationError({'marks': 'Marks cannot be higher than 100.'})
            
    def save(self, *args, **kwargs):
        self.full_clean() 
        self.grade_letter = self.calculate_grade()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.student.name} - {self.course.name}: {self.marks}"