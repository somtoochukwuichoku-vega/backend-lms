from django.contrib import admin

from .models import Course, Grade

# Register your models here.
admin.site.register(Course)
admin.site.register(Grade)