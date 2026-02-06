from enum import member
import uuid
from django.db import models 
from django.contrib.auth.models import AbstractUser

# Create your models here.
# class User(AbstractUser):
#     email = models.EmailField(unique=True) 
#     is_student = models.BooleanField(default=True)
#     profile_picture = models.ImageField(upload_to='profiles/', null=True, blank=True)
#     bio = models.TextField(max_length=500, blank=True)
#     avatar = models.TextField(null=True, blank=True)
#     role = models.CharField(max_length=50, default='student')

#     def __str__(self):
#         return self.username

class User(AbstractUser):
    email = models.EmailField(unique=True) 
    
    profile_picture = models.ImageField(upload_to='profiles/', null=True, blank=True)
    bio = models.TextField(max_length=500, blank=True)
    avatar = models.TextField(null=True, blank=True)
    

    def __str__(self):
        return self.username
    

class Organization(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    creator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='owned_orgs')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)    
    members = models.ManyToManyField(User, through='Membership', related_name='organizations')
    def __str__(self):
        return self.name


class Membership(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='memberships')
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=[
        ('admin', 'Admin'), 
        ('instructor', 'Instructor'), 
        ('student', 'Student')
    ])
    class Meta:
        unique_together = ('user', 'organization')