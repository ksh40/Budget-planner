from decimal import Decimal, InvalidOperation
from django.shortcuts import render
from .models import Item, Bundle


def food_home_view(request):
    raw_amount = request.GET.get('amount', '')
    try:
        amount = Decimal(raw_amount)
    except (InvalidOperation, TypeError):
        amount = Decimal('0.00')

    results = []

    if amount > 0:
        items = Item.objects.filter(price__lte=amount)
        bundles = Bundle.objects.filter(price__lte=amount)

        for item in items:
            results.append({
                'type': 'item',
                'name': item.name,
                'price': item.price,
                'place': item.place,
                'image': item.image,
                'change': amount - item.price,
            })

        for bundle in bundles:
            results.append({
                'type': 'bundle',
                'name': bundle.title,
                'price': bundle.price,
                'place': '',
                'image': bundle.image,
                'change': amount - bundle.price,
            })

        results.sort(key=lambda r: r['change'])

    context = {
        'amount': amount,
        'results': results,
    }
    return render(request, 'food/home.html', context)
