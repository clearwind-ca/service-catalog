from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from oauthlogin.models import OAuthConnection
import pytz
from django.conf import settings
from web.shortcuts import get_object_or_None

from gh import user

class Profile(models.Model):
    TIMEZONE_CHOICES = zip(pytz.common_timezones, pytz.common_timezones)

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar = models.CharField(max_length=255)
    timezone = models.CharField(max_length=255, choices=TIMEZONE_CHOICES, default="UTC")

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile for: {self.user.username}"

@receiver(post_save, sender=OAuthConnection)
def create_user_profile(sender, instance, created, **kwargs):
    if instance.access_token:
        username = instance.user.username
        existing_profile = get_object_or_None(Profile, user=instance.user)
        print(existing_profile)
        if not existing_profile:
            profile = user.login_as_user(username).get_user(username)
            Profile.objects.create(user=instance.user, avatar=profile.avatar_url)
    