from django.db import models
from django.contrib.auth.models import User
# Create your models here.
from django.db import transaction


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
    email = models.CharField(max_length=200, blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    designation = models.CharField(max_length=200, blank=True, null=True)
    profile_picture = models.ImageField(upload_to="user", blank=True, null=True)

    def __str__(self):
        return self.user.username  
    

class Surgery(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    name_of_surgery = models.TextField(blank=True, null=True)
    type_of_surgery = models.TextField(blank=True, null=True)
    complications = models.TextField(blank=True, null=True)
    date = models.DateField(blank=True,null=True)