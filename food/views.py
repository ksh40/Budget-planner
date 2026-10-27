from decimal import Decimal, InvalidOperation
from django.shortcuts import render
from .models import Item, Bundle
from plan.utils import get_budget
from .models import Item, Bundle
from wangapi.utils import attach_bookmarks

def food_home_view(request):
    amount, show_all = get_budget(request)

    if show_all:
        items, bundles = Item.objects.all(), Bundle.objects.all()
    elif amount > 0:
        items = Item.objects.filter(price__lte=amount)
        bundles = Bundle.objects.filter(price__lte=amount)
    else:
        items, bundles = Item.objects.none(), Bundle.objects.none()

    results = []
    for item in items:
        results.append({'pk': item.pk,
                        'kind': item._meta.label_lower,
                        'type': 'item', 
                        'name': item.name, 
                        'price': item.price,
                        'place': item.place, 
                        'image': item.image,
                        'instagram':item.instagram,
                        'twitter':item.twitter,
                        'tiktok':item.tiktok,
                        'website':item.website,
                        'change': amount - item.price})

    for bundle in bundles:
        results.append({'pk': bundle.pk,
                        'kind': bundle._meta.label_lower,
                        'type': 'bundle', 
                        'name': bundle.title, 
                        'price': bundle.price,
                        'place': '', 
                        'image': bundle.image,
                        'change': amount - bundle.price})

    results.sort(key=lambda r: r['price'] if show_all else r['change'])
    attach_bookmarks(request.user, results)

    return render(request, 'food/home.html', {
        'amount': amount, 'show_all': show_all, 'results': results,
    })

