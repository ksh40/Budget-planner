from django.db.models.signals import post_delete
from django.dispatch import receiver

from .models import Recipe, RecipePhoto


@receiver(post_delete, sender=RecipePhoto)
def delete_photo_file(sender, instance, **kwargs):
    
    if instance.image:
        try:
            instance.image.delete(save=False)
        except Exception:
            pass


@receiver(post_delete, sender=Recipe)
def delete_recipe_bookmarks(sender, instance, **kwargs):
    from wangapi.models import Bookmark

    Bookmark.objects.filter(kind="recipes.recipe", object_id=instance.pk).delete()
