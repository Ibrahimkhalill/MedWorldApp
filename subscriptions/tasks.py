from celery import shared_task
from django.utils import timezone
from mainapp.models import Subscription

@shared_task
def check_subscription_status_task():
    now = timezone.now()

    free_trial_expired = Subscription.objects.filter(
        free_trial=True, free_trial_end__lte=now
    )
    for subscription in free_trial_expired:
        subscription.free_trial = False
        subscription.save()
        print(f"Free trial expired for user {subscription.user.username}")

    print("Checked free trial and subscription statuses.")