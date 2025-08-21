from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from unittest.mock import patch, MagicMock
from .models import UserProfile

User = get_user_model()


class AuthenticationModelsTest(TestCase):
    """
    Test cases for authentication models
    """
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            firebase_uid='test_firebase_uid_123'
        )
        self.profile = UserProfile.objects.create(user=self.user)
    
    def test_user_creation(self):
        """Test user creation with Firebase UID"""
        self.assertEqual(self.user.username, 'testuser')
        self.assertEqual(self.user.email, 'test@example.com')
        self.assertEqual(self.user.firebase_uid, 'test_firebase_uid_123')
        self.assertFalse(self.user.is_verified)
        self.assertFalse(self.user.firebase_email_verified)
    
    def test_user_full_name(self):
        """Test user full name property"""
        self.user.first_name = 'John'
        self.user.last_name = 'Doe'
        self.user.save()
        
        self.assertEqual(self.user.full_name, 'John Doe')
        self.assertEqual(self.user.get_display_name(), 'John Doe')
    
    def test_user_display_name_fallback(self):
        """Test user display name fallback to username"""
        self.user.first_name = ''
        self.user.last_name = ''
        self.user.save()
        
        self.assertEqual(self.user.get_display_name(), 'testuser')
    
    def test_user_profile_creation(self):
        """Test user profile creation"""
        self.assertEqual(self.profile.user, self.user)
        self.assertEqual(self.profile.language, 'en')
        self.assertEqual(self.profile.timezone, 'UTC')
        self.assertTrue(self.profile.email_notifications)
        self.assertTrue(self.profile.push_notifications)
        self.assertFalse(self.profile.sms_notifications)
    
    def test_user_profile_full_address(self):
        """Test user profile full address method"""
        self.profile.address_line1 = '123 Main St'
        self.profile.city = 'New York'
        self.profile.state = 'NY'
        self.profile.postal_code = '10001'
        self.profile.country = 'USA'
        self.profile.save()
        
        expected_address = '123 Main St, New York, NY, 10001, USA'
        self.assertEqual(self.profile.get_full_address(), expected_address)
    
    def test_user_profile_no_address(self):
        """Test user profile with no address"""
        self.assertEqual(self.profile.get_full_address(), 'No address provided')


