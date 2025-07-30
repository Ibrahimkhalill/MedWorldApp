from rest_framework import serializers
from .models import OneTimeNotification, NotificationText

class NotificationTextSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationText
        fields = ['title', 'message']

class OneTimeNotificationSerializer(serializers.ModelSerializer):
    notification_text = NotificationTextSerializer()

    class Meta:
        model = OneTimeNotification
        fields = ['id', 'notification_text', 'is_read']
