from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import User, EmailVerificationToken
import re

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    avatar = serializers.URLField(required=False, allow_null=True)
    
    class Meta:
        model = User
        fields = ('id', 'name', 'email', 'password', 'password_confirm', 'phone', 'role', 'avatar')
        extra_kwargs = {
            'role': {'read_only': True}
        }
    
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value
    
    def validate_phone(self, value):
        if value and not re.match(r'^\+?1?\d{9,15}$', value):
            raise serializers.ValidationError("Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")
        return value
    
    def validate(self, attrs):
        if attrs['password'] != attrs.pop('password_confirm'):
            raise serializers.ValidationError({"password_confirm": "Password fields didn't match."})
        return attrs
    
    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data['email'],
            name=validated_data['name'],
            password=validated_data['password'],
            phone=validated_data.get('phone'),
            avatar=validated_data.get('avatar')
        )
        return user

# For safe user data exposure(no passwords), read_only_fields - Prevents users from modifying these via API
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'name', 'email', 'phone', 'role', 'is_verified', 'avatar', 'created_at', 'updated_at')
        read_only_fields = ('id', 'is_verified', 'created_at', 'updated_at')

# For email verification endpoint
class EmailVerificationSerializer(serializers.Serializer):
    token = serializers.UUIDField()