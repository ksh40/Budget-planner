from plan.utils import get_budget
from django.shortcuts import render
from .models import Activity


def activities_home_view(request):
    amount, show_all = get_budget(request)
    activities = Activity.objects.all() if show_all else Activity.objects.filter(price__lte=amount)

    results = [{'name': a.name, 
                'price': a.price, 
                'place': a.location,
                'description': a.description,
                'image': a.image, 
                'change': amount - a.price} for a in activities]
    results.sort(key=lambda r: r['price'] if show_all else r['change'])

    return render(request, 'activities/home.html', {
        'amount': amount, 'show_all': show_all, 'results': results,
    })