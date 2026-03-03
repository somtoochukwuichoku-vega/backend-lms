from django.utils import timezone
from rest_framework import permissions

from django.db import models

# Using Role ranking to resolve the highest role when a user has both
ROLE_RANK = {
    'admin': 2,
    'instructor': 1,
    'student': 0,
}

#Approach is go opposit way incase you want to add more roles

def get_effective_role(user, org_id):
    from users.models import Membership,Delegation

    if user.is_superuser:
        return 'admin'

    membership = Membership.objects.filter(
        user = user,
        organization_id = org_id,
        is_verified = True
    ).first()
    membership_role = membership.role if membership else None

    delegation = Delegation.objects.filter(
        granted_to = user,
        organization_id = org_id,
        is_active = True
    ).filter(
        models.Q(expires_at__isnull=True) | models.Q(expires_at__gt=timezone.now())
    ).first()
    delegation_role = delegation.temp_role if delegation else None

    # Resolve the highest role from both sources
    candidates = [r for r in [membership_role,delegation_role] if r is not None]
    if not candidates:
        return None 
    return max(candidates, key=lambda r:ROLE_RANK[r])

class IsOrgMember(permissions.BasePermission):
    """
    Allows any verified member of the org (student, instructor, or admin).
    Used for read-only endpoints where all org members should have access.
    """
    message = "You must be a verified member of this organization."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        org_id = view.kwargs.get('org_id')
        if not org_id:
            return False
        return get_effective_role(request.user, org_id) is not None


class IsOrgInstructor(permissions.BasePermission):
    """
    Allows only instructors and admins of the org.
    Used for Creating operations on courses, modules, and lessons.
    """
    message = "You must be an instructor or admin of this organization."
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        org_id = view.kwargs.get('org_id')
        if not org_id:
            return False

        role = get_effective_role(request.user, org_id)
        return role in ['admin', 'instructor']

class IsOrgAdmin(permissions.BasePermission):
    """
    Allows only org admins (and platform superusers).
    Used for org management: approving memberships, granting delegations.
    """
    message = "You must be an admin of this organization."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        org_id = view.kwargs.get('org_id')
        if not org_id:
            return False

        role = get_effective_role(request.user, org_id)
        return role == 'admin'

class IsOrgInstructorOrReadOnly(permissions.BasePermission):
    """
    Used on ListCreateAPIView endpoints where students can list but
    only instructors can create — modules and lessons list views.
    """
    message = "Read access requires org membership. Write access requires instructor or admin role."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        org_id = view.kwargs.get('org_id')
        if not org_id:
            return False

        role = get_effective_role(request.user, org_id)

        if request.method in permissions.SAFE_METHODS:
            # Any verified member can read
            return role is not None

        return role in ['admin', 'instructor']

class IsCourseOwnerOrOrgAdmin(permissions.BasePermission):
    """
    Object-level permission for UPDATE and DELETE on Course, Module, or Lesson.
    """
    message = "You must be the course instructor or an org admin to modify this resource."

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False

        if request.method in permissions.SAFE_METHODS:
            return True

        course = _resolve_course(obj)
        if course is None:
            return False

        # Allow the instructor who created the course
        if course.instructor == request.user:
            return True

        # Allow any org admin (permanent or delegated)
        if course.organization_id:
            role = get_effective_role(request.user, course.organization_id)
            return role == 'admin'

        return False



class IsDelegationManager(permissions.BasePermission):
    """
    Controls who can create, revoke, and list delegations.
    """
    message = "Only org admins and platform superusers can manage delegations."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        # Platform superusers can always manage delegations
        if request.user.is_superuser:
            return True

        org_id = view.kwargs.get('org_id')
        if not org_id:
            return False

        role = get_effective_role(request.user, org_id)
        return role == 'admin'



def _resolve_course(obj):
    """
    Handles Course, Module, and Lesson transparently so IsCourseOwnerOrOrgAdmin
    works the same way regardless of which model type it receives.
    """
    from academics.models import Course, Module, Lesson

    if isinstance(obj, Course):
        return obj
    if isinstance(obj, Module):
        return obj.course
    if isinstance(obj, Lesson):
        return obj.module.course
    return None
