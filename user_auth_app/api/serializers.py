from django.contrib.auth import authenticate, get_user_model
from rest_framework import serializers
from ..models import UserProfile
from django.contrib.auth.models import User
User = get_user_model()

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
    fullname = serializers.CharField(write_only=True)
    repeated_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['fullname', 'email', 'password', 'repeated_password']
        extra_kwargs = {
            'password': {'write_only': True},
            'email': {'required': True} 
        }

    def validate(self, data):
        if 'email' not in data or not data['email']:
            raise serializers.ValidationError({'error': 'Email field is required.'})

        if data['password'] != data['repeated_password']:
            raise serializers.ValidationError({'error': 'Passwords do not match.'})

        if User.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError({'error': 'A user with this email already exists.'})
        
        return data

    def create(self, validated_data):
        account = User.objects.create_user(
            email=validated_data['email'],
            username=validated_data['email'],
            password=validated_data['password']
        )

        fullname = validated_data.get('fullname', '').split()
        account.first_name = fullname[0] if fullname else ''
        account.last_name = ' '.join(fullname[1:]) if len(fullname) > 1 else ''
        account.save()
        
        UserProfile.objects.create(
            user=account,
            fullname=validated_data.get('fullname', '')
        )
        
        return account


class CustomAuthTokenSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(trim_whitespace=False)

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            user = authenticate(request=self.context.get('request'),
                                username=email, password=password)

            if not user:
                raise serializers.ValidationError(code='authorization')
        else:
            raise serializers.ValidationError(code='authorization')

        attrs['user'] = user
        return attrs
