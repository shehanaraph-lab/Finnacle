from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """
    Custom User model extending Django's AbstractUser
    """
    # Firebase UID (unique identifier from Firebase Auth)
    firebase_uid = models.CharField(
        max_length=128, 
        unique=True, 
        null=True, 
        blank=True,
        help_text=_("Firebase Authentication UID")
    )
    
    # Profile fields
    phone_number = models.CharField(
        max_length=20, 
        blank=True, 
        null=True,
        help_text=_("User's phone number")
    )
    
    date_of_birth = models.DateField(
        null=True, 
        blank=True,
        help_text=_("User's date of birth")
    )
    
    # Financial profile
    currency_preference = models.CharField(
        max_length=3,
        default='USD',
        choices=[
            ('USD', 'US Dollar'),
            ('EUR', 'Euro'),
            ('GBP', 'British Pound'),
            ('JPY', 'Japanese Yen'),
            ('CAD', 'Canadian Dollar'),
            ('AUD', 'Australian Dollar'),
        ],
        help_text=_("User's preferred currency")
    )
    
    # Account status
    is_verified = models.BooleanField(
        default=False,
        help_text=_("Whether the user's email has been verified")
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Firebase-specific fields
    firebase_email_verified = models.BooleanField(
        default=False,
        help_text=_("Whether Firebase has verified the user's email")
    )
    
    firebase_phone_verified = models.BooleanField(
        default=False,
        help_text=_("Whether Firebase has verified the user's phone")
    )
    
    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")
        db_table = 'auth_user'
    
    def __str__(self):
        return self.email or self.username
    
    @property
    def full_name(self):
        """Get user's full name"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username
    
    def get_display_name(self):
        """Get display name for the user"""
        return self.full_name or self.email or self.username


class UserProfile(models.Model):
    """
    Extended user profile information
    """
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='profile'
    )
    
    # Personal information
    avatar = models.ImageField(
        upload_to='avatars/', 
        null=True, 
        blank=True,
        help_text=_("User's profile picture")
    )
    
    bio = models.TextField(
        max_length=500, 
        blank=True,
        help_text=_("User's biography or description")
    )
    
    # Address information
    address_line1 = models.CharField(
        max_length=255, 
        blank=True,
        help_text=_("Address line 1")
    )
    
    address_line2 = models.CharField(
        max_length=255, 
        blank=True,
        help_text=_("Address line 2")
    )
    
    city = models.CharField(
        max_length=100, 
        blank=True,
        help_text=_("City")
    )
    
    state = models.CharField(
        max_length=100, 
        blank=True,
        help_text=_("State/Province")
    )
    
    postal_code = models.CharField(
        max_length=20, 
        blank=True,
        help_text=_("Postal/ZIP code")
    )
    
    country = models.CharField(
        max_length=100, 
        blank=True,
        help_text=_("Country")
    )
    
    # Preferences
    language = models.CharField(
        max_length=10,
        default='en',
        choices=[
            ('en', 'English'),
            ('es', 'Spanish'),
            ('fr', 'French'),
            ('de', 'German'),
            ('it', 'Italian'),
            ('pt', 'Portuguese'),
            ('ru', 'Russian'),
            ('zh', 'Chinese'),
            ('ja', 'Japanese'),
            ('ko', 'Korean'),
        ],
        help_text=_("User's preferred language")
    )
    
    timezone = models.CharField(
        max_length=50,
        default='UTC',
        help_text=_("User's timezone")
    )
    
    # Notification preferences
    email_notifications = models.BooleanField(
        default=True,
        help_text=_("Receive email notifications")
    )
    
    push_notifications = models.BooleanField(
        default=True,
        help_text=_("Receive push notifications")
    )
    
    sms_notifications = models.BooleanField(
        default=False,
        help_text=_("Receive SMS notifications")
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("User Profile")
        verbose_name_plural = _("User Profiles")
        db_table = 'authentication_userprofile'
    
    def __str__(self):
        return f"Profile for {self.user.username}"
    
    def get_full_address(self):
        """Get user's full address as a string"""
        address_parts = []
        if self.address_line1:
            address_parts.append(self.address_line1)
        if self.address_line2:
            address_parts.append(self.address_line2)
        if self.city:
            address_parts.append(self.city)
        if self.state:
            address_parts.append(self.state)
        if self.postal_code:
            address_parts.append(self.postal_code)
        if self.country:
            address_parts.append(self.country)
        
        return ", ".join(address_parts) if address_parts else "No address provided"
