from rest_framework import permissions

from users.models import Membership

class IsAdminUserRole(permissions.BasePermission):

    def has_permission(self, request, view):
        # safe methods Allows (GET, HEAD, OPTIONS) for everyone authenticated
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        
        return request.user and request.user.is_staff
    

class IsOrgAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        org_id = view.kwargs.get('org_id')
        if not request.user.is_authenticated or not org_id:
            return False
        
        return Membership.objects.filter(
            user=request.user, 
            organization_id=org_id, 
            role='admin'
        ).exists()
    

class IsOrgInstructor(permissions.BasePermission):
    def has_permission(self, request, view):
        org_id = view.kwargs.get('org_id')
        if not request.user.is_authenticated:
            return False
        
        org_id = view.kwargs.get('org_id')
        if not org_id:
            return False

        return Membership.objects.filter(
            user=request.user, 
            organization_id=org_id, 
            role__in=['admin', 'instructor'] # Admins can also do instructor tasks
        ).exists()
    
class IsCourseInstructorOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        # Checking If the object is a Course, check its instructor
        if hasattr(obj, 'instructor'):
            return obj.instructor == request.user
        # Checking If the object is a Lesson or Module, check the parent course instructor
        if hasattr(obj, 'module'):
            return obj.module.course.instructor == request.user
        if hasattr(obj, 'course'):
            return obj.course.instructor == request.user
        return False