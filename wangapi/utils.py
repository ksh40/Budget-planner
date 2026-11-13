from collections import defaultdict
from django.apps import apps
from django.db.models import Count
from .models import Bookmark

PLACEHOLDER_SUFFIX = '@users.invalid'


PLANNER_APPS = {'food', 'activities', 'eventful', 'punguza', 'students', 'recipes'}
RECIPE_KIND = 'recipes.recipe'

SOCIAL_FIELDS = (
    ('instagram', 'Instagram'),
    ('tiktok', 'TikTok'),
    ('twitter', 'Twitter / X'),
    ('youtube', 'YouTube'),
    ('website', 'Website'),
)


def get_model_for(kind):
    """Turn 'food.item' into the model class, or None if it isn't allowed."""
    try:
        app_label, model_name = kind.split('.')
        if app_label not in PLANNER_APPS:
            return None
        return apps.get_model(app_label, model_name)
    except (ValueError, LookupError):
        return None


def attach_bookmarks(user, results):
    """Add 'saved' (this user saved it) and 'saves' (how many people did) to each result.

    Every result needs 'kind' (obj._meta.label_lower) and 'pk' (obj.pk).
    """
    by_kind = defaultdict(list)
    for r in results:
        by_kind[r['kind']].append(r['pk'])

    counts, mine = {}, set()
    for kind, pks in by_kind.items():
        rows = (
            Bookmark.objects.filter(kind=kind, object_id__in=pks)
            .order_by()
            .values('object_id')
            .annotate(n=Count('id'))
        )
        for row in rows:
            counts[(kind, row['object_id'])] = row['n']
        if user.is_authenticated:
            saved_ids = Bookmark.objects.filter(
                user=user, kind=kind, object_id__in=pks
            ).values_list('object_id', flat=True)
            for oid in saved_ids:
                mine.add((kind, oid))

    for r in results:
        key = (r['kind'], r['pk'])
        r['saves'] = counts.get(key, 0)
        r['saved'] = key in mine
    return results


def decorate_recipes(user, recipes):
    """Set .saved and .saves on each Recipe so the recipe card can show its bookmark state."""
    results = [{'kind': RECIPE_KIND, 'pk': r.pk} for r in recipes]
    attach_bookmarks(user, results)
    for recipe, res in zip(recipes, results):
        recipe.saved, recipe.saves = res['saved'], res['saves']
    return recipes


def social_links(obj):
    """(label, url) pairs for whichever social fields the post has. Only http(s) links count."""
    links = []
    for field, label in SOCIAL_FIELDS:
        url = getattr(obj, field, '') or ''
        if isinstance(url, str) and url.startswith(('http://', 'https://')):
            links.append((label, url))
    return links


def card_data(obj):
    """The few fields every post type shares, whatever its model calls them."""
    return {
        'name': getattr(obj, 'name', None) or getattr(obj, 'title', '') or '',
        'place': getattr(obj, 'place', None) or getattr(obj, 'location', '') or '',
        'price': getattr(obj, 'price', None),
        'image': getattr(obj, 'image', None),
        'links': social_links(obj),
    }


def saved_items(user):
    """The user's saved posts, newest first. Bookmarks whose post was deleted are cleaned up.

    Recipes are left out here: they show as full cards via saved_recipes().
    """
    bookmarks = list(Bookmark.objects.filter(user=user).exclude(kind=RECIPE_KIND))

    ids_by_kind = defaultdict(list)
    for b in bookmarks:
        ids_by_kind[b.kind].append(b.object_id)

    objects = {}
    for kind, ids in ids_by_kind.items():
        model = get_model_for(kind)
        if model is None:
            continue
        for obj in model.objects.filter(pk__in=ids):
            objects[(kind, obj.pk)] = obj

    items, stale = [], []
    for b in bookmarks:
        obj = objects.get((b.kind, b.object_id))
        if obj is None:
            stale.append(b.pk)
            continue
        data = card_data(obj)
        data.update({'kind': b.kind, 'pk': b.object_id})
        items.append(data)

    if stale:
        Bookmark.objects.filter(pk__in=stale).delete()
    return items


def saved_recipes(viewer, owner):
    """Recipes the owner bookmarked (live ones only), newest bookmark first."""
    from recipes.models import Recipe

    ids = list(
        Bookmark.objects.filter(user=owner, kind=RECIPE_KIND).values_list('object_id', flat=True)
    )
    found = {
        r.pk: r
        for r in Recipe.objects.live()
        .filter(pk__in=ids)
        .select_related('chef__user')
        .prefetch_related('photos')
    }
    ordered = [found[i] for i in ids if i in found]
    return decorate_recipes(viewer, ordered)


def top_saved(limit=5):
    """The most saved posts across every mode."""
    rows = (
        Bookmark.objects.order_by()
        .values('kind', 'object_id')
        .annotate(n=Count('id'))
        .order_by('-n', 'kind', 'object_id')[:limit]
    )
    out = []
    for row in rows:
        model = get_model_for(row['kind'])
        obj = model.objects.filter(pk=row['object_id']).first() if model else None
        if obj is not None:
            data = card_data(obj)
            data['saves'] = row['n']
            out.append(data)
    return out
