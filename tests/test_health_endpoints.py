"""
Smoke tests for health check endpoints
"""
import pytest
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient


class HealthEndpointsTestCase(TestCase):
    """Test health check endpoints"""
    
    def setUp(self):
        self.client = APIClient()
    
    def test_health_check_endpoint(self):
        """Test basic health check endpoint"""
        url = reverse('core:health_check')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('status', response.data)
        self.assertEqual(response.data['status'], 'healthy')
        self.assertIn('timestamp', response.data)
        self.assertIn('version', response.data)
        self.assertIn('environment', response.data)
    
    def test_liveness_check_endpoint(self):
        """Test liveness check endpoint"""
        url = reverse('core:liveness_check')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('status', response.data)
        self.assertEqual(response.data['status'], 'alive')
        self.assertIn('timestamp', response.data)
        self.assertIn('uptime', response.data)
    
    def test_readiness_check_endpoint(self):
        """Test readiness check endpoint"""
        url = reverse('core:readiness_check')
        response = self.client.get(url)
        
        # Should return 200 or 503 depending on dependencies
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_503_SERVICE_UNAVAILABLE])
        self.assertIn('status', response.data)
        self.assertIn('checks', response.data)
        self.assertIn('timestamp', response.data)
        
        # Check that database and cache checks are present
        checks = response.data['checks']
        self.assertIn('database', checks)
        self.assertIn('cache', checks)
        
        # Each check should have a status
        for check_name, check_data in checks.items():
            self.assertIn('status', check_data)
            self.assertIn(check_data['status'], ['healthy', 'unhealthy'])


@pytest.mark.django_db
class TestHealthEndpointsIntegration:
    """Integration tests for health endpoints"""
    
    def test_health_endpoint_without_auth(self):
        """Test that health endpoints don't require authentication"""
        client = APIClient()
        
        # Test all health endpoints
        endpoints = [
            'core:health_check',
            'core:liveness_check', 
            'core:readiness_check'
        ]
        
        for endpoint_name in endpoints:
            url = reverse(endpoint_name)
            response = client.get(url)
            
            # Should not return 401 or 403 (authentication/permission errors)
            assert response.status_code not in [401, 403], f"Endpoint {endpoint_name} requires auth"
    
    def test_health_endpoints_return_json(self):
        """Test that all health endpoints return JSON"""
        client = APIClient()
        
        endpoints = [
            'core:health_check',
            'core:liveness_check',
            'core:readiness_check'
        ]
        
        for endpoint_name in endpoints:
            url = reverse(endpoint_name)
            response = client.get(url)
            
            assert response.headers['content-type'] == 'application/json'
            assert isinstance(response.data, dict)



