import logging
import firebase_admin
from firebase_admin import auth, credentials
from django.http import JsonResponse
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.deprecation import MiddlewareMixin
from rest_framework import status
from rest_framework.response import Response

logger = logging.getLogger(__name__)
User = get_user_model()


class FirebaseAuthenticationMiddleware(MiddlewareMixin):
    """
    Middleware to authenticate users using Firebase ID tokens
    """
    
    def __init__(self, get_response=None):
        super().__init__(get_response)
        # Initialize Firebase Admin SDK if not already initialized
        try:
            if not firebase_admin._apps:
                # You can configure this with environment variables
                firebase_config = getattr(settings, 'FIREBASE_CONFIG', {})
                if firebase_config.get('type') == 'service_account':
                    cred = credentials.Certificate(firebase_config)
                    firebase_admin.initialize_app(cred)
                else:
                    # Use default credentials (GOOGLE_APPLICATION_CREDENTIALS env var)
                    firebase_admin.initialize_app()
                logger.info("Firebase Admin SDK initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Firebase Admin SDK: {e}")
    
    def process_request(self, request):
        """
        Process the request and authenticate the user if a Firebase token is provided
        """
        # Skip authentication for certain paths
        if self._should_skip_auth(request.path):
            return None
        
        # Get the Firebase ID token from the Authorization header
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if not auth_header.startswith('Bearer '):
            return self._unauthorized_response('Missing or invalid Authorization header')
        
        token = auth_header.split('Bearer ')[1]
        if not token:
            return self._unauthorized_response('Missing Firebase ID token')
        
        try:
            # Verify the Firebase ID token
            decoded_token = auth.verify_id_token(token)
            
            # Get or create the user based on Firebase UID
            user = self._get_or_create_user(decoded_token)
            
            # Set the user on the request
            request.user = user
            request.firebase_user = decoded_token
            
            logger.info(f"User authenticated: {user.email} (UID: {decoded_token.get('uid')})")
            return None
            
        except auth.ExpiredIdTokenError:
            logger.warning("Expired Firebase ID token")
            return self._unauthorized_response('Token expired')
        except auth.RevokedIdTokenError:
            logger.warning("Revoked Firebase ID token")
            return self._unauthorized_response('Token revoked')
        except auth.InvalidIdTokenError:
            logger.warning("Invalid Firebase ID token")
            return self._unauthorized_response('Invalid token')
        except Exception as e:
            logger.error(f"Firebase authentication error: {e}")
            return self._unauthorized_response('Authentication failed')
    
    def _should_skip_auth(self, path):
        """
        Check if authentication should be skipped for this path
        """
        skip_paths = [
            '/api/v1/health/',
            '/api/v1/ready/',
            '/api/v1/alive/',
            '/admin/',
            '/',
            '/api/v1/auth/login/',
            '/api/v1/auth/register/',
            '/api/v1/auth/verify/',
        ]
        
        return any(path.startswith(skip_path) for skip_path in skip_paths)
    
    def _get_or_create_user(self, decoded_token):
        """
        Get or create a user based on Firebase token information
        """
        firebase_uid = decoded_token.get('uid')
        email = decoded_token.get('email')
        name = decoded_token.get('name', '')
        picture = decoded_token.get('picture', '')
        
        if not firebase_uid:
            raise ValueError("Firebase UID not found in token")
        
        # Try to find existing user by Firebase UID
        try:
            user = User.objects.get(firebase_uid=firebase_uid)
            # Update user information from Firebase
            self._update_user_from_firebase(user, decoded_token)
            return user
        except User.DoesNotExist:
            # Create new user
            return self._create_user_from_firebase(decoded_token)
    
    def _create_user_from_firebase(self, decoded_token):
        """
        Create a new user from Firebase token information
        """
        firebase_uid = decoded_token.get('uid')
        email = decoded_token.get('email')
        name = decoded_token.get('name', '')
        picture = decoded_token.get('picture', '')
        
        # Generate username from email or name
        username = self._generate_username(email, name)
        
        # Create the user
        user = User.objects.create_user(
            username=username,
            email=email,
            firebase_uid=firebase_uid,
            first_name=name.split()[0] if name and ' ' in name else '',
            last_name=' '.join(name.split()[1:]) if name and ' ' in name else '',
            is_verified=decoded_token.get('email_verified', False),
            firebase_email_verified=decoded_token.get('email_verified', False),
        )
        
        # Create user profile
        from .models import UserProfile
        profile = UserProfile.objects.create(user=user)
        
        logger.info(f"Created new user: {user.email} (UID: {firebase_uid})")
        return user
    
    def _update_user_from_firebase(self, user, decoded_token):
        """
        Update existing user information from Firebase token
        """
        # Update verification status
        if decoded_token.get('email_verified'):
            user.is_verified = True
            user.firebase_email_verified = True
        
        # Update phone verification if available
        if 'phone_number' in decoded_token:
            user.phone_number = decoded_token.get('phone_number')
            user.firebase_phone_verified = decoded_token.get('phone_number_verified', False)
        
        # Update name if available and different
        name = decoded_token.get('name', '')
        if name:
            name_parts = name.split()
            if len(name_parts) >= 2:
                if user.first_name != name_parts[0] or user.last_name != ' '.join(name_parts[1:]):
                    user.first_name = name_parts[0]
                    user.last_name = ' '.join(name_parts[1:])
        
        user.save()
        return user
    
    def _generate_username(self, email, name):
        """
        Generate a unique username from email or name
        """
        if email:
            base_username = email.split('@')[0]
        elif name:
            base_username = name.lower().replace(' ', '_')
        else:
            base_username = 'user'
        
        # Ensure username uniqueness
        username = base_username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}_{counter}"
            counter += 1
        
        return username
    
    def _unauthorized_response(self, message):
        """
        Return an unauthorized response
        """
        return JsonResponse({
            'error': 'Authentication failed',
            'message': message,
            'code': 'UNAUTHORIZED'
        }, status=status.HTTP_401_UNAUTHORIZED)


class FirebaseAuthRequiredMiddleware(MiddlewareMixin):
    """
    Middleware to ensure Firebase authentication is required for protected endpoints
    """
    
    def process_request(self, request):
        """
        Check if the user is authenticated via Firebase
        """
        # Skip for non-API paths and public endpoints
        if not request.path.startswith('/api/v1/') or self._is_public_endpoint(request.path):
            return None
        
        # Check if user is authenticated
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            return JsonResponse({
                'error': 'Authentication required',
                'message': 'Firebase ID token required for this endpoint',
                'code': 'AUTHENTICATION_REQUIRED'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Check if user has Firebase UID
        if not hasattr(request.user, 'firebase_uid') or not request.user.firebase_uid:
            return JsonResponse({
                'error': 'Invalid user account',
                'message': 'User account not properly linked to Firebase',
                'code': 'INVALID_USER_ACCOUNT'
            }, status=status.HTTP_403_FORBIDDEN)
        
        return None
    
    def _is_public_endpoint(self, path):
        """
        Check if the endpoint is public (doesn't require authentication)
        """
        public_paths = [
            '/api/v1/health/',
            '/api/v1/ready/',
            '/api/v1/alive/',
            '/api/v1/auth/login/',
            '/api/v1/auth/register/',
            '/api/v1/auth/verify/',
        ]
        
        return any(path.startswith(public_path) for public_path in public_paths)


