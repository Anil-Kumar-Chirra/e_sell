# accounts/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
from django.utils import timezone
from PIL import Image
import os


class User(AbstractUser):
    """
    Custom User model extending Django's AbstractUser for farmers e-commerce platform
    """
    USER_TYPE_CHOICES = [
        ('farmer', 'Farmer'),
        ('buyer', 'Buyer'),
        ('admin', 'Administrator'),
        ('vendor', 'Vendor/Supplier'),
    ]
    
    VERIFICATION_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
    ]
    
    # Basic Information
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, default='buyer')
    phone_regex = RegexValidator(
        regex=r'^(?:\+91)?[6-9]\d{9}$',
        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
    )
    phone_number = models.CharField(validators=[phone_regex], max_length=17, unique=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    
    # Address Information
    address_line_1 = models.CharField(max_length=255, blank=True)
    address_line_2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, default='India')
    
    # Verification and Status
    is_verified = models.BooleanField(default=False)
    verification_status = models.CharField(
        max_length=20, 
        choices=VERIFICATION_STATUS_CHOICES, 
        default='pending'
    )
    verification_date = models.DateTimeField(null=True, blank=True)
    
    # Business Information (for farmers and vendors)
    business_name = models.CharField(max_length=200, blank=True)
    business_registration_number = models.CharField(max_length=100, blank=True)
    tax_id = models.CharField(max_length=50, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        db_table = 'accounts_user' # means this model will be stored in 'accounts_user' table
        verbose_name = 'User' # means this model will be referred to as 'User' in the admin interface
        verbose_name_plural = 'Users' # means this model will be referred to as 'Users' in the admin interface
        indexes = [
            models.Index(fields=['user_type']),
            models.Index(fields=['verification_status']),
            models.Index(fields=['phone_number']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.username} ({self.get_user_type_display()})"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        
        # Resize profile picture if it exists
        if self.profile_picture:
            img = Image.open(self.profile_picture.path)
            if img.height > 300 or img.width > 300:
                output_size = (300, 300)
                img.thumbnail(output_size)
                img.save(self.profile_picture.path)
    
    @property
    def full_address(self):
        """Return formatted full address"""
        address_parts = [
            self.address_line_1,
            self.address_line_2,
            self.city,
            self.state,
            self.postal_code,
            self.country
        ]
        return ', '.join([part for part in address_parts if part])
    
    @property
    def is_farmer(self):
        return self.user_type == 'farmer'
    
    @property
    def is_buyer(self):
        return self.user_type == 'buyer'
    
    @property
    def is_vendor(self):
        return self.user_type == 'vendor'


class FarmerProfile(models.Model):
    """
    Extended profile for farmers with agriculture-specific information
    """
    FARMING_TYPE_CHOICES = [
        ('organic', 'Organic Farming'),
        ('conventional', 'Conventional Farming'),
        ('hydroponic', 'Hydroponic Farming'),
        ('mixed', 'Mixed Farming'),
    ]
    
    FARM_SIZE_CHOICES = [
        ('small', 'Small (< 2 acres)'),
        ('medium', 'Medium (2-10 acres)'),
        ('large', 'Large (10-50 acres)'),
        ('industrial', 'Industrial (> 50 acres)'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='farmer_profile')
    
    # Farm Information
    farm_name = models.CharField(max_length=200)
    farm_size = models.CharField(max_length=20, choices=FARM_SIZE_CHOICES)
    farm_size_acres = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    farming_type = models.CharField(max_length=20, choices=FARMING_TYPE_CHOICES, default='conventional')
    farming_experience_years = models.PositiveIntegerField(validators=[MaxValueValidator(100)])
    
    # Location specific to farm (might be different from user address)
    farm_address = models.TextField()
    farm_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    farm_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    
    # Certifications
    organic_certified = models.BooleanField(default=False)
    organic_certification_number = models.CharField(max_length=100, blank=True)
    organic_certification_expiry = models.DateField(null=True, blank=True)
    
    # Business Information
    bank_account_number = models.CharField(max_length=50, blank=True)
    bank_name = models.CharField(max_length=100, blank=True)
    bank_branch = models.CharField(max_length=100, blank=True)
    ifsc_code = models.CharField(max_length=11, blank=True)
    pan_number = models.CharField(max_length=10, blank=True)
    
    # Documents
    farm_photo = models.ImageField(upload_to='farm_photos/', null=True, blank=True)
    certification_document = models.FileField(upload_to='certifications/', null=True, blank=True)
    id_proof = models.FileField(upload_to='id_proofs/', null=True, blank=True)
    
    # Rating and Reviews
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    total_reviews = models.PositiveIntegerField(default=0)
    
    # Status
    is_active_seller = models.BooleanField(default=True)
    subscription_plan = models.CharField(max_length=50, default='basic')
    subscription_expiry = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'accounts_farmer_profile'
        verbose_name = 'Farmer Profile'
        verbose_name_plural = 'Farmer Profiles'
        indexes = [
            models.Index(fields=['farming_type']),
            models.Index(fields=['farm_size']),
            models.Index(fields=['organic_certified']),
            models.Index(fields=['is_active_seller']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.farm_name}"
    
    @property
    def is_subscription_active(self):
        return self.subscription_expiry and self.subscription_expiry > timezone.now()


class BuyerProfile(models.Model):
    """
    Extended profile for buyers (consumers, retailers, wholesalers)
    """
    BUYER_TYPE_CHOICES = [
        ('individual', 'Individual Consumer'),
        ('retailer', 'Retailer'),
        ('wholesaler', 'Wholesaler'),
        ('restaurant', 'Restaurant/Hotel'),
        ('institution', 'Institution'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='buyer_profile')
    
    # Buyer Information
    buyer_type = models.CharField(max_length=20, choices=BUYER_TYPE_CHOICES, default='individual')
    company_name = models.CharField(max_length=200, blank=True)
    gst_number = models.CharField(max_length=15, blank=True)
    
    # Preferences
    preferred_delivery_time = models.CharField(max_length=50, blank=True)
    special_instructions = models.TextField(blank=True)
    
    # Purchase History Summary
    total_orders = models.PositiveIntegerField(default=0)
    total_spent = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    average_order_value = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Loyalty Program
    loyalty_points = models.PositiveIntegerField(default=0)
    membership_tier = models.CharField(max_length=20, default='bronze')
    
    # Preferences for products
    prefers_organic = models.BooleanField(default=False)
    max_delivery_distance = models.PositiveIntegerField(default=50, help_text="Maximum delivery distance in KM")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'accounts_buyer_profile'
        verbose_name = 'Buyer Profile'
        verbose_name_plural = 'Buyer Profiles'
        indexes = [
            models.Index(fields=['buyer_type']),
            models.Index(fields=['membership_tier']),
            models.Index(fields=['prefers_organic']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.get_buyer_type_display()}"
    
    def update_purchase_stats(self, order_amount):
        """Update purchase statistics when a new order is placed"""
        self.total_orders += 1
        self.total_spent += order_amount
        self.average_order_value = self.total_spent / self.total_orders
        self.save()


class Address(models.Model):
    """
    Multiple addresses for users (shipping, billing, farm locations, etc.)
    """
    ADDRESS_TYPE_CHOICES = [
        ('home', 'Home'),
        ('office', 'Office'),
        ('farm', 'Farm'),
        ('warehouse', 'Warehouse'),
        ('billing', 'Billing'),
        ('shipping', 'Shipping'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
    address_type = models.CharField(max_length=20, choices=ADDRESS_TYPE_CHOICES)
    title = models.CharField(max_length=100, help_text="e.g., Home, Office, Main Farm")
    
    # Address Fields
    address_line_1 = models.CharField(max_length=255)
    address_line_2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100, default='India')
    
    # GPS Coordinates
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    
    # Status
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'accounts_address'
        verbose_name = 'Address'
        verbose_name_plural = 'Addresses'
        unique_together = ['user', 'title']
        indexes = [
            models.Index(fields=['user', 'address_type']),
            models.Index(fields=['is_default']),
            models.Index(fields=['postal_code']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.title}"
    
    @property
    def full_address(self):
        """Return formatted full address"""
        address_parts = [
            self.address_line_1,
            self.address_line_2,
            self.city,
            self.state,
            self.postal_code,
            self.country
        ]
        return ', '.join([part for part in address_parts if part])
    
    def save(self, *args, **kwargs):
        # If this address is set as default, remove default from other addresses
        if self.is_default:
            Address.objects.filter(user=self.user, is_default=True).update(is_default=False)
        super().save(*args, **kwargs)


class UserLoginHistory(models.Model):
    """
    Track user login history for security and analytics
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='login_history')
    login_time = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    login_successful = models.BooleanField(default=True)
    logout_time = models.DateTimeField(null=True, blank=True)
    session_duration = models.DurationField(null=True, blank=True)
    
    class Meta:
        db_table = 'accounts_user_login_history'
        verbose_name = 'User Login History'
        verbose_name_plural = 'User Login Histories'
        indexes = [
            models.Index(fields=['user', 'login_time']),
            models.Index(fields=['login_successful']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.login_time}"


# Signal handlers for profile creation
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Automatically create appropriate profile when user is created
    """
    if created:
        if instance.user_type == 'farmer':
            FarmerProfile.objects.create(
                user=instance,
                farm_name=f"{instance.username}'s Farm",
                farm_size='small',
                farm_size_acres=1.0,
                farming_experience_years=1,
                farm_address=instance.full_address or "Not specified"
            )
        elif instance.user_type in ['buyer', 'vendor']:
            BuyerProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """
    Save the profile when user is saved
    """
    try:
        if instance.user_type == 'farmer' and hasattr(instance, 'farmer_profile'):
            instance.farmer_profile.save()
        elif instance.user_type in ['buyer', 'vendor'] and hasattr(instance, 'buyer_profile'):
            instance.buyer_profile.save()
    except Exception:
        pass  # Profile might not exist yet