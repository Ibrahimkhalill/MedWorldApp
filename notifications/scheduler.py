import os
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from .views import send_visible_notifications

def start_scheduler():
    # Prevent multiple scheduler instances under Gunicorn
    if os.environ.get("RUN_MAIN") != "true":
        print("Scheduler not started (subprocess).")
        return

    scheduler = BackgroundScheduler()
    scheduler.add_job(
        send_visible_notifications,
        trigger=IntervalTrigger(seconds=10),
        id="send_visible_notifications",
        name="Check new notification",
        replace_existing=True,
    )
    scheduler.start()
    print("✅ Notifications Scheduler started...")

    import atexit
    atexit.register(lambda: scheduler.shutdown())