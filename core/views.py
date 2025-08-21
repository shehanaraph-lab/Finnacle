import logging
import time
from django.http import JsonResponse
from django.db import connection
from django.conf import settings
from django.core.cache import cache
from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    Basic health check endpoint that returns 200 OK if the service is running.
    """
    return Response({
        'status': 'healthy',
        'timestamp': time.time(),
        'version': '1.0.0',
        'environment': getattr(settings, 'ENVIRONMENT', 'development')
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def readiness_check(request):
    """
    Readiness check that verifies all dependencies are working correctly.
    """
    checks = {}
    overall_status = 'ready'
    
    # Database check
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        checks['database'] = {'status': 'healthy', 'response_time_ms': 0}
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        checks['database'] = {'status': 'unhealthy', 'error': str(e)}
        overall_status = 'not_ready'
    
    # Cache check
    try:
        cache_key = 'health_check_test'
        cache.set(cache_key, 'test_value', 30)
        cached_value = cache.get(cache_key)
        if cached_value == 'test_value':
            checks['cache'] = {'status': 'healthy'}
            cache.delete(cache_key)
        else:
            checks['cache'] = {'status': 'unhealthy', 'error': 'Cache read/write failed'}
            overall_status = 'not_ready'
    except Exception as e:
        logger.error(f"Cache health check failed: {e}")
        checks['cache'] = {'status': 'unhealthy', 'error': str(e)}
        overall_status = 'not_ready'
    
    response_status = status.HTTP_200_OK if overall_status == 'ready' else status.HTTP_503_SERVICE_UNAVAILABLE
    
    return Response({
        'status': overall_status,
        'timestamp': time.time(),
        'checks': checks,
        'version': '1.0.0'
    }, status=response_status)


@api_view(['GET'])
@permission_classes([AllowAny])
def liveness_check(request):
    """
    Liveness check that indicates if the application is alive and running.
    """
    return Response({
        'status': 'alive',
        'timestamp': time.time(),
        'uptime': time.time() - getattr(settings, 'START_TIME', time.time())
    }, status=status.HTTP_200_OK)


def welcome_view(request):
    """
    Welcome page for the Finacle API - renders HTML template
    """
    context = {
        'app_name': 'Finacle',
        'version': '1.0.0',
        'environment': getattr(settings, 'ENVIRONMENT', 'development'),
        'debug': settings.DEBUG,
        'endpoints': [
            {'name': 'Health Check', 'url': '/api/v1/health/', 'description': 'Service health status'},
            {'name': 'Readiness Check', 'url': '/api/v1/ready/', 'description': 'Dependencies health check'},
            {'name': 'Liveness Check', 'url': '/api/v1/alive/', 'description': 'Service liveness probe'},
            {'name': 'Admin Interface', 'url': '/admin/', 'description': 'Django admin panel'},
            {'name': 'API Root', 'url': '/api/v1/', 'description': 'API documentation'},
            {'name': 'Login', 'url': '/login/', 'description': 'User authentication'},
            {'name': 'User Profile', 'url': '/api/v1/auth/me/', 'description': 'User profile management'},
        ]
    }
    return render(request, 'core/welcome.html', context)


def login_view(request):
    """
    Login page for user authentication
    """
    context = {
        'app_name': 'Finacle',
    }
    return render(request, 'core/login.html', context)


def dashboard_view(request):
    """
    Dashboard page for authenticated users
    """
    context = {
        'app_name': 'Finacle',
    }
    return render(request, 'core/dashboard.html', context)
