from plan.utils import get_budget
from django.shortcuts import render
from .models import Eventful


def eventful_home_view(request):
    amount, show_all = get_budget(request)
    eventful = Eventful.objects.all() if show_all else Eventful.objects.filter(price__lte=amount)

    results = [{'name': e.name, 
                'price': e.price, 
                'place': e.location,
                'description': e.description,
                'image': e.image, 
                'change': amount - e.price} for e in eventful]
    results.sort(key=lambda r: r['price'] if show_all else r['change'])

    return render(request, 'eventful/home.html', {
        'amount': amount, 'show_all': show_all, 'results': results,
    })