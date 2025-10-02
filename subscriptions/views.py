
from rest_framework.response import Response
from rest_framework.decorators import api_view
from mainapp.serializers import *
from django.shortcuts import get_object_or_404
from mainapp.models import Subscription, UserProfile
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import authentication_classes, permission_classes
from dateutil.parser import parse
from django.utils.timezone import now


from background_task import background
# Create your views here.
import stripe

from rest_framework.response import Response
from django.http import HttpResponse
from collections import defaultdict
from datetime import datetime , timezone

        
@api_view(["POST"])
def revenuecat_webhook(request):
    try:
        payload = request.data
        event = payload.get("event", {})
        event_type = event.get("type")
        app_user_id = event.get("app_user_id")
        purchased_at_ms = event.get("purchased_at_ms")
        expiration_at_ms = event.get("expiration_at_ms")
        print("payload:", payload)
        print("Received RevenueCat webhook:", event_type, "for user:", app_user_id)
        
        # Validate user
        try:
            user = User.objects.get(id=int(app_user_id))
            print("user found:", user.username)
        except Exception:
            return Response({"error": "Invalid or missing user"}, status=400)

        # Determine entitlement safely
        entitlement_id = event.get("entitlement_id") or (event.get("entitlement_ids")[0] if event.get("entitlement_ids") else "Premium Plan")
        start_date = None
        end_date = None
        if purchased_at_ms:
            start_date = datetime.fromtimestamp(purchased_at_ms / 1000, tz=timezone.utc)
        if expiration_at_ms:
            end_date = datetime.fromtimestamp(expiration_at_ms / 1000, tz=timezone.utc)
        # Update subscription
        subscription, _ = Subscription.objects.get_or_create(user=user)
        if event_type in ["INITIAL_PURCHASE", "RENEWAL", "TEST"]:
            subscription.is_active = True
            subscription.free_trial = False
            subscription.free_trial_end = None
            subscription.start_date = start_date or subscription.start_date
            subscription.end_date = end_date or subscription.end_date
            subscription.save()
            
            Notification.objects.create(
            user=user,
            title="Subscription Activated",
            message=f"Your subscription to {entitlement_id} is now active.",
            data ={"url": "Subscriptions"},
            visible_at=now(), 
        )
            print("Subscription activated for user:", user.username)
        elif event_type in ["CANCELLATION", "EXPIRED"]:
            subscription.is_active = False
            subscription.save()
            print("Subscription deactivated for user:", user.username)
            Notification.objects.create(
            user=user,
            title="Subscription Expired",
            message=f"Your subscription to {entitlement_id} has expired.",
            data ={"url": "Subscriptions"},
            visible_at=now(),
        )

        if event_type in ["INITIAL_PURCHASE", "RENEWAL", "TEST"]:
        
        # # Save PaymentHistory safely
            PaymentHistory.objects.create(
                subscription=subscription,
                event_type=event_type.lower() if event_type else "",
                platform=event.get("store") or "",
                environment=event.get("environment") or "",
                amount=event.get("price") or 0,
                currency=event.get("currency") or "",
            )
        
            return Response({"status": "success"}, status=200)
        return Response({"status": "success"}, status=200)

    except Exception as e:
        print("Webhook error:", e)
        return Response({"status": "error", "detail": str(e)}, status=500)




    
# @api_view(["POST"])
# def stripe_webhook(request):
#     payload = request.body
#     sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")
   

#     try:
#         # Verify the webhook signature
#         event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
#     except (ValueError, stripe.error.SignatureVerificationError) as e:
#         return Response({"error": "Webhook signature failed"}, status=400)

#     # Handle checkout completion (when a subscription is created)
#     if event["type"] == "checkout.session.completed":
#         session = event["data"]["object"]

#         # Retrieve customer and subscription ID
#         stripe_customer_id = session.get("customer")
#         stripe_subscription_id = session.get("subscription")

#         # Fetch subscription details from Stripe
#         stripe_subscription = stripe.Subscription.retrieve(stripe_subscription_id)

#         # Extract start and end dates
#         current_period_start = datetime.fromtimestamp(stripe_subscription["current_period_start"])
#         current_period_end = datetime.fromtimestamp(stripe_subscription["current_period_end"])

#         # Update your Subscription model
#         try:
#             subscription = Subscription.objects.get(stripe_customer_id=stripe_customer_id)
#             subscription.stripe_subscription_id = stripe_subscription_id
#             subscription.start_date = current_period_start
#             subscription.end_date = current_period_end
#             subscription.is_active = True
#             subscription.free_trial = False  # Free trial is over
#             subscription.free_trial_end = None
#             subscription.save()
#         except Subscription.DoesNotExist:
#             print("Subscription for customer not found")

