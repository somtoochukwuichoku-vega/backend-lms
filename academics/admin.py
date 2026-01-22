from django.contrib import admin

from .models import Assignment, Course, Enrollment, Submission

# Register your models here.
admin.site.register(Course)
admin.site.register(Enrollment)
admin.site.register(Assignment)
admin.site.register(Submission)