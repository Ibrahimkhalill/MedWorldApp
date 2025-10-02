from django.contrib import admin

from .models import *
# Register your models here.


admin.site.register(UserProfile)
admin.site.register(Surgery)
admin.site.register(Scientific)
admin.site.register(Course)
admin.site.register(Budget)
admin.site.register(PercantageSurgery)
admin.site.register(Notification)
admin.site.register(Subscription)
admin.site.register(TermsCondition)
admin.site.register(PrivacyPolicy)
admin.site.register(PaymentHistory)