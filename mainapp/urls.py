from django.urls import path

from .views import *
from subscriptions.views import *
from authentications.views import *
from notifications.views import *
urlpatterns = [
  
   path("api/login/", login),
   path('api/check-email/', check_email_availability, name='check-email'),
   path("api/register/", register),
   path("api/delete_user_and_related_data/", delete_user_and_related_data),
   path("api/send-otp/", send_otp),
   path("api/verify-otp/", verify_otp),
   path("google-register/", google_register),
   path("google-login/", google_login),
   path("api/password-reset-otp/", Password_reset_send_otp),
   path("api/password-reset/", reset_password),
   path("api/user_profile/",user_profile),
   path("api/export/surgery_to_excel/", export_surgery_to_excel),
   path("api/export/surgery_to_pdf/", export_surgery_to_pdf),
   path("api/export/surgery_to_google_sheets/", export_surgery_to_google_sheets),
   # Surgery endpoints
    path('api/surgery-names-list/', get_surgery_names, name='surgery-name-list'),  # For listing and creating surgeries
    path('api/surgery/', surgery_view, name='surgery-list'),  # For listing and creating surgeries
    path('api/surgery/<int:pk>/', surgery_view, name='surgery-detail'),  # For updating, retrieving, and deleting a specific surgery

    path('api/percentage-surgery/', percentage_surgery_view, name='percentage-surgery-list'),  # GET all, POST
    path('api/percentage-surgery/<int:pk>/', percentage_surgery_view, name='percentage-surgery-detail'),  # GET single, DELETE
    # Scientific endpoints
    path('api/scientifics/', scientific_view, name='scientific-list'),  # Fetch all or create
    path('api/scientifics/<int:pk>/', scientific_view, name='scientific-detail'),  # Fetch, update, delete

    # Course endpoints
    path('api/courses/', course_view, name='course-list'),  # Fetch all or create
    path('api/courses/<int:pk>/', course_view, name='course-detail'),  # Fetch, update, delete

    # Budget endpoints
    path('api/budgets/', budget_view, name='budget-list'),  # Fetch all or create
    path('api/budgets/<int:pk>/', budget_view, name='budget-detail'),  # Fetch, update, delete
    
    path('api/notifications/', notification_view, name='notifications'),
    path('api/notifications/<int:pk>/read/', mark_notification_as_read, name='mark-notification-as-read'),
    path('api/notifications/unread-count/', unread_notification_count, name='unread-notification-count'),
    path('api/notifications/<int:pk>/sound-played/', mark_sound_played, name='unread-sound-notification'),
    
    path('api/create_or_retrieve_customer/', create_or_retrieve_customer, name='create_or_retrieve_customer'),
    path('api/payment-sheet/', payment_sheet, name='payment_sheet'),
    path('api/create-checkout-session/', create_checkout_session, name='create_checkout_session'),
    path('api/checkout/success/', checkout_success, name='checkout_success'),
    path('api/checkout/cancel/', checkout_cencel, name='checkout_cencel'),
    path('webhook/',stripe_webhook, name='webhook'),
    path('api/get_subscription/',get_subscription, name='get_subscription'),

    path('api/send-support-email/', send_support_email, name='send_support_email'),
   
]