#     # Handle subscription renewals
#     elif event["type"] == "invoice.payment_succeeded":
#         invoice = event["data"]["object"]
#         stripe_customer_id = invoice["customer"]
#         stripe_subscription_id = invoice["subscription"]

#         # Retrieve updated subscription details
#         stripe_subscription = stripe.Subscription.retrieve(stripe_subscription_id)
#         current_period_start = datetime.fromtimestamp(stripe_subscription["current_period_start"])
#         current_period_end = datetime.fromtimestamp(stripe_subscription["current_period_end"])

#         # Update subscription dates
#         try:
#             subscription = Subscription.objects.get(stripe_customer_id=stripe_customer_id)
#             subscription.start_date = current_period_start
#             subscription.end_date = current_period_end
#             subscription.is_active = True
#             subscription.save()
#         except Subscription.DoesNotExist:
#             print("Subscription for customer not found")

#     # Handle subscription cancellation
#     elif event["type"] == "customer.subscription.deleted":
#         stripe_subscription = event["data"]["object"]
#         stripe_customer_id = stripe_subscription["customer"]

#         try:
#             subscription = Subscription.objects.get(stripe_customer_id=stripe_customer_id)
#             subscription.is_active = False
#             subscription.end_date = datetime.now()
#             subscription.save()
#         except Subscription.DoesNotExist:
#             print("Subscription for customer not found")

#     return Response({"status": "success"}, status=200)


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
    
    

@api_view(['GET'])

def get_all_subscription(request):
   
    # Get or create the user's subscription object
    subscription = Subscription.objects.all()
    # Check if the user already has a Stripe customer ID
    subscription_serializer = SubscriptionSerializer(subscription, many=True)

    return Response(subscription_serializer.data, status=200)


def get_invoices_by_subscription(subscription_id):
    """
    Fetch all invoices associated with a subscription.
    """
    try:
        invoices = stripe.Invoice.list(subscription=subscription_id)
        return invoices
    except stripe.error.StripeError as e:
        # Handle Stripe API errors
        print(f"Stripe Error: {e}")
        return None


def get_total_revenue_by_subscription(subscription_id):
    """
    Calculate the total revenue for a specific subscription based on paid invoices.
    """
    invoices = get_invoices_by_subscription(subscription_id)
    if not invoices:
        return 0  # Return 0 if the Stripe API call fails

    total_revenue = 0
    for invoice in invoices.auto_paging_iter():
        if invoice.get("paid", False):  # Safely access "paid" to avoid KeyError
            total_revenue += invoice.get("amount_paid", 0) / 100  # Stripe amounts are in cents

    return total_revenue


@api_view(["GET"])
def calculate_all_for_dashboard(request):
    """
    Calculate the revenue for all users and classify them into free and pro users.
    """
    subscriptions = Subscription.objects.all()
    print("subscriptions:", subscriptions)
    if not subscriptions.exists():
        return Response({"error": "No subscriptions found"}, status=404)

    # Count active (pro) and free trial users
    pro_user_count = subscriptions.filter(is_active=True).count()
    print("pro_user_count:", pro_user_count)
    free_user_count = subscriptions.filter(free_trial_end__isnull=False).count()

    # Calculate total revenue from PaymentHistory
    total_revenue = PaymentHistory.objects.filter(event_type__in=["initial_purchase", "renewal"]).aggregate(
        total=models.Sum("amount")
    )["total"] or 0

    response = {
        "free_user": free_user_count,
        "pro_user": pro_user_count,
        "total_revenue": round(total_revenue, 2),
    }

    return Response(response, status=200)


@api_view(["GET"])
def calculate_yearly_revenue(request):
    """
    Calculate monthly revenue starting from the first subscription year to the current year.
    """
    yearly_monthly_revenue = defaultdict(lambda: {month: 0 for month in range(1, 13)})

    first_year = datetime.now().year
    payments = PaymentHistory.objects.filter(event_type__in=["initial_purchase", "renewal"])

    if not payments.exists():
        return Response({"error": "No payment history found"}, status=404)

    for payment in payments:
        if payment.created_at:
            year = payment.created_at.year
            month = payment.created_at.month
            yearly_monthly_revenue[year][month] += payment.amount or 0
            first_year = min(first_year, year)

    current_year = datetime.now().year
    all_revenue_data = []

    for year in range(first_year, current_year + 1):
        data = [yearly_monthly_revenue[year].get(month, 0) for month in range(1, 13)]
        all_revenue_data.append({
            "year": year,
            "data": data
        })

    response = {
        "all_revenue_data": all_revenue_data
    }

    return Response(response, status=200)