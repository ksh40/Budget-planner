from django.db.models.signals import post_delete
from django.dispatch import receiver

from accounts.models import Profile


@receiver(post_delete, sender=Profile)
def delete_profile_picture(sender, instance, **kwargs):
    if instance.profile_picture:
        try:
            instance.profile_picture.delete(save=False)
        except Exception:
            pass 