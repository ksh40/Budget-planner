from django.shortcuts import render
from plan.utils import get_budget
from .models import Punguza


def punguza_home_view(request):
    amount, show_all = get_budget(request)
    punguza = Punguza.objects.all() if show_all else Punguza.objects.filter(price__lte=amount)

    results = [{'name': p.name, 'price': p.price, 'place': p.place,
                'image': p.image, 'change': amount - p.price} for p in punguza]
    results.sort(key=lambda r: r['price'] if show_all else r['change'])

    return render(request, 'punguza/home.html', {
        'amount': amount, 'show_all': show_all, 'results': results,
    })
