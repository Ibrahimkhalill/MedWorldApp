from django.urls import path

from .views import *
urlpatterns = [
  
   path("login/", login),

   path("register/", register),
   path("send-otp/", send_otp),
   path("verify-otp/", verify_otp),
   path("google-register/", google_register),
   path("google-login/", google_login),
   path("password-reset-otp/", Password_reset_send_otp),
   path("password-reset/", reset_password),
   path("api/user_profile/",user_profile),
   path("api/surgery/", surgery),
   path("api/surgery/<int:surgery_id>/", surgery),
   path("api/export/surgery_to_excel/", export_surgery_to_excel),
   path("api/export/surgery_to_pdf/", export_surgery_to_pdf),
   path("api/export/surgery_to_google_sheets/", export_surgery_to_google_sheets),
   
]
