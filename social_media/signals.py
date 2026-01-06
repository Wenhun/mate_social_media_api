from social_media.models import Profile
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender=User)
def create_profile(
    sender: User, instance: User, created: bool, *args, **kwargs
) -> None:
    if created:
        user_profile = Profile(user=instance)
        user_profile.save()
        user_profile.follows.set([instance.profile.pk])  # type: ignore
        user_profile.save()
