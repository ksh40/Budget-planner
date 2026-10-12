from decimal import Decimal, InvalidOperation
from django.shortcuts import render
from .models import Eventful


def eventful_home_view(request):
    raw_amount = request.GET.get('amount', '')
    try:
        amount = Decimal(raw_amount)
    except (InvalidOperation, TypeError):
        amount = Decimal('0.00')

    results = []

    if amount >= 0:
        eventful = Eventful.objects.filter(price__lte=amount)
        for e in eventful:
            results.append({
                'name': e.name,
                'price': e.price,
                'place': e.location,
                'image': e.image,
                'change': amount - e.price,
            })
        results.sort(key=lambda r: r['change'])

    context = {
        'amount': amount,
        'results': results,
    }
    return render(request, 'eventful/home.html', context)