from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from users.views import (
    AdminManageMembershipView, 
    OrganizationListCreateView, 
    RegisterView, 
    ProfileView, 
    EnrollOrganizationView,
    change_password
)

urlpatterns = [
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('login/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('register/', RegisterView.as_view(), name='auth_register'),
    path('profile/', ProfileView.as_view(), name='user_profile'),
    path('change-password/', change_password, name='change_password'),
    path('organizations/', OrganizationListCreateView.as_view(), name='organization-list'),
    path('org/<uuid:org_id>/enroll/', EnrollOrganizationView.as_view(), name='enroll-org'),
    path('org/<uuid:org_id>/manage-members/', AdminManageMembershipView.as_view(), name='manage-members'),
]
