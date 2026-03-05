import django.db.models
import uuid
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.parsers import MultiPartParser, FormParser

from academics.permissions import IsOrgAdmin
from .models import Membership, Organization, User
from .serializers import OrganizationSerializer, RegisterSerializer, ProfileSerializer
from rest_framework.views import APIView
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer

class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)
    
    def get_object(self):
        return self.request.user
    
    def get(self, request, *args, **kwargs):
        """Get current user's profile"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    def put(self, request, *args, **kwargs):
        """Update current user's profile"""
        return self.update(request, *args, **kwargs)
    
    def patch(self, request, *args, **kwargs):
        """Partially update current user's profile"""
        return self.partial_update(request, *args, **kwargs)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    """Change user password"""
    user = request.user
    old_password = request.data.get('old_password')
    new_password = request.data.get('new_password')
    
    if not old_password or not new_password:
        return Response(
            {'error': 'Both old_password and new_password are required'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if not user.check_password(old_password):
        return Response(
            {'error': 'Old password is incorrect'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    user.set_password(new_password)
    user.save()
    
    return Response({'message': 'Password changed successfully'})

class OrganizationListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = OrganizationSerializer
    
    def get_queryset(self):
        return Organization.objects.filter(members=self.request.user)

    
# class RequestJoinView(APIView):
#     permission_classes = [IsAuthenticated]
#     def post(self, request, org_id):
#         org = get_object_or_404(Organization, id=org_id)
#         # Create a "Locked" membership. No code is generated yet.
#         # This acts as the "Notification" to the admin.
#         membership, created = Membership.objects.get_or_create(
#             user=request.user,
#             organization=org,
#             defaults={'is_verified': False, 'role': 'student'}
#         )
#         if not created:
#             return Response({"detail": "Request already exists."}, status=400)
#         return Response({"message": "Join request sent to Admin."})


class PublicOrganizationListView(generics.ListAPIView):
    """
    Returns only public organizations that the current user 
    is NOT already a member of.
    """
    serializer_class = OrganizationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        # Get IDs of orgs the user is already in
        my_org_ids = Membership.objects.filter(user=user).values_list('organization_id', flat=True)
        
        # Return public orgs excluding the ones user already joined
        return Organization.objects.filter(is_public=True).exclude(id__in=my_org_ids)

class EnrollOrganizationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, org_id):
        organization = get_object_or_404(Organization, id=org_id)
        
        # Checking to know if membership already exists (active or pending)
        membership, created = Membership.objects.get_or_create(
            user=request.user,
            organization=organization,
            defaults={'role': 'student'}
        )

        if not created:
            status_text = "active" if membership.is_verified else "pending approval"
            return Response({"detail": f"You already have an {status_text} membership."}, status=400)

        # checking if the organization is public
        if getattr(organization, 'is_public', False):
            membership.is_verified = True
            membership.save()
            return Response({"message": f"Successfully joined {organization.name}."}, status=201)
        
        return Response({"message": "Join request sent to Admin for approval."}, status=202)


class AdminManageMembershipView(APIView):
    permission_classes = [IsOrgAdmin]

    def get(self, request, org_id):
        pending = Membership.objects.filter(organization_id=org_id, is_verified=False)
        data = [{"membership_id": m.id, "user_email": m.user.email, "requested_at": m.created_at} for m in pending]
        return Response(data)

    def post(self, request, org_id):
        membership_id = request.data.get('membership_id')
        email = request.data.get('email') # For direct adds

        if membership_id:
            # Case 1: Approving a pending request
            membership = get_object_or_404(Membership, id=membership_id, organization_id=org_id)
            membership.is_verified = True
            membership.save()
            return Response({"message": f"User {membership.user.email} approved successfully."})
        
        elif email:
            # Case 2: Admin is force-adding a user who didn't request
            user_to_add = get_object_or_404(User, email=email)
            membership, created = Membership.objects.get_or_create(
                user=user_to_add,
                organization_id=org_id,
                defaults={'is_verified': True, 'role': 'student'}
            )
            if not created:
                membership.is_verified = True
                membership.save()
            return Response({"message": f"User {email} has been added directly."})
            
        return Response({"error": "Provide membership_id or email"}, status=400)