from django.db import models
from django.contrib.auth.models import User
# Create your models here.
from django.db import transaction
from datetime import timedelta, datetime


class OTP(models.Model):
    email = models.EmailField(null=True, blank=True)
    otp = models.CharField(max_length=5)
    created_at = models.DateTimeField(auto_now_add=True)
    attempts = models.IntegerField(default=0)  

    def __str__(self):
        return f'OTP for {self.email}: {self.otp}'
	
    def save(self, *args, **kwargs):
        with transaction.atomic():
            # Delete existing OTPs for the same email
            OTP.objects.filter(email=self.email).delete()
            super().save(*args, **kwargs)
         

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, blank=True, null=True)
    username = models.CharField(max_length=300, blank=True, null=True)  
    email = models.CharField(max_length=200, blank=True, null=True)
    specialty = models.TextField( blank=True, null=True)
    residencyDuration = models.CharField(max_length=200, blank=True, null=True)
    residencyYear = models.CharField(max_length=200, blank=True, null=True)
    phone_number= models.CharField(max_length=20, blank=True, null=True)
    gender = models.CharField(blank=True,null=True, max_length=100)
    profile_picture = models.ImageField(upload_to="user", blank=True, null=True)
    address =  models.TextField( blank=True, null=True)
    semester = models.CharField(max_length=10, blank=True, null=True)
    

    def __str__(self):
        return self.user.username  
    

class Surgery(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    name_of_surgery = models.CharField(max_length=500, blank=True, null=True)
    field_of_surgery = models.CharField(max_length=500, blank=True, null=True)
    type_of_surgery = models.CharField(max_length=500, blank=True, null=True)
    complications = models.BooleanField(default=False)
    histology = models.BooleanField(default=False)
    main_surgeon = models.BooleanField(default=False)
    date = models.DateTimeField(blank=True, null=True)
    histology_description = models.TextField(blank=True, null=True)
    complications_description = models.TextField(blank=True, null=True)
    notes1 = models.TextField(blank=True, null=True)
    notes2 = models.TextField(blank=True, null=True)
    

    def __str__(self):
        return f"{self.user.get_full_name() if self.user else 'Unknown User'} - {self.name_of_surgery or 'Unnamed Surgery'}"

    

class Scientific(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    types_works = models.CharField(max_length=255, blank=True, null=True)
    international = models.BooleanField(default=False)
    national = models.BooleanField(default=False)
    role = models.CharField(max_length=255, blank=True, null=True)
    date = models.DateTimeField(blank=True, null=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    co_author_names = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.get_full_name() if self.user else 'Unknown User'} - {self.types_works or 'Unnamed Work'}"

    


class Course(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    date = models.DateTimeField(blank=True, null=True)
    name = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.user.get_full_name() if self.user else 'Unknown User'} - {self.name or 'Unnamed Course'}"

    


class Budget(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    category = models.CharField(max_length=255, blank=True, null=True)
    date = models.DateTimeField(blank=True, null=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    registration_fee = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    travel_fee = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    accommodation_expense = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    total_fee = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"{self.user.get_full_name() if self.user else 'Unknown User'} - {self.category or 'Unnamed Budget'}"


# Notification Model (Example)
class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    message = models.TextField()
    data = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    visible_at = models.DateTimeField(null=True, blank=True)  # When this notification should become visible
    is_sound_played = models.BooleanField(default=False)  # New field

    def __str__(self):
        return self.title
    

class PercantageSurgery(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    surgery_name = models.TextField(blank=True, null=True)
    total_surgery = models.IntegerField(blank=True, null=True)
    

class Subscription(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="subscription")
    stripe_customer_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    stripe_subscription_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    is_active = models.BooleanField(default=False)
    free_trial = models.BooleanField(default=True)
    free_trial_end = models.DateTimeField(null=True, blank=True)
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def deactivate(self):
        """Deactivate subscription or free trial."""
        self.is_active = False
        self.free_trial = False
        self.save()

    def activate_free_trial(self, duration_days=30):
        """Activate free trial for a specific duration."""
        now = timezone.now()  # Use timezone-aware datetime
        self.free_trial = True
        self.free_trial_end = now + timedelta(days=duration_days)
        self.save()

    def activate_subscription(self, duration_days=30):
        """Activate subscription for a specific duration."""
        now = timezone.now()  # Use timezone-aware datetime
        self.is_active = True
        self.start_date = now
        self.end_date = now + timedelta(days=duration_days)
        self.save()

    def check_status(self):
        """Check if free trial or subscription has expired."""
        now = timezone.now()  # Use timezone-aware datetime
        
        # Check free trial status
        if self.free_trial and self.free_trial_end and now >= self.free_trial_end:
            self.deactivate()
            return "Free trial expired"

        # Check subscription status
        if self.is_active and self.end_date and now >= self.end_date:
            self.deactivate()
            return "Subscription expired"

        return "Active"