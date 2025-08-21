"""
Load testing configuration for Locust
"""
from locust import HttpUser, task, between


class FinacleUser(HttpUser):
    """Simulated user for load testing"""
    
    wait_time = between(1, 3)  # Wait 1-3 seconds between requests
    
    def on_start(self):
        """Called when a user starts"""
        pass
    
    @task(10)
    def health_check(self):
        """Test health check endpoint - most frequent"""
        self.client.get("/api/v1/health/")
    
    @task(3)
    def liveness_check(self):
        """Test liveness check endpoint"""
        self.client.get("/api/v1/alive/")
    
    @task(2)
    def readiness_check(self):
        """Test readiness check endpoint"""
        self.client.get("/api/v1/ready/")
    
    @task(1)
    def admin_page(self):
        """Test admin page access (should redirect to login)"""
        response = self.client.get("/admin/", catch_response=True)
        # Admin should redirect to login, so 302 is expected
        if response.status_code in [200, 302]:
            response.success()
        else:
            response.failure(f"Admin page returned {response.status_code}")


class AdminUser(HttpUser):
    """Simulated admin user"""
    
    wait_time = between(2, 5)
    weight = 1  # Less frequent than regular users
    
    @task
    def admin_health_checks(self):
        """Admin checking system health"""
        endpoints = [
            "/api/v1/health/",
            "/api/v1/ready/",
            "/api/v1/alive/"
        ]
        
        for endpoint in endpoints:
            self.client.get(endpoint)



