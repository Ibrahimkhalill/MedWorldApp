from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from django.utils import timezone
from datetime import datetime
from mainapp.models import Subscription


def check_subscription_status():
    """
    Automatically check and deactivate expired free trials or subscriptions.
    """
    now = timezone.now()

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

def start_scheduler():
    """
    Start the background scheduler for periodic tasks.
    """
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        check_subscription_status,
        trigger=IntervalTrigger(seconds=60),  # Run every 60 seconds
        id="check_subscription_status",
        name="Check and deactivate expired subscriptions",
        replace_existing=True,
    )
   

    scheduler.start()
    print("Scheduler started...")

    # Shut down the scheduler when Django exits
    import atexit
    atexit.register(lambda: scheduler.shutdown())
