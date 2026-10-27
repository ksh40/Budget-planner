from collections import defaultdict
from django.apps import apps
from django.db.models import Count
from .models import Bookmark

PLACEHOLDER_SUFFIX = '@users.invalid'


PLANNER_APPS = {'food', 'activities', 'eventful', 'punguza', 'students'}


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


def card_data(obj):
    """The few fields every post type shares, whatever its model calls them."""
    return {
        'name': getattr(obj, 'name', None) or getattr(obj, 'title', '') or '',
        'place': getattr(obj, 'place', None) or getattr(obj, 'location', '') or '',
        'price': getattr(obj, 'price', None),
        'image': getattr(obj, 'image', None),
    }


def saved_items(user):
    """The user's saved posts, newest first. Bookmarks whose post was deleted are cleaned up."""
    bookmarks = list(Bookmark.objects.filter(user=user))

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
