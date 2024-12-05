from rest_framework import serializers
from .models import UserProfile, Surgery
from django.contrib.auth.models import User



class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username',]  

# Serializer for UserProfile
class UserProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    class Meta:
        model = UserProfile
        fields = ['user', 'phone_number', 'designation', 'profile_picture']

# Serializer for Surgery
class SurgerySerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    class Meta:
        model = Surgery
        fields = ['id','user', 'name_of_surgery', 'type_of_surgery', 'complications','date']
