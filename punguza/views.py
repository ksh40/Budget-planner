from django.shortcuts import render
from plan.utils import get_budget
from .models import Punguza
from wangapi.utils import attach_bookmarks

def punguza_home_view(request):
    amount, show_all = get_budget(request)
    punguza = Punguza.objects.all() if show_all else Punguza.objects.filter(price__lte=amount)

    results = [{'pk': p.pk,
                'kind': p._meta.label_lower,
                'name': p.name, 
                'price': p.price, 
                'place': p.place,
                'image': p.image, 
                'change': amount - p.price} for p in punguza]
    results.sort(key=lambda r: r['price'] if show_all else r['change'])
    attach_bookmarks(request.user, results)

    return render(request, 'punguza/home.html', {
        'amount': amount, 'show_all': show_all, 'results': results,
    })
