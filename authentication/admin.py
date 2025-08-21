from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, UserProfile


class UserProfileInline(admin.StackedInline):
    """
    Inline admin for UserProfile
    """
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    fk_name = 'user'


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Admin interface for User model
    """
    inlines = (UserProfileInline,)
    
    list_display = (
        'username', 'email', 'firebase_uid', 'first_name', 'last_name',
        'is_verified', 'firebase_email_verified', 'is_active', 'is_staff',
        'date_joined'
    )
    
    list_filter = (
        'is_verified', 'firebase_email_verified', 'firebase_phone_verified',
        'currency_preference', 'is_active', 'is_staff', 'is_superuser',
        'date_joined', 'groups'
    )
    
    search_fields = (
        'username', 'email', 'first_name', 'last_name', 'firebase_uid'
    )
    
    ordering = ('-date_joined',)
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {
            'fields': (
                'first_name', 'last_name', 'email', 'phone_number',
                'date_of_birth', 'currency_preference'
            )
        }),
        (_('Firebase Integration'), {
            'fields': (
                'firebase_uid', 'firebase_email_verified', 'firebase_phone_verified'
            )
        }),
        (_('Permissions'), {
            'fields': (
                'is_active', 'is_staff', 'is_superuser', 'is_verified',
                'groups', 'user_permissions'
            ),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'username', 'email', 'password1', 'password2',
                'firebase_uid', 'first_name', 'last_name'
            ),
        }),
    )
    
    readonly_fields = ('firebase_uid', 'firebase_email_verified', 'firebase_phone_verified')
    
    def get_queryset(self, request):
        """
        Custom queryset to include profile information
        """
        return super().get_queryset(request).select_related('profile')
    
    def get_inline_instances(self, request, obj=None):
        """
        Only show profile inline when editing existing user
        """
        if not obj:
            return []
        return super().get_inline_instances(request, obj)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """
    Admin interface for UserProfile model
    """
    list_display = (
        'user', 'language', 'timezone', 'email_notifications',
        'push_notifications', 'sms_notifications', 'created_at'
    )
    
    list_filter = (
        'language', 'timezone', 'email_notifications', 'push_notifications',
        'sms_notifications', 'created_at', 'updated_at'
    )
    
    search_fields = (
        'user__username', 'user__email', 'user__first_name', 'user__last_name',
        'city', 'state', 'country'
    )
    
    ordering = ('-created_at',)
    
    fieldsets = (
        (_('User'), {
            'fields': ('user',)
        }),
        (_('Personal Information'), {
            'fields': ('avatar', 'bio')
        }),
        (_('Address'), {
            'fields': (
                'address_line1', 'address_line2', 'city', 'state',
                'postal_code', 'country'
            )
        }),
        (_('Preferences'), {
            'fields': ('language', 'timezone')
        }),
        (_('Notifications'), {
            'fields': (
                'email_notifications', 'push_notifications', 'sms_notifications'
            )
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    
    def get_queryset(self, request):
        """
        Custom queryset to include user information
        """
        return super().get_queryset(request).select_related('user')
    
    def has_add_permission(self, request):
        """
        Only allow adding profiles through user admin
        """
        return False
