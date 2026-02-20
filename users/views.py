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

    
class RequestJoinView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, org_id):
        org = get_object_or_404(Organization, id=org_id)
        # Create a "Locked" membership. No code is generated yet.
        # This acts as the "Notification" to the admin.
        membership, created = Membership.objects.get_or_create(
            user=request.user,
            organization=org,
            defaults={'is_verified': False, 'role': 'student'}
        )
        if not created:
            return Response({"detail": "Request already exists."}, status=400)
        return Response({"message": "Join request sent to Admin."})

# --- FLOW 2: ADMIN APPROVES OR INVITES ---
class AdminManageMembershipView(APIView):
    permission_classes = [IsOrgAdmin]

    # Admin sees all pending requests
    def get(self, request, org_id):
        pending = Membership.objects.filter(organization_id=org_id, is_verified=False)
        # (Simplify with a serializer in your real code)
        data = [{"user": m.user.email, "id": m.id} for m in pending]
        return Response(data)

    # Admin approves a request OR creates a new invite for someone who didn't request
    def post(self, request, org_id):
        email = request.data.get('email')
        role = request.data.get('role', 'student')
        user_to_invite = get_object_or_404(User, email=email)
        
        # Find existing request or create new record
        membership, created = Membership.objects.get_or_create(
            user=user_to_invite, 
            organization_id=org_id
        )
        
        # Auto-generate the unique code
        code = str(uuid.uuid4())[:8].upper()
        membership.invite_code = code
        membership.role = role
        membership.save()

        # SUCCESS: In production, trigger an email here containing the code.
        return Response({
            "message": f"Invite code generated for {email}",
            "invite_code": code 
        })

# --- FLOW 3: USER VERIFIES CODE ---
class VerifyMembershipView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, org_id):
        code = request.data.get('invite_code')
        membership = get_object_or_404(
            Membership, 
            user=request.user, 
            organization_id=org_id, 
            invite_code=code
        )
        
        membership.is_verified = True
        membership.invite_code = None # Burn the code
        membership.save()
        
        return Response({"message": "Membership verified. Welcome!"})

class JoinOrganizationView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, org_id):
        organization = get_object_or_404(Organization, id=org_id)
        # Check if they are already a member

        if Membership.objects.filter(user=request.user, organization=organization).exists():
            return Response({'detail': 'Already a member of this organization.'}, status=400)
        
        # Create the membership
        Membership.objects.create(
            user=request.user,
            organization=organization,
            role='student'  # Default role for joining
        )
        return Response({'message': f'Successfully joined {organization.name}'})