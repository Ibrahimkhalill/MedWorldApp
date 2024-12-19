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

from background_task import background
# Create your views here.
import requests
import stripe
import json
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.http import JsonResponse , HttpResponse

# Set your Stripe secret key
stripe.api_key = "sk_test_51QRTfHALRymUd61pnuUKrQxQMdEbZu7K5By0gbsyVHyR0BYQbryEq7PbSwycaGPURUBa29HGzf6SArPRzM19cH0B004mfG89ye"

# Webhook secret (get this from your Stripe Dashboard)
endpoint_secret = 'whsec_211c66fa5205c7c0a438eb4d3552b3bfb9ca4014e7cd308ad7928c5f8ad02e7c'

@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def create_or_retrieve_customer(request):
    user = request.user

    # Get or create the user's subscription object
    subscription, created = Subscription.objects.get_or_create(user=user)

    # Check if the user already has a Stripe customer ID
    if not subscription.stripe_customer_id:
        # Create a new Stripe customer
        customer = stripe.Customer.create(
            email=user.email,
            name=user.username
        )
        # Save the Stripe customer ID to the subscription
        subscription.stripe_customer_id = customer["id"]
        subscription.save()

    return Response({"stripe_customer_id": subscription.stripe_customer_id})


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def create_checkout_session(request):
    DOMAIN = "https://e418-115-127-156-9.ngrok-free.app"  # Replace with your actual domain
    # price_id = request.data.get("price_id")  # Stripe price ID

    # if not price_id:
    #     return Response({"error": "Price ID is required."}, status=400)

    user = request.user
    
    user_profile = get_object_or_404(UserProfile, user=user)

    # Get or create the user's subscription object
    subscription, created = Subscription.objects.get_or_create(user=user)

    # Ensure the user has a Stripe customer ID
    if not subscription.stripe_customer_id:
        # Create a new Stripe customer if it doesn't exist
        customer = stripe.Customer.create(
            email=user_profile.email,
            name=user_profile.username
        )
        subscription.stripe_customer_id = customer["id"]
        subscription.save()

    try:
        # Create the Stripe Checkout session
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[
                {
                    "price": "price_1QWFVvALRymUd61pk6tWMqx0",
                    "quantity": 1,
                }
            ],
            mode="subscription",
            customer=subscription.stripe_customer_id,  # Use the existing Stripe customer ID
            success_url=f"{DOMAIN}/checkout/success/",
            cancel_url=f"{DOMAIN}/checkout/cancel/",
            metadata={  # Attach metadata to the session
                "user_id": str(user.id),  # Include the user ID for tracking
                "custom_note": "Tracking payment for subscription",
            },
        )

        return Response({"checkout_url": session.url}, status=200)

    except Exception as e:
        return Response({"error": str(e)}, status=400)


    
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def payment_sheet(request):
    user = request.user

    # Get or create the user's subscription object
    subscription, created = Subscription.objects.get_or_create(user=user)

    # Check if the user already has a Stripe customer ID
    if not subscription.stripe_customer_id:
        # Create a new Stripe customer
        customer = stripe.Customer.create(
            email=user.email,
            name=user.username
        )
        # Save the customer's ID to the subscription object
        subscription.stripe_customer_id = customer.id
        subscription.save()
    else:
        # Retrieve the existing Stripe customer
        customer = stripe.Customer.retrieve(subscription.stripe_customer_id)

    # Create an ephemeral key for the customer (needed for secure client-side interaction)
    ephemeral_key = stripe.EphemeralKey.create(
        customer=customer.id,
        stripe_version="2024-11-20.acacia"  # Or the latest version
    )

    # Create a PaymentIntent for the subscription
    payment_intent = stripe.PaymentIntent.create(
        amount=1000,  # Amount in cents, adjust as per your subscription plan
        currency="usd",  # Adjust based on your currency
        customer=customer.id,
        payment_method_types=["card"],  # You can also include others like 'ideal' or 'sepa_debit'
        setup_future_usage="off_session",  # To save payment method for future use
    )

    # Return the necessary data to the client to complete the payment sheet
    return Response({
        "paymentIntent": payment_intent.client_secret,
        "ephemeralKey": ephemeral_key.secret,
        "customer": customer.id,
        "publishableKey": "pk_test_51QRTfHALRymUd61pQIlqCCDPqE2qT97tbKJUK2LGFisLHlpqWr6MqPMaz9HRXvjuDxvCVWsLAIQ8YbnoU46P3H8600tmZcy5rk"  # Your Stripe public key
    })
        

    
