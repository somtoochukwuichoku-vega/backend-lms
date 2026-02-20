from django.utils import timezone
from django.shortcuts import get_object_or_404, render
from rest_framework import generics, status

from rest_framework.response import Response
from rest_framework.views import APIView

from academics.permissions import IsDelegationManager, get_effective_role
from delegations.serializer import DelegationCreateSerializer, DelegationReadSerializer, DelegationRevokeSerializer, EffectiveRoleSerializer
from users.models import Delegation, Membership, Organization, User,models


class DelegationListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsDelegationManager]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return DelegationCreateSerializer
        return DelegationReadSerializer
    def get_queryset(self):
        org_id = self.kwargs.get('org_id')
        queryset = Delegation.objects.filter(
            organization_id=org_id
        ).select_related('granted_to', 'granted_by', 'organization')

        # Optional status filter from query param e.g. ?status=active
        status_filter = self.request.query_params.get('status')
        now = timezone.now()

        if status_filter == 'active':
            queryset = queryset.filter(
                is_active=True
            ).filter(
                models.Q(expires_at__isnull=True) | models.Q(expires_at__gt=now)
            )
        elif status_filter == 'expired':
            queryset = queryset.filter(is_active=True, expires_at__lte=now)
        elif status_filter == 'revoked':
            queryset = queryset.filter(is_active=False)
        elif status_filter == 'permanent':
            queryset = queryset.filter(is_active=True, expires_at__isnull=True)

        return queryset
    
    def perform_create(self, serializer):
        org_id = self.kwargs.get('org_id')
        org = get_object_or_404(Organization, id=org_id)
        serializer.save(
            granted_by=self.request.user,
            organization=org
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        # Return full detail using the read serializer
        read_serializer = DelegationReadSerializer(
            serializer.instance,
            context=self.get_serializer_context()
        )
        return Response(read_serializer.data, status=status.HTTP_201_CREATED)

class DelegationDetailView(generics.RetrieveAPIView):
    serializer_class = DelegationReadSerializer
    permission_classes = [IsDelegationManager]

    def get_queryset(self):
        return Delegation.objects.filter(
            organization_id=self.kwargs.get('org_id')
        ).select_related('granted_to', 'granted_by', 'organization')

class DelegationRevokeView(generics.UpdateAPIView):
    serializer_class = DelegationRevokeSerializer
    permission_classes = [IsDelegationManager]
    http_method_names = ['patch']

    def get_queryset(self):
        return Delegation.objects.filter(
            organization_id=self.kwargs.get('org_id'),
            is_active=True  # Can only revoke active delegations
        )

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data={'is_active': False}, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({
            'message': f"Delegation for {instance.granted_to.username} has been revoked.",
            'revoked_at': instance.revoked_at,
        })
    

class EffectiveRoleView(APIView):
    """
    Returns the full access picture for a user in this org — their membership
    role, any active delegation, and the resolved effective role.
    """
    permission_classes = [IsDelegationManager]

    def get(self, request, org_id):
        # Determine which user to check
        user_id = request.query_params.get('user_id')

        if user_id:
            # Only admins/superusers can check other users (already enforced by permission class)
            target_user = get_object_or_404(User, id=user_id)
        else:
            target_user = request.user

        org = get_object_or_404(Organization, id=org_id)

        # Get membership role
        membership = Membership.objects.filter(
            user=target_user,
            organization_id=org_id,
            is_verified=True
        ).first()
        membership_role = membership.role if membership else None

        # Get active delegation role
        now = timezone.now()
        delegation = Delegation.objects.filter(
            granted_to=target_user,
            organization_id=org_id,
            is_active=True
        ).filter(
            models.Q(expires_at__isnull=True) | models.Q(expires_at__gt=now)
        ).first()
        delegation_role = delegation.temp_role if delegation else None
        delegation_expires = delegation.expires_at if delegation else None

        # Resolve effective role using the same function the permission classes use
        effective_role = get_effective_role(target_user, org_id)

        data = {
            'user_id': target_user.id,
            'username': target_user.username,
            'email': target_user.email,
            'org_id': org_id,
            'org_name': org.name,
            'effective_role': effective_role,
            'membership_role': membership_role,
            'delegation_role': delegation_role,
            'delegation_expires_at': delegation_expires,
            'is_superuser': target_user.is_superuser,
        }

        serializer = EffectiveRoleSerializer(data)
        return Response(serializer.data)