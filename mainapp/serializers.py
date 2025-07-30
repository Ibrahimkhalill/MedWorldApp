from rest_framework import serializers
from .models import *
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
        fields = ['id','user','username', 'email', 'specialty','residencyDuration','residencyYear','phone_number','gender', 'profile_picture','address','semester']

# Serializer for Surgery
class SurgerySerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    class Meta:
        model = Surgery
        fields = [
            'id', 'user', 'name_of_surgery','field_of_surgery', 'type_of_surgery', 'complications', 'histology',
            'main_surgeon', 'date', 'histology_description', 'complications_description',
            'notes1', 'notes2'
        ]


class ScientificSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    class Meta:
        model = Scientific
        fields = [
            'id', 'user', 'types_works', 'international', 'national', 'role', 'date',
            'name', 'co_author_names'
        ]


class CourseSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    class Meta:
        model = Course
        fields = ['id', 'user', 'date', 'name', 'location']

class PercantageSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    class Meta:
        model = PercantageSurgery
        fields = ['id', 'user', 'surgery_name', 'total_surgery']

class BudgetSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    class Meta: 
        model = Budget
        fields = [
            'id', 'user', 'category', 'date', 'name', 'registration_fee', 'travel_fee',
            'accommodation_expense', 'total_fee'
        ]

class NotificationSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    class Meta:
        model = Notification
        fields = ['id', 'user', 'title', 'message', 'data', 'created_at', 'is_read', 'visible_at']
        read_only_fields = ['user', 'created_at', 'visible_at', 'is_read']
        
        
class SubscriptionSerializer(serializers.ModelSerializer):
    user_profile = UserProfileSerializer(source='user.userprofile', read_only=True)  # Access related UserProfile

    class Meta:
        model = Subscription
        fields = [
            'id',
            'user',
            'user_profile',  # Include the UserProfile data here
            'stripe_customer_id',
            'stripe_subscription_id',
            'is_active',
            'free_trial',
            'free_trial_end',
            'start_date',
            'end_date',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']

        
class CheckEmailSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True, allow_blank=False)
    
    
    
    
class TermsConditionSeriaLizer(serializers.ModelSerializer):
    class Meta:
        model = TermsCondition
        fields = ['id', 'text']
        
class PrivacyPolicySeriaLizer(serializers.ModelSerializer):
    class Meta:
        model = PrivacyPolicy
        fields = ['id', 'text']