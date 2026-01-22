from django.db import models 
from django.contrib.auth.models import AbstractUser

# Create your models here.
class User(AbstractUser):
    email = models.EmailField(unique=True) 
    is_student = models.BooleanField(default=True)
    profile_picture = models.ImageField(upload_to='profiles/', null=True, blank=True)
    bio = models.TextField(max_length=500, blank=True)
    avatar = models.TextField(null=True, blank=True)
    role = models.CharField(max_length=50, default='student')

    def __str__(self):
        return self.username