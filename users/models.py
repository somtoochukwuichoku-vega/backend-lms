from enum import member
from pyexpat import model
from time import timezone
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
    is_public = models.BooleanField(default=False)
    def __str__(self):
        return self.name
    class Meta: 
     ordering = ['-id']


class Membership(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='memberships')
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=[
        ('admin', 'Admin'), 
        ('instructor', 'Instructor'), 
        ('student', 'Student')
    ])
    invite_code = models.CharField(max_length=12, blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        unique_together = ('user', 'organization')
        # i am trying to make sure that the user can only be a member of one organization and preventing duplicate entries
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} — {self.role} in {self.organization.name}"


class Delegation(models.Model):
    DELEGABLE_ROLES = [
        ('instructor', 'instructor'),
        ('admin', 'admin')
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    granted_to = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='delegations_received',
        help_text="The User receiving elevated access"
    )
    granted_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='delegations_granted',
        help_text="The Org admin or superuser who approved this"
    )
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='delegations'
    )
    temp_role = models.CharField(
        max_length=20,
        choices=DELEGABLE_ROLES,
        help_text="The elevated role being granted."
    )
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Leave blank for a permanent delegation. Set a datetime for auto-expiry."
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Set to False to revoke access without deleting the record."
    )
    # Audit trail
    created_at = models.DateTimeField(auto_now_add=True)
    revoked_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Automatically set when is_active is flipped to False."
    )
    reason = models.TextField(
        blank=True,
        help_text="Optional note explaining why this delegation was granted."
    )
    class Meta:
        ordering = ['-created_at']
        indexes = [
            # This index makes the permission check fast even with many delegations
            models.Index(fields=['granted_to', 'organization', 'is_active']),
        ]

    def __str__(self):
        expiry = self.expires_at.strftime('%Y-%m-%d') if self.expires_at else 'permanent'
        return (
            f"{self.granted_to.username} → {self.temp_role} "
            f"in {self.organization.name} (expires: {expiry})"
        )
    
    @property
    def is_currently_valid(self):

        if not self.is_active:
            return False
        if self.expires_at and self.expires_at <= timezone.now():
            return False
        return True

    def revoke(self):
        self.is_active = False
        self.revoked_at = timezone.now()
        self.save(update_fields=['is_active', 'revoked_at'])



