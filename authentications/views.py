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
        email = request.data.get("email")  # Use email as the username
        password = request.data.get("password")
        userName = request.data.get("userName")
        specialty= request.data.get("specialty")
        residencyDuration= request.data.get("residencyDuration")
        residencyYear= request.data.get("residencyYear")
       
        
        if not email or not password:
            return Response({"error": "Email and password are required"}, status=status.HTTP_400_BAD_REQUEST)
    
        
        user = User.objects.create_user(username=email, password=password)
        user.save()
        
        UserProfile.objects.create(user=user, email=email,username=userName,specialty=specialty,residencyDuration=residencyDuration,residencyYear=residencyYear )
        subscription = Subscription.objects.create(user=user)
        subscription.activate_free_trial()  # Call the instance meth
        token, _ = Token.objects.get_or_create(user=user)
        return Response({
            "token": token.key,  # Return the token key
        }, status=status.HTTP_201_CREATED)

       

@api_view(["POST"])
def send_otp(request):
    if request.method == 'POST':
        email = request.data.get('email')
        try:
             if User.objects.filter(username=email).exists():
                 print("kjfj")
                 return Response({"error": "Email already exists"}, status=status.HTTP_400_BAD_REQUEST)
             else:
                  # Generate OTP
                otp = generate_otp()
                # Save OTP to database
                OTP.objects.create(email=email, otp=otp)
                
                # Render the HTML template
                html_content = render_to_string('otp_email_template.html', {'otp': otp, 'email':email})
                
                # Send email
                msg = EmailMultiAlternatives(
                    subject='Your OTP Code',
                    body='This is an OTP email.',
                    from_email='hijabpoint374@gmail.com',  # Sender's email address
                    to=[email],
                )
                msg.attach_alternative(html_content, "text/html")
                msg.send(fail_silently=False)  
                
                return Response({'message': 'OTP sent to your email.'})
           
        except Exception as e:
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
def Password_reset_send_otp(request):
   
    email = request.data.get('email')
    print(email)

    try:
        # Check if the user exists
        existing_user = User.objects.get(username=email)
        
        if existing_user:
            print("existing_user", existing_user)
            
            # Generate OTP
            otp = generate_otp()
            
            # Save OTP to the database (assuming OTP model has 'email' and 'otp' fields)
            OTP.objects.create(email=email, otp=otp)
            
            # Prepare the HTML content for the OTP email
            html_content = render_to_string('otp_email_template.html', {'otp': otp, 'email': email})
            
            # Prepare email message
            msg = EmailMultiAlternatives(
                subject='Your OTP Code',
                body='This is an OTP email.',
                from_email='hijabpoint374@gmail.com',  # Replace with a valid sender email
                to=[email],
            )
            
            msg.attach_alternative(html_content, "text/html")
            
            # Send email and ensure it is sent without errors
            msg.send(fail_silently=False)
            
            return Response({'message': 'OTP sent to your email.'}, status=status.HTTP_200_OK)
    
    except User.DoesNotExist:
        # Handle the case where the user does not exist
        return Response({'message': 'The account you provided does not exist. Please try again with another account.'}, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
        # Log the exception for debugging purposes (optional)
        print(f"Error occurred: {e}")
        return Response({'message': 'An unexpected error occurred. Please try again later.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    

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
     
     


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def delete_user_and_related_data(request):
    try:
        # Start a database transaction to ensure atomicity
        with transaction.atomic():
            user = request.user
            user.delete()
            print("User and all related data deleted successfully.")

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