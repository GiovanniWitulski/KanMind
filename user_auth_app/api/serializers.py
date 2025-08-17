from rest_framework import serializers
from ..models import UserProfile
from django.contrib.auth.models import User


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['user', 'fullname']


class UserDetailSerializer(serializers.ModelSerializer):
    fullname = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'email', 'fullname']
    
    def get_fullname(self, obj):
        try:
            return obj.userprofile.fullname
        except UserProfile.DoesNotExist:
            return f"{obj.first_name} {obj.last_name}".strip()


class RegistrationSerializer(serializers.ModelSerializer):
    repeated_password = serializers.CharField(style={'input_type': 'password'}, write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'repeated_password']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def validate(self, data):
        if data['password'] != data['repeated_password']:
            raise serializers.ValidationError({'error': 'Passwords do not match.'})

        if User.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError({'error': 'A user with this email already exists.'})
        
        return data

    def create(self, validated_data):
        validated_data.pop('repeated_password')
        account = User.objects.create_user(**validated_data)
        
        return account