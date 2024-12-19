# Generated by Django 5.1.3 on 2024-12-11 06:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mainapp', '0003_otp'),
    ]

    operations = [
        migrations.RenameField(
            model_name='userprofile',
            old_name='designation',
            new_name='residencyDuration',
        ),
        migrations.RemoveField(
            model_name='userprofile',
            name='phone_number',
        ),
        migrations.AddField(
            model_name='userprofile',
            name='residencyYear',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='specialty',
            field=models.TextField(blank=True, null=True),
        ),
    ]