@api_view(["POST"])
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")
   

    try:
        # Verify the webhook signature
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except (ValueError, stripe.error.SignatureVerificationError) as e:
        return Response({"error": "Webhook signature failed"}, status=400)

    # Handle checkout completion (when a subscription is created)
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]

        # Retrieve customer and subscription ID
        stripe_customer_id = session.get("customer")
        stripe_subscription_id = session.get("subscription")

        # Fetch subscription details from Stripe
        stripe_subscription = stripe.Subscription.retrieve(stripe_subscription_id)

        # Extract start and end dates
        current_period_start = datetime.fromtimestamp(stripe_subscription["current_period_start"])
        current_period_end = datetime.fromtimestamp(stripe_subscription["current_period_end"])

        # Update your Subscription model
        try:
            subscription = Subscription.objects.get(stripe_customer_id=stripe_customer_id)
            subscription.stripe_subscription_id = stripe_subscription_id
            subscription.start_date = current_period_start
            subscription.end_date = current_period_end
            subscription.is_active = True
            subscription.free_trial = False  # Free trial is over
            subscription.free_trial_end = None
            subscription.save()
        except Subscription.DoesNotExist:
            print("Subscription for customer not found")

    # Handle subscription renewals
    elif event["type"] == "invoice.payment_succeeded":
        invoice = event["data"]["object"]
        stripe_customer_id = invoice["customer"]
        stripe_subscription_id = invoice["subscription"]

        # Retrieve updated subscription details
        stripe_subscription = stripe.Subscription.retrieve(stripe_subscription_id)
        current_period_start = datetime.fromtimestamp(stripe_subscription["current_period_start"])
        current_period_end = datetime.fromtimestamp(stripe_subscription["current_period_end"])

        # Update subscription dates
        try:
            subscription = Subscription.objects.get(stripe_customer_id=stripe_customer_id)
            subscription.start_date = current_period_start
            subscription.end_date = current_period_end
            subscription.is_active = True
            subscription.save()
        except Subscription.DoesNotExist:
            print("Subscription for customer not found")

    # Handle subscription cancellation
    elif event["type"] == "customer.subscription.deleted":
        stripe_subscription = event["data"]["object"]
        stripe_customer_id = stripe_subscription["customer"]

        try:
            subscription = Subscription.objects.get(stripe_customer_id=stripe_customer_id)
            subscription.is_active = False
            subscription.end_date = datetime.now()
            subscription.save()
        except Subscription.DoesNotExist:
            print("Subscription for customer not found")

    return Response({"status": "success"}, status=200)


def checkout_success(request):
    return HttpResponse("Your checkout was successful!", status=200)


def checkout_cencel(request):
    return HttpResponse("Your checkout was successful!", status=200)



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_subscription(request):
    """
    Retrieve the subscription details for the authenticated user.
    """
    user = request.user
    try:
        # Retrieve subscription for the current user
        subscription = Subscription.objects.get(user=user)
        serializer = SubscriptionSerializer(subscription)
        return Response({"subscription": serializer.data}, status=200)
    except Subscription.DoesNotExist:
        return Response({"message": "No subscription found for this user."}, status=404)
    
    


@background(schedule=60)  # Check every 60 seconds (adjust as needed)
def check_subscription_status():
    """
    Automatically check and deactivate expired free trials or subscriptions.
    """
    now = datetime.now()

    # Check for expired free trials
    free_trial_expired = Subscription.objects.filter(
        free_trial=True, free_trial_end__lte=now
    )
    for subscription in free_trial_expired:
        subscription.free_trial = False
        subscription.save()
        print(f"Free trial expired for user {subscription.user.username}")

    # Check for expired subscriptions
    subscription_expired = Subscription.objects.filter(
        is_active=True, end_date__lte=now
    )
    for subscription in subscription_expired:
        subscription.is_active = False
        subscription.save()
        print(f"Subscription expired for user {subscription.user.username}")

    print("Checked free trial and subscription statuses.")