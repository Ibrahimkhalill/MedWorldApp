from django.db import models
from django.contrib.auth.models import User
# Create your models here.


class FirebaseToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.token
    
    
class NotificationText(models.Model):
    title = models.CharField(max_length=255, blank=True, null=True)
    message = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return self.title or "Notification Text"

class OneTimeNotification(models.Model):
    """A model for one-time notifications that can be sent to users."""
    notification_text = models.ForeignKey(
        NotificationText,
        on_delete=models.CASCADE,
        related_name='one_time_notifications',
        null=True,
        blank=True
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='app_one_time_notifications',  # changed related_name to avoid conflicts
        null=True,
        blank=True
    )
    is_read = models.BooleanField(default=False)

    def __str__(self):
        message_preview = (
            self.notification_text.message[:50] if self.notification_text and self.notification_text.message else "No message"
        )
        username = self.user.username if self.user else "Unknown User"
        return f"Notification for {username}: {message_preview}..."