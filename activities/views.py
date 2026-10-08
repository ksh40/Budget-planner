from django.shortcuts import render

from decimal import Decimal, InvalidOperation
from django.shortcuts import render
from .models import Activity


def activities_home_view(request):
    raw_amount = request.GET.get('amount', '')
    try:
        amount = Decimal(raw_amount)
    except (InvalidOperation, TypeError):
        amount = Decimal('0.00')

    results = []

    if amount >= 0:
        activities = Activity.objects.filter(price__lte=amount)
        for a in activities:
            results.append({
                'name': a.name,
                'price': a.price,
                'place': a.location,
                'image': a.image,
                'change': amount - a.price,
            })
        results.sort(key=lambda r: r['change'])

    context = {
        'amount': amount,
        'results': results,
    }
    return render(request, 'activities/home.html', context)