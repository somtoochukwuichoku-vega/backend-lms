from rest_framework import serializers

from users.models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'is_student', 'bio')

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('username', 'password', 'email', 'is_student')

    def create(self, validated_data):
        # use create_user to handle password hashing automatically
        user = User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password'],
            email=validated_data.get('email', ''),
            is_student=validated_data.get('is_student', True)
        )
        return user