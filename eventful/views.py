from plan.utils import get_budget
from django.shortcuts import render
from .models import Eventful
from django.db.models import Q
from django.utils import timezone


def eventful_home_view(request):
    amount, show_all = get_budget(request)
    
    today = timezone.localdate()
    upcoming = Eventful.objects.filter(
        Q(one_time=False) | Q(event_date__isnull=True) | Q(event_date__gte=today)
        )
    eventful = upcoming if show_all else upcoming.filter(price__lte=amount)

    results = [{'name': e.name, 
                'price': e.price, 
                'place': e.location,
                'description': e.description,
                'one_time': e.one_time,
                'event_date': e.event_date,
                'image': e.image, 
                'instagram':e.instagram,
                'twitter':e.twitter,
                'tiktok':e.tiktok,
                'website':e.website,
                'tickets':e.tickets,
                'change': amount - e.price} for e in eventful]
    results.sort(key=lambda r: r['price'] if show_all else r['change'])
    
    return render(request, 'eventful/home.html', {
        'amount': amount, 'show_all': show_all, 'results': results,
    })