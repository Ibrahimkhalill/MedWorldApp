from django.shortcuts import render

# Create your views here.

from django.contrib.auth.models import User
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

from background_task import background
# Create your views here.
import requests
import stripe
import json
from rest_framework.response import Response
from django.http import JsonResponse , HttpResponse


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated]) 
def unread_notification_count(request):
    now_time = now()
    unread_count = Notification.objects.filter(user=request.user, is_read=False, visible_at__lte=now_time ).count()
    print("unread_count",unread_count)
    return Response({"unread_count": unread_count}, status=status.HTTP_200_OK)

# API View for Fetching Notifications
@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated]) 
def notification_view(request):
    # Only return notifications that are currently visible
    now_time = now()
    notifications = Notification.objects.filter(
        user=request.user,
        visible_at__lte=now_time  # Only visible notifications
    ).order_by('-created_at')
    unread_count = Notification.objects.filter(user=request.user, is_read=False, visible_at__lte=now_time ).count()

    data = [{
        "id": notification.id,
        "title": notification.title,
        "message": notification.message,
        "data": notification.data,
        "created_at": notification.created_at,
        "is_read": notification.is_read,
        "is_sound_play": notification.is_sound_played,
       
    } for notification in notifications]
    return Response(data, status=status.HTTP_200_OK)

# Mark Notification as Read
@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated]) 
def mark_notification_as_read(request, pk):
    try:
        notification = Notification.objects.get(pk=pk, user=request.user)
        notification.is_read = True
        notification.save()
        return Response({"message": "Notification marked as read"}, status=status.HTTP_200_OK)
    except Notification.DoesNotExist:
        return Response({"error": "Notification not found"}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated]) 
def mark_sound_played(request, pk):
    try:
        notification = Notification.objects.get(pk=pk, user=request.user)
        notification.is_sound_played = True
        notification.save()
        return Response({"message": "Sound marked as played"}, status=status.HTTP_200_OK)
    except Notification.DoesNotExist:
        return Response({"error": "Notification not found"}, status=status.HTTP_404_NOT_FOUND)
    