from django.shortcuts import render
from django.contrib.auth.models import User
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.authtoken.models import Token
from mainapp.serializers import *
from django.contrib.auth import authenticate
from django.shortcuts import get_object_or_404
from rest_framework_simplejwt.authentication import JWTAuthentication
from mainapp.models import OTP, PercantageSurgery, Subscription, Surgery, UserProfile
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import authentication_classes, permission_classes
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string 
from django.utils import timezone
import django.http
from openpyxl import Workbook
from mainapp.models import Surgery
from fpdf import FPDF
from django.utils.timezone import now
from datetime import timedelta
from django.db import transaction
from .otpGenarate import generate_otp

from background_task import background
# Create your views here.
import requests
import stripe
import json
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.http import JsonResponse , HttpResponse


# Create your views here.
# User Registration
@api_view(["POST"])
def register(request):
    if request.method == "POST":
        email = request.data.get("email")
        password = request.data.get("password")
        userName = request.data.get("userName")
        specialty = request.data.get("specialty")
        residencyDuration = request.data.get("residencyDuration")
        residencyYear = request.data.get("residencyYear")

        if not email or not password:
            return Response({"error": "Email and password are required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Create user
            user = User.objects.create_user(username=email, password=password)
            user.save()

            # Create user profile
            UserProfile.objects.create(
                user=user,
                email=email,
                username=userName,
                specialty=specialty,
                residencyDuration=residencyDuration,
                residencyYear=residencyYear,
            )

            # Create subscription and activate free trial
            subscription = Subscription.objects.create(user=user)
            subscription.activate_free_trial()

            # Generate token
            token, _ = Token.objects.get_or_create(user=user)

            return Response({"token": token.key}, status=status.HTTP_201_CREATED)

        except IntegrityError:
            return Response({"error": "A user with this email already exists"}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


       

@api_view(["POST"])
def send_otp(request):
    if request.method == 'POST':
        email = request.data.get('email')
        
        if not email:
            return Response({"error": "Email is required"}, status=400)
        
        try:
            if User.objects.filter(username=email).exists():  # Or `.filter(email=email)` if that's what you use
                print("❗ Email already exists")
                return Response({"error": "Email already exists"}, status=status.HTTP_400_BAD_REQUEST)
            else:
                otp = generate_otp()
                OTP.objects.create(email=email, otp=otp)
                
                print(f"✅ OTP generated: {otp}")
                
                html_content = render_to_string('otp_email_template.html', {'otp': otp, 'email': email})
                
                msg = EmailMultiAlternatives(
                    subject='Your OTP Code',
                    body='This is an OTP email.',
                    from_email='medworld@medworld.online',
                    to=[email],
                )
                msg.attach_alternative(html_content, "text/html")
                msg.send(fail_silently=False)
                
                print(f"📧 OTP sent to {email}")
                return Response({'message': 'OTP sent to your email.'})
        
        except Exception as e:
            print(f"🔥 Error sending OTP: {e}")
            return Response({'error': str(e)}, status=500)
    
    return Response({'message': 'Invalid method.'})



@api_view(["POST"])
def verify_otp(request):
    if request.method == 'POST':
        otp = request.data.get('otp')
        email = request.data.get('email')
        
        print(email, otp)

        try:
                otp_record = OTP.objects.get(otp=otp, email=email)
                otp_record.attempts += 1  
                otp_record.save()  
                if (timezone.now() - otp_record.created_at).seconds > 120:
                    otp_record.delete()  
                    return Response({'message': ' Otp Expired'})
                else:
                    otp_record.delete()  
                    return Response('email verified', status=status.HTTP_200_OK)
        except OTP.DoesNotExist:
                return Response({'error': 'Invalid Otp'}, status=status.HTTP_400_BAD_REQUEST)
           
    return Response("Method is not allowed")

# User Login and Token Generation
@api_view(["POST"])
def login(request):
    email = request.data.get("email")
    password = request.data.get("password")

    if not email or not password:
        return Response({"error": "Email and password are required"}, status=status.HTTP_400_BAD_REQUEST)

    # Authenticate the user
    user = authenticate(request, username=email, password=password)

    if not user:
        return Response({"error": "Email or Password is wrong!"}, status=status.HTTP_401_UNAUTHORIZED)

    if not user.is_active:
        return Response({"error": "Account is inactive"}, status=status.HTTP_401_UNAUTHORIZED)

    # Generate or retrieve the token
    token, _ = Token.objects.get_or_create(user=user)

    return Response({
        "token": token.key,  # Return the token key
    }, status=status.HTTP_200_OK)
    


@api_view(["POST"])
def admin_login(request):
    email = request.data.get("email")
    password = request.data.get("password")

    if not email or not password:
        return Response({"error": "Email and password are required"}, status=status.HTTP_400_BAD_REQUEST)

    # Authenticate the user
    user = authenticate(request, username=email, password=password)

    if not user:
        return Response({"error": "Email or Password is wrong!"}, status=status.HTTP_401_UNAUTHORIZED)

    if not user.is_active:
        return Response({"error": "Account is inactive"}, status=status.HTTP_401_UNAUTHORIZED)

    # Check if the user is an admin or staff
    is_admin = user.is_superuser
    is_staff = user.is_staff

    if not is_admin and not is_staff:
        return Response({"error": "Email or Password is wrong!"}, status=status.HTTP_403_FORBIDDEN)

    # Generate or retrieve the token
    token, _ = Token.objects.get_or_create(user=user)

    return Response({
        "token": token.key,  # Return the token key
        "is_admin": is_admin,
        "is_staff": is_staff,
    }, status=status.HTTP_200_OK)
    
    
    

import traceback

@api_view(["POST"])
def Password_reset_send_otp(request):
    email = request.data.get('email')
    print(email)

    try:
        existing_user = User.objects.filter(username=email).first()
        print("existing_user", existing_user)

        if not existing_user:
            return Response({'message': 'No user found with this email.'}, status=status.HTTP_404_NOT_FOUND)

        # Generate OTP
        otp = generate_otp()

        # Save OTP to DB
        OTP.objects.create(email=email, otp=otp)

        # Load HTML email template
        html_content = render_to_string('otp_email_template.html', {'otp': otp, 'email': email})

        # Send the email
        msg = EmailMultiAlternatives(
            subject='Your OTP Code',
            body='This is an OTP email.',
            from_email='medworld@medworld.online',
            to=[email],
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send(fail_silently=False)

        return Response({'message': 'OTP sent to your email.'}, status=status.HTTP_200_OK)

    except Exception as e:
        import traceback
        print("🔴 Error in Password_reset_send_otp:")
        traceback.print_exc()
        return Response({'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    

@api_view(['POST'])
def reset_password(request):
    
    email =  request.data.get('email')
    new_password = request.data.get('newpassword')
    
    try:
        
        user = User.objects.get(username=email)
        
        if user:
            user.set_password(new_password)
            user.save()
            return Response({"message": "Password changed successfully"}, status=status.HTTP_200_OK)
        
    
    except User.DoesNotExist:
        return Response({"message": "User not found"}, status=status.HTTP_404_NOT_FOUND)
    
    except Exception as e:
        return Response({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    

#google_login
@api_view(["POST"])
def google_register(request):
    
    email = request.data.get("email")  
    
    if User.objects.filter(username=email).exists():
        return Response({"error": "Email already exists"}, status=status.HTTP_400_BAD_REQUEST)
    
    user = User.objects.create_user(username=email)
    user.save()
    
    UserProfile.objects.create(user=user)
    
    return Response({"message": "User created successfully"}, status=status.HTTP_201_CREATED)




# User Login and Token Generation
@api_view(["POST"])
def google_login(request):
    if request.method == "POST":
        email = request.data.get("email")
      

        if not email:
            return Response({"error": "Email and password are required"}, status=status.HTTP_400_BAD_REQUEST)

        user= User.objects.filter(username=email).first()

        if not user:
            return Response({"error": "Email or Password is wrong!"}, status=status.HTTP_401_UNAUTHORIZED)
    
    
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        return Response({
            "access_token": access_token,
            "refresh_token": str(refresh),
        }, status=status.HTTP_200_OK)



@api_view(['POST'])
def refresh_access_token(request):
    refresh_token = request.data.get('refresh_token')
    if not refresh_token:
        return Response({"error": "Refresh token is required"}, status=status.HTTP_400_BAD_REQUEST)
    try:
        refresh = RefreshToken(refresh_token)
        new_access_token = str(refresh.access_token)
        return Response({
            'access_token': new_access_token
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": "Invalid refresh token"}, status=status.HTTP_400_BAD_REQUEST)
     
     


@api_view(["DELETE"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def delete_user_and_related_data(request):
    try:
        # Start a database transaction to ensure atomicity
        with transaction.atomic():
            user = request.user
            user.delete()
            Response({"messages":"User and all related data deleted successfully."},status=status.HTTP_200_OK)

    except User.DoesNotExist:
        print("User does not exist.")
    except ProtectedError:
        print("Cannot delete the user due to protected related objects.")
    except Exception as e:
        print(f"Error: {e}")
        
        
@api_view(['POST'])
def check_email_availability(request):

    serializer = CheckEmailSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    email = serializer.validated_data['email'].strip().lower()

    email_exists = User.objects.filter(username=email).exists()

    return Response({'exists': email_exists}, status=status.HTTP_200_OK)



from django.db.models.functions import TruncMonth, TruncYear
from django.db.models import Count
from django.contrib.auth.models import User
from datetime import datetime

def calculate_users_by_year():
    # Get the earliest user creation year
    first_user = User.objects.order_by("date_joined").first()
    if not first_user:
        return {"error": "No users found."}

    starting_year = first_user.date_joined.year
    current_year = datetime.now().year

    # Prepare the result
    yearly_data = {}

    for year in range(starting_year, current_year + 1):
        # Query users for the current year grouped by month
        monthly_data = (
            User.objects.filter(date_joined__year=year)
            .annotate(month=TruncMonth("date_joined"))
            .values("month")
            .annotate(count=Count("id"))
            .order_by("month")
        )

        # Prepare the monthly data in the desired format
        months = [
            {"name": "Jan", "value": 0},
            {"name": "Feb", "value": 0},
            {"name": "Mar", "value": 0},
            {"name": "Apr", "value": 0},
            {"name": "May", "value": 0},
            {"name": "Jun", "value": 0},
            {"name": "Jul", "value": 0},
            {"name": "Aug", "value": 0},
            {"name": "Sep", "value": 0},
            {"name": "Oct", "value": 0},
            {"name": "Nov", "value": 0},
            {"name": "Dec", "value": 0},
        ]

        # Map database data to the months array
        for data in monthly_data:
            month_index = data["month"].month - 1  # Convert month to 0-based index
            months[month_index]["value"] = data["count"]

        # Add the year's data to the result
        yearly_data[str(year)] = months

    return yearly_data

@api_view(["GET"])
def yearly_user_data_view(request):
    try:
        data = calculate_users_by_year()
        return Response(data, status=200)
    except Exception as e:
        return Response({"error": str(e)}, status=500)