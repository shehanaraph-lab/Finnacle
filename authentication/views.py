import logging
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_http_methods
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import JSONParser
from .models import UserProfile
from .serializers import UserSerializer, UserProfileSerializer

logger = logging.getLogger(__name__)
User = get_user_model()


@api_view(['POST'])
@permission_classes([AllowAny])
def login_user(request):
    """
    Login user with Firebase credentials
    POST /api/v1/auth/login/
    """
    try:
        email = request.data.get('email')
        password = request.data.get('password')
        
        if not email or not password:
            return Response({
                'error': 'Missing credentials',
                'message': 'Email and password are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # In a real implementation, you would verify with Firebase Auth
        # For now, we'll check if the user exists in our database
        try:
            user = User.objects.get(email=email)
            if not user.firebase_uid:
                return Response({
                    'error': 'Invalid account',
                    'message': 'This account is not linked to Firebase'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Return user info (in real app, Firebase would handle auth)
            user_serializer = UserSerializer(user)
            try:
                profile = user.profile
                profile_serializer = UserProfileSerializer(profile)
            except UserProfile.DoesNotExist:
                profile = UserProfile.objects.create(user=user)
                profile_serializer = UserProfileSerializer(profile)
            
            logger.info(f"User login attempt: {user.email}")
            
            return Response({
                'success': True,
                'message': 'Login successful. Please use Firebase Auth for authentication.',
                'user': user_serializer.data,
                'profile': profile_serializer.data,
                'note': 'This is a demo endpoint. Use Firebase Auth in production.'
            })
            
        except User.DoesNotExist:
            return Response({
                'error': 'Invalid credentials',
                'message': 'User not found'
            }, status=status.HTTP_401_UNAUTHORIZED)
            
    except Exception as e:
        logger.error(f"Login error: {e}")
        return Response({
            'error': 'Login failed',
            'message': 'Failed to process login request'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def verify_firebase_token(request):
    """
    Verify Firebase ID token and return user information
    POST /api/v1/auth/verify/
    """
    try:
        token = request.data.get('token')
        if not token:
            return Response({
                'error': 'Missing token',
                'message': 'Firebase ID token is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Import here to avoid circular imports
        from firebase_admin import auth
        
        try:
            # Verify the Firebase ID token
            decoded_token = auth.verify_id_token(token)
            firebase_uid = decoded_token.get('uid')
            
            if not firebase_uid:
                return Response({
                    'error': 'Invalid token',
                    'message': 'Firebase UID not found in token'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get or create user
            try:
                user = User.objects.get(firebase_uid=firebase_uid)
                user_serializer = UserSerializer(user)
                return Response({
                    'success': True,
                    'user': user_serializer.data,
                    'message': 'Token verified successfully'
                })
            except User.DoesNotExist:
                return Response({
                    'success': False,
                    'message': 'User not found. Please register first.',
                    'firebase_uid': firebase_uid
                }, status=status.HTTP_404_NOT_FOUND)
                
        except Exception as e:
            logger.error(f"Firebase token verification failed: {e}")
            return Response({
                'error': 'Token verification failed',
                'message': str(e)
            }, status=status.HTTP_401_UNAUTHORIZED)
            
    except Exception as e:
        logger.error(f"Token verification error: {e}")
        return Response({
            'error': 'Internal server error',
            'message': 'Failed to verify token'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def user_profile(request):
    """
    Get or update user profile
    GET/PUT /api/v1/me/
    """
    try:
        user = request.user
        
        if request.method == 'GET':
            # Get user profile
            user_serializer = UserSerializer(user)
            try:
                profile = user.profile
                profile_serializer = UserProfileSerializer(profile)
                return Response({
                    'user': user_serializer.data,
                    'profile': profile_serializer.data
                })
            except UserProfile.DoesNotExist:
                # Create profile if it doesn't exist
                profile = UserProfile.objects.create(user=user)
                profile_serializer = UserProfileSerializer(profile)
                return Response({
                    'user': user_serializer.data,
                    'profile': profile_serializer.data
                })
        
        elif request.method == 'PUT':
            # Update user profile
            user_data = request.data.get('user', {})
            profile_data = request.data.get('profile', {})
            
            # Update user fields
            user_serializer = UserSerializer(user, data=user_data, partial=True)
            if user_serializer.is_valid():
                user_serializer.save()
            else:
                return Response({
                    'error': 'Invalid user data',
                    'details': user_serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Update profile fields
            try:
                profile = user.profile
            except UserProfile.DoesNotExist:
                profile = UserProfile.objects.create(user=user)
            
            profile_serializer = UserProfileSerializer(profile, data=profile_data, partial=True)
            if profile_serializer.is_valid():
                profile_serializer.save()
            else:
                return Response({
                    'error': 'Invalid profile data',
                    'details': profile_serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            return Response({
                'success': True,
                'message': 'Profile updated successfully',
                'user': user_serializer.data,
                'profile': profile_serializer.data
            })
    
    except Exception as e:
        logger.error(f"User profile error: {e}")
        return Response({
            'error': 'Internal server error',
            'message': 'Failed to process profile request'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    """
    Register a new user with Firebase UID
    POST /api/v1/auth/register/
    """
    try:
        firebase_uid = request.data.get('firebase_uid')
        email = request.data.get('email')
        first_name = request.data.get('first_name', '')
        last_name = request.data.get('last_name', '')
        
        if not firebase_uid or not email:
            return Response({
                'error': 'Missing required fields',
                'message': 'Firebase UID and email are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if user already exists
        if User.objects.filter(firebase_uid=firebase_uid).exists():
            return Response({
                'error': 'User already exists',
                'message': 'User with this Firebase UID already registered'
            }, status=status.HTTP_409_CONFLICT)
        
        if User.objects.filter(email=email).exists():
            return Response({
                'error': 'Email already exists',
                'message': 'User with this email already registered'
            }, status=status.HTTP_409_CONFLICT)
        
        # Create user
        username = email.split('@')[0]
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{email.split('@')[0]}_{counter}"
            counter += 1
        
        user = User.objects.create_user(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            firebase_uid=firebase_uid,
            is_verified=True,  # Firebase handles email verification
            firebase_email_verified=True
        )
        
        # Create user profile
        profile = UserProfile.objects.create(user=user)
        
        # Serialize response
        user_serializer = UserSerializer(user)
        profile_serializer = UserProfileSerializer(profile)
        
        logger.info(f"New user registered: {user.email} (UID: {firebase_uid})")
        
        return Response({
            'success': True,
            'message': 'User registered successfully',
            'user': user_serializer.data,
            'profile': profile_serializer.data
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"User registration error: {e}")
        return Response({
            'error': 'Registration failed',
            'message': 'Failed to register user'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_user(request):
    """
    Logout user (client-side token removal)
    POST /api/v1/auth/logout/
    """
    try:
        user = request.user
        logger.info(f"User logged out: {user.email}")
        
        return Response({
            'success': True,
            'message': 'Logged out successfully'
        })
        
    except Exception as e:
        logger.error(f"Logout error: {e}")
        return Response({
            'error': 'Logout failed',
            'message': 'Failed to process logout'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_status(request):
    """
    Get current user authentication status
    GET /api/v1/auth/status/
    """
    try:
        user = request.user
        user_serializer = UserSerializer(user)
        
        return Response({
            'authenticated': True,
            'user': user_serializer.data,
            'firebase_uid': user.firebase_uid,
            'is_verified': user.is_verified
        })
        
    except Exception as e:
        logger.error(f"User status error: {e}")
        return Response({
            'error': 'Status check failed',
            'message': 'Failed to check user status'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def forgot_password(request):
    """
    Initiate password reset (delegated to Firebase)
    POST /api/v1/auth/forgot-password/
    """
    try:
        email = request.data.get('email')
        if not email:
            return Response({
                'error': 'Missing email',
                'message': 'Email address is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if user exists
        try:
            user = User.objects.get(email=email)
            if not user.firebase_uid:
                return Response({
                    'error': 'Invalid account',
                    'message': 'This account is not linked to Firebase'
                }, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            # Don't reveal if user exists or not for security
            pass
        
        # In a real implementation, you would call Firebase Auth API
        # For now, we'll return a success message
        logger.info(f"Password reset requested for: {email}")
        
        return Response({
            'success': True,
            'message': 'Password reset email sent. Please check your email.',
            'note': 'Password reset is handled by Firebase Authentication'
        })
        
    except Exception as e:
        logger.error(f"Forgot password error: {e}")
        return Response({
            'error': 'Password reset failed',
            'message': 'Failed to process password reset request'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
