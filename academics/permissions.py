from rest_framework import permissions

class IsAdminUserRole(permissions.BasePermission):

    def has_permission(self, request, view):
        # Allow safe methods (GET, HEAD, OPTIONS) for everyone authenticated
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        
        # Check if the user is an admin via is_staff or custom role
        return request.user and (request.user.is_staff or request.user.role == 'admin')