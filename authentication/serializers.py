from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import UserProfile

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for User model
    """
    full_name = serializers.ReadOnlyField()
    display_name = serializers.ReadOnlyField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'full_name',
            'display_name', 'firebase_uid', 'phone_number', 'date_of_birth',
            'currency_preference', 'is_verified', 'firebase_email_verified',
            'firebase_phone_verified', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'username', 'firebase_uid', 'created_at', 'updated_at',
            'is_verified', 'firebase_email_verified', 'firebase_phone_verified'
        ]
    
    def validate_email(self, value):
        """
        Validate email uniqueness
        """
        if User.objects.filter(email=value).exclude(pk=self.instance.pk if self.instance else None).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value
    
    def validate_phone_number(self, value):
        """
        Validate phone number format
        """
        if value and not value.replace('+', '').replace('-', '').replace(' ', '').replace('(', '').replace(')', '').isdigit():
            raise serializers.ValidationError("Please enter a valid phone number.")
        return value


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for UserProfile model
    """
    full_address = serializers.ReadOnlyField()
    
    class Meta:
        model = UserProfile
        fields = [
            'id', 'avatar', 'bio', 'address_line1', 'address_line2', 'city',
            'state', 'postal_code', 'country', 'full_address', 'language',
            'timezone', 'email_notifications', 'push_notifications',
            'sms_notifications', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_postal_code(self, value):
        """
        Validate postal code format
        """
        if value and len(value) < 3:
            raise serializers.ValidationError("Postal code must be at least 3 characters long.")
        return value


class UserRegistrationSerializer(serializers.Serializer):
    """
    Serializer for user registration
    """
    firebase_uid = serializers.CharField(max_length=128)
    email = serializers.EmailField()
    first_name = serializers.CharField(max_length=30, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=30, required=False, allow_blank=True)
    
    def validate_firebase_uid(self, value):
        """
        Validate Firebase UID uniqueness
        """
        if User.objects.filter(firebase_uid=value).exists():
            raise serializers.ValidationError("A user with this Firebase UID already exists.")
        return value
    
    def validate_email(self, value):
        """
        Validate email uniqueness
        """
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value


class FirebaseTokenVerificationSerializer(serializers.Serializer):
    """
    Serializer for Firebase token verification
    """
    token = serializers.CharField()
    
    def validate_token(self, value):
        """
        Validate token is not empty
        """
        if not value or not value.strip():
            raise serializers.ValidationError("Token cannot be empty.")
        return value.strip()


class PasswordResetSerializer(serializers.Serializer):
    """
    Serializer for password reset request
    """
    email = serializers.EmailField()
    
    def validate_email(self, value):
        """
        Validate email format
        """
        if not value or not value.strip():
            raise serializers.ValidationError("Email cannot be empty.")
        return value.strip().lower()


class UserProfileUpdateSerializer(serializers.Serializer):
    """
    Serializer for updating user profile
    """
    user = UserSerializer(required=False)
    profile = UserProfileSerializer(required=False)
    
    def validate(self, data):
        """
        Validate that at least one field is provided
        """
        if not data.get('user') and not data.get('profile'):
            raise serializers.ValidationError("At least one field must be provided for update.")
        return data


class AuthResponseSerializer(serializers.Serializer):
    """
    Serializer for authentication responses
    """
    success = serializers.BooleanField()
    message = serializers.CharField()
    user = UserSerializer(required=False)
    profile = UserProfileSerializer(required=False)
    firebase_uid = serializers.CharField(required=False)
    token = serializers.CharField(required=False)
    error = serializers.CharField(required=False)
    code = serializers.CharField(required=False)


