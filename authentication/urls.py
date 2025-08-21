from django.urls import path
from . import views

app_name = 'authentication'

urlpatterns = [
    # User login
    path('login/', views.login_user, name='login'),
    
    # Firebase token verification
    path('verify/', views.verify_firebase_token, name='verify_token'),
    
    # User registration
    path('register/', views.register_user, name='register'),
    
    # User profile management
    path('me/', views.user_profile, name='user_profile'),
    
    # Authentication status
    path('status/', views.user_status, name='user_status'),
    
    # Logout
    path('logout/', views.logout_user, name='logout'),
    
    # Password reset
    path('forgot-password/', views.forgot_password, name='forgot_password'),
]
