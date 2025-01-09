from apscheduler.schedulers.background import BackgroundScheduler
from .views import send_visible_notifications
from apscheduler.triggers.interval import IntervalTrigger

def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(send_visible_notifications,  trigger=IntervalTrigger(seconds=1),
                       id="send_visible_notifications",
        name="Check new notification",
        replace_existing=True,)  # Run every minute
    scheduler.start()
    print("notifications Scheduler started...")

    # Shut down the scheduler when Django exits
    import atexit
    atexit.register(lambda: scheduler.shutdown())
