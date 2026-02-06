from rest_framework import serializers
from users.models import Membership, Organization, User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'bio')

class ProfileSerializer(serializers.ModelSerializer):
    profile_picture = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 
                 'profile_picture', 'bio', 'avatar', 'date_joined')
        read_only_fields = ('id', 'date_joined')
    
    def get_roles(self, obj):
        return [
            {"org": member.organization.name, "role": member.role} 
            for member in obj.memberships.all()
        ]
    
    def get_profile_picture(self, obj):
        if obj.profile_picture:
            return obj.profile_picture.url
        return None
    
    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('username', 'password', 'email')

    def create(self, validated_data):
        # use create_user to handle password hashing automatically
        user = User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password'],
            email=validated_data.get('email', ''),
        )
        return user

class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ['name', 'id']
        read_only_fields = ['id']
    def create(self, validated_data):
        user = self.context['request'].user
        # 1. Create the Organization
        org = Organization.objects.create(creator=user, **validated_data)
        
        # 2. Automatically make the creator the ADMIN
        Membership.objects.create(user=user, organization=org, role='admin')
        return org
    class Meta:
        ordering = ['-id']