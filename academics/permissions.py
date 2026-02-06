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