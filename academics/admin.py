from django.contrib import admin

from .models import Assignment, Course, Course_category, Enrollment, Course_level, Submission

# Register your models here.
admin.site.register(Course)
admin.site.register(Enrollment)
admin.site.register(Assignment)
admin.site.register(Submission)
admin.site.register(Course_category)
admin.site.register(Course_level)