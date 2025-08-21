"""
Tests for Django settings configuration
"""
import pytest
from django.conf import settings
from django.test import TestCase, override_settings


class SettingsTestCase(TestCase):
    """Test Django settings configuration"""
    
    def test_debug_setting(self):
        """Test DEBUG setting is properly configured"""
        # In tests, DEBUG should be True by default
        self.assertTrue(settings.DEBUG)
    
    def test_secret_key_exists(self):
        """Test that SECRET_KEY is configured"""
        self.assertTrue(settings.SECRET_KEY)
        self.assertNotEqual(settings.SECRET_KEY, '')
    
    def test_allowed_hosts_configured(self):
        """Test ALLOWED_HOSTS is configured"""
        self.assertIsInstance(settings.ALLOWED_HOSTS, list)
    
    def test_installed_apps_includes_required(self):
        """Test that required apps are in INSTALLED_APPS"""
        required_apps = [
            'django.contrib.admin',
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'django.contrib.sessions',
            'django.contrib.messages',
            'django.contrib.staticfiles',
            'rest_framework',
            'corsheaders',
            'core',
        ]
        
        for app in required_apps:
            self.assertIn(app, settings.INSTALLED_APPS)
    
    def test_middleware_includes_required(self):
        """Test that required middleware is configured"""
        required_middleware = [
            'corsheaders.middleware.CorsMiddleware',
            'django.middleware.security.SecurityMiddleware',
            'django.contrib.sessions.middleware.SessionMiddleware',
            'django.middleware.common.CommonMiddleware',
            'django.middleware.csrf.CsrfViewMiddleware',
            'django.contrib.auth.middleware.AuthenticationMiddleware',
            'django.contrib.messages.middleware.MessageMiddleware',
            'django.middleware.clickjacking.XFrameOptionsMiddleware',
        ]
        
        for middleware in required_middleware:
            self.assertIn(middleware, settings.MIDDLEWARE)
    
    def test_database_configured(self):
        """Test database configuration"""
        self.assertIn('default', settings.DATABASES)
        db_config = settings.DATABASES['default']
        self.assertIn('ENGINE', db_config)
        self.assertIn('NAME', db_config)
    
    def test_rest_framework_configured(self):
        """Test REST Framework configuration"""
        self.assertTrue(hasattr(settings, 'REST_FRAMEWORK'))
        rf_config = settings.REST_FRAMEWORK
        
        required_settings = [
            'DEFAULT_AUTHENTICATION_CLASSES',
            'DEFAULT_PERMISSION_CLASSES',
            'DEFAULT_PAGINATION_CLASS',
            'PAGE_SIZE',
        ]
        
        for setting in required_settings:
            self.assertIn(setting, rf_config)
    
    def test_cors_configuration(self):
        """Test CORS configuration"""
        self.assertTrue(hasattr(settings, 'CORS_ALLOWED_ORIGINS'))
        self.assertTrue(hasattr(settings, 'CORS_ALLOW_CREDENTIALS'))
    
    def test_logging_configured(self):
        """Test logging configuration"""
        self.assertTrue(hasattr(settings, 'LOGGING'))
        logging_config = settings.LOGGING
        
        self.assertIn('version', logging_config)
        self.assertIn('handlers', logging_config)
        self.assertIn('loggers', logging_config)
        self.assertIn('formatters', logging_config)


@pytest.mark.django_db
class TestSettingsIntegration:
    """Integration tests for settings"""
    
    def test_database_connection(self):
        """Test that database connection works"""
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            assert result == (1,)
    
    def test_cache_configuration(self):
        """Test cache configuration"""
        from django.core.cache import cache
        
        # Test basic cache operations
        cache.set('test_key', 'test_value', 30)
        assert cache.get('test_key') == 'test_value'
        cache.delete('test_key')
        assert cache.get('test_key') is None


@override_settings(DEBUG=False)
class ProductionSettingsTestCase(TestCase):
    """Test production-specific settings"""
    
    def test_security_settings_in_production(self):
        """Test that security settings are enabled in production"""
        with override_settings(DEBUG=False):
            # These settings should be True in production
            security_settings = [
                'SECURE_BROWSER_XSS_FILTER',
                'SECURE_CONTENT_TYPE_NOSNIFF',
                'SECURE_HSTS_INCLUDE_SUBDOMAINS',
                'SECURE_SSL_REDIRECT',
                'SESSION_COOKIE_SECURE',
                'CSRF_COOKIE_SECURE',
            ]
            
            for setting_name in security_settings:
                if hasattr(settings, setting_name):
                    self.assertTrue(getattr(settings, setting_name), 
                                  f"{setting_name} should be True in production")



