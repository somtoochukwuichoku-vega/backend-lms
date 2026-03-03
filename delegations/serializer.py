from django.utils import timezone
from rest_framework import serializers
from users.models import Delegation, Membership, Organization, User


class DelegationCreateSerializer(serializers.ModelSerializer):
    granted_to_email = serializers.EmailField(write_only=True)

    class Meta:
        model = Delegation
        fields = [
            'id',
            'granted_to_email', 
            'granted_to',
            'granted_by', 
            'organization',
            'temp_role',
            'expires_at',
            'reason',
            'is_active',
            'created_at',
        ]
        read_only_fields = ['id', 'granted_to', 'granted_by', 'organization', 'is_active', 'created_at']

    def validate_granted_to_email(self, value):
        try:
            return User.objects.get(email=value)
        except User.DoesNotExist:
            raise serializers.ValidationError(f"No user found with email '{value}'.")

    def validate_expires_at(self, value):
        if value and value <= timezone.now():
            raise serializers.ValidationError("expires_at must be a future datetime.")
        return value
    
    def validate(self, data):
        user_to_delegate = data.get('granted_to_email')
        org_id = self.context.get('org_id')

        if user_to_delegate and org_id:
            if not Membership.objects.filter(
                user=user_to_delegate,
                organization_id=org_id,
                is_verified=True
            ).exists():
                raise serializers.ValidationError({
                    'granted_to_email': (
                        "This user is not a verified member of this organization. "
                        "They must join the org before receiving a delegation."
                    )
                })

        return data

    def create(self, validated_data):
        # Pop the resolved User object from the email field
        user = validated_data.pop('granted_to_email')
        return Delegation.objects.create(granted_to=user, **validated_data)


class DelegationReadSerializer(serializers.ModelSerializer):
    """
    Used for listing and retrieving delegations.
    """
    granted_to_username = serializers.ReadOnlyField(source='granted_to.username')
    granted_to_email = serializers.ReadOnlyField(source='granted_to.email')
    granted_by_username = serializers.ReadOnlyField(source='granted_by.username')
    organization_name = serializers.ReadOnlyField(source='organization.name')
    is_currently_valid = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()

    class Meta:
        model = Delegation
        fields = [
            'id',
            'granted_to',
            'granted_to_username',
            'granted_to_email',
            'granted_by',
            'granted_by_username',
            'organization',
            'organization_name',
            'temp_role',
            'expires_at',
            'is_active',
            'is_currently_valid',
            'status',
            'reason',
            'created_at',
            'revoked_at',
        ]

    def get_is_currently_valid(self, obj):
        return obj.is_currently_valid

    def get_status(self, obj):
        """
        Human-readable status string for the frontend to display.
        One of: 'active' | 'expired' | 'revoked' | 'permanent'
        """
        if not obj.is_active:
            return 'revoked'
        if obj.expires_at and obj.expires_at <= timezone.now():
            return 'expired'
        if obj.expires_at is None:
            return 'permanent'
        return 'active'


class DelegationRevokeSerializer(serializers.ModelSerializer):
    """
    Used when an admin revokes a delegation.
    Only allows updating is_active — nothing else can be changed after creation.
    """
    class Meta:
        model = Delegation
        fields = ['is_active']

    def validate_is_active(self, value):
        if value is True:
            raise serializers.ValidationError(
                "You cannot re-activate a revoked delegation. Create a new one instead."
            )
        return value

    def update(self, instance, validated_data):
        instance.revoke()  # Uses the model's revoke() method to also set revoked_at
        return instance


class EffectiveRoleSerializer(serializers.Serializer):
    """
    Read-only serializer for the effective role endpoint.
    Returns a user's full access picture in a given org.
    """
    user_id = serializers.IntegerField()
    username = serializers.CharField()
    email = serializers.EmailField()
    org_id = serializers.UUIDField()
    org_name = serializers.CharField()

    # The resolved role — highest of membership + delegation
    effective_role = serializers.CharField(allow_null=True)

    # Breakdown of where the role came from
    membership_role = serializers.CharField(allow_null=True)
    delegation_role = serializers.CharField(allow_null=True)
    delegation_expires_at = serializers.DateTimeField(allow_null=True)
    is_superuser = serializers.BooleanField()