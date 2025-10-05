from celery import shared_task
from django.utils.timezone import now
from .models import  FirebaseToken
from mainapp.models import Notification
from .utils import send_firebase_notification
from django.db import transaction

@shared_task
def send_visible_notifications():
    now_time = now()

    with transaction.atomic():
        notifications = (
            Notification.objects
            .select_for_update(skip_locked=True)
            .filter(is_read=False, is_sound_played=False, visible_at__lte=now_time)
        )

        for notification in notifications:
            tokens = FirebaseToken.objects.filter(user=notification.user).values_list("token", flat=True)
            for token in tokens:
                send_firebase_notification(
                    token=token,
                    title=notification.title,
                    body=notification.message,
                    data=notification.data
                )

            notification.is_sound_played = True
            notification.save()
            print(f"✅ Notification {notification.id} sent to {tokens}")
