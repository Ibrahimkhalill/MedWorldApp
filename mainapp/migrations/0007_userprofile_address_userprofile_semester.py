# Generated by Django 5.1.3 on 2024-12-12 05:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mainapp', '0006_userprofile_gender_userprofile_phone_number'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='address',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='semester',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
    ]