class AuthenticationViewsTest(APITestCase):
    """
    Test cases for authentication views
    """
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            firebase_uid='test_firebase_uid_123'
        )
        self.profile = UserProfile.objects.create(user=self.user)
        
        # Mock Firebase token data
        self.mock_firebase_token = {
            'uid': 'test_firebase_uid_123',
            'email': 'test@example.com',
            'email_verified': True,
            'name': 'Test User'
        }
    
    @patch('firebase_admin.auth.verify_id_token')
    def test_verify_firebase_token_success(self, mock_verify):
        """Test successful Firebase token verification"""
        mock_verify.return_value = self.mock_firebase_token
        
        url = reverse('authentication:verify_token')
        data = {'token': 'valid_firebase_token'}
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['user']['email'], 'test@example.com')
    
    @patch('firebase_admin.auth.verify_id_token')
    def test_verify_firebase_token_user_not_found(self, mock_verify):
        """Test Firebase token verification for non-existent user"""
        mock_verify.return_value = {
            'uid': 'new_firebase_uid_456',
            'email': 'new@example.com',
            'email_verified': True
        }
        
        url = reverse('authentication:verify_token')
        data = {'token': 'valid_firebase_token'}
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.data['success'])
        self.assertEqual(response.data['firebase_uid'], 'new_firebase_uid_456')
    
    def test_verify_firebase_token_missing_token(self):
        """Test Firebase token verification with missing token"""
        url = reverse('authentication:verify_token')
        data = {}
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'Missing token')
    
    def test_user_profile_get(self):
        """Test getting user profile"""
        self.client.force_authenticate(user=self.user)
        url = reverse('authentication:user_profile')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user']['email'], 'test@example.com')
        self.assertEqual(response.data['profile']['language'], 'en')
    
    def test_user_profile_update(self):
        """Test updating user profile"""
        self.client.force_authenticate(user=self.user)
        url = reverse('authentication:user_profile')
        
        data = {
            'user': {
                'first_name': 'Updated',
                'last_name': 'Name'
            },
            'profile': {
                'bio': 'Updated bio',
                'language': 'es'
            }
        }
        
        response = self.client.put(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        # Refresh from database
        self.user.refresh_from_db()
        self.profile.refresh_from_db()
        
        self.assertEqual(self.user.first_name, 'Updated')
        self.assertEqual(self.user.last_name, 'Name')
        self.assertEqual(self.profile.bio, 'Updated bio')
        self.assertEqual(self.profile.language, 'es')
    
    def test_user_profile_unauthorized(self):
        """Test user profile access without authentication"""
        url = reverse('authentication:user_profile')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_register_user_success(self):
        """Test successful user registration"""
        url = reverse('authentication:register')
        data = {
            'firebase_uid': 'new_firebase_uid_789',
            'email': 'newuser@example.com',
            'first_name': 'New',
            'last_name': 'User'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        
        # Check if user was created
        new_user = User.objects.get(firebase_uid='new_firebase_uid_789')
        self.assertEqual(new_user.email, 'newuser@example.com')
        self.assertEqual(new_user.first_name, 'New')
        self.assertEqual(new_user.last_name, 'User')
        self.assertTrue(new_user.is_verified)
    
    def test_register_user_duplicate_firebase_uid(self):
        """Test user registration with duplicate Firebase UID"""
        url = reverse('authentication:register')
        data = {
            'firebase_uid': 'test_firebase_uid_123',  # Already exists
            'email': 'another@example.com',
            'first_name': 'Another',
            'last_name': 'User'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(response.data['error'], 'User already exists')
    
    def test_register_user_duplicate_email(self):
        """Test user registration with duplicate email"""
        url = reverse('authentication:register')
        data = {
            'firebase_uid': 'new_firebase_uid_789',
            'email': 'test@example.com',  # Already exists
            'first_name': 'Another',
            'last_name': 'User'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(response.data['error'], 'Email already exists')
    
    def test_logout_user(self):
        """Test user logout"""
        self.client.force_authenticate(user=self.user)
        url = reverse('authentication:logout')
        
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
    
    def test_user_status(self):
        """Test getting user authentication status"""
        self.client.force_authenticate(user=self.user)
        url = reverse('authentication:user_status')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['authenticated'])
        self.assertEqual(response.data['firebase_uid'], 'test_firebase_uid_123')
        self.assertFalse(response.data['is_verified'])
    
    def test_forgot_password(self):
        """Test forgot password functionality"""
        url = reverse('authentication:forgot_password')
        data = {'email': 'test@example.com'}
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('Password reset email sent', response.data['message'])
    
    def test_forgot_password_missing_email(self):
        """Test forgot password with missing email"""
        url = reverse('authentication:forgot_password')
        data = {}
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'Missing email')


class AuthenticationSerializersTest(TestCase):
    """
    Test cases for authentication serializers
    """
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            firebase_uid='test_firebase_uid_123'
        )
        self.profile = UserProfile.objects.create(user=self.user)
    
    def test_user_serializer(self):
        """Test UserSerializer"""
        from .serializers import UserSerializer
        
        serializer = UserSerializer(self.user)
        data = serializer.data
        
        self.assertEqual(data['username'], 'testuser')
        self.assertEqual(data['email'], 'test@example.com')
        self.assertEqual(data['firebase_uid'], 'test_firebase_uid_123')
        self.assertEqual(data['full_name'], '')
        self.assertEqual(data['display_name'], 'testuser')
    
    def test_user_profile_serializer(self):
        """Test UserProfileSerializer"""
        from .serializers import UserProfileSerializer
        
        serializer = UserProfileSerializer(self.profile)
        data = serializer.data
        
        self.assertEqual(data['language'], 'en')
        self.assertEqual(data['timezone'], 'UTC')
        self.assertTrue(data['email_notifications'])
        self.assertTrue(data['push_notifications'])
        self.assertFalse(data['sms_notifications'])
    
    def test_user_registration_serializer(self):
        """Test UserRegistrationSerializer"""
        from .serializers import UserRegistrationSerializer
        
        data = {
            'firebase_uid': 'new_firebase_uid_789',
            'email': 'newuser@example.com',
            'first_name': 'New',
            'last_name': 'User'
        }
        
        serializer = UserRegistrationSerializer(data=data)
        self.assertTrue(serializer.is_valid())
    
    def test_user_registration_serializer_duplicate_firebase_uid(self):
        """Test UserRegistrationSerializer with duplicate Firebase UID"""
        from .serializers import UserRegistrationSerializer
        
        data = {
            'firebase_uid': 'test_firebase_uid_123',  # Already exists
            'email': 'newuser@example.com',
            'first_name': 'New',
            'last_name': 'User'
        }
        
        serializer = UserRegistrationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('firebase_uid', serializer.errors)
    
    def test_firebase_token_verification_serializer(self):
        """Test FirebaseTokenVerificationSerializer"""
        from .serializers import FirebaseTokenVerificationSerializer
        
        data = {'token': 'valid_firebase_token'}
        serializer = FirebaseTokenVerificationSerializer(data=data)
        self.assertTrue(serializer.is_valid())
    
    def test_firebase_token_verification_serializer_empty_token(self):
        """Test FirebaseTokenVerificationSerializer with empty token"""
        from .serializers import FirebaseTokenVerificationSerializer
        
        data = {'token': ''}
        serializer = FirebaseTokenVerificationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('token', serializer.errors)


class AuthenticationIntegrationTest(APITestCase):
    """
    Integration tests for authentication system
    """
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
    
    @patch('firebase_admin.auth.verify_id_token')
    def test_full_authentication_flow(self, mock_verify):
        """Test complete authentication flow"""
        # Mock Firebase token verification
        mock_verify.return_value = {
            'uid': 'integration_test_uid_123',
            'email': 'integration@example.com',
            'email_verified': True,
            'name': 'Integration Test User'
        }
        
        # 1. Register new user
        register_url = reverse('authentication:register')
        register_data = {
            'firebase_uid': 'integration_test_uid_123',
            'email': 'integration@example.com',
            'first_name': 'Integration',
            'last_name': 'Test'
        }
        
        register_response = self.client.post(register_url, register_data, format='json')
        self.assertEqual(register_response.status_code, status.HTTP_201_CREATED)
        
        # 2. Verify token
        verify_url = reverse('authentication:verify_token')
        verify_data = {'token': 'valid_firebase_token'}
        
        verify_response = self.client.post(verify_url, verify_data, format='json')
        self.assertEqual(verify_response.status_code, status.HTTP_200_OK)
        
        # 3. Get user profile (requires authentication)
        user = User.objects.get(firebase_uid='integration_test_uid_123')
        self.client.force_authenticate(user=user)
        
        profile_url = reverse('authentication:user_profile')
        profile_response = self.client.get(profile_url)
        self.assertEqual(profile_response.status_code, status.HTTP_200_OK)
        
        # 4. Update profile
        update_data = {
            'user': {'first_name': 'Updated Integration'},
            'profile': {'bio': 'Integration test bio'}
        }
        
        update_response = self.client.put(profile_url, update_data, format='json')
        self.assertEqual(update_response.status_code, status.HTTP_200_OK)
        
        # 5. Check user status
        status_url = reverse('authentication:user_status')
        status_response = self.client.get(status_url)
        self.assertEqual(status_response.status_code, status.HTTP_200_OK)
        self.assertTrue(status_response.data['authenticated'])
        
        # 6. Logout
        logout_url = reverse('authentication:logout')
        logout_response = self.client.post(logout_url)
        self.assertEqual(logout_response.status_code, status.HTTP_200_OK)
